# FINAL REPORT: EXP-DEV-006 QUALIFICATION — CONFINATORY REPLICATION ON 50050–50099
**Frozen treatment, untouched cohort (w.r.t. treatment), N=50, 200 games**

---

## 1. Executive Verdict

**INCONCLUSIVE — guard inert on this cohort; suggestive but non-significant statistics; zero tail cost.**

The frozen DEV-006 treatment (byte-identical to Discovery, `06db94e5…`) was evaluated against the
frozen V54++ baseline (Sub 56146971) on the reserved Qualification cohort 50050–50099. The H=500
guard never fired (0/200 games) because no game in either arm attempted the first-time step-288
entry the guard targets — DEV-006 was behaviorally identical to DEV-005 on all 50 seeds. Primary:
mean +$517.58, 3W/0L/47T, t=1.76, p=0.085 — short of the frozen significance gate (t > 1.96).
Per the predeclared decision rule (frozen before any result was observed), the outcome is
**INCONCLUSIVE**: not qualified (statistical gate missed), not failed (no tail violation, no harm,
no integrity breach). This is Qualification evidence and supersedes nothing about Discovery.
No Kaggle claim is made or supported. **STOP.**

## 2. Protocol Identity

- `QUALIFICATION_PROTOCOL.md`, SHA-256 `1484e0059f6196f82fe3db27fc07cf33b50cd99fadef298f156e642bb4466dc4`
- Freeze commit `36c9f77` (2026-09-14T17:55:35Z); execution 17:55:41Z–18:02:59Z — freeze predates
  first seed execution by 6 seconds; no protocol modification after any result was observed.
- Fixed H=500, no sweep, no runway model, no other behavioral change; stopping rule (exactly N=50,
  then STOP) observed. Discovery record unmutated (parent protocol V1.5 hash re-verified at launch).

## 3. Seed Provenance (with one disclosed caveat)

- 50050–50099 certified **virgin with respect to the DEV-006/DEV-005 treatments** in
  `QUALIFICATION_SEED_PROVENANCE.md`: zero prior DEV-005/DEV-006 simulations, logs, result rows, or
  design references (only quarantine-guard range mentions); cohort pre-specified by task order and
  the protocol-reserved Stage-2 partition — no post-hoc selection.
- **Caveat (disclosed, not hidden):** EXP-DEV-002's Qualification (2026-09-11) previously consumed
  all 50 seeds under an unrelated treatment (`dev_002_hedged_portfolio` vs `ClosedLoopAgentV2` /
  `Dmitrii-LB2800`). The partition is therefore not "untouched" in the absolute sense; it is
  untouched by the treatment under test, which is the task order's §10 operative criterion.
- Final holdout 214200–214249: zero access beyond runner-guard non-consumption certification.

## 4. Simulator Identity

- kagsim 1.32.7 via validated pure-Python port (`kagsim_py 0.4.0.port1`); Windows binary present
  but not importable on Linux (ModuleNotFoundError, confirmed this session).
- All five task-§4 conditions re-verified this session BEFORE execution: manifest 4/4 + validators
  2/2 match; golden 47,520/47,520 exact; DEV-005 replay 100/100 bit-identical (219.6 s);
  decision events 400/400 identical; runtime probe exit 0 (identical at 72/144/216, single
  permitted divergence at 288).

## 5. Treatment Identity

- Treatment `dev_006_horizon_guard_scheduler.py` (`06db94e5…`), baseline
  `compiled_v54_plus_residual.py` Sub 56146971 (`18402ec6…`), diagnostic DEV-005 (`f52b1686…`),
  control Sub 56146947 (`f651ccd2…`) — all recomputed from disk at launch, all match frozen records.
- Task-order "commit 06db94e5" note: no such Git commit exists; `06db94e5…` is the treatment
  file's SHA-256 prefix. Hashes matched, so no STOP was triggered.

## 6. Primary Results (DEV-006 − baseline, N=50)

Mean **+$517.58**, median $0.00, SD $2,081.17, SE $294.32, t=1.7586, two-sided p=0.0849,
95% CI [−$73.88, +$1,109.04]. Min $0.00, max +$9,881, 5th percentile $0.00, 10% trimmed mean $0.00.
Record **3W/0L/47T** (6.0%/0%/94.0%), nonzero seeds 3. All statistics independently recomputed
from `QUALIFICATION_RAW_RESULTS.json` at full precision — exact match; paired-mean construction
verified on all 50 seeds.

## 7. Tail Results

Min $0.00, max +$9,881, p01–p90 all $0.00, p95 $4,338.40, p99 $9,013.21. Zero losses; worst seed is
a tie. Tail gate (min ≥ −$800.00): **PASS** with full margin.

## 8. H=500 Activation Statistics

- Guard fired: **0 events on 0 seeds** — `QUALIFICATION_HORIZON_GUARD_EVENTS.csv` is empty.
- All 68 at-step-288 specializes (34/arm) verified as maintenance of pre-existing specializations;
  **zero new late entries** in either arm across 200 games.

## 9. Specialization Outcomes

- Activated seeds: 17 per arm (identical sets); 14 activated ties, all exactly $0.00 in both
  matches and both arms (no hidden offsets).
- All 228 specializes (both arms) YARN_SPECIALIZED; 200 confirmation rejections (identical sets);
  liquidity healthy (min $142, zero below floor).

