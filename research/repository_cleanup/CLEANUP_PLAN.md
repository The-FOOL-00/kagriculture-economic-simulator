# KAGRICULTURE REPOSITORY CLEANUP & ARCHIVAL PLAN

This document outlines the step-by-step procedure for converting the Kagriculture workspace into a clean, reproducible, production-grade Git repository.

---

## 1. Objectives & Guiding Constraints
1. **Zero Data Loss**: Preserve all actual research scripts, candidate agents, production submissions, benchmark harnesses, postmortems, and configs.
2. **Eliminate Debris**: Remove ~18 GB of untracked and ignored caches, virtual environments, raw replay dumps, and temporary JSON files.
3. **Formalize Culture Versions**: Convert physical `Kagriculture-v24` and `Kagriculture-v25` directories into permanent, clean Git branches (`culture/v24`, `culture/v25`) and remove worktree folders from disk.
4. **Preserve Provenance**: Accurately document the Incumbent agent (V49 Meta Fusion), teammate contributions (Vj_kc_v24, Vj_kc_v27), and research progression (V40-V60).
5. **No History Destruction**: The Git object database is already clean (~99.7 MB). Do not rewrite Git history.
6. **Logical, Reviewable Commits**: Group changes into focused, semantically typed commits (`feat:`, `archive:`, `docs:`, `chore:`, `cleanup:`).

---

## 2. Execution Phases

### Phase 1: Non-Destructive Audits (Completed)
- Total size, file count, and directory breakdown cataloged (`LARGE_FILES.md`).
- File classification and retention policy defined (`FILE_CLASSIFICATION.md`).
- Full secrets scan completed across whole repository: **0 credentials found**.
- Worktree analysis and hash comparison between V24, V25, and Main completed.

### Phase 2: Culture Branch Archival & Worktree Pruning
1. In `Kagriculture-v24`, commit uncommitted small manifests (`V24_COHORT_MANIFEST.json`, `V24_LIVE_LEADERBOARD_SNAPSHOT.json`, `V24_QUAL_MANIFEST.json`, `V24_REPLAY_CORPUS_MANIFEST.json`).
2. Create/update branch `culture/v24` pointing to this complete state.
3. In `Kagriculture-v25`, commit uncommitted small manifests (`V25_COHORT_MANIFEST.json`, `V25_QUAL_MANIFEST.json`).
4. Create/update branch `culture/v25` pointing to this complete state.
5. Safely detach and remove the worktrees `C:\Users\Sundareswaran\Kagriculture-v24` and `C:\Users\Sundareswaran\Kagriculture-v25`.

### Phase 3: Manifests & Dataset Documentation
1. Create `data/README.md` and `data/MANIFEST.csv` detailing all excluded large replay corpora.
2. Create `docs/DATASETS.md` explaining acquisition URLs, commands, schemas, and checksums.

### Phase 4: Canonical Repository Documentation
1. Create `docs/FINAL_ARTIFACTS.md` (Incumbent V49 Meta Fusion, SHA256: `8CAFF630...`, packaging and benchmarks).
2. Create `docs/AGENTS.md` (Comprehensive catalog of all candidate and historical agents with SHA256 hashes).
3. Create `docs/RESEARCH_HISTORY.md` (Detailed chronological breakdown of V40 through V60 research hypotheses and findings).
4. Create `CHANGELOG.md` (Major competition milestones).
5. Update `README.md` (Clear top-level navigation, agent execution instructions, and repository structure).

### Phase 5: Destructive Working Tree Cleanup
1. Execute deletion of Class E and Class D items strictly matching `DELETION_MANIFEST.md`.
2. Free ~18 GB of disk space.

### Phase 6: Hardened .gitignore
1. Update `.gitignore` to prevent any future reintroduction of `.venv`, `__pycache__`, raw replays (`*.json` in replay folders), large `.pt` models, `.jsonl` dumps, and sensitive files.

### Phase 7: Logical Git Commits & Branch Alignment
1. Commit research reports and tooling (`research: ...`).
2. Commit candidate agents (`candidate: ...`).
3. Commit documentation (`docs: ...`).
4. Commit configuration and cleanup governance (`chore: ...`).
5. Fast-forward / update `main` to the final state.

### Phase 8: Final Validation & Report
1. Run pre-push checks (`git status`, `git diff`, `git count-objects`).
2. Verify Python agent execution sanity.
3. Generate `FINAL_CLEANUP_REPORT.md`.
