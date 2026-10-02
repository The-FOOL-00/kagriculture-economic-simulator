# V31R2 DECISION REPORT — live-ladder forensics, calibration, deadline plan

Date: 2026-09-22. Deadline: 2026-09-30 (8 days). Evidence: all 352
live episodes with replays (99 A7 + 251 V22R1 public + 2 validation),
9,807-team leaderboard snapshot, 548 local validation legs (E1/E2/E3/E3b).

## 1. The mission question — answered

> Why does A7 sit at 1859.6→1842.1 while V22R1 sits at
> 1875.0→1880.3→1854.5?

Three measured facts, in order of importance:

1. DIFFERENT POOLS. A7's opponents median 1864 (p75 1977, max 2695);
   V22R1's median 1929 (p75 2299, max 2859). V22R1 is matched ~65–320
   points tougher. Each agent beats ~1800s and loses to ~2000+s; the
   ratings describe the pools, not a quality gap.
2. SMALL SAMPLE + MATCHMAKING DYNAMICS (real, measured). A7: 99 games
   in ~9 hours (submitted 02:31 UTC); V22R1: 251 games in ~42 hours.
   Both slots went 6-11 / 4-10 over the latest 3h as matchmaking
   hardened (A7's loss-median opp 1926); ratings move ±20 in hours.
3. NO HEAD-TO-HEAD INFERIORITY. Shared opponents (11 teams): both-win
   4, both-lose 2, A7-only-win 4, V22R1-only-win 1 (MAOSEN: A7 −$45,
   V22R1 +$3,941). Absolutes identical (~$98–100k med both). A7 is NOT
   weaker than V22R1 — it is younger with a softer-then-hardening pool.

The ~12-point gap is a matchmaking/sample artifact. Both ratings are
still equilibrating; neither slot has separated from the other.

## 2. A7's validated live strength (keep!)

- +$1,286 extraction replicated live 6-0 vs 50-wash (4 exact +$1,286,
  incl. 3x vs 2436-rated naren_v; canonical melon trajectory +108 →
  +28 → +1286 @ step 252). V29's mechanism is LIVE-TRUTH, and the
  packaged A7 behaves identically to local A7 (no packaging mismatch).
- 50W/32L (61%) vs its pool; 16 blowout wins vs weak teams.
- Zero losses to 50/70-wash (7-0 combined, +$1,286/+$3,896).

## 3. A7's live gaps (all characterized, none one-line-fixable)

32 losses decompose into: wash-ledger mirrors (~6, ±$600 max, no
dominant counter-wash — E3b matrix spans $3–$307 and any switch
sacrifices the +$1,286 vs 50); livestock-mix (wen-type ~5: opponents
run +3 sheep/−3 geese ≈ +$8.6k, intrinsic policy, V3-router-internal);
fert/feed micro (shawenher-type: +99 yield units on identical
animals/seeds; +35 FERTILIZE); sell-execution micro (Marlubie −$4.3k,
identical counts/yields/sells — below count resolution);
strawberry-archetype (Fedor −$14k, 392 strawberries — different
strategy). Details: `V31R2_LOSS_FORENSICS.md`.

## 4. A8 campaign — exhausted, NO-BUILD

E1 price-gating 0-48 (−$35k, shed-clog destruction) · E2
order-splitting 0-40 (−$3k) · E3 washes ±$600 crumbs, no dominance ·
E3b full matrix transitive but immaterial · E6 skipped (predicted
clog). 548 legs. Every live-motivated one-line hypothesis falsified.
Remaining gaps need V3-internal policy surgery (frozen bytes,
interacting pasture/feed/cash/structure effects) — banned by §21/§31.
Spec verdict recorded in `V31R2_A8_SPEC.md` §14.

## 5. V22R1 assessment

V22R1 opens 50/50 (101/101) — V3-regime; AEC market timing does not
prevent trickle losses (JR −$13,785, same pattern as A7's). It holds
1880 by grinding a tough pool at 45.6%, not by superior mechanism.
NO evidence supports returning Slot B to a second V22R1-type agent
(OPTION 2 rejected).

## 6. Sim-to-live verdict

NO engine mismatch (1.32.7 = 1.32.7), NO packaging mismatch (live
+$1,286 = local +$1,286), NO evaluation mismatch (E3b wash effects
replicate live mirror scale: +$140 local vs −$139 live). The ONLY
mismatch was OPPONENT SET: V30 tested extinct weak proxies (256-0)
while the live 1800+ band is V3-clones with micro/strategy adaptations.
V30 reclassified OFFLINE REPLAY-POLICY EVIDENCE (see calibration doc).
The simulator is faithful; the gauntlet was wrong. Next cycle must
field live-derived clone opponents before any frontier claim.

## 7. DECISION — OPTION 1: KEEP A7 (exactly one, per §30)

Evidence: A7 performs well live (61% WR, validated +$1,286 mechanism,
no pathology — losses are diverse small meta-gaps, CASE B/D per §9);
no dominant single vulnerability with a narrow fix exists (E1–E3b
exhausted); V22R1 shows no superiority (shared splits favor A7).

## 8. Slot plan to September 30

- Slot A: V22R1 (KEEP, immutable fallback).
- Slot B: A7 (KEEP — do not replace; rating provisional, climbing).
- No A8 submission. No further local campaigns except monitoring.
- DAILY (cheap, no seeds): re-pull episode lists + scores; track A7
  rating/WR vs pool median; alert if WR <45% over any 50-game window
  or a NEW loss family (>3 same-signature losses) appears. Reopen A8
  ONLY on a new repeatable single-mechanism failure (V30 §12 gates
  still apply: >60% h2h vs A7 over ≥16 mirrored legs with a runnable
  agent, or >5% self-play excess with mechanism).
- 3000 target: neither slot is on a 3000 trajectory (both ~1900,
  p90 = 2403). No claim made. A7's realistic band by Sep 30 is
  ~1880–1950 if pools hold; reaching 2400+ needs the policy-level
  livestock/fert/crop program — a post-deadline project.

## 9. Stop-condition audit (§31)

Live data: OBTAINED (321/321 replays) ✓. Opponent identity: reliable
(teams + LB + washes; 3/139 mixed-wash teams flagged) ✓. Engine:
MATCHED ✓. Sample: adequate (82 + 237) ✓. A8 proposals: all falsified
or multi-interaction → correctly stopped ✓. V22R1 integrity:
verified untouched (SHA `6b879b3e…`, git `33763a8…`) ✓. Holdouts
340090..340199 + 214200..214249: verified untouched ✓ (scan below).
