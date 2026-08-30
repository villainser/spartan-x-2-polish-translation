#!/usr/bin/env python3
"""Apply the Spartan X 2 Polish v1.0 IPS to the verified No-Intro ROM."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys


PATCH_NAME = "Spartan X 2 (Japan) (Pl) (v1.0) (villainser).ips"
SOURCE_SIZE = 262_160
SOURCE_SHA256 = "386dd9ba05980b8097dcb6289519ef22cbf41d25dab24289e504bbea2c35f665"
PATCH_SHA256 = "b4595d124464afea49ad2c1af0f3487758e719c9bbf0781af9fa6eb4c980c3ed"
OUTPUT_SIZE = 262_160
OUTPUT_SHA256 = "0ff1f7a035b845fa853f3f4c14d0305b9c5bf3d3e1aaf894d9dc297631e89ae0"
DEFAULT_OUTPUT = "Spartan X 2 (Polish v1.0) [PL].nes"


class PatchError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_ips(source: bytes, patch: bytes) -> tuple[bytes, int]:
    if not patch.startswith(b"PATCH"):
        raise PatchError("Invalid IPS header")

    output = bytearray(source)
    position = 5
    record_count = 0

    while True:
        if position + 3 > len(patch):
            raise PatchError("Truncated IPS before EOF")

        marker = patch[position : position + 3]
        if marker == b"EOF":
            position += 3
            break

        offset = int.from_bytes(marker, "big")
        position += 3
        if position + 2 > len(patch):
            raise PatchError("Truncated IPS record length")

        length = int.from_bytes(patch[position : position + 2], "big")
        position += 2

        if length == 0:
            if position + 3 > len(patch):
                raise PatchError("Truncated IPS RLE record")
            length = int.from_bytes(patch[position : position + 2], "big")
            value = patch[position + 2]
            position += 3
            if length == 0:
                raise PatchError("Zero-length IPS RLE record")
            replacement = bytes([value]) * length
        else:
            if position + length > len(patch):
                raise PatchError("Truncated IPS data record")
            replacement = patch[position : position + length]
            position += length

        end = offset + length
        if offset < 16:
            raise PatchError("Patch attempts to modify the 16-byte iNES header")
        if end > len(output):
            raise PatchError("Patch record exceeds the source ROM size")

        output[offset:end] = replacement
        record_count += 1

    if position != len(patch):
        raise PatchError("Unexpected data after IPS EOF")

    return bytes(output), record_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply the verified Polish v1.0 patch to Spartan X 2 (Japan).nes"
    )
    parser.add_argument("source", type=Path, help="clean No-Intro Japanese ROM")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=f"output path (default: {DEFAULT_OUTPUT} next to the source)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_path = args.source.expanduser().resolve()
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else source_path.with_name(DEFAULT_OUTPUT)
    )
    patch_path = Path(__file__).resolve().with_name(PATCH_NAME)

    if output_path == source_path:
        raise PatchError("Refusing to overwrite the source ROM")
    if output_path.exists():
        raise PatchError(f"Output already exists: {output_path}")

    source = source_path.read_bytes()
    if len(source) != SOURCE_SIZE or sha256(source) != SOURCE_SHA256:
        raise PatchError(
            "Wrong source ROM. Expected the exact No-Intro Spartan X 2 (Japan).nes "
            f"({SOURCE_SIZE} bytes, SHA-256 {SOURCE_SHA256})."
        )

    patch = patch_path.read_bytes()
    if sha256(patch) != PATCH_SHA256:
        raise PatchError("The IPS file is missing, changed, or damaged")

    output, record_count = apply_ips(source, patch)
    if len(output) != OUTPUT_SIZE or sha256(output) != OUTPUT_SHA256:
        raise PatchError("Patched ROM does not match the verified Polish v1.0 build")

    try:
        with output_path.open("xb") as stream:
            stream.write(output)
    except Exception:
        if output_path.exists():
            output_path.unlink()
        raise

    print(f"Created: {output_path}")
    print(f"IPS records applied: {record_count}")
    print(f"SHA-256: {OUTPUT_SHA256}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, PatchError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
