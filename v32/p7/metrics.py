# SPDX-License-Identifier: MIT
"""V32 P7 prefix metrics (pure, deterministic functions).

Conventions (P5/P6-compatible):
- farmer-action equality: full native farmer literal equality (op + args).
- full-action equality: farmer + hands + market literal equality (P5 actions_equal).
- first STATE divergence: farmer position differs OR hand count differs OR
  |money diff| > 1.0 (P5 thresholds).
- first ECONOMIC divergence: |money diff| > 10.0 (P5 threshold).
- traces: lists of {"step", "ess", "action"} with aligned step indices.
"""

STATE_MONEY_EPS = 1.0
ECON_MONEY_EPS = 10.0


def _lit(x, default):
    return x if isinstance(x, list) and x else default


def farmer_equal(a1, a2):
    return _lit(a1.get("farmer"), ["PASS"]) == _lit(a2.get("farmer"), ["PASS"])


def actions_equal(a1, a2):
    """Full native joint-action equality (farmer + hands + market)."""
    if not farmer_equal(a1, a2):
        return False
    h1 = a1.get("hands") or []
    h2 = a2.get("hands") or []
    if len(h1) != len(h2):
        return False
    for x, y in zip(h1, h2):
        if _lit(x, ["PASS"]) != _lit(y, ["PASS"]):
            return False
    m1 = a1.get("market") or []
    m2 = a2.get("market") or []
    if len(m1) != len(m2):
        return False
    for x, y in zip(m1, m2):
        if _lit(x, []) != _lit(y, []):
            return False
    return True


def wash_shape(market):
    """Opening wash shape: any BUY_* plus a SELL (P6 screen convention)."""
    ops = [o[0] for o in (market or []) if isinstance(o, list) and o]
    return (any(o in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL") for o in ops)
            and "SELL" in ops)


def hire_count(market):
    return sum(1 for o in (market or [])
               if isinstance(o, list) and len(o) > 0 and o[0] == "HIRE")


def prefix_exact_match(teacher_acts, policy_acts, H, mode="farmer"):
    """True iff ALL native actions 0..H match (mode: farmer|full).

    Missing steps (short rollout) count as mismatch.
    """
    eq = farmer_equal if mode == "farmer" else actions_equal
    if len(teacher_acts) < H + 1 or len(policy_acts) < H + 1:
        return False
    return all(eq(t, p) for t, p in
               zip(teacher_acts[:H + 1], policy_acts[:H + 1]))


def wash_order_correct(market):
    """Order-correct wash: slot0 BUY_* then slot1 SELL, same item, qty > 0.

    Order is economically decisive (SELL-first strands wheat, -$1,014 vs
    BUY-first on seed 249675; see V32_P7_BASELINE_REPRO.md). The P6 screen
    metric wash_shape() is order-insensitive and passes both.
    """
    m = market or []
    if len(m) < 2 or not isinstance(m[0], list) or not isinstance(m[1], list):
        return False
    if len(m[0]) < 3 or len(m[1]) < 3:
        return False
    try:
        q0, q1 = int(m[0][2]), int(m[1][2])
    except (TypeError, ValueError):
        return False
    return (m[0][0] in ("BUY_SEED", "BUY_PRODUCT", "BUY_ANIMAL")
            and m[1][0] == "SELL" and m[0][1] == m[1][1]
            and q0 > 0 and q1 > 0)


def first_divergence(teacher_trace, policy_trace):
    """First action/state/economic divergence steps (None if never).

    teacher_trace/policy_trace: lists of {"ess", "action"} aligned by index
    (PRE-action states: index t holds the state before the step-t action).
    - t_act_farmer/t_act_full: first step whose ACTION literal differs.
    - t_state: P5 money-inclusive definition (pos/hands differ OR |dMoney|>1).
    - t_pos: position/hands ONLY (physical dislocation, money-blind).
    - t_econ: |dMoney| > 10.
    A divergent action taken at step t first shows in pre-action states at
    step t+1; P6's reported "step 3" uses action-step indexing (= our t_act).
    """
    n = min(len(teacher_trace), len(policy_trace))
    t_af = t_au = t_st = t_ps = t_ec = None
    for t in range(n):
        te = teacher_trace[t]
        po = policy_trace[t]
        if t_af is None and not farmer_equal(te["action"], po["action"]):
            t_af = t
        if t_au is None and not actions_equal(te["action"], po["action"]):
            t_au = t
        se, sp = te["ess"], po["ess"]
        pos_diff = (list((se.get("farmer") or [0, 0])[:2])
                    != list((sp.get("farmer") or [0, 0])[:2]))
        hands_diff = len(se.get("hands", []) or []) != len(
            sp.get("hands", []) or [])
        try:
            money_diff = abs(float(se.get("money", 0.0))
                             - float(sp.get("money", 0.0)))
        except (TypeError, ValueError):
            money_diff = 0.0
        if t_ps is None and (pos_diff or hands_diff):
            t_ps = t
        if t_st is None and (pos_diff or hands_diff
                             or money_diff > STATE_MONEY_EPS):
            t_st = t
        if t_ec is None and money_diff > ECON_MONEY_EPS:
            t_ec = t
        if t_af is not None and t_au is not None and t_st is not None \
                and t_ps is not None and t_ec is not None:
            break
    return {"t_act_farmer": t_af, "t_act_full": t_au,
            "t_state": t_st, "t_pos": t_ps, "t_econ": t_ec}


def opening_macro_survival(policy_trace, milestones):
    """Check policy trace against teacher-derived state/event milestones.

    milestones: list of {"step", "name", "check"} where check(ess, action)
    returns bool. All milestone definitions must come from the recorded teacher
    trajectory (see V32_P7_OPENING_MACRO.md); this function only evaluates them.
    Returns {"passed": bool, "reached": [names], "failed_at": name|None}.
    """
    by_step = {r["step"]: r for r in policy_trace}
    reached = []
    for m in milestones:
        r = by_step.get(m["step"])
        if r is None or not m["check"](r["ess"], r["action"]):
            return {"passed": False, "reached": reached,
                    "failed_at": m["name"]}
        reached.append(m["name"])
    return {"passed": True, "reached": reached, "failed_at": None}
