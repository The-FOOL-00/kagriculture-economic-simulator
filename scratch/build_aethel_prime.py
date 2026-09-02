import json
import zlib
import base64
import os
import sys

# Load Route A and Route B from worked_example_routes.json
with open("replays/raw/destbreso/worked_example_routes.json", "r", encoding="utf-8") as f:
    routes_data = json.load(f)

route_a = routes_data["A"]["route"] # Utkarsh #2 (3086 Elo)
route_b = routes_data["B"]["route"] # Mohamed Abdelrazik (2983 Elo)

# Load Closer Cleo base trace
spec_cleo = {}
with open("replays/raw/reference_agents/closer_cleo.py", "r", encoding="utf-8") as f:
    cleo_code = f.read()

# Let's verify route lengths
print(f"Route A turns: {len(route_a)}")
print(f"Route B turns: {len(route_b)}")

# Compress Route A and Route B into base85 strings
bytes_a = base64.b85encode(zlib.compress(json.dumps(route_a).encode('utf-8'))).decode('utf-8')
bytes_b = base64.b85encode(zlib.compress(json.dumps(route_b).encode('utf-8'))).decode('utf-8')

print(f"Compressed Route A: {len(bytes_a)} chars")
print(f"Compressed Route B: {len(bytes_b)} chars")

with open("scratch/route_a_payload.txt", "w") as f:
    f.write(bytes_a)

with open("scratch/route_b_payload.txt", "w") as f:
    f.write(bytes_b)
