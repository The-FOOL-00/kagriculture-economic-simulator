import os, sys, hashlib, json, time

def compute_sha256(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

root_dir = r"c:\Users\Sundareswaran\Kagriculture"
manifest = {
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    "environment": {
        "python_version": sys.version,
        "kaggle_environments_version": "1.32.7",
        "engine_source_hash_kaggriculture_py": "bc8a54879ef02c7ea64b8b333d6a976f0ea65c4949149d01f463f23bccee653e",
        "engine_source_hash_kaggriculture_json": "a82c89c1a2315b93f39775d8e025471a01b738647c9772658368ee6b1b6f4867"
    },
    "files": {}
}

for root, dirs, files in os.walk(root_dir):
    if '.git' in root or '__pycache__' in root:
        continue
    for f in sorted(files):
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, root_dir).replace("\\", "/")
        size = os.path.getsize(fp)
        try:
            sha = compute_sha256(fp)
            manifest["files"][rel] = {
                "size_bytes": size,
                "sha256": sha
            }
        except Exception as e:
            manifest["files"][rel] = {
                "error": str(e)
            }

manifest_path = os.path.join(root_dir, "FORENSIC_REPOSITORY_MANIFEST.json")
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Manifest written with {len(manifest['files'])} files to {manifest_path}")
