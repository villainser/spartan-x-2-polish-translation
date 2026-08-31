#!/usr/bin/env python3
"""Apply a verified Spartan X 2 Polish translation IPS variant."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
from pathlib import Path
import sys


SOURCE_SIZE = 262_160
SOURCE_SHA256 = "386dd9ba05980b8097dcb6289519ef22cbf41d25dab24289e504bbea2c35f665"
SOURCE_HEADER = bytes.fromhex("4e45531a081010400000000000000000")


@dataclass(frozen=True)
class Variant:
    label: str
    patch_name: str
    patch_sha256: str
    output_name: str
    output_size: int
    output_sha256: str
    output_header: bytes
    allowed_header_offsets: frozenset[int]


VARIANTS = {
    "ntsc": Variant(
        label="NTSC / Famicom",
        patch_name="Spartan X 2 (Japan) (Pl) (v1.0) (villainser).ips",
        patch_sha256="b4595d124464afea49ad2c1af0f3487758e719c9bbf0781af9fa6eb4c980c3ed",
        output_name="Spartan X 2 (Polish v1.0) [NTSC].nes",
        output_size=262_160,
        output_sha256="0ff1f7a035b845fa853f3f4c14d0305b9c5bf3d3e1aaf894d9dc297631e89ae0",
        output_header=bytes.fromhex("4e45531a081010400000000000000000"),
        allowed_header_offsets=frozenset(),
    ),
    "dendy": Variant(
        label="Dendy 50 Hz",
        patch_name=(
            "Spartan X 2 (Japan) (Pl) (v1.0) (villainser) [Dendy 50Hz].ips"
        ),
        patch_sha256="008a5b15cec2e8ca49d933cc53ddcf244f68c4d05f146de9cee1fa649c5d6cdf",
        output_name="Spartan X 2 (Polish v1.0) [Dendy 50Hz].nes",
        output_size=262_160,
        output_sha256="8e6013b39b053cda73a02f06340147a7e9e2dc05c375f81e4d15219cd6df27dc",
        output_header=bytes.fromhex("4e45531a081010480000000003000000"),
        allowed_header_offsets=frozenset({7, 12}),
    ),
    "pal": Variant(
        label="PAL 50 Hz",
        patch_name="Spartan X 2 (Japan) (Pl) (v1.0) (villainser) [PAL 50Hz].ips",
        patch_sha256="54f63cda530f7f47703c336d145265b6d3343de7b19974ad0010919d93bbd899",
        output_name="Spartan X 2 (Polish v1.0) [PAL 50Hz].nes",
        output_size=262_160,
        output_sha256="6d4c7ad650f0bce376291defd9609df103fa9db0e9bd897771bc095e6a02b866",
        output_header=bytes.fromhex("4e45531a081010480000000001000000"),
        allowed_header_offsets=frozenset({7, 12}),
    ),
}


class PatchError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def apply_ips(
    source: bytes, patch: bytes, allowed_header_offsets: frozenset[int]
) -> tuple[bytes, int]:
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
        if end > len(output):
            raise PatchError("Patch record exceeds the source ROM size")

        for header_offset in range(offset, min(end, 16)):
            if header_offset not in allowed_header_offsets:
                raise PatchError(
                    f"Patch attempts an unexpected header change at 0x{header_offset:02X}"
                )

        output[offset:end] = replacement
        record_count += 1

    if position != len(patch):
        raise PatchError("Unexpected data after IPS EOF")

    return bytes(output), record_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Apply a verified Spartan X 2 Polish translation patch"
    )
    parser.add_argument("source", type=Path, help="clean No-Intro Japanese ROM")
    parser.add_argument(
        "--region",
        choices=tuple(VARIANTS),
        default="ntsc",
        help="output timing variant (default: ntsc)",
    )
    parser.add_argument("-o", "--output", type=Path, help="output ROM path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    variant = VARIANTS[args.region]
    source_path = args.source.expanduser().resolve()
    output_path = (
        args.output.expanduser().resolve()
        if args.output
        else source_path.with_name(variant.output_name)
    )
    patch_path = Path(__file__).resolve().with_name(variant.patch_name)

    if output_path == source_path:
        raise PatchError("Refusing to overwrite the source ROM")
    if output_path.exists():
        raise PatchError(f"Output already exists: {output_path}")

    source = source_path.read_bytes()
    if (
        len(source) != SOURCE_SIZE
        or sha256(source) != SOURCE_SHA256
        or source[:16] != SOURCE_HEADER
    ):
        raise PatchError(
            "Wrong source ROM. Expected the exact No-Intro Spartan X 2 (Japan).nes "
            f"({SOURCE_SIZE} bytes, SHA-256 {SOURCE_SHA256})."
        )

    patch = patch_path.read_bytes()
    if sha256(patch) != variant.patch_sha256:
        raise PatchError("The selected IPS file is missing, changed, or damaged")

    output, record_count = apply_ips(
        source, patch, variant.allowed_header_offsets
    )
    if (
        len(output) != variant.output_size
        or sha256(output) != variant.output_sha256
        or output[:16] != variant.output_header
    ):
        raise PatchError(
            f"Patched ROM does not match the verified {variant.label} build"
        )

    created = False
    try:
        with output_path.open("xb") as stream:
            created = True
            stream.write(output)
    except Exception:
        if created and output_path.exists():
            output_path.unlink()
        raise

    print(f"Created: {output_path}")
    print(f"Variant: {variant.label}")
    print(f"IPS records applied: {record_count}")
    print(f"SHA-256: {variant.output_sha256}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, PatchError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
