import base64
import zlib
import json
import os
import hashlib

print("================================================================")
print("EXTRACTING EMBEDDED MODULES FROM V49 (RULE 11 & RULE 12)")
print("================================================================")

with open(r"forensic_verification/extracted_sources/layer_2.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find line 35 to 524
b85_lines = []
for line in lines[36:523]:
    line_s = line.strip()
    if line_s.startswith("'") and line_s.endswith("'"):
        b85_lines.append(eval(line_s))

full_b85 = "".join(b85_lines)
decomp = zlib.decompress(base64.b85decode(full_b85)).decode("utf-8")
modules = json.loads(decomp)

print(f"Successfully unpacked {len(modules)} modules from _V49_MODULES!")

out_dir = r"forensic_verification\extracted_sources\v49_modules"
os.makedirs(out_dir, exist_ok=True)

manifest = []
for name, code in modules.items():
    safe_name = name.replace(".", "_") + ".py"
    out_path = os.path.join(out_dir, safe_name)
    with open(out_path, "w", encoding="utf-8") as out:
        out.write(code)
    
    h = hashlib.sha256(code.encode("utf-8")).hexdigest()
    first_lines = [l.strip() for l in code.splitlines()[:3] if l.strip()]
    doc = first_lines[0] if first_lines else ""
    manifest.append({
        "module_name": name,
        "filename": safe_name,
        "size_bytes": len(code),
        "lines": len(code.splitlines()),
        "sha256": h,
        "summary": doc
    })
    print(f"Extracted: {name:32s} -> {safe_name:30s} ({len(code):5d} B, {len(code.splitlines()):3d} lines, sha256: {h[:12]}...)")

with open(r"forensic_verification\extracted_sources\v49_modules_manifest.json", "w", encoding="utf-8") as f:
    json.dump(manifest, f, indent=2)

print("\nManifest written to forensic_verification/extracted_sources/v49_modules_manifest.json")
