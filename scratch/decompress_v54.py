import os
import re
import base64
import zlib

with open("external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py", "r", encoding="utf-8") as f:
    code = f.read()

match = re.search(r'_V51_BASE_SOURCE = zlib\.decompress\(base64\.b85decode\(\s*\((.*?)\)\s*\)\)', code, re.DOTALL)
if match:
    raw_b85 = "".join(re.findall(r"'([^']*)'", match.group(1)))
    decompressed = zlib.decompress(base64.b85decode(raw_b85.encode("ascii"))).decode("utf-8")
    with open("scratch/v54_decompressed.py", "w", encoding="utf-8") as out:
        out.write(decompressed)
    print("Wrote scratch/v54_decompressed.py, length:", len(decompressed))
else:
    print("Pattern not matched")
