# V58 V49 vs Elite Comparison

Method: [compare_v49_elite.py](compare_v49_elite.py) +
in-sim capture ([capture_trajectories.py](capture_trajectories.py), engine 1.32.7,
discovery seeds 10000-10001, 44 games, 44/44 captured).
Numbers: [V49_VS_ELITE.json](V49_VS_ELITE.json).

## Difference matrix (medians; families = Aug elite h100; executables = 1.32.7 capture)

| Lever | V49 | F1 | F2 | F3-F6 | kaito3009 | saiteja3k | t2945 | tetsu | indar | dmitrii | P3090 | P3000 | nharv |
|-------|----:|---:|---:|------|----------:|---------:|------:|------:|------:|--------:|------:|------:|------:|
| crew peak | 13 | 14 | 14 | 14 | 15 | 12 | 12 | 12 | 12 | 11 | 14 | 14 | 14 |
| hires | 266 | 263 | 277 | 262 | 282 | 303 | 266 | 282 | 291 | 260 | 262 | 263 | 277 |
| tiles | 239 | 174 | 158 | 199 | 206 | 131 | 239 | 240 | 243 | 239 | 199 | 199 | 158 |
| melon | 12 | 24 | 24 | 19 | 11 | 21 | 12 | 12 | 12 | 12 | 19 | 19 | 24 |
| straw | 33 | 42 | 42 | 37 | 41 | 44 | 33 | 33 | 38 | 33 | 37 | 37 | 42 |
| wheat | 163 | 108 | 92 | 143 | 134 | 66 | 147 | 164 | 187 | 163 | 143 | 143 | 92 |
| carrot | 49 | 0 | 0 | 0 | 20 | 0 | 55 | 31 | 6 | 31 | 0 | 0 | 0 |
| land day | 6 | 7 | 7 | 6 | 6 | 7 | 6 | 6 | 6 | 6 | 6 | 6 | 7 |
| end herd | 12C/5S | ? | ? | ? | 11C/4S | 6C/1S | 6C/6S | 0/0 | 10C/4S | 8C/6S | 9C/4S | 8C/4S | 8C/6S |
| bank (cap) | 174,760 | 88k | 121k | 77-82k | 86,885 | 67,325 | 79,400 | 65,722 | 62,241 | 70,313 | 119,859 | 114,974 | 48,014 |

(Bank is cross-patch/cross-opponent; never compare raw across columns — see §36.)

## Structural reads

1. **V49 is a September-route agent.** Carrot (49) + wheat 163 + land-day-6 +
   12C/5S herd. No August elite seat plays this line (all carrot 0).
2. **Closest relative: thomastschinkel_2945.** Same day-0 (2C/2S, W7/M12),
   same quads (NW/NE/SW), same wash-heavy market census (SELL 459 vs 424,
   BUY_SEED 179 vs 187), same first-sale map — but 6C/6S end herd and
   -$150..-160 within V49 on discovery seeds. Same family, weaker calibration.
3. **dmitrii_lb2800 shares the V49 market census** (SELL 412, wash volumes
   ~17k carrot/wheat) with an 8C/6S herd — family member, lower output.
4. **kaitofukami_3009 is a different species**: sheep-only day-0, SELL 583,
   BUY_PRODUCT 37 (no wash), 11C/4S end. Ladder 3009 but weak on discovery
   seeds (45k) — regime-dependent.
5. **P3090/P3000/night_harvest are August fossils**: exact F5/F4/F2 hash
   matches, day-0 4S/1C (P3x), no carrot, no wash. Competitive in August,
   outscaled on 1.32.7 (103-124k vs V49 167-183k on the same seeds).
6. **V44 no-ops off-regime**: zero market orders, zero hires, ends at 3000 on
   seeds 10000/10001. Its 4 ladder wins (250617/250621) are a narrow regime —
   and it is the *only* ladder opponent that ever beats V49.
7. **saiteja_3000 ends on 2 quads** (misses SW) with 6C/1S — execution leak on
   these seeds; tetsutani liquidates its whole herd by end.

## The boundary inside the 3100+ population (§56)

F1 (24/42/108@land7) vs F3-F6 (19/37/143@land6) is the August boundary, but
both are carrot-0, wash-0 lines that the September cluster (V49 et al.) has
superseded in scale (tiles 239 vs 158-199, wheat 163 vs 92-143). The live
question is not August-F1-vs-F4 — it is whether anything in the September
cluster beats V49. Discovery capture says no (V49 8/8 legs across all 10
elites on seeds 10000-10001); the plan tournament (§14) tests this on fresh
tournament seeds with 400 legs.
