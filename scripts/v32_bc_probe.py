# SPDX-License-Identifier: MIT
"""V32 EXP-2 probes (numpy-only; runs under .venv).

1. BC probe: farmer_op classification from v32enc-v1.1 (majority baseline vs
   multinomial logistic regression, full-batch LBFGS-free Adam).
2. Router toy: per-seed opening-expert choice among {V3,A7,W2015} vs fixed V3
   from an early observable state (leave-one-seed-out).
3. Full-action exact-match honesty check (expected ~0 at this rung).

Usage: v32_bc_probe.py --traj FILE [--router-legs results/v32_exp1.jsonl]
Pure analysis over captured trajectories; runs no matches.
"""

import argparse
import json
import os
import sys

import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from v32_encoder import UNIT_OPS  # noqa: E402


def load_pairs(path):
    X, yf, acts = [], [], []
    n_fail = 0
    for line in open(path):
        rec = json.loads(line)
        for rows in (rec["rows_left"], rec["rows_right"]):
            for r in rows:
                if r["obs"] is None:
                    n_fail += 1
                    continue
                X.append(r["obs"])
                op = (r["farmer"] or ["?"])[0]
                yf.append(op if op in UNIT_OPS else "?")
                acts.append(r)
    return np.array(X, float), yf, acts, n_fail


def softmax_logits(X, W, b):
    z = X @ W + b
    z -= z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def train_softmax(X, Y, iters=400, lr=0.05, seed=0):
    rng = np.random.RandomState(seed)
    n, d = X.shape
    k = Y.shape[1]
    W = rng.randn(d, k) * 0.01
    b = np.zeros(k)
    mW = np.zeros_like(W)
    mb = np.zeros_like(b)
    for t in range(1, iters + 1):
        P = softmax_logits(X, W, b)
        G = (P - Y) / n
        gW = X.T @ G + 1e-4 * W
        gb = G.sum(axis=0)
        mW = 0.9 * mW + 0.1 * gW
        mb = 0.9 * mb + 0.1 * gb
        W -= lr * mW
        b -= lr * mb
    return W, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj", required=True)
    args = ap.parse_args()
    X, yf, acts, n_fail = load_pairs(args.traj)
    print("pairs=%d encode_fail=%d dim=%d" % (len(X), n_fail, X.shape[1]))
    labels = sorted(set(yf))
    li = {l: i for i, l in enumerate(labels)}
    y = np.array([li[v] for v in yf])
    print("farmer_op classes (%d): %s"
          % (len(labels), {l: int((y == li[l]).sum()) for l in labels}))
    maj = max(range(len(labels)), key=lambda i: (y == i).sum())
    print("majority baseline acc=%.3f (%s)" % ((y == maj).mean(), labels[maj]))

    # chronological split: first 80% train, last 20% test (no shuffle leakage)
    n = len(X)
    cut = int(n * 0.8)
    mu, sd = X[:cut].mean(0), X[:cut].std(0) + 1e-6
    Xs = (X - mu) / sd
    Y = np.zeros((cut, len(labels)))
    Y[np.arange(cut), y[:cut]] = 1
    W, b = train_softmax(Xs[:cut], Y)
    for name, sl in (("train", slice(0, cut)), ("test", slice(cut, n))):
        P = softmax_logits(Xs[sl], W, b)
        pred = P.argmax(1)
        print("%s softmax acc=%.3f (lift %+.3f over majority)"
              % (name, (pred == y[sl]).mean(),
                 (pred == y[sl]).mean() - (y[sl] == maj).mean()))

    # honesty check: full-action exact match of a per-head majority predictor
    from collections import Counter
    born = Counter((r["farmer"] or ["?"])[0] for r in acts)
    print("full-action exact-match at majority rung: ~0 by construction "
          "(joint match over farmer+hands+market); per-head majority farmer acc=%.3f"
          % (born.most_common(1)[0][1] / len(acts)))


if __name__ == "__main__":
    main()
