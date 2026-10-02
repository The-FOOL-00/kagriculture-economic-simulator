# V49 Blocked Action Loss Table (Phase 6 Forensics)

**Program:** Kagriculture V51 Research Program  
**Evaluation Target:** All 11 Historical Losses of V49 across 1,536 Benchmark Legs  
**Opponent:** V44 Incumbent (100% of V49 losses occurred against V44 on Route 0)  

---

## Forensic Loss Table

| LOSS_ID | SEED | SEAT | OPPONENT | FIRST_DIVERGENCE | BLOCKER_TYPE | INTENDED_ACTION | REPAIR_ACTION | REPLAY_STEP | TERMINAL_DELTA | OUTCOME_BEFORE | OUTCOME_AFTER | GENERALIZABLE | CONFIDENCE |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **L01** | 250416 | 0 | V44 | Step 520 (Route 0 delivery path) | **B2 (Path/Occupancy)** | Move to Shop with Carrot | Yield/Re-route | Step 524 | +$0.00 | LOSS (-$716) | LOSS (-$716) | No (Choreography tight) | High |
| **L02** | 250416 | 1 | V44 | Step 520 (Route 0 delivery path) | **B2 (Path/Occupancy)** | Move to Shop with Carrot | Yield/Re-route | Step 524 | +$0.00 | LOSS (-$716) | LOSS (-$716) | No (Choreography tight) | High |
| **L03** | 250428 | 0 | V44 | Step 624 (Late plot harvest) | **B4 (Timing Blocker)** | Final Crop Delivery | Advance Liquidation | N/A | +$0.00 | LOSS (-$31) | LOSS (-$31) | No (Macro pace) | High |
| **L04** | 250428 | 1 | V44 | Step 624 (Late plot harvest) | **B4 (Timing Blocker)** | Final Crop Delivery | Advance Liquidation | N/A | +$0.00 | LOSS (-$160) | LOSS (-$160) | No (Macro pace) | High |
| **L05** | 250433 | 0 | V44 | Step 144 (Route 0 EXP240 branch) | **B5 (Route-State Blocker)** | Cow Acquisition Sequence | None (Route 0 tape) | N/A | +$0.00 | LOSS (-$470) | LOSS (-$470) | Irreducible | Very High |
| **L06** | 250433 | 1 | V44 | Step 144 (Route 0 EXP240 branch) | **B5 (Route-State Blocker)** | Cow Acquisition Sequence | None (Route 0 tape) | N/A | +$0.00 | LOSS (-$470) | LOSS (-$470) | Irreducible | Very High |
| **L07** | 250436 | 0 | V44 | Step 36 (Opening Goose buy) | **B5 (Route-State Blocker)** | R42 Egg Arbitrage Deficit | None (Macro opening) | N/A | +$0.00 | LOSS (-$1,405) | LOSS (-$1,405) | Irreducible | Very High |
| **L08** | 250436 | 1 | V44 | Step 36 (Opening Goose buy) | **B5 (Route-State Blocker)** | R42 Egg Arbitrage Deficit | None (Macro opening) | N/A | +$0.00 | LOSS (-$1,405) | LOSS (-$1,405) | Irreducible | Very High |
| **L09** | 250439 | 0 | V44 | Step 36 (Opening Goose buy) | **B5 (Route-State Blocker)** | R42 Egg Arbitrage Deficit | None (Macro opening) | N/A | +$0.00 | LOSS (-$1,407) | LOSS (-$1,407) | Irreducible | Very High |
| **L10** | 250439 | 1 | V44 | Step 36 (Opening Goose buy) | **B5 (Route-State Blocker)** | R42 Egg Arbitrage Deficit | None (Macro opening) | N/A | +$0.00 | LOSS (-$1,407) | LOSS (-$1,407) | Irreducible | Very High |
| **L11** | 250497 | 1 | V44 | Step 144 (Route 0 EXP240 branch) | **B5 (Route-State Blocker)** | Cow Acquisition Sequence | None (Route 0 tape) | N/A | +$0.00 | LOSS (-$901) | LOSS (-$901) | Irreducible | Very High |

---

## Key Forensic Discoveries

1. **Zero Weed Collisions (B1 = 0):** In all 11 losses, exactly 0 weed-blocked actions occurred. Weeds did not cause or contribute to any loss.
2. **Structural Dominance of Route-State Discrepancies (B5):**
   - 7 of the 11 losses (L05, L06, L07, L08, L09, L10, L11) are pure **macro-portfolio divergences**. V44 executes an opening Goose purchase (step 36) or early Cow scaling (step 144) that captures high early product prices. Tactical action repairs at the micro-level cannot bridge a $1,400 deficit established on Step 36.
3. **Path & Timing Bottlenecks (B2 & B4):**
   - In L01/L02 (Seed 250416), unit congestion slightly delayed carrot deliveries. However, altering unit movement paths without full route choreography resynchronization introduces worker collisions and destroys downstream timing.
4. **Causal Conclusion:**
   Micro weed-repair provides exactly **zero rescue power** on the historical loss corpus. Rescuing these matches requires addressing macro route selection (Route 0 vs Route 2) rather than micro tile clearing.
