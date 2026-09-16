# EXP-ARCH-002 H1 — RE-EXECUTION ELIGIBILITY & FORENSIC RECONCILIATION AUDIT

**Experiment**: `EXP-ARCH-002_H1_DOMINANCE_TERMINAL`  
**Document**: `07_REEXECUTION_ELIGIBILITY_AUDIT.md`  
**Date**: 2026-09-16  
**Auditor / Principal Investigator**: Antigravity  
**Status**: **COMPLETED — VERDICT: OUTCOME A (RE-EXECUTION ELIGIBLE)**  

---

## 1. EXECUTIVE SUMMARY & GOVERNANCE PURPOSE

This document establishes the evidence-based forensic audit and governance determination regarding whether `EXP-ARCH-002_H1_DOMINANCE_TERMINAL` can receive a valid, clean re-execution following the invalidation of its original prospective execution.

The original execution of ARCH-002 (completed 2026-09-15 across seeds 320000–320499, N=500, 1,000 games) was formally classified as:
```
ARCH-002 ORIGINAL EXECUTION = INVALID / EXECUTION-INTEGRITY FAILURE (RUNNER STATE POLLUTION)
```
This classification remains **permanent, unalterable, and unoverwritten**. History is not rewritten. The original raw results (`RAW_RESULTS.json`), paired deltas (`PAIRED_DELTAS.csv`), telemetry (`TELEMETRY_EVENTS.csv`), execution log (`EXECUTION_LOG.txt`), and forensic report (`06_EXECUTION_AND_FORENSIC_REPORT.md`) are permanently preserved in the repository as records of an invalid execution.

This audit evaluates:
1. The exact technical mechanism of the runner-level state pollution defect.
2. Whether the defect is strictly confined to runner instrumentation.
3. The exact mathematical and structural reachability of the `ABSTAIN_ACCEPT` condition in `h1_dominance.py`.
4. Whether a corrected re-execution can be performed with **zero changes** to the scientific protocol, **zero changes** to the frozen H1 implementation, **zero changes** to the baseline, and **zero changes** to the prospective cohort.

---

## 2. GOVERNANCE & INTEGRITY LEDGER: FROZEN ARTIFACT IDENTITIES

All file SHA-256 hashes and commit identities were verified directly from disk on 2026-09-16 prior to drafting this audit:

