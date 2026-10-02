import json
import os

with open("research/v50/loss_regimes/v49_loss_corpus.json") as f:
    corpus = json.load(f)

print(f"Total losses: {len(corpus)}")
print("Keys in loss record:", list(corpus[0].keys()))
for i, l in enumerate(corpus):
    print(f"Loss {i+1}:", {k: l[k] for k in list(l.keys())[:10]})

