import sys, zlib, base64, re, os, json
sys.stdout.reconfigure(encoding='utf-8')

with open('external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

m = re.search(r'_V51_BASE_SOURCE\s*=\s*zlib\.decompress\(base64\.b85decode\(\(\s*(.*?)\s*\)\)\)', text, re.DOTALL)
if m:
    raw_b85 = m.group(1).replace("'", "").replace("\n", "").replace(" ", "")
    decompressed = zlib.decompress(base64.b85decode(raw_b85)).decode('utf-8', errors='ignore')
    print('Decompressed size:', len(decompressed), 'characters')
    print('=== Header of decompressed base source ===')
    print(decompressed[:2000])
else:
    print('Regex match failed!')
