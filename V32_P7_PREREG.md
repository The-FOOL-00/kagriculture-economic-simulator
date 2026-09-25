# V32 P7 — PREREGISTRATION DOCUMENT

## 1. PURPOSE & SCIENTIFIC QUESTION

Phase **V32 P7** continues the Kagriculture V32 research program to test whether the
P4→P5→P6 failure pattern — *pointwise per-step loss rebalancing sequentially shifts
the error horizon (Step 0 → Step 2 → Step 3) without repairing economic compounding* —
can be broken by **trajectory-level prefix supervision** instead of another
single-step weight.

The immediate scientific question:

> P4–P6 showed that fixing individual actions merely moves the failure one timestep
> forward. Can a trajectory-level objective teach the policy to preserve a multi-step
> coordinated economic macro, rather than repeatedly solving the next individual action?

## 2. HYPOTHESES

### H1 — TRAJECTORY-LEVEL PREFIX SUPERVISION

The feed-forward BC objective trains each action independently under teacher forcing,
which permits correct per-step actions while failing to preserve the dependency
between them during free-running execution. A trajectory-level prefix objective —
supervising coordinated prefixes (steps 0–4, 0–8, 0–12, 0–24) as units and selecting
on prefix-exact-match and free-running rollout consistency — should reduce early
sequence drift without requiring a recurrent architecture.

### H2 — MACRO-PHASE CONDITIONING

If expert trajectories contain identifiable phase/state transitions derivable from
**observable current state only** (no step labels, no teacher tape, no future
knowledge), explicitly conditioning the policy on a compact phase representation may
stabilize the opening macro beyond what prefix supervision alone achieves.

### H3 — PREFIX SUPERVISION IS SUFFICIENT WITHOUT NEW ARCHITECTURE

Before adding recurrence, determine whether the existing structured temporal
observation (157-dim, Groups A–D, v32p2feat-v1) plus a trajectory-level prefix
objective is enough. No Transformer / GRU / LSTM / memory bank / world model in P7.

## 3. KEY PREREGISTERED ANALYTICAL COMMITMENT (FACTORIZATION ARGUMENT)

Under teacher forcing with per-step independent predictions, sequence NLL
factorizes exactly:

```text
-log P(a*_0..H | s*_0..H) = Σ_t=0^H -log p(a*_t | s*_t)
```

Therefore **Mode A (teacher-forced) prefix supervision is mathematically a
window-uniform reweighting of per-step cross-entropy** — it cannot by itself encode
cross-step dependency in the gradient. The genuinely sequence-level tests in P7 are:

1. **Mode B — prefix rollout consistency**: free-running simulator execution of the
   learned policy from the prefix start, compared state-by-state against the teacher
   state trajectory (metric + checkpoint-selection criterion, not a gradient, since
   the simulator is not differentiable and RL/PPO is closed).
2. **Prefix-exact-match rate** (all native actions 0…H match) as a selection metric.
3. **State-trajectory distance** over the prefix under free-running execution.

If Mode A window-uniform supervision merely shifts the horizon again (Step 3 → Step 4/5
with economics still flat), that is evidence FOR the P4–P6 mechanism (P7-D/P7-E), not
a failed implementation — and it constitutes the first concrete justification for a
sequence-memory architecture.

## 4. CANONICAL STARTING POLICY & ARCHITECTURE FREEZE

- Starting checkpoint: `results/v32_p6_arm2_rebalanced.npz` (P6 Arm 2).
- Inference: always with the exact semantic mask (`v32/p6/mask.py`).
- Frozen: temporal feature encoder, 3×256 Tanh MLP trunk, native factorized heads,
  market head, lossless codec (`v32/p3/codec.py`), simulator, competition artifacts.
- Prefix training warm-starts from P6 Arm 2 (fine-tune, bounded epochs).
- No per-step loss spikes: **no `lambda_s3`, no `lambda_s4`, no step-indexed action
  schedule, no hardcoded next-action override.** This is the core P7 discipline.

## 5. PREFIX DEFINITIONS (FROM RECORDED DATA, NOT ASSUMPTIONS)

Prefixes are extracted from the actual recorded demonstrations in
`results/v32_p2_bc_legs.jsonl` (120 legs, 4 teachers, seeds 249635–249674):

- **P4**: steps 0–4. **P8**: steps 0–8. **P12**: steps 0–12. **P24**: steps 0–24.

Per prefix record: observation, temporal features, full native action, farmer/hand/
market actions, farmer position, inventory, cash, livestock/crop state, phase/time info.
Reference teacher for closed-loop divergence comparison: **E2_A7** (the macro whose
opening the P6 policy reproduces through Step 2; verified against recorded rows in
`V32_P7_PREFIX_DATASET.md`). If recorded data shows the four teachers share an
identical opening prefix, that is documented and the reference choice is moot for H≤4.

## 6. PREFIX LOSS (MODE A — TEACHER-FORCED)

```text
L_total = L_standard_BC + λ4·L_prefix4 + λ8·L_prefix8 + λ12·L_prefix12 + λ24·L_prefix24
```

