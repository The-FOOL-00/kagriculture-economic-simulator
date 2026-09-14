# TREATMENT DIFF AUDIT: DEV-006 vs DEV-005 (ONE-FACTOR PROOF)
**Experiment**: EXP-DEV-006
**Date**: 2026-09-14
**Baseline file**: `candidates/closed_loop_architecture/dev_005_confirmed_shop_scheduler.py`
**Baseline SHA-256**: `f52b168619e47bea6a052faff890fc84804cb39b47392d247139967f910e2a78`
**Treatment file**: `candidates/closed_loop_architecture/dev_006_horizon_guard_scheduler.py`
**Treatment SHA-256**: `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb`
**Verdict**: **ONE-FACTOR CONFIRMED — allowed difference (HORIZON_GUARD) only. PROCEED.**

---

## 1. Complete Static Diff (unified, byte-exact)

```diff
20a21,24
> # HORIZON GUARD (POST-HOC TEST VALUE for EXP-DEV-006_HORIZON_KILLTEST only).
> # H = 500 steps. NOT preregistered Discovery evidence. Do not sweep.
> HORIZON_GUARD_THRESHOLD = 500
> 
85c89
< class Dev005ConfirmedShopScheduler:
---
> class Dev006HorizonGuardScheduler:
87,90c91,99
<     DEV-005 Confirmed-Shop Gated Whole-Route Macro Production Scheduler.
<     Preserves DEV-004 whole-route physical feasibility and market absorption engine.
<     Introduces Confirmation Gating: requires physical shop unlock confirmation before
<     activating irreversible specialized production routes.
---
>     DEV-006 Horizon-Guarded Whole-Route Scheduler (EXP-DEV-006_HORIZON_KILLTEST).
> 
>     ONE-FACTOR INTERVENTION over DEV-005: a NEW specialization (transition from
>     BASELINE_BACKBONE to a specialized route) is rejected when the remaining
>     horizon is below HORIZON_GUARD_THRESHOLD (H = 500 steps, post-hoc test value).
>     All other behavior -- shop confirmation rule, route candidates, physical
>     feasibility model, market model, liquidity rules, worker routing, preemption,
>     terminal logic, and maintenance/reversion of pre-existing specializations --
>     is bit-for-bit identical to DEV-005.
125a135
>         self.horizon_rejected_count = 0
296a307,310
>         # 4. ONE-FACTOR HORIZON GUARD: a NEW specialization (from BASELINE) is
>         #    allowed only when remaining_steps >= HORIZON_GUARD_THRESHOLD.
>         remaining_horizon = max(0, 720 - step)
>         horizon_satisfied = remaining_horizon >= HORIZON_GUARD_THRESHOLD
299,301c313,326
<                 selected_plan = best_plan
<                 decision = "SPECIALIZE_CONFIRMED"
<                 self.post_confirmation_specialization_count += 1
---
>                 if (not horizon_satisfied
>                         and self.active_plan == "BASELINE_BACKBONE"
>                         and best_plan != "BASELINE_BACKBONE"):
>                     selected_plan = "BASELINE_BACKBONE"
>                     decision = "REJECT_HORIZON"
>                     rejection_reason = (
>                         f"INSUFFICIENT_HORIZON:{remaining_horizon}_REMAINING"
>                         f"<{HORIZON_GUARD_THRESHOLD}"
>                     )
>                     self.horizon_rejected_count += 1
>                 else:
>                     selected_plan = best_plan
>                     decision = "SPECIALIZE_CONFIRMED"
>                     self.post_confirmation_specialization_count += 1
319a345,346
>             "remaining_horizon": remaining_horizon,
>             "horizon_satisfied": horizon_satisfied,
332c359
<         if decision in ("SPECIALIZE_CONFIRMED", "REJECT_UNCONFIRMED"):
---
>         if decision in ("SPECIALIZE_CONFIRMED", "REJECT_UNCONFIRMED", "REJECT_HORIZON"):
372c399
<         _INSTANCE = Dev005ConfirmedShopScheduler()
---
>         _INSTANCE = Dev006HorizonGuardScheduler()
```

