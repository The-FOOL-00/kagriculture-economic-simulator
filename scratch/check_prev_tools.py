import json

path = r'C:\Users\Sundareswaran\.gemini\antigravity-ide\brain\0b7bc0c1-cfa6-4da5-b274-f995f1800b9a\.system_generated\logs\transcript_full.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        data = json.loads(line)
        calls = data.get('tool_calls', [])
        if calls:
            for c in calls:
                name = c.get('name')
                args = c.get('args') or c.get('arguments') or {}
                if name == 'run_command':
                    cmd = args.get('CommandLine', '')
                    print(f"Step {idx}: CMD: {cmd}")
                elif name == 'write_to_file':
                    target = args.get('TargetFile', '')
                    print(f"Step {idx}: WRITE: {target}")
