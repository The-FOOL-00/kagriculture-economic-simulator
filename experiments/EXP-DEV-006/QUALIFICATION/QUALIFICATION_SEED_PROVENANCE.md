# SEED PROVENANCE AUDIT: QUALIFICATION PARTITION CERTIFICATION
**Experiment**: EXP-DEV-006 Qualification (frozen DEV-006 treatment)
**Date**: 2026-09-14
**Auditor**: Muse Code powered by Meta Muse Spark (Zero-Leakage Governance)
**Partition Under Audit**: Seeds `50050` to `50099` ($N=50$ contiguous seeds)
**Certification Status**: **VIRGIN WITH RESPECT TO THE DEV-006/DEV-005 TREATMENTS — ZERO PRIOR
SIMULATIONS UNDER EITHER TREATMENT. ONE DISCLOSED PRIOR USE UNDER AN UNRELATED TREATMENT (see §2).**

---

## 1. Scope of This Audit

The task order (§10) requires the range to be "virgin with respect to this treatment": no prior
simulation may have consumed these seeds under DEV-006, and no post-hoc selection may have been
used. Absolute partition virginity is separately assessed and honestly reported in §2.

## 2. Disclosed Prior Consumption (unrelated treatment — EXP-DEV-002 Qualification, 2026-09-11)

`experiments/EXP-DEV-002/qualification/` consumed all 50 seeds 50050–50099 (verified: 50 distinct
seeds, min 50050, max 50099, contiguous) under treatment `dev_002_hedged_portfolio`
(`cdd19cc8…`) versus baselines `ClosedLoopAgentV2` and `Dmitrii-LB2800`. Verdict: QUALIFICATION FAIL.
This prior run involved **neither** the DEV-005 scheduler **nor** the DEV-006 horizon guard, and
neither the V54++ baseline (`compiled_v54_plus_residual.py`) nor the DEV-006 treatment.
It is the ONLY execution/result/log exposure of 50050–50099 found anywhere in the workspace:

- `QUALIFICATION_RAW_RESULTS.json`: only `.json` under `experiments/`/`results/` with
  `"seed": 5005x–5009x` rows (scoped grep over both trees).
- `QUALIFICATION_PAIRED_DELTAS.csv`: only `.csv` under `experiments/`/`results/`/`scratch/`
  with `^5005x–5009x,` seed rows (scoped grep over all three trees).
- `QUALIFICATION_EXECUTION_LOG.txt`, `QUALIFICATION_RUN_MANIFEST.json`,
  `QUALIFICATION_STATISTICS_RECOMPUTED.json`, `recompute_qualification_statistics.py`: same run.

The qualification partition is the program-shared Stage-2 partition
(`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md` §2.7: "Evaluated on Seeds 50050–50099 with frozen
code"), so this prior Stage-2 use by a different frozen treatment is consistent with the frozen
program design. It does not constitute exposure *of the DEV-006 treatment* to these seeds.

## 3. Zero DEV-006 / DEV-005 Exposure (all governance dimensions)

| Governance Dimension | Scan Method | Hits on 50050–50099 | Result |
| :--- | :--- | :---: | :--- |
| **DEV-006 execution sites** | Files referencing `Dev006HorizonGuardScheduler` (bounded search, `*.py`) | 6 files, cohorts 247xxx/248xxx only | Clean |
| **DEV-006 runners** | Cohort constants + quarantine guards in `run_exp_dev_006.py`, `run_horizon_killtest.py`, `run_killtest_port.py` | 50050–50099 appears ONLY in `assert_not_quarantined` hard-abort guards | Clean |
| **DEV-005 runners** | `run_exp_dev_005.py` quarantine | 50050–50099 hard-abort guard (line 61) | Clean |
| **Treatment sources** | Seed-specific literals in `dev_005…py`, `dev_006…py` | 0 (design derived from 247xxx retrospective; H=500 fixed, not fit) | Clean |
| **Result databases (`.json`)** | `"seed": 500[5-9][0-9]` over `experiments/`, `results/` | Only EXP-DEV-002 (unrelated treatment) | Clean |
| **Result tables (`.csv`)** | `^500[5-9][0-9],` over `experiments/`, `results/`, `scratch/` | Only EXP-DEV-002 (unrelated treatment) | Clean |
| **Execution logs (`.txt`)** | `Seed 500xx` lines in all DEV-005/DEV-006/kill-test logs | 0 (`grep -c "Seed 500"` = 0 on all three logs) | Clean |
| **Scratch audit scripts** | `kagsim`/`Game(`/`play_match` imports in the 5 qual-audit scripts | 0 (static auditors; never execute games) | Clean |
| **Git history** | `git log --grep`, pickaxe `-S 50050`/`-S 50099` | Protocol/manifest range-reservation mentions only; treatment file touched by freeze commit `8bc8248` only | Clean |
| **Forensic tracers** | `forensic_traces.py` key seeds | 248002/248007/248009/248029 (consumed Discovery seeds) only | Clean |

Documentation-only range mentions (quarantine tables, protocol reservations, audit-target listings
in ~145 files) constitute no execution, result, strategy-selection, or sweep exposure: no game was
simulated under DEV-005/DEV-006, no outcome was observed, and no DEV-006 design decision was
conditioned on these seeds.

## 4. No Post-Hoc Selection

The cohort (50050–50099) was specified verbatim by the task order and matches the protocol-reserved
Stage-2 partition (V1 §4.1, V1.1 §2.7). No seed was added, removed, or replaced on the basis of any
observed outcome; no Qualification outcome existed at freeze time.

## 5. Non-Consumption Certification Procedure Compliance

The final holdout (214200–214249) was not searched, listed, read, executed, or modified beyond
verifying that (a) the Qualification runner hard-aborts on it and (b) no Qualification artifact
references it. The Qualification cohort (50050–50099) is a disjoint block 164,101 seeds below
214200 (verified by integer comparison in the runner guard, not by inspecting holdout contents).

## 6. Certification Verdict

Partition **`50050–50099`** ($N=50$) is formally certified as **VIRGIN WITH RESPECT TO THE FROZEN
DEV-006 TREATMENT AND THE DEV-005 DIAGNOSTIC** and authorized as the Qualification cohort for
**EXP-DEV-006**, with the §2 prior unrelated-treatment use disclosed as a standing caveat on the
word "untouched" in its absolute sense.
