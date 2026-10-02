# V27 — FINAL REPORT: V25 BACKBONE ROBUSTNESS, REGIME DECOMPOSITION & CAUSAL ATTRIBUTION

## 1. Executive conclusion

V25 P3 was stronger than V3 on no virgin cohort tested; it fails to
generalize (OUTCOME D), and its apparent discovery edge was a harness
artifact — while the campaign's causal decomposition discovered A7
(V3 + 30-wash with full step-0 processing, +$1,451 exploratory), the
candidate for V28 confirmation.

## 2. Research question

Is V25 P3 a robustly stronger farming backbone than V3 (+$1,300.70 /
+$453.77 / −$218.75 across three cohorts), or was its advantage
cohort-sensitive? What mechanisms explain the variance, and does any
stable backbone warrant a V25-native AEC?

## 3. Frozen baseline

V22R1 (tag commit `33763a8…`, archive `6b879b3e…`) untouched and
re-verified at audit. V3 (`845e0d10…`) and V25 P3 (`13292582…`,
byte-identical to the V25 tip across four anchors) frozen; P3's exact
mechanism is a step-0 30/30 wash bypass plus PASS→WATER/DIG dispatch
(125 lines; no livestock/sales/coupling code). V26 infrastructure
reused (adapters hermetic; 19/19 V26 tests green before and after);
V26's verdict preserved unchanged: TRANSFER FAILED — MECHANISM.

## 4. Historical evidence

Reconstructed 120/120 checkpoint records (means/medians/min/max all
reproduce). Forensic corrections: (a) V25's W/L/T used its
preregistered |Δ|≤$500 tie rule (omitted from its final report),
exactly reproduced; exact-zero recounts are 40/0/0, 27/13/0, 18/22/0
(zero exact ties in 120 matches); (b) the constant `early_idle_rate`
is real determinism (reproduced in all 200 replays), not a telemetry
bug. Seat mirrors are near-identical (52/60), so effective N is 20
seeds/cohort; V25's 67.5%-positive claim does not survive
seed-clustered inference (13/20, p=0.26).

## 5. Cohort heterogeneity

The headline finding: **cohort A (+$1,300.70) is a worker-history
artifact, not program behavior.** V25's file-loader pool lets
candidates `import main` through the process-global module cache; a
reused worker replays a STALE V3 module. P2 (pure V3 passthrough)
processes step 0; P1/P3 bypass it. A 1-step P2 primer flips P3's next
match to the checkpoint row exactly (+1145→+1286, digest-identical);
P1≡P3 behaviorally (AST-equal), so their discovery contrast
(−55 vs +1,300) is pure harness. Same-queue replays: 120/120 + F1
40/40 exact; cross-queue: 0/40. On the history-free series
(A′ −$55 / B +$454 / C −$219), Kruskal seed p=0.57 — mutually
compatible null-ish; no cohort heterogeneity remains. Pooled
farm-purged program effect: +$60 (SD $2,126).

## 6. Behavioral divergence

Ledger (200 trajectories): P3 opens +$108 every game (deterministic
+$54/−$54 lockstep wash; +$28 through t=144, seed-invariant); labors
+12 waters/−13 passes (92% late-game, DIG net 0); ends with identical
farm structures; issues ~27 fewer wheat SELL orders per game. First
material divergence (≥$250 persistent gap): t≈252 (day-10 harvest
revenue) on ~all matches — a medium-horizon macro transition, not the
opening nor terminal accumulation. Reward emergence (sign lock):
median t=553. Farm gaps (V3v3, 60 seeds): 0 on 54/60; two monsters
(249463 +$13k program tip; 249450 +$6.9k farm route) dominate all
cohort means. Typical match (|Δ|≤$3k): −$53.

## 7. Economic attribution

Two large additive factors + one null + noise: 30-qty ≈ +$1,500;
step-0-init (call vs bypass) ≈ +$1,450; dispatch ≈ $0 (±$20);
farm ≈ 0 (54/60). P3 = qty(+1,500) − init(−1,450) ≈ +$60 by
cancellation. The $31-miss expansion gate on 249463 (CF-1: +$31.02
injection fires BUY_LAND + SHEEP×6 + HIRE×2; butterfly ≈ 400×)
explains the +$13k tip; CF-2 (no firing to +$2k on 249464) proves
gates are context-specific, not generic cash rules. No early
observable predicts terminal sign (early gaps constant; shops too
dispersed; chore dose sign-unstable); the t=288-lead watchlist was
refuted prospectively twice (corr −0.17, −0.04).

