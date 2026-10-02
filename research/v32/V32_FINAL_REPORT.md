# V32 FINAL Report — EXP-1 through EXP-3 (2026-09-22)

Post-deadline research program. Competition state UNCHANGED: Slot A V22R1,
Slot B A7. No submission touched, no holdout consumed, no learned agent
introduced. V22R1/A7 digests re-verified at start and end.

## 1. Question asked

Can a small learned generalist, initialized from our deterministic experts and
trained against a diverse policy population, beat the deterministic champion?
This milestone answers the feasibility pre-questions: is the population valid
(EXP-1)? is imitation viable (EXP-2)? is RL testable on our hardware (EXP-3)?

## 2. EXP-1: population benchmark — VALID (448 legs, 6 virgin seeds)

Standings: W72 = W2015 (84-12) > A7 (72-24) > V22R1 (60-34-2) > A1 > V25P3 >
V3 > A2 > DMITRII (0-96). Full matrix: `V32_EXP1_EXPERT_BENCHMARK.md`.

Key results:

1. A7's +$1,286 vs V3 reproduces EXACTLY on 12/12 virgin legs; A7 beats
   V22R1 12-0 (+$1,250) — the AEC agent inherits the wash-50 vulnerability.
2. Wash ladder by W/L: 7/2 > 20/15 > 30 > 50, all small-margin ($10–260).
3. V27-dispatch costs ≈ −$1.3k regardless of wash (clean 2×2 factorial).
4. **The opponent is the economy**: same expert, same seed, different
   opponent → absolute cash swings up to $31k (A7×V25P3 mutual suppression on
   seeds 249637/249638). Cross-group pairs average ~$14k more pair-cash than
   within-group pairs, same sign 6/6 seeds (post-hoc grouping — pre-registered
   follow-up on fresh TRAIN seeds in §5).
5. W72 is joint-#1 on W/L with the LOWEST winner cash (~$92k): a denial
   specialist, 100% extractive. W/L and cash decouple — §44 vindicated.
6. Mirrored deterministic legs are seat-symmetric (identical per-expert cash):
   mirrors are determinism checks, not independent samples. Count seeds.
7. Controls: A7-vs-AST 12/12 exact ties; V3-vs-PASS 151k/176k vs 3000.

## 3. EXP-2: imitation — VIABLE AS INIT, not a solution (5,752 pairs)

Cheapest rung (softmax, 90 feats): farmer-op test acc 22.4% vs 10.7% majority
(+11.4pp lift, chronological split, 0 encode failures). Signal exists (§52(1)
not triggered) but fidelity is far from expert — needs frame stack + R1 MLP +
hands/market heads. Full-action exact-match ≈ 0 at this rung (honest).

## 4. EXP-3: RL — TESTABLE at 1–10M, not yet justified

Throughput: ~1000 agent-steps/s (10 workers, fast experts) → 1M ≈ 17 min,
10M ≈ 2.8 h. Inference +8% (torch 1M). 50M gated on a 1M slope check; 1B+
rejected. Binding constraints: V22R1-class opponents 12× too slow (eval-only),
terminal-only 720-step credit assignment, and PPO-lift vs the router fallback.
No PPO run launched — Phase B is gated on Phase A reaching strong per-head DEV
accuracy plus a ≥40-seed router baseline (§52(7) comparator).

## 5. Pre-registered follow-ups (predictions, not claims)

- P1 (population forensics): CROSS pairs out-cash WITHIN pairs on a majority
  of fresh TRAIN seeds (249643+); price-path collision analysis on
  A7×V25P3 vs A7×V3 (seeds 249637/249638).
- P2 (ladder): R1 0.1M MLP + frame stack beats R0 test acc by ≥10pp on the
  same chronological split; BC policy DEV W/L/T vs PASS then V3.
- P3 (router): leave-one-seed-out opening-expert choice at ≥40 TRAIN seeds.
- P4 (gate): 1M-step PPO slope check only after P2+P3.

## 6. Decision-tree placement (§54)

Between rungs: NOT outcome G (population + BC signal + throughput all viable),
NOT yet A/D (no learned policy exists), leaning B/C-probe-next (BC ladder +
router before any PPO). No evidence was found that would promote end-to-end RL
above the router today — and none that would kill the learned direction.

## 7. Stale-test note (V32 maintenance)

`tests/test_v28_freeze.py::test_cohort_quarantine` tripped on the 448
authorized V32 EXP-1 rows (forward scan, same as V29/V30/V31R2). Replicated
scan verified non-V32 offender count = 0; V32 own-files joined the allowlist
by the same definitional argument. Protection over pre-V32 files unchanged.

## 8. Artifacts

§50 checklist: BASELINE_FREEZE ✓, EXPERT_POPULATION ✓, FINGERPRINTS ✓,
SAMPLING ✓, TRAINING ✓, STATE_ENCODER ✓ (+v1.1 prices correction),
ACTION_ENCODER ✓, REWARD ✓, PROMOTION (pre-registered) ✓, COMPUTE ✓,
EXP1 ✓, EXP2 ✓, EXP3 ✓, EXP4–9 protocol stubs ✓, FINAL_REPORT ✓,
QUAL_MANIFEST ✓, tests (17 V32 + full suite green) ✓, scripts + raw records ✓.
Checkpoints: none (no model trained beyond the numpy probe — nothing to freeze).
