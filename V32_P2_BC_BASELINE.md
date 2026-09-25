# V32 P2 BC BASELINE (CASE B — architecture-aligned warm start)

## 1. Compatibility verdict: CASE B (incompatible head, reuse trajectories)

EXP-2 produced NO torch checkpoint: the R0 artifact was a numpy softmax
probe over farmer-op labels (22.4% val) on 90-dim linear features. There
are no reusable policy weights for the locked pointer-head architecture.
Per brief §27 CASE B: EXP-2's validated expert actions
(`/tmp/v32_traj.jsonl`, scanned into the vocab for coverage) + 120 new
P2 capture legs (compact raw essentials, P2-TRAIN seeds 249635–249649,
teachers A7/V3/W72/W2015) → architecture-aligned BC on the LOCKED
pointer head. This is an alignment step, not a new hypothesis.

## 2. Training record

Runner: `scripts/v32_p2_bc_train.py` (Adam 3e-4, batch 1024, ≤30 epochs,
early-stop patience 5 on BC-val full-exact; ran all 30). Data: 138,048
train / 34,512 val steps (val seeds 249647–249649). Wall 53 min CPU.
Checkpoint: `results/v32_p2_bc.npz` (545,705 params).

| Split | full-exact | farmer | hands | market | mkt-nonnoop | NLL/slot |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 0.022 | 0.433 | 0.452 | 0.899 | 0.309 | (see note) |
| val | 0.022 | 0.438 | 0.443 | 0.897 | 0.300 | 1.012 |

Note: train NLL mis-reports (single-chunk overflow dominates the mean;
accuracies train≈val show no overfit). Full-exact is harsh by design
(all ~13 unit slots + all 10 market slots must match). Farmer 44% doubles
EXP-2's 22% linear probe (richer state + temporal features + teachers).

## 3. Economic replay (§29): MIXTURE-BC FAILS — $0 replay

BC (deterministic) vs 6-opponent panel on SCREEN 249650–249672, both
seats (276 legs, `results/v32_p2_eval_bc.jsonl`): BC−A7 mean −$101,315,
median −$96,734; W-L-T 0-138-0 (seat 0); uniform across opponents.
Mechanism (instrumented leg): step-0 wash missed ([SELL,WHEAT,0] instead
of [BUY50,SELL50]-class wash) → no economy → off-distribution drift →
qty-0 market orders all game → $560 terminal.
Root cause: 4-teacher label conflict on constant step-0 input (4 washes,
1 input) + conflicting supervision elsewhere. The architecture is
exonerated (T1–T11 pass; instrumented execution faithful); the
SUPERVISION MIXTURE is the blocker.
Per §45/§61: ONE controlled follow-up — single-teacher A7 BC (same
locked arch, A7-seat rows only). If it replays economically, it becomes
the PPO init; if it also collapses, STOP per §29 (Branch F).

## 4. Follow-up result: A7-BC ALSO FAILS — head optimization pathology

A7-only BC (43k steps, 100-epoch budget, early-stopped ep27): val
farmer 0.369 / hands 0.393 / mkt-nonnoop 0.271 — no better than mixture.
Replay: $0–39 on 16/16 SCREEN legs (mean −$109,161 vs A7). Longer
training confirmed useless (identical plateau).
Closed-loop probe (TRUE expert history): farmer 0.343 ≈ val — NO
eval-time bug; collapse is genuine compounding from weak imitation.
Step-0 wash probe: argmax = all-NO-OP (never memorized 60 identical
samples) — optimization failure, not data failure.

Root-cause chain (all offline, deterministic probes on 400 samples):
- Linear head on identical features: 100% by ep75 → features SUFFICIENT.
- Locked pointer head: 55% at ep300 (50–100× sample-efficiency gap).
- Frozen-keys variant: 42% (worse). Big-init: same. Longer: same.
- Key geometry at init: 41,800 market pairs + 169 unit pairs with
  cosine > 0.99 — content-shared encoder collapses qty/item variants
  to near-identical keys; queries cannot separate them.
- Rejected fix a1.1 (log-scaled qty): collapse WORSE (55,088 pairs);
  memorization unchanged. Reverted; frozen a1 hash stable (c8977778…).

CONCLUSION: the locked pointer head is optimization-infeasible for this
candidate space within any reasonable budget. The formula/dims stay
frozen per §35; any head change needs a NEW authorized phase. P2 STOPS
at the §29 BC gate (see `V32_P2_DECISION_REPORT.md`). No PPO run was
launched.
