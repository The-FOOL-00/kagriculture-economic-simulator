# SPDX-License-Identifier: MIT
# AEC Phase 004B: Resource Conversion Liquidity & Classification Remediation
## Technical Architecture & Remediation Specification

**Phase**: AEC Phase 004B  
**Mechanism Under Remediation**: `RESOURCE_CONVERSION`  
**Status**: Quarantined / Remediated / Offline Micro-Validated  
**Chassis**: Frozen V3 (`submission_Vj_kc_v3.tar.gz`) — SHA-256: `845e0d10981b11b06d272048ff5cee30d70a0403dd757651a556a78c8bf18943`  
**Target Population**: Offline Development Seeds `50000–50024`  
**Scientific Controls**: Zero prospective tournament runs (`340300–340349` untouched), zero holdout touches (`340050–340199` and `214200–214249` untouched), `EMERGENCY_FEED_PURCHASE` unedited and quarantined.

---

### 1. Executive Summary & Problem Formulation

In Phase 004 offline replay evaluation across 200 matches (seeds 50000–50024, 2 seats, 4 experimental arms), `RESOURCE_CONVERSION` exhibited severe structural and economic failure:
- **Mean Margin**: -$172.04
- **ITT Paired Mean Delta vs CONTROL**: -$258.96
- **Win / Loss / Tie Record**: 0 Wins, 50 Losses, 0 Ties
- **Total Commits**: 210 commits across 23 of 25 seeds

Forensic analysis of the 210 commits identified three fundamental architectural defects:
1. **Opportunity Family Misclassification (184 / 210 commits = 87.6%)**:
   The opportunity discovery pipeline classified ordinary market carrot seed purchases (`BUY_SEED CARROT 1`) as `RESOURCE_CONVERSION` (`PATCH_CONV_CONV_CHAIN_SEED_TO_CARROT`). These purchases had zero physical transformation, no immediate planting schedule, and no causal asset preservation, locking up working capital and depressing final liquidity.
2. **Missing Labor Preconditions & Silent Farmer Fallback (24 / 210 commits = 11.4%)**:
   On seeds where auxiliary hands were not present or unavailable (e.g. seeds 50019 and 50024), animal feeding operations (`PATCH_CONV_CONV_CHAIN_WHEAT_TO_EGG`) silently fell back to displacing the Farmer, abandoning high-value baseline harvests and creating catastrophic losses (-$3,367 on seed 50024).
3. **Absence of Working-Capital Liquidity Solvency Verification**:
   Candidates were evaluated solely on instantaneous static margin estimates ($R - C > 0$) rather than dynamic turn-by-turn cash solvency against downstream mandatory obligations (e.g. seed planting windows, wage commitments, tax deadlines).

Phase 004B resolves all three defects through principled, causal architectures without arbitrary dollar constants or heuristics.

---

### 2. Objective A: Working-Capital Liquidity & Causal Realizable Value

#### 2.1 Working-Capital Obligation Graph
Every conversion candidate defines an explicit spatio-temporal lifecycle:
$$\text{Input Acquisition} \longrightarrow \text{Resource Arrival} \longrightarrow \text{Resource Commitment} \longrightarrow \text{Processing / Feeding} \longrightarrow \text{Yield} \longrightarrow \text{Sale / Liquidation}$$

The working capital required by this lifecycle is analyzed via `ConversionLiquidityProfile` (`aec/resource/liquidity.py`):
```python
@dataclass
class ConversionLiquidityProfile:
    upfront_cash_required: float
    intermediate_cash_requirements: Dict[int, float]
    downstream_cash_release: float
    earliest_cash_recovery: int
    latest_cash_recovery: int
    mandatory_cash_obligations: Dict[int, float]
    working_capital_lockup: float
    terminal_cash_dependencies: List[str]
    is_solvent_trajectory: bool
    insolvency_turn: Optional[int] = None
    insolvency_reason: Optional[str] = None
    has_realizable_value_path: bool = True
    value_path_type: ConversionCausalPathType = ConversionCausalPathType.SALEABLE_OUTPUT
    value_path_description: str = ""
```

#### 2.2 Turn-by-Turn Dynamic Cash Solvency Simulation
Rather than applying arbitrary thresholds (`if cash < $500` or `if roi < 20%`), `ConversionLiquidityAnalyzer` runs a deterministic forward working-capital trajectory across the evaluation horizon:
1. Baseline obligations are extracted using `BaselineObligationExtractor`. Mandatory cash requirements are indexed by turn $t$: $M(t)$.
2. Initial cash is debited by the exact upfront cost: $C(t_0) = \text{cash}_0 - \text{upfront\_cost}$. If $C(t_0) < 0$, the candidate fails immediately with `Cash liquidity hole`.
3. For each step $\tau \in [t_0, t_0 + H]$:
   $$C(\tau) = C(\tau - 1) - \text{intermediate\_cost}(\tau) - M(\tau) + \text{revenue}(\tau)$$
