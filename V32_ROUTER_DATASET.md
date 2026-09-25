# V32 ROUTER DATASET (R1) — construction record

Spec: `V32_ROUTER_SPEC.md`. Splits: `V32_ROUTER_SPLITS.json`.
Assembled by `v32/router/dataset.py::load_rows` (no matches; pure join).

## 1. Design

Row = (seed, opponent) with cash/win/margin vectors over the 5 router
classes + the V3-opening prefix (t=0..24 public frames). Two label modes:
- b1 (full): class plays the whole episode (Regime A+ID + B1-diagnostic).
- b2 (cont): V3 opens 24 steps, fresh class-instance continues (B2).

Splits by seed: TRAIN 10 (60 rows/mode), VAL 5 (30), TEST 32 (192),
LOCKED 8 (48, run once after prereg seal, opened once). EXP-1 seeds
(249635-249640) reuse directed EXP-1 legs for b1; b1 self-play, V3
prefixes, and all b2 legs are generated fresh. Canonical seat-0 only
(mirrors verified symmetric 30/30 on fresh TRAIN seeds + 416/416 in
EXP-1 non-V22R1; V22R1 excluded from all grids).

## 2. Source files (counts filled after grid completion)

| File | Content | Legs |
| :--- | :--- | :--- |
| results/v32_exp1.jsonl | b1 legs, TRAIN EXP-1 seeds (existing) | 448 |
| results/v32_router_full_a.jsonl | b1, seeds 249641-249672 | 960 |
| results/v32_router_full_b.jsonl | b1, seeds 249675-249683 | 270 |
| results/v32_router_full_c.jsonl | b1 self-play + V3 prefixes, EXP-1 seeds | 60 |
| results/v32_router_cont_a.jsonl | b2, seeds 249641-249672 | 960 |
| results/v32_router_cont_b.jsonl | b2, seeds 249675-249683 | 270 |
| results/v32_router_cont_c.jsonl | b2, EXP-1 seeds | 180 |
| results/v32_router_full_locked.jsonl | b1, LOCKED 249684-249691 (run once) | 240 |
| results/v32_router_cont_locked.jsonl | b2 LOCKED: SKIPPED (vacuous, Addendum A1) | — |
| results/v32_v22r1_probe.jsonl | {W2015,A7} vs V22R1, TEST 249650-249655 | 24 |

Rows: b1 330 (60/30/192/48), b2 282 (no LOCKED).
Final dataset hash: `6af8fcb5…722410` (`results/v32_router_manifest.json`).
Reproducibility: 30/30 V3 legs reproduce EXP-1 rewards + action digests.

Per-leg provenance: engine 1.32.7, encoder v32enc-v1.1, class/opp/opener
digests, action+money digests, worker nonce, duration. Quarantine:
`check_seed_allowed` per leg; CONFIRM/protected/commissioning refused.

## 3. Manifest

Filled by `scripts/v32_router_dataset_manifest.py` after grids complete:
per-file leg counts, sha256, seed coverage, split row counts, dataset hash.
