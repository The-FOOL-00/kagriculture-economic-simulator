# DEVELOPMENT GATE 0.2 — VIRGIN HOLDOUT PROVENANCE AUDIT
## Exhaustive Provenance Audit of Proposed Final Holdout Partition (Seeds 50150–50199) Across All Project History, Artifacts, and Live Forensics

**Gate Protocol**: Development Gate 0.2 Final Experiment-Readiness Audit  
**Governing Standard**: Strict OOD Partition Hygiene & Zero Prior Exposure Protocol  
**Audit Target**: Proposed Final Fresh Virgin Holdout (Seeds 50150–50199, N=50 seeds)  
**Date**: 2026-09-11  
**Auditor**: Antigravity Autonomous Pair Programmer (Audit Engine)  
**Status**: **FORMAL AUDIT REPORT — GATE BLOCKED**

---

## 1. Executive Summary & Core Finding

In Development Gate 0.1, Correction `CORR-0.1-09` reclassified Seeds 50100–50149 as an "Audited Benchmark Partition" (because their loss characteristics were evaluated in Audit 2) and proposed **Seeds 50150–50199** as the candidate "Fresh Virgin Holdout" cohort for pre-deployment qualification.

Before executing any development experiment (`EXP-DEV-001` through `EXP-DEV-005`), Gate 0.2 mandated an exhaustive provenance audit across the entire codebase, git history, result databases, replay archives, and research reports to verify whether Seeds 50150–50199 were genuinely virgin.

### **AUDIT VERDICT: SEEDS 50150–50199 ARE CONTAMINATED (NOT VIRGIN)**

1. **Direct Strategy Selection (Seeds 50155, 50161)**: In `scratch/test_phase16_generalization.py`, Seeds 50155 and 50161 were selected and evaluated in the Multi-Shop Generalization Matrix comparing `ClosedLoopAgentV2` against `TomatoSpecialistV1` and `Dmitrii-LB2800`. The resulting data in `scratch/generalization_matrix_results.json` directly established that Tomato Specialist lost -$11,133 margin in Pizza+Pet Cafe worlds, resulting in the formal retraction of the Tomato/Pizza alpha and the strategic commitment to V2.
2. **Live Tournament Forensic Exposure (Seed 50186)**: Seed 50186 was the seed of official live Kaggle match `107564294` (`56146971` vs `Les 2 oies 56149479`, Bakery+Brunch, -$46,718 margin). This match was extracted, decoded, and analyzed in `research/live_loss_counterforensics_report.md:50`. Per `REPORT_INDEX.md:95`, this analysis directly "triggered the design of the Closed-Loop Liquidity Guard and dawn hiring priority arbitration."
3. **Full Cohort Simulation & Shop Extraction (Seeds 50150–50199)**: In `scratch/census_phase3_500seeds.py:3, 80-83`, all seeds in `range(50000, 50500)`—which directly subsumes 50150 through 50199—were simulated in complete 720-step matches (`Dmitrii` vs `compiled_v54_plus_residual`). Their first, second, and third shop unlocks, route selections, and realized cash outcomes were computed and aggregated into `results/phase3_shop_census_500seeds.json`, directly published in `reports/FULL_SPECTRUM_SHOP_ECONOMY_AND_META_FORENSICS_REPORT.md:21`. Furthermore, `scratch/find_pizza_pet_seeds.py:6` explicitly scanned `range(50000, 50200)` for shop unlocks.

Under Section 3 and Section 8 of the Development Gate Protocol:
> *"If any holdout seed was previously used for strategy selection, it is NOT virgin."*  
> *"BLOCKED: If holdout contamination is found."*

**DEVELOPMENT GATE 0.2 IS FORMALLY BLOCKED** on holdout contamination grounds.

---

## 2. Exhaustive Forensic Evidence Base

