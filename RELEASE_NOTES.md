# Spartan X 2 — Polish Translation v1.1

Release v1.1 adds complete Dendy and PAL editions alongside the existing NTSC
translation. All three IPS patches use the same clean Japanese ROM as their
source. No ROM image is included.

## What changed

- Added a Dendy build with native 50 Hz audio and Dendy CPU timing.
- Added a PAL build with native PAL 50 Hz timing.
- Corrected the cadence-dependent transition deadlock that could stop the game
  while Spartan entered the train.
- Gated subsequent synthetic 50 Hz gameplay ticks while a transition or
  published PPU-queue state is active.
- Extended `apply_patch.py` with explicit `ntsc`, `dendy` and `pal` selection,
  per-variant IPS/output authentication, and strict regional header checks.
- Added complete patch coordinates and checksums to `PATCH_MANIFEST.json`.

The NTSC output is unchanged from v1.0 and remains byte-identical with SHA-256
`0ff1f7a035b845fa853f3f4c14d0305b9c5bf3d3e1aaf894d9dc297631e89ae0`.

## Required source

```text
Size:    262160 bytes
SHA-256: 386dd9ba05980b8097dcb6289519ef22cbf41d25dab24289e504bbea2c35f665
```

Release archive SHA-256:
`09d332f881848de13c4574f8b864cac76568d746e6d4881f85253ecfb078eaa9`

Use the ROM variant that matches the selected emulator region. Save states are
not intended to be moved between variants.
