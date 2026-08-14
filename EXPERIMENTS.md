# Kaggriculture Experimental Log & Benchmark Scoreboard

All candidate architectures are rigorously evaluated against `agents/golden_v1.py` across identical seed sets before graduation to production.

---

## 🏆 Golden Control Scoreboard

| Agent Name | Description | Test Opponent | Matches | Win Rate | Mean Cash (Us) | Mean Cash (Opp) | Margin |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`golden_v1.py`** | Apex Grandmaster v3 (Town Frontrunner + 75 Tiles) | `starter` | 10 | **100.0%** | **$43,982.30** | $3,488.70 | **+$40,493.60** |

---

## 🧪 Experiment Registry

### Experiment 01 — Baseline Calibration & Benchmark Harness Validation
- **Hypothesis**: Parallel process harness executes exact deterministic 720-step episodes across multi-core CPUs with zero serialization errors.
- **Result**: Validated on 10 matches (Seeds 2000–2009) in 5.88 seconds. 100% win-rate, $43,982.30 mean final cash.

### Experiment 02 — Titan Apex v3 vs Golden Control v1 (50-Match Head-to-Head Tournament)
- **Hypothesis**: Dynamic Shop Demand Elasticity + Non-Linear Slippage-Aware Batch Selling + Pre-Emptive Opponent Radar outperforms the fixed batch baseline.
- **Seeds**: 5000–5049 (50 matches, swapped player sides every game).
- **Result**:
  - **Win Rate:** **78.0% (39 Wins / 11 Losses / 0 Ties)** 🏆
  - **Mean Final Cash (Titan Apex v3):** **$36,919.14**
  - **Mean Final Cash (Golden Control v1):** **$31,741.60**
  - **Head-to-Head Advantage:** **+$5,177.54 per game**
- **Conclusion**: Statistically significant superiority confirmed. Graduated to production `main.py`.
