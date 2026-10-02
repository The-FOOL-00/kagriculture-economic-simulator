# V32 ROUTER SPEC — R1 meta-policy over deterministic experts (2026-09-22)

Companion docs: `V32_P1_FORENSICS.md` (evidence), `V32_ROUTER_SPLITS.json`
(seeds), `V32_R1_PREREGISTRATION.md` (predictions + gate, hashed before
TEST/LOCKED outcomes are viewed). Dataset doc: `V32_ROUTER_DATASET.md`.

## 1. Architecture

```
OBSERVATION (legal public channels only)
  Regime A+ID: opponent identity (known-opponent setting, diagnostic static)
  Regime B:    24-step V3-opening prefix (obs stack + price/cash deltas)
                     |
              ROUTER (logistic / compact MLP, torch CPU, deterministic)
                     |
          expert probability vector over 5 classes
                     |
              selected expert (argmax, ties -> fixed order)
                     |
   B1 (diagnostic): fresh full episode  |  B2 (deployable): continuation
```

Router classes (frozen, immutable): E0_V3, E2_A7, E3_V25P3, E6_W72,
E7_W2015. Excluded with reason (P1 §7.1): A1/A2 dispatch lanes
(redundant/dead), DMITRII as class (weak lane; kept as opponent), V22R1
(eval-only cost + P1-F11 asymmetry; small opponent probe only).

## 2. Regimes (from P1 §6 information boundary)

- A (state-only pre-episode): PROVABLY CONSTANT (P1-F10). Implemented as
  the global best-fixed baseline + constancy test. No model.
- A+ID (opponent identity, static): diagnostic. Captures <= the
  opponent-driven half of the oracle gap (~47%, P1-F7). Deployable only
  with a known opponent.
- B1 (prefix-informed choice of a FRESH full episode): diagnostic upper
  bound for the value of early information. NOT deployable (no rewind).
  Free offline (prefixes from V3 legs + labels from full legs).
- B2 (V3 opens 24 steps, routed expert CONTINUES from step 24):
  the deployable candidate. Labels from true continuation legs.
- C (periodic re-routing): deferred (P1 §6).

Prefix N=24 (1 day, inside the 0-59 opening phase). Handoff: fresh
adapter instance at step 24 (coherent by construction — tape-indexed,
step-0 logic keyed off `obs['step']`; continuation-vs-full equivalence
is diagnostic, never assumed).

## 3. Opponent panel and family holdout

Panel (6): E0_V3, E2_A7, E3_V25P3, E6_W72, E7_W2015, E8_DMITRII.
Primary split trains on all 6. Secondary robustness split retrains
without wash-micro opponents {W72, W2015} and evaluates on them unseen.
Self-play legs (class vs class) complete the oracle (EXP-1 lacks them).

## 4. Targets (labels from completed rollouts only)

- TARGET A (primary): best expert by terminal own-cash. Epsilon band
  $500: admissible set = all classes within $500 of max (P1-F7 flat rows
  must not invent winners). Primary loss: cross-entropy vs
  uniform-over-admissible (soft). Hard top-1 accuracy reported.
- TARGET B: best by W/L (win-score, tie-break by cash). Separate head;
  F5 proves A and B disagree (vs W2015: W72 wins at $92k, V3 loses
  at $110k).
- TARGET C: softmax over cash with fixed temperature T=$2000, KL loss.
  Secondary formulation comparison.

## 5. Features (legal public channels only; never seed IDs, never future)

- A+ID: opponent one-hot (6) + seat (1) = 7 dims. (State excluded: constant.)
- B: frame stack of v32enc-v1.1 encodings at t in {0,12,24} (stack ablation:
  none={24}: 90; short={12,24}: 180; longer={0,12,24}: 270) PLUS a fixed
  23-dim prefix summary: own/opp cash at t=24 + deltas vs t=0 (4),
  all-product price deltas t=24 vs t=0 (9), wheat price t=0,4,...,24 (7),
  market inventory delta wheat (1), hires/fertilize counts prefix (2).
  Dims: 113 / 203 / 293.
- Normalization: TRAIN-only mean/std, frozen before VAL/TEST/LOCKED.

## 6. Models (exact widths; counts reported per config at train time)

- M0 global best-fixed (TRAIN mean cash). M1 per-opponent best-fixed
  lookup (TRAIN fit). Baselines, not learned.
- M2 multinomial logistic on A+ID (7 -> 5). Must ~= M1 (pipeline sanity).
- M3 R1-small MLP on B features, B1 labels (diagnostic).
- M4 R1-small MLP on B features, B2 labels. PRIMARY CANDIDATE.
- M5 R1-medium MLP on B features, B2 labels (capacity check).
- M6 shuffled-label control on M4 config (must collapse to <= baseline).
- R1-small: d -> 64 -> ReLU -> 32 -> ReLU -> 5.
  R1-medium: d -> 128 -> ReLU -> 64 -> ReLU -> 32 -> ReLU -> 5.
- MODEL C multi-task (expert + cash + winprob heads) as secondary on M4
  config only. No Transformer, no large sweep (brief §9).

## 7. Training protocol

Full-batch Adam, lr=1e-3, weight-decay=1e-2, <=2000 epochs, VAL early-stop
(patience 200 on VAL soft-CE). Two training seeds for M4/M5. Deterministic:
torch manual seed, deterministic algorithms, fixed row order; inference
argmax (temperature 0). Every run records brief §20 provenance
(commit, hashes, config, wall time, hardware).

## 8. Metrics (evaluate.py; rows = (seed, opponent), seeds = sample unit)

Per row: selected expert, own cash, win/T/loss, regret vs oracle-cash,
normalized regret vs A7. Aggregates: mean/median cash, W/L/T, mean/median
regret, 95% seed-bootstrap CI, worst 5%, catastrophic count (row cash
< A7 same-row cash - $25k), seed-positive fraction (mean over opponents
per seed > A7). Baselines on every eval: always-A7, always-best-fixed,
always-W72, seeded random, oracle-cash, oracle-W/L, M1 lookup.

## 9. Leakage and determinism rules (enforced by tests)

- No seed IDs / replay IDs / future rewards / opponent-private fields in
  features (encoder-audited + router-level test).
- Prefix features for a row come ONLY from that row's V3 opening leg.
- Splits by seed; LOCKED legs run once, after the prereg hash, opened once.
- Expert code immutable (digest-asserted at runner startup, recorded per leg).
- Router inference deterministic: same input -> same expert, rerun-equal.
