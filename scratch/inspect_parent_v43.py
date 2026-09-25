"""
Inspect parent_v43 inside V3
"""
import tarfile, re

with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
    m = tar.extractfile("main.py")
    src = m.read().decode("utf-8")

# Extract _PARENT_SRC literal
match = re.search(r"_PARENT_SRC\s*=\s*b'([^']+)'", src, re.DOTALL)
if not match:
    match = re.search(r'_PARENT_SRC\s*=\s*b"([^"]+)"', src, re.DOTALL)

if match:
    parent_raw = match.group(1).encode('utf-8').decode('unicode_escape')
    print(f"Parent src length: {len(parent_raw)} chars, {parent_raw.count(chr(10))} lines")
    for line in parent_raw.splitlines():
        if "routes =" in line or "def router(" in line or "router =" in line:
            print("  ", line[:120])
        elif "shop-router" in line:
            print("  ", line[:120])
        elif "route_id" in line or "ROUTER" in line:
            print("  ", line[:120])
else:
    print("Could not extract _PARENT_SRC via regex")
