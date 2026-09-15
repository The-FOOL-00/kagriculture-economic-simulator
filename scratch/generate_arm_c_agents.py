"""
Generator for Arm C Alternative Fixed Portfolios:
- C1: Strawberry-Heavy (48 Strawberry, 8 Melon, 10 Wheat, 14 Pasture)
- C2: Melon-Heavy (32 Strawberry, 24 Melon, 10 Wheat, 14 Pasture)
- C3: Balanced (36 Strawberry, 12 Melon, 20 Wheat, 14 Pasture)
"""

import re

with open("candidates/candidate_cl_fixed_zoning_v1.py", "r") as f:
    base_code = f.read()

# Generate C1: Strawberry-Heavy
c1_code = base_code.replace(
    'target_straw = 40 if day >= 7 else (8 if day < 6 else 16)',
    'target_straw = 48 if day >= 7 else (12 if day < 6 else 24)'
).replace(
    'target_melons = 7 if day < 7 else (12 if day < 11 else 16)',
    'target_melons = 4 if day < 7 else (6 if day < 11 else 8)'
).replace(
    'class ClosedLoopFixedZoningV1:',
    'class ClosedLoopFixedStrawHeavy:'
).replace(
    '_FIXED_ZONING_AGENT = ClosedLoopFixedZoningV1()',
    '_FIXED_ZONING_AGENT = ClosedLoopFixedStrawHeavy()'
)

with open("candidates/candidate_cl_fixed_straw_heavy.py", "w") as f:
    f.write(c1_code)

# Generate C2: Melon-Heavy
c2_code = base_code.replace(
    'target_straw = 40 if day >= 7 else (8 if day < 6 else 16)',
    'target_straw = 32 if day >= 7 else (8 if day < 6 else 16)'
).replace(
    'target_melons = 7 if day < 7 else (12 if day < 11 else 16)',
    'target_melons = 10 if day < 7 else (16 if day < 11 else 24)'
).replace(
    'class ClosedLoopFixedZoningV1:',
    'class ClosedLoopFixedMelonHeavy:'
).replace(
    '_FIXED_ZONING_AGENT = ClosedLoopFixedZoningV1()',
    '_FIXED_ZONING_AGENT = ClosedLoopFixedMelonHeavy()'
)

with open("candidates/candidate_cl_fixed_melon_heavy.py", "w") as f:
    f.write(c2_code)

# Generate C3: Balanced
c3_code = base_code.replace(
    'target_straw = 40 if day >= 7 else (8 if day < 6 else 16)',
    'target_straw = 36 if day >= 7 else (8 if day < 6 else 16)'
).replace(
    'target_melons = 7 if day < 7 else (12 if day < 11 else 16)',
    'target_melons = 6 if day < 7 else (9 if day < 11 else 12)'
).replace(
    'wheat_s < 26',
    'wheat_s < 35'
).replace(
    'can_buy_w = min(26 - wheat_s, min(26, int((money - 200) // 10)))',
    'can_buy_w = min(35 - wheat_s, min(35, int((money - 200) // 10)))'
).replace(
    'class ClosedLoopFixedZoningV1:',
    'class ClosedLoopFixedBalanced:'
).replace(
    '_FIXED_ZONING_AGENT = ClosedLoopFixedZoningV1()',
    '_FIXED_ZONING_AGENT = ClosedLoopFixedBalanced()'
)

with open("candidates/candidate_cl_fixed_balanced.py", "w") as f:
    f.write(c3_code)

print("Created C1 (Strawberry-Heavy), C2 (Melon-Heavy), and C3 (Balanced) successfully.")
