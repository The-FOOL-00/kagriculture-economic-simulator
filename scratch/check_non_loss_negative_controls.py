import sys, os
sys.path.insert(0, os.path.abspath("."))
import json

from scratch.run_exact_loss_counterfactuals import run_match_with_policy

NON_LOSS_NEGATIVE_CONTROLS = [
    {"loss_id": "NL_413", "seed": 250413, "seat": 0, "type": "NON_LOSS_EGG_SHOP", "nominal_loss": 0.0},
    {"loss_id": "NL_414", "seed": 250414, "seat": 0, "type": "NON_LOSS_EGG_SHOP", "nominal_loss": 0.0},
    {"loss_id": "NL_415", "seed": 250415, "seat": 0, "type": "NON_LOSS_EGG_SHOP", "nominal_loss": 0.0},
    {"loss_id": "NL_419", "seed": 250419, "seat": 0, "type": "NON_LOSS_EGG_SHOP", "nominal_loss": 0.0},
    {"loss_id": "NL_425", "seed": 250425, "seat": 0, "type": "NON_LOSS_EGG_SHOP", "nominal_loss": 0.0},
]

print("Evaluating Non-Loss Negative Controls under C0 vs C6 / C_off...")
for nl in NON_LOSS_NEGATIVE_CONTROLS:
    r0 = run_match_with_policy(nl, "C0")
    r6 = run_match_with_policy(nl, "C6")
    delta = r6["terminal_margin"] - r0["terminal_margin"]
    print(f"Seed {nl['seed']} Seat 0: C0 Margin = ${r0['terminal_margin']:>9.2f} | C6 Margin = ${r6['terminal_margin']:>9.2f} | Delta = ${delta:>9.2f}")
