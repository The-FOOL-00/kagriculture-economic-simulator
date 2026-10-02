# DEVELOPMENT GATE 0.3 — ZERO-LEAKAGE THREAT MODEL

## Forensic Threat Model, Attack Surface Taxonomy, and Containment Invariants

**Gate Protocol**: Development Gate 0.3 Remediation and Re-Certification  
**Governing Standard**: Absolute Zero-Leakage & Active Runtime Containment Standard  
**Document Status**: **ACTIVE ARCHITECTURAL SPECIFICATION**  
**Date**: 2026-09-11  
**Author**: Antigravity Autonomous Pair Programmer (Audit & Security Engine)  

---

## 1. Executive Summary & Security Philosophy

In Development Gate 0.2, the automated verification harness in `scratch/verify_agent_zero_leakage.py` was revealed to be purely documentary and passive: it monitored only what the simulator emitted, while placing zero active constraints on the candidate agent during `agent.act()`. As a result, 100% of malicious positive-control agents bypassed the harness undetected.

This document establishes the **formal threat model** for development experimentation. 

### Security Boundary Definition
In the Kaggriculture competition, agents run as standalone Python programs executing in a containerized evaluation environment. During local development, candidate agents run in the same Python process as the simulation harness to enable high-throughput benchmarking. This creates a severe threat surface: **an agent can inspect the process memory, traverse the Python runtime, or read the local filesystem to extract unrevealed information**.

The goal of the Active Containment Sandbox is **not** to claim impossible CPython kernel-level absolute isolation (which would require hardware hypervisors or seccomp containers), but rather to establish an **active, multi-layered runtime enforcement boundary** that guarantees no candidate agent can access future simulation state, opponent private state, external disk data, or non-deterministic process channels during evaluation.

---

## 2. Attack Surface Taxonomy & Threat Matrix

The table below catalogs every identified attack surface across the Python execution environment, documenting concrete attack examples, previous (Gate 0.2) protection status, and the mandatory active containment protections enforced in Gate 0.3.

