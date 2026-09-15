import base64
import zlib
import re
import os
import hashlib
import json

print("================================================================")
print("RECURSIVE UNWRAPPING OF NESTED COMPRESSION LINEAGE (RULE 12)")
print("================================================================")

current_source = open(r"external_repos\lixingtao123-Kaggriculture\variant_v54_h3q4\main.py", "r", encoding="utf-8").read()
layer_idx = 0
lineage_report = []

while True:
    layer_name = f"layer{layer_idx}"
    h = hashlib.sha256(current_source.encode("utf-8")).hexdigest()
    first_lines = [l.strip() for l in current_source.splitlines()[:5] if l.strip()]
    docstring = first_lines[0] if first_lines else ""
    
    out_path = f"forensic_verification/extracted_sources/layer_{layer_idx}.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(current_source)
        
    print(f"\n--- LAYER {layer_idx} ---")
    print(f"File: {out_path} ({len(current_source)} bytes, {len(current_source.splitlines())} lines)")
    print(f"SHA256: {h}")
    print(f"Header: {docstring}")
    
    # Check what symbols are present
    funcs = re.findall(r'def\s+([a-zA-Z0-9_]+)\s*\(', current_source)
    routes = list(set(re.findall(r'(_[A-Z0-9_]*ROUTE[A-Z0-9_]*)', current_source)))
    
    # Find any nested zlib.decompress(base64.b85decode( ... ))
    m = re.search(r'([a-zA-Z0-9_]+_SOURCE)\s*=\s*zlib\.decompress\(base64\.b85decode\(\s*\((.*?)\)\s*\)\)', current_source, re.DOTALL)
    
    lineage_report.append({
        "layer": layer_idx,
        "file": out_path,
        "size_bytes": len(current_source),
        "line_count": len(current_source.splitlines()),
        "sha256": h,
        "header": docstring,
        "functions_count": len(funcs),
        "functions_sample": funcs[:10],
        "route_symbols": routes,
        "has_nested_source": bool(m),
        "nested_source_var": m.group(1) if m else None
    })
    
    if not m:
        print(f"Reached bottom layer at Layer {layer_idx}! No further compressed source found.")
        break
        
    var_name = m.group(1)
    raw_b85_code = m.group(2)
    b85_str = eval(f"({raw_b85_code})")
    decompressed_bytes = zlib.decompress(base64.b85decode(b85_str))
    current_source = decompressed_bytes.decode("utf-8", errors="replace")
    layer_idx += 1

with open(r"forensic_verification\extracted_sources\lineage_manifest.json", "w", encoding="utf-8") as f:
    json.dump(lineage_report, f, indent=2)

print("\nLineage extraction completed. Saved forensic_verification/extracted_sources/lineage_manifest.json")