4. **Hard Solvency Invariant**: If $C(\tau) < 0$ at any step $\tau$, the trajectory encounters a working-capital deadlock. The candidate fails closed and **ABSTAINS**.

#### 2.3 Strict Causal Realizable Value Requirement
A conversion candidate is permitted only if it connects to an authoritative causal value path (`ConversionCausalPathType`):
- **Path A (`REQUIRED_INPUT`)**: Conversion produces an input required by a verified downstream baseline obligation.
- **Path B (`PRODUCTION_UNLOCK`)**: Conversion unlocks subsequent production on farm tiles.
- **Path C (`SALEABLE_OUTPUT`)**: Conversion creates a finished commodity realizable at market before terminal horizon.
- **Path D (`MANDATORY_ASSET_PRESERVATION`)**: Conversion prevents livestock starvation or escape.
- **Path E (`RESOURCE_LOSS_PREVENTION`)**: Conversion prevents unavoidable spoilage or loss.
- **Path F (`EXACT_TERMINAL_VALUE`)**: Conversion produces terminal liquidation value at step 718.
- **Rejection (`NO_REALIZABLE_PURPOSE`)**: If the output commodity has no physical destination or cannot be liquidated before game completion, the candidate is classified as dead-end and **ABSTAINS**.

---

### 3. Objective B: Strict Auxiliary Worker Precondition & Farmer Fallback Guard

#### 3.1 Labor Requirement Classification
Conversions are formally partitioned into labor requirement classes (`ConversionLaborClass` in `aec/resource/labor.py`):
1. `NO_WORKER_REQUIRED`: Pure market transactions requiring zero unit movement.
2. `PRIMARY_WORKER_REQUIRED`: Specialized operations strictly reserved for the Farmer.
3. `AUXILIARY_WORKER_PREFERRED`: Operations executable by any worker, prioritizing auxiliary hands.
4. `AUXILIARY_WORKER_REQUIRED`: Labor-intensive physical tasks (e.g. livestock feeding, shed transit) that must NOT divert the Farmer from the agricultural backbone.

#### 3.2 Auxiliary Worker Scheduling & Expiry Protection
For candidates with `AUXILIARY_WORKER_REQUIRED`:
- The scheduling engine searches exclusively across active auxiliary hands (units $1..N-1$).
- **Day-Boundary Expiry Guard**: Hired hands expire at the daily boundary (`step % 24 == 23`). If a multi-step task cannot complete before worker contract expiry, the task is rejected.
- If no auxiliary worker can execute the task without violating physical or temporal constraints, the mechanism **ABSTAINS**.

#### 3.3 The 7-Condition Farmer Fallback Rule
Farmer assignment is permitted if and only if all 7 formal conditions pass:
1. **Legal Capability**: Farmer exists and possesses the requisite physical capability.
2. **Zero Mandatory Obligation Breach**: Farmer displacement does not delay or cancel any mandatory baseline task.
3. **Zero High-Value Harvest Cannibalization**: Farmer displacement does not displace any scheduled `HIGH_VALUE_HARVEST` or `LIVESTOCK_SECURITY` tasks.
4. **Auxiliary Saturation Proof**: Formal proof that no available auxiliary hand can absorb the conversion.
5. **Reassignment Feasibility**: Any displaced non-mandatory task can be safely absorbed or delayed without deadlock.
6. **Schedule Coexistence**: Spatio-temporal route continuity and collision safety are guaranteed.
7. **Exact Counterfactual Safety**: Simulation confirms positive or neutral margin delta with zero invariant violations.

If any condition fails, Farmer fallback is strictly prohibited.

---

### 4. Objective C: Opportunity Family Audit & Classification Isolation

#### 4.1 Forensic Root-Cause Analysis of Phase 004 Attribution
In Phase 004, `discover_conversion_paths` generated a synthetic chain:
$$\text{BUY\_CARROT\_SEED} \longrightarrow \text{GROW\_CARROT\_CROP} \longrightarrow \text{HARVEST\_CARROT}$$
Because this chain was labeled `RESOURCE_CONVERSION`, ordinary seed purchases were emitted as `PATCH_CONV_CONV_CHAIN_SEED_TO_CARROT`. This was a semantic category error: purchasing seeds for general planting is `RESOURCE_ACQUISITION`, which belongs to production planning or market timing, NOT `RESOURCE_CONVERSION`.

