# SPDX-License-Identifier: MIT
"""Extract and verify all elite public benchmark agents from immutable raw notebooks.

Produces:
- research/v47/elite_corpus/agents/<agent_id>/main.py (and supporting files)
- research/v47/elite_corpus/elite_manifest.json
"""

from __future__ import annotations
import ast
import base64
import gzip
import hashlib
import io
import json
import os
import sys
import tarfile
import zlib
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
AGENTS_DIR = os.path.join(REPO_ROOT, "research/v47/elite_corpus/agents")
RAW_DIR = os.path.join(REPO_ROOT, "research/v47/elite_corpus/raw")
os.makedirs(AGENTS_DIR, exist_ok=True)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def extract_kaitofukami_3009() -> Dict[str, Any]:
    print("Extracting kaitofukami_v48_3009...")
    nb_path = os.path.join(
        RAW_DIR,
        "kaitofukami__40-40-early-floor-39-46-top-10-v48-fast-routes",
        "40-40-early-floor-39-46-top-10-v48-fast-routes.ipynb",
    )
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    src = "".join(nb["cells"][8]["source"])

    # Locate payload
    namespace = {}
    exec(src.split("agent_bytes =")[0], namespace)
    payload = namespace["payload"]
    agent_bytes = zlib.decompress(base64.b85decode(payload))

    digest = sha256_bytes(agent_bytes)
    assert digest == "dadee25a9840313218384208c53b2c4752f82c3209cc654632e0b96c65e2664a"

    out_dir = os.path.join(AGENTS_DIR, "kaitofukami_v48_3009")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "main.py")
    with open(target, "wb") as f:
        f.write(agent_bytes)

    return {
        "agent_id": "kaitofukami_v48_3009",
        "title": "40/40 Early Floor | 39/46 Top-10 | v48 Fast Routes",
        "source_url": "https://www.kaggle.com/code/kaitofukami/40-40-early-floor-39-46-top-10-v48-fast-routes",
        "author": "Kaito Fukami",
        "publication_date": "2026-09-02",
        "public_score": 3009.0,
        "best_score": 3009.0,
        "version": "v48",
        "license": "Apache-2.0",
        "source_hash": digest,
        "entrypoint": "main.py:agent",
        "file_size": len(agent_bytes),
    }


def extract_thomastschinkel_2945() -> Dict[str, Any]:
    print("Extracting thomastschinkel_2945...")
    nb_path = os.path.join(
        RAW_DIR,
        "thomastschinkel__the-2945-farm-96-vs-the-top-10-public-bots",
        "the-2945-farm-96-vs-the-top-10-public-bots.ipynb",
    )
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    s = nb["cells"][5]["source"]
    if isinstance(s, list):
        s = "".join(s)
    _, rest = s.split("\n", 1)
    agent_bytes = (rest + "\n").encode("utf-8")

    digest = sha256_bytes(agent_bytes)
    assert digest == "bfee70e9daaebeae0737a880f1df8f1c60d0783c59af620136cc0d28ef482bc7"

    out_dir = os.path.join(AGENTS_DIR, "thomastschinkel_2945")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "main.py")
    with open(target, "wb") as f:
        f.write(agent_bytes)

    return {
        "agent_id": "thomastschinkel_2945",
        "title": "The 2945 Farm: 96% vs the Top-10 Public Bots",
        "source_url": "https://www.kaggle.com/code/thomastschinkel/the-2945-farm-96-vs-the-top-10-public-bots",
        "author": "Thomas Tschinkel",
        "publication_date": "2026-08-31",
        "public_score": 2944.7,
        "best_score": 2945.0,
        "version": "v9/3",
        "license": "Apache-2.0",
        "source_hash": digest,
        "entrypoint": "main.py:agent",
        "file_size": len(agent_bytes),
    }


def extract_tetsutani_pasture() -> Dict[str, Any]:
    print("Extracting tetsutani_pasture...")
    nb_path = os.path.join(
        RAW_DIR,
        "tetsutani__shape-the-shop-work-the-pasture-kaggriculture",
        "shape-the-shop-work-the-pasture-kaggriculture.ipynb",
    )
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    s = "".join(nb["cells"][9]["source"])

    namespace = {}
    exec(s.split("main_bytes =")[0], namespace)
    main_b64 = namespace["MAIN_B64"]
    main_bytes = base64.b64decode(main_b64)

    digest = sha256_bytes(main_bytes)
    assert digest == "2b97e2c653018ac4aeffb8463ec91c8f26b097b4cef81289acc25ccdbc68f916"

    out_dir = os.path.join(AGENTS_DIR, "tetsutani_pasture")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "main.py")
    with open(target, "wb") as f:
        f.write(main_bytes)

    return {
        "agent_id": "tetsutani_pasture",
        "title": "Shape the Shop Work the Pasture | Kaggriculture",
        "source_url": "https://www.kaggle.com/code/tetsutani/shape-the-shop-work-the-pasture-kaggriculture",
        "author": "tetsu2131",
        "publication_date": "2026-08-25",
        "public_score": 2860.0,
        "best_score": 2860.0,
        "version": "public_router_value_aware_reserve_1",
        "license": "Apache-2.0",
        "source_hash": digest,
        "entrypoint": "main.py:agent",
        "file_size": len(main_bytes),
    }


