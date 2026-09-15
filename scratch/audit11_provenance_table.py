import json

def generate_provenance():
    experiments = [
        {
            "Experiment": "Early Watering & Gating Discovery",
            "Purpose": "Explore strawberry selective irrigation and initial fertilizer gating",
            "Seed_Range": "1000-1049",
            "N": 50,
            "Policy_Set": "M0 Baseline, Fertilizer Gating, Selective Watering",
            "Cohort_Type": "Discovery",
            "Previously_Inspected": "Yes (Extensively)",
            "Used_For_Code_Decisions": "Yes (Designed M1 fertilizer gate)",
            "Used_For_Final_Confirmation": "No (Exploratory only)"
        },
        {
            "Experiment": "Wheat Quota & Pasture Collision",
            "Purpose": "Identify wheat overplanting bottleneck and pasture slot placement",
            "Seed_Range": "1050-1149",
            "N": 100,
            "Policy_Set": "M1 Baseline, Quota Sweeps (30, 50, 70, 90)",
            "Cohort_Type": "Discovery",
            "Previously_Inspected": "Yes (Extensively)",
            "Used_For_Code_Decisions": "Yes (Selected Q50 wheat quota)",
            "Used_For_Final_Confirmation": "No (Exploratory only)"
        },
        {
            "Experiment": "M1 Baseline Holdout Validation",
            "Purpose": "Certify M1 baseline performance out-of-sample",
            "Seed_Range": "1200-1249",
            "N": 50,
            "Policy_Set": "M0 Baseline, Certified M1 Baseline",
            "Cohort_Type": "Holdout",
            "Previously_Inspected": "Yes",
            "Used_For_Code_Decisions": "No (Read-only validation)",
            "Used_For_Final_Confirmation": "No (Baseline only)"
        },
        {
            "Experiment": "Labor Bandwidth Discovery",
            "Purpose": "Identify strawberry harvest delays and peripheral weed transit costs",
            "Seed_Range": "1250-1349",
            "N": 100,
            "Policy_Set": "Raw Q50, Urgency Variants, Task Gating Variants",
            "Cohort_Type": "Discovery",
            "Previously_Inspected": "Yes (Extensively)",
            "Used_For_Code_Decisions": "Yes (Designed L_Minimal components A and B)",
            "Used_For_Final_Confirmation": "No (Exploratory only)"
        },
        {
            "Experiment": "Factorial Component Attribution",
            "Purpose": "Measure individual and joint effects of Urgency (A) and Weed Gating (B)",
            "Seed_Range": "1300-1399",
            "N": 100,
            "Policy_Set": "Raw Q50, A_only, B_only, A+B (L_Minimal)",
            "Cohort_Type": "Discovery / Ablation",
            "Previously_Inspected": "Yes",
            "Used_For_Code_Decisions": "Yes (Verified both arms had positive mean)",
            "Used_For_Final_Confirmation": "No (Discovery cohort)"
        },
        {
            "Experiment": "Livestock Controller Holdout",
            "Purpose": "Validate conditional livestock feeding rules",
            "Seed_Range": "1450-1649",
            "N": 200,
            "Policy_Set": "M1, Livestock Dynamic Controller",
            "Cohort_Type": "Holdout",
            "Previously_Inspected": "Yes",
            "Used_For_Code_Decisions": "No (Rejected complex controller)",
            "Used_For_Final_Confirmation": "No"
        },
        {
            "Experiment": "Worker Labor Bandwidth Holdout",
            "Purpose": "Evaluate harvest reservation and zoning in unseen seeds",
            "Seed_Range": "35000-35199",
            "N": 200,
            "Policy_Set": "Raw Q50, Zoned Dispatch, L_Minimal Prototype",
            "Cohort_Type": "Holdout",
            "Previously_Inspected": "Yes",
            "Used_For_Code_Decisions": "No (Evaluated generalization)",
            "Used_For_Final_Confirmation": "No"
        },
        {
            "Experiment": "Pristine Qualification Block",
            "Purpose": "Blind, untainted statistical certification of frozen candidate",
            "Seed_Range": "941000-941499",
            "N": 500,
            "Policy_Set": "M1 Baseline, Raw Q50, Frozen Candidate (L_Minimal)",
            "Cohort_Type": "Qualification",
            "Previously_Inspected": "No (Zero prior matches repository-wide)",
            "Used_For_Code_Decisions": "No (Strictly read-only evaluation)",
            "Used_For_Final_Confirmation": "Yes (Primary certification evidence)"
        }
    ]

    print("=" * 120)
    print("AUDIT 11: COMPLETE EXPERIMENTAL PROVENANCE TABLE")
    print("=" * 120)
    fmt = "{:<32s} | {:<42s} | {:<12s} | {:<4s} | {:<15s} | {:<12s} | {:<12s} | {:<12s}"
    print(fmt.format("Experiment", "Purpose", "Seed Range", "N", "Cohort Type", "Inspected?", "Code Decisions?", "Final Confirm?"))
    print("-" * 155)
    for e in experiments:
        print(fmt.format(
            e["Experiment"][:32],
            e["Purpose"][:42],
            e["Seed_Range"],
            str(e["N"]),
            e["Cohort_Type"],
            e["Previously_Inspected"][:12],
            e["Used_For_Code_Decisions"][:12],
            e["Used_For_Final_Confirmation"][:12]
        ))

    with open("scratch/audit11_provenance.json", "w") as f:
        json.dump(experiments, f, indent=2)

if __name__ == "__main__":
    generate_provenance()
