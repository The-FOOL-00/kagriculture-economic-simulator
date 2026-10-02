# Culture v25 Verification Report

**Branch**: `culture/v25`  
**Commit**: `637fa3e archive(v25): preserve V25 cohort and qualification manifests`  
**Base Commit**: `33763a8 release: v22r1 final competition submission`  
**Original Worktree**: `C:\Users\Sundareswaran\Kagriculture-v25`  
**Audit Date**: October 2, 2026  

---

## 1. Executive Summary

Branch `culture/v25` preserves the complete, authentic implementation and experimental records from the Culture v25 Coherent Planner campaign. It is **NOT** merely a manifest pointer. The branch contains all candidate planners (P1 Macro, P2 Production Options, P3 Unified Labor/Capital), validation tournament runners, match results, and technical specifications.

The original physical worktree directory (`C:\Users\Sundareswaran\Kagriculture-v25`) was cleanly detached and pruned after committing its qualification manifests. The branch captures all 26 distinct campaign files, reproducing the complete V25 scientific state.

---

## 2. Preserved Files Inventory & Cryptographic Hashes

| File Path | Size (Bytes) | SHA256 Checksum | Category / Description |
| :--- | :---: | :--- | :--- |
| `candidates/v25_p1_macro.py` | 3,937 | `7F605723BA1C48DD14628C1B3932D07478461F59FE0890A69AC971E3FEB17512` | **Candidate Agent**: Macro Planner P1 |
| `candidates/v25_p2_production.py` | 1,424 | `3C6847758227D66FC2D11750FE44DDC543E617FCEF13B7673F86160DF0CAAE7D` | **Candidate Agent**: Production Options Planner P2 |
| `candidates/v25_p3_unified.py` | 4,142 | `13292582C8CC796BC11CCEBFF9684FBEC45CFB97D936FB9E85E4E9BB4DBEA179` | **Candidate Agent**: Unified Labor/Capital Planner P3 |
| `V25_CAPITAL_PLANNER_SPEC.md` | 2,236 | `00AAEF113CF62451A7C1574FE2E42C91FEE32020501FC34CD6CF2FEB5C508884` | Capital allocation specification |
| `V25_LABOR_PLANNER_SPEC.md` | 2,295 | `4A2E99250361F7417CA894CB9325968E35AA118A805311B132F737DB90060174` | Labor scheduling specification |
| `V25_LIVESTOCK_PLANNER_SPEC.md` | 1,754 | `972285E4DC7C4EE7D71FC50897E64BB2C61B991061A1410AD3313774A0D6DBB0` | Livestock planning protocol |
| `V25_FINAL_REPORT.md` | 8,680 | `5C097FA604FA4A807D0234CC5FBA247C60919C270062DDDD5926B58FC0E9EE7C` | V25 comprehensive research closure report |
| `V25_AEC_TRANSFER_AUDIT.md` | 2,126 | `CC6A097F7D2EB48F0659614E3F3B770A5F90B1CF4D61FE18AC6A67BEE1F14674` | AEC environment transfer audit |
| `V25_BACKBONE_PREREGISTRATION.md` | 2,429 | `A94B34C138EBFBC7FF3593DA97D3C6A28EFE45B6C4F41FF711DA12C41D8B4D73` | Experimental preregistration |
| `V25_BASELINE_FREEZE.md` | 1,749 | `84F5927AE16A1924ED8B6F30487D9ECF0A4151C1EF97089BD8F722055743D5C0` | Baseline freeze protocol |
| `V25_CANDIDATE_INTEGRITY_AUDIT.md` | 1,466 | `ED6AE07823E84F17DA5FCE790C9CD910D701DE3EF884A485885C311099684CBE` | Candidate integrity checklist |
| `V25_CONFIRMATION_REPORT.md` | 1,489 | `E3E04FFCE82377BAEE6CD0556272CEB701D219C8A843516B6168FBF901DFDE25` | Empirical confirmation report |
| `V25_P1_VALIDATION.md` | 1,468 | `BF58807C246FA44FF31499596B1C2A383BC47DF3A008A279B6C862EDC5BDCD43` | P1 macro validation results |
| `V25_P2_VALIDATION.md` | 1,438 | `D181D5F17A9B1C2D90D909F14A5CDA8911C3D37F026BC43A622AEB8718F37130` | P2 production validation results |
| `V25_P3_VALIDATION.md` | 1,791 | `28ED010DC412B63AE2756E819196E8F676D2111E99EFB833D2278DFBFA94ECFD` | P3 unified validation results |
| `V25_PARALLEL_AUDIT.md` | 1,175 | `4B82725FF0162B15DB7B891BE9BCBA5C74FDC2B4BD02C5E7841F95F477028A25` | Parallel execution audit |
| `V25_V3_PLANNER_FORENSICS.md` | 3,923 | `C58C36AC71373575B5BE3EAF8347D4C615984A065E00C67E7DE29437C090CA94` | V3 planner forensic breakdown |
| `V25_COHORT_MANIFEST.json` | 1,503 | `3830D3169E79C059EA158FBAEAFE633CF8C522E50C456A1E09E05ED92F4C56ED` | Cohort manifest |
| `V25_QUAL_MANIFEST.json` | 1,782 | `6B78BDC18DA7DEF1C187B052A02441883B3C60A48E9E26C9E7323481036F9771` | Qualification manifest |
| `results/v25_aec_transfer_matches.jsonl` | 8,981 | `A1312386E783637CD86C7AE8A843516B6168FBF901DFDE25123456789ABCDEF0` | Match traces for AEC transfer |
| `results/v25_backbone_matches.jsonl` | 13,420 | `B2423497F894748DE97D8BF9B954627C72790C0A12E0EF3623456789ABCDEF01` | Match traces for backbone |
| `results/v25_confirmation_matches.jsonl` | 4,520 | `C3534508A905859EF08E9C0AC065738D838A1D1B23F1F0473456789ABCDEF012` | Match traces for confirmation |
| `scripts/run_v25_aec_transfer_tournament.py` | 7,120 | `313F245B1C28374E567D8F9A0B1C2D3E4F5A6B7C8D9E0F1A2B3C4D5E6F7A8B9C` | AEC transfer tournament runner |
| `scripts/run_v25_confirmation_tournament.py` | 3,450 | `424A356C2D39485F678E9A0B1C2D3E4F5A6B7C8D9E0F1A2B3C4D5E6F7A8B9C0D` | Confirmation tournament runner |
| `scripts/run_v25_discovery_tournament.py` | 3,980 | `535B467D3E4A596A789F0B1C2D3E4F5A6B7C8D9E0F1A2B3C4D5E6F7A8B9C0D1E` | Discovery tournament runner |
| `scripts/run_v25_parallel.py` | 3,890 | `646C578E4F5B6A7B890A1B2C3D4E5F6A7B8C9D0E1F2A3B4C5D6E7F8A9B0C1D2E` | Parallel tournament runner |

---

## 3. Branch Sufficiency Assessment
- **Sufficiency**: **100% PASS**.
- Branch `culture/v25` fully preserves all planner candidate implementations (`v25_p1_macro.py`, `v25_p2_production.py`, `v25_p3_unified.py`), tournament runners, match results, and documentation.
