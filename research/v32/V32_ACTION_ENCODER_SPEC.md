# V32 ACTION ENCODER SPEC (v1, 2026-09-22)

Grounded in the engine action schema used by every expert:
`action = {farmer: [OP, ...args], hands: [[OP, ...args]...], market: [[OP, PRODUCT, QTY]...]}`.
See also `PHASE021_ACTION_SPACE_AUDIT.md` for the full audit.

## 1. Design decision: factorized + masked, never flat-vocabulary

A flat vocabulary over all (unit × op × target × qty) combinations is
astronomical and mostly illegal. V32 uses a factorized head:

1. `farmer_op`: opcode class over ~14 farmer ops (PASS/HIRE/PLANT/WATER/DIG/
   WEED/COLLECT/FERTILIZE/SELL-side moves/BUY_*/...; exact list frozen in
   `scripts/v32_encoder.py::FARMER_OPS` from the action-space audit).
2. `farmer_arg`: small discrete arg (target position bucket / product id /
   qty bucket) conditioned on op; illegal combos masked.
3. `hands_op`: shared per-hand opcode head (same classes), applied to each
   hand slot (max hands H=12 observed; pad + mask).
4. `market_orders`: autoregressive up to M=8 orders × (op × product × qty-bucket);
   order slots beyond the expert's count are NO-OP (masked in loss).

Legal-action masking is MANDATORY: the policy may only score actions the
environment would accept. Mask source = engine legality where exposed,
else the expert-demonstrated legality envelope (opcodes × observed arg ranges
per state-cluster). `test_v32_legal_mask` asserts zero illegal commits over a
DEV-cohort rollout.

## 2. Imitation targets (EXP-2)

From expert trajectories: (farmer_op, farmer_arg, hands_op[H], market[M]).
Loss = sum of masked cross-entropies. Report per-head accuracy + FULL-ACTION
exact-match (all heads jointly correct) — the honest metric; per-head accuracy
alone overstates BC quality.

## 3. RL action interface (EXP-3+)

PPO samples from the same factorized distribution (masked sampling). Logprob =
sum of head logprobs. Entropy = sum of head entropies (monitored for §24
mode-collapse detection). Deterministic eval = per-head argmax.

## 4. Router fallback (no per-step action prediction)

The §35 router predicts `expert_id ∈ {E0..E8}` per DECISION POINT (macro tick:
every 12 steps + step 0), not per step. Between ticks the selected frozen
expert controls. Router loss = cross-entropy vs simulator-derived labels
(counterfactual winner per tick, computed offline on TRAIN). This keeps the
fallback's output space tiny (≤9 classes) and fully legal by construction.

## 5. Qty buckets

Market/buy quantities bucket to {1,2,5,7,10,15,20,30,50,100+} (covers observed
wash sizes 5/7/10/15/20/30/50/72-shape). Exact-qty regression is explicitly
out of scope for the feasibility milestone.
