# V40 Repository and Architecture Audit: Forensic Analysis of Previous RL Programs

**Document ID:** `research/v40/reports/REPOSITORY_AUDIT.md`  
**Date:** 2026-09-25  
**Candidate:** `research/v40/`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Executive Summary

This repository audit provides the foundational forensic analysis required before designing and executing the V40 Scalable Hierarchical Reinforcement Learning + Self-Play Research Program.

We examine the mechanics and empirical results of prior RL campaigns in this codebase—specifically **V32 RL-X2** (tabula-rasa / search-augmented macro RL) and **V38** (heuristic-guided bounded residual PPO)—as well as the verified production incumbent **V35** (`candidates/v35_a7_opening/main.py`) and the quarantined research candidate **V39** (`candidates/v39_live_targeted/main.py`).

The central conclusion of this audit is that RL did not fail because the game cannot be learned; RL failed because previous implementations were crippled by:
1. **Extremely Low Simulation Throughput:** 40–135 SPS on sequential `kaggle_environments` instances, limiting training to ~28,800 total steps (40 games).
2. **Pathological Action Space Design:** Action 0 (`TRUST_HEURISTIC`) was an always-safe no-op that allowed PPO policy gradients to rapidly collapse exploration to zero.
3. **Absence of Recurrent Temporal State:** Pure feedforward MLPs were incapable of tracking multi-day crop maturation horizons, price momentum, or opponent liquidation patterns.
4. **Lack of Dynamic Population Self-Play:** Models trained against only 1–2 static frozen opponents without league diversity or adversarial pressure.

---

## 2. Answers to the 12 Mandatory Audit Questions

### Q1: What exactly did RLX2/V38 train?
- **V32 RL-X2:** Trained a feedforward MLP actor-critic (128×128 hidden layers) using PPO on a 71-dimensional economic observation vector to select among 10 discrete macro options over a horizon $H=4$ steps. However, macro options only injected market orders without corresponding physical chore routines to build structures or plant crops. Without proper expert initialization, unguided stochastic exploration generated deviations on ~80% of steps, causing cash to collapse from ~$120k down to ~$1.2k.
- **V38:** Implemented a two-phase residual approach:
  1. *Behavioral Cloning (BC) warm-start:* Trained on 128 counterfactual decision states (achieving 87.5% validation accuracy) on a 64-dim feature vector and 11 discrete macro actions.
  2. *Bounded Residual PPO fine-tuning:* Trained for only 10 iterations (40 full-game rollouts against 2 static bots: `E2_A7` and `E8_DMITRII`).

