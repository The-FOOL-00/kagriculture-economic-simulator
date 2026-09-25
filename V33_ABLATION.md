# V33 Comprehensive Ablation Program: Component Decomposition

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Scope:** Full comparative ablation of baselines, route portfolios, switching frequencies, resets, market overlays, and meta-controllers across the 6-opponent league.

---

## 1. Master Ablation Matrix

All variants evaluated across identical DEV seeds (`249675..249679`), both seats, vs all 6 League Opponents (60 paired legs per configuration):

| Category | Variant / Configuration | League Win Rate | Mean Cash ($) | Paired $\Delta$ vs A7 | Switches / Resets | Catastrophic Tail Risk | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baselines** | `R0_A7` (Protected Incumbent) | **88.3% (53/60)** | **$102,037.15** | **$0.00** | 0 | **$0.00** | **BENCHMARK** |
| | `R1_V22R1` (Slot A Champion) | 66.7% (40/60) | $101,303.53 | -$733.62 | 0 | -$1,280.00 | Static Baseline |
| **Route Portfolio**| Best Static Alt (`R1_V22R1`) | 66.7% (40/60) | $101,303.53 | -$733.62 | 0 | -$1,280.00 | Sub-dominant |
| | Static Pure Livestock (`R2_DMITRII`) | 52.0% (26/50) | $85,002.30 | -$4,012.00 | 0 | -$8,433.00 | Specialized |
| | Unconditional 1-Switch ($t=48$) | 33.3% (20/60) | $100,951.95 | -$1,085.20 | 60 | -$8,433.00 | Failed |
| **Meta Selector** | V33 Gated Selector (0 Switches / Abstain) | **88.3% (53/60)** | **$102,037.15** | **$0.00** | 0 | **$0.00** | Safe Fallback |
| | V33 Gated Selector (1 Switch Allowed) | **88.3% (53/60)** | **$102,037.15** | **$0.00** | 0 | **$0.00** | Active Candidate |
| | Multi-Switching (2+ Switches Allowed) | 28.3% (17/60) | $94,110.00 | -$7,927.15 | >60 | -$12,500.00 | Disqualified |
| **Meta Reset** | 1 Midgame Reset ($t=48$) | **88.3% (53/60)** | **$102,037.15** | **$0.00** | 0 | **$0.00** | Neutral (Abstained) |
| | 2 Midgame Resets ($t \in \{48, 144\}$) | **88.3% (53/60)** | **$102,037.15** | **$0.00** | 0 | **$0.00** | Neutral (Abstained) |
| **Market Timing** | Pure $R0\_A7$ + Market Overlay | 83.3% (50/60) | $101,875.55 | -$161.60 | 0 (Market Only) | -$296.40 | Disqualified (F7) |
| **Full V33** | Route Selector + Reset + Market Overlay | 83.3% (50/60) | $101,875.55 | -$161.60 | 0 | -$296.40 | Degraded by Market |
| **Optional PPO** | High-Level RL Macro Policy | <80.0% | <$98,000 | -$4,000+ | High variance | Severe | Ruled out (Sec 32) |

---

## 2. Component-by-Component Scientific Attribution

1. **Why Pure A7 Beats the Route Portfolio:**
   - In 48 out of 50 inter-route matches, A7 directly defeated every alternative expert. Its deterministic single-quadrant monoculture generates superior capital velocity ($\approx \$102\text{k}$ mean cash vs $\approx \$85\text{k}–\$101\text{k}$).
   - The route dominance graph is completely transitive: no non-transitive "rock-paper-scissors" loop exists to exploit.
2. **Why Unconditional Switching Fails Catastrophically:**
   - Flipping execution from A7 to Dmitrii midgame without regard to state drops win rate by **-55.0%** (from 88.3% to 33.3%). A7's specialized infrastructure cannot be converted into livestock facilities without devastating liquidation losses.
3. **Why the V33 Selector Preserves 88.3% Win Rate:**
   - The selective prediction gate ($\ge \$2,500$ gain, $\ge 0.70$ confidence) correctly recognized that on normal seeds, switching is sub-optimal. It abstained in 100% of DEV matches, completely preventing the downside collapse that destroyed RL-X2 and unconditional policies.
4. **Why Market Sell Reordering Degrades Performance:**
   - Reordering sell orders based on instantaneous price impact delays high-velocity wheat cash inflows, starving the farm of working capital on adjacent turns and causing order rejections (-5.0% win rate drop).
