import base64
import zlib
import re
import os

for ver in ['v24', 'v27']:
    path = f'research/final_synthesis/teammates/{ver}/main.py'
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    match = re.search(r"_INNER_SRC_BLOB\s*=\s*'([^']+)'", src)
    if not match:
        match = re.search(r'_INNER_SRC_BLOB\s*=\s*"([^"]+)"', src)
    if match:
        blob = match.group(1).strip()
        decoded = zlib.decompress(base64.b85decode(blob)).decode('utf-8')
        out_path = f'research/final_synthesis/teammates/{ver}/decoded_inner.py'
        with open(out_path, 'w', encoding='utf-8') as out_f:
            out_f.write(decoded)
        print(f'{ver} decoded successfully! Length: {len(decoded)} chars, {decoded.count(chr(10))} lines. Saved to {out_path}')
    else:
        print(f'Failed to find _INNER_SRC_BLOB in {ver}')
