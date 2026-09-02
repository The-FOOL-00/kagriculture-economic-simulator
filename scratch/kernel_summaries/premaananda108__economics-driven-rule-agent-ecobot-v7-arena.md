# Kernel: premaananda108__economics-driven-rule-agent-ecobot-v7-arena

## Notebook: economics-driven-rule-agent-ecobot-v7-arena.ipynb (15 cells)

### [Markdown Cell 0]
## Economics-Driven Rule Agent (EcoBot v7) + Arena
A fully reactive agent: every hiring, trading, planting, and dispatch decision is recomputed live from `obs` each turn through macroeconomic formulas and a real routing solver, rather than following a scripted turn-by-turn playbook. Season-length deadlines (crop growth windows, liquidation day) and a handful of tuned reserve/threshold constants are fixed game parameters the bot plans around — but which asset to buy, how much to sell, and who does which task are all derived fresh from the current turn's `obs` every time.

- **Day 0 Opener**: A one-time burst at hour 0 (fires only while the farm still has zero sheep in the shed and zero animals on the field) — 2 cows + 2 sheep + 12 melon seeds + 9 wheat seeds + 4 wheat feed, with 4 hired hands to kick-start output immediately.
- **Dynamic Macro-Planner**: Evaluates active shop demand blended with observed market-inventory drift (`max(demand, 0.6 × observed depletion)`), NPV-based purchase decisions capped by each asset's own remaining-season growth window, and projected feed costs. This runs fresh every single turn from live `obs` data — there's no day-based replanning cadence and no delta-triggered "replan on unlock/price move" logic; the same formulas are simply re-evaluated continuously.
- **One-Time 50% Herd Downsizing**: When an animal species is unprofitable for 2 consecutive days, its herd is downsized by 50%, strictly once per season — saves grain and labour while preserving a productive core for late-game shop openings.
- **Daily Field Dispatch — Real VRP, not a priority queue**: Once per day, the full task list (feed, water, harvest, plant, fertilize, care, build, weed) is solved via parallel cheapest insertion — each task lands on whichever unit's route absorbs it at the lowest travel cost. Urgency (starvation-risk feeding > placing newly-bought animals > routine feed/water > premium-crop harvest windows > priority planting > regular harvest/planting > care > fertilize/fertilizer pickup > build > expired-plant and weed clearing) only decides which task is *considered* first; it never overrides distance in deciding *who* does it. `PLANT`+`WATER` and `BUILD`+`PLACE` are bundled into atomic same-stop actions so a task is never left half-done, and the solver reuses a single shed detour per route for pickups wherever it can.
- **Capacity-Driven Land Expansion**: Unlocks quadrants in a fixed order (NE → SW → SE) purely when the macro plan is spatially capacity-constrained — tile utilization ≥80%, ≤2 empty tiles left, or planned pasture/coop counts exceeding what's physically available — and the budget covers the purchase plus cash reserve. No fixed calendar day gates the unlock; it's demand- and budget-driven only.
- **Phased Crop Conveyor**: Melon rush (plantable through day 18), Strawberry backbone (15–42 bushes depending on shop demand, planted through day 14), continuous Wheat filler from early game that becomes the sole planting priority for days 21–26 (last plantable day), and Day 28+ full liquidation with final shed evacuation forced from day 29 hour 15 onward.
- **Throttled Market Sales**: Sensitive goods (Melon, Wool, Strawberry, Wheat) are sold via binary-search-throttled quantities (`_throttled_qty`) capping same-turn price impact at 15% — so bulk unloading never crashes the price it's trying to capture. The throttle lifts entirely once liquidation begins on day 28.

### [Code Cell 1]
```python
!pip install -q -U kaggle-environments
```

### [Code Cell 2]
```python
%%writefile main.py
"""Kaggle Submission — Single File Bundle."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

# ---------------------------------------------------------------------------
# MODULE: constants.py
# ---------------------------------------------------------------------------

TOTAL_DAYS: int = 30
TURNS_PER_DAY: int = 24
PURCHASE_HOUR: int = 21   # Single daily window for BUY_SEED / BUY_ANIMAL / BUY_LAND
MAX_MARKET_ORDERS: int = 10
MAX_HANDS: int = 13
BOARD_SIZE: int = 10
I0: int = 10_000

# Interleaved by distance rings from shed junction across NW, NE, SW (total 18 pasture slots)
PASTURE_CLUSTER: list[tuple[int, int]] = [
    # Ring 0: Shed corner tiles (dist 0)
    (4, 4), (5, 4), (4, 5),
    # Ring 1: Immediate shed neighbors (dist 1)
    (4, 3), (3, 4), (5, 3), (6, 4), (3, 5), (4, 6),
    # Ring 2: Secondary cluster tiles (dist 2)
    (3, 3), (4, 2), (2, 4), (6, 3), (5, 2), (7, 4), (2, 5), (3, 6), (4, 7),
]
SHED_TILES: list[tuple[int, int]] = [(4, 4), (5, 4), (4, 5), (5, 5)]
SHED_TILES_SET: frozenset[tuple[int, int]] = frozenset(SHED_TILES)

# Furthest corner tiles in each quadrant from the shed — unconditionally excluded
# from planting and weed digging (see dispatch.py:build_task_catalog) so workers never
# make long detours across the entire map for low-value tiles.
BLOCKED_CLUSTER: list[tuple[int, int]] = [
    (0, 0), (1, 0), (0, 1),                                                     # NW far corner
    (BOARD_SIZE - 1, 0), (BOARD_SIZE - 2, 0), (BOARD_SIZE - 1, 1),               # NE far corner
    (0, BOARD_SIZE - 1), (1, BOARD_SIZE - 1), (0, BOARD_SIZE - 2),               # SW far corner
    (BOARD_SIZE - 1, BOARD_SIZE - 1), (BOARD_SIZE - 2, BOARD_SIZE - 1),          # SE far corner
    (BOARD_SIZE - 1, BOARD_SIZE - 2),
]
BLOCKED_CLUSTER_SET: frozenset[tuple[int, int]] = froz
```

