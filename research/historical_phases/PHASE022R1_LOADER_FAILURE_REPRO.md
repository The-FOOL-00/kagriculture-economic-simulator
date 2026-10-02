# PHASE022R1 — V22 LOADER FAILURE REPRODUCTION

**Date**: 2026-09-20
**Artifact under test**: `submission_aec_v22.tar.gz` (SHA256 `2b23bc22...`, RETIRED)
**Method**: exact competition-loader simulation + real `kaggle_environments` 1.32.7 execution.
No repository code was modified for this reproduction. Scratch work in `/tmp` only.

## 1. Loader contract (verified in installed KE 1.32.7 source)

`kaggle_environments/agent.py:get_last_callable` executes agent sources as:

```python
code_object = compile(raw, path_str, "exec")
env = {}
if path is not None:
    exec_dir = os.path.dirname(path)
    sys.path.append(exec_dir)   # importability only, during exec
exec(code_object, env)          # bare namespace: NO __file__
```

So the competition loader guarantees importability of sibling files during
`exec`, but provides **no `__file__`**, no `__package__`, no module object.

## 2. Exact simulation (mission §3 semantics)

```python
source = open("main.py", encoding="utf-8").read()
namespace = {"__name__": "__main__"}
exec(compile(source, "main.py", "exec"), namespace)
```

Result (reproduced, `/tmp/v22r1_repro_fail.py`):

```text
EXCEPTION: NameError: name '__file__' is not defined
  File 'main.py', line 9, in <module>: '_DIR = os.path.dirname(os.path.abspath(__file__))'
```

First failing line: **packaged `main.py:9`** (module top, unconditional).
`agent()` is never defined; every step fails identically because KE lazily
(re-)execs the source per agent construction and the exception object becomes
the action.

## 3. End-to-end degradation under real KE (`/tmp/v22r1_ke_fail.py`)

`make("kaggriculture", {"episodeSteps": 720, "seed": 249376}, debug=False)
.run([packaged_main_py, "starter"])`:

| Player | Status | Reward |
| --- | --- | --- |
| P0 (V22 submission) | DONE | **$3,000.00** |
| P1 (starter) | DONE | $3,421.00 |

$3,000.00 is exactly `startingMoney` (KE `kaggriculture.py`: default 3000):
zero net income. 720/720 steps DONE. With `debug=True`, KE surfaces the
per-step `InvalidArgument: Invalid raw Python: NameError(...)` instead of
coercing; with `debug=False` (as in the shipped QA) the failure is silent.

Why every action degrades to PASS (`kaggriculture.py:558,915-916`):

```python
m = action.get("market", []) if isinstance(action, dict) else []
farmer_action = action.get("farmer", ["PASS"]) if isinstance(action, dict) else ["PASS"]
hands_actions = action.get("hands", []) if isinstance(action, dict) else []
```

The raised `InvalidArgument` exception object is not a `dict`, so the
interpreter substitutes all-PASS defaults. The recorded step-0 P0 action is
`{'farmer': ['PASS'], 'hands': [], 'market': []}` — the corpse signature.

Terminal reward: **$3,000.00** (starting money), deterministic across runs,
matching the auditor's 3x reproduction and the shipped QA's own
"$3,000.00 == $3,000.00" log line.

## 4. Exhaustive `__file__` inventory (all packaged `*.py`)

| Location | Context | Fatal under KE? |
| --- | --- | --- |
| `main.py:9` | module top of the **exec'd** entrypoint | **YES — root cause** |
| `aec/integration/backbone_adapter.py:60` | real module import (`__file__` set normally) | No |
| `aec/counterfactual/simulator.py:36,48` | ImportError fallback inside real module | No |
| `aec/evaluation/asset_value.py:31` | ImportError fallback inside real module | No |
| `aec/patches/harvest_patch.py:62` | ImportError fallback inside real module | No |
| `extracted_agents/dmitrii_lb2800/main.py:9` | dead file (never imported; only `unit_model.py` is), already loader-safe via `globals().get("__file__")` | No |
| `submission_Vj_kc_v3.tar.gz:main.py` | 0 occurrences; exec'd in bare ns by `BackboneAdapter` | No |

`main.py:9` is the **only** module-level `__file__` dependency on the live
path. Nothing in `aec/` or `scripts/` imports `main`, so the entrypoint has
no reverse dependencies. The `aec.*` uses are safe because KE imports them as
real modules (with `__file__`) via the temporary `exec_dir` sys.path entry,
and `sys.modules` retains them afterwards.

## 5. Classification

Auditor finding (entrypoint `__file__` failure): **CONFIRMED** — reproduced
at both the bare-`exec` level and end-to-end under KE 1.32.7 with identical
reward signature ($3,000.00 / $3,421, DONE/720).
