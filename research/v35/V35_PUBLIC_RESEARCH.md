# V35 Public Research Track: Opening Economics, Replay Meta & Public State Routers

## 1. Executive Summary
A comprehensive survey of public Kaggriculture research was conducted to catalog opening-state strategies, capital initialization mechanics, liquidity thresholds, and expert trajectory properties. This survey informs V35's investigation of whether opening capital optimization represents an isolated parameter tweak or a fundamental property of the Kaggriculture economic landscape.

---

## 2. Public Literature & Repository Matrix

| Mechanism / Source | Public Source & Authors | Score / Metric | Core Method | Relevance to V35 Opening Optimization | Reproducibility |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Step-0 Wheat Round Trip** | Ahmed Berat Ozer (Notebooks V43, V45) | ~2700+ LB | Simultaneous BUY/SELL of wheat at Step 0 to exploit initial pricing inefficiency and prime town market queues. | **HIGH.** Lineage of A7's 30/30 wash and V34's 25/25 modification. Directly controls opening cash float. | **100% REPRODUCIBLE** (embedded in A7/V3 codebase) |
| **Funded Atomic Opening** | Rayk Kretzschmar ("Rank Your Agent") | ~2650 LB | Coordinated Step 1 unit placement combined with bulk tool and animal purchases. | **HIGH.** Governs the Step 1 liquidity drain ($1,946 spent on 5 hires, 2 cows, 2 sheep). | **REPRODUCIBLE** |
| **Dynamic Shop Pairing Router** | `yhay81` (`shop-router-0911-simple`) | ~2720 LB | Static pre-computed action tapes keyed by shop unlock order and early market liquidity. | **MEDIUM.** Demonstrates that early capital dictates downstream shop access and tape compatibility. | **REPRODUCIBLE** |
| **Declarative Multi-Agent Farming** | `lixingtao123` (Variant V54) | ~2780 LB | Declarative constraint solving for crop cycles; conservative liquidity buffers before wage deductions. | **HIGH.** Validates that cash reserves must exceed daily wage obligations ($N_{\text{hands}} \times \$10$). | **100% REPRODUCIBLE** (in `external_repos`) |
| **Deterministic Terminal Harvest** | Dmitrii Gluzdov | 2800+ LB | 64-step deterministic forward simulation for terminal liquidation and physical cargo clearance. | **MEDIUM.** A7 incorporates Dmitrii's terminal rescue; V35 must verify zero downstream interference. | **REPRODUCIBLE** |
| **Storage & Weed Guards** | `tetsutani` & `aurax7` | ~2680 LB | Reactive checks for weed blockage, shed capacity constraints ($\le 99$ at hour 23), and order clamping. | **MEDIUM.** Invariant checking patterns adopted in V34/V35 LiquidityGuard. | **REPRODUCIBLE** |

---

## 3. Key Public Meta Findings & Hypotheses for V35

1. **The Origin of the 30/30 Wash:**
   In early public baselines (V43/V3), agents executed an aggressive 50/50 wheat wash at step 0 to capture maximum immediate spread. However, as the competition meta evolved and opponents became more aggressive in dumping or competing for early liquidity, 50/50 caused severe working capital starvation on Step 1. A7 ablated this down to 30/30, which stabilized the farm and vaulted it to the top tier.
2. **The 25/25 Hypothesis:**
   V34's finding that 25/25 outperforms 30/30 represents the logical continuation of this capital conservation curve: capturing 83.3% of the spread while freeing up an additional \$125 in immediate liquid cash float.
3. **Public Route Meta Compatibility:**
   Public research confirms that route-replay agents are hyper-sensitive to cash dips during the first 24 ticks (the "nursery phase"). If cash falls below the threshold needed to purchase seeds on the exact tick an empty tilled plot becomes available, the entire 72-tick crop rotation is offset, leading to compounded terminal harvest losses.
