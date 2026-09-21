# V26 — BACKBONE INTERFACE SPECIFICATION

## 1. Scope & Objective
This specification formalizes the **Backbone Contract** for the Adaptive Economic Compiler (AEC). In V22R1, the AEC was inextricably coupled to V3's internal implementation: its counterfactual simulator and state snapshotting inspected V3's private global variables (`_PARENT_NS`, `chassis`) and assumed V3's opening dynamics.

V26 decouples the AEC into an active-backbone-aware architecture:
- The **Backbone Policy** manages policy execution, internal state snapshotting, deterministic route lookahead, and cloned-state continuation.
- The **Economic Supervisor** reasons about market and production opportunities, counterfactual deltas, and macro safety without querying or assuming a specific backbone's internal variables.

---

## 2. Formal Interface Definition (`aec/backbone/interface.py`)

```python
class ContinuationPolicy(ABC):
    """Encapsulates isolated stateful continuation for shadow counterfactual rollouts."""
    
    @abstractmethod
    def step_action(self, rollout: Any, player: int = 0) -> Dict[str, Any]:
        """Produce the next action for a simulated forward rollout state.
        
        Args:
            rollout: ShadowRolloutState representing simulated environment state.
            player: 0 or 1.
            
        Returns:
            Kaggle-compliant action dict {'farmer': [...], 'hands': [...], 'market': [...]}.
        """
        ...

    @abstractmethod
    def snapshot(self) -> Dict[str, Any]:
        """Capture isolated snapshot of continuation state."""
        ...

    @abstractmethod
    def restore(self, snap: Dict[str, Any]) -> None:
        """Restore continuation state exactly to snapshot."""
        ...


class BackbonePolicy(ABC):
    """Formal interface separating the macro-planning backbone from the AEC supervisor."""

    @abstractmethod
    def identity(self) -> str:
        """Return canonical backbone name (e.g. 'V3_STANDALONE', 'V25_P3_UNIFIED')."""
        ...

    @abstractmethod
    def version(self) -> str:
        """Return version string."""
        ...

    @abstractmethod
    def code_hash(self) -> str:
        """Return SHA-256 fingerprint of the backbone implementation."""
        ...

    @abstractmethod
    def act(
        self,
        observation: Dict[str, Any],
        configuration: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute normal live action for the active game step.
        
        Hard Invariant: Must be called exactly once per live game step.
        """
        ...

    @abstractmethod
    def macro_fingerprint(
        self,
        observation: Dict[str, Any],
        player: int = 0
    ) -> Dict[str, Any]:
        """Compute the macro economic fingerprint for regime divergence detection.
        
        Fields: cash, crop inventory, livestock count, worker count,
        planned crop cycle, market regime, terminal phase.
        """
        ...

    @abstractmethod
    def snapshot_state(self) -> Dict[str, Any]:
        """Capture a complete, isolated memory snapshot of the backbone state."""
        ...

    @abstractmethod
    def restore_state(self, snapshot: Dict[str, Any]) -> None:
        """Restore backbone state exactly from snapshot without side-effects."""
        ...

    @abstractmethod
    def create_continuation_policy(self) -> ContinuationPolicy:
        """Instantiate an isolated continuation policy for counterfactual exploration.
        
        Hard Invariant: Calls to the returned ContinuationPolicy must NEVER mutate
        or contaminate the live BackbonePolicy state.
        """
        ...

    @abstractmethod
    def get_future_trajectory(
        self,
        step: int,
        horizon: int,
        player: int = 0,
        n_hands: int = 0
    ) -> List[Dict[str, Any]]:
        """Extract deterministic planned actions for steps [step + 1 .. step + horizon - 1].
        
        Read-only lookahead for static plan alignment.
        """
        ...

    @abstractmethod
    def reset(self) -> None:
        """Reset state for a fresh match."""
        ...
```

---

## 3. Six Hard Invariants of the Contract

1. **Exactly-Once Live Execution**: `act()` is called at most once per live turn. Repeated calls on the same turn raise `RuntimeError`.
2. **Cloned-State Continuation**: The evaluator evaluates what the *active backbone* would do from a cloned state, rather than what V3 would do.
3. **Absolute State Isolation**: Invoking `create_continuation_policy()` and calling `step_action()` on simulated rollouts has zero side-effects on live state.
4. **Deterministic Replay**: Identical observation and configuration sequences produce identical action sequences.
5. **No State Contamination**: Internal global variables (e.g. `_PARENT_NS`, route tapes, queues) are deepcopied on snapshot and restored on restore.
6. **Zero Economic Intrusion**: The adapter only translates interfaces; it does not insert, suppress, or modify economic choices.

---

## 4. Conformance Verification Plan
- **V3 Adapter**: Verified against `submission_Vj_kc_v3.tar.gz` across 720 turns on Seed 249376 (zero differences).
- **V25 P3 Adapter**: Verified against standalone `candidates/v25_p3_unified.py` across 720 turns on Seed 249376 (zero differences).
