import sys, os
sys.path.insert(0, os.path.abspath('.'))
from candidates.slot2_aethel_refined_v2 import agent as arm_a
from candidates.candidate_closed_loop_execution_v1 import agent as arm_b
from scratch.test_arm_c import arm_c_agent as arm_c
from scratch.test_arm_d import arm_d_agent as arm_d
from scratch.test_arm_e_z import arm_e_agent as arm_e
from scratch.test_arm_f import arm_f_agent as arm_f
from candidates.candidate_closed_loop_commitment_v1 import agent as arm_g
from scratch.evaluate_temporal_telemetry import run_telemetry_match

print("Testing all 7 arms on seed 42...")
for name, fn in [
    ('Arm A', arm_a), ('Arm B', arm_b), ('Arm C', arm_c),
    ('Arm D', arm_d), ('Arm E', arm_e), ('Arm F', arm_f), ('Arm G', arm_g)
]:
    res = run_telemetry_match(fn, seed=42)
    print(f"{name:<6}: Reward={res['reward']:8.1f} | Prod={res['productive']:4d} | Move={res['movement']:4d} | Idle={res['idle']:4d} | Leg={res['mean_leg']:4.2f}")
