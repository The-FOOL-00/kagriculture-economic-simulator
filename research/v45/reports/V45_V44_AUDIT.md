# V45 Comprehensive Audit of the V44 Foundation

**Document ID:** `research/v45/reports/V45_V44_AUDIT.md`  
**Date:** 2026-09-25  
**Repository:** `The-FOOL-00/kagriculture-economic-simulator`  
**Foundation Candidate:** `candidates/v44_economic_portfolio/main.py`  
**Audit Status:** Complete & Verified  

---

## 1. Executive Summary & Audit Mandate

The purpose of this audit is to provide a comprehensive structural, economic, and behavioural dissection of the V44 baseline prior to initiating V45 research.

V44 is the immediate predecessor to V45. It represents the state-of-the-art in Kagriculture economic strategy, having synthesized the lessons of V35 (deterministic opening chore planner), V39 (single-step liquidation correction), V40 (unrestricted RL failure forensics), V41 (safe residual interface), V42 (single-step safe incremental alpha), and V43 (multi-step compositional alpha).

---

## 2. Key Audit Inquiries & Architectural Findings

### Q1: Exactly what code does V44 execute at each step of the match?
* **Turns 0..519:** Pure native `V35OpeningController` chore engine. 100% bit-for-bit identical to V35. No overrides, no modifications.
* **Turns 520..689:** `V35OpeningController` chore engine with one defensive filter: any market orders for `BUY_ANIMAL` or `BUY_LAND` are filtered out (`mkt = [o for o in mkt if not (len(o) > 0 and o[0] in ("BUY_ANIMAL", "BUY_LAND"))]`).
* **Turns 690..692:** Cutoff-filtered V35 action (no early sales).
* **Turns 693..694:** First liquidation tranche: sells 50% of shed inventory (`max(1, qty // 2)`) across marketable commodities (`STRAWBERRY`, `MILK`, `WOOL`, `MELON`) for any commodity with $\ge 2$ units.
* **Turns 695..703:** Native V35 execution with payback cutoff.
* **Turns 704..705:** Second liquidation tranche: sells 50% of marketable shed stock.
* **Turns 706..715:** Native V35 execution with payback cutoff.
* **Turns 716..718:** Final flush: sells 100% of all residual shed stock (`qty > 0`).

### Q2: What was the primary negative result in V44?
V44 evaluated 13 economic families outside the terminal window:
1. **Land 2 Acceleration:** While producing apparent cash gains in select seeds, it caused **7 catastrophic casualties** and a 5th percentile tail loss of **-$12,064.25** due to early liquidity starvation.
2. **Labor Wage Capping (Step 550):** Stopping farm hand hiring caused **14 casualties** and **-$7,076.92** mean deficit because mature late crops rotted uncollected in the field.
3. **Midgame Spot Selling:** Midgame sales into town shop spikes ($> \$200$) appeared attractive in single runs, but full-horizon terminal rollouts showed net negative or sub-additive returns (-$7.94 to -$468.06). Indiscriminate midgame selling depresses the price curve for future steps and robs the agent of the Zero Carry Cost Invariant.

### Q3: What is the Zero Carry Cost Invariant?
In the Kagriculture engine:
* Commodities in the shed do not spoil, rot, or decay.
* Shed storage costs exactly $0 per turn.
* Liquidated cash earns 0 interest and pays no dividend unless actively spent on productive assets.
* After Step 520, productive assets (cows, land, sheep) cannot amortize their purchase cost before Step 719.
* Therefore, holding high-value commodities in the shed costs nothing and preserves complete optionality, whereas prematurely dumping them into thin midgame market depth destroys both market price and terminal compound margin.

### Q4: What is the exact boundary between V44 and V45?
* **V44 operates primarily on internal farm state and fixed schedule timing:** It checks step numbers (520, 693, 704, 716) and internal shed quantities. It does **not** dynamically react to opponent market orders, opponent cash distress, observable price velocity, or market volume imbalances.
* **V45 is explicitly adversarial and market-driven:** V45 asks whether observable opponent actions and market pressure can be detected in real time to dynamically adjust selling timing, volume tranches, order pre-emption, and supply withholding without relying on fixed step rules or hidden information.

---

## 3. Structural Vulnerabilities in V44

Forensic analysis of the few baseline losses in V44 (e.g., Seed 249657 vs `E2_A7` -$34 margin, Seed 249659 vs `E8_DMITRII` -$1,101 deficit) reveals key structural limitations:
1. **Rigid Liquidation Windows:** V44 waits strictly until Step 693. If an aggressive opponent liquidates at Step 688 or 690, V44 sells into an already collapsed order book.
2. **Blind Volume Sizing:** Selling a fixed 50% tranche ignores current market depth $I_{\text{market}}$. If $I_{\text{market}}$ is already saturated, selling 50% creates severe downward price slippage. Conversely, if town shops just drained market inventory, selling more or less could be drastically more optimal.
3. **No Exploitation of Opponent Liquidity:** If an opponent is starved of cash midgame, withholding supply or pre-empting town shop ticks can force the opponent into suboptimal actions.

---

## 4. Audit Verdict & Handover to V45

V44 is certified as **clean, sound, and fully reproducible**. It establishes a reliable baseline of **+$71.16 mean cash delta** over V35 with **0 casualties**. V45 inherits V44 as its bedrock benchmark and fallback executor.
