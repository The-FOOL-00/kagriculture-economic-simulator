import json
import sys

# Ensure UTF-8 stdout
if sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

with open(r'scratch\aethel_full_forensics_reconciled.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"{'Replay':<18} | {'Log':<18} | {'Verified':<8} | {'Engine':<7} | {'Seat':<4} | {'Opponent':<22} | {'Our':<8} | {'Opp':<8} | {'Margin':<8} | {'Outcome'}")
print("-" * 125)

missing_logs = []
for r in data:
    log_str = r['log_file'] if r['log_file'] else 'MISSING'
    if not r['match_verified']:
        missing_logs.append(r['episode_id'])
    opp_clean = r['opp_name'][:22]
    print(f"{r['replay_file']:<18} | {log_str:<18} | {str(r['match_verified']):<8} | {str(r['engine_version']):<7} | {r['our_seat']:<4} | {opp_clean:<22} | {r['our_score']:<8.0f} | {r['opp_score']:<8.0f} | {r['margin']:<8.0f} | {r['outcome']}")

print(f"\nTotal Replays: {len(data)}")
print(f"Missing logs count: {len(missing_logs)}")
if missing_logs:
    print(f"Missing log episode IDs: {missing_logs}")
