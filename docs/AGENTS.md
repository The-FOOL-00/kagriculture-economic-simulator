# Kagriculture Canonical Agent Registry

This document serves as the authoritative, definitive index of all candidate agents, production submissions, teammate integrations, and historical milestones developed throughout the Kagriculture project.

---

## 1. Master Agent Registry (V24 – V60)

| Agent Identifier | Version / Role | Branch / Location | Canonical File Path | SHA256 Checksum (64-char Hex) | Status | Key Characteristics / Benchmark Performance |
| :--- | :---: | :---: | :--- | :--- | :---: | :--- |
| **Meta Fusion (Incumbent)** | **V49** | `main` | `candidates/v49_meta_fusion/main.py` | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` | **SUBMITTED** | **99.31% WR** (572W / 4L / 0T). 2945 chassis + V44 CapEx cutoff + V48 route overrides + V49 E402 late seed-cap overlay. |
| **Meta Fusion Production** | **V49** | `main` | `submissions/v49_meta_fusion_submission/main.py` | `8CAFF63068BF68A34A9141D48F771D9007AFC0DFA792179A737ECCE919FBBD11` | **SUBMITTED** | Bit-exact copy of submitted production script. |
| **Meta Fusion Zip Bundle** | **V49** | `main` | `submissions/v49_meta_fusion_20260929_2212.zip` | `37F10DEE73C7E01BE1FE240FBFC5344F254D2FE29FB0764FB14B2C69AB99306D` | **SUBMITTED** | Official zipped bundle submitted to Kaggle platform. |
| **Vj Culture v24** | **V24** | `main` | `team_submissions/submission_Vj_kc_v24.tar.gz` | `4C9EF1DC189DE6185AFADE682CB8A758139390E4BAA8B6A010500443C75BD5CE` | **TEAM ELITE** | Best teammate submission; +500 cash margin over v27; room_guard, dead_stock, stranded wheat pickup fix. |
| **Vj Culture v27** | **V27** | `main` | `team_submissions/submission_Vj_kc_v27.tar.gz` | `EEE5AD4D7C67B27D7713E70B4B9E56220E92A8E8B90E6C59656A93ECE74B9A6C` | **TEAM BENCH** | Teammate variant; disabled guards caused -55.2 cash loss per match. |
| **Challenger C1** | **V24** | `culture/v24` | `candidates/challenger_c1.py` | `D20CFD614A613D120757CF4698EA3311B02116C07ED1D26F8CED66C5FB7604EF` | **ARCHIVED** | Idle zeroing challenger in Culture v24 campaign. |
| **Challenger C2** | **V24** | `culture/v24` | `candidates/challenger_c2.py` | `7AF08A7775FB41A61D165B07C3D89E174565CFB6740E25F1ED37F2B50696C2DA` | **ARCHIVED** | Livestock scale challenger in Culture v24 campaign. |
| **Challenger C3** | **V24** | `culture/v24` | `candidates/challenger_c3.py` | `C15C40D6DD6539A19669C3460F3DE0759BBF39D57EA11D2DB46E74850FE3854A` | **ARCHIVED** | Carrot compound challenger in Culture v24 campaign. |
| **Planner P1 Macro** | **V25** | `culture/v25` | `candidates/v25_p1_macro.py` | `7F605723BA1C48DD14628C1B3932D07478461F59FE0890A69AC971E3FEB17512` | **ARCHIVED** | Macro planner in Culture v25 campaign. |
| **Planner P2 Options** | **V25** | `culture/v25` | `candidates/v25_p2_production.py` | `3C6847758227D66FC2D11750FE44DDC543E617FCEF13B7673F86160DF0CAAE7D` | **ARCHIVED** | Production options planner in Culture v25 campaign. |
| **Planner P3 Unified** | **V25** | `culture/v25` | `candidates/v25_p3_unified.py` | `13292582C8CC796BC11CCEBFF9684FBEC45CFB97D936FB9E85E4E9BB4DBEA179` | **ARCHIVED** | Unified labor/capital planner in Culture v25 campaign. |
| **Economic Portfolio** | **V44** | `main` | `candidates/v44_economic_portfolio/main.py` | `57F974D397E52521E9055A2E4C67E852A8C856562D208C0472997D57413D7EFE` | **MILESTONE** | Discovered the critical **Step >= 520 CapEx Cutoff Rule** saving thousands in stranded capital. |
| **Adversarial Market** | **V45** | `main` | `candidates/v45_adversarial_market/main.py` | `87095976D167992A711EA5AA29860386484A76F9F75D02A1628585863BC3A4E4` | **RESEARCH** | Opponent market pressure model with AUROC 0.94. |
| **Adaptive Macro** | **V46** | `main` | `candidates/v46_adaptive_macro/main.py` | `7B8632F64DB04654B331C3247587BEC4D5C641515762AC8AC2201ED2AC9D7338` | **RESEARCH** | Macro-route diversity selector. |
| **Elite Transfer 2945** | **V47** | `main` | `candidates/v47_elite_transfer/main.py` | `8872E991DCAF28BC833A8428350F9B515046A9066F623F9D7AFBA785E4CAD47F` | **MILESTONE** | Foundational port of public 2945 chassis (Hayashi/Tschinkel lineage). |
| **Challenger Route B** | **V48** | `main` | `candidates/v48_challenger/main.py` | `F8D13866C1204DA04D5B8E7B73477D714F031F00C637B5B557FE8E2A45299BA1` | **MILESTONE** | Surgical shop-route 105 overrides for 3 shop pairs (+0.74 alpha). |
| **Dead Action Guard** | **V50** | `main` | `candidates/v50_dead_action_guard/main.py` | `E3DC43B55EB0C7450CBE14A9EF212AE67B8E37E5C286B757834F259E66F1C80E` | **REJECTED** | Evaluated fertilizer buyback suppression; starved late crop payouts. |
| **Blocked Action Repair** | **V51** | `main` | `candidates/v51_blocked_repair/main.py` | `1F0E92228642578CBF50885EA307707D317C826616498AF36ABF5EFE41A6795C` | **REJECTED** | Replay buffer for weed repair; 0 firings across 92,032 steps. |
| **Herd Swap Testbed** | **V52** | `main` | `research/v52/benchmarks/run_v52_fresh_ladder.py` | `4E95C337D566B3F0E6D8F8F99D95B6A820E9AA9B185D966B2F57816B3EC5D4C9` | **REJECTED** | Herd composition swapping caused shed bottleneck saturation. |
| **Engine Parity Harness** | **V53** | `main` | `research/v53/benchmarks/run_v53_grand_ladder.py` | `BC50D73D55A6CD3769D9AA69046E3A526E69D8408B1B6BA752B2FA2BE3F9473D` | **VERIFIED** | Bit-exact engine parity revalidation with `kaggle-environments 1.32.7`. |
| **CMS5 State Reconstruction** | **V54** | `main` | `candidates/cms5_v54_faithful.py` | `7E7C5CA37F31D3F106290A88CAD1526FCD77EBE53387993C9B71015DA77D7069` | **RESEARCH** | Mathematical boundary of opponent predictability from public observations. |
| **Teammate V54 H3Q4** | **V54** | `main` | `external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py` | `EF9B77603D1110126A133F972CA2155AA124A30FA3639F2F166664E0BA3361FE` | **TEAM ELITE** | Teammate V54 H3Q4 variant agent. |
| **V55 Blocked Action** | **V55** | `main` | `research/v55/candidates/v55_blocked_action/main.py` | `35B791FC0AFB2A7717BFBC18FDABA8B604C301DC38CF4156F1E2C587C91AEB36` | **REJECTED** | Dynamic adaptation candidate. |
| **V55 Post-Reveal Shop** | **V55** | `main` | `research/v55/candidates/v55_post_reveal_shop/main.py` | `3E41C785A8403784E5351C088680F8F706D3B595EFBA812AB6E34992F844DAA6` | **REJECTED** | Post-reveal route swapping dropped WR to 78.65% due to inventory desync. |
| **Forensic 4-Loss Autopsy** | **V56** | `main` | `research/tools/deep_forensic_four_losses.py` | `95E4029279BD3825E999E7586522302FE0AA384EB0FAFA8CD98EF53A6220E154` | **DIAGNOSTIC** | Forensic autopsy proving step 697 market queue collision mechanics. |
| **Market Queue Optimizer** | **V57** | `main` | `research/final_synthesis/FINAL_DECISION_LEDGER.md` | `CC3F2C37D45183389A53D94BE20C737E58045FCE4862413158B936F3DA8E4F8B` | **VERIFIED** | Proved V49 queue ordering is Pareto-optimal; interventions harmed control seeds. |
| **August Replay Reconstruct** | **V58** | `main` | `research/v58/analysis/` | `88A01FE0...` | **BENCHMARK** | Benchmark against August 3100+ meta; V49 achieved 400/400 wins (100% WR). |
| **September Meta Acquisition** | **V59** | `main` | `research/v59/` | `B1209AF3...` | **RESEARCH** | Replay acquisition pipeline for late September meta. |
| **Curve Counter Challenger** | **V60** | `main` | `external_repos/kaggriculture-v66-agent/candidate_v60_curve_counter.py` | `C82697ED2C868148BD84B5737D034E25461B65E65B211835037BD8BAADD4926C` | **RESEARCH** | Late recovery curve counter agent candidate. |

---

## 2. Cryptographic Integrity Standard

All checksums are 64-character uppercase hexadecimal strings computed via SHA-256 (`hashlib.sha256(open(path, 'rb').read()).hexdigest().upper()`) on normalized binary representations.
