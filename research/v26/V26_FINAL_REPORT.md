# V26 — FINAL REPORT: Backbone-Aware AEC Re-Architecture & Transfer to V25

## 1. Decision

**Formal state: `V26 TRANSFER FAILED — MECHANISM`**

The preregistered `TRANSFERRED` bar was met 3 of 4: positive mean transfer
(+$10.85), bootstrap 95% CI lower bound +$3.80 (≥ −$50), zero safety
breaches — but win rate 16/40 (40%) missed the >50% rule. A small positive
directional effect was observed with exact infrastructure neutrality; it is
economically negligible (~0.01% of terminal rewards) and does not support a
transfer claim under the preregistered rule.

On the §1 scientific question (is the AEC architecture transferable, or
V3-specific?), the answer is **Outcome A for the architecture**: the
backbone-aware evaluator, continuation model, safety gates, and telemetry
transferred to V25 cleanly with zero backbone-conditional economic logic.
The validated market-timing mechanism itself fires, commits safely, and
leans positive on V25 — but its economic leverage on the P3 planner is tiny.

## 2. What was built

- `aec/backbone/` — formal `BackbonePolicy` / `ContinuationPolicy` contracts
  (`interface.py`), shared rollout/observation utilities (`utils.py`), and
  exact adapters for V3 (`v3_adapter.py`) and V25 P3 (`v25_p3_adapter.py`).
- Backbone-aware counterfactual path: `CounterfactualSimulator.evaluate`
  and `ShadowRobustnessEvaluator` accept the active backbone and use
  `backbone.snapshot_state()` / `create_continuation_policy()` /
  `restore_state()` instead of hardcoded V3 globals. Legacy V3-callable
  path retained as fallback. No `if backbone == ...` economic branching.
- Root cause of the V25 AEC failure resolved: V22's snapshotter probed
  `agent_fn.__globals__['_PARENT_NS']`, which does not exist on the P3
  wrapper, silently returning an empty snapshot and corrupting live chassis
  state during shadow rollouts. The V25 adapter snapshots the underlying
  chassis explicitly (see `V26_P3_CONTINUATION_STATE_AUDIT.md`).
- Perf: `enable_quarantine_scan=False` skips detectors that cannot emit an
  enabled family (action-neutral; quarantine telemetry only). 7-17x faster
  matches. Verified by full-match digest parity plus committed test
  `tests/aec/test_v26_quarantine_scan_parity.py`.

## 3. Transfer tournament (preregistered)

Cohort `249470..249489` × seats {0,1}, 40 matches/arm, opponent frozen V3,
`MAX_WORKERS=9`, 160/160 checkpointed. Full rules in
`V26_AEC_TRANSFER_PREREGISTRATION.md`.

| Arm | Paired mean vs V3 | Median | Commits |
| --- | --- | --- | --- |
| ARM1 V25 standalone | −218.75 | −287.0 | 0 |
| ARM2 V25 + AEC infra-only | −218.75 | −287.0 | 0 |
| ARM3 V25 + market timing | −189.65 | −190.0 | 24 |
| ARM4 V3 + market timing (ref) | +19.80 | 0.0 | 36 |

Primary (ARM3−ARM1 paired): **mean +$10.85, median $0, min −$7, max +$97,
16W/6L/18T, bootstrap 95% CI [+$3.80, +$19.35]** (seed 7, 10k resamples).
Structure is clean: all 18 ties are zero-commit matches with bit-exact
ARM1 action parity; all 22 decisive matches carry commits (win rate
conditional on acting: 16/22 = 72.7%).

Secondary: H2 null parity 40/40 exact (PASS); H3 V3 reference +$19.80
non-negative (PASS, though loss-heavy at 11W/17L/12T); H4 worst loss −$7,
no tail events (PASS); H5 counterfactual reproducibility 8/8 exact under
two independent reconstructions (PASS, see
`V26_COUNTERFACTUAL_FIDELITY.md`).

## 4. Secondary findings (material, non-primary)

1. **V25's edge did not replicate on the virgin cohort.** ARM1 (V25 vs V3)
   scored −$218.75 mean, vs V25's +$1,300.70 discovery / +$453.77
   confirmation. V25's advantage appears cohort-sensitive with high
   cross-cohort variance. This concerns the backbone, not the AEC, but it
   frames any future V25 release discussion.
2. **Market-timing leverage on P3 is structurally small.** The trigger
   (≥2 reorderable same-turn market orders) fires selectively (24 commits /
   40 matches); P3's liquidity profile leaves little intra-turn insolvency
   for reordering to fix. Failure class is closest to §28-C (opportunity
   exists, economics differ by backbone) at small magnitude — not a
   continuation bug (parity/fidelity all exact) and not total disappearance.
3. **Seat symmetry.** Every seed's seat-0/seat-1 pair produced identical
   ARM3 rewards and commits; analysis remains seat-paired and valid.

## 5. Session cross-check and corrections

Prior work (§0–§22 artifacts, adapters, 49/160 tournament) was verified and
completed. Corrections made this session:

1. **Repaired 2 committed-test regressions** (`test_mechanism_isolation`
   test_1/test_8): restored the legacy Layer-1 `LOCAL_WEED_DIG` carve-out
   (Layers 1–2 simulate, commit gate diverts); V26 arm isolation now comes
   from `enable_quarantine_scan=False`, leaving the V22 contract intact.
   Full isolation suite 9/9 green.
2. **Fixed wrong P3 digest** in `V26_BASELINE_FREEZE.md` (and adapter
   equivalence doc): worktree file is byte-identical to the `e4eb8a4` blob;
   recorded hash corrected to `13292582…` matching tournament checkpoints.
3. **Fixed two doc inaccuracies** in `V26_BACKBONE_GENERALITY_AUDIT.md`
   (V3 identity string, continuation method name).
4. **Unstalled the tournament** (49→160 in ~5 min) via the verified
   action-neutral detector skip; checkpoint consistency of the 9 prior ARM2
   matches re-verified by digest re-run.
5. V22R1 protection verified: both tarballs match frozen hashes, tag
   `v22r1^{commit}` = `33763a8` = branch base, no stop condition (§24)
   triggered, no threshold tuning performed (§18).

## 6. Recommendations

1. **No V26A confirmation campaign**: a +$11 mean effect with 45% ties and
   40% all-match win rate does not justify a confirmation cohort.
2. **No release action**: V22R1 remains the submitted fallback, untouched.
   Any future V25-based candidate must first resolve finding 4.1 (backbone
   variance) on fresh cohorts.
3. **No V26B defensive-layer transfer**: §29 gating (V26A qualifies) not met.
4. The backbone-aware architecture (`aec/backbone/`, backbone-parametric
   simulator) is validated infrastructure and should be retained as the
   base for any future supervisor work — it is the durable Outcome-A
   result of this study.