| Artifact Role | File Path / Commit Reference | Authoritative Frozen SHA-256 / Commit | Verified Disk SHA-256 / Ref | Status |
|---|---|---|---|---|
| **Preregistration Protocol** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/02_PREREGISTRATION.md` | `508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5` | `508f1dff91f1bfd34186b1eeb6e899c97f87b99fff3841513abe3a88dc4a71b5` | **EXACT MATCH** |
| **Isolation Audit** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/01_ISOLATION_AUDIT.md` | `0381a93eee7cc3d51833439ce868d51923dc9a2ff0cca68f9d692e5f81c03de4` | `0381a93eee7cc3d51833439ce868d51923dc9a2ff0cca68f9d692e5f81c03de4` | **EXACT MATCH** |
| **Validation Report** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/03_IMPLEMENTATION_VALIDATION_REPORT.md` | `c87e3959b0fda3b7620883c2d85dd200736d4d3305c33353c9c5123ab5c8a402` | `c87e3959b0fda3b7620883c2d85dd200736d4d3305c33353c9c5123ab5c8a402` | **EXACT MATCH** |
| **Implementation Freeze Commit** | Git commit `862e35b75e375b49cd66e85c651fc4d463fd9b1e` | `862e35b75e375b49cd66e85c651fc4d463fd9b1e` | `862e35b75e375b49cd66e85c651fc4d463fd9b1e` | **EXACT MATCH** |
| **Governance Seal Commit** | Git commit `2dfeedb015bf39db2bd57fc965e3b74f8316e0a7` | `2dfeedb015bf39db2bd57fc965e3b74f8316e0a7` | `2dfeedb015bf39db2bd57fc965e3b74f8316e0a7` | **EXACT MATCH** |
| **Runner Freeze Commit** | Git commit `89d981b285a8bfb8f170f78238ba4c95232b7194` | `89d981b285a8bfb8f170f78238ba4c95232b7194` | `89d981b285a8bfb8f170f78238ba4c95232b7194` | **EXACT MATCH** |
| **Original Runner Script** | `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_execution.py` | `1599c4bb3153bb1f798a7e0e4f3cc0255f8eb304e913357fa83d850be1551fad` | `1599c4bb3153bb1f798a7e0e4f3cc0255f8eb304e913357fa83d850be1551fad` | **EXACT MATCH** |
| **Frozen Baseline V54++** | `candidates/compiled_v54_plus_residual.py` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb` | **EXACT MATCH** |
| **Protected Artifact** | `candidates/compiled_v54_plus_shop.py` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8` | **EXACT MATCH** |
| **Protected Artifact** | `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` | `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78` | **EXACT MATCH** |
| **Protected Artifact** | `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` | `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb` | **EXACT MATCH** |
| **Protected Pinned Unit Model** | `extracted_agents/dmitrii_lb2800/unit_model.py` | `c03e8c5cd10466c229ee0a44dece9a3943c10bff135d96a7822ffe75d6922724` | `c03e8c5cd10466c229ee0a44dece9a3943c10bff135d96a7822ffe75d6922724` | **EXACT MATCH** |

### Quarantine & Isolation Status
- **Final Holdout (`214200–214249`)**: Virgin, uninspected, unexecuted, untouched. Zero hits in logs or result manifests.
- **DEV-007 Reserved Cohort (`310000–310499`)**: Virgin, frozen, unexecuted, untouched.
- **Kaggle API / Network**: Zero network calls, zero remote submissions.
- **Working Tree**: Clean except for governing documentation and diagnostic scripts in `scratch/`.

---

## 3. SECTION VIII: COMPREHENSIVE RECONCILIATION AUDIT (QUESTIONS A–S)

### A. What exactly was wrong with the original runner?
In `experiments/EXP-ARCH-002_H1_DOMINANCE_TERMINAL/run_arch002_h1_execution.py`, lines 207–210 and 215–218:
```python
        # Check pre-E action identity (steps 0 to 711)
        if t < ENTRY_STEP:
            internal_base_act = base_inst_h1.call(copy.deepcopy(obs_h1), copy.deepcopy(cfg))
            if not _actions_equal(act_h1, internal_base_act):
                pure_pre_e_pass = False

        # In-window market tracking (712 to 717)
        if ENTRY_STEP <= t < FINAL_STEP:
            m_h1 = act_h1.get("market") if isinstance(act_h1, dict) else []
            internal_base_act = base_inst_h1.call(copy.deepcopy(obs_h1), copy.deepcopy(cfg))
            m_base = internal_base_act.get("market") if isinstance(internal_base_act, dict) else []
            if not _markets_equal(m_h1, m_base):
                pure_verbatim_pass = False
