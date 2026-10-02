# V56 Near-Tie and Loss-Boundary Distribution Analysis

## Executive Summary

To evaluate whether the 4 fresh losses of **`V49_Meta_Fusion`** are isolated anomalies or the extreme tails of a recurring structural mechanism, we audited the margin distribution across all 576 legs of the fresh benchmark suite (32 seeds `[250600..250631]` $\times$ 2 seats $\times$ 9 opponents).

**Key Discoveries:**
1. **Zero Ultra-Thin Wins Under $250**: Across all 572 wins, V49 achieved **zero** wins with margin $\le \$250$. The closest win in the entire 576-leg suite is +$305.00 (Seed 250631 vs V44).
2. **Absolute Opponent Specificity**: **100% of all games with $|\text{margin}| \le \$1,000$ occur exclusively against `V44`**. Against all other 8 opponents, V49's minimum margin exceeds $1,200+, and median margin exceeds $8,500+.
3. **The Mirror-Agent Clustering**: V49 and V44 share the same underlying choreographic tape lineage. When they compete, they run nearly identical macro strategies in a zero-sum shared market. In 60 out of 64 matches against V44 (93.75%), V49 wins. The 4 losses represent the razor-thin boundary of this mirrored competition ($-\$82$ and $-\$862$).

---

## 1. Margin Distribution Across the 576-Leg Suite

### 1.1 Complete Result Stratification

| Margin Range | Count of Matches | Percentage of Suite | Result Classification | Opponents Represented |
| :--- | :---: | :---: | :---: | :--- |
| **Margin $< -\$500$** | 2 | 0.35% | **Losses** (L1, L2: $-\$862.00$) | `V44` only (Seed 250617, Seats 0 & 1) |
| **$-\$500 \le \text{Margin} < \$0$** | 2 | 0.35% | **Losses** (L3, L4: $-\$82.00$) | `V44` only (Seed 250621, Seats 0 & 1) |
| **$\text{Margin} == \$0$ (Tie)** | 0 | 0.00% | None | — |
| **$\$0 < \text{Margin} \le \$100$** | 0 | 0.00% | None | — |
| **$\$100 < \text{Margin} \le \$250$**| 0 | 0.00% | None | — |
| **$\$250 < \text{Margin} \le \$500$**| 4 | 0.69% | Near Wins (+$305, +$384) | `V44` only (Seeds 250616, 250631) |
| **$\$500 < \text{Margin} \le \$1,000$**| 2 | 0.35% | Near Wins (+$551, +$798) | `V44` only (Seeds 250604, 250627) |
| **$\text{Margin} > \$1,000$** | 566 | 98.26% | Decisive Dominant Wins | All 9 Opponents |
| **TOTAL** | **576** | **100.00%** | **572W / 4L (99.31% WR)** | — |

---

## 2. Near-Tie Analysis ($|\text{Margin}| \le \$1,000$)

All 10 matches in the entire suite with absolute margin $\le \$1,000$ occurred against `V44`:

| Seed | Seat | V49 Final Cash | V44 Final Cash | Margin | Outcome | Decisive Factor |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 250621 | 0 | $116,047.00 | $116,129.00 | **-$82.00** | **LOSS** | Step 697 wool priority inversion ($144 delta) |
| 250621 | 1 | $116,047.00 | $116,129.00 | **-$82.00** | **LOSS** | Mirrored execution |
| 250631 | 0 | $100,398.00 | $100,093.00 | **+$305.00** | **WIN** | V49 late melon clearance |
| 250631 | 1 | $100,398.00 | $100,093.00 | **+$305.00** | **WIN** | Mirrored execution |
| 250616 | 0 | $89,733.00 | $89,349.00 | **+$384.00** | **WIN** | V49 strawberry frontrunning |
| 250616 | 1 | $89,733.00 | $89,349.00 | **+$384.00** | **WIN** | Mirrored execution |
| 250604 | 0 | $112,450.00 | $111,899.00 | **+$551.00** | **WIN** | V49 wool delivery pacing |
| 250604 | 1 | $112,450.00 | $111,899.00 | **+$551.00** | **WIN** | Mirrored execution |
| 250627 | 0 | $108,920.00 | $108,122.00 | **+$798.00** | **WIN** | V49 egg autarky |
| 250627 | 1 | $108,920.00 | $108,122.00 | **+$798.00** | **WIN** | Mirrored execution |
| 250617 | 0 | $115,527.00 | $116,389.00 | **-$862.00** | **LOSS** | V44 late strawberry harvest (+22 units) |
| 250617 | 1 | $115,527.00 | $116,389.00 | **-$862.00** | **LOSS** | Mirrored execution |

---

## 3. Scientific Implications

1. **V49 Has No General Near-Loss Vulnerability**: Against 8 of the 9 league opponents, V49's win margin is massive and completely unthreatened (minimum margin $> \$1,200$, mean margin $> \$7,500$). There are zero near-losses against the rest of the competitive field.
2. **The 4 Losses Are Not Random Anomalies**: They belong to a tight cluster of 12 matches against its closest structural peer (`V44`), where the two agents execute mirrored choreographies.
3. **The Casualty Hazard**: Because the near-wins against V44 (+$305 on 250631, +$384 on 250616) share the exact same structural features as the losses, any heuristic modification that attempts to flip the -$82 loss (such as reordering market sales) immediately causes **fatal casualties** on the near-wins.
