"""
Inspect V3 routes and route selection logic
"""
import tarfile, os, re

with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
    names = tar.getnames()
    print("Files in V3 tarball:", names)
    m = tar.extractfile("main.py")
    src = m.read().decode("utf-8")

print(f"V3 main.py length: {len(src)} chars, {src.count(chr(10))} lines")

# Search for routes definition
route_matches = re.findall(r"routes\s*=\s*\{([^}]+)\}", src)
print(f"Found {len(route_matches)} 'routes = {{...}}' occurrences")
if not route_matches:
    # search for route patterns
    for line in src.splitlines():
        if "route" in line.lower() and ("=" in line or "def " in line):
            print("  ", line[:100])
