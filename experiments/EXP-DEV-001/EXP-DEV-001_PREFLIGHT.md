# EXP-DEV-001 PREFLIGHT VERIFICATION REPORT

**Experiment Identifier**: `EXP-DEV-001`  
**Governing Protocol**: `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`  
**Protocol Freeze Hash (SHA-256)**: `671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3`  
**Git Commit**: `a1ba5acb0d04689874ce1333892825f014eea924`  
**Date**: 2026-09-11  
**Auditor**: Antigravity Autonomous Pair Programmer (Execution Engine)  
**Overall Preflight Status**: **PASS (ALL MANDATORY ITEMS PASSED)**  

---

## Preflight Verification Checklist

### A. Protocol
- [x] **protocol exists**: **PASS** — [`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/audits/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md)
- [x] **protocol hash matches freeze**: **PASS** — `671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3` verified bit-exact.
- [x] **frozen Git commit exists**: **PASS** — Commit `a1ba5acb0d04689874ce1333892825f014eea924` committed and verified.
- [x] **protocol unchanged since freeze**: **PASS** — `git diff --exit-code` returns 0.
- [x] **EXP-DEV-001 definition is unambiguous**: **PASS** — Hypothesis $H_1$, null $H_0$, metrics, partitions, and stop rules clearly specified.
- [x] **control is defined**: **PASS** — Primary control: `ClosedLoopAgentV2` (static 19S/0T); reference: `Dmitrii-LB2800`.
- [x] **treatment is defined**: **PASS** — `dev_001_dynamic_portfolio` ([`candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py)).
- [x] **primary metric is defined**: **PASS** — Mean Paired Margin vs `ClosedLoopAgentV2` in coins.
- [x] **sample size is defined**: **PASS** — Discovery $N=50$ (100 matches); Qualification $N=50$ (100 matches); Holdout $N=50$ (reserved).
- [x] **seed partition is defined**: **PASS** — Discovery: Seeds 50000–50049; Qualification: Seeds 50050–50099.
- [x] **stop criteria are defined**: **PASS** — Fail if Discovery margin $< \$0.00$ or worst single loss $< -\$800.00$.
- [x] **analysis procedure is defined**: **PASS** — CRN paired difference, Student's $t$, 95% CI, empirical quantiles.
- [x] **fallback behavior is defined**: **PASS** — Fallback A $\to$ B $\to$ C $\to$ D strictly adhered to.

