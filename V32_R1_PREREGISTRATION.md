# V32 R1 PREREGISTRATION — predictions + gate (2026-09-22)

Written after P1 forensics (EXP-1, n=6 seeds) and BEFORE any new match is
run or any TEST/LOCKED outcome is viewed. Hashed at commit time; hash
recorded in `V32_R1_CONFIRMATORY_REPORT.md`. Amending this file after
viewing TEST outcomes invalidates the confirmatory claim.

## 1. Predictions (point estimates with ranges, from P1-F1..F11)

P1. Best baseline on fresh seeds: per-opponent best-fixed (M1) at roughly
+$4k..+$6k mean cash over always-A7 (P1: +$4,947, 47% of oracle gap).
Global best-fixed will be W2015 or A7 depending on seed mix.
P2. Oracle-cash gap over A7 on TEST: mean +$8k..+$12k (P1: +$10,545),
median +$1k..+$3k (P1: +$1,638). The mean stays tail-driven (a few
+$30-50k suppression-avoidance rows per 40 seeds).
P3. Router improvement (M4 B2 over A7): +$2k..+$6k mean. Rationale: M4
should recover the opponent-driven half via wash/price prefix cues and
part of the seed-driven half via early price-path regime cues; full
oracle is unreachable (RNG expresses late on some seeds).
P4. Frame stack: longer {0,12,24} > short {12,24} > none {24} on VAL
soft-CE and TEST regret, by a material margin (>=10% relative regret
reduction longer-vs-none). Rationale: t=0 anchors deltas; t=12 catches
wash price impact; t=24 reads the emerging regime. If none ~= longer,
the regime is either immediate (wash-only) or too late (unpredictable).
P5. B1 (diagnostic) >= B2 (deployable) by $0..$2k (handoff costs little:
tape-indexed experts, 1-step reactive memory reset). If B2 << B1, the
handoff is lossy and B2 labels must be trusted over B1 hopes.
P6. Unseen wash-micro family (secondary split): M4-without-washmicro
degrades toward M1-fallback on {W72, W2015} opponents but stays above A7
on cash (wash-inference generalizes: small washes are visible in wheat
price impact). W/L on those opponents will NOT beat A7 (P1-F4: nothing
in-class beats W72; W/L routing adds ~0).
P7. W72 as a selected class: rare (<10% of TEST selections). Its value
is W/L-vs-W2015 only (P1-F5); cash-oracle almost never picks it.
P8. CROSS-vs-WITHIN confirmation (V32_FINAL_REPORT §5 P1): CROSS pairs
out-cash WITHIN pairs on a majority of fresh non-LOCKED seeds (>=21/41;
A1 correction: 41 fresh non-LOCKED b1 seeds, not 28 — miscounted at
prereg time; fixed before computing).
Mechanism note: same-wash pairs (30x30, 50x50) suppressed; mixed pairs
boom; W72-involved pairs always low.

## 2. Expected failure modes (ranked)

E1. Small-n overfit: 60 TRAIN rows vs ~21k params (M4-longer). VAL-TEST
gap or VAL-selection instability. Mitigation: heavy wd, early stop,
logistic/M1 fallbacks; honest Branch B/C report if it bites.
E2. Flat rows (vs W72, all within ~$800): label noise. Mitigation:
$500 admissible sets; per-opponent breakdown will show vs-W72 ~= 0 lift.
E3. Seed-driven half unreachable: early prefix carries no regime signal
(RNG expresses after t=24). Then M4 ~= M1 (opponent-driven only) and the
residual oracle gap stands -> Branch C evidence, not a bug.
E4. DMITRII reactive variance: DMITRII-opponent rows noisier (reactive
policy); expect widest CIs there.
E5. Handoff pathology on specific classes (e.g., P3 dispatch state):
continuation-equivalence diagnostic will catch; per-class breakdown shown.

## 3. Main gate (M4 B2 on TEST+LOCKED, 40 seeds x 6 opponents = 240 rows)

G1. Mean cash improvement over always-A7 > $0 with 95% seed-bootstrap CI
excluding 0 (common random numbers: same seeds/opponents).
G2. No catastrophic tail: worst row >= A7 same-row cash minus $25,000.
G3. Seed-positive fraction >= 60% (per-seed mean over opponents > A7).
G4. Shuffled-label control (M6) <= best baseline (no-leakage evidence).
G5. Determinism: rerun reproduces all TEST selections; packaging parity
stands (no expert code touched).
G6. Benefit not driven by one seed: drop-one-seed sensitivity — mean lift
stays positive dropping any single seed.
PASS (all G1-G6): Branch A if mean lift >= +$2k and opponent-holdout
secondary holds above A7; else Branch B. FAIL G1: Branch B/C/D per §4.
Any G4/G5 fail: Branch E (stop, repair).

## 4. ADDENDUM A1 (2026-09-22, post-grid, pre-TEST-analysis)

Structural finding (source-proven, not outcome-fitted): E2_A7, E6_W72,
E7_W2015 are behaviorally IDENTICAL to E0_V3 from step 1 onward
(`V31R2WashAdapter.split_cap=None` default; A7 `dispatch=False`; all
step-0 logic keys off `obs['step']`). They differ ONLY in step-0 wash
orders. Only E3_V25P3 differs post-0 (P3 dispatch, crumbs).
Consequence: Regime B2 (V3 opens 24 steps incl. the wash, then routed
continuation) is VACUOUS — verified: all 282 b2 rows flat within $500
(max spread $45). The router decision IS the step-0 wash decision and
must be made AT step 0; post-opening expert-switching cannot work for
this population. B2 training results (all soft-CE = ln 5) are reported
as vacuity controls, not candidates. B2-LOCKED legs are SKIPPED
(vacuous by construction; saves 240 legs).

Amended primaries (gate criteria G1-G6 UNCHANGED, applied to b1 rows):
- Deployable static wash-choice: M1 lookup + M2 logistic (A+ID, b1).
- Diagnostic seed-predictability: M3 (B1 prefix -> fresh-episode
  choice, b1) vs M1, with stack ablation {none, short, longer} (added
  configs M3_stack_none/short, M3_s1, M3_shuffled_b1).
Viewed before this addendum: aggregate b1/b2 spreads + TRAIN rows only;
no TEST selections, comparisons, or per-seed outcomes. LOCKED unopened.

## 5. Branch pre-mapping (brief §28)

- M4 >> A7, holds on holdout, clean tails -> A (expand + dynamic routing).
- M4 > chance on selection, small/unstable economics -> B (representation).
- Oracle gap large, M4 ~= A7 -> C (richer temporal/opponent features).
- Oracle gap ~= 0 on fresh seeds -> D (drop routing; within-policy work).
- Shuffled ~= real, or contamination found -> E (stop and repair).
