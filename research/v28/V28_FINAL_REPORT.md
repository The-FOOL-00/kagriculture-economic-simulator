# V28 — FINAL REPORT: A7 VIRGIN CONFIRMATION

## 1. Executive conclusion

**A7 CONFIRMED: on 40 virgin seeds × 2 seats, frozen A7 beats frozen V3
by +$1,390 mean (+$1,286 median, 78W/2L, seed 95% CI [+$1,188, +$1,592]),
passing all six preregistered gates via a legible one-melon mechanism.**

## 2. V27 context

V27 classified V25 P3 as OUTCOME D (failed to generalize): the +$1,300.70
cohort-A result was a P2-residue worker-history artifact, and P3 lost on
virgin seeds (pooled −$434, seed CI [−747, −152]). From the causal
decomposition V27 discovered A7 (V3's full step-0 processing + 30-wash),
which scored +$1,451 (119/120) — but post-hoc on consumed seeds, hence
purely exploratory. V28 is its first and only confirmatory test.

## 3. Candidate specification

A7 = `V27AblationAdapter("V27-ABL-A7")`, frozen V27 bytes
(`18d2c8ea…`, 7,140 bytes, unchanged since V27 Stage A): call V3 at
step 0 normally; if its market is exactly [BUY50, SELL50], resize both
to 30; all other steps bit-identical to V3; no dispatch, no AEC. Full
freeze record: `V28_A7_FREEZE.md`; behavioral spec: `V28_A7_SPEC.md`.

## 4. Integrity validation

V22R1 re-verified untouched (tag commit `33763a8…`, archive
`6b879b3e…`). Process/import audit on consumed seeds: A7vV3 rewards +
digests invariant across 7 execution contexts per seed (orders A/B,
P3-primer, fresh subprocess, fresh-worker pool); V3vV3 5/5 invariant;
`sys.modules` clean; namespaces distinct; no RNG/env/fs vectors in
adapters or V3 payload. Serial/pool parity 8/8. Tournament ran with a
fresh worker process per match (80/80 distinct pids + nonces).

## 5. Preregistration

`V28_PREREGISTRATION.md` (committed `91073c8`, before the first
confirmation match): primary endpoint paired Δ = A7−V3; six gates with
frozen math (mean>0, median>0, posrate>50%, W>L, seed-clustered
t-CI fully>0, min>−$10k); exact-zero ties primary; anti-p-hacking
rules; prespecified 10-match fresh-subprocess verification.

## 6. Virgin cohort

`249530..249569` (40×2=80). Registry scan: max consumed seed anywhere
249529; seed-field parse of all results JSONL + 6-digit-literal scan of
2,393 files + streaming scan of 2 large scratch files; all residual
hits resolved (V27 reservations, exclusive range bounds, timestamp
microseconds, replay digit noise). Holdouts untouched. Manifest:
`V28_COHORT_MANIFEST.json`.

## 7. Primary results

Mean +$1,389.99, median +$1,286, SD $1,443 (match) / $631 (seed),
W/L/T 78/2/0 exact (77/2/1 at |Δ|≤$500), posrate 0.975, seed-positive
40/40, min −$3,154, max +$12,087, q05/q95 +$1,286/+$1,369, trimmed mean
+$1,289.5, bootstrap CI [+$1,286, +$1,594], Wilcoxon p=1.4e−14.
Raw: `results/v28_raw_results.jsonl` (`2efb4446…`); paired CSV
(`a0600fc8…`). Rewrite deployed 80/80; 0 unexpected shapes.

## 8. Six-gate result

| Gate | Result |
| :--- | :--- |
| 1. Mean > 0 (+$1,390.0) | PASS |
| 2. Median > 0 (+$1,286) | PASS |
| 3. Posrate > 50% (78/80) | PASS |
| 4. W > L (78/2/0) | PASS |
| 5. Seed CI > 0 ([+$1,188, +$1,592]) | PASS |
| 6. Floor > −$10k (−$3,154) | PASS |

**6/6 → OUTCOME A.** No tail-dependence overlay (top-1 share 9.5%).

## 9. Seat and seed analysis

37/40 seeds seat-identical; medians +$1,286 both seats. 39/40
seed-means equal +$1,286 (+83 harvest noise on two; +$5,279.5 on the
farm-gap tip seed). The seat-mean gap (+$604) is fully explained by
two program-independent farm gaps (−$6,267/−$10,965 in V3vV3), not by
any seat-favoring mechanism. 0 ties, 0 action-identical matches.

## 10. Tail analysis

+$12,087 expansion tip (9.5% share; mean still +$1,255 without it);
worst loss −$3,154 (3× inside the floor). Both losses are poorer-farm
legs with the mechanism intact. No 249450-style route pathology
recurs; A7 (no route/labor code) exposes no new tail channel.

## 11. Mechanism analysis

Typical win (74/80): wash savings (+$108) → step-17 cash $266-vs-$158
→ melon-seed gate $164.50 cleared by A7 / missed by V3 ($6.53) →
+1 melon plant (step 18; the game's ONLY unit divergence) → +$1,258
harvest at obs[252] → +$1,286 frozen to terminal. Tip leg: the $10,438
sheep gate (second independent observation after V27's 249463) tipped
by treatment cash. Wobble legs: late reactive-market micro-divergence,
structures identical.

## 12. Counterfactual evidence

CF-V28-1: $10,438.35 gate bisected to <$1; brain swaps prove purely
state-driven firing; restore-and-continue exact; independent re-run
identical. CF-V28-2: melon ×2 gate at ≈$164.50; +$6.53 flips V3.
Predicted vs realized reported separately throughout.

## 13. Generalization conclusion

**A7 CONFIRMED — STANDALONE MECHANISM.** The V27 exploratory effect
replicated quantitatively on virgin seeds (+$1,390 vs +$1,451), with
tighter structure (median = mode = +$1,286 on 74/80 legs).

## 14. Explicit non-conclusions

- This does NOT prove A7 is optimal (the $6.53 melon miss suggests
  nearby wash sizes may behave discretely differently — untested, and
  §28 forbids tuning on this evidence).
- This does NOT decompose value-creation vs zero-sum price extraction
  (A7vA7 vs V3vV3 absolute levels unmeasured).
- This does NOT promote A7 to the engineering/competition backbone
  (no packaging, no holdout, no live evidence).
- The $10,438 gate is now n=2, still not a general regime theory.
- Farm-gap seeds (2/40) show the +$1.3k edge does not overcome a
  −$6k+ farm deficit head-to-head on the poor leg.

## 15. Next research recommendation (exactly one)

**V29: preregistered A7 promotion gate on a protected holdout slice
(340050..340089, 40×2) PLUS absolute-level decomposition (A7vA7 vs
V3vV3 on the same seeds)** — one experiment answering whether A7 (a)
replicates on a truly held-out farm distribution and (b) creates vs
extracts value, before any AEC-substrate work or packaging decision.
