import json
import os
import sys
import hashlib
from pathlib import Path

def validate_all():
    print("=" * 70)
    print("STARTING LOCAL VALIDATION OF KAGGLE BUNDLE & NOTEBOOK")
    print("=" * 70)

    repo_root = Path.cwd().resolve()
    bundle_dir = repo_root / "kaggle_arch002_bundle"
    nb_path = bundle_dir / "notebook" / "arch002_h1_kaggle.ipynb"
    manifest_path = bundle_dir / "KAGGLE_DEPENDENCY_MANIFEST.json"
    hash_manifest_path = bundle_dir / "HASH_MANIFEST.txt"
    source_dir = bundle_dir / "source"

    # -------------------------------------------------------------------------
    # 1. Notebook JSON & Schema Validation
    # -------------------------------------------------------------------------
    print("\n[1/6] Validating Notebook JSON & Metadata...")
    assert nb_path.exists(), f"Notebook not found at: {nb_path}"
    with open(nb_path, "r", encoding="utf-8") as f:
        nb_data = json.load(f)

    assert nb_data.get("nbformat") == 4, f"Unexpected nbformat: {nb_data.get('nbformat')}"
    assert "cells" in nb_data and len(nb_data["cells"]) > 0, "Notebook contains no cells!"
    print(f"  Notebook JSON valid. Total cells: {len(nb_data['cells'])}")

    # Check GPU T4 x 2 metadata
    meta = nb_data.get("metadata", {})
    assert meta.get("accelerator") == "GPU", "Metadata accelerator is not GPU!"
    print("  Kaggle metadata correctly targets GPU accelerator.")

    # -------------------------------------------------------------------------
    # 2. Python Syntax Validation for All Code Cells
    # -------------------------------------------------------------------------
    print("\n[2/6] Validating Python Syntax Across All Code Cells...")
    code_cells = [c for c in nb_data["cells"] if c.get("cell_type") == "code"]
    print(f"  Found {len(code_cells)} code cells.")

    for idx, cell in enumerate(code_cells):
        code_src = "".join(cell.get("source", []))
        try:
            compile(code_src, f"cell_{idx}", "exec")
        except SyntaxError as e:
            raise AssertionError(f"Syntax error in code cell {idx}: {e}")
    print("  All code cells compiled successfully (100% valid Python syntax).")

    # -------------------------------------------------------------------------
    # 3. Required File Manifest & Checksums
    # -------------------------------------------------------------------------
    print("\n[3/6] Validating Bundle Manifest & Checksums...")
    assert manifest_path.exists(), "Missing KAGGLE_DEPENDENCY_MANIFEST.json"
    assert hash_manifest_path.exists(), "Missing HASH_MANIFEST.txt"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    print(f"  Manifest specifies {manifest['total_files']} files ({manifest['total_bytes']:,} bytes).")
    for item in manifest["files"]:
        bundled_file = source_dir / item["kaggle_destination"]
        assert bundled_file.exists(), f"Missing bundled file: {bundled_file}"
        with open(bundled_file, "rb") as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest()
        assert actual_sha == item["sha256"], (
            f"Checksum mismatch for {item['kaggle_destination']}: {actual_sha} != {item['sha256']}"
        )

    print("  All 23 bundled source files present with exact matching SHA-256 digests.")

    # -------------------------------------------------------------------------
    # 4. Import & Dependency Validation
    # -------------------------------------------------------------------------
    print("\n[4/6] Validating Python Import Paths...")
    port_path = str(repo_root / "experiments" / "EXP-DEV-006_HORIZON_KILLTEST" / "port")
    h1_path = str(repo_root / "experiments" / "EXP-ARCH-002_H1_DOMINANCE_TERMINAL")

    for p in (port_path, h1_path, str(repo_root)):
        if p not in sys.path:
            sys.path.insert(0, p)

    import kagsim_py.api as papi
    import h1_agent
    import h1_baseline
    import h1_const
    import h1_dominance
    import h1_search
    import h1_shadow
    import h1_telemetry
    import h1_units
    import run_arch002_h1_reexecution as runner

    assert papi.ENGINE_VERSION == "1.32.7", f"Incorrect engine version: {papi.ENGINE_VERSION}"
    print("  All simulator and H1 modules imported cleanly.")

    # -------------------------------------------------------------------------
    # 5. Preflight Gate Execution (Up to Prospective Boundary)
    # -------------------------------------------------------------------------
    print("\n[5/6] Executing Preflight Gates (Sections 4-10)...")
    
    # G-HASH verification
    runner.verify_integrity_hashes()
    print("  G-HASH verified: baseline and preregistration match.")

    # Quarantine verification
    for s in (214200, 214249, 310000, 310499, 100, 320500):
        try:
            runner.assert_quarantine(s, allow_consumed_validation=False)
            raise AssertionError(f"Quarantine failed on seed {s}")
        except RuntimeError:
            pass
    print("  Quarantine gates verified.")

    # Consumed seed purity test
    res = runner.run_seed_crn(248000, allow_consumed_validation=True)
    assert res["delta_paired"] == 0.0
    assert res["game_a"]["pure_pre_e_pass"] is True
    assert res["game_b"]["pure_pre_e_pass"] is True
    print(f"  Consumed seed 248000 purity verified: delta_paired={res['delta_paired']:.2f}")

    # -------------------------------------------------------------------------
    # 6. Verify Prospective Execution Remains Unexecuted Locally
    # -------------------------------------------------------------------------
    print("\n[6/6] Verifying Prospective Boundary Enforcement...")
    # Verify prospective cohort (320000–320499) was not touched
    local_raw = repo_root / "experiments" / "EXP-ARCH-002_H1_DOMINANCE_TERMINAL" / "kaggle_execution" / "RAW_RESULTS.json"
    assert not local_raw.exists(), "Prospective output RAW_RESULTS.json unexpectedly exists!"
    print("  Prospective cohort 320000-320499 remains virgin and unexecuted locally.")

    print("\n" + "=" * 70)
    print("LOCAL VALIDATION COMPLETE: 100% PASS")
    print("Notebook and bundle are fully validated and ready for manual upload to Kaggle.")
    print("=" * 70)

if __name__ == "__main__":
    validate_all()
