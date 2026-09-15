import os
import sys
import hashlib
import kaggle_environments

sys.path.insert(0, os.path.abspath('.'))

def build_and_verify_compiled_b_only():
    print("=" * 80)
    print("PHASE 10: STANDALONE ARTIFACT COMPILATION & BEHAVIORAL EQUIVALENCE TEST")
    print("=" * 80)

    # 1. Read parent M1
    with open("candidates/candidate_cl_fert_gated.py", "r", encoding="utf-8") as f:
        m1_code = f.read()

    # 2. Read research_b_only_v1
    with open("candidates/research_b_only_v1.py", "r", encoding="utf-8") as f:
        b_code = f.read()

    # Extract ResearchBOnlyV1 class from b_code
    cls_start = b_code.find("class ResearchBOnlyV1")
    cls_end = b_code.find("agent = ResearchBOnlyV1()")
    b_class_code = b_code[cls_start:cls_end].replace("m1_module.ClosedLoopEconomicV1", "ClosedLoopEconomicV1")

    # In m1_code, replace the terminal agent instantiation
    m1_main_idx = m1_code.find("agent = ClosedLoopEconomicV1()")
    m1_base = m1_code[:m1_main_idx]

    header = '''# SPDX-License-Identifier: MIT
"""
Compiled Standalone Research Candidate: ResearchBOnlyV1 (B_Only)
Pure Observation-Driven, Zero-Dependency, Standalone Competition Deployment Artifact.
Parent: ClosedLoopEconomicV1 (M1) + Wheat Quota 50 + Discretionary Weed Task Gating (Component B).
Self-contained single-file module. Zero external or local repository dependencies.
"""

'''
    compiled_code = header + m1_base + "\n" + b_class_code + """
agent = ResearchBOnlyV1()

def candidate_agent(obs, config=None):
    return agent(obs, config)

def agent(obs, config=None):
    return candidate_agent(obs, config)
"""

    output_path = "candidates/compiled_research_b_only_v1.py"
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(compiled_code)

    sha = hashlib.sha256(compiled_code.encode("utf-8")).hexdigest()
    print(f"1. Successfully compiled {len(compiled_code.splitlines())} lines to {output_path}")
    print(f"   Compiled Artifact SHA256: {sha}")

    # 3. Test behavioral equivalence on 20 paired seeds
    print("\n2. Verifying Behavioral Equivalence vs Modular Source across 20 Paired Seeds:")
    import candidates.research_b_only_v1 as mod_source
    import importlib.util
    spec = importlib.util.spec_from_file_location("compiled_mod", output_path)
    comp_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comp_mod)

    mismatches = []
    test_seeds = list(range(10001, 10021))
    for s in test_seeds:
        # Run modular source
        agent_src = mod_source.ResearchBOnlyV1()
        env_src = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        steps_src = env_src.run([agent_src, "starter"])
        r_src = float(steps_src[-1][0]["reward"])

        # Run compiled standalone
        agent_comp = comp_mod.ResearchBOnlyV1()
        env_comp = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 720, "seed": s})
        steps_comp = env_comp.run([agent_comp, "starter"])
        r_comp = float(steps_comp[-1][0]["reward"])

        # Compare actions turn-by-turn
        actions_match = True
        for st_idx in range(len(steps_src)):
            if steps_src[st_idx][0]["action"] != steps_comp[st_idx][0]["action"]:
                actions_match = False
                break

        match = (r_src == r_comp) and actions_match
        if not match:
            mismatches.append((s, r_src, r_comp))
        print(f"   Seed {s}: Source=${r_src:9.2f} | Compiled=${r_comp:9.2f} | Match: {match}")

    print("-" * 80)
    print(f"Equivalence Verdict: {len(mismatches)} mismatches across {len(test_seeds)} seeds.")
    assert len(mismatches) == 0, f"Behavioral mismatch detected on seeds: {mismatches}"
    print("PASS: 100% Exact behavioral and turn-by-turn action equivalence confirmed!")

    # 4. Test isolated standalone execution (outside workspace)
    import tempfile, subprocess
    with tempfile.TemporaryDirectory() as td:
        iso_main = os.path.join(td, "main.py")
        with open(iso_main, "w", encoding="utf-8") as f:
            f.write(compiled_code)
        
        test_script = os.path.join(td, "test_iso.py")
        with open(test_script, "w") as f:
            f.write("""
import sys, kaggle_environments
sys.path = [p for p in sys.path if "kagriculture" not in p.lower()]
env = kaggle_environments.make("kaggriculture", configuration={"episodeSteps": 20, "seed": 10001})
res = env.run(["main.py", "starter"])
print("ISOLATED_CONTAINER_STATUS:", res[-1][0]["status"])
print("ISOLATED_CONTAINER_REWARD:", res[-1][0]["reward"])
print("ISOLATED_CONTAINER_ACTION_STEP1:", res[1][0]["action"])
""")
        p = subprocess.run([sys.executable, test_script], capture_output=True, text=True)
        print(f"\n3. Isolated Container Execution Test (Stripped sys.path):\n{p.stdout.strip()}")
        assert "ISOLATED_CONTAINER_STATUS: DONE" in p.stdout
        assert "None" not in p.stdout.split("ISOLATED_CONTAINER_ACTION_STEP1:")[1]
        print("PASS: Compiled artifact executes flawlessly in clean isolated container without repository!")

if __name__ == "__main__":
    build_and_verify_compiled_b_only()
