md = """# Kagriculture Canonical Agent Registry

This document serves as the authoritative index of all candidate agents, production submissions, teammate integrations, and historical milestones developed throughout the Kagriculture project.

---

## 1. Master Agent Index

| Agent Name | Generation | Canonical Branch | Source Path | SHA256 (64-char) | Engine Spec | Status | Key Characteristics / Benchmark Notes |
| :--- | :---: | :---: | :--- | :--- | :---: | :---: | :--- |
| **Meta Fusion (Incumbent)** | **V49** | `main` | `candidates/v49_meta_fusion/main.py` | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` | 1.32.7 | **SUBMITTED** | **99.31% WR** (572W/4L). 2945 chassis + V44 CapEx + V48 route overrides + V49 E402 late seed-cap overlay. |
| **Meta Fusion Submission** | **V49** | `main` | `submissions/v49_meta_fusion_submission/main.py` | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` | 1.32.7 | **SUBMITTED** | Bit-exact production submission file. |
| **Vj Culture v24** | **V24** | `main` | `team_submissions/submission_Vj_kc_v24.tar.gz` | `4C9EF1DC189DE6185AFADE682CB8A758139390E4BAA8B6A010500443C75BD5CE` | 1.32.7 | **TEAM ELITE** | Best teammate submission; +500 cash margin over v27; room_guard, dead_stock, stranded wheat pickup fix. |
| **Vj Culture v27** | **V27** | `main` | `team_submissions/submission_Vj_kc_v27.tar.gz` | `EEE5AD4D7C67B27D7713E70B4B9E56220E92A8E8B90E6C59656A93ECE74B9A6C` | 1.32.7 | **TEAM BENCH** | Teammate variant; disabled guards caused -55.2 cash loss per match. |
| **V35 Production Agent** | **V35** | `main` | `final_submission/V35_FINAL_SUBMISSION.tar.gz` | `9D2DB0C688E127BA3526008BBE08D09B28FBFE389D11A8FADA16606EC1ADC9FA` | 1.32.7 | **HISTORIC** | Mid-competition milestone; A7 opening wash controller. |
| **V35 Standalone Main** | **V35** | `main` | `submission_final_v35/main.py` | `92B29C3CE75F2306D9B61803457404032FCD4CA1129F19E1AD0107E018F35F44` | 1.32.7 | **HISTORIC** | Decompressed V35 agent file. |
| **Challenger C1** | **V24** | `culture/v24` | `candidates/challenger_c1.py` | `0390922...` | 1.32.7 | **ARCHIVED** | Idle zeroing challenger in Culture v24 campaign. |
| **Challenger C2** | **V24** | `culture/v24` | `candidates/challenger_c2.py` | `0390922...` | 1.32.7 | **ARCHIVED** | Livestock scale challenger in Culture v24 campaign. |
| **Challenger C3** | **V24** | `culture/v24` | `candidates/challenger_c3.py` | `0390922...` | 1.32.7 | **ARCHIVED** | Carrot compound challenger in Culture v24 campaign. |
| **Planner P1 Macro** | **V25** | `culture/v25` | `candidates/v25_p1_macro.py` | `e4eb8a4...` | 1.32.7 | **ARCHIVED** | Macro planner in Culture v25 campaign. |
| **Planner P2 Macro** | **V25** | `culture/v25` | `candidates/v25_p2_macro.py` | `e4eb8a4...` | 1.32.7 | **ARCHIVED** | Option-level planner in Culture v25 campaign. |
| **Planner P3 Macro** | **V25** | `culture/v25` | `candidates/v25_p3_macro.py` | `e4eb8a4...` | 1.32.7 | **ARCHIVED** | Unified labor/capital planner in Culture v25 campaign. |
| **Dead Action Guard** | **V50** | `main` | `candidates/v50_dead_action_guard/main.py` | `E3DC43B55EB0C7450CBE14A9EF212AE67B8E37E5C286B757834F259E66F1C80E` | 1.32.7 | **REJECTED** | Evaluated fertilizer buyback suppression; starved late crop payouts. |
| **Blocked Action Repair** | **V51** | `main` | `candidates/v51_blocked_repair/main.py` | `1F0E92228642578CBF50885EA307707D317C826616498AF36ABF5EFE41A6795C` | 1.32.7 | **REJECTED** | Replay buffer for weed repair; 0 firings across 92,000 steps. |
| **Elite Transfer 2945** | **V47** | `main` | `candidates/v47_elite_transfer/main.py` | `8872E991DCAF28BC833A8428350F9B515046A9066F623F9D7AFBA785E4CAD47F` | 1.32.7 | **MILESTONE** | Foundation of modern 2945 chassis transfer. |
| **Challenger Route B** | **V48** | `main` | `candidates/v48_challenger/main.py` | `F8D13866C1204DA04D5B8E7B73477D714F031F00C637B5B557FE8E2A45299BA1` | 1.32.7 | **MILESTONE** | Introduced surgical shop-route 105 overrides for 3 shop pairs (+0.74 alpha). |
| **Economic Portfolio** | **V44** | `main` | `candidates/v44_economic_portfolio/main.py` | `58FDE86583A64689994AE26CDA8DD050B0A05ACE769C173042FCD76FB9BA34DF` | 1.32.7 | **MILESTONE** | Discovered step >= 520 CapEx cutoff rule. |
| **Compositional Alpha** | **V43** | `main` | `candidates/v43_compositional_alpha/main.py` | `281ACD6961CC4172133483014FC2A47AA51341102B02FFBDCA9598CB44A92D02` | 1.32.7 | **MILESTONE** | Multi-step micro-alpha composition. |
| **Alpha Residual** | **V42** | `main` | `candidates/v42_alpha_residual/main.py` | `0B90784AFC8CFC66D3A947448E99CE796E5286C3E0D70F4A85B593141B24F296` | 1.32.7 | **MILESTONE** | Staggered endgame liquidation bounds. |
| **Safe Residual RL** | **V41** | `main` | `candidates/v41_safe_residual/main.py` | `3A28F422FBF3E0151912FDE078534315D2C2764156CD48DBF29E6334A817D5F3` | 1.32.7 | **RESEARCH** | Counterfactual offline residual RL testbed. |
| **Recurrent Macro RL** | **V40** | `main` | `candidates/v40_recurrent_macro/main.py` | `3F87FA2C5C24A4F29EE3F9DD16BDE9B2192B7326ECF2EFD321C07BF17F6D9E5B` | 1.32.7 | **RESEARCH** | FastKagricultureSim (500+ SPS) PPO/GRU macro controller. |
| **A7 Standalone** | **V30** | `main` | `candidates/v30_a7_standalone/main.py` | `51C1D25245F68DD8DE66B355F2AD6CA1D79DE8AF02EFED521A5A82F7BE69CE3F` | 1.32.7 | **HISTORIC** | Standalone A7 candidate baseline. |
| **Root Evaluation Wrapper** | **Root** | `main` | `main.py` | `8315D67063BC065672529156ADC3C8083FB61C3DA6D17CABDE186D6B46A58B3F` | 1.32.7 | **UTILITY** | Packed simulation runner and telemetry probe. |

---

## 2. Integrity Verification
All SHA256 checksums are computed using standard cryptographic SHA-256 (`hashlib.sha256(data).hexdigest().upper()`) on normalized binary representations.
"""

with open(r"C:\Users\Sundareswaran\Kagriculture\docs\AGENTS.md", "w", encoding="utf-8") as f:
    f.write(md)

print("Created docs/AGENTS.md successfully.")
