import base64
import re
import zlib

with open("external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py", "r", encoding="utf-8") as f:
    content = f.read()

m = re.search(r'_V51_BASE_SOURCE\s*=\s*zlib\.decompress\(base64\.b85decode\(\((.*?)\)\)\)', content, re.DOTALL)
if m:
    raw = m.group(1).replace("\n", "").replace(" ", "").replace("'", "").replace('"', '')
    src = zlib.decompress(base64.b85decode(raw)).decode("utf-8")
    with open("scratch/v51_source.py", "w", encoding="utf-8") as out:
        out.write(src)
    print("Wrote scratch/v51_source.py, bytes:", len(src))
else:
    print("Pattern not found!")
