import json, glob, os

brain_dir = r"C:\Users\Sundareswaran\.gemini\antigravity-ide\brain"
for conv_id in os.listdir(brain_dir):
    if conv_id == '599320aa-d7d3-471c-bc01-e6a18a768eb2': # current
        continue
    t_path = os.path.join(brain_dir, conv_id, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(t_path):
        with open(t_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                data = json.loads(line)
                c = str(data.get("content", ""))
                calls = str(data.get("tool_calls", ""))
                txt = (c + " " + calls).lower()
                if "cap 6" in txt or "cap=6" in txt or "cap of 6" in txt or "cap to 6" in txt or "6 tomato" in txt or "13 strawberry" in txt or "13-strawberry" in txt:
                    print(f"Conv {conv_id[:8]} Line {i} [{data.get('type')}]: {c[:150].replace(chr(10), ' ')}")