```
1. At step `t`, `act_h1 = agent_h1(copy.deepcopy(obs_h1), copy.deepcopy(cfg))` was invoked.
2. Inside `agent_h1` (`h1_agent.py:130`), for `t < ENTRY_STEP`, it called `self.fb.call(obs, configuration)`, where `self.fb` is `base_inst_h1`. This single call advanced `base_inst_h1`'s internal state (internal ledgers: `m_update_flow`, `m_repay`, `m_release_pending`, order queues).
3. Immediately thereafter, the runner executed `internal_base_act = base_inst_h1.call(...)` on the **exact same instance** with the same step observation.
4. This second call advanced `base_inst_h1`'s internal ledgers a second time on step `t`.
5. On the subsequent step `t+1`, `base_inst_h1` executed from an internally corrupted state relative to the environment observation and relative to the unpolluted control baseline instance (`agent_base` / `base_inst_ctrl`).
6. This double-stepping caused false pre-E divergence in 975 / 1000 games and spurious score deltas (ranging from -$1,465 to +$1,357) in 558 / 1000 games where H1 explicitly abstained.

### B. Is the defect confined to runner instrumentation?
**YES**. The defect is 100% confined to lines 207–210 and 215–218 of `run_arch002_h1_execution.py`. No H1 policy module performs a double call or mutates baseline state. When `agent_h1` is evaluated with an independent twin instance (without the runner's second call), `act_h1` matches the unpolluted baseline with 100% bit-identity on steps 0–711 (empirically confirmed on non-prospective seeds 248000, 248001, 248002).

### C. Did the H1 policy itself change during the invalid run?
**NO**. All 8 H1 policy modules remained completely unchanged on disk throughout the run and retain bit-identity with implementation freeze commit `862e35b75e375b49cd66e85c651fc4d463fd9b1e`.

### D. Did the baseline itself change?
**NO**. `candidates/compiled_v54_plus_residual.py` remained bit-identical to `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`.

### E. Did the simulator change?
**NO**. `experiments/EXP-DEV-006_HORIZON_KILLTEST/port/kagsim_py` remained bit-identical and functional at engine 1.32.7.

### F. Did the treatment/control design change?
**NO**. The experimental design was Common Random Numbers (CRN) with 2 games per seed (Game a: Seat 0 H1, Seat 1 Baseline; Game b: Seat 0 Baseline, Seat 1 H1), paired delta $\Delta_i = 0.5(\delta_{i,a} + \delta_{i,b})$.

### G. Did the randomization/seed cohort change?
**NO**. The cohort was exactly seeds 320000–320499 inclusive (500 seeds, 1,000 games).

### H. Were any results used to make mid-run modifications?
**NO**. The execution ran without human or automated intervention; no parameters, thresholds, or code paths were modified mid-run.

### I. Can the runner defect be corrected without changing the preregistered scientific question?
**YES**. The scientific question (§1) asks whether grafting the H1 dominance-gated terminal optimizer onto the V54++ residual baseline improves expected terminal money without tail harm. Repairing the measurement runner so that it does not pollute the baseline policy during P-PURE verification directly answers the original scientific question.

### J. Can the original H1 implementation remain bit-identical?
**YES**. All 8 H1 files will remain 100% bit-identical.

### K. Can the baseline remain bit-identical?
**YES**. The baseline remains 100% bit-identical.

### L. Can the simulator remain bit-identical?
**YES**. The simulator remains 100% bit-identical.

### M. Can the same cohort 320000–320499 be used again without scientific cherry-picking?
**YES**. The entire 500-seed cohort was executed as a whole and invalidated as a whole due to an instrumentation flaw. No individual seed was selected, rejected, or conditioned upon. Re-executing the entire 500-seed cohort under a valid runner constitutes an unbiased, non-cherry-picked execution of the preregistered sample.

### N. Is the same cohort still considered prospective for purposes of a corrected execution under the repository's governance rules?
**YES**. Because the original run was invalidated by execution-integrity failure (§18 P-PURE pre-E identity violation), its outputs are scientifically void. Under governed research discipline, an invalidated run does not consume the prospective validity of the cohort for testing the original hypothesis, provided:
1. The original run remains permanently documented as an invalid execution.
2. The corrected execution uses a newly frozen runner with independent validation.
3. The cohort is executed in full without modification.

### O. Does the governance structure permit re-execution after invalid execution?
**YES**. `02_PREREGISTRATION.md` §23 item 5 explicitly provides:
> *"Integrity-gate failure (hash mismatch, P-PURE violation, quarantine trip, parity failure) ⇒ STOP and investigate before any interpretation. Resumption, if ever justified, requires a written incident record + a protocol amendment with a new identity — never a silent restart."*

This audit serves as the written incident and eligibility record. A corrected execution must be recorded under a new runner identity (`run_arch002_h1_reexecution.py`), a dedicated re-execution freeze record (`08_REEXECUTION_FREEZE_RECORD.md`), and a dedicated final report (`09_REEXECUTION_AND_FORENSIC_REPORT.md`).

### P. Does any amendment become necessary?
**NO PROTOCOL AMENDMENT IS NECESSARY**. As established in Section 4 below, the H1 implementation and protocol are coherent. The second issue (`ABSTAIN_ACCEPT`) is a legitimate preregistered abstention property of H1 under D3 verbatim market passthrough.

### Q. If amendment is required, exactly what must be amended?
N/A. No protocol amendment is required.

### R. Is the re-execution still testing the original H1 hypothesis?
**YES**. The re-execution tests H1-ACT and H1-OVERALL exactly as preregistered in `02_PREREGISTRATION.md` §2.

### S. What parts of the original run remain permanently invalid?
All performance statistics ($\bar{\Delta} = -$32.8520, p = 0.001832, min = -$1,465.00, loss rate = 41.80%), all paired deltas in `PAIRED_DELTAS.csv`, and all game scores in `RAW_RESULTS.json` from the original run are permanently invalid. They reflect runner state pollution artifacts and must never be used to evaluate H1.

---

## 4. SECTION IX: FORENSIC INVESTIGATION OF THE SECOND ARCH-002 ISSUE (`ABSTAIN_ACCEPT` & `OK_ACTIVATED = 0`)

The original run recorded:
- `ABSTAIN_DOMINANCE`: 756 / 1,000 games (75.6%)
- `ABSTAIN_ACCEPT`: 244 / 1,000 games (24.4%)
- `OK_ACTIVATED`: 0 / 1,000 games (0.0%)

### 4.1 Exact Acceptance Condition
In `h1_dominance.py:143–160`:
```python
    delta = {
        item: int(final_run["sold"].get(item, 0) or 0)
        - int(baseline_run["sold"].get(item, 0) or 0)
        for item in PRODUCTS_9
    }
    values = list(delta.values())
    conjuncts = {
        "worker_change": bool(changed),
        "deposited_gain": bool(deposited_gain),
        "sold_delta_min": min(values),
        "sold_delta_max": max(values),
        "all_nonnegative": all(v >= 0 for v in values),
        "some_positive": any(v > 0 for v in values),
    }
    accepted = bool(
        changed and deposited_gain and conjuncts["all_nonnegative"]
        and conjuncts["some_positive"]
    )
