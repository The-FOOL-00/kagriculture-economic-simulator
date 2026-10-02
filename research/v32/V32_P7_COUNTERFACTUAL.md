# V32 P7 — CAUSAL COUNTERFACTUAL (ARM 1, DIVERGENCE STEP 3)

## 1. DESIGN (PREREG §10; `scripts/v32_p7_counterfactual.py`)

Cohort: seeds 249675–249677 × E0_V3 × seats 0,1 (6 legs). Live E2_A7 queries
for forced steps (verified: forced literals are the canonical macro actions —
no tape import, no counter bug). Full episodes via env.run.

- **A**: policy free run.
- **B**: teacher FULL joint action forced at step 3 (PICKUP SHEEP), policy after.
- **C**: teacher FULL joint actions forced steps 0–8, policy from step 9.

Results: `results/v32_p7_counterfactual_arm1.json`.

## 2. RESULT: NO RECOVERY IN ANY BRANCH (6/6 LEGS EACH)

| Branch | Terminal cash (6 legs) | Key observation |
|:---|:---|:---|
| A (policy) | $29, $29, $0, $0, $0, $0 | baseline |
| B (fix step 3) | $0 ×6 | step 4 = NORTH 6/6 (≠ PICKUP WHEAT) |
| C (teacher 0–8) | $0 ×6 | steps 9–10 match (FEED/CARE 6/6); step 11 = CARE 6/6 (≠ WEST); step 12 = CARE (≠ PLANT MELON) |

## 3. CAUSAL READING

1. **The failure is NOT localized to the step-3 arg (B)**. Forcing PICKUP SHEEP
   at step 3 does not unlock step 4: the policy still emits NORTH on the
   closed-loop step-4 state, even though it predicts PICKUP WHEAT on 192/192
   TRAIN step-4 states. The teacher-forced step-4 repair is causally inert —
   closed-loop states (wash-qty history in action-history features, cash,
   shed deltas) map to the wrong decision. One local fix does not restore the
   chain.
2. **The policy is reactive-only (C)**. From a perfect step-8 state it executes
   the two STATE-LOCAL tending steps (FEED@9, CARE@10 — "tend the animal in
   front of you") and then fails the first MACRO-TRANSITION (WEST@11 — "leave
   the pasture to plant melons"), looping CARE instead. It never replants,
   never rebuilds revenue, terminal $0.
3. **Combined**: the policy fails EVERY macro-transition (steps 3, 4, 11, …)
   and succeeds only on memorized choreography (0–2, via spikes) and reactive
   tending (9–10). No single-step or single-prefix intervention within P7's
   allowed set addresses a TRANSITION-CLASS failure — the policy lacks
   execution-context memory of which macro-transition comes next.

## 4. RELATION TO P6

P6's counterfactual (force SOUTH@2 → still $0 via step-3 SOUTH) showed the
horizon shift. P7's counterfactual shows the shift's TERMINUS: even forcing
through step 8, the policy fails the next macro-transition. The bottleneck was
never "the next step" — it is the absence of macro-sequencing state.
