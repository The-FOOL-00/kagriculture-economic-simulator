# V32 P4 BASELINE REPRODUCTION (Arm 0)

Source Checkpoints:
- `results/v32_p3_bc.npz` (LR 3e-4, 30 epochs, 277k params)
- `results/v32_p3_bc_lr3e3.npz` (LR 3e-3, 30 epochs, 277k params)

## 1. Step-0 Action Reproduction

Evaluated over all 240 step-0 samples across the dataset (192 train + 48 val):

| Checkpoint | Slot 0 Op | Slot 0 Item | Slot 0 Qty | Slot 1 Op | Slot 1 Item | Slot 1 Qty | Slots 2..9 | Wash Shape Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ground Truth (All Teachers)** | **BUY_PRODUCT** | **WHEAT** | **7–50** | **SELL** | **WHEAT** | **2–50** | **NOOP** | **240/240 (100%)** |
| `v32_p3_bc.npz` (3e-4) | SELL | WHEAT | 30 | BUY_PRODUCT | WHEAT | 30 | NOOP | **0/240 (0.0%)** |
| `v32_p3_bc_lr3e3.npz` (3e-3) | SELL | WHEAT | 30 | BUY_PRODUCT | WHEAT | 30 | NOOP | **0/240 (0.0%)** |
| `v32_p3_bc_a7.npz` (A7-only) | NOOP | — | — | NOOP | — | — | NOOP | **0/240 (0.0%)** |

### Slot Probability Distributions at Step 0:
- **`v32_p3_bc.npz` (3e-4)**:
  - Slot 0: $P(\text{BUY\_PRODUCT}) = 0.234$, $P(\text{SELL}) = 0.763$, $P(\text{NOOP}) = 0.002$.
  - Slot 1: $P(\text{BUY\_PRODUCT}) = 0.580$, $P(\text{SELL}) = 0.248$, $P(\text{NOOP}) = 0.166$.
- **`v32_p3_bc_lr3e3.npz` (3e-3)**:
  - Slot 0: $P(\text{BUY\_PRODUCT}) = 0.187$, $P(\text{SELL}) = 0.813$, $P(\text{NOOP}) = 0.000$.
  - Slot 1: $P(\text{BUY\_PRODUCT}) = 0.952$, $P(\text{SELL}) = 0.041$, $P(\text{NOOP}) = 0.004$.

Both checkpoints produce the exact reversed wash:
$$\text{Market} = [[\text{SELL}, \text{WHEAT}, 30], [\text{BUY\_PRODUCT}, \text{WHEAT}, 30]]$$

## 2. Unit and Global Accuracy Metrics

From `results/v32_p3_bc_report.json` and `results/v32_p3_bc_lr3e3_report.json`:

| Metric | P3 3e-4 (Train) | P3 3e-4 (Val) | P3 3e-3 (Train) | P3 3e-3 (Val) |
| :--- | :--- | :--- | :--- | :--- |
| `full_exact` | 0.047 | 0.046 | 0.071 | 0.071 |
| `farmer_op` | 0.478 | 0.468 | 0.537 | 0.535 |
| `unit_op` | 0.476 | 0.470 | 0.501 | 0.499 |
| `unit_arg` | 0.940 | 0.925 | 0.946 | 0.932 |
| `unit_qty` | 0.833 | 0.804 | 0.849 | 0.822 |
| `market_op` | 0.974 | 0.969 | 0.985 | 0.983 |
| `market_op_nonnoop` | 0.824 | 0.801 | 0.908 | 0.902 |
| `market_item` | 0.772 | 0.744 | 0.775 | 0.754 |
| `market_qty` | 0.803 | 0.759 | 0.804 | 0.759 |

## 3. Closed-Loop Economic Baseline

Evaluated across 120 legs on seeds 249675–249684 vs 6 opponents:

| Arm | Mean Cash | Median Cash | Max Cash | Win Rate | First Divergence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **A7 Reference** | $90,965 | $88,470 | $142,499 | 100% | — |
| **P3 BC (3e-4)** | $467 | $448 | $1,243 | 0.0% (0/120) | Step 0 (Slot order) |
| **P3 BC (3e-3)** | $60 | $0 | $2,829 | 0.0% (0/120) | Step 0 (Slot order) |

## 4. Baseline Conclusion
The P3 baseline demonstrates high general market fidelity (~90% non-NOOP accuracy) and solid unit parity, but **0/240 step-0 wash recovery** and **0/120 closed-loop wins**, with first divergence occurring at step 0 due solely to market slot ordering confusion.
