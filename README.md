# Kagriculture Economic Simulator & Competitive Agent Repository

**Kagriculture** is a competitive multi-agent economic simulation research project built for the Kaggle Kaggriculture competition. In a 700-turn synchronous economic environment, two competing farm agents make simultaneous decisions managing worker choreography, land expansion, crop rotation, livestock feeding, shop delivery contracts, and market liquidity to maximize final net worth.

This repository preserves the complete, validated research progression, simulation engines, candidate architectures, and the official final competition submission (**V49 Meta Fusion**).

---

## 1. Quick Start: Running the Final Agent

The production competition agent is **V49 Meta Fusion**, located at [`candidates/v49_meta_fusion/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/v49_meta_fusion/main.py).

### Prerequisites
- Python 3.11 or 3.12 (standard Kaggle / A100 runtime)
- `kaggle-environments == 1.32.7`

```bash
pip install kaggle-environments==1.32.7
```

### Self-Play Smoke Test
Run a full 700-step head-to-head match locally:
```python
from kaggle_environments import make

env = make("kaggriculture", configuration={"episodeSteps": 700})
env.run(["candidates/v49_meta_fusion/main.py", "candidates/v49_meta_fusion/main.py"])

print("Match complete!")
print("Player 0 final cash/reward:", env.state[0].reward)
print("Player 1 final cash/reward:", env.state[1].reward)
```

---

## 2. Repository Structure

```
Kagriculture/
│
├── README.md                           # Master project guide and documentation portal
├── CHANGELOG.md                        # Chronological competition milestones
├── .gitignore                          # Hardened repository hygiene and exclusion rules
│
├── candidates/                         # Agent implementations across generations
│   ├── v49_meta_fusion/                # -> INCUMBENT PRODUCTION AGENT (99.31% WR)
│   ├── v48_challenger/                 # Milestone: Route 105 surgical overrides (+0.74 alpha)
│   ├── v47_elite_transfer/             # Milestone: Public 2945 elite chassis integration
│   ├── v44_economic_portfolio/         # Milestone: Discovery of Step >= 520 CapEx cutoff rule
│   ├── v30_a7_standalone/              # Historic: Standalone A7 candidate
│   ├── v50_dead_action_guard/          # Post-V49: Fertilizer suppression (rejected)
│   └── v51_blocked_repair/             # Post-V49: Weed repair buffer (rejected)
│
├── submissions/                        # Official packaged competition submissions
│   ├── v49_meta_fusion_20260929_2212.zip # Packed final competition submission archive
│   └── v49_meta_fusion_submission/     # Extracted verification directory
│
├── team_submissions/                   # Teammate collaborator submissions
│   ├── submission_Vj_kc_v24.tar.gz     # Teammate Vj Culture v24 bundle (best teammate)
│   └── submission_Vj_kc_v27.tar.gz     # Teammate Vj Culture v27 bundle
│
├── research/                           # Chronological scientific research dossiers
│   ├── final_synthesis/                # Definitive causal traces, decisions, and postmortems
│   ├── v40/ .. v44/                    # FastSim, residual RL, compositional alpha, CapEx
│   ├── v45/ .. v48/                    # Market modeling, route diversity, 2945 transfer
│   ├── v49/                            # Top-meta memory and E402 late seed-cap overlay
│   ├── v50/ .. v55/                    # Fertilizer, weed repair, cowswap, and midgame tests
│   ├── v56/ .. v57/                    # V49 4-loss forensics and market queue optimization
│   ├── v58/ .. v60/                    # August replay validation & September elite acquisition
│   └── repository_cleanup/             # Archival audit reports, classifications, manifests
│
├── docs/                               # Canonical documentation and provenance ledgers
│   ├── FINAL_ARTIFACTS.md              # Authoritative final submission and teammate dossier
│   ├── AGENTS.md                       # Master agent catalog with SHA256 cryptographic hashes
│   ├── RESEARCH_HISTORY.md             # In-depth chronicle of hypotheses and results (V40-V60)
│   └── DATASETS.md                     # Replay corpus acquisition and schema documentation
│
├── data/                               # Dataset documentation and manifests
│   ├── README.md                       # External data policy and retrieval instructions
│   └── MANIFEST.csv                    # Ledger of all excluded replay corpora
│
├── engine/                             # Core environment engine and simulation logic
├── aec/                                # PettingZoo AEC multi-agent environment wrapper
├── scripts/                            # Tournament runners, benchmark scripts, diagnostic tools
├── configs/                            # Simulation and experiment configurations
└── tests/                              # Comprehensive test suite and assertions
```

---

## 3. Preserved Historical Branches

To prevent multi-gigabyte repository bloat while preserving 100% of historical development, experimental Culture campaigns are preserved on dedicated, self-contained Git branches:

- [`culture/v24`](file:///c:/Users/Sundareswaran/Kagriculture): Preserves the Culture v24 campaign, including Challengers C1 (idle zeroing), C2 (livestock scale), and C3 (carrot compound), alongside competitive bottleneck matrices and qualification manifests.
- [`culture/v25`](file:///c:/Users/Sundareswaran/Kagriculture): Preserves the Culture v25 campaign, including the Coherent Planner architecture (Macro P1, Options P2, Unified P3) and confirmation reports.

To inspect or switch to a historical branch:
```bash
git checkout culture/v24
# or
git checkout culture/v25
```

---

## 4. Key Scientific Breakthroughs

1. **Step >= 520 CapEx Cutoff Rule (V44)**:
   Forbidding `BUY_ANIMAL` and `BUY_LAND` after step 520 preserves critical cash float and prevents dead inventory that cannot amortize before match termination.
2. **Surgical Shop-Route 105 Overrides (V48)**:
   Overriding standard routes with Route 105 for Brunch/Farmers, Bakery/Brunch, and PetCafe/Farmers shop pairs delivered **+0.74 alpha** and eliminated historical loss scenarios without regression.
3. **E402 Late Seed-Cap Overlay (V49 Incumbent)**:
   Clamping `BUY_SEED` for wheat and carrots after turn 624 to exact unplanted tile counts prevents cash waste, driving the Incumbent agent to a **99.31% Win Rate (572W / 4L / 0T)** in rigorous out-of-sample testing.
4. **Pareto-Optimal Market Ordering (V56–V57)**:
   Microscopic analysis of V49's 4 rare losses showed they stem from simultaneous step-697 transaction collisions in the market interpreter where tie-breaking favors player order. Interventions attempting to alter slot order caused casualties on adjacent seeds; the baseline ordering is Pareto-optimal.

---

## 5. Large External Datasets

Raw multi-gigabyte simulation match replays (~15 GB) are **intentionally excluded from Git** to keep the repository lightweight and portable. All code required to reacquire replays via the Kaggle API is documented in:
- [`docs/DATASETS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/DATASETS.md)
- [`data/MANIFEST.csv`](file:///c:/Users/Sundareswaran/Kagriculture/data/MANIFEST.csv)

---

## 6. Verification and Benchmarks

To run the standard evaluation benchmark between the Incumbent and reference opponents:
```bash
python scripts/run_tournament.py --agent1 candidates/v49_meta_fusion/main.py --agent2 agent_frontier.py --seeds 10
```

Detailed cryptographic hashes for all candidate artifacts are maintained in [`docs/AGENTS.md`](file:///c:/Users/Sundareswaran/Kagriculture/docs/AGENTS.md).
