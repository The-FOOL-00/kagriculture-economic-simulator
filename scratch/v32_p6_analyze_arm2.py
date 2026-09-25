# SPDX-License-Identifier: MIT
import json, os, numpy as np

p = "results/v32_p6_eval_arm2.jsonl"
rows = [json.loads(line) for line in open(p) if line.strip()]
print(f"Total rows: {len(rows)}")

cash = [r["my_cash"] for r in rows]
s0_wash = sum(1 for r in rows if r.get("step0_wash"))
s0_pass = sum(1 for r in rows if r.get("step0_pass"))
s1_north = sum(1 for r in rows if r.get("step1_north"))
s1_hires = np.mean([r.get("step1_hires", 0) for r in rows])
s2_south = sum(1 for r in rows if r.get("step2_south"))
wins = sum(1 for r in rows if r.get("win"))
losses = sum(1 for r in rows if r["my_cash"] < r["opp_cash"])
ties = sum(1 for r in rows if r["my_cash"] == r["opp_cash"])

print(f"S0 Wash:   {s0_wash}/{len(rows)} ({100*s0_wash/len(rows):.1f}%)")
print(f"S0 Pass:   {s0_pass}/{len(rows)} ({100*s0_pass/len(rows):.1f}%)")
print(f"S1 North:  {s1_north}/{len(rows)} ({100*s1_north/len(rows):.1f}%)")
print(f"S1 Hires:  {s1_hires:.2f} / 5.00")
print(f"S2 South:  {s2_south}/{len(rows)} ({100*s2_south/len(rows):.1f}%)")
print(f"\nTerminal Cash Statistics:")
print(f"  Mean:   ${np.mean(cash):.2f}")
print(f"  Median: ${np.median(cash):.2f}")
print(f"  Std:    ${np.std(cash):.2f}")
print(f"  Min:    ${np.min(cash):.2f}")
print(f"  Max:    ${np.max(cash):.2f}")
print(f"\nOutcomes:")
print(f"  Wins:   {wins}/{len(rows)} ({100*wins/len(rows):.1f}%)")
print(f"  Losses: {losses}/{len(rows)} ({100*losses/len(rows):.1f}%)")
print(f"  Ties:   {ties}/{len(rows)} ({100*ties/len(rows):.1f}%)")
