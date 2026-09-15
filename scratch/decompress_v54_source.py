import base64, zlib, re

with open('external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'_V51_BASE_SOURCE = zlib\.decompress\(base64\.b85decode\(\s*\((.*?)\)\s*\)\)\.decode\("utf-8"\)', content, re.DOTALL)
if m:
    b85 = m.group(1).replace("'", "").replace("\n", "").replace(" ", "")
    src = zlib.decompress(base64.b85decode(b85.encode('ascii'))).decode('utf-8')
    with open('scratch/v51_base_source_decompressed.py', 'w', encoding='utf-8') as out:
        out.write(src)
    print(f'Decompressed V51 source: {len(src.splitlines())} lines written to scratch/v51_base_source_decompressed.py')
else:
    print('Pattern not matched')
