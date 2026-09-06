import os

for root, dirs, files in os.walk("."):
    for f in files:
        p = os.path.join(root, f)
        try:
            with open(p, "r", encoding="utf-8", errors="ignore") as file:
                lines = file.readlines()
                for idx, line in enumerate(lines):
                    if "126,840" in line or "126840" in line:
                        print(f"{p}:{idx+1}: {line.strip()}")
        except Exception:
            pass
