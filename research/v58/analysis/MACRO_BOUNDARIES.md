# V58 Macro Boundaries

Family = exact action-stream identity through turn N (S3 hashes).
F1 (dominant elite route) splits after turn 100:

- h100 b6092398b75bdf7b: n=258 -> 7 distinct h200 sub-routes (top3: ['37f58efcx243', '23eaab8dx8', 'c83101c2x3'])
- h100 44c973c075570f2a: n=80 -> 8 distinct h200 sub-routes (top3: ['45fe2ad8x67', '1cbcc2a6x4', 'f5c2ed8fx2'])
- h100 14d879ad45aeff5b: n=40 -> 2 distinct h200 sub-routes (top3: ['9320586dx39', '9da454b2x1'])
- h100 92f69b53ed03cb15: n=15 -> 13 distinct h200 sub-routes (top3: ['e3e145bex3', '06706dd4x1', '5b79489fx1'])
- h100 e6651fba348a3438: n=13 -> 4 distinct h200 sub-routes (top3: ['d9141cacx9', 'd929041cx2', '583f443fx1'])
- h100 389790f3d64fd9de: n=10 -> 3 distinct h200 sub-routes (top3: ['6ab72354x8', 'e8360303x1', '1306313ax1'])
- h100 d11ac0583bf176c8: n=6 -> 3 distinct h200 sub-routes (top3: ['7ad85593x4', '1edef455x1', 'a876f19ex1'])
- h100 093e01b2807546d8: n=6 -> 1 distinct h200 sub-routes (top3: ['af6de9d7x6'])
- h100 0d95b4cc2e4dc9c1: n=6 -> 4 distinct h200 sub-routes (top3: ['c73b8293x3', '7fc668e1x1', '0c52e2acx1'])
- h100 23db3943221029eb: n=5 -> 4 distinct h200 sub-routes (top3: ['d1c13e3ex2', 'b93554bax1', '3d2481f2x1'])
- h100 97868990f2d1f0ac: n=4 -> 3 distinct h200 sub-routes (top3: ['ff374fd8x2', '8a90ed69x1', '3b1cd8cex1'])
- h100 4d602f1134d8e175: n=3 -> 1 distinct h200 sub-routes (top3: ['1fb37318x3'])

Executable-agent hash placement vs elite families:

- P3000_claimed: h100_in_elite=True (elite_n=15, all_n=4036) h200_in_elite=True (elite_n=3)
- P3090_claimed: h100_in_elite=True (elite_n=13, all_n=16292) h200_in_elite=True (elite_n=9)
- dmitrii_lb2800: h100_in_elite=False (elite_n=0, all_n=0) h200_in_elite=False (elite_n=0)
- indarkarhana_top10: h100_in_elite=False (elite_n=0, all_n=66) h200_in_elite=False (elite_n=0)
- kaitofukami_v48_3009: h100_in_elite=False (elite_n=0, all_n=4522) h200_in_elite=False (elite_n=0)
- night_harvest: h100_in_elite=True (elite_n=80, all_n=9704) h200_in_elite=True (elite_n=1)
- saiteja_mega_3000: h100_in_elite=False (elite_n=0, all_n=4) h200_in_elite=False (elite_n=0)
- tetsutani_pasture: h100_in_elite=False (elite_n=0, all_n=0) h200_in_elite=False (elite_n=0)
- thomastschinkel_2945: h100_in_elite=False (elite_n=0, all_n=0) h200_in_elite=False (elite_n=0)
- v44: h100_in_elite=False (elite_n=0, all_n=3) h200_in_elite=False (elite_n=0)
- v49: h100_in_elite=False (elite_n=0, all_n=0) h200_in_elite=False (elite_n=0)

## Decision-boundary reading
Turn-100 identity already separates the two macro crop routes (24/42/108@land7 vs 19/37/143@land6); turn-200 identity splits execution variants within a macro route. A safe macro selector would therefore have to commit no later than ~turn 100 (day 4) to change macro route — but the captured executables show routes are committed at step 0 (tapes).
