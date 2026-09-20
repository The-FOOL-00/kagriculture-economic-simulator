# PHASE022 SUBMISSION REPRODUCTION (Independent Adversarial Audit)

**Date**: 2026-09-20
**Archive**: `submission_aec_v22.tar.gz` (SHA256
`2b23bc228366e7df5fbe4ecdd38bd3c26d3fd1c0da58e5b97f745c979075df23`, 547,236 bytes)
**Method**: fresh extraction to `/tmp/v22audit`; static audit; execution under
`kaggle_environments` 1.32.7 (the competition loader) in a scratch venv. The
repository archive was never modified.

## 1. Static audit: PASS

| Check | Result |
| --- | --- |
| Archive SHA256 | `2b23bc22...` matches expected |
| Size | 547,236 bytes matches manifest |
| Member count | 130 (108 files + 22 dirs) matches report |
| Entrypoint | `main.py:agent` present, correct signature |
| Bundled V3 SHA256 | `845e0d10...` bit-identical to frozen V3 |
| Packaged `aec/` vs working tree | `diff -r` IDENTICAL (audited == packaged) |
| Packaged `config.py`, `extracted_agents/` | IDENTICAL to working tree |
| Third-party imports | none (stdlib + shipped locals only; `kagsim` imported solely by dead file `aec/counterfactual/parity_harness.py`, unreachable from live path) |
| Absolute paths / user names | none in submission members |
| Secrets / credentials | none |
| Network imports | none |
| Packaged config defaults | `frozen_mode=True`, all quarantine flags `False`, enabled = 3 foundation mechanisms |
| `extracted_agents/dmitrii_lb2800` | 5.0 MB, 9 files (report diagram shows 1 file; only `unit_model.py` is imported; rest is dead weight, harmless) |
| `main.py` line endings | CRLF (cosmetic only) |

## 2. Execution under the competition loader: FAIL (release-blocking)

Reproduction of the report's own QA procedure
(`make("kaggriculture", {"episodeSteps": 720, "seed": 249376}).run([main.py, "starter"])`):

| Run | P0 (AEC submission) | P1 | Steps | Status |
| --- | --- | --- | --- | --- |
| Direct `main.py` (run 1) | **$3,000.00** | $3,421 | 720 | DONE |
| Direct `main.py` (run 2) | **$3,000.00** | $3,421 | 720 | DONE |
| V3 reference vs starter | $185,041.00 | $3,658 | 720 | DONE |
| AEC vs V3 head-to-head | $3,000.00 | $149,763 | 720 | DONE |

$3,000.00 is exactly `STARTING_MONEY`: the submission earned zero net income in
every game. It loses to its own backbone by ~$146,000 head-to-head.

### 2.1 Root cause (confirmed, not hypothesized)

Kaggle's loader (`kaggle_environments/agent.py:get_last_callable`) executes the
agent file via **`exec(source, {})` -- with no `__file__` defined**. The
packaged `main.py` resolves its directory at module top:

```python
_DIR = os.path.dirname(os.path.abspath(__file__))  # NameError under KE
```

Direct confirmation: `exec(open('main.py').read(), {})` raises
`NameError: name '__file__' is not defined`.

Failure chain:

1. Every step, agent construction raises `NameError`, wrapped by KE as
   `InvalidArgument`, captured as the action object (`Agent.act` try/except).
2. The kaggriculture interpreter coerces non-dict actions to `{}` (`{}` ->
   all-PASS defaults; `kaggriculture.py:557,914`), silently.
3. Result: all-PASS episode, DONE, $3,000.00, fast (1.2 s; zero V3 compute),
   deterministic -- matching every "passing" QA signal in the report.

Control experiment proving the diagnosis: loading the identical packaged code
through a wrapper that supplies a real module (with `__file__`) plays a full
V3-scale game ($185,041.00, DONE, deterministic across repeats, 719 agent
calls, decisions BACKBONE/ABSTAIN only on seed 249376 -- consistent with the
kagsim tie on that seed). The AEC code is functional; **the entrypoint is what
is broken, and only under the competition loader.**

### 2.2 Why the packaged QA certified a dead agent

`scripts/build_phase022_submission.py:188-189` asserts only
`status == DONE` and `p0_reward > 0`. A dead all-PASS agent satisfies both
($3,000 > 0). The "determinism check" ($3,000 == $3,000) then certifies the
corpse as bit-identical. Contributing QA weaknesses:

- Wrong opponent (`starter` instead of V3): no behavioral-correspondence check.
- Vacuous reward bar (no comparison against the $94k validation scale or the
  $3k starting-money floor).
- `debug=False`: KE hides the per-step `Invalid raw Python` errors.
- 5.21 s full-match runtime (7.2 ms/step) contradicts the validation mean of
  75.76 ms/step by 10x -- a discrepancy the QA never flags.
- P1 (starter) reward never recorded or sanity-checked.

## 3. Instrumentation anomaly (fully explained, not a second bug)

An instrumented scratch copy of `main.py` (logging added) ran to $3,000 with
zero log lines written: further proof the file's `agent()` body never executes
under KE (module exec fails before any call). No additional defect.

## 4. Fix description (NOT implemented -- auditor role)

Single-point entrypoint repair, confined to the generated `main.py`:

- Resolve the submission root without `__file__` at import time (KE injects
  `configuration["__raw_path__"]` on every call; usable with `os.getcwd()` /
  `sys.path` fallbacks for non-KE harnesses).
- Keep all `aec.*` imports as-is (they resolve via KE's `exec_dir` sys.path
  append during exec and via `sys.modules` afterwards; verified no lazy
  third-party imports exist on the live path).
- Strengthen QA to: assert reward far above starting money (e.g. > $10,000 vs
  starter); run against the V3 reference head-to-head in KE; surface agent
  stderr (debug) and fail on any agent-side exception; assert per-step latency
  within an order of magnitude of validation; rebuild and re-verify the
  archive hash.

Note the irony: `BackboneAdapter` already resolves the V3 tarball relative to
its own module path (which works under KE); only `main.py`'s absolute-path
override breaks. The repair is small but the archive must be rebuilt and every
packaged claim re-verified.

## 5. Classification

**Package integrity (static): PASS. Standalone execution (behavioral): FAIL.**
The submission as packaged does not execute its own code in the competition
environment. This alone blocks release regardless of all other findings.
Re-verification after repair is mandatory; the current archive hash must be
retired.
