import sys, os, json, zlib, base64

with open('forensic_verification/extracted_sources/layer_1.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

b85_lines = []
for l in lines[1408:]:
    ls = l.strip()
    if ls.startswith("'") and ls.endswith("'"):
        b85_lines.append(eval(ls))
    elif ls.startswith(")") and b85_lines:
        break

full_b85 = ''.join(b85_lines)
v50_mods = json.loads(zlib.decompress(base64.b85decode(full_b85)).decode('utf-8'))
print('V50 modules:', list(v50_mods.keys()))
for k, v in v50_mods.items():
    print(f'Module {k}: {len(v)} bytes, {len(v.splitlines())} lines')

with open('scratch/v50_hybrid_source.py', 'w', encoding='utf-8') as out:
    out.write(v50_mods.get('v50.hybrid', ''))
print('Saved scratch/v50_hybrid_source.py')
