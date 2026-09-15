import hashlib
import json

def audit12():
    canonical_hashes = {
        "M1 Baseline (candidates/candidate_cl_fert_gated.py)": (
            "candidates/candidate_cl_fert_gated.py",
            "4ab127dafb02cf495b14a71be09ba231f5c04496095136babaf2ae592e4e595c"
        ),
        "Slot 1 (agents/candidate_a_aethel_v1.py)": (
            "agents/candidate_a_aethel_v1.py",
            "c1945f24f34ca9d5124e8200df14af019f6cb4cdec3ca402d9a3a88f6b04e36f"
        ),
        "Slot 2 (candidates/slot2_aethel_refined_v2.py)": (
            "candidates/slot2_aethel_refined_v2.py",
            "79efb19a9b9d8146d53a7531d1f1962d5d963b8ea2b5b509e12ad526559de93d"
        ),
        "Frozen Candidate (candidates/candidate_cl_labor_minimal_v1.py)": (
            "candidates/candidate_cl_labor_minimal_v1.py",
            "6708397769d64de5935623c8bf6df7076ce0b1afff236555128757fb577a6759"
        )
    }

    print("=" * 100)
    print("AUDIT 12: COMPETITION ARTIFACT IMMUTABILITY AUDIT")
    print("=" * 100)

    results = {}
    all_matched = True
    for label, (path, expected_sha) in canonical_hashes.items():
        with open(path, "rb") as f:
            measured_sha = hashlib.sha256(f.read()).hexdigest()
        matched = (measured_sha == expected_sha)
        if not matched:
            all_matched = False
        status = "MATCH (UNTOUCHED)" if matched else "FAILED / CORRUPTED"
        print(f"\n{label}:")
        print(f"  Path:         {path}")
        print(f"  Expected:     {expected_sha}")
        print(f"  Measured:     {measured_sha}")
        print(f"  Status:       {status}")
        results[label] = {
            "path": path,
            "expected": expected_sha,
            "measured": measured_sha,
            "matched": matched
        }

    print("\n" + "-" * 100)
    print(f"Overall Immutability Status: {'ALL MATCHED - ZERO MODIFICATIONS' if all_matched else 'FAILED - MODIFICATION DETECTED'}")

    with open("scratch/audit12_results.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    audit12()
