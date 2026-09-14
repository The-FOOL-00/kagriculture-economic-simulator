# DEVELOPMENT EXPERIMENT PROTOCOL V1.5
## EXP-DEV-006: Confirmed-Shop + Horizon-Gated Whole-Route Scheduler over V54++ Residual Preemption

**Document Identifier**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_5.md`
**Experiment Identifier**: `EXP-DEV-006`
**Date**: 2026-09-14
**Status**: PRE-REGISTRATION FREEZE (Must be committed to Git prior to first simulation)
**Governance Authority**: Zero-Leakage Governance
**Authoritative Baseline**: `candidates/compiled_v54_plus_residual.py` (Submission `56146971`)
**Baseline Verified SHA-256**: `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`
**Treatment Candidate**: `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py`
**Treatment SHA-256**: `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb`
**Diagnostic Reference**: `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py`
**Diagnostic SHA-256**: `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78`
**Discovery Partition**: Seeds `248000` to `248049` ($N=50$ contiguous virgin seeds, 200 paired CRN matches)
**Prior Retrospective Evidence**: `experiments/EXP-DEV-006_HORIZON_KILLTEST/VERDICT.md` (SUPPORTED, mechanism-only, consumed cohort)

---

## 1. Executive Summary & Research Question

### 1.1 Context from Preceding Experiments
- **EXP-DEV-004**: Whole-route macro production planning captures massive specialization upside, but suffers premature-specialization failures.
- **EXP-DEV-005**: Confirmed-shop gating dramatically reduces premature specialization losses. Fresh Discovery (247000–247049): mean +$797.76, 5W/2L/43T. Both residual losses entered specialization at Step 288 (Day 12).
- **HORIZON KILL-TEST** (retrospective, consumed cohort only): a fixed remaining-horizon guard (H=500) converted both Step-288 losses to exactly $0.00, preserved all 5 wins, left 48/48 other seeds bit-identical. Verdict SUPPORTED **as a mechanism result only** — NOT generalization, NOT Qualification, NOT Kaggle evidence.

### 1.2 Primary Research Question
> *"Does adding a fixed remaining-horizon guard (H=500) to the confirmed-shop whole-route scheduler preserve the large upside of DEV-005 while eliminating its late-specialization tail failures on fresh unseen seeds?"*

### 1.3 Secondary Research Question
> *"Does the H=500 guard eliminate the same class of late-entry failure seen retrospectively, or did the retrospective result depend on the particular two seeds?"*

---

## 2. Formal Hypotheses

### Primary Hypothesis ($H_1$)
> A confirmed-shop whole-route planner that additionally rejects NEW specialization when `remaining_steps < 500` will reproduce positive expected economic value over V54++ on unseen seeds while exhibiting materially fewer late-specialization failures than the ungated DEV-005 rule.

### Null Hypothesis ($H_0$)
> The H=500 guard does not reproduce its retrospective effect on fresh seeds (no reduction in late-entry failures, or the guard destroys legitimate upside), producing a paired mean delta indistinguishable from or worse than baseline/DEV-005.

---

## 3. Treatment Definition: ONE-FACTOR CONTINUATION OF DEV-005

### 3.1 Starting Point (exact)
The treatment is based **exactly** on `dev_005_confirmed_shop_scheduler.py`, including:
- Confirmed-shop gating rule (Protocol V1.4 §3): specialization requires the route's required shop in `unlocked_shops`, $\tau = 1500.0$, $L_{\min} = 100.0$.
- Identical route registry, physical feasibility model, market absorption engine, preemption parameters, checkpoint schedule (72/144/216/288), worker routing, terminal logic.

### 3.2 The ONE New Rule: HORIZON_GUARD (H = 500, FIXED)
A NEW specialization (transition from `BASELINE_BACKBONE` to a specialized route) is allowed only when:

$$\text{remaining\_steps} = 720 - \text{step} \ge 500$$

If `remaining_steps < 500`, the planner rejects the new specialization (`REJECT_HORIZON`) and retains the non-specialized/generalist route. Pre-existing specializations (entered at earlier checkpoints) are maintained/reverted exactly as in DEV-005; the guard applies ONLY to new entries from `BASELINE_BACKBONE`.

Consequence on the fixed checkpoint schedule: the guard can only ever fire at Step 288 (remaining 432 < 500). Steps 72/144/216 (remaining 648/576/504) are unaffected by construction.

### 3.3 H = 500 IS FIXED — NO SWEEP
Do NOT sweep, optimize, or fit H from the fresh Discovery data. If H=500 fails, that is the experimental result; any replacement H becomes EXP-DEV-007.

### 3.4 NO RUNWAY MODEL
The retrospective audit's "required production runway vs remaining horizon" idea is recorded as a future hypothesis ONLY. It is NOT implemented here.

### 3.5 Explicitly Forbidden Additions
No new crop logic, animal logic, margin/liquidity threshold, market rules, route candidates, worker routing, terminal liquidation, valuation formula, or shop rule.

---

## 4. Simulator Identity

**Authoritative engine**: kagsim 1.32.7. The Windows CPython binary (`kagsim.cp314-win_amd64.pyd`) is not loadable in this Linux execution environment, so the validated pure-Python port is used under Protocol §8, with all five conditions verified and recorded in `PRECHECK.md`:
1. `PORT_MANIFEST.json` unchanged (4/4 file hashes match);
2. Golden traces exact (47,520/47,520 checkpoints);
3. Frozen DEV-005 replay 100/100 bit-identical (re-run 2026-09-14);
4. No simulator source changes after validation;
5. Engine version remains 1.32.7.

No new simulator implementation was created.

---

## 5. Experimental Design & Endpoints

### 5.1 Discovery Sample Size
- $N=50$ contiguous virgin seeds (`248000–248049`, certified in `SEED_PROVENANCE.md`).
- 200 balanced Common Random Number (CRN) matches per seed-batch:
  - Primary arm: DEV-006 vs V54++ baseline × 2 seats → $\Delta^{6}_i = 0.5(\Delta^{6}_{i,0}+\Delta^{6}_{i,1})$.
  - Diagnostic arm: DEV-005 vs V54++ baseline × 2 seats (identical CRN) → $\Delta^{5}_i$.
  - Mechanism contrast: $\Delta^{6}_i - \Delta^{5}_i$ per seed (diagnostic, unpooled from other experiments).

### 5.2 Primary Endpoint
- **Paired Mean Cash Delta**: $\Delta \mu_6 = \frac{1}{N}\sum_i \Delta^{6}_i$ (DEV-006 minus V54++ baseline).

### 5.3 Secondary Endpoints
- DEV-005 vs baseline on the SAME fresh partition (diagnostic comparison; do not pool experiments statistically).
- Full statistic suite (§7 of task order): N, mean, median, SD, SE, t, two-sided p, 95% Student-t CI, 10% trimmed mean, p01–p99, min/max, W/L/T + rates, means excluding best/worst/top-two.
- Mechanism metrics: specializations attempted/accepted, rejected by confirmation gate, rejected by horizon gate, before/after H=500 boundary, late-specialization incidents, terminal dead inventory proxies, worker/liquidity/asset/market mismatch flags.
- Outlier sensitivity: top-1 / top-2 contribution share (DEV-005 warning: mean +$797.76 with trimmed mean $0).

---

## 6. Pre-Registered Discovery Decision Gates

| Outcome Category | Quantitative Criteria | Mechanistic Interpretation | Decision |
| :--- | :--- | :--- | :--- |
| **Category A (Strong)** | $\Delta\mu_6 > 0$ AND worst seed $\ge -\$6{,}000$ AND mean-ex-best $> 0$ AND late-entry failures < DEV-005 arm AND zero horizon-prevented large wins | H=500 mechanism reproduced on fresh seeds | **Recommend Qualification staging (do not auto-run)** |
| **Category B (Partial)** | $\Delta\mu_6 > 0$ but fails one Category-A robustness clause | Directional support, robustness gap | **Retain in Discovery; diagnose** |
| **Category C (Null)** | $\Delta\mu_6 \approx 0$ (95% CI covers 0 with small magnitude) and no mechanism separation | Guard inert on fresh seeds | **No-Go / mechanism not reproduced** |
| **Category D (Harm)** | $\Delta\mu_6 < 0$ materially, or guard prevents large wins, or new severe failure mode | Guard destructive or useless | **Reject $H_1$; record as failed generalization** |

A statistically non-significant result is not automatically useless; a huge mean driven by one seed is not automatically strong. Trimmed mean, median, and top-1/top-2 concentration govern the robustness reading.

---

## 7. Governance & Stopping Rule

1. **Quarantined**: `50050–50099`, `214200–214249`, `50000–50499`, `245000–245049`, `246000–246049`, `247000–247049`. The runner hard-aborts on any quarantined seed.
2. **Frozen artifacts**: `56146971` (`compiled_v54_plus_residual.py`), `56146947` (`compiled_v54_plus_shop.py`), all DEV-004/DEV-005 historical artifacts — read-only, hash-verified, never modified.
3. **No Kaggle submission**; live Kaggle analysis stays separate.
4. **No inspection-driven treatment changes**: individual fresh-seed outcomes must not be inspected during execution to change the treatment. Forensics run AFTER all 50 seeds complete.
5. **Stopping rule**: execute exactly $N=50$ seeds (`248000–248049`), then STOP. No extension, no replacement of seeds, no H re-tuning, no automatic Qualification.

---

## 8. Claim Discipline

Allowed: "EXP-DEV-006 reproduced/failed to reproduce the H=500 mechanism on the fresh Discovery cohort." / "The treatment reduced/increased late-entry failures." / "The result is Discovery evidence."
Forbidden: "H=500 is globally optimal." / "Top-10 is proven." / "Kaggle superiority is proven." / "Qualification is guaranteed."

---

## 9. Protocol Commitment Rule

This protocol and its SHA-256 hash must be written to disk, verified, and committed to Git repository history BEFORE the first simulation of EXP-DEV-006 begins. The protocol commit hash and timestamp are recorded in `PROTOCOL_HASH.txt` and `EXECUTION_MANIFEST.json`.
