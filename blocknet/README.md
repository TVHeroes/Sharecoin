# Blocknet / XBridge listing - draft, not submitted

`sharecoin--v31.99.0.conf` is a draft XBridge config for listing SHC on
Block DX (Blocknet's atomic-swap DEX), following the exact format used by
Blocknet's own [blockchain-configuration-files](https://github.com/blocknetdx/blockchain-configuration-files)
repo (see `xbridge-confs/litecoin--v0.18.1.conf` there for the reference
example this was modeled on).

## Status: draft only, nothing submitted or deployed yet

Values confirmed correct against this project's own chain params
(`bitcoin-source/src/kernel/chainparams.cpp`'s `CMainParams`) and a real
live node's `getnetworkinfo`:

- `AddressPrefix=63` / `ScriptPrefix=18` / `SecretPrefix=214` - matches
  `PUBKEY_ADDRESS`/`SCRIPT_ADDRESS`/`SECRET_KEY`.
- `Port=8332` - matches every deployed node's `-rpcport`.
- `BlockTime=120` - matches `nPowTargetSpacing`.
- `TxVersion=2` - matches this project's own `shcatomicswap` patch.

Values NOT independently verified against Blocknet's actual current
schema/service-node software, just estimated from the one Litecoin
example available - re-check before actually submitting:

- `MinTxFee` / `FeePerByte` - drafted from the live node's `relayfee`
  (0.00000100 SHC/kvB), but unit conventions for these two specific
  fields weren't confirmed against Blocknet's own docs.
- `Address`/`Ip`/`Username`/`Password` - deliberately left blank; these
  point at whichever machine actually runs the Sharecoin wallet for the
  Service Node, not decided yet.

## What compatibility research confirmed (2026-07-29)

Block DX/XBridge is actively maintained as of 2026. XBridge's stated
compatibility requirement is just a JSON-RPC interface plus CLTV support
and 13 specific RPC methods (`createrawtransaction`, `decoderawtransaction`,
`getblock`, `getblockchaininfo`, `getblockhash`, `getnewaddress`,
`getrawmempool`, `getrawtransaction`, `gettransaction`, `gettxout`,
`listunspent`, `sendrawtransaction`, `signmessage`/`signrawtransaction`,
`verifymessage`) - Sharecoin has all of these unchanged from upstream
Bitcoin Core, and CLTV/CSV/Segwit are active from genesis (same fact
already verified for the `shcatomicswap` tool, see NOTES.md).

## Real remaining work, not yet done

1. **A Service Node** - Blocknet's own node software, needs to run
   continuously and have RPC access to a live, funded Sharecoin wallet.
   This is a genuine 24/7 service, not a one-shot tool - per the
   project's standing rule, this would default to the Pi unless told
   otherwise.
2. **Real testing on Block DX** before submitting, using that Service
   Node - not just a config-file review.
3. **Submission**: fork `blocknetdx/blockchain-configuration-files`,
   add the tested config, open a pull request. (Alternative: pay a
   Blocknet community member via their Discord `#block-dx-listing`
   channel to handle listing + hosting instead of self-hosting.)

None of this has been started - this folder currently only holds the
draft config and this note.