### Q2: What was the action space?
- **V32 RL-X2 (10 discrete options):**
  - `0: FOLLOW_A7` (delegate tick control directly to A7's expert routine)
  - `1: CROP_FOCUS`, `2: LIVESTOCK_FOCUS`, `3: MIXED_PRODUCTION`, `4: HARVEST_PRIORITY`
  - `5: PRESERVE_CASH`, `6: OPPORTUNISTIC_SELL`, `7: SELECTIVE_PREEMPT`, `8: LIQUIDATE`, `9: EXPAND_LAND`
- **V38 (11 discrete options):**
  - `0: TRUST_HEURISTIC` (unconditionally legal default to the baseline heuristic)
  - `1: EXPAND_LAND`
  - `2: HIRE_WORKER`
  - `3: ANIMAL_EXPANSION (Cow)`
  - `4: CROP_EXPANSION (Melon)`
  - `5: SHOP_SUPPLY`
  - `6: SELL_INVENTORY`
  - `7: HOLD_INVENTORY`
  - `8: MARKET_OPPORTUNITY`
  - `9: LIQUIDITY_PROTECT`
  - `10: RECOVERY`
  *Crucial Flaw:* In both systems, Action 0 was unconditionally legal and mapped directly to executing the expert baseline.

### Q3: What was the observation space?
- **V32 RL-X2:** 71-dimensional structured macroeconomic vector:
  - 19 Capital & Macro (cash, cash runway, liquid inventory value, committed expenditures, cash-at-risk)
  - 12 Labor (active worker counts, idle counts, wage burdens, utilization rates)
  - 16 Crops & Livestock (planted crop stages, animal counts, shed occupancy, feeding state)
  - 8 Land & Market (owned tiles, free tiles, crop prices, recent trade volume)
  - 8 Opponent Observables (visible livestock, visible crops, visible workers, trade activity)
  - 4 Temporal (current step, day progress, harvest distance, terminal proximity)
  - 4 Risk (insolvency risk, shed overflow risk, feeding deadline risk)
- **V38:** 64-dimensional economic feature vector:
  - Normalized liquid cash, wage runway days, estimated net worth, liquidation values
  - Shed inventory counts for all 9 commodities, spot market prices, and price deltas
  - Unlocked quadrants, worker counts, empty/weed tiles, days of feed runway
  *Compliance Note:* Both representations strictly used legally observable information and avoided opponent private inventories, hidden future market prices, or seed identity.

### Q4: What was the reward?
- **V32 RL-X2:** A7-relative reward (R1) based on terminal margin delta:
  $$r_T = \frac{C_T(\text{agent}) - C_T(\text{A7})}{10,000.0}$$
- **V38:** Opponent-relative terminal differential margin:
  $$r_T = \frac{C_T(\text{player}) - C_T(\text{opponent})}{10,000.0}$$
  assigned strictly at step $T=719$, with $r_t = 0.0$ for all intermediate steps $t < 719$.

### Q5: How often did the policy act?
- Both architectures operated on fixed macro intervals of $H = 4$ simulation ticks (180 decisions per 720-step game). In V38, actions could persist for up to 8 ticks under specific safety constraints, but the model made decisions strictly on macro ticks ($step \equiv 0 \pmod 4$).

### Q6: How many environments were parallelized?
- **V32 RL-X2:** Benchmark suite profiled up to 12 parallel processes, but training rollouts were collected across 1 to 4 workers.
- **V38:** **1 worker only** (completely sequential single-threaded execution inside `train_ppo.py`).

### Q7: What simulator throughput was achieved?
- Single-worker official `kaggle_environments` achieved **~40–48 SPS** (~15–18 seconds per 720-step episode).
- In V32 multiprocessing benchmarks (`rlx2_f0_benchmark.json`), throughput plateaued at **~454 SPS** across 8–12 workers due to Python process creation, IPC serialization, and `kaggle_environments` schema validation.
- In V38 sequential training, throughput was ~120 SPS (running 4 episodes in ~23 seconds).

### Q8: What prevented larger-scale training?
1. **Environment Stepping Overhead:** Calling `kaggle_environments.step([act0, act1])` incurred heavy JSON schema validation, stdout/stderr redirection, and state history cloning. Running 10 million steps at 45 SPS would take >61 hours.
2. **Microscopic Training Budgets:** Due to slow simulation, V38 was trained for only 10 iterations × 4 episodes = 40 episodes = **28,800 environment steps**. In modern deep RL, 28k steps is trivial.
3. **No Recurrent State Memory:** Feedforward networks lacked temporal memory of past actions, price trends, and crop schedules, forcing the system to rely on hand-crafted heuristic fallbacks.
4. **Premature Convergence to Heuristic:** Because `TRUST_HEURISTIC` was always available and any uncoordinated exploration caused small cash drops, PPO rapidly converged to 100% heuristic selection within 6 iterations, causing training to terminate.

### Q9: Why did PPO converge to `TRUST_HEURISTIC` / no-op behaviour?
- In Kagriculture, the deterministic heuristic (V35 25/25 opening + A7 chore chassis) already operates near the empirical efficiency frontier of physical chore coordination (~$100k terminal cash).
- Any exploratory macro deviation (e.g., buying a cow or buying land early) drains liquidity and alters tile states. Without a physical executor capable of dynamically tending the new assets, the deviation resulted in missed chore cycles, bounced seed orders, or idle workers.
- Because PPO evaluates advantage against the trajectory distribution, deviations that reduced cash yielded negative advantage values relative to `TRUST_HEURISTIC`. Policy gradient updates exponentially penalized non-zero actions, driving the probability of `TRUST_HEURISTIC` to 1.0. Once $P(\text{TRUST\_HEURISTIC}) \to 1.0$, policy entropy collapsed, gradients evaporated, and learning stopped.

### Q10: Which parts of the earlier RL architecture should be retained?
- **Observation Feature Vector:** The clean extraction of normalized economic state, cash runway, inventories, and market prices (`candidates/v32_rlx2/state.py` and `candidates/v38_heuristic_ppo/state_features.py`).
- **Hierarchical Macro-Action Framing:** Decoupling high-level economic decisions from low-level physical pathfinding and tile interactions.
- **Fail-Closed Safety Guards:** Liquidity buffer enforcement ensuring the agent never exhausts its working capital for daily wages or basic seed planting.
- **Opponent League Pool:** Standard tournament evaluation opponents (`E2_A7`, `E1_V22R1`, `E8_DMITRII`, `V54`, `SYN_AGG`).

### Q11: Which parts must be discarded?
- **The Trivial `TRUST_HEURISTIC` No-Op Action:** The policy must not be offered a single action that simply executes the entire baseline agent. It must make genuine macro choices across economic dimensions (e.g. crop allocation, livestock volume, expansion timing, market timing).
- **Single-Threaded Sequential `kaggle_environments` Stepping:** The standard `kaggle_environments` wrapper with its stdout redirection and JSON schema validation is far too slow for serious RL.
- **Pure Feedforward MLPs:** Must be replaced with a recurrent temporal encoder (LSTM / GRU) to capture long-horizon state history.
- **Sparse Terminal-Only Reward:** Must be augmented with meaningful macroeconomic advantage estimation, value decomposition, or potential-based shaping that aligns with terminal match outcome.
- **Static Opponent Training:** Must be replaced with population-based self-play and snapshot league sampling.

### Q12: What can be reused without introducing leakage?
- Feature extraction functions that operate strictly on `observation` at turn $t$.
- The frozen opponent definitions in `scripts/v32_common.py` and `candidates/v32_rlx2/opponents.py`.
- Safe seed ranges (`V32_TRAIN`: 249635–249674, `V32_DEV`: 249675–249694) while strictly adhering to the non-negotiable quarantine on protected holdouts (`214200–214249`, `340090–340199`, `249695–249734`).

---

## 3. High-Throughput Engine Discovery

Profiling reveals that `kaggle_environments.step()` spends:
- **30.8%** of time on deep-copying observations.
- **48.6%** of time on `kaggle_environments` framework overhead (schema validation, string buffers, logging).
- Only **20.6%** on actual simulation and agent logic.

By creating a direct execution harness (`FastKagricultureEnv`) that invokes the official `kaggriculture.py` interpreter directly:
- Single-worker throughput jumps from **40.1 SPS** to **571.8 SPS** (**14.2× speedup**).
- Across 8 CPU workers, projected throughput exceeds **4,500+ SPS**.
- This transforms a 10-million-step training run from **58+ hours down to ~35 minutes**, making large-scale hierarchical recurrent RL computationally feasible.