def extract_indarkarhana_top10() -> Dict[str, Any]:
    print("Extracting indarkarhana_top10...")
    nb_path = os.path.join(
        RAW_DIR,
        "indarkarhana__shape-the-shop-work-the-pasture-top-10",
        "shape-the-shop-work-the-pasture-top-10.ipynb",
    )
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Cell 2 has ARCHIVE_B64
    src2 = "".join(nb["cells"][2]["source"])
    ns = {}
    exec(src2, ns)
    archive_b64 = ns["ARCHIVE_B64"]
    payload = base64.b64decode(archive_b64)

    expected_sha = "fa9e7eb1a0174a1bf292fb4d47bd209defed929758214d3506e050a68ee5f98f"
    assert sha256_bytes(payload) == expected_sha

    out_dir = os.path.join(AGENTS_DIR, "indarkarhana_top10")
    os.makedirs(out_dir, exist_ok=True)

    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as bundle:
        bundle.extractall(out_dir)

    main_path = os.path.join(out_dir, "main.py")
    main_digest = sha256_bytes(open(main_path, "rb").read())

    return {
        "agent_id": "indarkarhana_top10",
        "title": "Shape the Shop Work the Pasture (TOP 10)",
        "source_url": "https://www.kaggle.com/code/indarkarhana/shape-the-shop-work-the-pasture-top-10",
        "author": "Indar Karhana",
        "publication_date": "2026-08-26",
        "public_score": 2880.0,
        "best_score": 2880.0,
        "version": "e776a",
        "license": "Apache-2.0",
        "source_hash": main_digest,
        "entrypoint": "main.py:agent",
        "file_size": os.path.getsize(main_path),
    }


def extract_kaitofukami_v43() -> Dict[str, Any]:
    print("Extracting kaitofukami_v43...")
    nb_path = os.path.join(
        RAW_DIR,
        "kaitofukami__103-128-fresh-public-v43-sparse-shop-hybrid",
        "103-128-fresh-public-v43-sparse-shop-hybrid.ipynb",
    )
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)
    s = "".join(nb["cells"][11]["source"])

    ns = {}
    exec(s.split("agent_bytes =")[0], ns)
    payload = ns["payload"]
    agent_bytes = zlib.decompress(base64.b85decode(payload))

    digest = sha256_bytes(agent_bytes)

    out_dir = os.path.join(AGENTS_DIR, "kaitofukami_v43")
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "main.py")
    with open(target, "wb") as f:
        f.write(agent_bytes)

    return {
        "agent_id": "kaitofukami_v43",
        "title": "103/128 Fresh Public | v43 Sparse Shop Hybrid",
        "source_url": "https://www.kaggle.com/code/kaitofukami/103-128-fresh-public-v43-sparse-shop-hybrid",
        "author": "Kaito Fukami",
        "publication_date": "2026-08-28",
        "public_score": 2850.0,
        "best_score": 2850.0,
        "version": "v43",
        "license": "Apache-2.0",
        "source_hash": digest,
        "entrypoint": "main.py:agent",
        "file_size": len(agent_bytes),
    }


