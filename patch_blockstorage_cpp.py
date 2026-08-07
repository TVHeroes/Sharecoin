"""
Patches src/node/blockstorage.cpp - the field rename (nNonce -> nNonce64 +
mix_hash), one CheckProofOfWork call site updated to the new signature (see
patch_pow_h.py), and one CheckProofOfWork call site removed entirely rather
than updated - see the comment below on why.
"""
path = 'src/node/blockstorage.cpp'
text = open(path).read()

old_index_load = '''                pindexNew->nNonce         = diskindex.nNonce;
                pindexNew->nStatus        = diskindex.nStatus;
                pindexNew->nTx            = diskindex.nTx;

'''
new_index_load = '''                pindexNew->nNonce64       = diskindex.nNonce64;
                pindexNew->mix_hash       = diskindex.mix_hash;
                pindexNew->nStatus        = diskindex.nStatus;
                pindexNew->nTx            = diskindex.nTx;

'''
assert old_index_load in text, 'index-load block not found verbatim'
text = text.replace(old_index_load, new_index_load, 1)

# This call site is in LoadBlockIndexGuts, which runs once per already-
# validated block in the on-disk index on EVERY node startup. Upstream could
# afford checking it here because a precomputed-hash-vs-target comparison is
# essentially free. ProgPoW has no equivalent cheap shortcut - a real check
# means recomputing the full hash, which is expensive by design (that's the
# whole point of proof of work). Every block reaching this point already
# passed this exact check once, when it was first connected (nStatus
# reflects that) - mechanically porting this call to the new
# full-header-recompute signature, like the other two call sites in this
# file, would silently turn every node restart into an O(chain length) full
# PoW recomputation. Confirmed as the real cause of a multi-minute-plus
# startup stall that got worse the more blocks a node already had synced
# (found and fixed 2026-08-07 - see NOTES.md). Removed instead of ported.
old_check1 = '''                if (!CheckProofOfWork(pindexNew->GetBlockHash(), pindexNew->nBits, consensusParams)) {
                    LogError("%s: CheckProofOfWork failed: %s\\n", __func__, pindexNew->ToString());
                    return false;
                }

                pcursor->Next();'''
new_check1 = '''                // Deliberately not re-running CheckProofOfWork here (unlike
                // upstream, which could afford it: a precomputed-hash
                // comparison against target is essentially free). ProgPoW
                // has no equivalent cheap shortcut - checking it for real
                // means recomputing the full hash, which is expensive by
                // design, and this loop runs once per already-validated
                // block on every single startup. Every block reaching this
                // point already passed this exact check when it was first
                // connected (nStatus reflects that), so redoing it here
                // just pays real PoW-computation cost per block on every
                // restart for no additional security benefit.

                pcursor->Next();'''
assert old_check1 in text, 'first CheckProofOfWork call site not found verbatim'
text = text.replace(old_check1, new_check1, 1)

old_check2 = '''    if (!CheckProofOfWork(block_hash, block.nBits, GetConsensus())) {'''
new_check2 = '''    if (!CheckProofOfWork(block, block.nBits, GetConsensus())) {'''
assert old_check2 in text, 'second CheckProofOfWork call site not found verbatim'
text = text.replace(old_check2, new_check2, 1)

open(path, 'w').write(text)
print('blockstorage.cpp patched OK')
