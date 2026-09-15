# EXP-DEV-006 VERDICT

## SUPPORTED

The 500-step horizon-gate mechanism is supported as a retrospective
mechanism test on the consumed DEV-005 Discovery cohort (247000–247049).
This is a MECHANISM verdict, not statistical significance, not Discovery,
not Qualification, not generalization, and not Kaggle evidence.

---

## Mechanism criteria (Phase 7)

| ID | Criterion | Result |
|---|---|---|
| A | Both residual losses materially improved | PASS: −$1,844 → $0.00 and −$5,393 → $0.00 (100% recovery, +$7,237.00) |
| B | Aggregate Discovery-cohort result improves | PASS: mean +$797.76 → +$942.50 (paired diff +$144.74) |
| C | No comparable new downside | PASS: 0 losses introduced, 0 other-seed changes (48/48 diffs exactly $0.00) |
| D | No destruction of legitimate upside | PASS: all 5 wins (+$5.4k…+$13.1k) preserved bit-identically; 0 wins sacrificed |
| E | Improvement actually due to late-entry economics, not an unrelated difference | PASS WITH DOCUMENTED NUANCE (see below) |

E-nuance: one-factor purity is gate-proven — the ONLY behavioral difference
from DEV-005 anywhere in the cohort is blocking the two step-288 entries
(guard fired exactly there; every other seed bit-identical). So the recovery
is 100% caused by avoiding late entries. But instrumented traces show the
late-entry harm is mediated by the entry's FULL cascade, not purely by
own-farm capital amortization: 247025 lost −$4,310 own-farm (suffix mismatch,
1,895 feed units, zero sheep bought, step-313 sheep missed) while 247034's
own farm beat its counterfactual (+$630) and the paired −$5,393 came
entirely through shared-market/weed channels (+$6,023 to the opponent,
identical shops). "Remaining horizon < 500" is therefore supported as a
PREDICTIVE gate for uneconomic late entry; the micro-story "unamortized
livestock capital" is refuted as the sole mediator ($0 livestock outlay).
Full decomposition: FORENSIC_AUDIT.md §§5–6.

No p-value was used for this verdict. (For reference only: paired diff
+$144.74, sd $800.99 — the verdict rests on criteria A–E, not significance.)

---

## The six verdict questions (Phase 11)

**1. Did the 500-step horizon mechanism actually fix the two residual losses?**
YES. Both converted to exact $0.00 ties: 247025 (−$1,844 → $0.00, +$1,844)
and 247034 (−$5,393 → $0.00, +$5,393). REJECT_HORIZON fired at step 288 in
exactly these two seeds (both matches), as preregistered.

**2. What did it cost elsewhere?**
NOTHING measurable. All other 48 seeds are bit-identical to DEV-005
(diffs exactly $0.00): 0 losses introduced, 0 wins sacrificed, 0 other
changes. DEV-006 W/L/T = 5/0/45 vs DEV-005 5/2/43.

**3. Did it remove legitimate high-upside cases?**
NO. All specialization events after step 216 (the 22 step-288 checkpoint
events), all positive deltas above +$2,000 (5 seeds), and all above +$5,000
(5 seeds) were inspected: the 5 first-at-216 wins (+$5,426, +$12,235,
+$13,064, +$6,139, +$10,261) are preserved bit-identically (diff $0.00,
upside_preserved=True). No first-at-288 winner existed to sacrifice — the
only 288-entries were the two losses. See POSITIVE_CONTROL_RESULTS.csv and
LATE_SPECIALIZATION_TABLE.csv.

**4. Is "minimum production runway" a better mechanism than a fixed step cutoff?**
H2 (allow entry only when expected payoff over the remaining horizon exceeds
required recovery cost) is documented as the stronger mechanistic hypothesis:
entry step confounds runway with the remaining commitment bundle (216-entry
still captures 5 sheep buys; 288-entry captures 0) and with world-channel
exposure. BUT H2 is NOT implementable from the current model (no capital term,
no amortization cliff — FORENSIC_AUDIT.md §4), NOT separable from H1 on N=2
late entries, and any H2 threshold would be post-hoc. Per mandate it is
documented ONLY (FORENSIC_AUDIT.md §7), not implemented, not swept.

**5. Is DEV-005 now ready for Qualification?**
NO. (a) The treatment changed → per Phase 12 it is DEV-006, a NEW treatment
identity requiring fresh Discovery, frozen implementation, frozen threshold,
and a protocol amendment — never "DEV-005 with a tiny fix." (b) The H=500
value is post-hoc (fit to N=2 late entries on this cohort); its justification
for fresh data is thin despite the clean mechanism result. (c) Qualification
partitions (50050–50099) and holdout (214200–214249) remain untouched per
mandate.

**6. What exact modification is justified next?**
Freeze DEV-006 = DEV-005 + HORIZON_GUARD (H=500, new-entry block only;
SHA-256 `06db94e59e2c271b5490aad78fdb760bd8a250f28ec4407de2d2f6be0644f5eb`)
as the new Discovery treatment with a protocol amendment, and run a FRESH
50-seed Discovery on virgin seeds (new range; never 247000–247049, never
quarantined partitions). Only if that fresh Discovery passes its gates may
Qualification be considered. Separately, preregister an H2 runway-rule
experiment for future work; do not bundle it into DEV-006.

---

## Execution integrity

- 200 games, both arms live, identical CRN, on the validated `kagsim_py` port
  (47,520/47,520 golden checkpoints; 100/100 DEV-005 replay games
  bit-identical; 400/400 frozen decision events identical).
- Hard gates passed: `replay_parity_ok` (50/50 bit-identical to frozen),
  `one_factor_purity_ok` (nonzero diffs only where the guard fired).
- All five preregistered predictions (README §3.1) confirmed exactly.
- H was NOT swept (H=500 only). No Kaggle submission. No quarantined seed
  executed. DEV-005 artifacts, frozen submissions 56146971/56146947 untouched.

## STOP (Phase 14)

No Qualification run. No parameter sweep. No submission. Awaiting review.
