#!/usr/bin/env python3
"""
Standalone Sharecoin (SHC) address/keypair generator.

Generates a real secp256k1 keypair entirely on THIS machine - no network
connection, no dependency on any Sharecoin node. Nobody but you ever sees
the private key. That's what makes the resulting address genuinely yours:
whoever holds the private key controls any coins sent to the address, and
only you have it.

Requires: pip install base58 pycryptodome ecdsa
"""
import base58
import secrets
from Crypto.Hash import SHA256, RIPEMD160
from ecdsa import SigningKey, SECP256k1

SECRET_KEY_VERSION = 239      # matches Sharecoin's base58Prefixes[SECRET_KEY]
BECH32_HRP = "shcrt"          # matches Sharecoin's bech32_hrp (sharenet/regtest)

CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"


def hash160(b: bytes) -> bytes:
    return RIPEMD160.new(SHA256.new(b).digest()).digest()


def bech32_polymod(values):
    generator = [0x3b6a57b2, 0x26508e6d, 0x1ea119fa, 0x3d4233dd, 0x2a1462b3]
    chk = 1
    for v in values:
        top = chk >> 25
        chk = (chk & 0x1ffffff) << 5 ^ v
        for i in range(5):
            chk ^= generator[i] if ((top >> i) & 1) else 0
    return chk


def bech32_hrp_expand(hrp):
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def bech32_create_checksum(hrp, data):
    values = bech32_hrp_expand(hrp) + data
    polymod = bech32_polymod(values + [0, 0, 0, 0, 0, 0]) ^ 1
    return [(polymod >> 5 * (5 - i)) & 31 for i in range(6)]


def bech32_encode(hrp, data):
    combined = data + bech32_create_checksum(hrp, data)
    return hrp + "1" + "".join(CHARSET[d] for d in combined)


def convertbits(data, frombits, tobits, pad=True):
    acc = 0
    bits = 0
    ret = []
    maxv = (1 << tobits) - 1
    for value in data:
        acc = (acc << frombits) | value
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad and bits:
        ret.append((acc << (tobits - bits)) & maxv)
    return ret


def segwit_address(hrp, witver, witprog):
    data = [witver] + convertbits(witprog, 8, 5)
    return bech32_encode(hrp, data)


def main():
    signing_key = SigningKey.generate(curve=SECP256k1, entropy=secrets.token_bytes)
    priv_bytes = signing_key.to_string()

    point = signing_key.verifying_key.pubkey.point
    x = int(point.x()).to_bytes(32, "big")
    prefix = b"\x03" if int(point.y()) % 2 else b"\x02"
    compressed_pubkey = prefix + x

    pubkey_hash = hash160(compressed_pubkey)
    address = segwit_address(BECH32_HRP, 0, pubkey_hash)  # native segwit (P2WPKH), the current default address type

    wif = base58.b58encode_check(
        bytes([SECRET_KEY_VERSION]) + priv_bytes + b"\x01"  # \x01 = compressed pubkey
    ).decode()

    print("=" * 70)
    print("New Sharecoin (SHC) wallet generated")
    print("=" * 70)
    print()
    print(f"Address (share this to receive mining rewards):")
    print(f"  {address}")
    print()
    print(f"Private key / WIF (KEEP THIS SECRET - anyone with this can")
    print(f"spend any coins sent to the address above):")
    print(f"  {wif}")
    print()
    print("Save the private key somewhere safe (a password manager, an")
    print("encrypted file, on paper). If you lose it, any coins sent to")
    print("this address are gone for good - there is no recovery.")
    print("=" * 70)


if __name__ == "__main__":
    main()
