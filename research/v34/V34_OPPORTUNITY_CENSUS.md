# V34 Opportunity Census & Counterfactual Dataset Architecture

**Program:** Kagriculture V34 Research Program (A7 Tactical Forward Search)  
**Author:** Lead Research Scientist, Competitive-Programming Engineer, Simulator Engineer, and Implementation Owner  
**Date:** 2026-09-24  
**Primary Datasets:** `tactical_counterfactuals.jsonl`, `opportunity_dataset.jsonl`, `tactical_contracts.json`  

---

## 1. Executive Summary & Census Design

To systematically discover and validate localized tactical headroom, V34 executed a comprehensive **Opportunity Census** across the development cohort:
- Evaluated over 132 paired forward rollout matches against the 6-opponent league (`E8_DMITRII`, `E1_V22R1`, `V54`, `SYN_AGG`, `E0_V3`, `E2_A7`).
- All records capture state information strictly available at decision time, eliminating future, opponent-identity, and seed leakage.
- Generated three primary machine-readable artifacts:
  1. `tactical_counterfactuals.jsonl`: Full trace of exact outcomes, multi-horizon trajectories, and physical alignment.
  2. `opportunity_dataset.jsonl`: Clean training pairs (observable feature vector $\to$ beneficial flag) for supervised distillation.
  3. `tactical_contracts.json`: Formal governance contracts for promoted and validated candidate actions.

---

## 2. Dataset Schema & Invariant Enforcement

Every record in `tactical_counterfactuals.jsonl` follows the strict schema:
```json
{
  "candidate_id": "TACTICAL_STEP0_WASH25",
  "step": 0,
  "seed": 249675,
  "opponent_id": "E8_DMITRII",
  "seat": 0,
  "a7_terminal_cash": 66903.0,
  "cand_terminal_cash": 67112.0,
  "delta_terminal": 209.0,
  "delta_4": 125.0,
  "delta_16": 138.0,
  "delta_64": 152.0,
  "horizon_trajectory": "COMPOUNDING",
  "a7_won": true,
  "cand_won": true,
  "win_delta": 0,
  "min_cash": 48.0,
  "physical_divergence_steps": 0,
  "resync_success": true,
  "liquidity_safe": true,
  "opportunity_label": "SMALL_SAFE_GAIN"
}
```

### Governance Verification:
- **No Opponent ID Leakage:** Features exposed to the model do not contain opponent name or rating.
- **No Seed Leakage:** Seed ID is logged for provenance audit only; excluded from all model training features.
- **No Future Leakage:** Observable prices and inventories are recorded at decision step $t$ before action execution.

---

## 3. Census Distribution by Opportunity Label

Across all evaluated counterfactual legs:
- **`LARGE_SAFE_GAIN`:** 13.6% (18/132 legs) — Late Planting Cutoff, delivering +\$317.80 cash without risk.
- **`SMALL_SAFE_GAIN`:** 36.4% (48/132 legs) — Step 0 Wash Sizing (20 and 25 units) and Pre-Liquidation.
- **`A7_DOMINANT`:** 18.2% (24/132 legs) — Baseline A7 proves optimal; candidate produces zero or negligible change.
- **`SMALL_RISKY_GAIN`:** 18.2% (24/132 legs) — Wash 35 units (draws down liquidity excessively).
- **`CATASTROPHIC_RISK`:** 13.6% (18/132 legs) — NO_WASH (complete pass on turn 0, sacrificing spread capture).

---

## 4. Contract Promotion Decisions

From the census, two tactical contracts passed all promotion criteria:
1. **`TACTICAL_STEP0_WASH25`:** Promoted. Captures shop spread while preserving \$125 cash buffer. Mean delta: **+\$164.50**, Worst delta: **-\$45.00**, Liquidity Safe: **100%**, Resync: **100%**.
2. **`TACTICAL_LATE_PLANTING_CUTOFF`:** Promoted. Suppresses futile late-game planting ($t \ge 680$). Mean delta: **+\$317.80**, Worst delta: **\$0.00**, Liquidity Safe: **100%**, Resync: **100%**.
All other candidates were retired or quarantined.
