# V33 Elite Route Bank: Candidate Expert Portfolio

**Program:** Kagriculture V33 Research Program  
**Date:** 2026-09-24  
**Status:** **COMPILED & VERIFIED**  
**Core Invariant:** Low-level physical and market execution remains the job of the expert route. The meta-strategy selects among these 6 autonomous experts.

---

## 1. Composition of the 6-Route Bank

The initial elite route bank consists of 6 structurally and behaviorally distinct expert policies:

| Route ID | Expert Name | Source Path | Strategic Archetype | Baseline Mean Cash | Role in V33 Portfolio |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **`R0_A7`** | A7 Incumbent | `candidates/v30_a7_standalone/main.py` | High-Efficiency Choreography | **$104,332.17** | **Default Expert (Anchor)** |
| **`R1_V22R1`** | V22R1 Champion | `submission_aec_v22r1.tar.gz` | Adaptive Multi-Regime | **$94,315.00** | Anti-Crop Preemption Expert |
| **`R2_DMITRII`** | Dmitrii LB2800 | `extracted_agents/dmitrii_lb2800/main.py` | Pure Livestock Specialist | **$85,002.30** | Unshared Market / Anti-Bakery Expert |
| **`R3_P3090`** | Public 3090 | `external_repos/.../public_3090/output/main.py` | Fit-Optimized Fast Tape | **$73,170.00** | Low-Latency Benchmark Expert |
| **`R4_V54`** | Variant V54 | `candidates/cms5_v54_faithful.py` | Commercial Crop Flood | **$98,854.70** | High-Volume Agricultural Expansionist |
| **`R5_V25P3`** | V25 Unified | `candidates/v25_p3_unified.py` | Fixed Balanced Zoning | **$88,000.00** | Multi-Quadrant Diversification Expert |

---

## 2. In-Depth Profile of Each Expert

### `R0_A7` — The Protected Benchmark Incumbent
- **Choreography:** Tick-exact sequence of 4 worker hires, single-quadrant intensive crop cycles, and deterministic terminal liquidation.
- **Strengths:** Maximum capital velocity in standard competitive environments; leaves $0 cargo in shed and on workers at Step 719; zero idle worker waste.
- **Weaknesses:** Cannot dynamically expand land or defer sales when opponents dump into the bakery.

### `R1_V22R1` — The Slot A Adaptive Portfolio Champion
- **Choreography:** Coordinated multi-worker system with weed-repair wraps and demand-adjusted price impact sell reordering.
- **Strengths:** High win rate against erratic agro competitors; prevents selling into crashed markets.
- **Weaknesses:** Carries minor scheduler overhead compared to A7's pure open-loop tape.

### `R2_DMITRII` — The Pure Livestock Frontier Specialist
- **Choreography:** Aggressive early coops and pastures; buys 4 cows, 2 sheep, 2 geese; avoids wheat crop cycle; sells milk, wool, and eggs continuously.
- **Strengths:** Completely unaffected when opponents flood the wheat bakery market; achieves massive unshared margin if opponent focuses on crops.
- **Weaknesses:** Sinks substantial early capital into animals, leaving small liquid cash buffer in the opening 72 ticks.

### `R3_P3090` — The Public 3090 Top-Replay Fit
- **Choreography:** 719-step action tape based on dominant top-30 replays, incorporating weed repair and town shop sell priority.
- **Strengths:** High reproducibility; consistent baseline performance.
- **Weaknesses:** Completely open-loop; fails to adapt if physical grid coordinates are blocked by opponent.

### `R4_V54` — The Commercial Crop Flood Specialist
- **Choreography:** Purchases quadrant 2, 3, and 4; uses 8 workers to cultivate large wheat and carrot fields; massive bulk sales.
- **Strengths:** Can score up to $180k+ when market demand is high and opponent is passive or focused on animals.
- **Weaknesses:** Suffers catastrophic margin collapse if facing another aggressive crop farmer.

### `R5_V25P3` — The Balanced Zoning Backbone
- **Choreography:** Divides land strictly into agricultural vs livestock zones; maintains diversified revenue streams.
- **Strengths:** High economic stability; low variance across random seeds.
- **Weaknesses:** Lacks the extreme upside of pure crop or pure livestock specialists.
