#!/usr/bin/env python3
"""Build the reproducible Spartan X 2 Polish Translation v1.1 release."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import zlib
import zipfile


RELEASE = "v1.1"
ARCHIVE_NAME = "4681-SpartanX2.zip"
OLD_ARCHIVE_SHA256 = "694066c8919c90218cd83cfa8f4f6b6689f7caa8f57dd01456b70f8b1cb4ebc1"

SOURCE = {
    "filename": "Spartan X 2 (Japan).nes",
    "size": 262_160,
    "sha256": "386dd9ba05980b8097dcb6289519ef22cbf41d25dab24289e504bbea2c35f665",
    "sha1": "4aee1b4ba1037c9fa8139d4f620cb3c4daa473bd",
    "md5": "e8051bec80c0f1a38b64200431cd77ec",
    "crc32": "09825979",
    "headerless_md5": "9c460fde3896233ff9cb9b833d2fa78d",
    "header": "4e45531a081010400000000000000000",
}

VARIANTS = {
    "ntsc": {
        "label": "NTSC / Famicom",
        "patch_filename": "Spartan X 2 (Japan) (Pl) (v1.0) (villainser).ips",
        "patch_size": 9_804,
        "patch_sha256": "b4595d124464afea49ad2c1af0f3487758e719c9bbf0781af9fa6eb4c980c3ed",
        "record_count": 459,
        "output_filename": "Spartan X 2 (Polish v1.0) [NTSC].nes",
        "output_size": 262_160,
        "output_sha256": "0ff1f7a035b845fa853f3f4c14d0305b9c5bf3d3e1aaf894d9dc297631e89ae0",
        "output_sha1": "54134a5cb63572b5d82819bcb76208dc4a7f2e56",
        "output_md5": "8c3089b49c9da41149a2bf64ddbab31c",
        "output_crc32": "acfcee90",
        "output_headerless_md5": "107cdf1bf7bd4a8e97ffb273f38ef443",
        "output_header": "4e45531a081010400000000000000000",
        "timing": "NTSC / Famicom (60 Hz)",
    },
    "dendy": {
        "label": "Dendy 50 Hz",
        "patch_filename": (
            "Spartan X 2 (Japan) (Pl) (v1.0) (villainser) [Dendy 50Hz].ips"
        ),
        "patch_size": 10_035,
        "patch_sha256": "008a5b15cec2e8ca49d933cc53ddcf244f68c4d05f146de9cee1fa649c5d6cdf",
        "record_count": 463,
        "output_filename": "Spartan X 2 (Polish v1.0) [Dendy 50Hz].nes",
        "output_size": 262_160,
        "output_sha256": "8e6013b39b053cda73a02f06340147a7e9e2dc05c375f81e4d15219cd6df27dc",
        "output_sha1": "480e7c66efd581fe41d07f775353d3d8ded7325c",
        "output_md5": "c467b1dfa1595124fa6916b81cdf5d90",
        "output_crc32": "7e089d24",
        "output_headerless_md5": "37faa789aceb89c09f3af34fef1b3831",
        "output_header": "4e45531a081010480000000003000000",
        "timing": "Dendy (50 Hz frames with Dendy CPU timing)",
    },
    "pal": {
        "label": "PAL 50 Hz",
        "patch_filename": (
            "Spartan X 2 (Japan) (Pl) (v1.0) (villainser) [PAL 50Hz].ips"
        ),
        "patch_size": 10_796,
        "patch_sha256": "54f63cda530f7f47703c336d145265b6d3343de7b19974ad0010919d93bbd899",
        "record_count": 503,
        "output_filename": "Spartan X 2 (Polish v1.0) [PAL 50Hz].nes",
        "output_size": 262_160,
        "output_sha256": "6d4c7ad650f0bce376291defd9609df103fa9db0e9bd897771bc095e6a02b866",
        "output_sha1": "d9e203532a1196b73d72d797c6a7c788061cd435",
        "output_md5": "b6643d3dedaaf64f9b9ff9731c787456",
        "output_crc32": "8ba7a69f",
        "output_headerless_md5": "58c0253a199354933ac5be099a922633",
        "output_header": "4e45531a081010480000000001000000",
        "timing": "PAL (50 Hz)",
    },
}

PRG_START = 16
PRG_SIZE = 128 * 1024
CHR_START = PRG_START + PRG_SIZE
CHR_SIZE = 128 * 1024


class BuildError(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def metadata(data: bytes) -> dict[str, object]:
    return {
        "size": len(data),
        "sha256": sha256(data),
        "sha1": hashlib.sha1(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),
        "crc32": f"{zlib.crc32(data) & 0xFFFFFFFF:08x}",
        "headerless_md5": hashlib.md5(data[16:]).hexdigest(),
        "header": data[:16].hex(),
    }


def verify_image(path: Path, expected: dict[str, object], label: str) -> bytes:
    data = path.read_bytes()
    actual = metadata(data)
    for field in (
        "size",
        "sha256",
        "sha1",
        "md5",
        "crc32",
        "headerless_md5",
        "header",
    ):
        expected_value = expected.get(field)
        if expected_value is not None and actual[field] != expected_value:
            raise BuildError(
                f"Wrong {label} {field}: expected {expected_value}, got {actual[field]}"
            )
    if data[:4] != b"NES\x1a":
        raise BuildError(f"{label} is not an iNES/NES 2.0 image")
    return data


def diff_records(source: bytes, output: bytes) -> list[tuple[int, bytes]]:
    if len(source) != len(output):
        raise BuildError("IPS release variants must be length-preserving")
    records: list[tuple[int, bytes]] = []
    position = 0
    while position < len(source):
        if source[position] == output[position]:
            position += 1
            continue
        start = position
        while (
            position < len(source)
            and source[position] != output[position]
            and position - start < 0xFFFF
        ):
            position += 1
        records.append((start, output[start:position]))
    return records


def make_ips(records: list[tuple[int, bytes]]) -> bytes:
    patch = bytearray(b"PATCH")
    for offset, replacement in records:
        if offset >= 0x1000000:
            raise BuildError("IPS offset exceeds 24-bit range")
        patch.extend(offset.to_bytes(3, "big"))
        patch.extend(len(replacement).to_bytes(2, "big"))
        patch.extend(replacement)
    patch.extend(b"EOF")
    return bytes(patch)


def apply_generated_ips(source: bytes, patch: bytes) -> tuple[bytes, int]:
    if not patch.startswith(b"PATCH"):
        raise BuildError("Generated patch has no IPS header")
    output = bytearray(source)
    position = 5
    count = 0
    while True:
        marker = patch[position : position + 3]
        if marker == b"EOF":
            position += 3
            break
        if len(marker) != 3:
            raise BuildError("Generated patch is truncated")
        offset = int.from_bytes(marker, "big")
        position += 3
        length = int.from_bytes(patch[position : position + 2], "big")
        position += 2
        if length == 0:
            raise BuildError("Release generator does not emit IPS RLE records")
        replacement = patch[position : position + length]
        if len(replacement) != length or offset + length > len(output):
            raise BuildError("Generated patch record is invalid")
        position += length
        output[offset : offset + length] = replacement
        count += 1
    if position != len(patch):
        raise BuildError("Generated patch contains trailing bytes")
    return bytes(output), count


def hex_range(start: int, end: int, width: int = 5) -> list[str]:
    return [f"0x{start:0{width}X}", f"0x{end:0{width}X}"]


def manifest_record(
    order: int, offset: int, replacement: bytes, source: bytes
) -> dict[str, object]:
    end = offset + len(replacement)
    record: dict[str, object] = {
        "application_order": order,
        "operation": "replace",
        "coordinate_frame": (
            "authenticated Japanese source to named output; complete-file offsets "
            "are zero-based and ranges are half-open"
        ),
        "input_range": [offset, end],
        "output_range": [offset, end],
        "file_range_hex": hex_range(offset, end),
        "expected_bytes": source[offset:end].hex(" "),
        "new_bytes": replacement.hex(" "),
        "intent": "reconstruct the complete named regional output",
    }

    if end <= PRG_START:
        record.update(
            {
                "physical_payload": "container header",
                "payload_offset_range": [offset, end],
                "physical_bank": "N/A: container header is not banked",
                "cpu_ppu_address": "N/A: parsed before cartridge mapping",
                "mapping_tuple": "N/A: static container metadata",
            }
        )
        return record

    if offset >= PRG_START and end <= CHR_START:
        payload_start = offset - PRG_START
        payload_end = end - PRG_START
        bank = payload_start // 0x2000
        bank_end = (payload_end - 1) // 0x2000
        if bank != bank_end:
            raise BuildError("PRG manifest record crosses an 8 KiB bank")
        bank_offset = payload_start % 0x2000
        bank_offset_end = bank_offset + len(replacement)
        record.update(
            {
                "physical_payload": "PRG-ROM",
                "payload_offset_range": [payload_start, payload_end],
                "physical_prg_bank": bank,
                "physical_bank_unit_bytes": 0x2000,
                "physical_bank_numbering": "zero-based physical 8 KiB PRG-ROM banks",
                "physical_bank_offset_range": [bank_offset, bank_offset_end],
                "runtime_cycle_frame": (
                    "N/A for static replacement; visibility depends on mapper state"
                ),
            }
        )
        if bank < 14:
            record.update(
                {
                    "cpu_address_range": "N/A without a selected switchable slot",
                    "cpu_windows": [
                        {
                            "slot": 0,
                            "select_register": "0x8000",
                            "cpu_address_range": [
                                0x8000 + bank_offset,
                                0x8000 + bank_offset_end,
                            ],
                        },
                        {
                            "slot": 1,
                            "select_register": "0xA000",
                            "cpu_address_range": [
                                0xA000 + bank_offset,
                                0xA000 + bank_offset_end,
                            ],
                        },
                    ],
                    "mapping_tuple": (
                        "Mapper 65 / Irem H3001, PRG mode 0: write the physical "
                        f"8 KiB bank number {bank} to $8000 or $A000"
                    ),
                }
            )
        else:
            cpu_start = (0xC000 if bank == 14 else 0xE000) + bank_offset
            record.update(
                {
                    "cpu_address_range": [cpu_start, cpu_start + len(replacement)],
                    "mapping_tuple": (
                        "Mapper 65 / Irem H3001, PRG mode 0: physical banks 14 "
                        "and 15 are fixed at $C000 and $E000"
                    ),
                }
            )
        return record

    if offset >= CHR_START and end <= CHR_START + CHR_SIZE:
        payload_start = offset - CHR_START
        payload_end = end - CHR_START
        bank = payload_start // 0x400
        bank_end = (payload_end - 1) // 0x400
        if bank != bank_end:
            raise BuildError("CHR manifest record crosses a 1 KiB bank")
        bank_offset = payload_start % 0x400
        record.update(
            {
                "physical_payload": "CHR-ROM",
                "payload_offset_range": [payload_start, payload_end],
                "physical_chr_bank": bank,
                "physical_bank_unit_bytes": 0x400,
                "physical_bank_numbering": "zero-based physical 1 KiB CHR-ROM banks",
                "physical_bank_offset_range": [
                    bank_offset,
                    bank_offset + len(replacement),
                ],
                "cpu_address": "N/A: CHR-ROM is mapped into PPU address space",
                "ppu_address": "N/A without a selected 1 KiB PPU slot",
                "mapping_tuple": (
                    "Mapper 65 / Irem H3001: write the physical CHR bank number "
                    f"{bank} to $B000+slot, where slot is 0..7"
                ),
                "runtime_cycle_frame": (
                    "N/A for static replacement; visibility requires the named CHR slot"
                ),
            }
        )
        return record

    raise BuildError("Manifest record crosses a container payload boundary")


def write_generated(path: Path, data: bytes, check: bool) -> None:
    if check:
        if not path.exists() or path.read_bytes() != data:
            raise BuildError(f"Generated artifact mismatch: {path}")
        return
    if path.exists():
        if path.read_bytes() != data:
            raise BuildError(f"Refusing to overwrite changed artifact: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def build_readme() -> str:
    lines = [
        "Spartan X 2 - Polish Translation v1.1",
        "Patch author: villainser",
        "",
        "This archive contains translation patches only. It does not contain a ROM image.",
        "",
        "Choose exactly one complete regional variant and use the matching emulator mode:",
        "  ntsc  - NTSC / Famicom (60 Hz)",
        "  dendy - Dendy (50 Hz)",
        "  pal   - PAL (50 Hz)",
        "",
        "All three patches require the same clean source:",
        f"  {SOURCE['filename']}",
        f"  Size: {SOURCE['size']} bytes",
        f"  MD5: {str(SOURCE['md5']).upper()}",
        f"  CRC32: {str(SOURCE['crc32']).upper()}",
        f"  SHA-256: {str(SOURCE['sha256']).upper()}",
        f"  RetroAchievements headerless MD5: {str(SOURCE['headerless_md5']).upper()}",
        "",
        "Recommended application commands:",
        "  python3 apply_patch.py --region ntsc  \"/path/to/Spartan X 2 (Japan).nes\"",
        "  python3 apply_patch.py --region dendy \"/path/to/Spartan X 2 (Japan).nes\"",
        "  python3 apply_patch.py --region pal   \"/path/to/Spartan X 2 (Japan).nes\"",
        "",
        "The script verifies the source ROM, selected IPS, output size, output header",
        "and output SHA-256 before creating the file. It never overwrites the source",
        "or an existing output file.",
        "",
        "Verified variants:",
    ]
    for key, variant in VARIANTS.items():
        lines.extend(
            [
                "",
                f"[{key}] {variant['label']}",
                f"Patch: {variant['patch_filename']}",
                f"Patch size: {variant['patch_size']} bytes",
                f"Patch SHA-256: {str(variant['patch_sha256']).upper()}",
                f"Output: {variant['output_filename']}",
                f"Output size: {variant['output_size']} bytes",
                f"Output MD5: {str(variant['output_md5']).upper()}",
                f"Output CRC32: {str(variant['output_crc32']).upper()}",
                f"Output SHA-256: {str(variant['output_sha256']).upper()}",
                (
                    "RetroAchievements headerless MD5: "
                    f"{str(variant['output_headerless_md5']).upper()}"
                ),
            ]
        )
    lines.extend(
        [
            "",
            "A standard IPS patcher may also be used, but IPS does not authenticate its",
            "source. Verify the source and output checksums manually in that workflow.",
            "",
            "Credits:",
            "Polish translation and patch: villainser",
            "English translation, hacking, and graphics: Occluded Hairdo",
            "Additional hacking: Parasyte",
            "Original English translation group: Abstract Crouton Productions",
            "",
            "The Polish release builds on the work of the English translation project.",
            "",
        ]
    )
    return "\n".join(lines)


def build_checksums() -> str:
    lines = [
        "SHA-256 checksums",
        "",
        "Required source (not included):",
        f"{SOURCE['sha256']}  {SOURCE['filename']}",
        "",
        "Included patches:",
    ]
    for variant in VARIANTS.values():
        lines.append(f"{variant['patch_sha256']}  {variant['patch_filename']}")
    lines.extend(["", "Expected outputs (not included):"])
    for variant in VARIANTS.values():
        lines.append(f"{variant['output_sha256']}  {variant['output_filename']}")
    lines.append("")
    return "\n".join(lines)


def deterministic_zip(files: list[tuple[str, bytes]]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(
        buffer, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for name, data in files:
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--ntsc", type=Path, required=True, help="verified NTSC output")
    parser.add_argument("--dendy", type=Path, required=True, help="verified Dendy output")
    parser.add_argument("--pal", type=Path, required=True, help="verified PAL output")
    parser.add_argument(
        "--check", action="store_true", help="verify existing artifacts without writing"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source = verify_image(args.source.resolve(), SOURCE, "source")
    target_paths = {"ntsc": args.ntsc, "dendy": args.dendy, "pal": args.pal}
    patch_bytes: dict[str, bytes] = {}
    manifest_variants: dict[str, object] = {}

    for key, target_path in target_paths.items():
        variant = VARIANTS[key]
        expected = {
            "size": variant["output_size"],
            "sha256": variant["output_sha256"],
            "sha1": variant["output_sha1"],
            "md5": variant["output_md5"],
            "crc32": variant["output_crc32"],
            "headerless_md5": variant["output_headerless_md5"],
            "header": variant["output_header"],
        }
        output = verify_image(target_path.resolve(), expected, f"{key} output")
        records = diff_records(source, output)
        patch = make_ips(records)
        reapplied, applied_count = apply_generated_ips(source, patch)
        if reapplied != output:
            raise BuildError(f"Fresh IPS reapplication mismatch for {key}")
        if (
            len(patch) != variant["patch_size"]
            or sha256(patch) != variant["patch_sha256"]
            or len(records) != variant["record_count"]
            or applied_count != variant["record_count"]
        ):
            raise BuildError(f"Generated IPS identity mismatch for {key}")
        patch_bytes[key] = patch
        manifest_variants[key] = {
            "label": variant["label"],
            "timing": variant["timing"],
            "patch": {
                "filename": variant["patch_filename"],
                "format": "IPS",
                "size": len(patch),
                "sha256": sha256(patch),
                "record_count": len(records),
                "changed_byte_count": sum(len(data) for _, data in records),
            },
            "output": {
                "filename": variant["output_filename"],
                **metadata(output),
            },
            "operations": [
                manifest_record(index, offset, data, source)
                for index, (offset, data) in enumerate(records, start=1)
            ],
        }

    manifest = {
        "schema": "spartan-x2-source-bound-ips-manifest-v1",
        "release": RELEASE,
        "source": SOURCE,
        "container": {
            "source_format": "legacy iNES",
            "mapper": 65,
            "trainer": False,
            "prg_rom_bytes": PRG_SIZE,
            "chr_rom_bytes": CHR_SIZE,
            "trailing_bytes": 0,
        },
        "variants": manifest_variants,
        "validation": {
            "serialized_patch_reapplication": "passed for all variants",
            "result": "each reapplied output is byte-identical to its validated target",
            "source_authentication": "enforced by apply_patch.py before output creation",
            "patch_authentication": "per-variant SHA-256 enforced by apply_patch.py",
            "output_authentication": "size, header, and SHA-256 enforced before write",
        },
        "distribution": "IPS patches and verification metadata only; no ROM image",
    }
    manifest_bytes = (json.dumps(manifest, indent=2, ensure_ascii=True) + "\n").encode()
    checksums_bytes = build_checksums().encode()

    for key, variant in VARIANTS.items():
        write_generated(
            repo_root / str(variant["patch_filename"]), patch_bytes[key], args.check
        )
    write_generated(repo_root / "PATCH_MANIFEST.json", manifest_bytes, args.check)
    write_generated(repo_root / "CHECKSUMS.txt", checksums_bytes, args.check)

    archive_files = [
        (str(VARIANTS[key]["patch_filename"]), patch_bytes[key])
        for key in ("ntsc", "dendy", "pal")
    ]
    archive_files.extend(
        [
            ("apply_patch.py", (repo_root / "apply_patch.py").read_bytes()),
            ("readme.txt", build_readme().encode()),
            ("CHECKSUMS.txt", checksums_bytes),
            ("PATCH_MANIFEST.json", manifest_bytes),
        ]
    )
    archive_bytes = deterministic_zip(archive_files)
    archive_path = repo_root / "dist" / ARCHIVE_NAME
    if args.check:
        if not archive_path.exists() or archive_path.read_bytes() != archive_bytes:
            raise BuildError(f"Generated artifact mismatch: {archive_path}")
    else:
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        if archive_path.exists() and archive_path.read_bytes() != archive_bytes:
            old_hash = sha256(archive_path.read_bytes())
            if old_hash != OLD_ARCHIVE_SHA256:
                raise BuildError(
                    f"Refusing to replace unknown release archive: {archive_path}"
                )
        archive_path.write_bytes(archive_bytes)

    print(f"Release: {RELEASE}")
    for key in ("ntsc", "dendy", "pal"):
        variant = VARIANTS[key]
        print(
            f"{key}: {variant['patch_size']} bytes, "
            f"{variant['patch_sha256']}, {variant['record_count']} records"
        )
    print(f"archive: {len(archive_bytes)} bytes, {sha256(archive_bytes)}")
    print("mode: check" if args.check else "mode: build")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (BuildError, OSError) as error:
        print(f"ERROR: {error}")
        raise SystemExit(2)
