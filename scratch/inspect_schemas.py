import os, json
import kaggle_environments

pkg_dir = os.path.dirname(kaggle_environments.__file__)
schemas_json = os.path.join(pkg_dir, 'schemas.json')
with open(schemas_json, 'r') as f:
    s = json.load(f)
print("=== SCHEMAS.JSON observation ===")
print(json.dumps(s.get("state", {}).get("properties", {}).get("observation", {}), indent=2))

kagg_json = os.path.join(pkg_dir, 'envs', 'kaggriculture', 'kaggriculture.json')
with open(kagg_json, 'r') as f:
    k = json.load(f)
print("=== KAGGRICULTURE.JSON observation ===")
print(json.dumps(k.get("observation", {}), indent=2))