where each `L_prefix(H)` is the **uniform mean** per-step action loss over steps
0…H (unit + market heads, same masking as `v32/p3/metrics.py::head_losses`):

```text
L_prefix(H) = (1/(H+1)) · Σ_t=0^H L_action(t)
```

Uniform within the window — explicitly NOT a spike on the last step. Only one λ is
nonzero per arm ( Arms 1–4 test H = 4, 8, 12, 24 respectively, each only if the
shorter horizon shows benefit per §9). Default λ4 = 10.0 (P5 early-horizon scale),
bounded fine-tune (≤10 epochs, lr 3e-4, batch 128, grad-clip 1.0, Adam).

Terminal/state consistency (`L_prefix_terminal`, `L_state`) is evaluated as a
**Mode B rollout metric** (actual simulator execution), not a gradient, because:
(a) the policy has no state-prediction head (frozen architecture), (b) backprop
through the simulator is unavailable, (c) RL/advantage/reward objectives are closed
in P7. No teacher-state overwrite, no action splicing, no future-state inputs during
rollout — audited in `tests/test_v32_p7.py`.

## 7. EXPERIMENTAL ARMS

| Arm | Name | Training? | Intervention |
|:---:|:---|:---:|:---|
| 0 | P6 baseline repro | No | P6 Arm 2 + semantic mask; exact control |
| 1 | Prefix-4 | Yes | Warm-start P6 Arm 2; uniform 0–4 window objective |
| 2 | Prefix-8 | Conditional | Only if Prefix-4 helps but macro still breaks ≤8 |
| 3 | Prefix-12 | Conditional | Only if Prefix-8 shows additional benefit |
| 4 | Prefix-24 | Conditional | Only if evidence requires it past Step 12 |
| 5 | Phase conditioning | Conditional | Only after H1 tested; state-derived phase only |

## 8. PHASE CONDITIONING (H2) — GATED

Allowed only after Prefix-only behavior is measured. Phase must be a deterministic
function of **current observable state** (e.g. hires/livestock/structures/day derived
from `ess`), fixed before training, with no step-index lookup, no teacher tape, no
seed ID, no future knowledge. Ablation: A (P6 baseline) vs B (prefix only) vs C
(prefix + phase). If phase cannot be defined from state alone, H2 is rejected
without training.

## 9. EXPANSION / STOP RULES (§42)

- Do not train Prefix-8 unless Prefix-4 shows material prefix-stability gain.
- Do not train Prefix-12/24 unless the next-longer horizon shows additional benefit.
- Longer supervision is not assumed better; the correct horizon is the smallest one
  capturing the causal coordination structure.
- If Prefix-4 merely moves first divergence Step 3 → Step 4 with economics still
  flat, that CONFIRMS the horizon-shift mechanism (P7-D trajectory) — do not chase
  with Prefix-8 spikes; document and proceed to decision.

## 10. EVALUATION PROTOCOL (FROZEN)

- Screen: identical P6 120-leg screen (seeds 249675–249684 × 6 opponents
  E0_V3,E1_V22R1,E2_A7,E3_V25P3,E6_W72,E7_W2015 × 2 seats), deterministic, masked.
- First-divergence reference: live E2_A7 replay in the learner seat vs the same
  opponent/seed (open-loop tape → deterministic on-manifold reference).
- Metrics per leg: step 0–8 farmer ops, hires, first action/state/economic
  divergence, prefix-exact-match (H=4/8), prefix state-match, opening-macro survival,
  terminal cash, win, tail percentiles.
- Counterfactuals (A: policy; B: teacher action at divergence then policy; C:
  teacher prefix through horizon then policy) via actual simulator execution only.

## 11. DECISION GATES

- **Gate 1 (Prefix stability)**: prefix-exact-match(H) and median first divergence
  materially improve vs Arm 0 on the 120-leg screen.
- **Gate 2 (Economic recovery)**: capital trap avoided; terminal cash rises
  materially above the flat-zero regime with non-zero median; reproducible.
- **Gate 3 (Holdout quarantine)**: 249685–249694, 249695–249734, 214200–214249,
  340090–340199 untouched. Generalization only if Gates 1+2 pass.
- **Gate 4 (PPO)**: `PPO 1M SLOPE GATE: CLOSED`. Reopens only after stable BC +
  economic recovery + reproducibility. No RL, no reward regression, no advantage
  weighting, no terminal-cash training objective in P7.

## 12. POSSIBLE OUTCOMES (PREREGISTERED MAPPING)

- P7-A: Prefix-4 stabilizes macro + economics → P7 PASS.
- P7-B: Prefix-8/12 required → P7 PASS (with minimum-horizon finding).
- P7-C: Phase conditioning adds stabilization → P7 PARTIAL (phase) or PASS.
- P7-D: Prefix supervision fails → P7 STOP (sequence-memory now justified).
- P7-E: Behavioral recovery without economic recovery → P7 PARTIAL.

## 13. ARTIFACTS & TESTS

Artifacts per protocol §38 (Prefix8/12/24, phase docs only if executed). Tests in
`tests/test_v32_p7.py` covering §39 (12 invariants) plus leakage audit (§40). All
prior suites re-run. Protected holdouts verified virgin at exit.