| # | Attack Surface | Concrete Attack Vector Example | Existing Gate 0.2 Protection | Required Gate 0.3 Active Containment Guarantee |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Python Filesystem** | `open("sample_replay.json")`, `open("results/phase3_shop_census_500seeds.json")`, reading disk artifacts to discover future shop unlocks or match history. | None. Filesystem was completely open. | **Active Builtin Interception**: `builtins.open` is intercepted during `act()`. Any attempt to read or open files raises `LeakageViolationError` immediately. |
| **2** | **Module Imports** | `import kagsim`, `import subprocess`, `import socket`, `import ctypes` at runtime inside `act()` or within nested functions. | Superficial top-file AST check only; runtime dynamic imports were completely unmonitored. | **Dynamic Import Sandbox**: `builtins.__import__` is wrapped with a strict deny-list blocking `kagsim`, `ctypes`, `subprocess`, `socket`, `urllib`, `requests`, `multiprocessing`. |
| **3** | **Python Reflection** | `getattr(obj, "__subclasses__")()`, traversing class hierarchies to find `kagsim.Game` or `_sim` references. | AST symbol check for `__subclasses__` on top-level file only. Easily evaded via string concat or `globals()`. | **Reflection Isolation**: Frame walking and class tree traversal are severed. Simulator references are decoupled from agent-accessible namespaces. |
| **4** | **Garbage Collector (`gc`)** | `for o in gc.get_objects(): if type(o).__name__ == "Game": opp = o.observe(1)` to discover live simulation objects and read opponent shed/inventories. | None. `gc` module was completely unrestricted. | **GC Interception Hook**: `gc.get_objects` is hooked during `act()` to raise `LeakageViolationError` on invocation, completely blinding agents to heap objects. |
| **5** | **Subprocess Execution** | `subprocess.run(["python", "-c", "import kagsim..."])`, `os.system(...)`, executing out-of-process simulator or file parsers. | None. `os` and `subprocess` could spawn shell processes. | **Subprocess Blocking**: `subprocess.Popen`, `subprocess.run`, `subprocess.call`, `os.system`, and `os.popen` are hooked to raise `LeakageViolationError`. |
| **6** | **Sockets & Network** | `socket.socket()`, `urllib.request.urlopen()`, phoning home to external or local HTTP server for ground-truth lookahead. | Top-level AST import check only. Dynamic import or existing socket object bypassed it. | **Network Hook & AST Block**: `socket.socket` raises `LeakageViolationError` at runtime; recursive AST audit rejects network libraries. |
| **7** | **Process Environment** | `os.environ["SECRET"]`, `os.environ.get("COMPETITION_SEED")`, extracting out-of-band state passed through environment variables. | None. `os.environ` was completely readable. | **Environment Sanitization Proxy**: `os.environ` is replaced during `act()` with an isolated proxy that raises `LeakageViolationError` on any read. |
| **8** | **Multiprocessing** | `multiprocessing.Process()`, `concurrent.futures.ProcessPoolExecutor()` spawning isolated workers to bypass sandbox hooks. | None. Multiprocessing unmonitored. | **Process Spawning Prohibition**: `multiprocessing` and related fork/spawn methods are intercepted and prohibited during evaluation. |
| **9** | **Foreign Function (`ctypes`)** | `ctypes.string_at(...)`, `ctypes.pythonapi` manipulating raw pointers to read C++ `Sim` state directly from memory. | Top-level AST import check only. `ctypes` already in memory was usable. | **Ctypes Memory Interception**: `ctypes.string_at`, `ctypes.CDLL`, and dynamic `import ctypes` are intercepted and blocked with `LeakageViolationError`. |
| **10** | **Inspect Module** | `inspect.stack()`, `inspect.currentframe()`, peeking up the call stack into the simulator harness frame to extract `g` or opponent observations. | Top-level AST import check only. Helper modules or dynamic inspect bypassed it. | **Call Stack Interception**: `inspect.stack`, `inspect.currentframe`, and `sys._getframe` are patched during `act()` to raise `LeakageViolationError`. |
| **11** | **Debugger / Trace Hooks** | `sys.settrace()`, `sys.setprofile()` intercepting simulator step execution from within the agent process. | None. Trace hooks unmonitored. | **Execution Trace Prohibition**: Setting or querying execution trace hooks during agent runtime is prohibited. |
| **12** | **Simulator Object Discovery** | Finding `kagsim.Game` via globals, function closures, or default arguments. | None. Simulator instance was passed or visible in caller scope. | **Scoped Isolation**: Harness isolates `g` in local scope, never assigns `g` to module globals or attributes, and blocks frame climbing. |
| **13** | **Global PRNG State** | `random.getstate()`, `random.setstate()`, predicting future random events or resetting PRNG to force deterministic outcomes. | Superficial symbol check for `_rng`. Standard `random.getstate()` completely open. | **PRNG State Guard**: `random.getstate` and `random.setstate` raise `LeakageViolationError` during `act()`. Agent internal RNG must use private instances. |
| **14** | **Module Globals (`globals()`)** | Querying `globals()` or `__main__.__dict__` to discover harness references or opponent variables. | None. Module globals completely open. | **Namespace Encapsulation**: Active simulator and evaluation harness run in isolated scope; `sys.modules['__main__']` contains no simulation pointers. |
| **15** | **`sys.modules` Reflection** | `sys.modules['kagsim']` or `sys.modules['__main__']` lookups to bypass import statements and reach simulator internals. | None. `sys.modules` dictionary was completely exposed. | **Module Table Guard**: Accessing forbidden simulator modules or harness internals via `sys.modules` raises `LeakageViolationError`. |
| **16** | **Helper Module Evasion** | Placing forbidden logic in `local_helper.py` (`import inspect; def peek(): return inspect.stack()`) to evade single-file AST audit. | 100% bypass in Gate 0.2. AST auditor only checked top-level file. | **Recursive AST Auditor**: AST inspection traverses the entire agent directory, recursively auditing every imported local file before execution. |

---

## 3. Threat Model Guarantees and Limitations

### What the Active Containment Sandbox Guarantees
1. **Zero Filesystem Leakage**: Candidate agents cannot read replay files, results databases, seed logs, or source files during execution.
2. **Zero In-Process Simulator Introspection**: Candidate agents cannot use `gc`, `sys._getframe`, `inspect`, or `globals()` to discover the running simulation game or inspect opponent state.
3. **Zero Parallel Lookahead**: Candidate agents cannot instantiate parallel `kagsim.Game` instances inside `act()` to forecast future shop unlock schedules or future random events.
4. **Zero Out-of-Band Communications**: Candidate agents cannot spawn external subprocesses, open network sockets, or extract environment secrets.
5. **Fail-Closed Execution**: Any attempt to violate containment immediately raises `LeakageViolationError` and terminates the match as a disqualified failure.

### What the Active Containment Sandbox Does Not Claim
- **Hardware-Level Enclave Isolation**: The sandbox is a CPython runtime enforcement layer, not a hardware hypervisor (like Intel SGX) or an OS-level seccomp jail. If a malicious developer deliberately compiles custom native C extensions designed to exploit kernel memory vulnerabilities, process containment could be bypassed.
- **Scope of Intent**: The containment layer is designed to enforce scientific integrity and prevent accidental or structural data leakage in automated development pipelines. It is paired with recursive static AST screening and git provenance tracking to ensure end-to-end reproducibility.

---

## 4. Certification Criteria for Gate 0.3

Under this threat model, Development Gate 0.3 requires:
1. **100% Adversarial Failure Rate**: All positive-control adversarial agents attempting forbidden operations (across all 14 tested classes) must fail immediately at runtime.
2. **100% Production Compatibility**: Legitimate candidate agents (`ClosedLoopAgentV2`, `compiled_v54_plus_shop.py`, `compiled_v54_plus_residual.py`) must run without raising any leakage errors and produce identical behavior to unconstrained execution.