### 2.1 Direct Strategy Selection Evidence: Seeds 50155 and 50161
In `scratch/test_phase16_generalization.py:29-55`:
```python
# Find 2 seeds for each shop pair in 50000..50500
def find_shop_seeds():
    pairs_needed = {
        ("PIZZA_SHOP", "PIZZA_SHOP"): [],
        ("PIZZA_SHOP", "PET_CAFE"): [],
        ...
    }
    for s in range(50000, 50600):
        g = kagsim.Game(s)
        for _ in range(144):
            g.step({'farmer': ['PASS'], 'hands': [], 'market': []}, ...)
        shops = g.observe(0)['town']['unlocked_shops']
        if len(shops) >= 2:
            pair = tuple(sorted(shops[:2]))
            if pair in pairs_needed and len(pairs_needed[pair]) < 3:
                pairs_needed[pair].append(s)
```
- **Selected Seeds for `PIZZA_SHOP + PET_CAFE`**: `[50069, 50155, 50161]`
- **Evaluated Agents**: `ClosedLoopAgentV2`, `TomatoSpecialistV1(sale_batch=6)`, `Dmitrii-LB2800`
- **Output Artifact**: `scratch/generalization_matrix_results.json`
  ```json
  "PIZZA_SHOP + PET_CAFE": {
    "v2": 107046.67,
    "tom": 95913.67,
    "delta": -11133.0,
    "seeds": [50069, 50155, 50161]
  }
  ```
- **Strategic Impact**: Proved that diverting farm acreage to tomatoes causes a severe -$11,133 loss relative to the 19S/0T bedrock. This finding formed the core justification for retracting the Tomato thesis.

---

### 2.2 Live Tournament Match Evidence: Seed 50186
In `research/live_loss_counterforensics_report.md:50`:
```markdown
| Episode ID | Our Submission | Opponent | Seed | Shop Combination | Our Cash | Opp Cash | Margin |
|---|---|---|---|---|---|---|---|
| **107564294** | 56146971 | Les 2 oies (`56149479`) | 50186 | BAKERY + BRUNCH | $45,862 | $92,580 | **-$46,718** |
```
In `scratch/run_closed_loop_comprehensive_suite.py:91`:
```python
{"ep": "107564294", "opp_name": "Les 2 oies (56149479)", "seed": 50186, "world": "BAKERY + BRUNCH"},
```
In `REPORT_INDEX.md:90, 95`:
```markdown
- **Seeds:** Live episode seeds (e.g. 50266, 50186, 50025, 50130)
- **Downstream Decision Impact:** Triggered the design of the Closed-Loop Liquidity Guard and dawn hiring priority arbitration.
```
- **Strategic Impact**: Seed 50186 was not merely simulated; its replay was forensically analyzed to discover the Day 12 hiring collapse and $800 liquidity cliff that defined the architecture of `ClosedLoopAgentV1` and `V2`.

---

### 2.3 Macro Census & Shop Extraction Evidence: All Seeds 50150–50199
In `scratch/census_phase3_500seeds.py:80-83, 190`:
```python
num_seeds = 500
start_seed = 50000
seeds = list(range(start_seed, start_seed + num_seeds)) # range(50000, 50500)
...
out_path = os.path.join(BASE_DIR, "results", "phase3_shop_census_500seeds.json")
```
In `scratch/find_pizza_pet_seeds.py:6`:
```python
for s in range(50000, 50200):
    g = kagsim.Game(s)
    for _ in range(144):
        g.step(...)
    shops = g.observe(0)['town']['unlocked_shops']
    if 'PIZZA_SHOP' in shops: pizza_seeds.append((s, shops))
    if 'PET_CAFE' in shops: pet_seeds.append((s, shops))
```
- **Filesystem Verification**: `results/phase3_shop_census_500seeds.json` was generated on **Thu Sep 10 23:52:16 2026** (size: 5,605 bytes, N=500 seeds).
- **Published Reference**: `reports/FULL_SPECTRUM_SHOP_ECONOMY_AND_META_FORENSICS_REPORT.md:21` cites:
  > *"Across 500 fresh CRN seeds (seeds 50000..50499) evaluated in parallel..."*
