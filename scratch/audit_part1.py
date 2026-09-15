import sys
import os
import ast
import hashlib
import shutil
import tempfile
import warnings
import kaggle_environments

def check_ast(filepath):
    print("--- 1. AST and Static Inspection ---")
    with open(filepath, "rb") as f:
        content = f.read()
    sha256 = hashlib.sha256(content).hexdigest()
    print(f"File: {filepath}")
    print(f"SHA256: {sha256}")
    assert sha256 == "3fe18be5fad8b4c79fe27c8a50d316c857cecb87545d52a94e91b49e153bc2e6", "Hash mismatch!"

    tree = ast.parse(content.decode('utf-8'))
    
    # Check imports
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append(n.name)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module)
    
    print(f"Imported modules: {imports}")
    disallowed = ["candidates", "agents", "scratch", "reports", "engine", "scripts", "subprocess", "socket", "urllib", "requests", "http"]
    for imp in imports:
        if imp:
            for dis in disallowed:
                assert not imp.startswith(dis), f"Disallowed import: {imp}"
    
    # Check for exec, eval, open, os.environ, __import__
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in ["exec", "eval", "__import__", "compile"], f"Dynamic code loading call: {node.func.id}"
                # If open is used:
                assert node.func.id != "open", "File open() call detected!"
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr in ["environ", "getenv", "system", "popen"]:
                    assert False, f"OS interaction detected: {node.func.attr}"
        elif isinstance(node, ast.Attribute):
            if node.attr in ["environ"]:
                assert False, "Environment variable access detected!"
    
    # Check for recursion in functions
    func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    for fdef in func_defs:
        for node in ast.walk(fdef):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == fdef.name:
                    assert False, f"Direct recursion detected in {fdef.name}"
    
    print("Static AST checks PASSED: Zero forbidden imports, zero network/os calls, zero file access, zero recursion.")

def run_isolated_episodes(filepath, num_seeds=20):
    print(f"\n--- 2. Isolated Execution of 20 Episodes as main.py ---")
    seeds = list(range(865000, 865000 + num_seeds))
    
    temp_dir = tempfile.mkdtemp(prefix="kagg_audit_p1_")
    print(f"Created temporary directory: {temp_dir}")
    dest_file = os.path.join(temp_dir, "main.py")
    shutil.copyfile(filepath, dest_file)
    
    repo_root = os.path.abspath(".")
    # Clean sys.path
    clean_sys_path = [p for p in sys.path if os.path.abspath(p) != repo_root and "Kagriculture" not in p or "site-packages" in p]
    
    orig_path = list(sys.path)
    orig_cwd = os.getcwd()
    
    try:
        sys.path = clean_sys_path
        os.chdir(temp_dir)
        
        with warnings.catch_warnings(record=True) as w_list:
            warnings.simplefilter("always")
            for i, seed in enumerate(seeds):
                cfg = {"episodeSteps": 720, "seed": seed}
                env = kaggle_environments.make("kaggriculture", configuration=cfg)
                steps = env.run(["main.py", "starter"])
                
                p0 = steps[-1][0]
                status = p0["status"]
                reward = float(p0["reward"])
                
                # Check for step errors
                for s_idx, step_data in enumerate(steps):
                    agent_st = step_data[0]
                    act = agent_st.get("action")
                    # Schema check
                    if s_idx > 0:
                        assert act is not None, f"Seed {seed} step {s_idx} had null action!"
                        assert isinstance(act, (list, tuple, str, dict, kaggle_environments.utils.Struct)), f"Seed {seed} step {s_idx} action is not valid schema: {type(act)}"
                
                assert status == "DONE", f"Seed {seed} status failed: {status}"
                assert reward > 3000.0, f"Seed {seed} passive reward: {reward}"
                print(f"Episode {i+1:02d}/{num_seeds} [Seed {seed}]: status={status}, reward={reward:.2f}, steps={len(steps)}")
            
            print(f"Total warnings recorded across {num_seeds} episodes: {len(w_list)}")
            assert len(w_list) == 0, f"Unexpected warnings: {[str(w.message) for w in w_list]}"
            
    finally:
        os.chdir(orig_cwd)
        sys.path = orig_path
        shutil.rmtree(temp_dir, ignore_errors=True)
        
    print(f"Isolated 20-episode audit PASSED: 0 crashes, 0 warnings, 0 exceptions, 0 null-actions.")

if __name__ == "__main__":
    filepath = os.path.abspath("candidates/compiled_research_b_only_v2.py")
    check_ast(filepath)
    run_isolated_episodes(filepath, num_seeds=20)
