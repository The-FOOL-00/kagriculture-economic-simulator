# V34 Fail-Closed Liquidity Safety Invariants & Capital Runway Audit

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Module:** `candidates/v34_a7_tactical/liquidity_guard.py`  
**Test Suite:** `tests/test_v34_liquidity.py`  

---

## 1. Executive Summary: The Hidden Failure Mode

Across both V32 (P12 option evaluations) and V33 (market sell-reordering overlays), liquidity starvation was the single most destructive hidden failure mode:
1. **The P12 Land Expansion Collapse:**
   In P12, unlocking a 4th quadrant appeared to have high terminal value against passive opponents. But against active league opponents, spending \$4,000 on land reduced liquid cash to \$0 right before daily wage deductions, triggering insolvency and worker strikes.
2. **The V33 Market Overlay Degradation:**
   In V33, reordering sell orders delayed wheat sales by 1 turn. Because A7 relied on same-turn wheat cash to purchase equipment and seeds, delaying the sale caused subsequent purchase orders to bounce, dropping league win rate by 5.0%.
3. **The Empirical A7 Floor:**
   Our 7,190-step decision trace revealed that A7's liquid capital drops to as low as **\$4.00** during early turns ($t \in [10, 80]$). A7 operates with razor-thin capital buffers.

To guarantee zero regression, V34 establishes a **fail-closed Liquidity Guard** that runs on all proposed tactical candidates.

---

## 2. Formal Capital Invariants

A tactical candidate action $a_t$ is permitted if and only if all three invariants hold:

### Invariant 1: Intra-Turn Execution Precedence
$$\forall k \in [1, |a_t^{\text{market}}|], \quad \text{Cash}_0 + \sum_{j=1}^k \text{CashFlow}(a_{t,j}^{\text{market}}) \ge \text{Floor}(t)$$
If a BUY order precedes a SELL order, starting cash must cover the purchase unconditionally. Selling cannot be assumed to fund earlier buys in the same turn.

### Invariant 2: Imminent Wage Runway ($t \pmod{24} \ge 20$)
$$\text{ProjectedCash}(t) \ge N_{\text{workers}} \times \$10.00 \times 1.15 + \text{Floor}(t)$$
When within 4 steps of midnight ($t \pmod{24} \ge 20$), liquid cash must exceed total expected wages plus a 15% safety buffer.

### Invariant 3: Minimum Cash Floor
$$\text{Floor}(t) = \begin{cases} \$20.00 & \text{if } t < 120 \\ \$100.00 & \text{if } t \ge 120 \end{cases}$$
Liquid capital may never drop below \$20.00 in early turns or \$100.00 in mid-late turns.

---

## 3. Empirical Validation of Liquidity Guard

In `tests/test_v34_liquidity.py`:
- **Starvation Rejection Test:** Orders spending \$100 before receiving \$250 from sales were rejected with 100% precision.
- **Precedence Reversal Test:** Reordering sales to execute prior to purchases was approved and confirmed safe.
- **Wage Runway Test:** Seed purchases that threatened upcoming wages were rejected with 100% precision.

---

## 4. Policy Enforcement

The Liquidity Guard is fail-closed. If an observation is noisy, prices are missing, or a calculation raises an exception, the guard returns `is_safe = False`, and the controller defaults immediately to protected A7.
