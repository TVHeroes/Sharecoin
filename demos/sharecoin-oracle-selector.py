"""
Sharecoin oracle node selector: pick a random subset of data-providing nodes
for the current round, using already-confirmed on-chain randomness.

Honest note on timing: the pitch describes this running "for every incoming
data request", but the underlying beacon only actually changes once a new
block confirms (roughly every 2 minutes on this network), not on every
single request. So in practice this selects the active node subset "for the
current block", and multiple requests within that same block will get the
same subset, that's expected, not a bug. Call this again after a new block
confirms to get a freshly rotated subset. Unlike the raffle or sortition
scripts, this deliberately does NOT wait for a future height, it always acts
on whatever's already confirmed right now, since oracle selection needs an
answer immediately, not after a scheduled delay.

Usage:
    python sharecoin-oracle-selector.py --nodes nodes.txt --subset-size 5
"""

import argparse
import hashlib
import json
import urllib.request
from base64 import b64encode

RPC_URL = "http://127.0.0.1:8332"
RPC_USER = "your_rpc_username"
RPC_PASS = "your_rpc_password"

WINDOW_SIZE = 8


def call_rpc(method, params=None):
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "sharecoin-oracle-selector",
        "method": method,
        "params": params or [],
    }).encode()
    req = urllib.request.Request(
        RPC_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Basic " + b64encode(f"{RPC_USER}:{RPC_PASS}".encode()).decode(),
        },
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read())
        if body.get("error"):
            raise RuntimeError(body["error"]["message"])
        return body["result"]


def select_subset(nodes, subset_size, beacon_hex):
    sorted_nodes = sorted(nodes)
    remaining = list(sorted_nodes)
    picks = []
    for i in range(subset_size):
        round_hash = hashlib.sha256(f"{beacon_hex}:{i}".encode()).hexdigest()
        idx = int(round_hash, 16) % len(remaining)
        node = remaining.pop(idx)
        picks.append((node, round_hash, idx))
    return sorted_nodes, picks


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--nodes", required=True, help="File with one node ID/endpoint per line.")
    parser.add_argument("--subset-size", type=int, required=True, help="How many nodes to select for this round.")
    args = parser.parse_args()

    with open(args.nodes) as f:
        nodes = [line.strip() for line in f if line.strip()]

    if args.subset_size > len(nodes):
        print(f"Subset size {args.subset_size} is larger than the node pool ({len(nodes)}), clamping.")
        args.subset_size = len(nodes)

    current_height = call_rpc("getblockcount")
    window_start = current_height - WINDOW_SIZE + 1
    beacon_result = call_rpc("getrandombeacon", [window_start, WINDOW_SIZE])
    beacon_hex = beacon_result["beacon"]

    sorted_nodes, picks = select_subset(nodes, args.subset_size, beacon_hex)

    print(f"Round for block {current_height} (beacon window {window_start}-{current_height}).")
    print(f"Beacon value: {beacon_hex}")
    print()
    print("Draw order (verify by hand: sha256(f'{beacon}:{round}') mod nodes-remaining):")
    for i, (node, h, idx) in enumerate(picks):
        print(f"  Round {i + 1}: {h[:16]}... mod {len(sorted_nodes) - i} = {idx} -> {node}")
    print()
    print(f"Active node subset for block {current_height}:")
    for node, _, _ in picks:
        print(f"  - {node}")
    print()
    print("Call again after the next block confirms to get a freshly rotated subset.")


if __name__ == "__main__":
    main()