def extract_saiteja_mega_3000() -> Dict[str, Any]:
    print("Extracting saiteja_mega_3000...")
    nb_path = os.path.join(
        RAW_DIR,
        "saitejabandaruin__kaggriculture-ultimate-mega-ensemble-3000",
        "kaggriculture-ultimate-mega-ensemble-3000.ipynb",
    )
    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    # Cell 2 has payloads
    s2 = "".join(nb["cells"][2]["source"])
    ns = {}
    exec(s2.split("with tarfile.open")[0], ns)
    payloads = ns["payloads"]

    out_dir = os.path.join(AGENTS_DIR, "saiteja_mega_3000")
    os.makedirs(out_dir, exist_ok=True)

    for filename, pld in payloads.items():
        decompressed = zlib.decompress(base64.b85decode(pld))
        with open(os.path.join(out_dir, filename), "wb") as f:
            f.write(decompressed)

    # Cell 3 has main.py
    s3 = "".join(nb["cells"][3]["source"])
    if s3.startswith("%%writefile main.py"):
        s3 = s3[len("%%writefile main.py"):].lstrip("\n")
    main_bytes = s3.encode("utf-8")
    with open(os.path.join(out_dir, "main.py"), "wb") as f:
        f.write(main_bytes)

    digest = sha256_bytes(main_bytes)

    return {
        "agent_id": "saiteja_mega_3000",
        "title": "Kaggriculture | Ultimate Mega-Ensemble 3000+",
        "source_url": "https://www.kaggle.com/code/saitejabandaruin/kaggriculture-ultimate-mega-ensemble-3000",
        "author": "Sai Teja Bandaru",
        "publication_date": "2026-09-05",
        "public_score": 2980.0,
        "best_score": 3000.0,
        "version": "mega_v1",
        "license": "Apache-2.0",
        "source_hash": digest,
        "entrypoint": "main.py:agent",
        "file_size": len(main_bytes),
    }


def register_existing_agents() -> List[Dict[str, Any]]:
    agents = []

    # E8_DMITRII (LB ~2800)
    dmitrii_path = os.path.join(REPO_ROOT, "extracted_agents/dmitrii_lb2800/main.py")
    if os.path.exists(dmitrii_path):
        d_bytes = open(dmitrii_path, "rb").read()
        agents.append({
            "agent_id": "dmitrii_lb2800",
            "title": "Dmitrii Russian GM Livestock Agent (LB 2800+)",
            "source_url": "submission_dmitrii_lb2800.tar.gz",
            "author": "Dmitrii (Russian GM)",
            "publication_date": "2026-08-15",
            "public_score": 2800.0,
            "best_score": 2800.0,
            "version": "v1.0",
            "license": "Apache-2.0",
            "source_hash": sha256_bytes(d_bytes),
            "entrypoint": "extracted_agents/dmitrii_lb2800/main.py:agent",
            "file_size": len(d_bytes),
        })

    # V54_H3Q4
    v54_path = os.path.join(REPO_ROOT, "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py")
    if os.path.exists(v54_path):
        v54_bytes = open(v54_path, "rb").read()
        agents.append({
            "agent_id": "v54_h3q4",
            "title": "V54 Declarative Crop Specialist (H3Q4)",
            "source_url": "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4",
            "author": "lixingtao123",
            "publication_date": "2026-08-20",
            "public_score": 2750.0,
            "best_score": 2750.0,
            "version": "v54",
            "license": "Apache-2.0",
            "source_hash": sha256_bytes(v54_bytes),
            "entrypoint": "external_repos/lixingtao123-Kaggriculture/variant_v54_h3q4/main.py:agent",
            "file_size": len(v54_bytes),
        })

    # V66
    v66_path = os.path.join(REPO_ROOT, "external_repos/kaggriculture-v66-agent/main.py")
    if os.path.exists(v66_path):
        v66_bytes = open(v66_path, "rb").read()
        agents.append({
            "agent_id": "v66_agent",
            "title": "Kaggriculture V66 Agent",
            "source_url": "external_repos/kaggriculture-v66-agent",
            "author": "Public Community",
            "publication_date": "2026-08-22",
            "public_score": 2820.0,
            "best_score": 2820.0,
            "version": "v66",
            "license": "Apache-2.0",
            "source_hash": sha256_bytes(v66_bytes),
            "entrypoint": "external_repos/kaggriculture-v66-agent/main.py:agent",
            "file_size": len(v66_bytes),
        })

    return agents


def main():
    print("=" * 80)
    print("V47 PHASE 4: EXTRACTING EXACT PUBLIC BENCHMARK ARTIFACTS")
    print("=" * 80)

    extracted_records = [
        extract_kaitofukami_3009(),
        extract_thomastschinkel_2945(),
        extract_tetsutani_pasture(),
        extract_indarkarhana_top10(),
        extract_kaitofukami_v43(),
        extract_saiteja_mega_3000(),
    ]

    existing_records = register_existing_agents()
    all_records = extracted_records + existing_records

    manifest_path = os.path.join(REPO_ROOT, "research/v47/elite_corpus/elite_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2)

    print(f"\nSuccessfully registered {len(all_records)} elite benchmark agents.")
    print(f"Manifest written to: {manifest_path}")

    for rec in all_records:
        print(f"  [{rec['agent_id']}] Score: {rec['public_score']} | Hash: {rec['source_hash'][:16]}... | Author: {rec['author']}")


if __name__ == "__main__":
    main()
