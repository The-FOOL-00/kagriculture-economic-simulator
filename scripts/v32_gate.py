# SPDX-License-Identifier: MIT
"""V32 promotion gate function (V32_PROMOTION_PROTOCOL.md §2, clauses 1-8).

Pure function over leg records. Clause 8 (determinism rerun) is evaluated by
the caller comparing two runs; this module evaluates clauses 1-7 and provides
the digest comparator for clause 8.
"""

TAIL_LIMIT = -25000.0
FAMILY_MIN_WR = 0.40
MIN_POSITIVE_FAMILIES = 3


def _median(xs):
    xs = sorted(xs)
    n = len(xs)
    if n == 0:
        return 0.0
    m = n // 2
    return xs[m] if n % 2 else 0.5 * (xs[m - 1] + xs[m])


def evaluate_gate(legs, learner_id, champion_id, family_of):
    """legs: [{seed, seat, opponent, learner_cash, champion_cash, family}...].

    family_of(opponent_id) -> family label. Returns (pass: bool, report: dict).
    """
    if not legs:
        return False, {"error": "no-legs"}
    ds = [l["learner_cash"] - l["champion_cash"] for l in legs]
    wins = sum(1 for d in ds if d > 0)
    losses = sum(1 for d in ds if d < 0)
    ties = sum(1 for d in ds if d == 0)
    decided = wins + losses
    mean_d = sum(ds) / len(ds)
    med_d = _median(ds)
    wr = (wins / decided) if decided else 0.0

    by_fam = {}
    for l, d in zip(legs, ds):
        fam = family_of(l["opponent"])
        by_fam.setdefault(fam, []).append(d)
    fam_wr = {}
    fam_mean = {}
    for fam, xs in by_fam.items():
        w = sum(1 for x in xs if x > 0)
        dec = sum(1 for x in xs if x != 0)
        fam_wr[fam] = (w / dec) if dec else 0.0
        fam_mean[fam] = sum(xs) / len(xs)

    clauses = {
        "c1_positive_mean": mean_d > 0,
        "c2_positive_median": med_d > 0,
        "c3_wr_gt_half": wr > 0.5,
        "c4_wins_gt_losses": wins > losses,
        "c5_no_tail": all(d > TAIL_LIMIT for d in ds),
        "c6_no_family_collapse": all(v >= FAMILY_MIN_WR for v in fam_wr.values()),
        "c7_breadth": sum(1 for v in fam_mean.values() if v > 0) >= MIN_POSITIVE_FAMILIES,
    }
    report = {"clauses": clauses, "pass_1_7": all(clauses.values()),
              "mean": mean_d, "median": med_d, "wr": wr,
              "wins": wins, "losses": losses, "ties": ties,
              "family_wr": fam_wr, "family_mean": fam_mean,
              "worst": min(ds), "n": len(ds)}
    return all(clauses.values()), report


def digests_equal(run_a, run_b):
    """Clause 8: every leg's action digest identical across reruns (by key)."""
    da = {l["key"]: l["action_digest"] for l in run_a}
    db = {l["key"]: l["action_digest"] for l in run_b}
    if set(da) != set(db):
        return False
    return all(da[k] == db[k] for k in da)
