import json
import os

with open('extracted_agents/dmitrii_lb2800/actions.json') as f:
    tapes = json.load(f)

print('Number of tapes:', len(tapes))
for i in range(len(tapes)):
    tape = tapes[i]
    hands_144 = len(tape[144].get('hands', []))
    hands_240 = len(tape[240].get('hands', []))
    hands_360 = len(tape[360].get('hands', []))
    hands_500 = len(tape[500].get('hands', []))
    hands_700 = len(tape[700].get('hands', []))
    print(f'Tape {i:2d}: hands at 144: {hands_144}, at 240: {hands_240}, at 360: {hands_360}, at 500: {hands_500}, at 700: {hands_700}')
