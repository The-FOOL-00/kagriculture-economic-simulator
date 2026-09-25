# V39 — Research Plan: Live V35 Loss Forensics & Targeted Counterfactual Search

## 1. Executive Summary & Core Mission
V35 is currently LIVE in Kaggriculture (`candidates/v35_a7_opening/main.py`, SHA-256: `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249`).
The production candidate is strictly frozen.

V39 is a **failure-driven research program**:
> **Use actual live V35 games, current public replay/meta data, and exact local simulation to identify concrete failure mechanisms, then develop the smallest deterministic interventions that could rescue those failures without damaging V35's existing strengths.**

V39 will NOT:
- Modify V35, A7, or V22R1.
- Submit anything to Kaggle or create competition submissions.
- Launch generic RL or unconstrained PPO searches.
- Evaluate or access protected holdout seeds (`214200–214249`, `340090–340199`, `249695–249734`).
- Block the interactive session synchronously on long-running processes (all long jobs will run in the background).

---

## 2. Frozen Architectural Baselines
| System | File Path | SHA-256 Checksum | Operational Status |
| :--- | :--- | :--- | :--- |
| **V35** | `candidates/v35_a7_opening/main.py` | `1959021bdb1aeff720732aec866f5c9f3c9fa0b259ee0ab25982bda367593249` | **Live Production Benchmark** (Frozen) |
| **A7** | `candidates/v30_a7_standalone/main.py` | `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f` | **Historic Baseline Reference** (Frozen) |
| **V22R1** | `submission_aec_v22r1.tar.gz` | `6b879b3e499d2cf43b76884f6ef433479468b5c316f92cf4a8cc5119586fb3f5` | **Historic Portfolio Anchor** (Frozen) |

---

## 3. Quarantined & Protected Holdouts
Under no circumstances will any code inspect, download, score, train on, or evaluate seeds in:
- `214200 – 214249` (V22R1 protected cohort)
- `340090 – 340199` (V28/V29 virgin confirmation holdout)
- `249695 – 249734` (V25/V26 robustness holdout)

All simulation harnesses will enforce explicit safe seed allowlists.

---

## 4. Phase-by-Phase Execution Roadmap
1. **Phase 0 — V35 Live Identity**: Fetch submission metadata (`56540535`), score, status, episode count -> `V39_LIVE_STATUS.md`.
2. **Phase 1 — Live Episode Harvester**: Build background harvester in `scratch/v39/live/`, download all V35 replays and logs -> `V39_LIVE_DATA_CATALOG.md` & `scratch/v39/live/episodes.jsonl`.
3. **Phase 2 — Result Classification**: Classify every V35 game (Win/Loss/Tie by margin) -> `V39_LIVE_RESULT_DISTRIBUTION.md`.
4. **Phase 3 — Loss Forensics**: Timeline reconstruction for every loss, tracking cash, market, inventory, and finding the **first divergence point** -> `V39_LIVE_LOSS_FORENSICS.md`.
5. **Phase 4 — Failure Taxonomy**: Cluster losses into causal mechanism classes -> `V39_FAILURE_TAXONOMY.md`.
6. **Phase 5 — Research Prioritization**: Rank mechanisms by $Priority = Frequency \times MeanLossMargin \times Recoverability \times InterventionConfidence$ -> `V39_RESEARCH_PRIORITY.md`.
7. **Phase 6 — Public Meta Audit**: Analyze Kaggle discussions, recent public agent developments, Rust simulator findings, and Southeast map theories -> `V39_PUBLIC_META_AUDIT.md`.
8. **Phase 7 — Live Opponent Fingerprinting**: Extract observable behavioral fingerprints for all opponents encountered -> `scratch/v39/live/opponent_fingerprints.jsonl` & `V39_OPPONENT_FINGERPRINTS.md`.
9. **Phase 8 — Fixability Analysis**: Classify into Fixable, Partially Fixable, Not Fixable, Unknown -> `V39_FIXABILITY_ANALYSIS.md`.
10. **Phase 9 — Exact State Reconstruction**: Extract immutable decision state snapshots immediately preceding the first divergence -> `scratch/v39/loss_states/`.
11. **Phase 10 — Targeted Counterfactual Search**: Run exact local rollouts ($H=4, H=8$) on cloned states without mutating original episodes.
12. **Phase 11 — Smallest Legal Intervention**: Identify minimal 1-variable causal interventions -> `V39_INTERVENTION_CATALOG.md`.
13. **Phase 12 — Rescue Simulation**: Test candidate interventions across target losses, measuring rescues vs casualties.
14. **Phase 13 — Near-Tie Analysis**: Counterfactual search on near-ties to explore margin stabilization -> `V39_NEAR_TIE_ANALYSIS.md`.
15. **Phase 14 — Mechanism Clustering**: Group failure states into shared economic mechanisms -> `V39_MECHANISM_CLUSTERING.md`.
16. **Phase 15–20 — Candidate Construction & Verification**:
    - Build `candidates/v39_live_targeted/` ONLY if backed by repeated, causal evidence.
    - Preserve V35 as 100% fallback chassis.
    - No-regression gauntlet against V35 benchmarks.
    - Adversarial stress tests and deterministic rule distillation.
17. **Phase 21–25 — Validation & Competition Monitoring**:
    - Statistical testing (paired $\Delta$, bootstrap CI, McNemar) -> `V39_STATISTICS.md`.
    - Maintenance of `scratch/v39/live_loss_database.jsonl`.
    - Read-only periodic competition monitoring utility.
18. **Phase 26–29 — Final Decision**: Formulate definitive verdict -> `V39_FINAL_DECISION.md`.
