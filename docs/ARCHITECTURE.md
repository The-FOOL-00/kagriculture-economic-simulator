# Architecture & Repository Audit: Kaggriculture Engine

## 1. System Overview & Current Architecture

Kaggriculture is a 30-day (720 turns, 24 turns/day) two-player imperfect-information economic simulation game. The winner is the player with the highest cash balance at step 720.

The repository currently contains:
- `main.py`: Standalone submission agent containing full self-contained logic (inlined models, pathfinding, farm state representation, scheduler, and market manager).
- `config.py`: Game constants, asset costs, crop growth cycles, shop consumption tables, market pricing curves, and land prices.
- `farm_state.py`: Class parsing raw observation dictionaries, classifying tiles (plants, weeds, structures, animals), and computing inventory counts.
- `pathfinding.py`: BFS-based spatial pathfinding over unlocked grid tiles (10x10 max, 4 quadrants NW/NE/SW/SE) and Manhattan distance heuristics.
- `replay_analyzer.py`: Replay downloader and metric parser (wealth trajectory, planting history, market sales).
- `arena.py`: Basic 1v1 execution utility using `kaggle_environments.make("kaggriculture")`.

---

## 2. Decision Pipeline & Core Subsystems

```
Raw Environment Observation (JSON)
           │
           ▼
     [ FarmState ]  <── Analyzes Tiles, Inventories, Animals, Crop Stages
           │
     ┌─────┴─────────────────────────┐
     ▼                               ▼
[ Market / Economy Manager ]   [ Worker Scheduler ]
  - Day-0 Opening Strategy       - Daily Labor Sizing (fib_hire_cost)
  - Land Expansion Schedule      - Chore Generation & Prioritization
  - Seed / Asset Purchasing      - Worker Tile Assignment & Routing
  - Town Frontrun Selling        - Shed Pickups & Deposits
     │                               │
     └─────────────┬─────────────────┘
                   ▼
     Formatted Step Action Dict:
     { "farmer": [...], "hands": [...], "market": [...] }
```

---

## 3. Major Heuristics & Historical Discoveries

### Proven Mechanisms (Must Preserve)
1. **Labor Liquidity Reserve**: Keeping a strict $30–$35 cash buffer so the daily farm hand hiring routine (Fibonacci wage curve: $1, $1, $2, $3, $5, $8...) never starves from mid-season purchases.
2. **Town Scarcity Frontrunning**: Town shops drain market inventory on periodic intervals (`step % 4 == 0`), creating immediate price peaks. Queuing sell orders right after these consumption ticks maximizes dollar yield per unit sold.
3. **Golden Multi-Quadrant Land Layout**: Unlocking NE Land ($1,000) on Day 0 or early game allows scaling from 25 tiles to 50–75 tiles without mid-game crop overcrowding.
4. **BFS Navigation & Multi-Worker Pathing**: Workers step towards target chores via shortest paths on unlocked grid tiles.

### Fragile Assumptions & Weaknesses in Past Iterations
1. **Hardcoded Day-0 Action Sequences**: Past iterations locked in fixed Day-0 purchases (e.g. fixed 45 Melons or fixed 3 Cows + 1 Sheep) rather than evaluating dynamic market initializations or shop compositions.
2. **Greedy Chore Assignment**: Workers currently grab the highest priority chore regardless of worker-chore spatial clustering, sometimes resulting in path cross-over.
3. **Static Selling Thresholds**: Selling logic relied on simple `day >= 26 or shed_items >= 20` rather than calculating dynamic price elasticity, expected future town demand, and price impact of batch selling.
4. **Lack of Rolling Horizon Search**: Decisions were 100% reactive step-to-step without simulating future game states or computing risk-adjusted win probabilities against opponent trajectory.

---

## 4. Proposed Modular Migration Path

```
engine/
├── world_model.py         # Complete environment state tracking & transition simulation
├── market_model.py        # Price impact curves, inventory pressure, town consumption forecast
├── economic_evaluator.py  # Net Present Value (NPV) & ROI solver for all assets & crops
├── opponent_model.py      # Opponent farm radar, harvest timing predictor, strategy classifier
├── macro_planner.py       # Rolling-horizon beam search / macro-action optimizer
├── labor_scheduler.py     # Deadline-aware multi-worker Hungarian/spatial assignment
└── unified_agent.py       # Integrated agent logic & single-file compiler for main.py
```

---

## 5. Benchmarking & Experimental Standard
- **Golden Control**: `agents/golden_v1.py` (Apex Grandmaster v3 - $48,213 average baseline).
- **Harness**: `benchmark_harness.py` supporting deterministic seed batches (10, 50, 100, 500 seeds) with detailed statistical output (Win Rate, Mean Reward, Margin, Percentiles).
- **Strict Progression Gate**: Any candidate must demonstrably outperform `golden_v1.py` in win-rate and mean reward over statistically rigorous seed sets before replacing the active control.