#### 4.2 Semantic Separation & Family Routing
In Phase 004B:
- `CONV_CHAIN_SEED_TO_CARROT` is explicitly typed as `opportunity_family = "RESOURCE_ACQUISITION"` with `labor_class = NO_WORKER_REQUIRED`.
- `PatchGenerator` rejects all `RESOURCE_ACQUISITION` opportunities from the `RESOURCE_CONVERSION` compiler.
- `RESOURCE_CONVERSION` is strictly restricted to physical transformations:
  * `CONV_CHAIN_WHEAT_TO_MILK` (Wheat Feed $\to$ Cow $\to$ Milk)
  * `CONV_CHAIN_WHEAT_TO_EGG` (Wheat Feed $\to$ Goose $\to$ Egg)
  * `CONV_CHAIN_WHEAT_TO_WOOL` (Wheat Feed $\to$ Sheep $\to$ Wool)
- Every emitted conversion patch records complete machine-readable provenance in `attribution_info`:
  ```python
  attribution = {
      "opportunity_family": "RESOURCE_CONVERSION",
      "resource_graph_path": "WHEAT -> FEED -> MILK",
      "physical_conversion": True,
      "market_actions": market_actions,
      "worker_actions": worker_actions,
      "labor_class": "AUXILIARY_WORKER_REQUIRED",
      "input": "WHEAT",
      "output": "MILK",
      "cash_effect": net_val,
      "capacity_effect": 0,
      "downstream_purpose": "SALEABLE_OUTPUT",
      "terminal_relevance": True
  }
  ```

---

### 5. Multi-Worker Dominance Extensions

`MultiWorkerDominancePruner` (`aec/coordination/dominance.py`) was extended with two formal dominance relations:
1. **Auxiliary Worker Preference Dominance**:
   $$\text{Plan } A \succ \text{Plan } B \quad \text{if } (\text{FarmerDiverted}(A) = \text{False}) \land (\text{FarmerDiverted}(B) = \text{True})$$
   Any plan utilizing an auxiliary worker strictly dominates a plan that diverts the Farmer, all other obligation and transit metrics being equal.
2. **Completion Timing Dominance**:
   $$\text{Plan } A \succ \text{Plan } B \quad \text{if } \max_{a \in A} \text{step}_{\text{comp}}(a) < \max_{b \in B} \text{step}_{\text{comp}}(b)$$
   A plan releasing resources or workers earlier strictly dominates a later plan.

---

### 6. Verification Architecture: Micro-Validation Battery (RC-R1..20)

Twenty adversarial unit fixtures were implemented in `tests/aec/test_resource_remediation_fixtures.py`:
- **RC-R1**: Conversion requires cash, but exact baseline obligations cannot remain funded $\to$ **ABSTAIN**.
- **RC-R2**: Conversion temporarily reduces cash but exact future revenue restores solvency $\to$ **FEASIBLE**.
- **RC-R3**: Conversion input purchase has no realizable downstream use $\to$ **ABSTAIN**.
- **RC-R4**: Immediate positive symbolic value but causes future cash deadlock $\to$ **ABSTAIN**.
- **RC-R5**: Auxiliary worker available $\to$ **Assign Auxiliary Hand**.
- **RC-R6**: Auxiliary worker unavailable $\to$ **ABSTAIN** (no Farmer fallback).
- **RC-R7**: Farmer is sole worker, baseline has zero obligations $\to$ **Permitted by exact semantics**.
- **RC-R8**: Farmer diversion destroys mandatory harvest obligation $\to$ **ABSTAIN**.
- **RC-R9**: Farmer diversion destroys optional move only $\to$ **FEASIBLE**.
- **RC-R10**: Two workers available; one preserves baseline better $\to$ **Dominance selects optimal worker**.
- **RC-R11**: Market seed purchase classified as `RESOURCE_ACQUISITION` $\to$ **Rerouted / Excluded from conversion**.
- **RC-R12**: True physical conversion classified as `RESOURCE_CONVERSION` $\to$ **Conversion family retained**.
- **RC-R13**: Multi-stage conversion trajectory $\to$ **Complete DAG verified**.
- **RC-R14**: Conversion output arrives too late for terminal horizon $\to$ **ABSTAIN**.
- **RC-R15**: Conversion requires terminal liquidation $\to$ **Exact terminal purpose verified**.
- **RC-R16**: Repeated identical state $\to$ **Bit-exact determinism verified**.
- **RC-R17**: Infeasible physical candidate $\to$ **Exact simulator / safety certifier rejects**.
- **RC-R18**: Valid worker schedule but zero cash liquidity $\to$ **ABSTAIN**.
- **RC-R19**: Auxiliary worker expires at day boundary ($\text{step } 23$) $\to$ **ABSTAIN**.
- **RC-R20**: Auxiliary hand feeds livestock while Farmer harvests $\to$ **Counterfactual verifies coordinated plan**.

**Result**: 20 / 20 passed in 0.14s. Full regression suite: 354 / 354 passed.
