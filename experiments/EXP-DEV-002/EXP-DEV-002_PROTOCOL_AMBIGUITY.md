# EXP-DEV-002 PROTOCOL AMBIGUITY & GOVERNANCE STOP REPORT

**Document Identifier**: `EXP-DEV-002-AMBIGUITY-V1.0`  
**Governing Standard**: Section 1 & Section 10 of User Directives; Section 5 of `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`  
**Cryptographic Protocol Hash**: `671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3`  
**Git Commit**: `a1ba5acb0d04689874ce1333892825f014eea924`  
**Date**: 2026-09-11  
**Status**: **FORMAL PREFLIGHT HALT — AWAITING USER PROTOCOL DETERMINATION**  

---

## 1. Executive Summary & Mandatory Stop Injunction

Under **Directive 1** of the user instructions:
> *"Determine the registered definition of EXP-DEV-002. If the exact treatment is already specified, execute that treatment exactly. Do NOT invent a new treatment under the name EXP-DEV-002. If the frozen protocol does NOT contain enough specification for the intended hedged adaptation experiment, STOP and report: `EXP-DEV-002_PROTOCOL_AMBIGUITY.md`. Do not silently redefine the experiment."*

And under **Directive 10 (Protocol Fallback D)**:
> *"STOP if ambiguity remains. Do not choose the interpretation that maximizes the chance of Top-10 performance."*

