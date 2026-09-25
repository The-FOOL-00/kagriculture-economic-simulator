# V32 P2 ARCHITECTURE (frozen a1, hash `c8977778…`)

Machine-readable: `V32_P2_ARCHITECTURE.json`. Code: `v32/p2/`.
Tests: `tests/test_v32_p2.py` (T1–T11 + features + models).

## 1. Simulator-grounded action interface (the one forced adaptation)

The kaggriculture 1.32.7 simulator exposes NO legal-action enumeration API:
invalid actions are silent no-ops (`_apply_unit_action`, `_parse_order`).
A step requires a JOINT action — farmer op + per-hand ops (0–14 observed)
+ market order list (0–10). Atomic enumeration of the joint action is
combinatorially infeasible, so the locked pointer head is applied
PER-SLOT, with all slots sampling independently in parallel given the
state. This is NOT autoregressive (§32): there is no conditional chain
(type→target→qty), no sequential patching, no conditional masking. It is
the minimal faithful mapping of "one atomic candidate" onto a
multi-effector simulator, and matches the validated V32 factorized-head
precedent (`V32_ACTION_ENCODER_SPEC.md`) with pointer scoring instead of
fixed classifiers.

- Unit slots (farmer + each actual hand): shared head, 101 candidates.
- Market slots (M=10 = env `maxMarketOrdersPerTurn`): per-slot query
  (state + learned slot embedding), 1466 candidates each. NO-OP emits `[]`
  (interior `[]` preserved: race-slot alignment; trailing `[]` stripped).
- Joint logprob/entropy = sums over slots (valid units only).

## 2. Locked tables

| Component | Spec |
| :--- | :--- |
| State features | Groups A–D, 157 dims, `v32p2feat-v1` |
| Temporal windows | 1 / 8 / 32 / 128 steps + validity masks |
| Normalizer | TRAIN-only, frozen `d2a41ab7…`, clip ±8 |
| Trunk | 157→256→256→256, Tanh, shared actor/critic |
| Candidate encoder | op-emb 16 + item-emb 8 + 3 scalars → 128 → Tanh → 256 |
| Queries/keys | 256; logit = q·k/√256 |
| Critic | shared h → 256 → Tanh → scalar V(s) |
| Masking | PLANT_c iff seeds[c]==0 only; −1e9; market unmasked (clamps) |
| Total params | 545,705 |

## 3. Guarantees (tested)

T1 zero-probability illegal; T2 normalization; T3 permutation invariance;
T4 single-action determinism; T5 exact execution identity (live env steps);
T6 rollout/update parity via regen-from-state + identity hashes; T7 padding
invariance; T8 serialization determinism; T9 count safety (hands ≤ 16
assert-cap, market ≤ 10 by construction); T10 state-independent candidate
encodings (no future/oracle fields); T11 100% expert-action exact mapping
(172,560 steps, 0 misses).

## 4. P2 outcome note (STOP at §29 BC gate)

The frozen a1 head is semantically EXACT (all tests pass) but
optimization-infeasible: content-shared keys collapse (41,800 market
pairs at cosine > 0.99) and bilinear scoring fits 50–100× slower than a
linear control (55% vs 100% at ep300/75 on 400 samples). Proposed a1.1
(log-scaled qty) was tested, made collapse worse, and REVERTED — the
frozen hash above is stable. Any head change needs a NEW authorized
phase (`V32_P2_DECISION_REPORT.md` §4). No PPO run was launched.
