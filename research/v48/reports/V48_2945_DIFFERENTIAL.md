# V48 — 2945 vs V47 Exact Differential Audit

**Date:** 2026-09-26  
**Program:** Kagriculture V48 — 2945 Challenger  
**Incumbent Benchmark B1:** `thomastschinkel_2945`  
**Incumbent Benchmark B2:** V47 (`candidates/v47_elite_transfer/main.py`)  

---

## 1. Executive Summary: What V47 Actually Is

Part 2 of the V48 mandate required answering a fundamental question:

> **Does V47 differ meaningfully from raw 2945 under identical world conditions?**

### The Definitive Finding:
When facing the identical farm state (same seed, same seat, same tiles):

```text
V47 == thomastschinkel_2945 (EXACT_PARITY: 100% Bit-for-Bit Identity)
```

In the 128-leg benchmark between V47 and raw 2945:
- **110 legs tied with exact margin $0.00.**
- **9 legs were recorded as V47 wins (+margin).**
- **9 legs were recorded as V47 losses (-margin).**

Our step-by-step trace forensics investigated the 18 non-tie legs (e.g. Seed 249812):
1. **Seat-Symmetry Analysis:** In every non-tie seed, the margin in Seat 0 was the exact negative of the margin in Seat 1 (e.g. Seed 249812: V47 in Seat 0 won by +$118.00; V47 in Seat 1 lost by -$118.00). The paired margin across both seats was **exactly $0.00**.
2. **Causal Source of Non-Ties:** 
   - **Asymmetric Weed Spawns:** In Kaggriculture, weeds spawn randomly and independently on Farm 0 vs Farm 1. On Seed 249812 at step 301, Farm 1 suffered a random weed spawn on a planned wheat plot, forcing Hand 4 to execute `['DIG']` while Farm 0 executed `['PLANT', 'WHEAT']`.
   - **Market Execution Order:** Seat 0 orders execute prior to Seat 1 orders in the simultaneous resolution phase.
3. **Status of V44 CapEx Cutoff:** The Step $\ge 520$ animal/land cutoff added to V47 did not trigger on any of these seeds because the underlying 2945 tape naturally ceases capital acquisitions prior to Step 520.

**Conclusion:** V47 is in practice identical to 2945. Any true improvement in V48 must come from **genuine behavioral divergence** over the 2945 chassis.

---

## 2. Action Divergence Metrics

| Action Dimension | Divergence Count (Identical Environment) | Divergence Count (Cross-Seat Matchup) | Classification |
| :--- | :--- | :--- | :--- |
| **Farmer Movement** | 0 / 719 steps | 0 / 719 steps | EXACT_PARITY |
| **Hired Hands Movement**| 0 / 719 steps | 3 / 719 steps (Weed RNG) | EXACT_PARITY |
| **Market Orders (BUY)**| 0 / 719 steps | 0 / 719 steps | EXACT_PARITY |
| **Market Orders (SELL)**| 0 / 719 steps | 0 / 719 steps | EXACT_PARITY |
| **Route Selection** | 0 / 719 steps | 0 / 719 steps | EXACT_PARITY |

---

## 3. Direction for V48 Challenger

Because V47 is functionally identical to 2945, V48's objective is crystallized:
We must identify the **structural economic blindspots of the 2945 architecture** and construct targeted, state-conditional patches that make V48 strictly superior to raw 2945.
