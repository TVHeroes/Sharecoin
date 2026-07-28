#!/bin/bash
# Builds the vendored chiavdf Python extension (vendor/chiavdf) into a local
# venv, so sharecoin_vdf_wrapper.py can `import chiavdf`.
#
# Requires (Debian/Raspberry Pi OS): cmake, g++ (C++17), python3-dev,
# python3-venv, libgmp-dev -  install with:
#   sudo apt install -y cmake g++ python3-dev python3-venv libgmp-dev
#
# ENABLE_GNU_ASM (chiavdf's x86/x64 asm fast path) is disabled automatically
# by upstream's own CMakeLists.txt on non-x86 CMAKE_SYSTEM_PROCESSOR values
# (see the vendored src/CMakeLists.txt's provenance comment) - no manual
# override needed to build on the Pi's aarch64.
#
# BUILD_VDF_CLIENT=N skips chiavdf's own networked timelord client, which
# this wrapper has no use for (same setting upstream's own non-Windows CI
# uses) - only the _chiavdf python extension is needed.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHIAVDF_DIR="$SCRIPT_DIR/vendor/chiavdf"
VENV_DIR="$SCRIPT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

pip install --upgrade pip setuptools wheel "pybind11>=3.0.4" "setuptools_scm[toml]>=10.2.0"

cd "$CHIAVDF_DIR"
BUILD_VDF_CLIENT=N pip install .

echo
echo "Build finished. Verifying with a real prove/verify roundtrip (small iteration count - not the calibrated production delay)..."
# Run from outside vendor/chiavdf/ - it contains its own uninstalled
# chiavdf/ source stub (no compiled .so), which would otherwise shadow the
# properly-installed venv package if the working directory were still here.
cd "$SCRIPT_DIR"
python3 - <<'EOF'
from chiavdf import create_discriminant, prove, verify_wesolowski

challenge = b"sharecoin-vdf-wrapper build smoke test"
disc_bits = 512
iterations = 100000
# Fixed canonical generator element, per chiavdf's own test suite
# (tests/test_verifier.py) - the challenge picks the group (via the
# discriminant), the generator is always this same starting point within it.
x = b"\x08" + (b"\x00" * 99)

discriminant = create_discriminant(challenge, disc_bits)
result = prove(challenge, x, disc_bits, iterations, "")
form_size = len(result) // 2
y, proof = result[:form_size], result[form_size:]

assert verify_wesolowski(str(discriminant), x, y, proof, iterations), "verify_wesolowski rejected a proof it just produced"
print("OK: build works, prove()/verify_wesolowski() round-trip succeeded.")
EOF