## 10. DEV-005 Comparison (same seeds, identical CRN, unpooled)

DEV-005: mean +$517.58, 3W/0L/47T — **identical to DEV-006 in every reported statistic**.
Mechanism contrast (DEV-006 − DEV-005): mean $0.00, min/max $0.00, 50 ties. The Qualification
cohort cannot distinguish the two treatments; any upside observed here belongs to the shared
DEV-005 backbone (early YARN entries), not to the guard.

## 11. Win Forensic Analysis (all 3 wins traced, 12 games)

50059 (+$7,888), 50069 (+$8,110), 50091 (+$9,881): all step-216 YARN entries, both seats agree to
the dollar, both arms byte-identical at every snapshot. Trajectories show the healthy early-entry
shape (identical through 216, bounded dip −$1.2k–$5.1k, smooth compounding to the win). No hidden
artifact; terminal money equals reward exactly. Full analysis in
`QUALIFICATION_FORENSIC_AUDIT.md`; trajectories in `QUALIFICATION_FORENSIC_TRACES.json`.

## 12. Outlier Sensitivity

Top-1 = 38.2% of total, top-2 = 69.5%; mean-ex-best +$326.49 (survives), mean-ex-top2 +$164.33
(survives); 10% trimmed mean $0.00; median $0.00. The mean is carried by 3 wins — **the mean must
not be described as robust evidence of broad improvement.** Ex-best/ex-top2 survival is noted
without elevating it to a robustness claim, since no frozen gate conditions on it.

## 13. Replicated Mechanism vs Generalized Economic Advantage (pre-registered caution, honored)

- **Replicated mechanism: NOT DEMONSTRATED HERE.** The Discovery mechanism (late-entry loss
  elimination, 4/4 across retrospective + fresh cohorts) faced zero trigger events on this cohort.
  The guard's value proposition was untestable here — neither confirmed nor refuted. Combined
  evidence remains 4/4 eliminations with 0 new tests, plus a third consecutive cohort showing zero
  guard cost (0 prevented wins, 0 new losses across 150 fresh seeds and 100 retrospective games).
- **Generalized economic advantage: NOT ESTABLISHED.** p=0.085 with trimmed mean $0 and only three
  nonzero seeds is, at best, suggestive. The Discovery caution applies verbatim to this cohort.
- Neither conclusion is oversold: the mechanism result is absence-of-test, not failure; the
  statistical result is near-miss, not success.

## 14. Gate Scorecard (frozen criteria, applied exactly)

| Gate | Frozen source | Result |
|------|---------------|--------|
| A. Statistical (t > 1.96, p < 0.05) | V1.1 §2.7 Stage 2 | **NOT PASS** (t=1.76, p=0.085) |
| B. Mechanism (fewer late failures than DEV-005; zero prevented wins) | V1.5 §6 Cat. A | **NOT PASS** (0 vs 0; guard inert) |
| C. Tail-risk (worst ≥ −$800) | V1.1 §2.7 / V1 §4.1 | **PASS** (min $0.00) |
| D. Integrity (hashes, purity, parity) | Discovery manifest + V1.5 | **PASS** (5/5, OK, 5/5) |

**Decision per predeclared rule: INCONCLUSIVE** (A missed → not QUALIFY; no FAIL trigger:
C holds, no significant harm, no guard-caused failure, D holds).

## 15. Qualification Recommendation

**INCONCLUSIVE — do not qualify, do not retire on mechanism grounds, do not re-test without a new
pre-registered protocol.** The treatment survived an untouched (w.r.t. treatment) 50-seed cohort
with zero losses and zero guard cost, but the cohort did not present the failure class the guard
exists to fix, and the statistics miss the frozen bar. Any follow-up (larger N, enriched late-entry
cohort, or holdout consideration) requires a NEW experiment record with a NEW freeze — it is not
authorized by this report.

## 16. Top-10 / Kaggle Relevance

No Top-10 or Kaggle-superiority claim is made or supported by this experiment. Nothing was submitted
to Kaggle; no submission was generated; the final holdout was not touched.

---

## Artifacts

`QUALIFICATION_PROTOCOL.md`, `QUALIFICATION_PROTOCOL_HASH.txt`, `QUALIFICATION_PRECHECK.md`,
`QUALIFICATION_SEED_PROVENANCE.md`, `QUALIFICATION_EXECUTION_MANIFEST.json`,
`QUALIFICATION_EXECUTION_LOG.txt`, `QUALIFICATION_RAW_RESULTS.json`,
`QUALIFICATION_PAIRED_DELTAS.csv`, `QUALIFICATION_DECISION_EVENTS.csv`,
`QUALIFICATION_SPECIALIZATION_EVENTS.csv`, `QUALIFICATION_HORIZON_GUARD_EVENTS.csv`,
`QUALIFICATION_STATISTICS_RECOMPUTED.json`, `QUALIFICATION_RESULT_SUMMARY.json`,
`QUALIFICATION_FORENSIC_AUDIT.md`, `QUALIFICATION_FINAL_REPORT.md`
(+ `run_qualification.py`, `qualification_forensic_traces.py`,
`QUALIFICATION_FORENSIC_TRACES.json`). Results left uncommitted for review. **STOP.**
