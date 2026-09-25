# V32 P7 — DECISION REPORT: TRAJECTORY-LEVEL PREFIX SUPERVISION

## 1. PRIMARY CONCLUSION

```text
P7 PARTIAL — trajectory fidelity improved, but economic compounding remains insufficient
```

```text
PPO 1M SLOPE GATE: CLOSED
```

Additionally: **a sequence-memory architecture investigation is now
scientifically justified** (Q9 below) — the first phase to produce concrete
mechanistic evidence for it.

## 2. EXECUTIVE SUMMARY

P7 tested whether trajectory-level prefix supervision (H1) and state-derived
macro-phase conditioning (H2) could convert P6's local action fidelity into
sustained macro fidelity with the existing feed-forward representation (H3).

Method: canonical opening prefixes reconstructed from all 240 recorded
demonstration seats (all four teachers share the IDENTICAL 0–24 farmer macro);
Arm 0 reproduced P6 exactly ($0.07/$0.00/0 wins, div step 3, 120/120); Arm 1
trained a row-uniform prefix-4 objective (λ4 = 10, warm-start P6, no new
spikes) and screened it on the identical 120-leg protocol with paired live
teacher references.

Result: Arm 1 improved EVERY continuous fidelity metric — wash bleed −89%
(−$1,014 → −$118), step-3 op SOUTH → PICKUP, t_pos 4 → 5, state distance lower
at every step 0–8 — but moved NONE of the binary macro metrics: t_act stuck at
3 (120/120), prefix-exact 0%, macro survival 0/120, median cash $0.00, 0 wins.
The residual failure is a closed-loop ARG flip (train: SHEEP; closed loop:
COW) under state shift at step 3, plus a policy that fails EVERY
macro-transition (steps 3, 4, 11, …) while succeeding only on memorized
choreography (0–2) and reactive tending (9–10) — proven by counterfactuals B
(forced step-3 fix → still NORTH@4 → $0) and C (forced teacher 0–8 → fails
WEST@11 → $0).

Per the preregistered §42 stop rule, Prefix-8/12/24 were NOT run (no material
prefix-stability gain; longer windows give step 3 LESS signal and cannot create
missing closed-loop labels) and phase conditioning was NOT trained (rejected
with proof: the confused states share phase LIVESTOCK_SETUP, so a phase
embedding is provably incapable of separating them).

## 3. ANSWERS TO THE 11 FINAL DECISION QUESTIONS (§44)

1. **Does prefix supervision materially improve multi-step fidelity?** YES on
   continuous fidelity (state trajectory uniformly closer, wash bleed −89%,
   t_pos +1); NO on prefix-exact stability (0%).
2. **Minimum successful prefix horizon?** NONE SUCCEEDS — no uniform
   teacher-forced horizon stabilizes the macro. The binding constraint is
   supervision TYPE (missing closed-loop labels), not horizon LENGTH.
3. **Does state divergence decrease?** YES — mean state distance lower at every
   step 1–8 (−95% @2 … −13% @8).
4. **Does first divergence move later?** Action NO (3→3); physical state YES
   (+1, 4→5); money-inclusive NO (1→1, thresholds still exceeded).
5. **Does the opening livestock/pasture macro survive?** NO — 0/120 both arms;
   failure moved from wrong-OP to wrong-ARG at step 3.
6. **Does terminal cash materially recover?** NO — $0.07 → $1.14 mean, $0.00
   median, 0 wins. The capital trap closes on all 120 legs.
7. **Does phase conditioning add value?** UNTESTED-BY-PROOF: rejected without
   training; same-phase confusion proof shows incapability on the binding error.
8. **Is the existing feed-forward representation sufficient?** NO for macro
   stability (sufficient only for memorized choreography + reactive tending).
9. **Is a recurrent/sequence architecture now scientifically justified?** YES —
   as the leading next investigation. The policy fails macro-TRANSITIONS (which
   require execution context: "what comes next in THIS macro") while passing
   state-local steps; feed-forward re-derivation from instantaneous observation
   is the diagnosed bottleneck. Justified ≠ proven: the next phase must test it.
10. **Is generalization justified?** NO — economics unrecovered; all holdouts
    virgin (verified §COMPETITION_SAFETY_EXIT).
11. **Is PPO still closed?** YES — `PPO 1M SLOPE GATE: CLOSED`. No RL, reward,
    or advantage objective was used in P7.

## 4. SECONDARY FINDINGS (FORENSIC)

1. **Universal SELL-first wash**: P6 emits order-flipped wash on all legs AND
   train seeds; P6's own order-sensitive probe reads 0/240 while P5's reads
   240/240 — P6's step-2 spike flipped wash order as collateral (supports P7's
   thesis: pointwise spikes destabilize the joint macro). Causal cost: −$1,014
   (isolated). Prefix-4 reduced it to −$118 via qty compromise, not order fix.
2. **P6-manifest hash erratum**: recorded P5 hash (8bfb219e) ≠ file bytes
   (dc939b29); file is P5-era (mtime/meta) and behavior-verified (probe
   240/240 wash, 0/240 S2) — manifest typo, content authentic, file untouched.
3. **P6 t_state/t_econ convention**: P6's "3/3" uses action-step indexing; under
   P5's literal money-inclusive definitions the values are 1/1 (wash bleed).
   P7 reports all conventions explicitly.
4. **Teacher-forced ≠ closed-loop at step 3**: P7 predicts NORTH on train
   step-3 states but PICKUP-COW in closed loop — the decision boundary balances
   on nuisance features (cash/stranded-goods/action-history).

## 5. MACHINE-READABLE RUN RECORD

```json
{
  "phase": "V32_P7",
  "primary_conclusion": "P7 PARTIAL — trajectory fidelity improved, but economic compounding remains insufficient",
  "ppo_gate": "CLOSED",
  "sequence_memory_justified": true,
  "baseline_checkpoint": "results/v32_p6_arm2_rebalanced.npz",
  "candidate_checkpoint": "results/v32_p7_prefix4.npz",
  "architecture": "P3Policy(157, 12) + semantic mask (frozen)",
  "loss": "L_unit + L_mkt + 50*L_crit_s0 + 10*L_early_1_10 + 50*L_s2_farmer + 10*L_prefix4_uniform",
  "development_seeds": "249675:249684",
  "metrics_arm1": {
    "wash_shape": 1.0, "wash_order": 0.0, "pass": 1.0, "north": 1.0,
    "hires_mean": 5.0, "south": 1.0, "pickup3_sheep": 0.0,
    "pem4_farmer": 0.0, "pem8_farmer": 0.0, "macro_pass": 0.0,
    "t_act_med": 3, "t_state_med": 1, "t_pos_med": 5, "t_econ_med": 1,
    "cash_mean": 1.14, "cash_med": 0.0, "win_rate": 0.0
  }
}
```

## 6. WHAT COMES NEXT (NOT THIS PHASE)

A sequence-memory investigation (recurrent/attention execution context) is
justified to test whether carrying macro state across steps repairs
macro-transitions. It must inherit: frozen artifacts, simulator semantics,
native schema, codec, seed governance, and P7's mechanisms as its baseline to
beat (t_act 3, pem 0%, arg-flip, transition-class failure). PPO stays closed
until stable BC + economic recovery + reproducibility are demonstrated.
