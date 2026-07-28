# VDF wrapper parameters: current version and permanence policy

This mirrors docs/BEACON-SPEC.md's structure and reasoning, because it is
the same kind of problem: `vdf-wrapper/sharecoin_vdf_wrapper.py`'s
underlying computation (a Wesolowski VDF over a class group derived from
`getrandombeacon`'s output) is permanent and independently verifiable by
anyone who reruns it. But the *usage conventions* - what discriminant size
and iteration count to use, what real-world delay that implies, what it's
recommended for - live in this document, one person can edit at any time,
and nothing previously stopped that from changing quietly.

## Read this first: what the VDF wrapper does and does not solve

`getrandombeacon` already bounds the miner-grinding bias: an attacker
controlling `k` consecutive blocks in a window has at most `2^k` candidate
outcomes to choose from (docs/BEACON-SPEC.md, docs/DETAILS.md's
"Randomness beacon, in full"). **The VDF wrapper does not shrink that
bound.** A VDF's non-parallelizability is a per-input guarantee (you
cannot speed up one evaluation with more hardware) - it says nothing about
evaluating multiple *different* candidate inputs in parallel. An attacker
with `k+1` machines can run all `2^k` of their candidate outcomes through
the VDF simultaneously and still pick whichever one they prefer once the
delay elapses. For the small `k` values a realistic attack involves, that
is cheap. If bounding grinding bias further is the goal, the lever is
`window_size`, not this tool.

What the VDF wrapper *does* add: right now, whoever validates a beacon
window's last block first can read the raw `beacon` value an instant
before anyone else - a first-mover informational edge for anything built
on top that reacts to the beacon (a bet, a front-run trade, an early
guess). A mandatory, equal, non-skippable sequential delay between "raw
beacon known" and "derived value known" removes that edge for every
party, including the node operator who saw the winning block first:
nobody can compute the delayed output faster than anyone else, regardless
of who saw the input first.

Use this tool for the timing-fairness property. Do not present it as
"stronger randomness" or as closing the residual grinding-bias gap -
neither claim is accurate.

## What is and isn't a protocol rule

**Not a protocol rule at all.** Unlike `getrandombeacon`, this tool is not
part of bitcoin-source, not RPC, not consensus-adjacent in any way. It is
an ordinary off-chain script that takes a `getrandombeacon` output as
input. Nothing about it is fixed by the node software; everything below is
this repository's own recommended convention, changeable the same way
BEACON-SPEC.md's conventions are: a new tagged, OpenTimestamped version,
never a silent edit.

The one property that *is* mathematically fixed, regardless of version:
`create_discriminant` derives the class group deterministically from the
`beacon` hex, with no ceremony and no party who could have set it up
maliciously - anyone can rederive the same group from the same beacon
value.

## Version 1 (current)

| Parameter | Value | Notes |
|---|---|---|
| Discriminant size | 1024 bits | `BQFC_MAX_D_BITS`, chiavdf's own hard ceiling (`src/bqfc.h`) - also the value Chia's own mainnet uses. Not a tunable choice; 2048 (this spec's original draft value) does not work, chiavdf rejects it outright. |
| Iteration count | 28,500,000 | Targets ~5 minutes on the Pi 5 (this project's backup node, used as reference hardware since it is the weakest machine in the deployment - the VPS/Oracle nodes will be faster, making this a conservative, not optimistic, delay estimate). |
| Real-world delay this implies | ~5 minutes on Pi 5 reference hardware | See "Benchmarking status" below for how this was measured. Faster hardware finishes sooner; this is the slow end of the range, deliberately. |

### Benchmarking status

Measured directly on the live Pi 5 backup node (`192.168.1.200`), not
estimated: a real `derive` run against an actual confirmed
`getrandombeacon` window (`start_height=1000, window_size=8`, chain tip at
height 1114 at the time) with `--iterations 5000000` took **52.582
seconds** wall time, end to end, including the real RPC round-trip - a
measured rate of **~95,100 iterations/second**. `28,500,000` iterations
(`300 seconds * 95,100`, rounded) was then chosen to target roughly 5
minutes on this hardware. Independently verifying that same output with
`verify` took 0.134 seconds - confirming the core VDF property directly
(compute: ~53s, verify: ~0.1s), not just asserting it from chiavdf's own
documentation.

This is a single-run measurement on one specific device, not an average
across many runs or devices. Re-benchmark (and bump this to Version 2) if
the reference hardware changes, or if a more rigorous multi-run
measurement is done. `vdf-wrapper/build_vdf.sh`'s own smoke test uses a
much smaller iteration count (100,000) purely to confirm the build works
quickly - that number is not a usable delay and must not be confused with
the calibrated value above.

## Intended applications

Same list as docs/BEACON-SPEC.md (lotteries, NFT/collectible reveals, fair
matchmaking, DAO/committee sortition, delayed-reveal commitments,
oracle/validator subset selection), specifically for the subset of those
where a first-mover timing edge on the raw beacon value would matter (for
example: an on-chain bet that resolves against the beacon, where whoever
sees the winning block first could otherwise act on it before anyone
else). For applications that only care about the already-bounded grinding
bias and not about first-mover timing, this tool adds delay for no benefit
- use the base beacon directly.

## Permanence policy

Identical to docs/BEACON-SPEC.md's: any future change to the values in
this document is a new version (`Version 2`, `Version 3`, ...), never a
silent edit to `Version 1`'s numbers - committed to git history, tagged
(`vdf-wrapper-spec-v1`), and timestamped with
[OpenTimestamps](https://opentimestamps.org/) (`VDF-WRAPPER-SPEC.md.ots`,
committed alongside this file), so anyone can independently verify what
this document said and when, without trusting this repository, GitHub, or
its maintainer. Covered by the same `.github/workflows/spec-timestamp.yml`
automation as docs/BEACON-SPEC.md: re-stamped on change, upgraded to a
completed Bitcoin-anchored proof automatically once a day.
