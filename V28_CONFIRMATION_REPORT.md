# V28 — CONFIRMATION REPORT (§31 verification record)

Verdict: **OUTCOME A — A7 CONFIRMED: STANDALONE MECHANISM**
(6/6 preregistered gates pass; see `V28_GATE_RESULTS.md`).

## §31 positive-result checklist

1. **Independent subset re-run:** preregistered 10-match subset
   (seeds 249530..249534 × 2 seats) re-executed from scratch in
   fully fresh subprocess interpreters — **10/10 reward+digest
   identical** to frozen tournament records
   (`scripts/v28_verify_farmgaps.py`).
2. **Candidate hash:** A7 file `18d2c8ea…` asserted at every runner
   startup; all 80 records carry matching `cand_digest`, exact flag
   vector, and V3 `845e0d10…` / engine 1.32.7 digests. Rewrite
   deployed 80/80, unexpected-shape 0/80.
3. **Execution-order invariance:** isolation audit (34 runs, 2
   consumed seeds) — 7/7 A7vV3 invariant across orders A/B,
   P3-primer, fresh subprocess, and pool; P3-primer regression
   PASS; `sys.modules` clean; namespaces distinct.
4. **Serial/parallel parity:** 8/8 consumed-subset matches identical
   across serial/pool (+ subprocess in committed tests); 0 mismatches.
5. **Mechanism audit:** `V28_MECHANISM_AUDIT.md` — typical win is ONE
   melon plant (wash savings → $164.50 seed gate → step-18 plant →
   obs[252] harvest → +$1,286 frozen); tip/loss/wobble legs diagnosed.
6. **Tail audit:** `V28_TAIL_AUDIT.md` — top-1 share 9.5%, no
   tail-dependence; worst loss −$3,154 (3× inside the floor); farm
   gaps measured (2/40); no route fragility.
7. **Qualification:** `V28_QUAL_MANIFEST.json` (this report's
   companion) records the frozen promotion-eligibility evidence.

## Promotion status

A7 is CONFIRMED as a research-backbone mechanism. It is NOT submitted,
NOT packaged, and NOT yet the engineering backbone: V22R1
(`33763a8` / `6b879b3e…`, re-verified untouched) remains the
competition fallback, and no AEC work has been started on A7. The
single next experiment is recommended in `V28_FINAL_REPORT.md` §15.
No live leaderboard submission was made or is authorized by this report.
