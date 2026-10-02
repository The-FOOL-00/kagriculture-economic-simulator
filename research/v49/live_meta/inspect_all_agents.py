#!/usr/bin/env python3
"""Inspect all live meta agents to find specific strategic additions."""

import os
import re

META_DIR = os.path.dirname(os.path.abspath(__file__))

def check_agent(name, filepath):
    print("=" * 80)
    print(f"AGENT: {name} ({os.path.basename(filepath)})")
    print("=" * 80)
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()

    print(f"Total lines: {len(text.splitlines())}, Size: {len(text)} bytes")

    # Search for settings / config dicts
    settings = re.findall(r'(?:DEFAULT_SETTINGS|settings|CFG|CONFIG)\s*=\s*\{([^}]+)\}', text)
    if settings:
        print("\nFound Settings/Config:")
        for s in settings[:2]:
            print(s.strip()[:400])

    # Search for router function or route names
    routes = re.findall(r'(?:def _router|def router|class Router|ROUTES|_ROUTES)[\s\S]*?(?:def |\n\n\n)', text[:40000])
    if routes:
        print("\nFound Router/Routes signature:")
        for r in routes[:2]:
            print(r.strip()[:400])

    # Search for specific techniques:
    print("\nTechnique Presence:")
    for tech in [
        "ORDERPRI", "herd_safe", "risk_aware", "feed_protect", "sale_window",
        "dead_stock", "front_run", "room_guard", "budget_guard", "lead_sale",
        "overrides", "CARROT", "COW", "SHEEP", "WEED", "FERTILIZER"
    ]:
        matches = len(re.findall(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE))
        if matches:
            print(f"  - {tech}: {matches} matches")

def main():
    targets = [
        ("abhinav_cha22", os.path.join(META_DIR, "abhinav_cha22", "cha22-agent_extracted.py")),
        ("arsgorynich_herdsafe_v3", os.path.join(META_DIR, "arsgorynich_herdsafe_v3", "unpacked_b85_0.py")),
        ("flexonafft_multiroute", os.path.join(META_DIR, "flexonafft_multiroute", "kaggriculture-multi-route-farming-agent_extracted.py")),
        ("guruprasaath_master_v3", os.path.join(META_DIR, "guruprasaath_master_v3", "kaggriculture-master-engine-v3_extracted.py")),
        ("haideptry_shepherd", os.path.join(META_DIR, "haideptry_shepherd", "the-shepherds-ledger-herd-safe-sovereign_extracted.py")),
        ("statma_ca25", os.path.join(META_DIR, "statma_ca25", "unpacked_b64_0.py")),
        ("wzhengbiao_v15stack", os.path.join(META_DIR, "wzhengbiao_v15stack", "kaggriculture-v15stack-submit.py")),
    ]

    for name, path in targets:
        if os.path.exists(path):
            check_agent(name, path)
        else:
            print(f"File not found: {path}")

if __name__ == '__main__':
    main()
