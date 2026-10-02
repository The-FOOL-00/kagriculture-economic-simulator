# V32 P7 — FIRST DIVERGENCE ANALYSIS (P4 → P5 → P6 → P7)

## 1. DIVERGENCE TRAJECTORY ACROSS PHASES (120-LEG SCREENS)

| Phase | t_act_farmer (median) | t_pos | t_state/t_econ | Step-3 action | Terminal cash |
|:---|:---:|:---:|:---:|:---:|:---:|
| P4 Arm 1 | 0 (WEST≠PASS) | 1 | 1 / 1 | — | $108.39 |
| P5 Arm 2 | 2 (PICKUP≠SOUTH) | 2 | 2 / 2 | — | $2.94 |
| P6 Arm 2 | 3 (SOUTH≠PICKUP) | 4 | 1 / 1 | SOUTH | $0.07 |
| P7 Arm 0 (repro) | 3 (120/120) | 4 (120/120) | 1 / 1 | SOUTH | $0.07 |
| P7 Arm 1 (prefix-4) | 3 (120/120) | **5** (120/120) | 1 / 1 | **PICKUP COW** | $1.14 |

(P4/P5 t_pos/t_state/t_econ reconstructed under P7 conventions from their
reports; P4's $108 reflects an idle farmer drawing no wages, not competence.)

## 2. WHAT MOVED AND WHAT DID NOT (ARM 0 → ARM 1)

- t_act_farmer: 3 → 3 (unmoved; the DIVERGING ACTION changed SOUTH → PICKUP-COW
  but the divergence STEP did not).
- t_act_full: 0 → 0 (wash-order literal differs at step 0 in both).
- t_pos: 4 → 5 (+1: PICKUP is stationary, so physical dislocation appears one
  step later — a DELAY, not a repair).
- t_state / t_econ: 1 → 1 (wash bleed reduced −$1,014 → −$118 but still exceeds
  the $1/$10 thresholds on all legs).
- All distributions are degenerate (120/120 identical): the opening is fully
  deterministic given the checkpoint; there is no seed/opponent variance to
  exploit.

## 3. THE P7 TARGET QUESTION, ANSWERED

> Determine whether sequence-level supervision converts local action fidelity
> into sustained trajectory fidelity.

Answer: PARTIALLY. Local fidelity improved (wash qty, step-3 op, state
distances, t_pos), but SUSTAINED trajectory fidelity was not achieved:
prefix-exact stays 0%, the first DIVERGING ACTION remains at step 3, and the
policy still cannot execute two consecutive correct macro transitions
(step 3 arg wrong; step 4 wrong even when step 3 is forced — see
`V32_P7_COUNTERFACTUAL.md`).

## 4. WHY t_act = 3 IS STICKY (THREE STACKED MECHANISMS)

1. **Trunk-coupled op ranking** (teacher-forced): NORTH rises with PICKUP under
   the prefix gradient; the −0.53 gap never closes (`V32_P7_PREFIX_DIAGNOSTICS.md`).
2. **Closed-loop arg flip under state shift**: arg head says SHEEP on train
   states, COW in closed loop (cash/stranded-goods/action-history nuisance).
   No teacher-forced label supervises the closed-loop state.
3. **Same-phase confusion**: train and closed-loop step-3 states share phase
   LIVESTOCK_SETUP, so even phase context cannot separate them (§6 of
   `V32_P7_PHASE_ABLATION.md`).

Mechanisms 2–3 are horizon-independent: no uniform window of ANY length
addresses them. This is the evidentiary basis for stopping prefix expansion
and for justifying a sequence-memory investigation.