### [Markdown Cell 3]
## Quick check (sanity check)

A short 48-turn run (2 in-game days) against `"random"`, to catch
obvious errors (exceptions, invalid action format) before running a full match.

### [Code Cell 4]
```python
import importlib
import main as agent_module
importlib.reload(agent_module)

from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 48}, debug=True)
env.run([agent_module.agent, "random"])

final = env.steps[-1]
for i, s in enumerate(final):
    print(f"Player {i}: reward={s.reward}, status={s.status}")
```

### [Markdown Cell 5]
## Full season (720 turns) vs `starter`

This is the main local test before submitting — a full season
(expectation: bank > 100,000).

### [Code Cell 6]
```python
env_full = make("kaggriculture", configuration={"episodeSteps": 720}, debug=True)
env_full.run(["main.py", "starter"])

final = env_full.steps[-1]
for i, s in enumerate(final):
    money = s["observation"]["farms"][i]["money"] if "observation" in s else None
    print(f"Player {i}: reward={s.reward}, status={s.status}, money={money}")
```

### [Markdown Cell 7]
## Day-by-day diagnostics (optional)

If the bank balance is lower than expected, it's useful to look at the
share of `PASS`/movement per day

### [Code Cell 8]
```python
from collections import Counter

replay = env_full.toJSON()
steps = replay["steps"]

for day in range(0, 30, 3):
    ops = Counter()
    for hour in range(24):
        idx = day * 24 + hour
        if idx >= len(steps):
            break
        act = steps[idx][0].get("action", {})
        acts = [act.get("farmer", ["PASS"])[0]] + [h[0] for h in act.get("hands", []) if h]
        ops.update(acts)
    total = sum(ops.values()) or 1
    passes = ops.get("PASS", 0)
    moves = sum(ops.get(d, 0) for d in ("NORTH", "SOUTH", "EAST", "WEST"))
    print(f"Day {day:2d}: total={total:3d} pass={passes:3d} ({passes/total:.0%}) move={moves:3d} ({moves/total:.0%})")
```

### [Markdown Cell 9]
## Multi-Game Evaluation (Arena Benchmark)
Parallel evaluation across multiple random seeds with symmetric pairings ($P_0$ vs $P_1$ and $P_1$ vs $P_0$) to verify consistency against baselines.

### [Code Cell 10]
```python
%%writefile arena.py
from __future__ import annotations

import argparse
import io
import json
import os
import random
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

EPISODE_STEPS: int = 720
REPLAYS_DIR: Path = Path("replays")
BUILTIN_AGENTS: frozenset[str] = frozenset({"random", "starter", "pass"})


@dataclass(frozen=True)
class MatchResult:
    seed: int
    bot_a: str
    bot_b: str
    reward_a: float
    reward_b: float
    error: str | None
    replay_path: str | None = None


def _resolve_bot(name: str) -> str:
    if name in BUILTIN_AGENTS:
        return name
    path = Path(name)
    if not path.is_file():
        raise FileNotFoundError(f"Bot script not found: {name}")
    return str(path.resolve())


def _bot_display_name(name: str) -> str:
    if name in BUILTIN_AGENTS:
        return name
    p = Path(name)
    return p.parent.name if p.stem == "main" and p.parent.name else p.stem


def _save_replay(env: object, bot_a: str, bot_b: str, seed: int, fmt: str) -> str:
    REPLAYS_DIR.mkdir(exist_ok=True)
    base_name = f"replay_{seed}_{_bot_display_name(bot_a)}_vs_{_bot_display_name(bot_b)}"
    saved: list[str] = []

    if fmt in ("html", "both"):
        html_path = REPLAYS_DIR / f"{base_name}.html"
        html_path.write_text(getattr(env, "render")(mode="html"), encoding="utf-8")
        saved.append(str(html_path))

    if fmt in ("json", "both"):
        json_path = REPLAYS_DIR / f"{base_name}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(getattr(env, "toJSON")(), f)
        saved.append(str(json_path))

    return ", ".join(saved)


def run_single_match(bot_a: str, bot_b: str, seed: int, save_format: str = "none") -> MatchResult:
    with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
        fro
```

### [Code Cell 11]
```python
!python arena.py --bots main.py starter --games 2 --workers 4 --seed 42
```

### [Markdown Cell 12]
## Preparing the submission

`main.py` is already in the notebook's working directory (written by cell 3) —
this is the submission's output file. For a single-file agent, no additional
packaging is needed.

### [Code Cell 13]
```python
import ast

with open("main.py") as f:
    tree = ast.parse(f.read())

has_agent = any(isinstance(n, ast.FunctionDef) and n.name == "agent" for n in tree.body)
assert has_agent, "main.py must define a top-level `agent` function"
print("OK: main.py defines `agent()` and parses cleanly.")
```

### [Code Cell 14]
```python
!find /kaggle/working -type d -name "__pycache__" -exec rm -rf {} +
!find /kaggle/working -type f -name "*.pyc" -delete
```

