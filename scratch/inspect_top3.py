import json, os
from deep_closed_loop_forensics import analyze_game_deep

for f, p, name in [
    ('scratch/replays/Crop_Dusta_104824599.json', 1, 'Crop_Dusta (#2)'),
    ('scratch/replays/Crop_Dusta_104821339.json', 0, 'Crop_Dusta (#2 - Game 2)'),
    ('scratch/replays/Yuan800_104824200.json', 0, 'Yuan800 (#3)'),
    ('scratch/replays/Whyme_Labs_104824599.json', 0, 'Whyme_Labs (#5)')
]:
    res = analyze_game_deep(f, p, name)
    print('='*80)
    print(f"{res['team']} | Final: ${res['reward']:,.1f} vs ${res['opp_reward']:,.1f}")
    snaps = res['snaps']
    cols = ['day', 'money', 'hands', 'quads', 'cows', 'sheep', 'pastures']
    print(snaps.loc[snaps['day'].isin([0, 2, 4, 6, 9, 14, 19, 24, 29]), cols].to_string(index=False))
    print('Sells:', res['sells'].groupby('item')['qty'].sum().to_dict() if not res['sells'].empty else {})
    print('Buys:', res['buys'].groupby(['op', 'item'])['qty'].sum().to_dict() if not res['buys'].empty else {})