### B. Simulator
- [x] **exact simulator version identified**: **PASS** — `kagsim` `ENGINE_VERSION`: `1.32.7` (matches `kaggle_environments 1.32.7`).
- [x] **simulator source/build identified**: **PASS** — Ported from C++ source [`external_repos/kaggriculture-cppsim/sim/sim.hpp`](file:///c:/Users/Sundareswaran/Kagriculture/external_repos/kaggriculture-cppsim/sim/sim.hpp), compiled to binary `.pyd`.
- [x] **simulator initializes successfully**: **PASS** — `kagsim.Game(seed)` tested and confirmed working.
- [x] **game length verified**: **PASS** — 720 steps per episode.
- [x] **action semantics verified**: **PASS** — Unit operations (DIG, PLANT, WATER, HARVEST, FEED, etc.) and market operations (HIRE, BUY_LAND, BUY_SEED, SELL).
- [x] **market order limit verified**: **PASS** — Maximum 10 orders executed per step.
- [x] **shop semantics verified**: **PASS** — Unlocks every 3 days (Step 72, 144, 216...); pulls every 4 steps.
- [x] **simulator identity recorded**: **PASS** — Recorded in [`EXP-DEV-001_CONFIG.json`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_CONFIG.json).

### C. Agents
- [x] **V2 resolves correctly**: **PASS** — [`candidates/closed_loop_architecture/closed_loop_v2.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/closed_loop_v2.py) (SHA-256: `95b64439...`).
- [x] **static 19S/0T resolves correctly**: **PASS** — Plan 0 execution verified bit-exact to `ClosedLoopAgentV2`.
- [x] **Dmitrii resolves correctly**: **PASS** — Entry point [`extracted_agents/dmitrii_lb2800/main.py`](file:///c:/Users/Sundareswaran/Kagriculture/extracted_agents/dmitrii_lb2800/main.py) (SHA-256: `495bfa48...`).
- [x] **treatment resolves correctly**: **PASS** — [`candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py`](file:///c:/Users/Sundareswaran/Kagriculture/candidates/closed_loop_architecture/dev_001_dynamic_portfolio.py).
- [x] **no baseline unexpectedly modified**: **PASS** — Baseline files clean.
- [x] **frozen submissions unchanged**: **PASS** —
  - Shop (`candidates/compiled_v54_plus_shop.py`): `f651ccd220e701968bc33579812d8917da63f5b0582f2fd0d363fa6a16ffd8b8`
  - Residual (`candidates/compiled_v54_plus_residual.py`): `18402ec6fa3709b9b5ef90dd9c8d7b9c0e44aea55ab163e44a80a4adc0cb7eeb`

### D. Leakage
- [x] **active containment sandbox enabled**: **PASS** — `ActiveContainmentSandbox` wraps all candidate actions.
- [x] **14-vector adversarial suite passes**: **PASS** — 14 / 14 attacks intercepted and blocked (100.0%).
- [x] **all prohibited behaviors remain blocked**: **PASS** — File I/O, `gc`, `inspect`, subprocess, socket, ctypes, RNG state, secret env access.
- [x] **production-agent compatibility passes**: **PASS** — Bit-exact action and score parity across 720-step episodes.
- [x] **no leakage control disabled**: **PASS** — Zero bypass flags active.
- [x] **no temporary bypass exists**: **PASS** — Standard containment active.

### E. Holdout
- [x] **no seed 214200–214249 appears in experiment seed list**: **PASS** — Seed list restricted to 50000–50049 (Discovery) and 50050–50099 (Qualification).
- [x] **runner hard-rejects these seeds**: **PASS** — Hard programmatic assertion implemented.
- [x] **no holdout output is loaded**: **PASS** — Verified zero holdout outputs exist or are referenced.
- [x] **no holdout-derived configuration is used**: **PASS** — Verified.
- [x] **no holdout-derived threshold is used**: **PASS** — Verified.

### F. Workspace
- [x] **experiment directory is isolated**: **PASS** — [`experiments/EXP-DEV-001/`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001).
- [x] **no stale outputs will be overwritten**: **PASS** — Clean directory.
- [x] **raw results will be preserved**: **PASS** — All raw JSON/CSV and logs stored permanently.
- [x] **baseline hashes recorded**: **PASS** — Recorded in configuration.
- [x] **frozen submission hashes recorded**: **PASS** — Verified bit-exact.

### G. Statistics
- [x] **paired comparison defined**: **PASS** — $\text{Margin}(s) = (\text{Cand}_0 - \text{Ctrl}_1) + (\text{Cand}_1 - \text{Ctrl}_0)$.
- [x] **CI method defined**: **PASS** — Student's $t$ with $df = n - 1$.
- [x] **win-rate definition fixed**: **PASS** — Proportion of seeds where paired margin $> 0$.
- [x] **treatment-selection rule fixed**: **PASS** — Single preregistered treatment variant; advance to Qual if $\Delta \mu > +\$50.00$ and $p_{05} \ge -\$200.00$.
- [x] **multiple-testing policy fixed**: **PASS** — Exactly 1 candidate evaluated.
- [x] **stopping rule fixed**: **PASS** — Terminate if Discovery margin $< 0$ or worst loss $< -\$800.00$.

### H. Reproducibility
- [x] **exact seed manifest saved**: **PASS** — [`EXP-DEV-001_SEEDS.json`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_SEEDS.json).
- [x] **protocol hash saved**: **PASS** — [`EXP-DEV-001_PROTOCOL_HASH.txt`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_PROTOCOL_HASH.txt).
- [x] **simulator identity saved**: **PASS** — [`EXP-DEV-001_CONFIG.json`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_CONFIG.json).
- [x] **agent identity/hash saved**: **PASS** — [`EXP-DEV-001_CONFIG.json`](file:///c:/Users/Sundareswaran/Kagriculture/experiments/EXP-DEV-001/EXP-DEV-001_CONFIG.json).
- [x] **execution command saved**: **PASS** — `python experiments/EXP-DEV-001/run_exp_dev_001.py`.
- [x] **raw evidence saved**: **PASS** — Target output files specified.

---

**PREFLIGHT VERDICT: PASS** — Ready for Stage 2 (Smoke Test) and Stage 3 (Discovery Execution).
