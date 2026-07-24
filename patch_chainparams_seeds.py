"""
Replaces the regtest/sharenet chain's placeholder DNS seed with a real one,
so a freshly downloaded node with no flags/config can discover peers and
join the network on its own - without this, every new node only knows
about the network because someone handed it an -addnode value by hand,
which makes the maintainer a single point of bootstrap for the whole
network's topology, not just a single point of failure for one node.

Real Bitcoin Core's DNS seeds resolve to many independently-crawled peer
addresses; sharecoin.duckdns.org only ever resolves to whichever machine
currently holds the floating primary IP, so this is closer to a single
well-known bootstrap host than a true multi-source DNS seed - but it's
enough to get a fresh node its first peer, which is all a seed needs to do;
normal address-relay takes over from there.
"""

path = "bitcoin-source/src/kernel/chainparams.cpp"

with open(path, encoding="utf-8") as f:
    content = f.read()

old = '''        vFixedSeeds.clear(); //!< Regtest mode doesn't have any fixed seeds.
        vSeeds.clear();
        vSeeds.emplace_back("dummySeed.invalid.");'''

new = '''        vFixedSeeds.clear(); //!< Regtest mode doesn't have any fixed seeds.
        vSeeds.clear();
        // Real seed (not Bitcoin regtest's usual dummy placeholder) - lets a
        // freshly started node with no -addnode/config discover a peer and
        // join the network on its own. Only ever resolves to whichever
        // machine currently holds the floating primary IP, so this is one
        // bootstrap host, not a true multi-source DNS seed - still enough
        // to get a first peer, which is all a seed needs to do.
        vSeeds.emplace_back("sharecoin.duckdns.org.");'''

assert old in content, "regtest vSeeds block not found verbatim"
content = content.replace(old, new, 1)

old_port = "        nDefaultPort = 18544;"
new_port = (
    "        // Was 18544 (an arbitrary compiled-in default). DNS A-records "
    "can't carry\n"
    "        // port numbers, so a bare seed hostname (or a manually-typed "
    "-addnode=host\n"
    "        // with no :port) gets connected to on whatever nDefaultPort "
    "says - which\n"
    "        // has to actually match the port real-world deployments "
    "forward/listen on\n"
    "        // (8443 - see sharecoin.duckdns.org's port-forward and every "
    "-addnode\n"
    "        // example in this repo) or the DNS seed above is silently "
    "useless: it\n"
    "        // finds the right IP but tries the wrong port and nothing "
    "connects.\n"
    "        nDefaultPort = 8443;"
)
assert old_port in content, "nDefaultPort line not found verbatim"
content = content.replace(old_port, new_port, 1)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("patched OK")
