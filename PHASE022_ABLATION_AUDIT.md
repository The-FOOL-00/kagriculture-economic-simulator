# PHASE022 ABLATION & ATTRIBUTION AUDIT (Independent Adversarial Audit)

**Date**: 2026-09-20
**Scope**: 7-arm factorial (`FULL`, `NO_TIMING`, `NO_LIQ`, `NO_SHUTDOWN`,
`TIMING_ONLY`, `LIQ_ONLY`, `SHUTDOWN_ONLY`), each N=40 on seeds 249376..249395.

## 1. Are the seven configurations actually different? YES (3-layer enforcement)

Arm configs are built in `scripts/run_phase022_consolidation.py:300-336` by
assigning distinct `enabled_mechanisms` tuples onto fresh
`build_robust_qualified_config()` instances. Enforcement was traced through
three independent layers:

| Layer | Location | Behavior |
| --- | --- | --- |
| L1 opportunity filter | `aec/opportunities/__init__.py:149-163` | frozen mode admits only `fam in enabled` (plus a `LOCAL_WEED_DIG` telemetry carve-out, blocked later) |
| L2 patch generation | `aec/patches/generator.py:82-87` | refuses any family not in `enabled` (same carve-out), counts as quarantined |
| L3 commit gate | `aec/integration/executor.py:758-783` | `mech_fam not in enabled_mechanisms` forces ABSTAIN (`MECHANISM_POLICY_VIOLATION`); quarantined-status families forced to ABSTAIN (`SCIENTIFIC_QUARANTINE`) |

No execution path from opportunity to committed action bypasses L3: the
in-flight continuation path (`executor.py:328-372`) can only engage for a patch
that already passed L3, and no multi-step patch can commit under the qualified
config (all 34 commits are single-step market mutations; verified in
`results/phase022_decision_traces.json`).

### Ablation truth table

| Arm | Intended mechanisms | Actually active mechanisms | Match? |
| --- | --- | --- | --- |
| FULL_FOUNDATION | Timing + Liq + Shutdown | Timing + Liq + Shutdown (Liq/Shutdown eligible, never fired) | YES |
| NO_MARKET_TIMING | Liq + Shutdown | Liq + Shutdown (never fired) | YES |
| NO_TERMINAL_LIQUIDATION | Timing + Shutdown | Timing + Shutdown | YES |
| NO_PHASE_SHUTDOWN | Timing + Liq | Timing + Liq | YES |
| MARKET_TIMING_ONLY | Timing | Timing | YES |
| TERMINAL_LIQUIDATION_ONLY | Liq | Liq (never fired) | YES |
| PHASE_SHUTDOWN_ONLY | Shutdown | Shutdown (never fired) | YES |

**The ablation implementation is valid.** Configurations differ as intended at
all three enforcement layers.

## 2. Are the identical arm summaries legitimate? YES, with a data gap

Four timing-on arms report bit-identical summaries (mean +$33.35, CI
[-$335.08, +$401.78], 21/7/12, rewards $94,346.40/$94,313.05, 34 timing commits);
three timing-off arms report bit-identical summaries (mean -$2.15, 5/5/30,
0 commits). This pattern is **expected from implementation behavior**, not
evidence of a copy-paste bug:

1. `TERMINAL_LIQUIDATION` can only trigger at step == 718 with shed stock
   (`aec/opportunities/terminal.py:27-42`); `PHASE_SHUTDOWN` only generates a
   patch when V3 emits a dead `BUY_SEED` (`aec/patches/generator.py:202-219`).
   Zero commits for both across all arms means neither condition produced a
   committable candidate in this cohort, so removing them changes nothing.
2. Proof the arms genuinely executed (rather than being copied): `total_candidates`
   differs by timing status (1310 with timing vs 1073 without; delta = 237
   timing candidates), while the three timing-off arms agree at 1073, showing
   Liq/Shutdown added zero candidates anywhere.
3. Proof of determinism across re-execution: the FULL arm re-ran the fresh
   validation config and reproduced its summary bit-identically.
4. The timing-off 5/5/30 pattern with mean -$2.15 is consistent with pure
   V3-vs-V3 seat asymmetry under head-to-head mirroring (treatment with zero
   commits plays byte-identical V3 actions via backbone passthrough). Control
   means legitimately differ across timing on/off ($94,313.05 vs $94,338.40)
   because treatment commits move shared market prices and change opponent
   scores. The decisive-match SET differs between arms (10 vs 6 seat-only rows)
   because deltas are equilibrium outcomes, not additive components.

**Data gap (material for reproducibility): only the FULL/fresh arm persisted
per-match rows.** The other six arms stored summaries only
(`run_phase022_consolidation.py:338-351` discards `arm_matches`). Therefore:

- Arm means, CIs, p-values, and W/L/T **cannot be independently recomputed**
  from artifacts (trusted via code review of the shared, exactly-verified
  `compute_cohort_statistics`, but not re-derivable).
- Row-level identity of the timing-on arms cannot be verified.
- Which seeds were decisive in the timing-off arms cannot be checked.

## 3. Is "100% of active alpha" / "necessary and sufficient" established?

**Only in the weak, cohort-specific reading.** The data establish:

> "Market timing is the only mechanism that produced measurable incremental
> effect in this cohort and experimental design."

They do NOT establish:

> "Market timing is the only mechanism producing measurable incremental
> economic effect" (as a general causal fact).

Reasons:

1. Liq/Shutdown never fired, so the experiment measured their effect as zero
   **conditional on V3 never stranding inventory or buying dead seeds in these
   40 matches** -- a property of (V3 x cohort), not of the mechanisms.
2. Marginal +$35.50 is +$33.35 minus -$2.15, i.e. it subtracts seat-noise
   residue; presenting it as the mechanism's effect size inherits the CI that
   spans zero.
3. "Necessary and sufficient driver of economic outperformance" extrapolates a
   40-match cohort result to a general causal law. The interaction audit (zero
   collisions) is likewise conditional on mechanisms that never co-fired.

## 4. "Zero regression / proven defense-in-depth" is vacuous in this cohort

Because Liq/Shutdown never generated a committable candidate, "zero regression"
means "never acted," and "proven defense-in-depth" means "pure-function unit
tests passed" (the two terminal tests never touch the executor). Their live
wiring (step-718 trigger, shutdown pruning inside real games) is entirely
unexercised by the 28,760 validation steps. The honest characterization is:
"no evidence of regression in this cohort (mechanisms never triggered); live
protective value unproven."

## 5. Classification

**Attribution: PASS WITH CAVEAT.** Ablation enforcement is real and verified;
identical summaries are explained, not anomalous. But per-arm ledgers are
missing (reproducibility gap), and the causal headline must be cut down to the
cohort-specific reading.
