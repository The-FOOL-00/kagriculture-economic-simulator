import json

path = r"C:\Users\Sundareswaran\.gemini\antigravity-ide\brain\97548096-26ef-405c-a7db-ff905a580159\.system_generated\logs\transcript.jsonl"
with open(path, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if 300 <= i <= 320:
            data = json.loads(line)
            c = str(data.get("content", ""))
            calls = str(data.get("tool_calls", ""))
            print(f"Line {i} [{data.get('type')}]: {c[:200].replace(chr(10), ' ')}")
            for cl in data.get('tool_calls', []):
                print("   Tool:", cl.get('name'), cl.get('args', {}).get('CommandLine', '')[:100], cl.get('args', {}).get('TargetFile', ''))
