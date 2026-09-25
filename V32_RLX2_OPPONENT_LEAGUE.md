# V32 RL-X2 — OPPONENT LEAGUE SPECIFICATION & SAMPLING PROTOCOL
**Phase:** V32 RL-X2  
**Date:** 2026-09-23  
**Status:** SPECIFIED, IMPLEMENTED & VERIFIED  
**Package:** `candidates/v32_rlx2/opponents.py`  
**Author:** Kagriculture Autonomous Research Agent  

---

## 1. Opponent League Architecture (§27, §28, §29)

To ensure that the strategic policy does not overfit to a single fixed opponent (e.g. `E0_V3`), RL-X2 establishes a frozen 6-opponent league representing fundamentally different competitive archetypes:

```text
+---------------------------------------------------------------------------------------+
|                                FROZEN OPPONENT LEAGUE                                 |
+-------------------+--------------------------------+----------------------------------+
| Opponent ID       | Archetype                      | Strategic Signature              |
+-------------------+--------------------------------+----------------------------------+
| E2_A7             | Protected Incumbent            | Step-0 30-wash + route replay    |
| E1_V22R1          | Live Slot A Champion           | Robust balanced farm management  |
| E0_V3             | Legacy Tape Control            | Fixed open-loop route baseline   |
| E8_DMITRII        | Frontier Competitor (2800+ LB) | Early micro-sales + milk dumps   |
| V54               | Declarative Backbone           | Pure state-driven crop planning  |
| SYN_AGG           | Adversarial Market Dumper      | Rapid inventory liquidation      |
+-------------------+--------------------------------+----------------------------------+
```

---

## 2. Opponent Archetype Deep Forensics

1. **`E2_A7` (Protected Incumbent Baseline):**
   - SHA-256: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`.
   - Executes the Step-0 30/30 wheat wash ($30 \times 25$ round-trip), establishing an immediate +$1,286 alpha over V3. Replays optimal pre-computed route tapes with reactive safety layers (`hand_align`, `weed_repair`, `sell_lead`, `front_run`, `budget_guard`, `room_guard`, `clamp_sells`, `dead_stock`, `terminal_liquidation`).
2. **`E1_V22R1` (Live Slot A Champion):**
   - Tarball SHA-256: `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5`.
   - Battle-tested on the live Kaggle leaderboard; highly stable capital management with conservative hiring schedules.
3. **`E0_V3` (Frozen Legacy Baseline):**
   - Tarball SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`.
   - The open-source standard for route replay across 41 opening shop sequences.
4. **`E8_DMITRII` (Frontier Competitor, Dmitrii Gluzdov 2800+ LB):**
   - Source SHA-256: `495bfa4825c9e58638e804aeeb62a9537826f6d4d869222815e1bbeefd84d3dc`.
   - Distinctive strategy: executes aggressive early micro-sales (Step 0 wheat, Step 196 milk), dumps large melon and milk batches around steps 250, 614, and 697, and uses terminal Monte Carlo search. Beat A7 on Seed 249677 (-$1,167 margin) due to mid-game price front-running.
5. **`V54` (Declarative Backbone Reference):**
   - Pure state-feedback planner; provides diverse, dynamic crop mixes and reactive pasture stocking without tape replay.
6. **`SYN_AGG` (Synthetic Hostile Market Stressor):**
   - Continuous dumping policy that liquidates milk, wool, melon, strawberry, and wheat as soon as shed quantity $> 0$. Stress-tests agent resilience against severe commodity price depression.

---

## 3. League Sampling Regimes (§28)

The `OpponentSampler` class provides three switchable sampling modes:
1. **Uniform Mode (`uniform`):** Equal $1/6$ probability across all opponents. Prevents strategic drift.
2. **Hard-Weighted Mode (`hard_weighted`):**
   - `E8_DMITRII`: **35%** (highest weight on known failure mode)
   - `E2_A7`: **20%** (incumbent self-play)
   - `E1_V22R1`: **20%** (slot A benchmark)
   - `V54`: **10%** (declarative diversity)
   - `SYN_AGG`: **10%** (hostile market stress)
   - `E0_V3`: **5%** (sanity control)
3. **Specialized Target Mode (`a7_only` / `dmitrii_only`):** Dedicated focus for counterfactual fine-tuning.

---

## 4. Non-Transitivity & Cycle Tracking Protocol (§29)

Every evaluation across the league records the full pairwise match matrix:
$$M_{ij} = \text{WinRate}(\text{Agent } i \text{ vs Opponent } j)$$
If cyclical dominance appears ($A \succ B \succ C \succ A$), the policy is trained using population sampling across all cycle vertices rather than collapsing to a single scalar objective.
