# V32 P5 — ECONOMIC RECOVERY & FIRST-DIVERGENCE METRIC REPORT

## 1. COMPARATIVE METRIC SUMMARY: P4 ARM 1 VS P5 ARM 2

In accordance with Section 25 and Section 26 of the V32 P5 Protocol, this report directly compares the canonical P4 baseline against P5 Arm 2 across all 120 development screen legs (Seeds `249675–249684` $\times$ 6 opponents $\times$ 2 seats):

| Metric | P4 Arm 1 (Baseline) | P5 Arm 2 (Early-Horizon BC) | Delta / Change | Interpretation |
|:---|:---:|:---:|:---:|:---|
| **Step-0 Wash Shape** | 120/120 (100.0%) | 120/120 (100.0%) | 0.0% | Preserved 100% |
| **Step-0 Farmer PASS** | 0/120 (0.0%) | 120/120 (100.0%) | **+100.0%** | **Completely Repaired** |
| **Step-1 Farmer NORTH** | 0/120 (0.0%) | 120/120 (100.0%) | **+100.0%** | **Completely Repaired** |
| **Step-1 Hires (Mean)** | 0.00 hands | 5.00 hands | **+5.00 hands** | **100% Full Hiring Executed** |
| **Median First Action Divergence** | **Step 0** | **Step 2** | **+2 Steps Later** | Divergence delayed past opening |
| **Median First State Divergence** | Step 1 | Step 2 | **+1 Step Later** | State preserved through Step 1 |
| **Terminal Cash (Mean)** | $108.39 | $2.94 | -$105.45 | **Failed Economic Recovery** |
| **Terminal Cash (Median)** | $0.50 | $0.00 | -$0.50 | Flat zero regime |
| **Win Rate** | 0.0% (0/120) | 0.0% (0/120) | 0.0% | 0 wins across panel |

---

## 2. THE ANATOMY OF FAILED ECONOMIC RECOVERY

Section 26 explicitly dictates:
> *"A P5 model that has later divergence and improved teacher fidelity but still earns ~$100 is not a successful policy... The core target is stable closed-loop behavior that translates into materially improved economics."*

Why did successfully repairing Step 0 (`PASS`) and Step 1 (`NORTH` + 5 Hires) fail to improve terminal cash?

### 2.1 The Capital Trap Mechanism
1. **In P4 Arm 1**:
   - The model diverged at Step 0 by moving `WEST`.
   - At Step 1, under an unfamiliar observation, it failed to hire the 5 workers and failed to buy livestock.
   - Because it never hired workers, it never paid worker wages. The $3,000 capital from the wash slowly leaked down to ~$108.
2. **In P5 Arm 2**:
   - The model executed Step 0 and Step 1 with 100% fidelity.
   - It hired 5 workers and purchased livestock contracts, spending **$1,747 in capital** (leaving $1,005).
   - BUT at Step 2: The teacher moves `SOUTH` back to the shed [4, 4] to retrieve the livestock.
   - The Arm 2 model commands `['PICKUP', 'COW']` while standing at [4, 3] (1 tile away from the shed!).
   - The simulator rejects the pickup command because the unit is not adjacent to the shed.
   - The farmer holds zero livestock.
   - At Steps 3–6, the farmer walks North to the board boundary [4, 0] and gets stranded.
   - The 5 hired hands stand idle on the field, and by Step 24 (end of Day 1), the remaining $1,005 is completely consumed by worker wage deductions without a single crop harvested or animal placed!
   - Terminal cash hits **$0.00**.

### 2.2 The Fragility of Open-Loop Behavioral Cloning
This proves a fundamental limitation of standard Behavioral Cloning on rigid macro-trajectories:
- Pure BC cannot learn closed-loop causal recovery.
- An open-loop sequence of 15 dependent steps ($A_0 \to A_1 \to \dots \to A_{14}$) has cumulative success probability $\prod_{t=0}^{14} P(A_t | s_t)$. Even if each step is learned with 95% accuracy, $0.95^{15} \approx 46\%$, and a single positional timing mismatch at Step 2 renders all subsequent investments worthless.
- Without an interactive expert oracle (Case B: A7 is not a Markovian planner) or closed-loop policy-gradient exploration, standard BC cannot self-correct when slightly displaced from the optimal path.
