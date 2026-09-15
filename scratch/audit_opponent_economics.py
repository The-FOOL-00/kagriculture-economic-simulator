import json

with open('scratch/live_meta_corpus_summary.json') as f:
    summary = json.load(f)

targets = ['originators', 'agi', 'meteor', 're:dorf', 'les 2 oies', 'xxxxyt', 'snaykey']
print(f"Total episodes: {len(summary)}")

for ep in summary:
    opp = ep['opp_name'].lower()
    if any(t in opp for t in targets):
        print("="*60)
        print(f"Opponent: {ep['opp_name']} | Won: {ep['won']} | Seed: {ep['seed']}")
        print(f"File: {ep['file']}")
        print(f"Shops: {ep['shops']}")
        print(f"Our cash: {ep['our_cash']} | Opp cash: {ep['opp_cash']} | Margin: {ep['margin']}")
        opp_tel = ep.get('opp_telemetry', {})
        our_tel = ep.get('our_telemetry', {})
        print(f"Opp produced: {opp_tel.get('produced', {})}")
        print(f"Opp sold:     {opp_tel.get('sold', {})}")
        print(f"Our produced: {our_tel.get('produced', {})}")
        print(f"Our sold:     {our_tel.get('sold', {})}")
