# CORRECTED CROSS-REPOSITORY STRATEGIC CONCLUSIONS
## Forensic & Empirical Synthesis Grounded in Direct Evidence

---

## 1. Executive Corrected Verdict

The previous "Championship Repository Intelligence Audit" correctly identified the high-level code lineages (Mohui v66 wrapping chain, Lixingtao v54 nested layers, Island GA parameter set, cppsim C++ fidelity), but **overstated empirical performance margins, hallucinated the online replay dataset size, conflated raw simulator throughput with end-to-end search speed, and presented speculative marketing claims ("Guaranteed >120k", "Top 5") as facts**.

When stripped of rhetorical inflation, the empirical facts establish:

1. **`kaggriculture-cppsim` is a high-fidelity bit-exact simulator for Kaggle 1.32.7**:
   - Matches observation dicts turn-by-turn across 6/6 real Kaggle episode traces (10,066 field-blocks per trace, 0 divergence).
   - Exhibits strict deterministic reproducibility (identical state and action SHA256 hashes across repeated runs).
   - Shop pinning mechanism successfully removes weed RNG board-dependence (23/24 seeds re-rolled unpinned vs 0/24 pinned).
   - **However**: Its raw throughput (2,746 ep/s single-core, 15,311 ep/s multi-core) drops to **62.5 ep/s** when running real Python agents due to cross-language GIL and Python interpreter execution overhead. The true end-to-end acceleration factor is **~415x**, NOT 2,000x.

2. **Mohui v66 is a composite heuristic wrapper, not an autonomous learning agent**:
   - Architecture is an explicit importlib cascade: `v66` -> `v65` -> `v62` -> `v60` -> `v58` -> `v51` -> embedded `v50`.
   - Classification uses only public observable states (`_public_signature` at turns 72 and 144) to identify opponents (Curve q2, CYGN clone, Daniel) and select counter-routes.
   - It decisively defeats legacy baselines (V2 win rate 100%, +114,615 margin).
   - **However**: Against v54, V66's margin is **+3,072 coins** (not a blowout), and V54 actually defeats V66 on specific seeds (e.g. seed 101: V54 wins by +7,739; seed 606: V54 wins by +2,425).

3. **Lixingtao v54 represents multi-layered nested engineering with severe holdout overfitting**:
   - Unpacked 3 layers of nested compression: Layer 0 (v51, 171 KB) -> Layer 1 (v50, 137 KB) -> Layer 2 (v49, 117 KB), revealing 13 historical modular components.
   - `v23.planner` explicitly attempted route switching and quantity MPC, but the author abandoned them because *"seed-grouped holdouts did not improve wins"*.
   - `lixingtao123` contains **52 replay files (51 unique episodes)**, NOT "200+ online replays".
   - The reported 100% win rates were achieved on narrow 16-seed panels against obsolete baselines (`variant_a`, `public_2900`). When evaluated on random holdouts (seeds 31-40), performance collapsed to a **10% win rate**.

4. **Public Ecosystem Capabilities vs. Blind Spots**:
   - **Exists**: High-speed C++ simulation (`kagsim`), island-model genetic algorithm with block crossover and ring migration (`islandga`), public signature opponent recognition (`v66`), observation-conditioned residual sell control (`v49`).
   - **Does NOT Exist in Any of the 5 Repositories**: Online MCTS, tree search, dynamic programming, learned neural value functions, self-play reinforcement learning, counterfactual regret minimization.

---

## 2. Code Capability vs. Actual Use Ledger (Rule 14)

| Component / Subsystem | Repository | Exists in Code? | Actually Executed? | Used in Final Agent? | Used During Search? | Used During Eval? | Ground-Truth Finding |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **C++ Bit-Exact Simulator** | `kaggriculture-cppsim` | YES | YES | NO (Tool/Eval) | YES | YES | Fully verified C++ engine; speeds up fixed evaluation ~415x. |
| **Shop Pinning System** | `kaggriculture-cppsim` | YES | YES | NO (Eval only) | YES | YES | Decouples weed RNG from season shop unlocks. |
| **Telemetry Invariant Asserts** | `kaggriculture-cppsim` | YES | YES | NO (Validation) | NO | YES | 6/6 telemetry tests pass. |
| **Island GA Optimizer** | `kaggriculture-island-ga` | YES | YES | NO (Search tool) | YES | NO | 4 islands, 7 mutations, tournament size 3, confirm panel. |
| **Ring Migration & Archipelago Restart** | `kaggriculture-island-ga` | YES | YES | NO (Search tool) | YES | NO | Confirmed in `search.py` lines 44-46, 220-248. |
| **Public Signature Classifier** | `kaggriculture-v66-agent` | YES | YES | YES | NO | YES | Classifies Curve q2, CYGN, Daniel using public turns 72/144. |
| **Terminal Return Overlay** | `kaggriculture-v66-agent` | YES | YES | YES | NO | YES | 6-turn terminal loaded hand return to bank cash. |
| **Nested Unpacker Lineage** | `lixingtao123-Kaggriculture` | YES | YES | YES | NO | NO | Unpacks v51 -> v50 -> v49 at startup. |
| **Quantity MPC** | `lixingtao123-Kaggriculture` | NO (Removed) | NO | NO | ABANDONED | NO | Tested in v23, abandoned due to poor holdout generalization. |
| **200+ Online Replay Miner** | `lixingtao123-Kaggriculture` | NO (Overstated) | PARTIAL | NO | NO | YES (30 games) | Only 51 unique replays exist; 30 analyzed in JSON summaries. |
| **Goose Relocation Policy** | `okami001-Kaggriculture` | YES | YES | YES | NO | YES | Scripted goose movement to clear farming tiles. |

---

## 3. Corrected D-MPSF Assessment (Rule 18)

The previous report recommended the **Dual-Track Compiler-Guided Model-Predictive Strategy Foundry (D-MPSF)** with exaggerated certainty. Here is the evidence-based scientific reassessment:

| Assessment Dimension | Prior Audit Claim | Corrected Forensic Reality | Evidence Basis |
| :--- | :--- | :--- | :--- |
| **Evidence Strength** | "Overwhelming" | **MODERATE** | C++ simulation speed and genetic optimization are proven tools, but combining them does not guarantee a competitive edge. |
| **Expected Upside** | "Guaranteed >120k, Top 5" | **SPECULATIVE (+10k to +25k over V2)** | V66 achieves 125k-175k on favorable seeds, but drops to 41k on unfavorable seeds. No architecture guarantees leaderboard rank. |
| **Implementation Risk** | "Low" | **HIGH** | Integrating C++ bindings, Python compilers, and multi-island GA introduces significant interface and state-marshaling complexity. |
| **Simulator Fidelity Risk** | "Zero" | **LOW TO MODERATE** | Core mechanics match 1.32.7, but shop pinning removes game-theoretic opponent interaction. Over-optimizing on pinned shops causes drift on live unpinned seeds. |
| **Overfitting Risk** | "Extremely Low" | **VERY HIGH** | Demonstrated by Lixingtao: 100% win rate on training holdouts collapsed to 10% on random holdouts. Fixed action streams overfit heavily to training seeds. |
| **Top-10 Plausibility** | "Near Certain" | **PLAUSIBLE HYPOTHESIS** | Attainable only if the architecture incorporates robust closed-loop adaptation, NOT pure open-loop trajectory optimization. |
