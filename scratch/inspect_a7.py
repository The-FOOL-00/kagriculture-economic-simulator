import base64
import zlib
import re

with open('candidates/v30_a7_standalone/main.py', 'r') as f:
    text = f.read()

m = re.search(r'_V3_SRC = zlib\.decompress\(base64\.b64decode\((b"[^"]+")\)\)', text)
if not m:
    m = re.search(r"_V3_SRC = zlib\.decompress\(base64\.b64decode\((b'[^']+')\)\)", text)

if m:
    b_lit = eval(m.group(1))
    src = zlib.decompress(base64.b64decode(b_lit)).decode('utf-8')
    print('Decompressed length:', len(src), 'chars, lines:', src.count('\n'))
    with open('scratch/v3_decompressed.py', 'w', encoding='utf-8') as out:
        out.write(src)
    print('Saved decompressed source to scratch/v3_decompressed.py')
else:
    print('Pattern not matched')
