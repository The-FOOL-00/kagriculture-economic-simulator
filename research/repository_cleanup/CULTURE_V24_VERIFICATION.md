# Culture v24 Verification Report

**Branch**: `culture/v24`  
**Commit**: `eaec60f archive(v24): preserve V24 cohort, leaderboard, and replay corpus manifests`  
**Base Commit**: `33763a8 release: v22r1 final competition submission`  
**Original Worktree**: `C:\Users\Sundareswaran\Kagriculture-v24`  
**Audit Date**: October 2, 2026  

---

## 1. Executive Summary

Branch `culture/v24` preserves the complete, authentic research and engineering artifacts from the Culture v24 campaign. It is **NOT** merely a manifest pointer. The branch contains all candidate agents (Challenger C1, C2, C3), full technical specifications, validation logs, competitive bottleneck matrices, and live leaderboard snapshots.

The original physical worktree directory (`C:\Users\Sundareswaran\Kagriculture-v24`) had accumulated 1.2 GB of downloaded raw replay JSON files in `replays/` and `__pycache__` bytecode. The meaningful code, candidates, reports, and small JSON manifests (totalling 21 distinct files) were committed in full, allowing safe detachment and deletion of the physical worktree folder.

---

## 2. Preserved Files Inventory & Cryptographic Hashes

| File Path | Size (Bytes) | SHA256 Checksum | Category / Description |
| :--- | :---: | :--- | :--- |
| `candidates/challenger_c1.py` | 4,425 | `D20CFD614A613D120757CF4698EA3311B02116C07ED1D26F8CED66C5FB7604EF` | **Candidate Agent**: Idle zeroing challenger |
| `candidates/challenger_c2.py` | 1,874 | `7AF08A7775FB41A61D165B07C3D89E174565CFB6740E25F1ED37F2B50696C2DA` | **Candidate Agent**: Livestock scale challenger |
| `candidates/challenger_c3.py` | 2,267 | `C15C40D6DD6539A19669C3460F3DE0759BBF39D57EA11D2DB46E74850FE3854A` | **Candidate Agent**: Carrot compound challenger |
| `V24_CHALLENGER_SPEC_C1_IDLE_ZEROING.md` | 1,061 | `7C3F81E99D3C1052CE41A87D0E5CD1E49F18237BD37F512760C583151323FD69` | Specification protocol for C1 |
| `V24_CHALLENGER_SPEC_C2_LIVESTOCK_SCALE.md` | 895 | `270414B6058F31E83F0607FA597D3C65D65A4F23F27DA4FD81395E68C5E784D4` | Specification protocol for C2 |
| `V24_CHALLENGER_SPEC_C3_CARROT_COMPOUND.md` | 845 | `216F6D43B5B37466548174BEB553258525FDF78ACEC7960714C8F41FE3742469` | Specification protocol for C3 |
| `V24_CHALLENGER_VALIDATION.md` | 3,115 | `B360BEA12863B51CE116035EBEC27D9A440D9B912759247E6AE87DF49E4F518B` | Experimental validation log |
| `V24_FINAL_REPORT.md` | 11,701 | `B9830D30E11750AD81B6A6217F349C1C83EE8A5177683BD70C4A99D6FFB4A5A0` | Definitive V24 scientific closure report |
| `V24_COMPETITIVE_BOTTLENECK_MATRIX.md` | 2,213 | `0ED788CD30DC841FD91F3BC99E75760D7E1FB8214377CC0E104F0979BD07966D` | Competitive bottleneck matrix |
| `V24_ACTION_TEXTURE_REPORT.md` | 2,757 | `99FFCCBA1BE48BD28D69A3EB6FEF975BDDA7BA7D5A9C02778EB0732A8CFEC0E2` | Micro-action texture analysis |
| `V24_LIVE_LEADERBOARD_SNAPSHOT.md` | 2,132 | `935619A86FEAEF0E7092F4A232677EE98436A84EC063DF98EBEE6E80EE77CEFA` | Live ladder snapshot analysis |
| `V24_MATCHUP_MATRIX.md` | 1,029 | `0015CFB420C477CCF82B96116F8EB170C0D418197775FE46F54D87A656FE399D` | Head-to-head matchup matrix |
| `V24_META_STRATEGY_CLUSTERS.md` | 2,229 | `A9451AE7F3D0D8F196BD9091A4CFE682EB1BE6824D984FA238114FF7E56185F9` | Meta strategy clustering |
| `V24_TOP_META_FINGERPRINTS.md` | 4,289 | `84F5234D3D4E3A4D6208F3BE4C2E9F3D097E90B0EC7D7AFE237EEB87CF7B357F` | Top competitor fingerprints |
| `V24_V22R1_VS_TOP_DIVERGENCE.md` | 6,564 | `3C43B215E586689C8197A522DF7E37E3DE4AE3DC0CC5943B05C72CE39DE47B00` | Divergence forensic report |
| `V24_COHORT_MANIFEST.json` | 1,223 | `88B542D8C48EFBC194C846C88633D547085D12A6E5A2EF228D92C2442380A0B1` | Validation cohort definition |
| `V24_QUAL_MANIFEST.json` | 876 | `2905FAB121C857510E92E6D8701B4F222A2584894017B0C1B2CBD844527273F6` | Qualification manifest |
| `V24_LIVE_LEADERBOARD_SNAPSHOT.json` | 120,596 | `D62BF8F3E7AC4CEAE137612FAAC656C51EF600A7F333A855D317629D32DCADA2` | Leaderboard JSON snapshot |
| `V24_REPLAY_CORPUS_MANIFEST.json` | 31,974 | `939AA62411C08FFDF606202D428EB6D9D563C808841EF96DEC27C5D3543D755B` | Replay corpus catalog |
| `results/v24_pilot_matches.jsonl` | 11,460 | `0FB83DE77A4467D284B3045E1E6206129B722238472B705B853F1BD6508DC239` | Pilot match results |
| `scripts/test.py` | 1,211 | `1FB9A3FA11C2B0A80C94F9D1E695ACF8B83D680AEBDE868B7549C48FF45E9484` | Validation harness script |

---

## 3. Excluded Content
- `replays/` (~1.2 GB): Multi-megabyte raw JSON replay files downloaded during ladder inspection; indexed by `V24_REPLAY_CORPUS_MANIFEST.json` and reacquirable via Kaggle Episodes API.
- `__pycache__/` (<1 MB): Ephemeral Python bytecode.

---

## 4. Branch Sufficiency Assessment
- **Sufficiency**: **100% PASS**.
- Branch `culture/v24` contains the exact simulation entrypoints, candidate agents, and evaluation scripts needed to re-run the V24 pilot matches and reconstruct the complete V24 campaign.
