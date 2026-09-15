# DEVELOPMENT INFORMATION TIMELINE: TEMPORAL EPISTEMOLOGY & ZERO-LEAKAGE PROTOCOL (POST-AUDIT 2.2)
## Strict Information Boundary Specification, Decision Horizons, and Anti-Leakage Invariants

**Governing Standard**: Audit 2.2 Final Evidence Base ([`AUDIT2_2_FINAL_EVIDENCE_BASE.md`](file:///c:/Users/Sundareswaran/Kagriculture/AUDIT2_2_FINAL_EVIDENCE_BASE.md))  
**Information Discipline**: Section 13 (Information Timeline) & Section 27 (No-Leakage Rule)  
**Date**: 2026-09-11  
**Status**: **AUTHORITATIVE IMMUTABLE PROTOCOL**

---

## 1. The Three-Tier Information Taxonomy

In reinforcement learning, heuristic search, and game-theoretic strategy design, **information leakage** (accessing future, hidden, or opponent private state) creates illusions of competence that collapse catastrophically in production.

For every decision at step $t \in [0, 719]$, state variables must be strictly categorized:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. KNOWN BEFORE DECISION                                                    │
│ Legally present in the agent's observation dictionary `obs` at step t.       │
│ Verified accessible via official Kaggle environment API. Zero extrapolation. │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 2. INFERRED                                                                 │
│ Statistically or causally estimated using ONLY history from steps 0 to t.   │
│ Examples: Bayesian posterior over remaining shops, opponent archetype       │
│ classification, expected yield dates. Zero future lookahead.                │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
┌──────────────────────────────────────▼──────────────────────────────────────┐
│ 3. UNKNOWN                                                                  │
│ Information physically non-existent or legally hidden at step t.            │
│ Examples: Future shop reveals (Days 3..24), future weed RNG draws,          │
│ opponent simultaneous current-turn orders, opponent private shed inventory. │
└─────────────────────────────────────────────────────────────────────────────┘
```

> [!CAUTION]
> **Zero-Tolerance Anti-Leakage Invariant**: Any agent or experimental script that references an `UNKNOWN` variable before its legal disclosure step is **strictly disqualified and marked RETRACTED**. No hindsight, no post-match replay parameter injection, no future shop peeking, and no PRNG stream cracking.

---

## 2. Simulator Observation Specification (`obs` at Step $t$)

Verified against `kaggle_environments/envs/kaggriculture/kaggriculture.py` and `sim.hpp`:

### 2.1 Legally Accessible Fields (`KNOWN`)

| Category | Observation Field | Datatype / Structure | Legal Content at Step $t$ |
| :--- | :--- | :--- | :--- |
| **Temporal** | `obs["step"]` | Integer ($0 \le t \le 719$) | Current game step |
| | `obs["day"]` | Integer ($0 \le d \le 29$) | Current game day ($d = \lfloor t / 24 \rfloor$) |
| | `obs["hour"]` | Integer ($0 \le h \le 23$) | Current game hour ($h = t \pmod{24}$) |
| | `obs["player"]` | Integer ($0$ or $1$) | Agent's seat index |
| **Own Farm** | `obs["farms"][player]["money"]` | Float | Current liquid bank balance |
| | `obs["farms"][player]["farmer"]` | `[x, y]` coordinates | Current farmer tile position |
| | `obs["farms"][player]["hands"]` | List of `[x, y]` | Current worker hand positions |
| | `obs["farms"][player]["hires_today"]` | Integer | Number of workers hired on current day |
| | `obs["farms"][player]["unlocked_quadrants"]` | List of strings | Land quadrants owned (e.g. `["NW", "NE"]`) |
| | `obs["farms"][player]["tiles"]` | 10x10 array of tile dicts | Physical crop/animal state on own farm |
| **Private State** | `obs["private"]["shed"]` | Dict `{product: count}` | Own shed commodity inventory ($\le 100$) |
| | `obs["private"]["seeds"]` | Dict `{crop: count}` | Own seed bag inventory |
| | `obs["private"]["inventories"]` | List of dicts per hand | Commodities currently carried by workers |
| **Public Opponent** | `obs["farms"][1-player]["money"]` | Float | Opponent current liquid cash |
| | `obs["farms"][1-player]["farmer"]` | `[x, y]` coordinates | Opponent farmer position |
| | `obs["farms"][1-player]["hands"]` | List of `[x, y]` | Opponent worker positions |
| | `obs["farms"][1-player]["hires_today"]` | Integer | Opponent worker hires today |
| | `obs["farms"][1-player]["unlocked_quadrants"]`| List of strings | Opponent land quadrants owned |
| | `obs["farms"][1-player]["tiles"]` | 10x10 array of tile dicts | Opponent physical farm layout |
| **Public Market** | `obs["market"]["inventory"]` | Dict `{product: count}` | Global open market commodity stock |
| | `obs["market"]["prices"]` | Dict `{product: price}` | Current clearing buy/sell prices |
| **Town Center** | `obs["town"]["unlocked_shops"]` | List of strings | Shops revealed up to current step ($\le 8$) |

---

### 2.2 Legally Prohibited / Non-Existent Fields (`UNKNOWN`)

| Prohibited Information | Physical Reality | Why It Is Strictly UNKNOWN |
| :--- | :--- | :--- |
| **Future Town Shops** | Shops 1–8 generated by PRNG at game start. | Hidden in simulator private state until dawn of days 3, 6, 9, 12, 15, 18, 21, 24. |
| **Opponent Private Shed** | Opponent inventory stored in opponent's private sub-dict. | NOT included in player's observation. Player can only see opponent's physical tiles. |
| **Opponent Seeds & Backpacks**| Opponent worker backpacks and seed inventory. | NOT included in player's observation. |
| **Current-Turn Opponent Orders**| Opponent market buy/sell and worker action lists. | Submitted simultaneously; executed after turn submission. |
| **Future Weed Spawns** | Weed locations sampled via PRNG each dawn. | Consumes random draws at dawn; unknown until realized. |
| **PRNG Internal State** | 64-bit random state in `sim.hpp`. | Unobservable; coupled to empty tile counts via weed spawning. |

---

## 3. Chronological 30-Day Decision Horizon Map

This timeline charts the exact step at which information transitions from `UNKNOWN` to `KNOWN` across the 720-step episode:

```
Step 0          Step 72         Step 144        Step 216        Step 264        Step 288        Step 712       Step 719
[Day 0]         [Day 3]         [Day 6]         [Day 9]         [Day 11]        [Day 12]        [Day 29]       [Game End]
   │               │               │               │               │               │               │               │
   ▼               ▼               ▼               ▼               ▼               ▼               ▼               ▼
Day 0 Opening   Shop 1 Reveal   Shop 2 Reveal   Shop 3 Reveal   Day 11 Planting Shop 4 Reveal   MC Terminal    Terminal Cash
No shops known  1/8 shops known 2/8 shops known 3/8 shops known Vacant tile     4/8 shops known Liquidation    Evaluation
Pure Prior      Bayesian Update 1st Pasture Buy 2nd Pasture Buy decision        1st Straw Harvest (Steps 712-718)
```

### Detailed Milestone Breakdown:

#### 1. Day 0 Dawn (Step 0) — Initial Capital Allocation
- **Known**: Starting cash $3,000.00; NW quadrant unlocked (25 tiles); farmer at (4,4); market prices at base equilibrium ($I_0 = 10,000$).
- **Inferred**: Prior probability distribution over all 8 town shops (Wheat 62.5%, Straw 50.0%, etc.).
- **Unknown**: All 8 town shops; opponent strategy; weed spawn locations.
- **Legal Strategic Behavior**: Commit to robust prior-dominant bedrock (Strawberry Bedrock + Wheat autarky). Zero conditioning on future shops.

#### 2. Day 3 Dawn (Step 72) — Shop 1 Reveal
- **Known**: Exactly 1 shop revealed (`unlocked_shops[0]`); opponent Day 0–2 land purchases and planting observable.
- **Inferred**: Posterior distribution over remaining 7 shops updated via Bayes' rule without replacement bias (sampled with replacement).
- **Unknown**: Shops 2–8 (87.5% of town demand); future market prices.

#### 3. Day 6 Dawn (Step 144) — Shop 2 Reveal & First Livestock Decision
- **Known**: Shops 1 and 2 revealed (`unlocked_shops[0..1]`); NE quadrant unlock status; opponent tile configurations.
- **Inferred**: First strong evidence of town demand orientation (e.g. presence of Yarn Store or Pet Cafe).
- **Unknown**: Shops 3–8; whether dairy (Milk) or wool (Sheep) will receive secondary shop support.
- **Legal Strategic Behavior**: Day 6 sheep pasture placement ($500 head, tile reserved).

#### 4. Day 9 Dawn (Step 216) — Shop 3 Reveal & Seed 50081 Liquidity Gate
- **Known**: Shops 1, 2, and 3 revealed (`unlocked_shops[0..2]`); cash on hand before dawn hiring.
- **Inferred**: Total cash required to execute planned sheep purchases at Step 217.
- **Unknown**: Shops 4–8; opponent market sell orders at Step 216.
- **Legal Strategic Behavior**: Enforce dynamic liquidity buffer ($\text{Cash} \ge \$1,000$) to prevent fatal sheep purchase failure observed on Seed 50081.

#### 5. Day 11 Dawn (Step 264) — Secondary Crop / Slack Exploitation Horizon
- **Known**: Shops 1, 2, and 3 revealed; physical tile vacancy map across NW, NE, SW quadrants.
- **Inferred**: Feasibility of inserting a fast secondary crop (e.g. Carrot or Tomato) without cannibalizing Day 12 strawberry harvest labor.
- **Unknown**: Shops 4–8 (62.5% of town shops are STILL UNKNOWN).
- **Legal Strategic Behavior**: If dynamic planting is attempted, it may condition **strictly on Shops 1–3**. Peeking at Shops 4–8 is an explicit leak.

#### 6. Day 12 Dawn (Step 288) — Shop 4 Reveal & First Strawberry Harvest Wave
- **Known**: Exactly 4 shops revealed (50.0% of total); first strawberry harvest ready (16–24 units).
- **Inferred**: Expected price impact of selling harvest to town shops vs dumping on market.
- **Unknown**: Shops 5–8; late-game market saturation.

#### 7. Day 24 Dawn (Step 576) — Final Shop Reveal (Shop 8)
- **Known**: All 8 town shops now completely revealed (`len(unlocked_shops) == 8`).
- **Inferred**: Exact deterministic capacity of remaining town demand until game end.
- **Unknown**: Opponent exact remaining private shed inventory.

#### 8. Day 29 Late Game (Steps 712–718) — Terminal Liquidation & Shop Closure
- **Known**: Exactly 1 to 7 steps remaining in the entire match; all farm crops harvested; market prices.
- **Inferred**: Optimal terminal worker actions (fertilizer pickup, final sales, market queueing).
- **Unknown**: Opponent final step market trades.
- **Legal Strategic Behavior**: Execute Monte Carlo terminal planning or JIT market queueing to convert every inventory unit to cash before Step 719.

---

## 4. Mandatory Anti-Leakage Protocol Specifications & Verification Checklist

Before any experimental candidate is accepted into the development registry, it must pass this verification checklist, which is programmatically executed via the test harness [`scratch/verify_agent_zero_leakage.py`](file:///c:/Users/Sundareswaran/Kagriculture/scratch/verify_agent_zero_leakage.py):

| Verification Check | Target Inspection | Verification Method | Failure Penalty |
| :--- | :--- | :--- | :--- |
| **Leak Check 1: Future Shops** | Inspect all agent references to `town["unlocked_shops"]`. | Assert `len(unlocked_shops) <= (step // 72)`. Assert no access to simulator's private shop array. | **IMMEDIATE DISQUALIFICATION** |
| **Leak Check 2: Opponent Private** | Inspect all agent references to `obs`. | Assert zero reads from `obs["private"]` belonging to opponent. Only own private shed/seeds read. | **IMMEDIATE DISQUALIFICATION** |
| **Leak Check 3: PRNG Inspection** | Inspect imports and random state queries. | Assert zero seeding or internal state querying of C++ `sim.hpp` or Python `random`. | **IMMEDIATE DISQUALIFICATION** |
| **Leak Check 4: Replay Hindsight** | Check agent initialization arguments. | Assert zero seed-indexed lookup tables, pre-recorded shop mappings, or match telemetry caches. | **IMMEDIATE DISQUALIFICATION** |
| **Leak Check 5: Terminal Leakage** | Inspect end-of-game logic. | Assert zero score prediction peeking or future step counterfactuals that evaluate future game steps. | **IMMEDIATE DISQUALIFICATION** |

> [!CAUTION]
> **Legal Enforcement Rule**: These constraints are strictly enforced in Kaggle competition execution containers. Any strategy relying on state outside `obs` will fail instantly in competition. Runtime verification via `scratch/verify_agent_zero_leakage.py` is mandatory before any experiment is logged to `DEVELOPMENT_EXPERIMENT_REGISTRY.md`.
