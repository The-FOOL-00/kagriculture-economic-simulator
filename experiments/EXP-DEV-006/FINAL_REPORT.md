# FINAL REPORT: EXP-DEV-006 — CONFIRMED-SHOP + HORIZON-GATED WHOLE-ROUTE SCHEDULER
**Fresh Discovery on virgin seeds 248000–248049 (N=50)**

---

## 1. Executive Verdict

**Category A (Strong) — mechanism reproduced on fresh seeds. Recommend Qualification staging; do not auto-run.**

EXP-DEV-006 reproduced the H=500 mechanism on the fresh Discovery cohort: the guard eliminated both fresh late-entry losses (converting −$8,282 and −$6,528 to exactly $0.00), preserved both fresh wins, left 48/48 other seeds bit-identical, and introduced zero new losses. Primary: mean +$290.90, 2W/0L/48T, worst seed $0.00. This is Discovery evidence only — not Qualification, not Kaggle evidence. H=500 is not claimed globally optimal.

## 2. Protocol Identity

- `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_5.md`, SHA-256 `e52a0570a8bc9cfeafe1165f49f4c9d77ef9a3b7aa030783f8aef7e9ee7b04e8`
- Freeze commit `8bc8248` (2026-09-14T17:32:11Z), manifest record `f42c72b` (17:32:26Z); execution 17:32:31Z–17:39:36Z — freeze predates execution.
- Fixed H=500, no sweep, no runway model, no other behavioral change; stopping rule (exactly N=50, then STOP) observed.

## 3. Seed Provenance

- Block `248000–248049` certified 100% virgin in `SEED_PROVENANCE.md`: zero execution/result/strategy/sweep exposure across 1644 `.py` files, all result databases, 68-commit Git history (2 doc-only hits), stride/range analysis (0 reachable), and 163 conversation stores (0 execution contexts).
- Buffers: 33,751 seeds above holdout 214200–214249; disjoint from all 7 quarantined ranges (runner hard-abort verified in code; no abort triggered).

## 4. Simulator Identity

- kagsim 1.32.7 via validated pure-Python port (`kagsim_py 0.4.0.port1`, `ENGINE_VERSION 1.32.7`); Windows binary unloadable on Linux.
- All 5 §8 conditions re-verified this session: manifest 4/4 + validators 2/2 match; golden 47,520/47,520 exact; DEV-005 replay 100/100 bit-identical (202.3 s); no source changes; engine 1.32.7. Preflight 9/9 passed.

## 5. Treatment Identity

- Treatment `dev_006_horizon_guard_scheduler.py` (`06db94e5…`), baseline `compiled_v54_plus_residual.py` Sub 56146971 (`18402ec6…`), diagnostic DEV-005 (`f52b1686…`), control Sub 56146947 (`f651ccd2…`) — all recomputed from disk, all match frozen records.

## 6. One-Factor Proof

- Static diff DEV-006 vs DEV-005 is byte-verified in `TREATMENT_DIFF_AUDIT.md`: allowed difference (H=500 parameter + predicate + `REJECT_HORIZON` branch + telemetry + class rename) only; valuation, confirmation gate, routes, worker/terminal logic untouched.
- Runtime probe (`treatment_identity_probe.py`, exit 0): identical decisions/values at steps 72/144/216; single permitted divergence at step 288 (SPECIALIZE vs REJECT_HORIZON, same candidate/value).
- Game-level purity gate: nonzero contrast on exactly the 2 guard seeds; guard fired only at step 288. **Purity OK.**

## 7. Primary Results (DEV-006 − baseline, N=50)

Mean **+$290.90**, median $0.00, SD $1,469.71, SE $207.85, t=1.40, two-sided p=0.168, 95% CI [−$126.79, +$708.59]. Record **2W/0L/48T** (4.0%/0%/96.0%). All statistics independently recomputed from RAW_RESULTS at full precision — exact match.

## 8. Tail Results

Min $0.00, max +$8,738, p01–p95 all $0.00, p99 $7,301.81. Zero losses; worst seed is a tie. The left tail that existed under DEV-005 (−$8,282, −$6,528) is absent under DEV-006.

## 9. H=500 Activation Statistics

- Guard fired: 4 events on 2 seeds (248007, 248009) — always step 288, always first-time YARN entry, always confirmed shop, model values +$7,520.60/+$5,919.68.
- Guard could never fire at steps 72/144/216 by construction (remaining 648/576/504 ≥ 500).
- 26 at-288 DEV-006 specializes, all verified maintenance of pre-existing specializations; **zero new late entries** under the guard.

