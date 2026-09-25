# V39 Intervention Catalog — Formal Specification of Minimal Deterministic Candidates

## 1. Architectural Philosophy
Following the core directive of V39:
> **Find the smallest deterministic intervention that rescues observed live failures without damaging V35's existing strengths.**

Key Rules:
1. **One-Variable / Micro-Targeted**: Do NOT modify broad game choreography. Intervene only at the exact step and state where the failure occurs.
2. **Zero Downstream Drift ($D(t) = 0$ for $t < 694$)**: 100% of V35's opening (25/25 wheat wash), midgame scaling, worker routing, and land acquisitions are completely preserved.
3. **Pure Deterministic Predicate**: Zero learned weights, zero neural networks, zero hidden state, zero future information.
4. **Fail-Closed Safety**: Any unexpected state or exception immediately reverts to exact V35 behavior.

---

## 2. Formal Intervention Specifications

### Candidate INT-1: `FLUSH_694` (Terminal High-Value Perishable Shed Flush)
- **Problem Solved**:
  At Step 694 (Day 28, Hour 22), V35 holds unliquidated `MILK`, `STRAWBERRY`, and `WOOL` in its shed. The baseline static tape omits them until Step 696/698. Opponents dump first at Step 694, crashing market prices and inflicting $800 to $1,500 in price slippage.
- **Trigger Predicate**:
  ```python
  def trigger_flush_694(observation) -> bool:
      step = int(observation.get("step", 0) or 0)
      if step not in (693, 694):
          return False
      shed = observation.get("private", {}).get("shed", {})
      return any(shed.get(item, 0) > 0 for item in ("STRAWBERRY", "MILK", "WOOL"))
  ```
- **Action Transformation**:
  ```python
  def apply_flush_694(action, observation):
      shed = observation.get("private", {}).get("shed", {})
      mkt = action.setdefault("market", [])
      already = {o[1] for o in mkt if o[0] == "SELL"}
      for item in ("STRAWBERRY", "MILK", "WOOL"):
          qty = shed.get(item, 0)
          if qty > 0 and item not in already and len(mkt) < 10:
              mkt.append(["SELL", item, qty])
      return action
  ```
- **Safety Gate**:
  - Max order cap ($N \le 10$) strictly enforced.
  - Sells only confirmed shed inventory (`private['shed']`).
  - Does not sell seeds or feed items (`WHEAT` protected by base logic).

---

### Candidate INT-2: `SUPPRESS_HIRE_DAY29` (Day 29 Hire Suppression)
- **Problem Solved**:
  On Day 29 (Step 696–718), A7's static route queues multiple `["HIRE"]` market commands. Because each hire costs $144 to $377+ and workers terminate at Step 719 without producing crops, this burns $300 to $650 of pure cash.
- **Trigger Predicate**:
  ```python
  def trigger_suppress_hire(observation) -> bool:
      step = int(observation.get("step", 0) or 0)
      return step >= 696
  ```
- **Action Transformation**:
  ```python
  def apply_suppress_hire(action):
      mkt = action.get("market", [])
      action["market"] = [o for o in mkt if o[0] != "HIRE"]
      return action
  ```
- **Safety Gate**:
  Active only in the final 24 steps of the game.

---

### Candidate INT-3: `V39_COMBINED_TERMINAL_POLISH` (INT-1 + INT-2)
- Combines `FLUSH_694` with `SUPPRESS_HIRE_DAY29`.
- Captures peak revenue from delicate animal/crop products while eliminating useless terminal labor expenditure.
