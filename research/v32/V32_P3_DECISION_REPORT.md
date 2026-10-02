# V32 P3 DECISION REPORT

## 0. Primary conclusion (§40)

```text
P3 PARTIAL — representation repaired, but closed-loop/economic recovery insufficient
```

PPO 1M slope gate: `CLOSED` (reopening conditions 4, 5, 8 of §41 fail; see §6).

Failure classification (§32): **F3 primary** (optimization failure —
representation correct, joint training cannot fit the critical rare pattern in
reasonable budget) **+ F6 mechanism** (closed-loop compounding converts the
single step-0 error into total economic failure). NOT F1/F2 (schema recovered,
codec lossless, heads adequate), NOT F4 (data contains the wash 240/240), NOT
F5 (features sufficient — dedicated probes fit from them), NOT F7 (experts
demonstrate $91k+ economics).

## 1. What P3 proved (assets for any follow-up)

1. **Native action schema** (`V32_P3_ACTION_SCHEMA.md/.json`): complete
   simulator-grounded factorization (18 unit opcodes — WEED has no simulator
   branch; M=10 race-aligned market slots; PLANT atomic coupling as the only
   cross-unit coupling; qty-clamp/partial-fill; `int()` exception hazards).
   Every row cited to `kaggriculture.py` source lines.
2. **Lossless codec** (`v32/p3/codec.py`): literal identity over all 172,560
   recorded steps (N1=N2=N3=0) + live execution identity. G1 PASSES.
3. **Market-side head repair, behavioral**: mkt-nonnoop 0.30 (P2) → 0.80–0.90
   (P3) in BC generalization; m_op 99.5% joint memorization; dedicated step-0
   probe fits the wash fully (60/60 A7 exact) where P2's pointer NEVER fit 60
   identical samples (stuck all-NO-OP). The 1466-way bilinear collapse
   mechanism is gone with it.
4. **Unit-side parity at half the params**: 277k vs 546k; P2-exact unit-mean
   55.0% == pointer 55%; farmer 0.47–0.54 vs 0.44; no sample-efficiency
   inversion (strict-linear control worse on every head).
5. **Session-archaeology correction**: P2's "55%/100%" recovered verbatim from
   P2's session log — contiguous-400, unit-mean/farmer-only, LR 3e-3, P2's
   "linear" was a 3-layer MLP. P3's original ≥95% full-joint G2 bar was
   miscalibrated from that evidence and is retired with documented
   justification; G2 re-ran on P2's exact protocol.
6. **Clean causal chain to the failure**: step-0 slot-order error (only
   differing slots vs all 4 teachers; units match) → void SELL + buy-high →
   drift → $467/$60. No mystery, no hidden bug (T5-class execution identity
   holds throughout).

## 2. What failed, precisely

All three BC checkpoints miss the opening wash (mixture: reversed
`[SELL30,BUY30]`; A7-only: all-NOOP). The 180 step-0 train samples (0.13%,
unanimous order supervision) cannot override the global M0≈SELL mode in 30
epochs at LR 3e-4 OR 3e-3 (higher LR dug the wrong optimum deeper:
slot-0 P(SELL) 0.76→0.81 — a stable wrong equilibrium, not slow convergence).
Closed loop: D1 $467/$448 (15× P2 but mechanism-broken, 0 wins), D2 $60/$0
(higher fidelity, worse economics — fidelity≠economics). G3 FAILS, G4 FAILS
(§29 spirit), G5/G6 not run per protocol (single-seed arms; broken policy
correctly kept off single-touch seeds).

## 3. Gate scorecard (prereg §4)

| Gate | Result |
| :--- | :--- |
| G1 codec lossless | PASS (0 unexplained mismatches, 172,560 steps) |
| G2 memorize (recalibrated) | PASS (market repair behavioral; unit parity; §1.3–1.4) |
| G3 step-0 wash | PARTIAL (dedicated-probe PASS; all full-BC FAIL) |
| G4 closed-loop economics | FAIL ($467 mechanism-broken; $60) |
| G5 stability | NOT RUN (moot — failure mode reproduced across 3 runs/2 LRs instead) |
| G6 generalization | NOT RUN (correctly — policy broken; CONFIRM preserved virgin) |

## 4. Why this is PARTIAL, not STOP-C upstream/downstream

STOP C ("head cannot memorize despite sufficient information") does not
trigger: the head DOES memorize the wash in isolation and market patterns
jointly to 99.5%. The binding constraint is JOINT OPTIMIZATION of a rare
(0.13%) sharp pattern under a shared trunk — an optimization-rate/budget
problem (F3), one level up from P2's head-representation problem. P3 moved the
bottleneck but did not clear it. No prohibited complexity was introduced; no
resampling (forbidden) was attempted; the two LR runs + one single-teacher run
are the complete P3 training record (no sweep).

## 5. What would have to change (follow-up guidance, NOT authorized here)

Any ONE of these is a new phase with its own prereg: (a) optimization budget
for rare patterns (LONGER training with wash-tracking — predicted ~400+
effective epochs from probe dilution math; uncertain); (b) architecture that
frees rare-pattern fitting from shared-trunk equilibrium (e.g., per-slot heads
— analyzed: fixes confusion, NOT dilution, so weakly indicated); (c) a
principled treatment of critical-rare supervision that is NOT silent
reweighting (explicit, prereged loss design — governance-heavy). PPO-from-BC
is NOT the fix (inits earn ≈$0–467 with broken mechanics → no signal, same as
P2's argument).

## 6. PPO gate: CLOSED (§41 checklist)

1 schema ✓ · 2 codec ✓ · 3 memorize ~✓ (recalibrated) · 4 step-0 wash ✗ ·
5 closed-loop material+mechanism ✗ · 6 reproducible ~ · 7 not replay ✓ ·
8 unseen nontrivial ✗ (untested) · 9 representation-dominance ~ (fidelity yes,
critical-pattern no). Conditions 4, 5, 8 fail → CLOSED. No PPO launched in P3.

## 7. Competition state

Re-verified byte-identical at exit (Slot A `6b879b3e…`, Slot B `4a076730…`,
V3 `845e0d10…`, spot adapters). P3 executed only prereged P3-SCREEN
`249675–249684` + consumed P2 seeds. CONFIRM/holdouts virgin. No submission
touched or launched. See `V32_P3_COMPETITION_SAFETY.md`.
