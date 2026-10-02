# V55 Research Program: Final Scientific Report
## Post-Reveal Shop-Regime Continuation Search & Blocked-Action Audit

**Governance Status**: Complete  
**Engine**: `kaggle-environments 1.32.7`  
**Incumbent**: `V49_Meta_Fusion` (SHA256: `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11`)  
**Decision**: **`V55_RETAIN_V49`**  
**V49 Retained**: **`True`**

---

## Executive Summary

The V55 research program investigated whether the verified champion `V49_Meta_Fusion` (99.31% fresh win rate) could be improved by making state-dependent continuation decisions *only after future town shop demand is legally revealed* in `observation.town["unlocked_shops"]`, or alternatively via a generic blocked-action execution repair mechanism.

Following the definitive V54 discovery that Seed 250416 and Seed 250436 are mathematically indistinguishable prior to Step 216 ($obs_{250416}(t) \equiv obs_{250436}(t)$ for $t \le 215$), V55 formulated and tested the honest causal hypothesis:
> *"Once newly spawned town shops are legally visible, can V49 safely change its future continuation to exploit the revealed demand regime?"*

Across a comprehensive multi-phase research investigation comprising engine mechanics auditing, prefix parity verification, temporal leakage bounds, causal branch matrices, empirical action audits, and an out-of-sample 576-leg fresh benchmark ladder against 9 strong opponents, the scientific conclusion is decisive:
1. **The Shed Saturation Trap**: Holding inventory (e.g. Milk) to capture elevated town shop demand causes shed capacity saturation ($100/100$ items). Under official engine rules (`kaggriculture._apply_unit_action`), when the shed is full, any field worker executing `DROP` has their harvested crops silently deleted from existence with zero payment (`del inv[item]` with `take = 0`).
2. **False-Positive Asymmetry**: While milk withholding yields modest gains on Seed 250436 (+$627 to +$1,641), the identical legal post-reveal rule triggers a catastrophic **-$30,569 casualty** on Seed 250416 when a dairy shop rolls at Step 288.
3. **Fresh Benchmark Collapse**: On the 576-leg fresh ladder across 32 unseen seeds, the post-reveal shop candidate collapsed from 99.31% to **78.65% Win Rate** (a -20.66% regression), suffering **119 fatal casualties** and a mean paired delta of **-$6,524.25**.
4. **General Blocked-Action Null**: An exhaustive audit of 11,504 turns revealed that V49 experiences exactly **0** weed-blocked planting actions. Attempting to clear "obstacles" with `DIG` would destroy V49's own mature Wheat crops. The candidate produced a paired delta of **+$0.00** across all 576 legs.

`V49_Meta_Fusion` is completely retained as the sovereign champion.

---

## Mandated Final Scientific Q&A (Section 16)

### Q1: What is the earliest legal point at which the future shop regime becomes observable?
**Answer**: **Step 216 (Hour 0 of Day 9)** for Shop Instance #3.
Town shops unlock strictly at Steps 72, 144, 216, 288, 360, 432, 504, and 576.
Through Step 215, all observable fields (`farms`, `market.prices`, `market.inventory`, `town.unlocked_shops`, and public opponent telemetry) are mathematically identical between seeds that subsequently roll divergent shop types (e.g., Seed 250416 rolling `PET_CAFE` vs Seed 250436 rolling `PIZZA_SHOP`). Prior to Step 216, zero bits of legal information exist to distinguish these worlds.

### Q2: Can V49's fixed continuation be improved after that reveal?
**Answer**: **No.**
By Step 216, 30% of the game has elapsed and V49's physical production infrastructure is locked into place: 6 cows, 4 sheep, 2 geese, 1 empty pasture, 3 farm hands, and active multi-tier strawberry/melon/wheat crop rotations.
- Purchasing additional cows at Step 216 costs $1,200 and deposits the animal in the shed, where it sits idle producing 0 milk because no hand is scripted to move it to pasture (tested in Family C: -$411 to -$455 delta).
- Delaying milk sales to exploit town demand saturates the 100-item shed capacity, causing field workers to discard harvested high-value crops into the void (tested in Family B: -$30,569 loss on 250416).

### Q3: Can the same post-reveal rule improve 250436/250439 while leaving 250416 unharmed?
**Answer**: **No.**
In Seed 250436, multiple dairy shops appear in rapid succession (Pizza at 216, Pizza at 288, Smoothie at 360), absorbing milk rapidly enough that withholding milk can occasionally clear at elevated prices.
However, in Seed 250416, a dairy shop (`SMOOTHIE_SHOP`) appears later at Step 288. Under any consistent, observation-driven rule, the appearance of the shop triggers milk withholding. Because 250416 has lower aggregate demand, milk accumulates, saturates the shed, and destroys over $30,000 of strawberry and melon revenue. The rule cannot differentiate the two worlds without illegal future shop knowledge.

### Q4: Does shop identity alone suffice, or is realized market response required?
**Answer**: **Neither suffices.**
- **Shop Identity Alone**: Fails because the market price trajectory is not determined by town shops in isolation; it depends on whether the opponent also produces dairy. If the opponent also sells milk (e.g. V44 on 250436), town consumption is offset by opponent dumping, keeping prices depressed.
- **Realized Market Response**: Fails because by the time market inventory drops or rises, shed congestion has already occurred or delayed cashflow has crippled late-game hand hiring and fertilizer application.

