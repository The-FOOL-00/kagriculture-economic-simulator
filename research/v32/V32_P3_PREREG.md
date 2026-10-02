# V32 P3 PREREGISTRATION — native action-head repair + BC recovery

Status: SEALED at P3 entry (2026-09-23), before any P3 training.
Scope: representation/action-head repair ONLY. No PPO is authorized by this document.

## 1. Scientific question

Can a simulator-native slot-factorized action representation recover enough of the
expert's behavior under closed-loop behavioral cloning that learned economic
behavior becomes nontrivial and stable?

## 2. Fixed design (no search)

- State: P2 structured-temporal features, Groups A-D, 157 dims, `v32p2feat-v1`,
  TRAIN-only normalizer `d2a41ab7…`, clip ±8. Unchanged unless a forensic defect
  is found and documented.
- Trunk: 157→256→256→256, Tanh, shared. Same dims as P2 a1.
- Heads: independent per-slot native classifiers exactly matching
  `V32_P3_ACTION_SCHEMA.md` (unit op/arg/qty, market op/item/qty per slot).
  No pointer, no Transformer/GRU/LSTM/attention/MoE/router, no autoregression,
  no global action-ID classifier, no hyperparameter sweep.
- Data: P2 BC legs (`results/v32_p2_bc_legs.jsonl`, 120 legs / 172,560 steps,
  seeds 249635–249649) with identical train/val split (val = 249647–249649).
  Single-teacher vs mixture supervision is the ONE predeclared branch (§5).
- Optimizer: Adam 3e-4, batch 1024 (same as P2 BC). Memorization probes may use
  smaller batches on the fixed 400-sample subset; full-BC runs ≤30 epochs with
  the same early-stop rule (patience 5 on val full-exact).

## 3. P3 screen/confirmation seeds (virgin V32-DEV, declared before first use)

- P3-SCREEN (closed-loop BC + step-0 + economics): `249675–249684` (10 seeds).
- P3-CONFIRM (single-touch generalization, §30): `249685–249694` (10 seeds).
- Development probes (codec/execution/memorization smoke): consumed P2 seeds
  only (`249635–249649`, `249635` preferred — already used by T5).
- P2-SCREEN `249650–249672` may be reused ONLY for paired P2-BC-vs-P3-BC
  comparisons (same seeds = comparable), never for tuning.
- V32-CONFIRM `249695–249734`, GATE0, and all 340xxx ranges remain refused.

## 4. Gates (all must be reported; P3 PASS needs all green)

| Gate | Criterion | Predeclared bar |
| :--- | :--- | :--- |
| G1 codec | round-trip over all 172,560 recorded steps | 0 unexplained semantic mismatches |
| G2 memorize | 400-sample subset, full-action exact match | ≥95% (P2 pointer: 55% @ep300; linear control: 100% @ep75) |
| G3 step-0 | wash reproduction on step-0 wash examples | exact native wash object, ≥95% of wash cases |
| G4 closed-loop | P3-SCREEN terminal cash, paired vs P2 BC | materially above P2 BC ($0–138) on majority of seeds, mechanism-consistent |
| G5 stability | repeat closed-loop with 2 training seeds | same qualitative outcome (nontrivial + stable, not one lucky episode) |
| G6 generalization | P3-CONFIRM single touch | nontrivial behavior persists (fidelity + economics above P2-BC level) |

G2/G3 bars are representation bars: failure means STOP D/F per §31, not "train longer".

## 5. Predeclared branch: supervision mixture

P2 evidence shows 4-teacher label conflict on identical step-0 inputs. P3 runs
memorization (G2) on the MIXTURE subset first; if G2 passes on mixture, full BC
stays mixture. If mixture G2 fails while single-teacher (A7-seat) G2 passes,
P3 pivots to single-teacher A7 BC and documents the mixture as a supervision
confound (distinct from the representation question). Teacher choice is the only
allowed data branch; no other resampling, reweighting, or filtering.

## 6. Stop conditions (§31 STOP A–G apply verbatim)

In particular: schema unrecoverable (A), codec lossy (B), memorization fails (C),
step-0 unrepresentable (D), closed-loop ≈$0 despite fidelity (E), bottleneck
moves upstream to temporal features (F), repair requires prohibited complexity (G).

## 7. PPO status

CLOSED. Reopening eligibility requires ALL nine §41 conditions demonstrated in
`V32_P3_DECISION_REPORT.md`; eligibility is then a separate review, not execution.

## 8. Provenance

Entry commit state: HEAD `d818fb1` + untracked V28–V32 research files (see
`V32_P3_COMPETITION_SAFETY.md`). Engine `kaggle-environments 1.32.7`, CPU-only.
P2 exit hash `c8977778…` re-verified at entry. No P3 training has run as of sealing.
