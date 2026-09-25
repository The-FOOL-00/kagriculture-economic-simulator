"""
Extract parent namespace by executing V3 up to line 12
"""
import tarfile

with tarfile.open("submission_Vj_kc_v3.tar.gz", "r:gz") as tar:
    m = tar.extractfile("main.py")
    src = m.read().decode("utf-8")

# Execute in isolated namespace
ns = {}
exec(compile(src[:src.find("del _PARENT_SRC")], "v3_init.py", "exec"), ns)
p_ns = ns.get("_PARENT_NS", {})
print("Parent NS keys:", [k for k in p_ns.keys() if not k.startswith("__")])

# Check if chassis or routes are in p_ns
for k, v in p_ns.items():
    if "chassis" in str(type(v)).lower() or hasattr(v, "routes") or hasattr(v, "router"):
        print(f"Key '{k}' is chassis/router object: {type(v)}")
        if hasattr(v, "routes"):
            print(f"  Routes count: {len(v.routes)}, keys: {list(v.routes.keys())}")
        if hasattr(v, "router"):
            print(f"  Router callable: {v.router}")