### Q5: Which commodities benefit from post-reveal adaptation?
**Answer**: **None in practice.**
- `WOOL`: Single-product `YARN_STORE` instances consume 2 units of Wool every 4 steps (0.50 units/turn), driving Wool prices to the $200+ ceiling. However, V49's 4 sheep already produce maximum wool on a 3-day shear cycle; no post-reveal change can increase wool output without reallocating land from crops.
- `MILK`, `WHEAT`, `EGG`, `STRAWBERRY`: Multi-product shops consume only 1 unit per 4 steps. Withholding inventory for these commodities causes shed saturation and severe delivery blockage.

### Q6: What exact economic mechanism creates the improvement?
**Answer**:
The modest historical gain on 250436 (+$627 to +$1,641) was created by **price arbitrage**: delaying milk sales until market inventory fell below $I_0 = 10$, raising milk unit prices from $100 to $120–$140.
However, the causal counter-mechanism that causes catastrophic collapse is **engine-level shed overflow**:
```python
room = max(0, shed_capacity - sum(shed.values()))
take = min(n, room)
if take > 0:
    shed[item] = shed.get(item, 0) + take
del inv[item]  # If room == 0, take == 0: harvested crop is deleted!
```
When milk occupies shed space, `room` reaches 0. Field workers harvesting Strawberries and Melons drop their inventory into the shed, where the engine deletes the items without credit, destroying thousands of dollars in revenue.

### Q7: Does the mechanism generalize to unseen seeds and unseen strong opponents?
**Answer**: **No. It generalizes catastrophically in reverse.**
Across the 576-leg fresh benchmark ladder on 32 unseen seeds `[250600..250631]`:
- Win Rate collapsed from **99.31% to 78.65%**.
- Elite Win Rate collapsed from **98.96% to 67.97%**.
- Generated **119 fatal casualties** (30 vs V44, 26 vs Dmitrii, 26 vs Tetsutani, 22 vs Kaito, 15 vs Indarkarhana).
- Mean paired delta vs V49: **-$6,524.25** (95% CI `[-$7,539.46, -$5,572.90]`).

### Q8: How much apparent alpha disappears when illegal future information is removed?
**Answer**: **100% of the alpha disappears.**
The apparent +$7,120 margin on Seed 250436 from pre-reveal dairy specialization (V54 Step-150 COWSWAP) requires knowing at Step 150 that future shops will be Pizza and Ice Cream.
When that illicit future knowledge is removed, an honest policy must execute identically on 250416 and 250436, converting the apparent gain into a net loss of -$1,410 to -$30,569 across the pair. All apparent pre-reveal dairy alpha is unexploitable temporal leakage.

### Q9: Does a generic blocked-action repair mechanism exist independently of the V54 shop work?
**Answer**: **No.**
A comprehensive execution-layer audit of V49 across 16 benchmark seeds (11,504 agent steps) demonstrated:
- Intended `PLANT` actions blocked by a `WEED`: **EXACTLY ZERO (0)**. V49 operates on pre-cleared, pre-plowed choreographic grids where weeds never spawn.
- Intended `PLANT` actions on occupied tiles occurred on tiles hosting **mature, high-yielding Wheat crops** (yield 3–4). Issuing `DIG` to "clear the blocker" would destroy the agent's own wheat crop.
- The remaining no-op actions were idempotent (`CARE` on already-cared animals, `WATER` on rain-moistened tiles).
- On the 576-leg fresh ladder, `V55_Blocked_Action` was 100% inactive, yielding **+$0.00 paired delta** and 0 rescues.

### Q10: Should V49 be retained or should a research candidate be promoted?
**Answer**: **`V55_RETAIN_V49`**.
`V49_Meta_Fusion` is 100% retained. Zero research candidates passed the promotion gates.

---

## Complete Verification of Required Artifacts

All 16 required artifacts specified in Section 15 have been fully generated, mathematically cross-checked, and committed:

1. `research/v55/analysis/SHOP_REVEAL_TIMELINE.md` (Verified)
2. `research/v55/analysis/SHOP_REVEAL_TIMELINE.json` (Verified)
3. `research/v55/analysis/V49_PREFIX_PARITY.md` (Verified)
4. `research/v55/analysis/V49_PREFIX_PARITY.json` (Verified)
5. `research/v55/analysis/TEMPORAL_LEAKAGE_REPORT.md` (Verified)
6. `research/v55/analysis/SHOP_REGIME_TAXONOMY.md` (Verified)
7. `research/v55/analysis/CAUSAL_BRANCH_TABLE.md` (Verified)
8. `research/v55/analysis/BLOCKED_ACTION_AUDIT.md` (Verified)
9. `research/v55/counterfactuals/critical_seed_counterfactuals.json` (Verified)
10. `research/v55/counterfactuals/reveal_point_matrix.json` (Verified)
11. `research/v55/counterfactuals/continuation_matrix.json` (Verified)
12. `research/v55/candidates/v55_post_reveal_shop/main.py` (Verified)
13. `research/v55/candidates/v55_blocked_action/main.py` (Verified)
14. `research/v55/benchmarks/v55_fresh_ladder.json` (Verified)
15. `research/v55/benchmarks/v55_blocked_fresh_ladder.json` (Verified)
16. `research/v55/benchmarks/per_opponent_results.json` (Verified)
17. `research/v55/reports/V55_FINAL_LADDER.md` (Verified)
18. `research/v55/reports/V55_FINAL_REPORT.md` (Verified)
19. `research/v55/COMPLETE` (Verified)
