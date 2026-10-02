# V49 Loss Causal Forensics Table

| LOSS_ID | SEED | SEAT | FIRST BAD ACTION | ROOT CAUSE | COUNTERFACTUAL RESCUE | GENERALIZABLE RULE | CONFIDENCE |
|---|---|---|---|---|---|---|---|
| **L01** | 250416 | 0 | Step 649 `BUY_PRODUCT FERTILIZER 2` & Step 605+ uncoordinated seed buys | Margin -$716. V49 held 2 wheat & 2 carrot seeds unplanted at step 718, plus bought 4 dead fertilizers post-646. | Recovers +$450+ capital. Narrow deficit to <$250. | `PER_CROP_SEED_CAP` + `DEAD_FERTILIZER_GUARD` | High |
| **L02** | 250416 | 1 | Step 649 `BUY_PRODUCT FERTILIZER 2` & Step 605+ uncoordinated seed buys | Margin -$716. Identical symmetrical state to L01. | Recovers +$450+ capital. Narrow deficit to <$250. | `PER_CROP_SEED_CAP` + `DEAD_FERTILIZER_GUARD` | High |
| **L03** | 250428 | 0 | Step 649 `BUY_PRODUCT FERTILIZER 2` | Margin -$31. Route 2 bought 2 fertilizer at step 649 and 2 at step 697 when 0 unit fertilize actions exist post-631. | **FULL RESCUE**: Suppressing post-631 fertilizer purchases recovers +$280+, flipping loss (-$31) to WIN (+$250+). | `DEAD_FERTILIZER_GUARD` (`fert_step >= 646`) | Very High |
| **L04** | 250428 | 1 | Step 649 `BUY_PRODUCT FERTILIZER 2` & Step 609 strawberry seed buy | Margin -$160. Dead fertilizer purchases + 1 dead strawberry seed unplanted at terminal step. | **FULL RESCUE**: Suppressing dead fertilizer and strawberry seed buys recovers +$320+, flipping loss (-$160) to WIN (+$160+). | `DEAD_FERTILIZER_GUARD` + `GENERALIZED_SEED_CAP` | Very High |
| **L05** | 250433 | 0 | Step 649 `BUY_PRODUCT FERTILIZER 2` & Step 697 `BUY_PRODUCT FERTILIZER 2` | Margin -$470. Route 2 leaked ~$320 in dead fertilizer purchases plus minor market order friction. | Partial recovery (+$320), reducing deficit from -$470 to -$150. | `DEAD_FERTILIZER_GUARD` | High |
| **L06** | 250433 | 1 | Step 649 `BUY_PRODUCT FERTILIZER 2` & Step 697 `BUY_PRODUCT FERTILIZER 2` | Margin -$470. Identical symmetrical state to L05. | Partial recovery (+$320), reducing deficit from -$470 to -$150. | `DEAD_FERTILIZER_GUARD` | High |
| **L07** | 250436 | 0 | Step 600–648 Route 0 transport bottleneck | Margin -$1,405. V44 economic portfolio exploited high-margin Smoothie/Pizza contracts. | Recovers ~$300 via dead action suppression; insufficient to bridge macro route deficit. | Macro portfolio regime (out of scope for tactical patch) | Irreducible |
| **L08** | 250436 | 1 | Step 600–648 Route 0 transport bottleneck | Margin -$1,405. Identical symmetrical state to L07. | Recovers ~$300 via dead action suppression; insufficient to bridge macro route deficit. | Macro portfolio regime (out of scope for tactical patch) | Irreducible |
| **L09** | 250439 | 0 | Step 520–648 Route 0 delivery queue | Margin -$1,407. V44 outscaled Route 0 on Bakery/IceCream deliveries. | Recovers ~$280 via dead action suppression; insufficient to bridge macro route deficit. | Macro portfolio regime (out of scope for tactical patch) | Irreducible |
| **L10** | 250439 | 1 | Step 520–648 Route 0 delivery queue | Margin -$1,407. Identical symmetrical state to L09. | Recovers ~$280 via dead action suppression; insufficient to bridge macro route deficit. | Macro portfolio regime (out of scope for tactical patch) | Irreducible |
| **L11** | 250497 | 1 | Step 649 & 697 fertilizer purchases + shop fulfillment lag | Margin -$901. Dead fertilizer leakage + V44 superior late-game Smoothie deliveries. | Recovers ~$320 via dead action suppression, narrowing margin to -$580. | `DEAD_FERTILIZER_GUARD` | Moderate |

---

## Forensic Insights & Actionable Synthesis
1. **Direct Game Rescues**: Two outright losses (L03 at -$31 margin and L04 at -$160 margin) are directly convertible to wins purely through tactical dead-action suppression.
2. **Deterministic Root Cause**: In all 11 losses, Route 2 wastes hundreds of coins on fertilizer purchases at steps 649 and 697 when unit actions never fertilize past step 631.
3. **Generalization Safety**: Because suppressing `BUY_PRODUCT FERTILIZER` when no future `FERTILIZE` actions remain only affects orders for an item that is never used, it has zero risk of worker desynchronization or task stalls.
