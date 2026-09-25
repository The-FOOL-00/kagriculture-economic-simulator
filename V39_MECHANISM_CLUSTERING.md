# V39 Mechanism Clustering — Unification of Failure Modes

## 1. Principles of Mechanism Unification
A foundational rule of the V39 program is:
> **Do NOT create one patch per episode. Research the shared economic mechanism, not the individual game.**

Across the entire live competition record of V35, the 6 failure states collapse into **three distinct economic clusters**.

---

## 2. Cluster Breakdown & Taxonomy

```text
               TOTAL V35 FAILURES (N = 6)
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
   CLUSTER 1         CLUSTER 2         CLUSTER 3
Terminal Liquidation    Macro Land      Seat Priority
  Omission & Delay      Pacing (SE)       Parity
   (4 episodes)        (1 episode)      (1 episode)
     [66.7%]             [16.7%]          [16.7%]
         │                 │                 │
         │                 │                 ▼
         │                 ▼            Non-actionable
         │            Broad macro      tiebreaker limit
         │             (Too risky)
         ▼
   SINGLE UNIFIED
    INTERVENTION
(FLUSH_694 + SUPPRESS)
```

---

## 3. Deep Cluster Characterization

### Cluster 1: Terminal Liquidation Order & Delay (Episodes `113183263`, `113171441`, `113164394`, `113166778`)
- **Core Mechanism**:
  A7 / V35's static route tape schedules a partial sell at Step 694 (`WHEAT`, `CARROT`, `EGG`) and postpones selling `MILK`, `STRAWBERRY`, and `WOOL` until Step 696 or 698.
- **Evidence of Unification**:
  In **all 4 episodes**, V35 had $\ge 4$ Milk, $\ge 15$ Strawberries, and $\ge 2$ Wool physically resting in its shed at Step 694. In all 4 episodes, the opponent executed a complete dump at Step 694. When V35 sold 2 turns later, it suffered $800 to $1,500 in price slippage.
- **Unification Power**:
  A single, universal deterministic rule (`FLUSH_694`) addresses all 4 episodes simultaneously with zero bespoke logic per episode.

### Cluster 2: Macro Land Pacing (Episode `113177277`)
- **Core Mechanism**:
  Opponent (`Adhiraj Jagtap`) purchased Southeast land at Step 267 instead of Step 290.
- **Assessment**:
  Isolated single-episode outlier (1/29 games). Forcing early SE land acquisition across all seeds harms V35's liquidity buffer on low-capital boards, risking widespread casualties. This cluster is explicitly excluded from local patching.

### Cluster 3: Seat Priority Parity (Episode `113153701`)
- **Core Mechanism**:
  Self-play validation on Seed 0.
- **Assessment**:
  Seat 1 market order priority in simultaneous execution. Inherent platform characteristic.
