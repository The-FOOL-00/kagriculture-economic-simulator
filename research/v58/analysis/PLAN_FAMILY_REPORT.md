# V58 Plan Family Report

Each plan = one executable elite route (S10), reconstructed by in-sim capture
rather than by copying tapes: the plan library IS the agent set, characterized
by [V49_VS_ELITE.json](V49_VS_ELITE.json). Plans A-J below; V49 is the fallback.

| Plan | Agent | Lineage | Day-0 | End herd | Land | Wash | Capture bank |
|------|-------|---------|-------|----------|------|------|--------------|
| A | thomastschinkel_2945 | Sept wash family | 2C/2S W7/M12 | 6C/6S | d6 | yes | 79,400 |
| B | dmitrii_lb2800 | Sept wash family | 2C/2S W7/M12 | 8C/6S | d6 | yes | 70,313 |
| C | kaitofukami_v48_3009 | Sept fast-route | 4S W5/M7 | 11C/4S | d6 | no | 86,885 |
| D | saiteja_mega_3000 | Sept router | 3C/1S M7/W10 | 6C/1S | d7 | partial | 67,325 |
| E | tetsutani_pasture | Sept pasture | 2C/2S W7/M12 | 0/0 (liq.) | d6 | partial | 65,722 |
| F | indarkarhana_top10 | Sept pasture | 2C/2S W7/M12 | 10C/4S | d6 | partial | 62,241 |
| G | P3090_claimed | Aug F5 (exact) | 4S/1C W5/M5 | 9C/4S | d6 | no | 119,859 |
| H | P3000_claimed | Aug F4 (exact) | 4S/1C W5/M5 | 8C/4S | d6 | no | 114,974 |
| I | night_harvest | Aug F2 (exact) | 2C/2S W7/M12 | 8C/6S | d7 | no | 48,014 |
| J | v44_economic_portfolio | conditional | regime-gated | — | — | — | 3,000 (off-regime) |
| — | V49 (fallback) | Sept wash family | 2C/2S W7/M12 | 12C/5S | d6 | yes | 174,760 |

Quality rule (§31) applied:

- Multi-player support: A/B (family-shared census), G/H/I (hash families with
  13-80 elite seats across 9-26 teams). C-F are single-lineage September
  routes (each its author's public submission; no hash population).
- Multi-seed: capture 2 seeds + tournament 20 seeds (see PLAN_TOURNAMENT.json).
- Mechanism understood: wash engine (A/B/V49), fast micro-sales (C), tape
  fossils (G/H/I). D/E/F carry execution leaks (2-quad end, herd liquidation).
- Deterministic: all execute deterministically (seat-mirrored scores identical
  in capture).
- No hidden information: all run on callback-visible state only.

Plans G/H/I fail the current-meta relevance gate (Gate G): exact August lines,
superseded. Plans D/E/F fail the mechanism gate (leaks, no alpha hypothesis).
Plan J fails the strategy gate (V56: queue artifact, off-regime no-op).
Plans A/B/C survive to the tournament as the only candidates with a live
hypothesis (herd-mix gradient A/B; regime tape C).
