# AEC-RESOURCE: Scientific Readiness Audit & Quarantine Matrix
## Architectural Development Phase 002

### Scientific Governance Certification

- **Task Category**: ARCHITECTURAL DEVELOPMENT (Phase 002).
- **Prospective Competition Trials**: **ZERO**. No prospective competition cohorts or live Kaggle runs were launched.
- **Holdout Verification**: Protected holdout seeds (`340050–340199`) remain 100% untouched.
- **Historical Experiment Cohorts**: EXP-AEC-003 seeds (`340250–340299`) remain 100% untouched.
- **Frozen Control Backbone**: `submission_Vj_kc_v3.tar.gz` verified byte-identical (SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`).

---

### 1. Capability Readiness Classification Matrix

Each capability within the AEC compiler stack is classified strictly under one of four states:
- **VALIDATED**: Architecturally implemented, micro-validated across adversarial suites, and prospectively validated in preregistered competition trials.
- **PARTIALLY VALIDATED**: Architecturally implemented and micro-validated across synthetic/adversarial fixtures, but **NOT** yet prospectively validated in live competition trials.
- **DEVELOPMENT ONLY**: In progress; partial unit tests; not ready for full compiler integration.
- **UNIMPLEMENTED**: Identified in architectural gap analysis but no operational code exists.

| Compiler Subsystem / Capability | Architectural Status | Micro-Validation Status | Prospective Validation | Overall Classification | Governance Directive |
|:---|:---:|:---:|:---:|:---:|:---|
| **AEC-001 Foundation** | Implemented | 100% Pass | Validated | **VALIDATED** | Core compiler infrastructure |
| **AEC-003 Market Timing Compiler** | Implemented | 100% Pass | Validated (EXP-AEC-003) | **VALIDATED** | Production compiler pass |
| **AEC-RECONNECT Trajectory Splicing**| Implemented | 100% Pass | Pending Trial | **PARTIALLY VALIDATED** | Unblocked; pending preregistered trial |
| **AEC-RESOURCE Temporal DAG** | Implemented | 100% Pass (8 tests) | Not Initiated | **PARTIALLY VALIDATED** | Compiler pass unblocked |
| **AEC-RESOURCE Feed Security Engine**| Implemented | 100% Pass (5 tests) | Not Initiated | **PARTIALLY VALIDATED** | Subsystem unblocked |
| **AEC-RESOURCE Conversion Engine** | Implemented | 100% Pass (5 tests) | Not Initiated | **PARTIALLY VALIDATED** | Subsystem unblocked |
| **AEC-RESOURCE Adversarial Parity** | Implemented | 100% Pass (20 tests)| Not Initiated | **PARTIALLY VALIDATED** | Cases A–T verified |
| **Dynamic Labor Shadow Pricing** | Interface Only | Mocked | None | **DEVELOPMENT ONLY** | Quarantined; separate gap |
| **Multi-Agent Opponent Game Forecast**| None | None | None | **UNIMPLEMENTED** | Out of scope; relies on regime signals |

> [!IMPORTANT]
> **AEC-RESOURCE is NOT prospectively validated.** 
> While its architectural correctness, temporal DAG conservation, and feed security accounting have been micro-validated with 100% test pass rates across synthetic fixtures and adversarial suites, no prospective competition trial has been executed. It must be treated as **PARTIALLY VALIDATED / ARCHITECTURALLY COMPLETE**.

---

### 2. Mechanism Quarantine Ledger & Structural Status

Under scientific governance rule 1.D, **STRUCTURAL CAPABILITY $\ne$ EMPIRICAL VALIDATION**.
The implementation of AEC-RESOURCE structurally unblocks several mechanisms that were previously impossible to reason about without dynamic inventory and feed security modeling. However, **all such mechanisms remain strictly QUARANTINED in `aec/config.py`**.

| Mechanism Name | Category | Structural Status | Quarantine Status in `config.py` | Scientific Rationale |
|:---|:---|:---:|:---:|:---|
| `OPPORTUNITY_DETECTOR` | CORE | Unblocked | **ACTIVE** | Core detection pipeline |
| `MARKET_TIMING_DISCOVERY`| MARKET | Unblocked | **ACTIVE** | Validated in EXP-AEC-003 |
| `TIMING_EXPANSION` | TIMING | Unblocked | **ACTIVE** | Validated in EXP-AEC-003 |
| `DYNAMIC_ROUTE_RECONNECT`| ROUTING | Unblocked | **QUARANTINED** | Micro-validated in AEC-RECONNECT; pending prospective trial |
| `RESOURCE_CONVERSION` | RESOURCE | **STRUCTURALLY UNBLOCKED** | **QUARANTINED** | Newly unblocked by AEC-RESOURCE; requires dedicated preregistered micro-validation before activation |
| `EMERGENCY_FEED_PURCHASE`| RESOURCE | **STRUCTURALLY UNBLOCKED** | **QUARANTINED** | Newly unblocked by Feed Security Engine; requires dedicated preregistered micro-validation before activation |
| `CARGO_FERRY_PRIORITY` | LOGISTICS | Blocked | **QUARANTINED** | Awaits multi-worker logistics coordination |
| `OPPONENT_PREEMPT_SELL` | MARKET | Blocked | **QUARANTINED** | Awaits opponent inventory estimation |
| `TERMINAL_HARVEST_SWEEP`| TERMINAL | Blocked | **QUARANTINED** | Awaits terminal liquidation pass |
| `TOWN_CYCLE` | LOGISTICS | Blocked | **QUARANTINED** | Awaits town cycle timing optimizer |

---

### 3. Readiness Gates for Future Prospective Activation

Before `RESOURCE_CONVERSION` or `EMERGENCY_FEED_PURCHASE` can be considered for live competition deployment, the research program requires the following sequence:

1. **Protocol Preregistration**: Formal preregistration document specifying seed cohorts (outside the protected 340050–340199 holdout), primary metric ($\Delta \text{Gold}$ relative to V3 backbone), and strict statistical rejection thresholds.
2. **Offline Replay Validation**: Running candidate patches on deterministic historical replays to ensure zero degradation of baseline backbone score under benign market conditions.
3. **Controlled Cohort Trial**: Paired trial execution under the registered protocol.
4. **Forensic Audit & Sign-off**: Independent verification that zero safety invariants were breached, zero unexpected rollouts occurred, and observed gains exceed preregistered effect sizes.

Until all four gates are completed, both mechanisms remain **strictly quarantined**.
