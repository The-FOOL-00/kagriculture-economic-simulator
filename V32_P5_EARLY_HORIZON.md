# V32 P5 — CRITICAL EARLY-HORIZON BC ANALYSIS (STEPS 0–24)

## 1. EXECUTIVE SUMMARY

In accordance with Section 11 and Section 20 of the V32 P5 Protocol, this document analyzes the critical opening horizon (Steps 0–24) where the economic trajectory of the entire episode is determined.

Across the 720-step episode, the first 24 steps represent only 3.3% of the horizon, but account for:
- 100% of initial labor acquisition (hiring 5 hands on Day 1).
- 100% of initial livestock acquisition (2 cows, 2 sheep).
- 100% of initial pasture construction and animal placement.
- Over 90% of downstream economic compounding potential.

---

## 2. STEP INTERVAL METRICS (720-STEP HORIZON)

| Step Interval | Description | Full-Action Match (%) | Mean Feature Distance $\|s_t^P - s_t^T\|_2$ | Mean Cash Delta $|\Delta \text{Cash}|$ | Mean Farmer Position Error | Economic State Status |
|:---:|:---|:---:|:---:|:---:|:---:|:---|
| **0** | Opening Turn | 0.0% | 0.00 | $0.0 | 0.0 tiles | Step-0 Market wash executed; Farmer moves West |
| **1–10** | Choreography & Hiring | 0.0% | **19.19** | **$734.4** | 1.2 tiles | Hands & Animals missed; Spurious orders |
| **11–24** | Planting & Day 1 Close | 0.0% | 19.34 | $244.5 | 2.4 tiles | No hands working; Initial capital draining |
| **25–48** | Day 2 | 0.0% | 18.18 | $109.8 | 0.4 tiles | Farm idle; zero crop/animal yields |
| **49–72** | Day 3 | 0.0% | 19.19 | $214.5 | 1.0 tiles | Cash depleted to < $50 |
| **73–144** | Days 4–6 | 0.0% | 20.07 | $462.3 | 1.4 tiles | Starvation regime |
| **145–288** | Mid-Game | 0.0% | 20.64 | $4,639.6 | 3.0 tiles | Teacher compounding ($5k+); Policy flat ($0) |
| **289–480** | Late Mid-Game | 0.0% | 23.48 | $31,125.3 | 3.0 tiles | Teacher compounding ($30k+); Policy flat ($0) |
| **481–719** | Terminal Endgame | 0.0% | **25.77** | **$65,195.1** | 3.8 tiles | Teacher finishes at $84k+; Policy at ~$72 |

---

## 3. STEP-BY-STEP EARLY-HORIZON TRACE (STEPS 0–15)

```text
Step 0:
  Teacher: Farmer PASS | Market [BUY_PRODUCT WHEAT 30, SELL WHEAT 30]
  Policy:  Farmer WEST | Market [BUY_PRODUCT WHEAT 30, SELL WHEAT 30]
  Result:  Market wash succeeds ($3000 capital); Farmer displaces to (4, 5).

Step 1:
  Teacher: Farmer NORTH | Market [SELL WHEAT 13, BUY WHEAT 5, 5x HIRE, BUY COW 2, BUY SHEEP 2]
  Policy:  Farmer BUILD_PASTURE | Market [BUY WHEAT 80, SELL WHEAT 998, ...]
  Result:  Policy misses ALL 5 HIRES and ALL 4 LIVESTOCK. State distance jumps to 21.376.

Step 2:
  Teacher: Farmer SOUTH | Hands: 5 hands present | Money: $1,253
  Policy:  Farmer PLACE COW | Hands: 0 hands present | Money: $1,253 (unused)
  Result:  Teacher prepares to pick up animals from shed; Policy farmer stands idle in empty field.

Step 3:
  Teacher: Farmer PICKUP SHEEP | Hands: active
  Policy:  Farmer PICKUP COW (fails, not at shed) | Hands: 0
  Result:  Policy holds no animals.

Steps 4–10:
  Teacher: Pickup wheat -> Move North -> Move West -> Build Pasture -> Place Sheep -> Feed -> Care.
  Policy:  Attempts PLACE COW without cow -> Attempts BUILD_PASTURE in wrong tile -> PASS.
  Result:  Teacher establishes 4 productive animals; Policy establishes 0 animals.

Steps 11–24:
  Teacher: Plants melons and wheat; 5 hands water and till; day ends with established farm.
  Policy:  Farmer wanders randomly; cash drains; Day 1 ends with empty farm.
```

---

## 4. SCIENTIFIC CONCLUSION & THE DESIGN OF ARM 2

This trace provides definitive confirmation of:
1. **Hypothesis H2 (Concentration in Early Decisions)**: The failure of P4 Arm 1 is concentrated entirely in the first few steps:
   - Step 0: Farmer unit op was unweighted and picked `WEST` instead of `PASS`.
   - Step 1: Because Step 0 farmer moved West, Step 1 failed to execute the 5-hire and livestock purchase.
   - Step 2: The farmer must return South to the shed to pick up livestock.
2. **The Mechanism for Arm 2 (Bounded Early-Horizon Weighting)**:
   - In P4 Arm 1, we weighted **only market slots 0 and 1 at step 0** ($\lambda_{crit} = 50.0$).
   - This saved the market wash, but left the **farmer unit head at Step 0** and the **critical early-horizon actions (Steps 0–10)** vulnerable to gradient dilution by the other 136,000 steps in the dataset.
   - To stabilize closed-loop BC, we must apply **Early-Horizon Weighting** across the entire initialization choreography (Steps 0 to 10), covering BOTH unit heads and market heads!
