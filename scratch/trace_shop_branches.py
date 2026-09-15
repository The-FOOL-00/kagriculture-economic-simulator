"""
scratch/trace_shop_branches.py
==============================
Section 1: Exhaustive AST and source analysis of all shop-dependent branches
across the canonical V66 lineage (V66, V65, V62, V60, V59, V58, V56, V54).

Outputs: research/shop_branch_source_map.md
"""

import os
from pathlib import Path

def generate_branch_map():
    branches = [
        {
            "id": "V66_BRANCH_01_TWOMOON",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "314-315",
            "input_state": "step == 72, not curve_active, signature == _TWOMOON_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _TWOMOON_STEP72 (where signature[0] == ('BRUNCH_SPOT',))",
            "route_selected": "yarn (_BASE._V56_YARN_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "BRUNCH_SPOT (requires exact opponent/market signature)"
        },
        {
            "id": "V66_BRANCH_02_YAT",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "316-317",
            "input_state": "step == 72, not curve_active, signature == _YAT_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _YAT_STEP72 (where signature[0] == ('FARMERS_MARKET',))",
            "route_selected": "recovery (_BASE._V58_RECOVERY_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "FARMERS_MARKET (requires exact opponent/market signature)"
        },
        {
            "id": "V66_BRANCH_03_VICTOR_ARM",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "318-320",
            "input_state": "step == 72, not curve_active, signature == _VICTOR_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _VICTOR_STEP72 (where signature[0] == ('FARMERS_MARKET',))",
            "route_selected": "state['victor_armed'] = True",
            "first_step": 72,
            "last_step": 143,
            "shop_dependency": "FARMERS_MARKET (arms two-stage check)"
        },
        {
            "id": "V66_BRANCH_03_VICTOR_CONFIRM",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "340-345",
            "input_state": "step == 144, state['victor_armed'], signature == _VICTOR_STEP144",
            "exact_condition": "step == 144 and state['victor_armed'] and _public_signature(obs) == _VICTOR_STEP144 (where signature[0] == ('FARMERS_MARKET', 'YARN_STORE'))",
            "route_selected": "clone (_BASE._V58_CLONE_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "FARMERS_MARKET + YARN_STORE"
        },
        {
            "id": "V66_BRANCH_04_BAKERY_STAGE1",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "321-322",
            "input_state": "step == 72, not curve_active, signature == _BAKERY_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _BAKERY_STEP72 (where signature[0] == ('BAKERY',))",
            "route_selected": "bakery_yarn (_BASE._V58_BAKERY_YARN_ROUTE)",
            "first_step": 72,
            "last_step": 143,
            "shop_dependency": "BAKERY"
        },
        {
            "id": "V66_BRANCH_04_BAKERY_STAGE2",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "346-348",
            "input_state": "step == 144, state['branch'] == 'bakery', second shop observed",
            "exact_condition": "step == 144 and state['branch'] == 'bakery' and (second == 'YARN_STORE' -> 'bakery_yarn' else 'recovery')",
            "route_selected": "bakery_yarn (_BASE._V58_BAKERY_YARN_ROUTE) if second == 'YARN_STORE' else recovery (_BASE._V58_RECOVERY_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "BAKERY + YARN_STORE"
        },
        {
            "id": "V66_BRANCH_05_FARMERS_STAGE1",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "323-324",
            "input_state": "step == 72, not curve_active, signature == _FARMERS_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _FARMERS_STEP72 (where signature[0] == ('FARMERS_MARKET',))",
            "route_selected": "recovery (_BASE._V58_RECOVERY_ROUTE)",
            "first_step": 72,
            "last_step": 143,
            "shop_dependency": "FARMERS_MARKET"
        },
        {
            "id": "V66_BRANCH_05_FARMERS_STAGE2",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "349-351",
            "input_state": "step == 144, state['branch'] == 'farmers', second shop observed",
            "exact_condition": "step == 144 and state['branch'] == 'farmers' and (second == 'YARN_STORE' -> 'yarn' else 'recovery')",
            "route_selected": "yarn (_BASE._V56_YARN_ROUTE) if second == 'YARN_STORE' else recovery (_BASE._V58_RECOVERY_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "FARMERS_MARKET + YARN_STORE (Key driver of seeds 204 & 208!)"
        },
        {
            "id": "V66_BRANCH_06_NEIBYR",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "325-326",
            "input_state": "step == 72, not curve_active, signature == _NEIBYR_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _NEIBYR_STEP72 (where signature[0] == ('PIZZA_SHOP',))",
            "route_selected": "recovery (_BASE._V58_RECOVERY_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "PIZZA_SHOP"
        },
        {
            "id": "V66_BRANCH_07_C0NRAD",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "327-328",
            "input_state": "step == 72, not curve_active, signature == _C0NRAD_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _C0NRAD_STEP72 (where signature[0] == ('FARMERS_MARKET',))",
            "route_selected": "ice_minimax (_BASE._V58_ICE_MINIMAX_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "FARMERS_MARKET"
        },
        {
            "id": "V66_BRANCH_08_JOHNBLAKE",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "329-330",
            "input_state": "step == 72, not curve_active, signature == _JOHNBLAKE_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _JOHNBLAKE_STEP72 (where signature[0] == ('BRUNCH_SPOT',))",
            "route_selected": "known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "BRUNCH_SPOT"
        },
        {
            "id": "V66_BRANCH_09_STEPHEN",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "331-332",
            "input_state": "step == 72, not curve_active, signature == _STEPHEN_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _STEPHEN_STEP72 (where signature[0] == ('BRUNCH_SPOT',))",
            "route_selected": "known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "BRUNCH_SPOT"
        },
        {
            "id": "V66_BRANCH_10_COKE_ARM",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "333-335",
            "input_state": "step == 72, not curve_active, signature == _COKE_STEP72",
            "exact_condition": "step == 72 and not curve_active and signature == _COKE_STEP72 (where signature[0] == ('ICE_CREAM_SHOP',))",
            "route_selected": "state['coke_armed'] = True",
            "first_step": 72,
            "last_step": 143,
            "shop_dependency": "ICE_CREAM_SHOP"
        },
        {
            "id": "V66_BRANCH_10_COKE_CONFIRM",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v66_meta_closed_loop.py",
            "function": "_advance(obs, visible)",
            "line": "352-357",
            "input_state": "step == 144, state['coke_armed'], signature == _COKE_STEP144",
            "exact_condition": "step == 144 and state['coke_armed'] and _public_signature(obs) == _COKE_STEP144 (where signature[0] == ('ICE_CREAM_SHOP', 'BRUNCH_SPOT'))",
            "route_selected": "known_yarn (_BASE._V58_KNOWN_YARN_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "ICE_CREAM_SHOP + BRUNCH_SPOT"
        },
        {
            "id": "V65_BRANCH_11_CYGN_CLONE",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v65_curve_cygn_clone.py",
            "function": "kaggle_agent_v65_curve_cygn_clone",
            "line": "41-43",
            "input_state": "curve_active, step >= 144, shops == ('YARN_STORE', 'PIZZA_SHOP')",
            "exact_condition": "curve_active and step >= 144 and tuple(_BASE._v58_shops(obs)[:2]) == ('YARN_STORE', 'PIZZA_SHOP')",
            "route_selected": "_CLONE (_BASE._V58_CLONE_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "YARN_STORE + PIZZA_SHOP"
        },
        {
            "id": "V65_BRANCH_12_KNOWN_YARN_REPAIR",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v65_curve_q2_known_yarn_repair.py",
            "function": "kaggle_agent_v65_curve_q2_known_yarn_repair",
            "line": "110-113",
            "input_state": "step == 72, curve_active, signature == _CURVE_Q2_REPAIR_STEP72",
            "exact_condition": "step == 72 and curve_active and _public_signature(obs) == _CURVE_Q2_REPAIR_STEP72 (where signature[0] == ('FARMERS_MARKET',))",
            "route_selected": "_KNOWN_YARN (_BASE._V58_KNOWN_YARN_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "FARMERS_MARKET"
        },
        {
            "id": "V65_BRANCH_13_DANIEL_BACKBONE",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v65_curve_q2_daniel_backbone.py",
            "function": "kaggle_agent_v65_curve_q2_daniel_backbone",
            "line": "53-56",
            "input_state": "step == 72, curve_active, signature == _DANIEL_STEP72",
            "exact_condition": "step == 72 and curve_active and _Q2._public_signature(obs) == (('SMOOTHIE_SHOP',),) + ...",
            "route_selected": "_BACKBONE (_BASE._V56_BACKBONE_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "SMOOTHIE_SHOP"
        },
        {
            "id": "V65_BRANCH_14_ATTACK_YARN",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v65_local_combined.py",
            "function": "_attack_advance",
            "line": "96-102",
            "input_state": "step == 72, state['armed'] (from step 1), signature matches _attack_step72_signature",
            "exact_condition": "shops[0] in {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET'} and mine money 149, rival 724, wheat 9975/30",
            "route_selected": "base_yarn (_BASE._V56_YARN_ROUTE)",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "BAKERY / BRUNCH_SPOT / FARMERS_MARKET"
        },
        {
            "id": "V62_BRANCH_15_DEFAULT_FIRST_YARN",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v58_base_action / _v59_route",
            "line": "3656 / 3902-3903",
            "input_state": "shops[0] == 'YARN_STORE'",
            "exact_condition": "first == 'YARN_STORE'",
            "route_selected": "_V56_YARN_ROUTE",
            "first_step": 72,
            "last_step": 718,
            "shop_dependency": "YARN_STORE (Pure public shop rule! No opponent matching required!)"
        },
        {
            "id": "V62_BRANCH_16_PET_CAFE_ROUTE",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v58_base_action / _v59_route",
            "line": "3658-3662 / 3904-3910",
            "input_state": "first == 'PET_CAFE', future_step >= 144, shops[1] in _V57_PET_SECOND_SHOPS",
            "exact_condition": "first == 'PET_CAFE' and step >= 144 and len(shops) >= 2 and shops[1] in {'BAKERY', 'BRUNCH_SPOT', 'FARMERS_MARKET', 'ICE_CREAM_SHOP', 'PET_CAFE', 'PIZZA_SHOP', 'SMOOTHIE_SHOP', 'YARN_STORE'}",
            "route_selected": "_V57_PET_ROUTE",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "PET_CAFE + any legal second shop"
        },
        {
            "id": "V58_BRANCH_17_FARMERS_SMOOTHIE",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v59_route",
            "line": "3880-3883",
            "input_state": "mode == 'farmers-recovery', step >= 144, shops[1] == 'SMOOTHIE_SHOP'",
            "exact_condition": "mode == 'farmers-recovery' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'SMOOTHIE_SHOP'",
            "route_selected": "_V58_SMOOTHIE_ROUTE (else _V58_RECOVERY_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "FARMERS_MARKET (step 72) + SMOOTHIE_SHOP (step 144)"
        },
        {
            "id": "V58_BRANCH_18_BAKERY_YARN",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v59_route",
            "line": "3888-3891",
            "input_state": "mode == 'bakery-second-shop', step >= 144, shops[1] == 'YARN_STORE'",
            "exact_condition": "mode == 'bakery-second-shop' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'YARN_STORE'",
            "route_selected": "_V58_BAKERY_YARN_ROUTE (else _V56_BACKBONE_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "BAKERY (step 72) + YARN_STORE (step 144)"
        },
        {
            "id": "V58_BRANCH_19_PIZZA_PET",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v59_route",
            "line": "3892-3895",
            "input_state": "mode == 'pizza-second-shop', step >= 144, shops[1] == 'PET_CAFE'",
            "exact_condition": "mode == 'pizza-second-shop' and future_step >= 144 and len(shops) >= 2 and shops[1] == 'PET_CAFE'",
            "route_selected": "_V58_PIZZA_RECOVERY_ROUTE (else _V56_BACKBONE_ROUTE)",
            "first_step": 144,
            "last_step": 718,
            "shop_dependency": "PIZZA_SHOP (step 72) + PET_CAFE (step 144)"
        },
        {
            "id": "V58_BRANCH_20_KNOWN_YARN",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v59_route / _v58_known_yarn",
            "line": "3828-3831 / 3733-3754",
            "input_state": "step == 96, shops[0] == 'YARN_STORE', signature matches known continuation",
            "exact_condition": "shops[0] == 'YARN_STORE' and (mine, opp, wheat, animals) in {(214, 214, 9982, 4, 2, 7, 12), (215, 125, 9979, 4, 2, 7, 12)}",
            "route_selected": "_V58_KNOWN_YARN_ROUTE",
            "first_step": 96,
            "last_step": 718,
            "shop_dependency": "YARN_STORE"
        },
        {
            "id": "V58_BRANCH_21_CLONE",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v59_route",
            "line": "3833-3841",
            "input_state": "step >= 72, shops[0] == 'YARN_STORE', mirror_streak >= 240 at step 360",
            "exact_condition": "shops[0] == 'YARN_STORE' and step >= 360 and mirror_streak >= 240",
            "route_selected": "_V58_CLONE_ROUTE",
            "first_step": 360,
            "last_step": 718,
            "shop_dependency": "YARN_STORE + exact opponent public farm clone"
        },
        {
            "id": "V56_BRANCH_22_BASE_BACKBONE",
            "source_file": "external_repos/kaggriculture-v66-agent/candidate_v62_composite_bakery_yarn.py",
            "function": "_v59_route",
            "line": "3911",
            "input_state": "Default fallback if no shop branch condition triggers",
            "exact_condition": "True (fallback default)",
            "route_selected": "_V56_BACKBONE_ROUTE",
            "first_step": 0,
            "last_step": 718,
            "shop_dependency": "None (default macro backbone prior)"
        },
        {
            "id": "V54_BRANCH_23_STATIC_ROUTE",
            "source_file": "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py",
            "function": "kaggle_agent",
            "line": "1-120",
            "input_state": "All steps",
            "exact_condition": "None (Zero shop adaptation; completely blind to unlocked_shops)",
            "route_selected": "r007-1-flow3-h2q4 static route",
            "first_step": 0,
            "last_step": 718,
            "shop_dependency": "None (Blind to all town shops)"
        }
    ]

    os.makedirs("research", exist_ok=True)
    out_path = Path("research/shop_branch_source_map.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# Canonical V66 Lineage: Comprehensive Shop-Dependent Branch Source Map\n\n")
        f.write("This document exhaustively catalogs every route decision, mode switch, and conditional branch across the canonical lineage (**V66 $\\to$ V65 $\\to$ V62 $\\to$ V60 $\\to$ V59 $\\to$ V58 $\\to$ V56 $\\to$ V54**) that depends directly or indirectly on town shop states (`YARN_STORE`, `BAKERY`, `ICE_CREAM_SHOP`, `FARMERS_MARKET`, `PET_CAFE`, `PIZZA_SHOP`, `SMOOTHIE_SHOP`, `BRUNCH_SPOT`).\n\n")
        f.write("---\n\n")
        f.write("| Branch ID | Source File | Function | Line(s) | Trigger Step | Shop Dependency | Route Selected | Exact Predicate Expression |\n")
        f.write("| :--- | :--- | :--- | :---: | :---: | :--- | :--- | :--- |\n")
        for b in branches:
            f.write(f"| **{b['id']}** | `{Path(b['source_file']).name}` | `{b['function']}` | {b['line']} | Step {b['first_step']} | **{b['shop_dependency']}** | `{b['route_selected']}` | `{b['exact_condition']}` |\n")
        f.write("\n---\n\n")
        f.write("## Detailed Branch Forensics\n\n")
        for b in branches:
            f.write(f"### {b['id']}\n")
            f.write(f"- **Source File**: [`{b['source_file']}`](file:///{os.path.abspath(b['source_file'])})\n")
            f.write(f"- **Function**: `{b['function']}` (Lines {b['line']})\n")
            f.write(f"- **Input State**: `{b['input_state']}`\n")
            f.write(f"- **Exact Condition**: `{b['exact_condition']}`\n")
            f.write(f"- **Route Selected**: `{b['route_selected']}`\n")
            f.write(f"- **Step Range**: Steps {b['first_step']} to {b['last_step']}\n")
            f.write(f"- **Shop Dependency Analysis**: {b['shop_dependency']}\n\n")

    print(f"Generated {out_path} with {len(branches)} cataloged branches.")

if __name__ == "__main__":
    generate_branch_map()
