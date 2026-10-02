# V32 P6 — FARMER CLASS FREQUENCY & EARLY CHOREOGRAPHY AUDIT

## 1. PURPOSE & METHODOLOGY

In accordance with Section 8 and Section 9 of the **V32 P6 Protocol**, this document audits the entire Behavioral Cloning dataset (`results/v32_p2_bc_legs.jsonl`, 96 training legs, 138,240 transitions) to measure opcode frequencies globally, across the early horizon (Steps 1–10), and at Step 2 specifically.

---

## 2. EMPIRICAL CLASS FREQUENCIES

### 2.1 Global Farmer Opcode Frequencies (138,240 Transitions)
| Opcode | Total Count | Relative Frequency |
|:---|:---:|:---:|
| `WEST` | 14,920 | 10.81% |
| `NORTH` | 14,684 | 10.64% |
| `WATER` | 13,628 | 9.87% |
| `EAST` | 12,880 | 9.33% |
| `PASS` | 12,820 | 9.29% |
| `SOUTH` | 12,100 | 8.77% |
| `HARVEST` | 11,280 | 8.17% |
| `CARE` | 10,596 | 7.68% |
| `COLLECT_FERTILIZER` | 10,468 | 7.58% |
| `FEED` | 9,368 | 6.79% |
| `PICKUP` | 4,796 | 3.47% |
| `PLACE` | 4,124 | 2.99% |
| `PLANT` | 3,416 | 2.47% |
| `FERTILIZE` | 1,188 | 0.86% |
| `DROP` | 1,068 | 0.77% |
| `DIG` | 512 | 0.37% |
| `BUILD_PASTURE` | 200 | 0.14% |
| `BUILD_COOP` | 0 | 0.00% |

Globally, `SOUTH` represents 8.77% of all actions, while `PICKUP` represents 3.47%.

---

### 2.2 Early Horizon (Steps 1–10) Farmer Frequencies (1,920 Transitions)
| Opcode | Early Count (Steps 1–10) | Relative Frequency |
|:---|:---:|:---:|
| `NORTH` | 384 | 20.00% |
| `PICKUP` | 384 | 20.00% |
| `SOUTH` | 192 | 10.00% |
| `WEST` | 192 | 10.00% |
| `BUILD_PASTURE` | 192 | 10.00% |
| `PLACE` | 192 | 10.00% |
| `FEED` | 192 | 10.00% |
| `CARE` | 192 | 10.00% |

In Steps 1–10, `PICKUP` occurs **twice as frequently** as `SOUTH` (20.0% vs 10.0%).

---

### 2.3 Step-by-Step Trajectory Choreography (Steps 0–10)
Analyzing the demonstration targets step-by-step across all 192 demonstration sequences:

| Timestep | Farmer Position | Expert Target Opcode | Target Count | Share | Economic Function |
|:---:|:---:|:---:|:---:|:---:|:---|
| **Step 0** | `[4, 4]` | **`PASS`** | 192 / 192 | **100.0%** | Opening market wash executed |
| **Step 1** | `[4, 4]` | **`NORTH`** | 192 / 192 | **100.0%** | Steps to [4, 3], hires 5 hands, buys livestock |
| **Step 2** | `[4, 3]` | **`SOUTH`** | 192 / 192 | **100.0%** | **Steps back to [4, 4] shed tile** |
| **Step 3** | `[4, 4]` | **`PICKUP`** | 192 / 192 | **100.0%** | Picks up COW from shed |
| **Step 4** | `[4, 4]` | **`PICKUP`** | 192 / 192 | **100.0%** | Picks up SHEEP from shed |
| **Step 5** | `[4, 4]` | **`NORTH`** | 192 / 192 | **100.0%** | Walks towards pasture site |
| **Step 6** | `[4, 3]` | **`WEST`** | 192 / 192 | **100.0%** | Positions for pasture build |
| **Step 7** | `[3, 3]` | **`BUILD_PASTURE`** | 192 / 192 | **100.0%** | Constructs pasture |
| **Step 8** | `[3, 3]` | **`PLACE`** | 192 / 192 | **100.0%** | Places livestock into pasture |
| **Step 9** | `[3, 3]` | **`FEED`** | 192 / 192 | **100.0%** | Feeds livestock |
| **Step 10** | `[3, 3]` | **`CARE`** | 192 / 192 | **100.0%** | Cares for livestock |

---

## 3. ROOT CAUSE ATTRIBUTION

1. **Deterministic Target at Step 2**:
   Across all 4 training experts (`E0_V3`, `E2_A7`, `E7_W2015`, `E6_W72`), the Step-2 action is **100.0% `SOUTH`** (192 / 192).
   There is **ZERO** `PICKUP` at Step 2 in the training set.
2. **Temporal Entanglement / Premature Triggering**:
   At Step 1, the market purchases 2 Cows and 2 Sheep into the shed.
   At Steps 3 and 4, the farmer executes `PICKUP` twice.
   Because the state features at Step 2 reflect `COW: 2, SHEEP: 2` in the shed, the model's spatial representation fails to enforce the geometric precondition that the farmer must first return `SOUTH` to `[4, 4]` before issuing `PICKUP`.
   The model triggers the `PICKUP` opcode **one step prematurely** at Step 2 while still standing at `[4, 3]`.
