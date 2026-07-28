"""
Sharecoin time-locked vault (dead-man's switch style delayed reveal).

Honest note on what this actually provides: this is a commit-then-reveal
scheme with a real, on-chain, publicly verifiable trigger condition (a
Sharecoin block height and its getrandombeacon value), not literal
cryptographic timelock encryption. The encryption key is generated at lock
time and printed once, the operator has to keep it sealed themselves
(a safe, a separate device, split between trustees, whatever fits) and only
apply it once the target height has genuinely passed. What Sharecoin's
beacon actually buys you here is a real, tamper-evident, publicly-checkable
answer to "has the reveal condition genuinely been met yet", and a
commitment hash that proves the revealed secret wasn't altered after the
fact. It does not make it cryptographically impossible for the key-holder
to decrypt early if they choose to break their own promise, that would need
a real identity-based-encryption scheme (like drand's tlock), which this
beacon's plain hash output isn't designed for.

Usage:
    python sharecoin-timelock-vault.py lock --secret "my message" --blocks-ahead 5 --out vault.json
    python sharecoin-timelock-vault.py reveal --vault vault.json --key <the key printed by lock>
"""

import argparse
import base64
import hashlib
import json
import urllib.request
from base64 import b64encode

from cryptography.fernet import Fernet

RPC_URL = "http://127.0.0.1:8332"
RPC_USER = "your_rpc_username"
RPC_PASS = "your_rpc_password"

WINDOW_SIZE = 8


def call_rpc(method, params=None):
    payload = json.dumps({
        "jsonrpc": "1.0",
        "id": "sharecoin-timelock-vault",
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


def cmd_lock(args):
    current_height = call_rpc("getblockcount")
    target_height = current_height + args.blocks_ahead

    key = Fernet.generate_key()
    fernet = Fernet(key)
    ciphertext = fernet.encrypt(args.secret.encode())
    commitment = hashlib.sha256(args.secret.encode()).hexdigest()

    vault = {
        "ciphertext": ciphertext.decode(),
        "target_height": target_height,
        "lock_height": current_height,
        "commitment": commitment,
    }
    with open(args.out, "w") as f:
        json.dump(vault, f, indent=2)

    print(f"Vault written to {args.out}")
    print(f"Locked at block {current_height}, unlocks at block {target_height}")
    print(f"Commitment hash (publish this now, so the reveal can be checked against it): {commitment}")
    print()
    print("KEY (keep this sealed separately, do not store it next to the vault file,")
    print("and do not apply it until block " + str(target_height) + " has genuinely passed):")
    print(key.decode())


def cmd_reveal(args):
    with open(args.vault) as f:
        vault = json.load(f)

    target_height = vault["target_height"]
    current_height = call_rpc("getblockcount")

    if current_height < target_height:
        print(f"Not yet. Current height {current_height}, unlocks at {target_height} "
              f"({target_height - current_height} block(s) remaining).")
        return

    window_start = target_height - WINDOW_SIZE + 1
    beacon_result = call_rpc("getrandombeacon", [window_start, WINDOW_SIZE])
    beacon_hex = beacon_result["beacon"]

    fernet = Fernet(args.key.encode())
    plaintext = fernet.decrypt(vault["ciphertext"].encode()).decode()

    actual_commitment = hashlib.sha256(plaintext.encode()).hexdigest()
    if actual_commitment != vault["commitment"]:
        print("WARNING: revealed content does not match the original commitment hash.")
        print(f"Expected: {vault['commitment']}")
        print(f"Actual:   {actual_commitment}")
        return

    print(f"Reveal condition met: block {target_height} confirmed.")
    print(f"On-chain proof (getrandombeacon {window_start} {WINDOW_SIZE}): {beacon_hex}")
    print(f"Commitment verified: {actual_commitment}")
    print()
    print("Revealed secret:")
    print(plaintext)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    lock_parser = sub.add_parser("lock", help="Lock a secret until a future block height.")
    lock_parser.add_argument("--secret", required=True, help="The message to lock.")
    lock_parser.add_argument("--blocks-ahead", type=int, default=10, help="Blocks from now to unlock at.")
    lock_parser.add_argument("--out", default="vault.json", help="Output vault file.")
    lock_parser.set_defaults(func=cmd_lock)

    reveal_parser = sub.add_parser("reveal", help="Attempt to reveal a locked secret.")
    reveal_parser.add_argument("--vault", required=True, help="Path to the vault file.")
    reveal_parser.add_argument("--key", required=True, help="The key printed at lock time.")
    reveal_parser.set_defaults(func=cmd_reveal)

    args = parser.parse_args()
    args.func(args)
