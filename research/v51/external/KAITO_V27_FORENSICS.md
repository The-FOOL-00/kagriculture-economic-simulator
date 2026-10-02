# Forensic Analysis: Kaito Fukami — 25/27 Strict-Future | v27 Midgame Meta Reset

**Source:** Kaggle Notebook `kaitofukami/25-27-strict-future-v27-midgame-meta-reset`  
**Author:** Kaito Fukami  
**Date:** August 2026  
**Reported Metric:** 3090.1 (Internal Offline Strict-Future Replay Metric; 25/27 Top-30 Replays)  
**Live Ladder Status:** Public baseline iteration pre-v48 (3009.0)  
**Target Environment:** `kaggle-environments==1.32.7`  
**License/Attribution:** Apache-2.0 / MIT (Retained upstream notices)

---

## 1. Strategy Architecture Overview

Kaito Fukami's v27 "Midgame Meta Reset" was designed to address the brittleness of open-loop fixed-route action replay against dynamic opponents. In pure open-loop play, an agent follows a static action tape derived from historical winning trajectories. When dynamic factors—such as opponent crop saturation, market price crashes, or random weed spawning—diverge from the expected replay state, fixed tapes fail.

v27 attempted a dual-layer solution:
1. **Macro Layer (Midgame Meta Reset):** Periodically evaluate observable market and rival signatures at discrete checkpoint steps ($t \in \{48, 144, 288\}$) to switch between candidate route tapes.
2. **Micro Layer (Local Action Repair):** Provide an in-place state machine (`_weed_repair_action` / `wrap_weed_repair`) that catches physical tile blockers (e.g. `WEED` on an intended `PLANT` or `BUILD_PASTURE` tile), executes a corrective action (`DIG`), and resumes tape execution through a delayed replay buffer.

---

## 2. The Exact Action-Repair Mechanism (`wrap_weed_repair`)

The core micro-repair implementation in v27 (packaged into `scripts.v22_weed_repair`) is an identity-free decorator wrapping any deterministic action policy.

```python
def wrap_weed_repair(policy, base_actions, *, replay_steps=8, stop_on_match=False):
    replay_steps = max(0, int(replay_steps))
    states = {0: {}, 1: {}}
    telemetry = {
        "games": 0,
        "collisions": 0,
        "dig_actions": 0,
        "retry_actions": 0,
        "replay_actions": 0,
        "early_matches": 0,
        "expired_transactions": 0,
        "by_operation": {},
    }
```

### State Machine Lifecycle per Actor:

1. **Trigger Condition:**
   - Evaluated for each unit: `farmer` (index 0) and `hands` (indices $1..N$).
   - Trigger fires if and only if:
     $$\text{intended}[0] \in \{\text{'BUILD\_PASTURE'}, \text{'PLANT'}\} \quad \land \quad \text{tile}(x, y).\text{kind} == \text{'WEED'}$$
   - The actor cannot already have an active transaction in flight (`actor not in active`).

2. **Collision Turn ($t_{\text{collision}}$):**
   - The transaction is opened:
     ```python
     active[actor] = {
         "start": step,
         "intended": copy.deepcopy(intended),
     }
     ```
   - The intended action is replaced with:
     ```python
     unit_actions[index] = ["DIG"]
     ```
   - Telemetry increments: `collisions += 1`, `dig_actions += 1`.

3. **Retry Turn ($\text{age} == 1$, i.e. $t_{\text{collision}} + 1$):**
   - The tile is now cleared (assuming `DIG` succeeds).
   - The intended original action is replayed:
     ```python
     unit_actions[index] = copy.deepcopy(transaction["intended"])
     ```
   - Telemetry increments: `retry_actions += 1`.

4. **Replay Phase ($2 \le \text{age} \le 1 + \text{replay\_steps}$):**
   - Because the actor spent turn $t_{\text{collision}}$ digging, its schedule is offset by 1 turn relative to the static tape.
   - For the next `replay_steps` turns (default 8 turns), the actor executes the action scheduled for step $t - 1$:
     ```python
     previous = _trace_action(base_actions, step - 1, actor)
     unit_actions[index] = previous
     ```
   - **Early Exit (`stop_on_match=True`):** If the delayed action matches what the tape naturally prescribed for turn $t$, the transaction terminates early (`active.pop(actor)`).
   - Telemetry increments: `replay_actions += 1`.

5. **Expiration ($\text{age} > 1 + \text{replay\_steps}$):**
   - After $1 + \text{replay\_steps}$ turns, the transaction closes and the actor snaps back to the base policy's unshifted schedule.
   - Telemetry increments: `expired_transactions += 1`.

---

## 3. Structural Properties of the Repair Mechanism

| Property | Implementation Fact | Consequence / Governance Note |
| :--- | :--- | :--- |
| **Actor Locality** | Per-actor state tracking (`active[actor]`) | **Strictly Local.** Actor A's repair never alters Actor B's action. |
| **Market Decoupling** | `action["market"]` is untouched by the wrapper | **100% Decoupled.** Zero interference with order queues or pricing. |
| **Route Decoupling** | Does not alter route ID or switch branches | Pure tactical intervention within the currently active route tape. |
| **Supported Blockers** | Exclusively `tile.get("kind") == "WEED"` | Does NOT handle unit occupancy, cash starvation, or tile locks. |
| **Target Operations** | Exclusively `PLANT` and `BUILD_PASTURE` | Ignores `WATER`, `HARVEST`, `FERTILIZE`, or `MOVE`. |

---

## 4. Interaction with Midgame Meta Reset (The Macro Layer)

In v27, the macro layer attempted to re-evaluate route choice at step 48 and 144:
- In offline replay evaluation, Kaito reported an impressive 3090.1 score across 25/27 test cases.
- **Local Reproduction Fact (V33 Audit):** Independent reproduction in our V33 research showed that forced midgame route switching at $t \ge 144$ dropped win rate to **33.3%** (-$8,433 downside tail). Capital allocations made prior to step 144 (coops, tilled plots, worker positions) become completely mismatched with the new route's expectations.
- As a result, in later versions (v43, v48), Kaito Fukami largely **abandoned midgame route switching**, replacing it with the static Step-144 Shop Router (`EXP240` vs `V39`), while **retaining `scripts.v22_weed_repair`** in the core planner.

---

## 5. Causal Assessment for V51

1. **Safety:** The `wrap_weed_repair` state machine is mathematically fail-safe for unaffected turns. If no weed collision occurs, it returns `align_hands(policy(obs))` identically.
2. **Key Question for V49:** Does V49's 2945 chassis ever experience naturally occurring weed collisions on `PLANT` or `BUILD_PASTURE` actions?
   - If YES: A weed repair wrapper can preserve crop/pasture schedules and prevent idle turns.
   - If NO: The mechanism will be completely inert (0 activations, 0 delta).