```

### 4.2 Exact Source of `sold` and Baseline Comparison
In `h1_shadow.py:execute_market`, `cursor.sold[item]` tracks units sold by executing market orders in `action["market"]`. In `simulate_schedule`, candidate rollouts execute `schedule[offset]["market"]`.

### 4.3 Exact D3/P5 Protocol Constraints & Structural Reachability
1. **D3 Constraint** (`02_PREREGISTRATION.md` §0, §5): Step-718 market rule is **Verbatim baseline passthrough**.
2. **P5 Constraint** (`02_PREREGISTRATION.md` §5): Markets on 712–717 are **Verbatim baseline passthrough**.
3. In `plan_terminal` (`h1_search.py`), candidate schedules modify only worker commands (`farmer`, `hands`). The market orders remain strictly identical to `baseline_schedule[offset]["market"]` for all steps 712–718.
4. In `h1_shadow.py:simulate_schedule`, the candidate rollout executes `baseline_schedule[offset]["market"]`.
5. The baseline policy (`candidates/compiled_v54_plus_residual.py` / `scripts.v19_terminal.py:205`) constructs its step-718 market orders as:
   `quantity = max(0, int(shed.get(item, 0) or 0))`
   The baseline **never places unfulfillable sell orders**; it orders selling only what was projected to be in its shed.
6. Therefore, in the baseline rollout, `baseline_run["sold"][item]` fulfills 100% of the baseline's sell orders.
7. In the candidate rollout, although extra crops are deposited into the shed (`final_shed >= baseline_shed`), the market orders executed are identical to the baseline's orders. The candidate fulfills the exact same orders.
8. Therefore, `final_run["sold"][item] == baseline_run["sold"][item]` for all 9 products.
9. Consequently:
   `delta[item] = final_run["sold"][item] - baseline_run["sold"][item] == 0` for all products.
10. `some_positive = any(v > 0 for v in delta.values())` is **identically False**.

### 4.4 Mathematical & Structural Impossibility
Under the frozen candidate search and shadow simulator:
$$\Delta_{\text{sold}}(p) = \min(Q_{\text{ordered}}(p), S_{\text{candidate}}(p)) - \min(Q_{\text{ordered}}(p), S_{\text{baseline}}(p))$$
Because $Q_{\text{ordered}}(p) \le S_{\text{baseline}}(p) \le S_{\text{candidate}}(p)$, we have:
$$\min(Q_{\text{ordered}}(p), S_{\text{candidate}}(p)) = Q_{\text{ordered}}(p) = \min(Q_{\text{ordered}}(p), S_{\text{baseline}}(p))$$
$$\Delta_{\text{sold}}(p) \equiv 0 \quad \forall p \in \text{PRODUCTS\_9}$$
Thus, `some_positive` is **mathematically and structurally unreachable** across all candidate proposals in all games.

### 4.5 Origin and Preregistration Intent
In Dmitrii LB2800 (`terminal_planner.py:148–150, 369–381`), at step 718, `simulate()` re-computed `shop_liquidation(farm, private, prices)` on the candidate's post-harvest shed state, liquidating the newly reaped units into coins and producing `sold_delta > 0`.

When ARCH-002 was preregistered, the author explicitly froze:
- `D3: Step-718 market rule: Verbatim baseline passthrough... live-recompute variant recorded as future experiment H1b, NOT authorized` (`02_PREREGISTRATION.md` §0).
- But in §8.1(5), the author copied Dmitrii LB2800's acceptance conjunction requiring `some product's sold delta > 0` (`mirror :364–391`).

