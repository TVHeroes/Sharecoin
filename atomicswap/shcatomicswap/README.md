# shcatomicswap

Sharecoin's chain-param patch of [decred/atomicswap](https://github.com/decred/atomicswap)'s
`cmd/btcatomicswap` tool, for doing atomic swaps directly against a
Sharecoin node's RPC (no exchange, no counterparty trust beyond the swap
contract itself).

Built by taking the upstream `btcatomicswap` tool and adding a
`shareCoinMainNetParams` value with Sharecoin's real live mainnet chain
params (`PubKeyHashAddrID=63`, `ScriptHashAddrID=18`, `PrivateKeyID=214`,
`Bech32HRPSegwit="shc"`, HD key IDs), matching
`bitcoin-source/src/kernel/chainparams.cpp`'s `CMainParams`, mapped
`walletPort()` to `8332` to match every deployed node's `-rpcport`, and
disabled `-testnet` with a clear error instead of silently pointing at
real Bitcoin's own testnet params (no public Sharecoin testnet is
deployed). Same address values already independently re-verified for the
draft Block DX / XBridge listing, see `../../blocknet/README.md`.

`LICENSE-decred-atomicswap` is upstream's own ISC license, copied
alongside per this project's existing convention for vendored/adapted
third-party code (see `bitcoin-source/src/crypto/ethash/` for the same
pattern).

## Building

Needs the rest of `decred/atomicswap`'s module tree to build (this
directory only holds Sharecoin's modified files, not the full upstream
checkout). Clone upstream, drop these files into `cmd/shcatomicswap/`
there, then `go build` from that directory.

## Usable address type

This tool's HTLC design only accepts legacy **P2PKH** (base58, prefix
byte 63) addresses for `initiate`/`participate` - the redeem/refund path
is hardcoded around that address type. A real swap needs a P2PKH address
specifically (`getnewaddress "" legacy`), not the `shc1...` bech32
addresses used everywhere else in this project.

## Status

Built and verified at the address/param/RPC-boundary level: a generated
address round-trips correctly against `shareCoinMainNetParams`, and
running `shcatomicswap initiate` decodes the address, passes the P2PKH
check, and computes RPC port 8332 correctly (fails only at
`getrawchangeaddress: connection refused` with no wallet running, proving
the patch works right up to that boundary). `-testnet` confirmed to error
cleanly instead of misbehaving.

Deliberately not yet run: `initiate`/`participate`/`redeem`/`refund`
against a real wallet with real funds, since those steps genuinely
lock/move real SHC. That's a step to run deliberately against your own
wallet, not something to automate. See `../../blocknet/README.md` for the
real remaining work before the Block DX listing goes anywhere near
production.
