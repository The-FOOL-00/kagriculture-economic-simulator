# V32 R1 DECISION REPORT — BRANCH C (refined; 2026-09-22)

Primary question: "Can a learned meta-policy select among strong
deterministic experts to generalize and economically beat the strongest
fixed expert?" ANSWER: NO — with mechanism proofs at every step.

## 1. Classification: BRANCH C (oracle gap exists, router cannot find it)

Evidence: oracle +$7,897 gate-set mean over A7 (CI [+$5,984, +$10,064],
positive on 40/40 seeds, +$4,850 on LOCKED-only); best learned router
−$279 (CI includes 0); all P1 post-hoc patterns refuted on fresh seeds.

## 2. Required refinement of C (what "richer representations" cannot fix)

C-generic says "investigate richer temporal/opponent representations,
not PPO yet." The evidence refines this to a NO-GO for selection-based
routing specifically, with three proofs:
R1. The router decision ≡ the step-0 wash decision (A7/W72/W2015 are
V3-identical from step 1 on; source-proven + 282/282 b2 rows flat ≤$45).
Post-opening expert-switching is vacuous FOR THIS POPULATION — no future
switching study on these experts can work. Do not retry Regime C here.
R2. The best wash is a seed lottery: step-0 state is constant (P1-F10);
per-opponent best flips TRAIN→TEST on 5/6 opponents; CROSS-WITHIN fails
(17/41). No pre-episode information exists to condition on.
R3. The lottery resolves at median step ~258 (money-curve divergence),
invisible in any t≤24 prefix (wheat@t24 constant, M3 ≡ shuffled
economically). No early-frame router can predict it either.
Consequence: the $7.9k oracle is reachable ONLY by (a) within-episode
ADAPTIVE policies that observe the resolving lottery mid-game and adjust
the live economy (genuinely state-conditioned BC/PPO — the router
fallback is exhausted, which per V32 §52(7)/EXP-3 inverts the burden:
PPO is now the ONLY remaining learned route to the gap), or (b) new
expert designs (e.g. delayed-wash scouting — unproven economics, needs
its own validation program). NOT by better prefixes, bigger MLPs, or
more router seeds.

## 3. What R1 delivered (negative result, full value)

- Static routing over 40 fresh seeds: fixed experts tied (W72 nominal
+$796, CI includes 0); opponent-conditioning anti-generalizes (M1 −$601).
- B2-vacuity + wash-identity proofs (save all future switching effort).
- Late-lottery timing (t≈260) redirecting representation work mid-game.
- Reusable `v32/router` package + 13 tests + frozen dataset (330 b1 rows,
hash `6af8fcb5…`) for any future adaptive-policy work.
- Two P1 post-hoc patterns (opponent-driven 47%, CROSS-WITHIN) correctly
refuted by fresh data — the program's self-correction works.

## 4. Explicit non-recommendations

- Do NOT train bigger routers / longer prefixes on this population.
- Do NOT run Regime-C switching on these experts (R1).
- Do NOT promote any R1 router (gate failed all clauses but G4/G5).
- Do NOT touch competition slots (frozen; re-verified below).
- Do NOT run large PPO on the basis of R1 alone: R1 removes the router
alternative (§52(7) comparator resolved: router ≈ baseline < oracle),
which PERMITS a gated 1M-step PPO slope check (per EXP-3 gate) but does
not fund 50M+ runs. The slope check must show within-episode adaptation
signal first (OUTCOME B/C discipline).

## 5. Competition-state re-verification (phase exit)

Slot A `6b879b3e…fb3f5` / Slot B `4a076730…016619` re-verified
byte-identical at phase end; no submission rebuilt/resubmitted; no
protected holdout or V32-CONFIRM seed executed (full-suite green,
including all quarantine tests); all research on allocated V32 seeds
(TRAIN/VAL/TEST/LOCKED-research + 6 TEST seeds for the V22R1 probe).
