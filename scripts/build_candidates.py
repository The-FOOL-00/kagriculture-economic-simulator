# SPDX-License-Identifier: MIT
"""
Build Candidates A, B, C, D for Aethel-Refined V2 Causal Attribution Experiment
"""

import os

def main():
    os.makedirs("agents", exist_ok=True)
    
    with open("replays/raw/reference_agents/closer_cleo.py", "r", encoding="utf-8") as f:
        cleo = f.read()

    # Candidate A: Exact Closer Cleo (Anchor Champion)
    with open("agents/candidate_a_aethel_v1.py", "w", encoding="utf-8") as f:
        f.write(cleo)

    # Candidate B: Market Controller (No Front-Run, Baseline T717)
    cand_b = cleo.replace("_FRONT_RUN_HORIZON = 1", "_FRONT_RUN_HORIZON = 0")
    with open("agents/candidate_b_aethel_mc.py", "w", encoding="utf-8") as f:
        f.write(cand_b)

    # Candidate C: Step-712 Terminal (No Market Controller, No Front-Run)
    cand_c = cleo.replace("_FRONT_RUN_HORIZON = 1", "_FRONT_RUN_HORIZON = 0")
    # Replace step >= 717 with step >= 712 in _base_agent
    cand_c = cand_c.replace("if step >= 717:", "if step >= 712:")
    # Disable market controller in agent(obs, config)
    target_mc = 'def agent(obs, config=None):\n    """c27 with its SELL layer partially replaced by the market controller."""\n    action = _base_agent(obs, config)'
    replacement_mc = 'def agent(obs, config=None):\n    return _base_agent(obs, config)'
    assert target_mc in cand_c, "Failed to locate agent market controller in candidate C"
    cand_c = cand_c.replace(target_mc, replacement_mc)
    with open("agents/candidate_c_aethel_t712.py", "w", encoding="utf-8") as f:
        f.write(cand_c)

    # Candidate D: Aethel-Refined (Market Controller + Step-712 Terminal, No Front-Run)
    cand_d = cleo.replace("_FRONT_RUN_HORIZON = 1", "_FRONT_RUN_HORIZON = 0")
    # Replace step >= 717 with step >= 712 in both _base_agent and agent
    cand_d = cand_d.replace("if step >= 717:", "if step >= 712:")
    with open("agents/candidate_d_aethel_refined.py", "w", encoding="utf-8") as f:
        f.write(cand_d)

    print("Successfully built Candidates A, B, C, D in agents/ directory.")

if __name__ == "__main__":
    main()
