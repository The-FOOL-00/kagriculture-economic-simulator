import csv, json

with open('experiments/EXP-AEC-002/COMMITTED_PATCHES.csv', 'r') as f:
    rows = list(csv.DictReader(f))

print(f"Total committed patches: {len(rows)}")
for r in rows:
    print(f"Seed {r['seed']} | Match: {r['match_id']} | Turn: {r['turn']} | Seat: {r['treatment_seat']}")
    print(f"  Patch: {r['patch_id']} | Mech: {r['mechanism_family']}")
    print(f"  CF Delta Money: {r['delta_money']} | CF Delta Margin: {r['delta_margin']} | Realized: {r['delta_money_realized']}")
    print(f"  Baseline:  {r['baseline_action']}")
    print(f"  Candidate: {r['candidate_action']}")
    print("-" * 60)