## 2. Hunk-by-Hunk Classification

| # | Location | Change | Classification |
|---|----------|--------|----------------|
| 1 | L21–24 | `HORIZON_GUARD_THRESHOLD = 500` constant + comment | **ALLOWED** (the guard parameter; H=500 exactly) |
| 2 | L89 | Class rename `Dev005…` → `Dev006…` | Cosmetic (required for dual-arm CRN import; zero behavioral effect) |
| 3 | L91–99 | Docstring describing the guard | Cosmetic (comment-only) |
| 4 | L135 | `horizon_rejected_count` telemetry counter | **ALLOWED** (guard telemetry; write-only counter) |
| 5 | L307–310 | `remaining_horizon` / `horizon_satisfied` computation | **ALLOWED** (guard predicate) |
| 6 | L313–326 | `REJECT_HORIZON` branch for new specializations from BASELINE when horizon unsatisfied | **ALLOWED** (the guard itself; `else` path is the original 3 lines verbatim) |
| 7 | L345–346 | Two telemetry keys in decision event dict | **ALLOWED** (telemetry only; not read by any policy code) |
| 8 | L359 | `"REJECT_HORIZON"` added to specialization-events log tuple | **ALLOWED** (logging only) |
| 9 | `act()` | **Zero changes** (checkpoint dispatch, policy routing, seed trim, shed guard, terminal logic all byte-identical) | Verified identical |
| 10 | `kaggle_agent()` | Singleton instantiates renamed class | Cosmetic (required by rename) |
| 11 | Valuation, confirmation gate, route profiles, constants (`TAU`, `L_MIN`, friction, weights) | **Zero changes** | Verified identical |

**Forbidden-category scan**: no new crop/animal logic, margin/liquidity threshold, market rules, route candidates, worker routing, terminal liquidation, valuation formula, or shop rule. **Result: none found.**

## 3. Runtime Identity Test (pre-execution, synthetic obs, zero game simulation)

File: `experiments/EXP-DEV-006/treatment_identity_probe.py` (exit 0 on 2026-09-14):

```
step=72 remain=648: IDENTICAL (SPECIALIZE_CONFIRMED/YARN_SPECIALIZED/36718.0)
step=144 remain=576: IDENTICAL (SPECIALIZE_CONFIRMED/YARN_SPECIALIZED/33536.0)
step=216 remain=504: IDENTICAL (SPECIALIZE_CONFIRMED/YARN_SPECIALIZED/28009.0)
step=288 remain=432: DEV005=SPECIALIZE_CONFIRMED DEV006=REJECT_HORIZON (candidate YARN_SPECIALIZED value 24827.0)
IDENTITY PROBE: PASS — one-factor guard confirmed, all else identical.
```

Interpretation:
- Valuation function outputs identical for all 6 plans × all 4 checkpoints.
- Action policy identical at every checkpoint with `remaining >= 500`, including identical specialization decisions and identical expected values.
- The single permitted divergence occurs exactly where specified: step 288 (`remaining=432 < 500`), where an otherwise-eligible specialization (same candidate, same value 24827.0) is rejected by DEV-006 only.

## 4. Supporting Game-Level Evidence (retrospective, non-fresh)

The horizon kill-test executed 200 games (50 seeds × 2 arms × 2 seats) on the consumed 247000–247049 cohort with purity gates: all nonzero DEV-006−DEV-005 diffs coincided with `REJECT_HORIZON` events, and `REJECT_HORIZON` fired only at step 288. This corroborates — but does not substitute for — the static + probe proof above.

## 5. Audit Conclusion

The treatment differs from DEV-005 **only** by the H=500 horizon guard (parameter + predicate + rejection branch + telemetry + rename). No STOP condition triggered. **PROCEED to Discovery.**