- **Forensic Finding**: All 50 seeds (50150 through 50199) were simulated in complete head-to-head matches between Dmitrii and V54++, and their town shop realizations were extracted and cataloged into project databases.

---

## 3. Seed-by-Seed Provenance Classification Table

Every seed in the proposed holdout cohort (50150–50199) is classified below under the four mandated categories:
- **`USED`**: Explicitly evaluated in strategy selection, parameter comparison, or counterforensic diagnostics.
- **`INDIRECTLY TOUCHED`**: Simulated or scanned in macro census/shop surveys (`census_phase3_500seeds.py`, `find_pizza_pet_seeds.py`), but not individually isolated for parameter tuning.
- **`UNUSED`**: Zero exposure across all files, logs, scripts, and databases.
- **`UNKNOWN`**: Unresolvable provenance.

| Seed | Classification | Underlying Artifacts | Specific Exposure Description |
| :---: | :---: | :--- | :--- |
| **50150** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50151** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50152** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50153** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50154** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50155** | **USED** | `scratch/test_phase16_generalization.py`, `scratch/generalization_matrix_results.json` | **Strategy Selection**: Evaluated V2 vs Tomato Specialist; drove Tomato retraction. |
| **50156** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50157** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50158** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50159** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50160** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50161** | **USED** | `scratch/test_phase16_generalization.py`, `scratch/generalization_matrix_results.json` | **Strategy Selection**: Evaluated V2 vs Tomato Specialist; drove Tomato retraction. |
| **50162** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50163** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50164** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50165** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50166** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50167** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50168** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50169** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50170** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50171** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50172** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50173** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50174** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50175** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50176** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50177** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50178** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50179** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50180** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50181** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50182** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50183** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50184** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50185** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50186** | **USED** | `research/live_loss_counterforensics_report.md:50`, `REPORT_INDEX.md:90` | **Live Tournament Episode 107564294**: Directly motivated Closed-Loop Liquidity Guard. |
| **50187** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50188** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50189** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50190** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50191** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50192** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50193** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50194** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50195** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50196** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50197** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50198** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |
| **50199** | **INDIRECTLY TOUCHED** | `scratch/census_phase3_500seeds.py`, `scratch/find_pizza_pet_seeds.py` | Simulated in 500-seed census; scanned for Pizza/Pet Cafe shops. |

---

## 4. Summary Statistics on Proposed Holdout Partition

```
================================================================================
HOLDOUT PROVENANCE SUMMARY (SEEDS 50150 - 50199)
================================================================================
Total Seeds Inspected:               50
USED (Direct Strategy Selection):     3 (Seeds 50155, 50161, 50186)
INDIRECTLY TOUCHED (Phase 3 Census): 47 (Remaining seeds in cohort)
UNUSED (Genuinely Virgin Seeds):      0 (0.0%)
UNKNOWN:                              0 (0.0%)
================================================================================
VIRGINITY RATE: 0 / 50 (0.0%)
CONTAMINATION STATUS: CONFIRMED CONTAMINATED
================================================================================
```

---

## 5. Remediation Protocol for a Truly Virgin Holdout

To resolve this holdout failure before pre-deployment testing:
1. **Abandon Seeds 50150–50199**: These seeds are compromised by historical simulation, shop logging, and explicit strategy comparison.
2. **Select Completely Unexplored Seed Space**: Any new holdout must be drawn from outside the entire `50000..50600` range (which was swept in `census_phase3_500seeds.py` and `test_phase16_generalization.py`), and outside historical validation ranges (`40000..40199`, `100..614`).
3. **Proposed Candidate Clean Range**: **Seeds 60000–60049** (50 seeds).
   - Preliminary grep confirmation: Zero occurrences of `60000..60049` in any script, log, or results file in the repository.
   - Must undergo pre-allocation provenance certification before designation.

---

## 6. Gate Decision Impact

Because holdout contamination is confirmed and includes explicit prior strategy selection on Seeds 50155, 50161, and 50186:

**VERDICT: BLOCKED (GATE 0.2 REQUIREMENT 2 FAILED)**