## 8. Causal ablations (exploratory, consumed seeds)

V3S sanity 120/120 exact. A3 (no dispatch) −$10 [−18,−4], 98/120
direct ties: dispatch inert. A2 (50-bypass) −$1,543, 5/115: 50 without
step-0 processing toxic. A1 (V3 opening) −$53 net, kills the 249463
tip: opening necessary for the tip but a lottery ticket otherwise
(−$170 typical ex-tip). A4/A5/A6 not applicable (no such code).
**A7 (30-call: V3 processing + 30-wash) +$1,450.8, 119W/1L/0T,
seed CI [+1,181, +1,896]** — keeps both factors; post-hoc discovery,
needs V28 virgin confirmation. Init flows through late reactive
markets only (A3-vs-A7 units identical 719 turns; market parts t=433);
qty through wash-path fill cascades (units part t=153).

## 9. Counterfactual fidelity

Exact-state clone + active-backbone probes; snapshot/restore
bit-exact (terminals reproduce F2 records both seats); independent
re-run identical (threshold $31.02 ×3); below-threshold silence +
non-tip control as falsification. Predicted (firing) vs realized
(+$13k trajectory consequence) reported separately, never equated.
Long-horizon simulator rollouts deliberately omitted (drift theater;
ablations give realized terminals instead).

## 10. Prospective discovery (virgin 249490..249509)

40/40: mean −$398.05, median −$236, 12W/28L/0T, posrate 0.30, seed-pos
6/20, tail −$2,109, max +570 (no tip), seats 20/20 identical (no farm
checks triggered). All five preregistered directional rehearsal gates
fail. Analysis-only; code frozen with hash record.

## 11. Prospective confirmation (virgin 249510..249529)

40/40: mean −$469.85, median −$100, 18W/22L/0T, posrate 0.45,
seed-pos 9/20, tail −$4,098, seed CI [−1,030, −10] (entirely
negative). **Five of six preregistered gates FAIL** (only tail-floor
passes). Pooled virgin (80 matches / 40 seeds): mean −$433.9, seed CI
[−747, −152], 30W/50L. Audit: 3/3 matches independently reproduced
bit-exactly; V22R1/P3/V3 hashes verified; 45/45 tests green.

## 12. Generalization assessment

**OUTCOME D — V25 FAILED TO GENERALIZE.** Per prereg §6 (1+ gates fail
with negative mean and seed CI excluding large positives — here
excluding zero itself): P3 loses to V3 by $150–$750 on unseen seeds.
V3 remains the stronger validated backbone. (Not E: CIs do not
straddle zero; not C: no regime structure found — just seed noise
around ≈$0 retrospective and negative prospective.)

## 13. Implications for AEC

No V25-native economic supervisor is justified: there is no stable
backbone edge to supervise (P3 ≈ V3 retrospectively, P3 < V3
prospectively), no early regime predictor to condition on, and the one
large historical effect was harness artifact. Do not build AEC on P3.
The A7 discovery (+$1,451 exploratory) is the only substrate candidate
worth a future supervisor — after virgin confirmation.

## 14. Explicit non-conclusions

- This does NOT prove V3 is optimal or unbeatable — only that P3 does
  not beat it (A7 might; untested on virgin seeds).
- This does NOT prove the dispatch could never matter — only that
  these 12 late waters net ≈$0 here (other dispatches untested).
- The additive model (qty/init/dispatch) is fit on consumed seeds and
  could shift on virgin seeds (retrospective +$60 vs prospective
  −$434 residual wobble is consistent with it, not proof of it).
- The 249463 gate characterization is n=1 and not a general regime.
- Order-based market panels describe attempted (not filled) trades;
  terminal money (ground truth) bounds all consequences.
- P2-residue specifics (which V3 key persists) were localized to
  step-0-init (1-step primer suffices) but the exact key was time-boxed
  out; the 1-bit rule + reproducer fully determine all V27 decisions.

## 15. Next recommended research cycle

**V28: virgin confirmation of A7 vs V3** (one experiment): preregister
A7 (frozen `V27-ABL-A7` bytes) vs V3 on virgin seeds 249530..249569
(20×2 discovery + 20×2 confirmation, hermetic adapters, same six
gates). Rationale: 7σ exploratory edge (+$1,451, 119/120 wins,
systematic init+qty mechanism) that cannot be luck but is post-hoc
selected on consumed seeds — the single highest-information test in
the program. On pass: A7 becomes the research backbone and the first
legitimate substrate for a native economic supervisor. On fail: reopen
backbone discovery from V3.