An exhaustive audit of [`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/audits/DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md) and [`DEVELOPMENT_EXPERIMENT_REGISTRY.md`](file:///c:/Users/Sundareswaran/Kagriculture/research/audits/DEVELOPMENT_EXPERIMENT_REGISTRY.md) revealed a **fundamental, irreconcilable discrepancy** between the user's intended research mission and the prospective pre-registration frozen on disk.

In strict compliance with the anti-silent-redefinition covenant, **zero simulation runs have been launched**, and execution is formally **HALTED**.

---

## 2. Forensic Analysis of the Protocol Discrepancy

### 2.1 Side-by-Side Specification Comparison

| Dimension | User Prompt Directive (Intended Mission) | Frozen Pre-Registration (`DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md:93-107`) | Conflict Status |
| :--- | :--- | :--- | :---: |
| **Title / Scope** | `EXP-DEV-002 — HEDGED ADAPTIVE PORTFOLIO RESEARCH` | `EXP-DEV-002 (RQ2: Rebuilt Shop Information Value Quantification)` | **DIRECT CONFLICT** |
| **Research Question** | *"Can adaptive portfolio behavior capture useful information from revealed shops while explicitly limiting irreversible downside exposure?"* | *"What is the exact empirical Value of Information (VoI) of each successive town shop unlock across the 8 unlock steps (Days 3..24) when measured under authoritative C++ simulator definitions?"* | **DIRECT CONFLICT** |
| **Candidate Treatment** | Constrained / hedged adaptive portfolio policy (e.g. limited substitution, strawberry floor, delayed commitment) | `dev_002_shop_voi_evaluator` (policy conditioned on realized shop unlocks at step $t$) | **TREATMENT MISMATCH** |
| **Baseline Control** | **Control A**: `ClosedLoopAgentV2`<br>**Control B**: Static 19S/0T baseline<br>**Reference**: `Dmitrii-LB2800` | Open-loop expected value policy assuming unconditional base uniform shop draw probabilities | **CONTROL MISMATCH** |
| **Primary Metric** | Paired margin vs V2 with lower-tail risk metrics ($p_{01}$, $p_{05}$, worst single-seed loss) | Empirical Expected Value of Information: $\text{VoI}(t) = \mathbb{E}_{\text{Shops}}[V(\pi^*(\text{Shop}_{1..t}))] - \mathbb{E}[V(\pi_0)]$ | **METRIC MISMATCH** |
| **Sample Size** | Discovery (50 seeds), advancing if non-inferior tail risk | 100 Seeds (Discovery 50000–50049 + Qualification 50050–50099) | **STRUCTURAL DIFFERENCE** |
| **Stop Rule** | Worst loss ceiling (e.g. $< -\$800.00$), negative mean | Total VoI across all regimes $< \$50.00$ | **CRITERION MISMATCH** |

---

## 3. Codebase and Treatment Integrity Audit

1. **Absence of `dev_002_shop_voi_evaluator` on Disk**:
   - A global regex search across `c:\Users\Sundareswaran\Kagriculture\` confirms that `dev_002_shop_voi_evaluator` appears **strictly as text** in markdown registry files.
   - Zero Python files, modules, or classes implementing `dev_002_shop_voi_evaluator` exist in `candidates/`, `scratch/`, or anywhere in the repository.
   - The frozen protocol does not specify the decision mapping $\pi^*(\text{Shop}_{1..t})$ or the baseline open-loop policy $\pi_0$.

2. **Absence of Preregistered Hedged Adaptation Candidates**:
   - Prompt Section 3 lists potential hedging concepts:
     - *limited substitution*
     - *staggered substitution*
     - *reserve capacity*
     - *partial hedge*
     - *delayed commitment*
     - *minimum Strawberry floor*
     - *reversible inventory exposure*
   - Section 3 explicitly instructs: *"Potential concepts are only examples unless already preregistered... Do NOT introduce these merely because they sound good. Only use a registered treatment."*
   - None of these candidate concepts were pre-registered in `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1.md` under `EXP-DEV-002`.

3. **Danger of Silent Redefinition**:
   - If an agent were to arbitrarily code a "hedged tomato substitution" agent, assign it the name `dev_002`, and execute seeds 50000–50049, it would violate:
     - **Section 1**: *"Do NOT invent a new treatment under the name EXP-DEV-002."*
     - **Section 2.4 of Protocol V1**: Anti-p-hacking and prospective pre-registration rules.
     - **Audit 2.2 Core Mandate**: Prohibition against post-hoc hypothesis adjustments.

---

## 4. Preflight Audit Results

Prior to halting, all objective environmental and governance invariants were verified:

| Audit Item | Result | Evidence / Detail |
| :--- | :---: | :--- |
| **Protocol Hash** | **VERIFIED** | SHA-256 `671e915eadd72adb710421b45e6a33ad533abd9d68ff67770b8dd412ff7381b3` matches freeze bit-for-bit. |
| **Git Commit** | **VERIFIED** | Commit `a1ba5acb0d04689874ce1333892825f014eea924` clean; zero uncommitted diffs on protocol. |
| **14-Vector Leakage Suite** | **100% PASS** | 14 of 14 adversarial vectors intercepted and blocked by `ActiveContainmentSandbox`. |
| **Production Agent Parity** | **100% PASS** | `ClosedLoopAgentV2`, Sub 56146947, Sub 56146971 execute with bit-exact parity under sandbox. |
| **Holdout Quarantine** | **100% PASS** | Seeds `214200–214249` strictly excluded and programmatic assertion active. |
| **Treatment Definition** | **FAILED** | **Treatment is undefined on disk and in conflict with frozen protocol.** |

---

## 5. Formal Remediation Pathways for User Determination

To proceed without compromising scientific validity, the user must select one of the following formal resolution pathways:

### Pathway 1: Protocol Amendment V1.1 — Formally Register Hedged Adaptive Portfolio
If the intended goal is indeed **Hedged Adaptive Portfolio Research** responding to EXP-DEV-001's tail collapse:
1. Formally author and commit `DEVELOPMENT_EXPERIMENT_PROTOCOL_V1_1.md` (or formal amendment annex).
2. Explicitly pre-register:
   - **Candidate Treatment**: e.g., `dev_002_hedged_portfolio` (specifying exact parameters: e.g. minimum 13 Strawberry floor, maximum 6 Tomato substitution, Step 144 commitment cutoff, and $500 liquidity hedge).
   - **Hypothesis**: Formal $H_1$ and $H_0$ with margin and tail-loss thresholds ($p_{05} \ge -\$200.00$, worst loss $\ge -\$800.00$).
   - **Baselines**: `ClosedLoopAgentV2`, Static 19S/0T, `Dmitrii-LB2800`.
   - **Partitions**: Discovery (Seeds 50000–50049, $N=50$), Qualification (Seeds 50050–50099, $N=50$).
3. Implement candidate code in `candidates/closed_loop_architecture/dev_002_hedged_portfolio.py`.
4. Cryptographically freeze and commit before executing any simulation.

### Pathway 2: Execute Original Registered RQ2 (Value of Information Quantification)
If the goal is to execute the experiment **already frozen** under `EXP-DEV-002` in Protocol V1:
1. Fully specify and implement the mathematical open-loop baseline $\pi_0$ and information-conditioned policy $\pi^*$ in `candidates/closed_loop_architecture/dev_002_shop_voi_evaluator.py`.
2. Evaluate empirical $\text{VoI}(t)$ across the 8 shop unlock steps (Steps 72 to 576) over the pre-registered 100 seeds (Discovery + Qualification).
3. Determine whether early shop information meets the $\text{VoI} \ge \$100.00$ threshold or triggers the $<\$50.00$ stop condition.

### Pathway 3: Preserve EXP-DEV-002 as VoI and Channel Hedging to EXP-DEV-004
If the user wishes to maintain strict sequence without protocol amendments:
- `EXP-DEV-004` is already pre-registered in Protocol V1 as:
  > *"RQ4: World Regime Downside Resilience and Cash Buffer: Maintaining dynamic cash reserves and targeted hedging eliminates catastrophic tail losses on adverse shop worlds... Candidate: `dev_004_robust_hedging`."*
- Crop hedging and liquidity hedging can be unified under `EXP-DEV-004` when reached in natural sequence.

---

## 6. Current State & Action Taken

- **Execution**: **HALTED (0 seeds simulated)**.
- **Holdout Status**: **UNTOUCHED (Seeds 214200–214249 strictly quarantined)**.
- **EXP-DEV-001 Verdict**: **PRESERVED AS FAILED (unchanged)**.
- **Evidence Ledger**: **NO UNVERIFIED CLAIMS RECORDED**.
- **Next Step**: Awaiting user instruction on which pathway (Pathway 1, 2, or 3) to execute.
