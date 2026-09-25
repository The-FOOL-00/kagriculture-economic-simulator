# V30 PACKAGING AUDIT — A7-standalone experimental candidate

## Artifact

- File: `submission_a7_v30.tar.gz` (143,296 bytes)
- SHA256 (this build): `4a07673072b6aef9346bf4c21ee5a5979b9da50fccc609fb731dcdbf8f016619`
  (gzip/tar mtimes vary per build; source identity is the stable hash below)
- Source: `candidates/v30_a7_standalone/main.py`
  SHA256: `51c1d25245f68dd8de66b355f2ad6ca1d79de8af02efed521a5a82f7be69ce3f`
- Builder: `scripts/v30_build_a7_standalone.py` (SHA-gated inputs)

## Checklist (§36)

| Check | Result |
|---|---|
| root `main.py` only in tarball | PASS (`tar tzf` = `main.py`) |
| competition loader (fresh dir, import agent, full match) | PASS (AST 129,182 vs V3 127,896) |
| package size | PASS (143KB) |
| dependency availability | PASS (stdlib `math` only) |
| no external network | PASS (no socket/urllib/requests; one false-positive substring `hire_requests`) |
| deterministic startup | PASS (cross-process digest identity) |
| no forbidden absolute paths | PASS (none in new code; V3 bytes verbatim) |
| no research-only imports | PASS (no aec/test/scratch imports) |
| no debug output breaking protocol | PASS (agent returns dict; silent) |
| A7 signature via loader path | PASS (+1,286 exactly) |

## Slot recommendation (§25, §43 — human decides)

- Slot A (robust, KEEP): V22R1 — submitted, frozen, frontier-level
  (ties V3, beats DMITRII 16-0, self-play 101.6k).
- Slot B (experimental challenger): `submission_a7_v30.tar.gz` — beats
  Slot A 16-0 (+1,272), beats all 6 tested meta families 80-0, inherits
  V29's 80-0 holdout vs V3-regime.
- Never replace Slot A with the challenger until live games validate it;
  the two-slot constraint means the challenger displaces whatever is
  currently second — confirm current slot contents before submitting.

## Known limitations

- A7's edge is EXTRACTIVE (V29): it exploits the V3-regime opening, it
  does not raise absolute output. If the live field has moved off the
  V3-regime opening, the +1.3k edge may not transfer (but nothing
  observed beats A7 either: worst case it plays V3-level = frontier).
- Late-September live top is unobservable from here; recommendation rests
  on early/mid-September observables + mechanism reasoning.
- Tarball bytes are not reproducible across rebuilds (mtimes); the
  recorded SHA256 refers to THIS build. Rebuilding requires re-recording
  (source SHA is stable).
