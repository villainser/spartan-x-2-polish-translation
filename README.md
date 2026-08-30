# Spartan X 2 — Polish translation

This repository contains the Polish translation patch for the Japanese Famicom release of *Spartan X 2*. The patch is distributed as IPS and must be applied to a clean copy of the Japanese game.

No ROM image is included. You must provide your own copy of the game.

## Download

Download `4681-SpartanX2.zip` from the [latest release](https://github.com/villainser/spartan-x-2-polish-translation/releases/latest). The archive contains:

- the IPS patch;
- `apply_patch.py`, which verifies the source ROM and the resulting file;
- a text file with the required checksums.

## Required ROM

Use the following No-Intro dump:

```text
Spartan X 2 (Japan).nes
Size:    262160 bytes
MD5:     E8051BEC80C0F1A38B64200431CD77EC
CRC32:   09825979
SHA-256: 386DD9BA05980B8097DCB6289519EF22CBF41D25DAB24289E504BBEA2C35F665
```

The English translation and other dumps or revisions are not valid source files for this patch.

## Applying the patch

Extract the release archive, place your ROM in a convenient directory, and run:

```bash
python3 apply_patch.py "/path/to/Spartan X 2 (Japan).nes"
```

The script checks the source ROM and IPS file before writing `Spartan X 2 (Polish v1.0) [PL].nes`. It refuses to overwrite the source or an existing output file.

A standard IPS patcher may also be used, but it will not necessarily verify that you selected the correct source ROM. Compare the resulting file with the output checksums below.

## Verified files

| File | Size | SHA-256 |
| --- | ---: | --- |
| `Spartan X 2 (Japan).nes` | 262160 bytes | `386dd9ba05980b8097dcb6289519ef22cbf41d25dab24289e504bbea2c35f665` |
| `Spartan X 2 (Japan) (Pl) (v1.0) (villainser).ips` | 9804 bytes | `b4595d124464afea49ad2c1af0f3487758e719c9bbf0781af9fa6eb4c980c3ed` |
| `Spartan X 2 (Polish v1.0) [PL].nes` | 262160 bytes | `0ff1f7a035b845fa853f3f4c14d0305b9c5bf3d3e1aaf894d9dc297631e89ae0` |

The expected output has MD5 `8C3089B49C9DA41149A2BF64DDBAB31C`, CRC32 `ACFCEE90`, and RetroAchievements headerless MD5 `107CDF1BF7BD4A8E97FFB273F38EF443`.

## Emulator region

Run the game in NTSC or Famicom mode. PAL and Dendy timing modes are not supported by this release.

## RetroAchievements

The Polish ROM hash has not yet been linked to the [Spartan X 2 achievement set](https://retroachievements.org/game/4681). Full compatibility testing of all 15 achievements will begin only after the set maintainer accepts the hash for player compatibility testing.

## Credits

- Polish translation and patch: **villainser**
- English translation, hacking, and graphics: **Occluded Hairdo**
- Additional hacking: **Parasyte**
- Original English translation group: **Abstract Crouton Productions**

The Polish release builds on the work of the English translation project.
