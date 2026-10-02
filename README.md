# Kagriculture: Economic Simulator & Competitive Agent Architecture

**Kagriculture** is a competitive multi-agent economic simulation research project built for the Kaggle [Kaggriculture Competition](https://www.kaggle.com/competitions/kaggriculture). In a 700-turn synchronous economic environment, two competing farm agents make simultaneous decisions managing worker choreography, land acquisition, crop sequencing, livestock feeding, shop contract fulfillment, and market liquidity to maximize final net worth.

This repository preserves the complete, verified research progression, simulation engines, candidate architectures, and the official final competition submission (**V49 Meta Fusion**).

---

## Competition Result

| Field | Official Result | Verification & Source |
| :--- | :--- | :--- |
| **Competition** | [Kaggriculture](https://www.kaggle.com/competitions/kaggriculture) ($50,000 USD Featured Simulation) | Official Kaggle Competition |
| **Team Name** | **Eldritch** (Team ID `16791873`) | Team Members: `thefool00` (Repo Author), `sanjay6727` |
| **Final / Current Rank** | **#1,125** (Top ~11% out of 10,246 teams) | [Kaggriculture Competition Leaderboard](https://www.kaggle.com/competitions/kaggriculture/leaderboard) |
| **Kaggle Rating / Score** | **1,791.9** | Multi-player asynchronous Elo rating |
| **Rank Recorded** | **October 2, 2026** | Verified via official Kaggle Leaderboard API & CSV snapshot |
| **Final Submission** | **V49 Meta Fusion** | Submitted on 2026-09-30 17:15:29 UTC |
| **Submission Artifact** | [`submissions/v49_meta_fusion_20260929_2212.zip`](file:///c:/Users/Sundareswaran/Kagriculture/submissions/v49_meta_fusion_20260929_2212.zip) | Official packaged bundle submitted to platform |
| **Submission Source** | [`candidates/v49_meta_fusion/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v49_meta_fusion/main.py) | Standalone executable production script |
| **Source SHA-256** | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` | Cryptographic SHA-256 verification hash |
| **Archive SHA-256** | `37F10DEE73C7E01BE1FE240FBFC5344F254D2FE29FB0764FB14B2C69AB99306D` | Platform zip bundle verification hash |

> **Note on Performance Metrics**:  
> - **Kaggle Leaderboard Rank (#1,125, Rating 1,791.9)** measures asynchronous Elo rating across diverse public matchmaking pairings.  
> - **Internal Validation Benchmark (99.31% WR, 572W / 4L / 0T)** measures local deterministic head-to-head performance against baseline opponent suites across 576 fresh unobserved seeds and 100% win rate (400/400) against historical top-tier replay policies.

For complete competition details, see [`docs/COMPETITION.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/COMPETITION.md).

---

## Final Agent Architecture: V49 Meta Fusion

The final submitted agent, **V49 Meta Fusion**, represents the synthesis of four major research milestones:

```
V47 Elite 2945 Chassis (Hayashi/Tschinkel pathfinding & dispatch)
   │
   ├── + V44 Systematic CapEx Cutoff (Step >= 520 Land/Animal purchase freeze)
   │
   ├── + V48 Surgical Route 105 Overrides (+0.74 alpha on 3 weak shop pairs)
   │
   └── + V49 E402 Late Seed-Cap Overlay (Step >= 624 exact unplanted tile clamp)
         └── Result: 99.31% Win Rate / Zero Dead Capital / 0 Casualties
```

### Architectural Pillars
1. **Elite 2945 Movement Engine (V47)**: Port of the public 2945 chassis providing non-blocking multi-unit worker scheduling, dynamic cow-to-goose substitution, and shed-capacity guards.
2. **Systematic CapEx Cutoff (V44)**: Strict rule prohibiting `BUY_ANIMAL` and `BUY_LAND` after step 520, preventing non-amortizing capital expenditure in the late game.
3. **Surgical Shop-Route 105 Overrides (V48)**: Targeted overrides for three specific shop pairs (`Brunch/Farmers`, `Bakery/Brunch`, `PetCafe/Farmers`) substituting Route 105, yielding +0.74 alpha with zero casualties.
4. **E402 Late Seed-Cap Overlay (V49)**: Clamp on seed purchasing after step 624 strictly matching the exact count of remaining unplanted tiles, completely eliminating stranded inventory.

---

## Quick Start & Verification

### Running the Final Agent Locally
```python
from kaggle_environments import make

# Initialize standard 700-step environment
env = make("kaggriculture", configuration={"episodeSteps": 700})

# Run self-play match between V49 instances
env.run(["candidates/v49_meta_fusion/main.py", "candidates/v49_meta_fusion/main.py"])

print("Match complete!")
print("Player 0 final cash/reward:", env.state[0].reward)
print("Player 1 final cash/reward:", env.state[1].reward)
```

### High-Throughput Headless Simulator
For rapid validation (500+ steps/second), use the custom simulation engine:
```python
from research.v40.env.fast_sim import FastKagricultureSim
import candidates.v49_meta_fusion.main as v49

sim = FastKagricultureSim()
obs0, obs1 = sim.reset(seed=42)

for turn in range(700):
    act0 = v49.agent(obs0, sim.configuration)
    obs, rewards, done, info = sim.step([act0, {}])
    obs0 = obs[0]
    if done:
        break

print(f"Simulation completed at step {sim.step_idx}. Player 0 Reward: {rewards[0]}")
```

---

## Repository Structure

```
Kagriculture/
│
├── README.md                           # Master landing page & verified competition result
├── CHANGELOG.md                        # Chronological release and milestone ledger
├── .gitignore                          # Hardened repository hygiene and exclusion rules
│
├── docs/                               # General documentation & specifications
│   ├── COMPETITION.md                  # Detailed Kaggle standing, scoring & team profile
│   ├── AGENTS.md                       # Canonical agent registry with SHA256 hashes (V24-V60)
│   ├── FINAL_ARTIFACTS.md              # Authoritative final submission and teammate dossier
│   ├── RESEARCH_HISTORY.md             # In-depth chronicle of hypotheses and results (V22-V60)
│   ├── DATASETS.md                     # Replay corpus acquisition and schema documentation
│   ├── ARCHITECTURE.md                 # System architecture and simulation mechanics
│   ├── EXPERIMENTS.md                  # Comprehensive experimental log and registry
│   ├── CONTRADICTIONS.md               # Empirical discrepancy resolution records
│   └── WALKTHROUGH.md                  # Repository codebase guide and walkthrough
│
├── candidates/                         # Production agent candidates
│   ├── v49_meta_fusion/                # -> FINAL INCUMBENT AGENT (99.31% WR)
│   ├── v48_challenger/                 # Milestone: Route 105 surgical overrides (+0.74 alpha)
│   ├── v47_elite_transfer/             # Milestone: Public 2945 elite chassis integration
│   ├── v44_economic_portfolio/         # Milestone: Discovery of Step >= 520 CapEx cutoff rule
│   ├── v25_p1_macro.py                 # Historical Culture v25 Macro Planner
│   ├── challenger_c1.py                # Historical Culture v24 Idle Zeroing Challenger
│   └── ...                             # Full candidate evolution suite
│
├── submissions/                        # Official platform submission packages
│   ├── v49_meta_fusion_20260929_2212.zip # Final platform submission archive
│   └── v49_meta_fusion_submission/     # Extracted production files
│
├── team_submissions/                   # Collaborator team submissions
│   ├── submission_Vj_kc_v24.tar.gz     # Teammate Vj Culture v24 bundle (best teammate)
│   └── submission_Vj_kc_v27.tar.gz     # Teammate Vj Culture v27 bundle
│
├── research/                           # Organized version-specific research dossiers
│   ├── tools/                          # Reusable forensic and diagnostic analysis scripts
│   ├── final_synthesis/                # Definitive causal traces, decisions, and postmortems
│   ├── v24/ .. v39/                    # Historical research dossiers (V24 through V39)
│   ├── v40/ .. v49/                    # FastSim, residual RL, compositional alpha, V49 incumbent
│   ├── v50/ .. v57/                    # Mechanism falsification, 4-loss forensics, queue audits
│   ├── v58/ .. v60/                    # August replay holdout & September elite acquisition
│   ├── historical_phases/              # Phase 14 through Phase 22 development records
│   ├── audits/                         # Intermediate claim ledgers, gates, and audits
│   └── repository_cleanup/             # Archival audit reports, classifications, manifests
│
├── data/                               # Dataset documentation & retrieval guides
│   ├── README.md                       # External data governance and retrieval commands
│   └── MANIFEST.csv                    # Ledger of all excluded external replay corpora
│
├── engine/                             # Core environment engine and simulation logic
├── aec/                                # PettingZoo AEC multi-agent environment wrapper
├── scripts/                            # Tournament runners, benchmark scripts, diagnostic tools
├── configs/                            # Simulation and experiment configurations
└── tests/                              # Comprehensive test suite and assertions
```

---

## Research Progression Overview

```
V22R1 (Baseline Release)
  ├── V24: Live Meta & Challengers (C1 idle zeroing, C2 scale, C3 carrot) [Merged from culture/v24]
  ├── V25: Coherent Planner Campaign (P1 macro, P2 options, P3 unified) [Merged from culture/v25]
  ├── V26-V30: Robustness, Noise Audit, and A7 Standalone packaging
  ├── V31R2-V35: Real-Price Forensics, Behavioral Cloning & A7 Opening Wash Controller
  ├── V36-V39: Independent Validation, PPO experiments & Live Loss Forensics
  ├── V40: FastKagricultureSim High-Throughput Engine (500+ steps/sec) & Macro RL
  ├── V41-V43: Safe Residual RL, Staggered Liquidation & Compositional Alpha
  ├── V44: Systematic CapEx Cutoff (Step >= 520 Rule saves thousands in stranded assets)
  ├── V45-V46: Opponent Market Pressure Modeling (AUROC 0.94) & Macro Route Diversity
  ├── V47: Public 2945 Elite Chassis Transfer (Hayashi/Tschinkel lineage)
  ├── V48: Surgical Shop-Route 105 Overrides (+0.74 alpha on 3 underperforming pairs)
  ├── V49: Live Top-Meta Memory & E402 Late Seed-Cap Overlay [FINAL INCUMBENT: 99.31% WR]
  ├── V50-V55: Hypothesis Falsification (Fertilizer suppression, weed buffer, cowswap rejected)
  ├── V56-V57: Microscopic Forensic Autopsy of V49's 4 Loss Worlds & Market Queue Lock
  └── V58-V60: August 3100+ Replay Reconstruction (400/400 wins) & September Recovery Build
```

For complete technical notes across all versions, see [`docs/RESEARCH_HISTORY.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/RESEARCH_HISTORY.md) and [`docs/AGENTS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/AGENTS.md).

---

## Historical Git Branches

To maintain archival hygiene without bloating the repository with raw temporary datasets, experimental campaigns were maintained on dedicated Git branches and subsequently incorporated:

- **`culture/v24`**: Preserved the Culture v24 campaign artifacts (Challengers C1, C2, C3, competitive bottleneck matrices, qualification manifests). Merged into `main` via PR #2; branch retained remotely as an immutable historical snapshot.
- **`culture/v25`**: Preserved the Culture v25 Coherent Planner artifacts (P1, P2, P3 planners, confirmation reports). Merged into `main` via PR #1; branch retained remotely as an immutable historical snapshot.
- **`main`**: Canonical production branch incorporating all validated candidates, clean documentation, and final competition submissions.

---

## License & Attribution

This project is licensed under the Apache License 2.0. Detailed third-party notices and attribution for lineage components (including Hayashi, Tschinkel, Dmitrii Gluzdov, and public benchmark baselines) are maintained in the respective candidate source headers.