## 10. Specialization Outcomes

- Activated seeds: 13 (DEV-006) vs 15 (DEV-005); difference is exactly the 2 guard-saved seeds.
- All 184 specializes (both arms) YARN_SPECIALIZED; 168 confirmation rejections (identical sets); liquidity healthy (min $142, zero below floor).
- Activated ties (11 seeds): exactly $0.00 in both matches and both arms — no hidden offsets.

## 11. DEV-005 Comparison (same fresh seeds, identical CRN, unpooled)

DEV-005: mean −$5.30, 2W/2L/46T, min −$8,282. Mechanism contrast (DEV-006 − DEV-005): mean +$296.20, min $0.00, max +$8,282, nonzero on exactly the 2 guard seeds. Both arms' wins identical (+$5,807, +$8,738); DEV-006 = DEV-005 with the 2 late losses removed and nothing else changed.

## 12. Best/Worst Seed Forensic Analysis

- Best (248029, +$8,738): step-216 YARN entry; investment dip (−$1,153 @288) compounding to a win over 504 steps of runway. Both arms byte-identical at all 60 money snapshots.
- Worst (all 48 ties at $0.00): no DEV-006 loss exists; the prevented worst cases (248007/248009) show the late-entry cascade — step-288 entry, investment dip, violent non-recovering sawtooth to −$8,282/−$6,528 under DEV-005 vs exactly-baseline money at every snapshot under DEV-006.
- Full trajectories: `forensic_traces.json` (16 games); analysis in `FORENSIC_AUDIT.md`.

## 13. Outlier Sensitivity

Top-1 = 60.1% of total, top-2 = 100%; mean-ex-best +$118.51 (survives), mean-ex-top2 $0.00; 10% trimmed mean $0.00; median $0.00. The mean is carried by 2 wins — **do not describe DEV-006 as robust because its mean is positive.** Robustness here rests on the replicated loss-elimination mechanism (4/4 across cohorts), not on the mean.

## 14. Mechanism Generalization Assessment

The H=500 guard eliminated the same class of late-entry failure on unseen seeds — it did not depend on the retrospective two seeds. Combined cross-cohort evidence: 4/4 late-entry losses → $0.00, 7/7 wins preserved, 96/96 other seeds bit-identical, 0 prevented wins, 0 new losses. The model's ~$14k/seed overvaluation of late entry (predicting +$5.9k/+$7.5k, realizing −$6.5k/−$8.3k) confirms the valuation model cannot price the late-transition cascade. Limits: N=2 fresh activations (4 total); 100%-YARN cohort (non-YARN late entries untested); primary mean not significant (p=0.168).

## 15. Qualification Recommendation

**Recommend Qualification staging.** All Category-A clauses met: positive mean (+$290.90), acceptable worst case ($0.00 ≥ −$6,000), ex-best survival (+$118.51), fewer late failures than DEV-005 arm (0 < 2), zero prevented wins, verified one-factor identity, independently recomputed statistics, no new failure mode. **Do not run Qualification automatically** — await explicit review. Suggested Qualification would test DEV-006 (frozen `06db94e5`) on 50050–50099 against Sub 56146971.

## 16. Top-10 Relevance

No Top-10 or Kaggle-superiority claim is made or supported by this experiment. Relevance is indirect: DEV-006 is now the first treatment in the DEV chain combining (a) fresh-Discovery upside preservation with (b) a replicated tail-risk fix and zero observed cost — the profile a future Qualification candidate requires. Whether that profile survives unseen Qualification seeds and live Kaggle dynamics is untested.

---

## Artifacts

`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_5.md`, `PROTOCOL_HASH.txt`, `SEED_PROVENANCE.md`, `TREATMENT_DIFF_AUDIT.md`, `PRECHECK.md`, `EXECUTION_MANIFEST.json`, `EXECUTION_LOG.txt`, `RAW_RESULTS.json`, `PAIRED_DELTAS.csv`, `DECISION_EVENTS.csv`, `SPECIALIZATION_EVENTS.csv`, `HORIZON_GUARD_EVENTS.csv`, `STATISTICS_RECOMPUTED.json`, `FORENSIC_AUDIT.md`, `FINAL_REPORT.md` (+ `run_exp_dev_006.py`, `treatment_identity_probe.py`, `forensic_traces.py`, `forensic_traces.json`). Results left uncommitted for review. **STOP.**
