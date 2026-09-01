# Spartan X 2 — Polish translation

This repository contains Polish translation patches for the Japanese Famicom
release of *Spartan X 2*. Release v1.1 provides three complete regional
variants: NTSC, Dendy and PAL.

No ROM image is included. You must provide your own copy of the game.

## Download

Download `4681-SpartanX2.zip` from the
[latest release](https://github.com/villainser/spartan-x-2-polish-translation/releases/latest).
The archive contains:

- three IPS patches, one for each supported region;
- `apply_patch.py`, which authenticates the source, selected patch and output;
- `CHECKSUMS.txt`;
- `PATCH_MANIFEST.json`, with complete source/output identities and patch
  coordinates.

Release v1.1 adds the regional builds and packaging. The translation payload
remains v1.0, so the patch and output filenames retain that version.

## Required ROM

All variants use the same clean No-Intro dump:

```text
Spartan X 2 (Japan).nes
Size:    262160 bytes
MD5:     E8051BEC80C0F1A38B64200431CD77EC
CRC32:   09825979
SHA-256: 386DD9BA05980B8097DCB6289519EF22CBF41D25DAB24289E504BBEA2C35F665
```

The English translation and other dumps or revisions are not valid source
files for these patches.

## Choose a regional variant

Apply exactly one patch and select the matching region in your emulator or
core.

| `--region` | Emulator setting | Intended timing |
| --- | --- | --- |
| `ntsc` | NTSC or Famicom | Original 60 Hz timing |
| `dendy` | Dendy | 50 Hz frames with Dendy CPU timing |
| `pal` | PAL | PAL 50 Hz timing |

Do not force a different region after choosing a patch. Save states should
also remain with the exact ROM variant that created them.

Use the Dendy patch only when the emulator or core exposes an explicit Dendy
mode, and use the PAL patch only in PAL mode. Otherwise choose the NTSC patch
with NTSC or Famicom mode.

## Applying a patch

Extract the release archive and run one of these commands:

```bash
python3 apply_patch.py --region ntsc "/path/to/Spartan X 2 (Japan).nes"
python3 apply_patch.py --region dendy "/path/to/Spartan X 2 (Japan).nes"
python3 apply_patch.py --region pal "/path/to/Spartan X 2 (Japan).nes"
```

NTSC is the default when `--region` is omitted. Use `-o` to choose a custom
output path.

The script checks the source ROM before loading a patch. It then verifies the
selected IPS, complete output, file size and final header before creating the
ROM. It refuses to overwrite the source or an existing output file.

A standard IPS patcher may also be used, but IPS does not authenticate its
source. Compare the resulting file with the checksums below when using another
patcher.

## Verified files

| Variant | IPS size | IPS SHA-256 | Output SHA-256 |
| --- | ---: | --- | --- |
| NTSC | 9804 bytes | `b4595d124464afea49ad2c1af0f3487758e719c9bbf0781af9fa6eb4c980c3ed` | `0ff1f7a035b845fa853f3f4c14d0305b9c5bf3d3e1aaf894d9dc297631e89ae0` |
| Dendy | 10035 bytes | `008a5b15cec2e8ca49d933cc53ddcf244f68c4d05f146de9cee1fa649c5d6cdf` | `8e6013b39b053cda73a02f06340147a7e9e2dc05c375f81e4d15219cd6df27dc` |
| PAL | 10796 bytes | `54f63cda530f7f47703c336d145265b6d3343de7b19974ad0010919d93bbd899` | `6d4c7ad650f0bce376291defd9609df103fa9db0e9bd897771bc095e6a02b866` |

The NTSC output is byte-identical to v1.0. The Dendy and PAL variants use NES
2.0 timing headers and region-specific 50 Hz scheduling.

Additional MD5, CRC32, SHA-1, headerless MD5 and ordered patch records are in
`PATCH_MANIFEST.json`.

## RetroAchievements

Every regional output has a different headerless MD5. RetroAchievements will
recognize a build only when that exact hash is linked to the
[Spartan X 2 achievement set](https://retroachievements.org/game/4681). Check
the set's supported game hashes before starting an achievement run.

## Credits

- Polish translation and patch: **villainser**
- English translation, hacking, and graphics: **Occluded Hairdo**
- Additional hacking: **Parasyte**
- Original English translation group: **Abstract Crouton Productions**

The Polish release builds on the work of the English translation project.
