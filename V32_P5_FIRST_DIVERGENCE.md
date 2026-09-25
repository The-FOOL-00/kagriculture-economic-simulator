# V32 P5 — FIRST-DIVERGENCE FORENSICS & ATTRIBUTION

## 1. EXECUTIVE SUMMARY

In accordance with Sections 10 and 12 of the V32 P5 Protocol, this forensic report pinpoints the exact timestep, action head, parameter, and physical consequence of the first divergence between the canonical P4 Arm 1 policy and the expert demonstration.

### Formal Conclusion:
> **The initial divergence in P4 Arm 1 is NOT at steps 1–10. It is at STEP 0.**
>
> While P4 successfully recovered the **Step-0 Market Wash** (`[['BUY_PRODUCT', 'WHEAT', 30], ['SELL', 'WHEAT', 30]]`), it did so via selective weighting ($\lambda_{crit}=50.0$) on **market slots only**.
>
> The **Farmer Unit Head** was unweighted. Due to extreme rare-pattern dilution across 138,048 training transitions, the model learned to command `['WEST']` (54.64% probability) instead of `['PASS']` (4.46% probability) on Step 0.
>
> This single unweighted action head error displaced the farmer to tile (4, 5) at Step 0, which triggered the entire downstream collapse at Step 1.

---

## 2. SEED-BY-SEED DIVERGENCE RECORDS

Across all 5 development screen seeds (`249675–249679`):

| Seed | First Action Divergence ($t_{act}$) | Slot & Head Differing | Teacher Action | Policy Action | First State Divergence ($t_{state}$) | First Economic Divergence ($t_{econ}$) | Physical Consequence |
|:---:|:---:|:---|:---|:---|:---:|:---:|:---|
| **249675** | Step 0 | Farmer Unit Op | `['PASS']` | `['WEST']` | Step 1 | Step 2 | Farmer moves to (4,5); fails to hire hands at Step 1 |
| **249676** | Step 0 | Farmer Unit Op | `['PASS']` | `['WEST']` | Step 1 | Step 2 | Farmer moves to (4,5); fails to hire hands at Step 1 |
| **249677** | Step 0 | Farmer Unit Op | `['PASS']` | `['WEST']` | Step 1 | Step 2 | Farmer moves to (4,5); fails to hire hands at Step 1 |
| **249678** | Step 0 | Farmer Unit Op | `['PASS']` | `['WEST']` | Step 1 | Step 2 | Farmer moves to (4,5); fails to hire hands at Step 1 |
| **249679** | Step 0 | Farmer Unit Op | `['PASS']` | `['WEST']` | Step 1 | Step 2 | Farmer moves to (4,5); fails to hire hands at Step 1 |

---

## 3. ERROR TAXONOMY & ATTRIBUTION CHAIN

We evaluate the seven diagnostic questions required by Section 12:

1. **Was the action unreasonable given the policy's observed state?**
   - Yes. At step 0, all 240 training legs (100.0%) exhibit `['PASS']`. Moving `['WEST']` into the edge of the farm quadrant serves no economic or agronomic purpose.
2. **Was the action reasonable but different from the teacher?**
   - No. It is an ungrounded artifact of gradient dilution.
3. **Did the action create a new state never represented in training?**
   - Yes. In 100% of training data, the farmer at step 1 is at position (5, 5) and begins moving `['NORTH']`. A state with the farmer at (4, 5) on step 1 with $3,000 cash **does not exist anywhere in the training corpus**.
4. **Did the next state still resemble teacher states?**
   - No. Feature distance jumped immediately from 0.000 to **21.376**.
5. **Did the next action become significantly less predictable?**
   - Yes. Under this novel state, the model completely failed to predict the multi-slot market orders (hiring 5 hands and purchasing 2 cows + 2 sheep), emitting spurious product orders instead.
6. **Did that lead to a second divergence?**
   - Yes. At Step 1, the policy hired 0 hands (vs teacher's 5 hands) and bought 0 livestock (vs teacher's 4 livestock).
7. **Did the second divergence cause the economic collapse?**
   - Yes. With 0 hands, the policy had no labor to harvest or water, and with no livestock, it had no animal compounding. Cash drained from initial purchases down to ~$72 terminal cash.
