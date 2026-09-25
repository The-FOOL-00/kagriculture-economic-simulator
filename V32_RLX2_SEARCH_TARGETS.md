# V32 RL-X2: Strategic Search Targets (RLX2-F5)

## 1. Executive Summary

This report documents the generation, filtering, and analysis of exact strategic search targets under Experiment **RLX2-F5**. 

Rather than relying purely on random Monte Carlo exploration in high-dimensional trajectory space, the RL-X2 system leverages the exact, deterministic Kaggle simulation engine as a counterfactual evaluation oracle. At critical economic decision horizons, every legal strategic macro-action $a \in \mathcal{A}_{\text{legal}}(s_t)$ is evaluated by:
1. Stepping the environment under macro-intent $a$ for $H = 4$ simulation ticks.
2. Resuming the deterministic A7 policy from step $t + 4$ to episode termination at step 720.
3. Measuring the counterfactual terminal cash realization $V(s_t, a)$ against the A7 baseline continuation $V(s_t, 0)$.

A decision state is defined as an **Actionable Strategic Target** if:
$$\Delta^*(s_t) = \max_{a \in \mathcal{A}} V(s_t, a) - V(s_t, 0) > 0$$

Target generation is conducted in parallel using an 8-worker process pool across pilot training seeds from `V32_TRAIN` against both `E2_A7` (mirror) and `E8_DMITRII` (asymmetric competitive frontier).

---

## 2. Decision Steps & Temporal Distribution

Targets are evaluated at 11 causally significant macroeconomic inflection points throughout the 720-step horizon:

| Decision Step | Game Day | Phase | Economic Significance |
| :---: | :---: | :---: | :--- |
| **72** | Day 3 | Early | First shop unlock (Bakery / Dairy); initial seed & input ramp |
| **144** | Day 6 | Early | Second shop unlock; pasture layout & livestock entry decisions |
| **216** | Day 9 | Early-Mid | Third shop unlock; compounding capital allocation |
| **288** | Day 12 | Mid | Mid-game land expansion & secondary crop cycle initiation |
| **360** | Day 15 | Mid | Mid-game labor and cash reinvestment vs holding |
| **432** | Day 18 | Mid | Pre-peak crop planting & inventory positioning |
| **504** | Day 21 | Late-Mid | Late crop cycle commitments & shop demand fulfillment |
| **576** | Day 24 | Late | Penultimate production cycle; crop vs livestock prioritization |
| **614** | Day 25.5 | Late | P11 forensic market shock inflection point (Dmitrii melon dump) |
| **648** | Day 27 | Pre-terminal | Final planting cutoff; pre-liquidation harvest scheduling |
| **696** | Day 29 | Pre-terminal | Market inventory dumping & final asset conversion |

*(Note: Terminal steps 712–718 remain strictly quarantined per P11 results; zero targets are evaluated in the terminal physical window).*

---

## 3. Empirical Discoveries & Strategic Headroom

Initial extraction across pilot seeds revealed striking, reproducible positive strategic deviations:

### Finding 1: Massive Alpha via Mid-Game Land Expansion (Action 9: `EXPAND_LAND`)
* **Inflection Point:** Step 288 (Day 12).
* **Observed Delta vs A7:**
  * Against `E2_A7` (Seed 249635, Seat 0): **+$11,179.00** ($86,303 vs $75,124 baseline).
  * Against `E8_DMITRII` (Seed 249635, Seat 0): **+$5,528.00** ($80,652 vs $75,124 baseline).
* **Mechanism:** A7 maintains a fixed, conservative land ownership footprint to preserve cash for scheduled worker chores. At Step 288, cash reserves are sufficiently high ($15,013) that an immediate land parcel purchase allows additional high-yield crop compounding that matures before Day 27, yielding an immense terminal payout that A7's static route completely leaves on the table.

### Finding 2: Late-Mid Crop Acceleration (Action 1: `CROP_FOCUS` & Action 3: `MIXED_PRODUCTION`)
* **Inflection Points:** Steps 360, 504, 576.
* **Observed Deltas vs A7:**
  * Step 576 against `E8_DMITRII`: **+$608.00** (Best Action: 1 `CROP_FOCUS`).
  * Step 576 against `E2_A7`: **+$549.00** (Best Action: 1 `CROP_FOCUS`).
  * Step 504 against `E8_DMITRII`: **+$52.00** (Best Action: 3 `MIXED_PRODUCTION`).
  * Step 504 against `E2_A7`: **+$39.00** (Best Action: 1 `CROP_FOCUS`).
  * Step 360 against `E8_DMITRII`: **+$20.00** (Best Action: 1 `CROP_FOCUS`).
  * Step 360 against `E2_A7`: **+$16.00** (Best Action: 1 `CROP_FOCUS`).
* **Mechanism:** At step 576 (Day 24), A7 begins prematurely idling workers or performing suboptimal maintenance routines. Shifting priority to intensive crop maintenance and planting allows one final rapid crop yield before game close.

### Finding 3: Robustness of A7 in Pure Liquidation Windows
* At Step 72 (Day 3), Step 144 (Day 6), Step 648 (Day 27), and Step 696 (Day 29), Action 0 (`FOLLOW_A7`) was optimal in over 85% of states.
* Confirming the core thesis: **A7 is a formidable baseline, but possesses clear, discrete macroscopic blindspots in mid-game capital expansion and late crop cycle timing.**

---

## 4. Dataset Schema

Every target record written to `reports/strategic_targets.jsonl` contains:
```json
{
  "seed": 249635,
  "opponent_id": "E8_DMITRII",
  "seat": 0,
  "step": 288,
  "state_vector": [ ... 71 floats ... ],
  "action_mask": [ true, true, false, true, true, true, true, true, false, true ],
  "a7_cash": 75124.0,
  "action_values": {
    "0": 75124.0,
    "1": 75097.0,
    "2": -1e9,
    "3": 75097.0,
    "4": 74164.0,
    "5": 74944.0,
    "6": 73735.0,
    "7": 73435.0,
    "8": -1e9,
    "9": 80652.0
  },
  "best_action": 9,
  "best_cash": 80652.0,
  "best_delta": 5528.0,
  "second_best_action": 0,
  "second_best_cash": 75124.0,
  "gap": 5528.0
}
```

---

## 5. Next Steps: Search-Assisted Initialization (RLX2-F6 / RLX2-F7)

These target tuples provide direct supervised policy pre-training signals:
1. Cross-entropy pretraining of the `StrategicActor` on $\arg\max_a V(s_t, a)$ with advantage weighting $\Delta^*(s_t)$.
2. Value head calibration on the observed counterfactual return $V(s_t, a) / 100,000$.
3. Seamless handoff to PPO on-policy exploration starting from this informed, value-positive initialization.
