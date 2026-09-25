# V43 Market Microstructure & Economic Regime Report

**Document ID:** `research/v43/reports/V43_MARKET_REGIME_REPORT.md`  
**Date:** 2026-09-25  
**Repository:** `Kagriculture`  
**Artifact Path:** `research/v43/artifacts/regime_catalog.json`  
**Scope:** Investigation of market microstructure dynamics, price elasticity, order depth, opponent liquidation timing, and zero-leakage regime classification without opponent ID.

---

## 1. Executive Summary

In direct compliance with Sections 10 and 11 of the V43 specification, we conducted extensive market microstructure profiling across 17,256 simulator game steps evaluating diverse market environments against all four primary league opponents (`E8_DMITRII`, `E2_A7`, `E0_V3`, `SYN_AGG`).

Crucially, **the runtime policy is completely blind to `opponent_id` and random seed**. The agent infers market conditions, competitor pressure, and liquidation crowding entirely through observable macroeconomic variables:
* Spot price momentum across marketable commodities: $\mu_{\Delta P} = \frac{P_t - P_{t-1}}{\max(1, P_{t-1})}$.
* Net competitor liquidity velocity (trade activity proxy).
* Shed capacity utilization and inventory perishability.
* Time remaining until episode close ($T=720$).

---

## 2. Macroeconomic Regime Taxonomy & Empirical Distribution

Across 17,256 evaluated decision steps on safe training seeds:

| Regime ID | Regime Classification | State Count | Frequency (%) | Mean Commodity Price | Causal Economic Characteristic | Strategic Policy Directives |
| :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **0** | `STABLE_MARKET` | 14,654 | **84.9%** | **$162.93** | Steady order absorption; normal price spreads; predictable chore routines. | Follow V35 baseline choreography (100% Golden Property). |
| **1** | `TERMINAL_LOCK` | 816 | **4.7%** | **$120.23** | Steps 685–718; field harvesting ending; shed inventory realization phase. | Prioritize multi-point staggered liquidation (Steps 694, 705, 716). |
| **2** | `RISING_MARKET` | 707 | **4.1%** | **$88.68** | Positive price momentum ($\mu_{\Delta P} > +0.08$); expanding market demand. | Delay sales until price plateaus; withhold high-elasticity goods. |
| **3** | `CROWDED_MARKET` | 677 | **3.9%** | **$127.20** | Heavy competitor trade volume; high sell-side pressure; risk of price crash. | Strictly avoid large bulk dumps; use smaller partial orders (30–40%). |
| **4** | `FALLING_MARKET` | 402 | **2.3%** | **$93.10** | Negative price momentum ($\mu_{\Delta P} < -0.08$); supply glut. | Suppress sales of non-perishables (`HOLD_DEPRESSED_GOODS`). |
| **5** | `THIN_MARKET` | 0 | 0.0% | $0.00 | Wide bid-ask spreads; low liquidity. | Abstain from discretionary spot sales. |

---

## 3. Competitor Liquidation Behavior & Market Pre-emption

By tracking opponent inventory liquidations across thousands of turns, we uncovered the underlying mechanics of terminal commodity price collapses:

| Opponent ID | Detected Dump Events | Mean Liquidation Step | Earliest Step | Latest Step | Causal Microstructure Behavior |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`E8_DMITRII`** | 24 | **705.4** | 686 | 718 | Concentrated sell waves beginning at Step 695; crashes marketable price depth by **35% to 50%**. |
| **`E2_A7`** | 27 | **702.3** | 686 | 718 | Moderate terminal dumping; sells dairy and wool in batches between steps 696 and 708. |
| **`E0_V3`** | 28 | **704.1** | 689 | 718 | Late terminal dumping; concentrates shed flush around Step 704–706. |
| **`SYN_AGG`** | 0 | N/A | N/A | N/A | Midgame continuous dumper; sells incrementally every 12–24 steps rather than holding for terminal flush. |

### The Pre-emption Advantage at Step 694
* **Why Step 694 is the Global Optimum:**
  Opponents `E8_DMITRII`, `E2_A7`, and `E0_V3` initiate their primary harvest liquidation waves between steps 695 and 705.
  Liquidating at **Step 694** executes right before the Step 695 crash, capturing unflooded market prices.
* **Why Step 692 Fails:**
  Executing at Step 692 produces **negative cash delta (`-$12.25`)** because field workers have not finished transporting the final day's harvest into the shed. Selling prematurely forfeits inventory volume.
* **The Secondary Recovery Window at Step 705:**
  Following the competitor sell wave at steps 695–700, market depth partially stabilizes by Step 704–706. The secondary liquidation window captures remaining inventory without causing a secondary crash.

---

## 4. Empirical Order Sizing & Internal Price Slippage

Dumping 100% of shed inventory in a single market basket causes internal price slippage due to downward sloping demand curves.

$$\Delta P_{\text{slippage}} \propto -\kappa \cdot \left(\frac{Q_{\text{order}}}{D_{\text{market}}}\right)$$

* **Full Dump (100% at Step 694):** Order size frequently exceeds 12 units. Marginal price drops from `$45.00` down to `$22.00` per unit, resulting in substantial revenue loss and a severe negative lower tail (P5 `-$241.00`).
* **Partial Dump (50% or 40% at Step 694):** Order size is restricted to 4–6 units. Marginal price remains above `$38.00`, capturing maximum revenue per unit while preserving the remainder for the Step 705 recovery window.

---

## 5. Architectural Implementation in V43 Policy

1. **Continuous Feature Representation:**
   Rather than hard-coding opponent classifications, V43 encodes:
   * Commodity momentum vectors: 9 dimensions.
   * Perishability ratio: $\frac{\text{Milk} + \text{Strawberry}}{\text{Total Shed Goods}}$.
   * Net worth exposure ratio: $\frac{\text{Marketable Shed Value}}{\text{Total Net Worth}}$.
   * Temporal proximity: $\frac{720 - \text{step}}{720}$.
2. **LCB Gating under Crowded Regimes:**
   When competitor trade activity indicates a `CROWDED_MARKET`, the uncertainty estimate $\hat{\sigma}$ expands, automatically raising the required threshold for discretionary market actions and defaulting to the safe staggered schedule.
