# V32 STATE ENCODER SPEC (v1, 2026-09-22)

Grounded in the observed 1.32.7 schema (`aec/backbone/utils.py`
`build_simulated_observation`, `scripts/v30_gauntlet.py::telemetry`):
`observation = {step, player, farms[2], private{shed,seeds}, town{unlocked_shops}}`;
`farm = {money, farmer[x,y], hands[], tiles[][], unlocked_quadrants}`.

## 1. Encoder input contract

- ONLY information legally observable at decision time: own `farms[player]`,
  own `private`, shared `town`, `step`, and the OPPONENT-OBSERVABLE subset of
  `farms[1-player]` (see §4). Never hidden RNG, never future states, never
  opponent `private`, never seed IDs, never replay identifiers.
- Encoder is a pure function `encode(observation, player) -> fixed vector`.
  Versioned (`v32enc-v1`); any change bumps the version and invalidates old
  checkpoints' comparability.

## 2. Feature groups (fixed widths, v1)

| Group | Features (count) | Notes |
| :--- | :--- | :--- |
| Global (8) | step/720, day/30, remaining/720, cash/1e5, cash_delta_12, shed_total/1e5, seeds_total/1e3, shops_unlocked/8 | normalized; delta from frame stack |
| Crop (24) | per-crop (WHEAT/CARROT/TOMATO/STRAWBERRY/MELON × planted/growing/ready/yield-proxy) + total_plant/total_tiles | tile scan; yield-proxy = ready × per-crop unit value |
| Livestock (10) | COW/SHEEP/GOOSE counts, feed_req, pasture_tiles, pasture_ratio, milk/wool/egg flow (3), starvation_flag | starvation from V31R2 forensics |
| Workers (8) | n_hands, farmer_xy (2), carrying_frac, task histogram top-4 (hire/water/weed/idle proxies) | no unit IDs (permutation risk) |
| Land (6) | quadrants_unlocked, cultivated, pasture, free_productive, weed_tiles, dry_tiles | tile scan |
| Market (14) | unlocked_shops one-hot-ish (8), sell_pressure, inventory_pressure, price-move sign (3), wash_flag_step0 | prices are NOT directly exposed; use shop + ledger proxies (see §5) |
| Opponent-observable (16) | opp money bucket (4), opp plant/pasture/weed (3), opp hands count (1), opp unlocked_quads (1), opp recent sell-pressure proxy (3), opp livestock proxy (3), opp wash-size bucket (1) | ALL from `farms[1-player]` public fields ONLY |
| Phase (4) | one-hot macro phase: opening (0-59) / mid (60-479) / late (480-659) / terminal (660+) | boundaries from V3 regime analysis |

Total: 90 floats. Frame stack k=4 (current + t-12/24/36) for the Global +
Opponent groups only (keeps width 90 + 3×24 = 162 with stack; exact layout in
`scripts/v32_encoder.py::V32_OBS_DIM`).

## 3. Normalization

Running mean/std per feature over the TRAIN cohort only (frozen before DEV use;
recomputed never mid-run). Clip to [-8, +8]. Bucket features are already 0/1.

## 4. Opponent-observability audit

The encoder test (`test_v32_encoder_leakage`) constructs paired observations
differing ONLY in opponent `private`/hidden fields and asserts byte-identical
encoder output; and differing in opponent public fields asserts output differs
where the §2 opponent group covers it. This is the §51(5) no-leakage gate.

## 5. Known schema gaps (honest)

- CORRECTION 2026-09-22 (live probe, encoder v1.1): `obs['market']` DOES
  expose `{prices, inventory}` × 9 products. The Market group uses real prices
  (9/14 features); the proxy-only design in the v1.0 draft is superseded.
  Leakage re-audit passed (prices are shared-public, not opponent-private).
- Tile-state enums beyond PLANT/PASTURE/WEED (dry/growth stage) are read
  defensively (`.get`, default 0) so schema drift degrades to zeros, loudly
  logged, never crashes.
