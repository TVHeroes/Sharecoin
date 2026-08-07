"""
Patches src/bitcoin.cpp - the unified multi-call wrapper (sharecoin.exe) hardcoded
upstream binary names (bitcoin-qt, bitcoind, bitcoin-cli, etc.) that this fork
never renamed, so every subcommand ("sharecoin gui", "sharecoin node", ...)
failed with execvp "file not found" - the actual binaries on disk are named
sharecoin-qt/sharecoind/sharecoin-cli/etc, never bitcoin-*.
"""
path = 'src/bitcoin.cpp'
text = open(path).read()

replacements = [
    ('args.emplace_back(UseMultiprocess(cmd) ? "bitcoin-gui" : "bitcoin-qt");',
     'args.emplace_back(UseMultiprocess(cmd) ? "sharecoin-gui" : "sharecoin-qt");'),
    ('args.emplace_back(UseMultiprocess(cmd) ? "bitcoin-node" : "bitcoind");',
     'args.emplace_back(UseMultiprocess(cmd) ? "sharecoin-node" : "sharecoind");'),
    ('args.emplace_back("bitcoin-cli");',
     'args.emplace_back("sharecoin-cli");'),
    ('args.emplace_back("bitcoin-wallet");',
     'args.emplace_back("sharecoin-wallet");'),
    ('args.emplace_back("bitcoin-tx");',
     'args.emplace_back("sharecoin-tx");'),
    ('args.emplace_back("bench_bitcoin");',
     'args.emplace_back("bench_sharecoin");'),
    ('args.emplace_back("bitcoin-chainstate");',
     'args.emplace_back("sharecoin-chainstate");'),
    ('args.emplace_back("test_bitcoin");',
     'args.emplace_back("test_sharecoin");'),
    ('args.emplace_back("test_bitcoin-qt");',
     'args.emplace_back("test_sharecoin-qt");'),
    ('args.emplace_back("bitcoin-util");',
     'args.emplace_back("sharecoin-util");'),
]

for old, new in replacements:
    assert old in text, f'call site not found verbatim: {old!r}'
    text = text.replace(old, new, 1)

open(path, 'w').write(text)
print('bitcoin.cpp patched OK')