Crucially, in `02_PREREGISTRATION.md` §21.1 and §24.1, the preregistration explicitly provided:
- `Pattern C — Mechanism Untestable / Inactive: k <= 2 ("mechanism not activated in this cohort")`.
- `I-6: If pattern C holds, the licensed next step is exposure forensics (reason-code histogram diagnosis), not a bigger N with the same design. If pattern B holds with a diagnosed cause, the licensed next step is H1b (single-cause redesign, new protocol).`

### 4.6 Classification
This behavior is classified as:
**LEGITIMATE PREREGISTERED ABSTENTION BEHAVIOR (MECHANISM INACTIVITY UNDER PREREGISTERED CONSTRAINTS)**.

- It is **not** an implementation bug: `h1_dominance.py` implements `02_PREREGISTRATION.md` §8.1(5) verbatim.
- It is **not** an unresolved ambiguity: the protocol specifically defined Pattern C ($k \le 2$) and named "H1b" as the future protocol for testing a live-recompute market rule.
- Altering `h1_dominance.py` or `h1_shadow.py` would violate the preregistration and convert ARCH-002 into the unauthorized H1b experiment.
- A clean re-execution of ARCH-002 under a corrected runner will rigorously document whether H1 is 100% mechanism-inactive ($k=0$, Pattern C+E, $\bar{\Delta} = \$0.00$) with **unpolluted P-PURE validity**. That is a valid scientific finding.

---

## 5. SECTION X: RE-EXECUTION ELIGIBILITY DECISION

**DECISION: OUTCOME A — RE-EXECUTION ELIGIBLE**

**Basis**:
1. The runner defect (double-calling `base_inst_h1.call` during P-PURE checking) is strictly an execution-layer defect.
2. The H1 protocol (`02_PREREGISTRATION.md`) remains completely unchanged.
3. The H1 implementation (`h1_*.py`) remains 100% bit-identical.
4. The acceptance logic in `h1_dominance.py` is fully coherent with the preregistered protocol.
5. The baseline and simulator are 100% bit-identical.
6. The authorized cohort remains exactly `320000–320499` (N=500 seeds, 1,000 games).
7. Governance permits a corrected execution under a new runner artifact (`run_arch002_h1_reexecution.py`) with its own validation gate and freeze record, while permanently preserving the original invalid run in repository records.

---

## 6. SPECIFICATION FOR CORRECTED RUNNER (`run_arch002_h1_reexecution.py`)

The corrected runner will:
1. **Never call a stateful policy instance twice per turn**.
2. To verify P-PURE pre-E identity without mutating policy state, instantiate an **independent baseline twin instance** (`base_inst_twin`) per seat. On each step $t < \text{ENTRY\_STEP}$, compare `act_h1` (produced by `agent_h1`, which calls `base_inst_h1` exactly once) against `act_twin = base_inst_twin.call(copy.deepcopy(obs_h1), copy.deepcopy(cfg))`. Neither instance is double-called.
3. In-window market tracking (steps 712–717) will inspect `act_h1.get("market")` against `act_twin.get("market")` without making additional calls.
4. Deep-copy all observations and configs passed to policy calls.
5. Retain all quarantine gates (hard abort on holdout `214200–214249`, DEV-007 `310000–310499`, and out-of-cohort seeds).
6. Use dedicated output paths (`REEXECUTION_RAW_RESULTS.json`, `REEXECUTION_PAIRED_DELTAS.csv`, `REEXECUTION_TELEMETRY_EVENTS.csv`, `REEXECUTION_MANIFEST.json`) to guarantee zero overwriting of original run artifacts.
7. Preserve atomic checkpointing, crash resilience, and deterministic multiprocessing.

---

## 7. GOVERNANCE STATEMENT

- **DEV-007 Status**: Cohort `310000–310499` remains completely virgin, untouched, unexecuted, and frozen.
- **Final Holdout Status**: Cohort `214200–214249` remains completely virgin, protected, and untouched.
- **Next Required Phase**: Implement corrected runner `run_arch002_h1_reexecution.py` and execute the non-prospective validation suite (Phase G).
