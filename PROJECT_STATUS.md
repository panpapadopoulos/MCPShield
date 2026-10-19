# MCPShield Project Status

## Project Overview

MCPShield (CS 52560, Purdue University Northwest) is a runnable local security research prototype. React dashboard → FastAPI → resumable request/response gateway → deterministic mock MCP tools and vulnerable virtual agent. Baseline, rules, real configurable LLM and hybrid detector implementations share the same scenario interface. Enforcement is functional; live LLM experiments and deployment/visual verification have external blockers below.

Initial inspection on 2026-10-18 found no code, datasets, tests, documentation, or AGENTS.md. Root and nested MCPShield/ initially contained separate unborn Git repositories. Root now tracks origin/main at a5cc5f6 from the earlier authorized push. Nested MCPShield/.git remains untouched and excluded from implementation work. The user has now authorized committing and pushing this continuation.

## Completed

- Codex, initial increment: shield/core.py request/response rules, deny-by-default warnings, non-overridable blocks, four in-memory tools; shield/benchmark.py legacy nine-scenario smoke suite. Eight tests passed at that checkpoint. Initial smoke rules stopped all five attacks and delivered four legitimate calls; these are historical smoke results, not research evidence.
- Codex, continuation: shield/core.py now retains exact request/response snapshots across approval without tool replay. Detector errors fail closed. Unknown tools are denied before dispatch.
- shield/detectors.py: configurable real OpenAI-compatible JSON classifier, strict decision parsing, bounded HTTPS/loopback transport, disabled redirects, redacted failures, and hybrid precedence. Fake outputs are restricted to tests. LLM/hybrid experimental results remain NOT RUN.
- scripts/fetch_corpus.py and data/provenance.json: pinned inert MCPCorpus metadata download, 13,875 records, enforced SHA-256. No upstream code or servers executed.
- shield/dataset.py: deterministic source-backed adaptations, explicit authored labels/provenance, canonical repository and near-duplicate groups, split validator. Final dataset: 126 scenarios, 14 valid repository sources, 42 legitimate and 84 malicious interactions; 90 test / 36 validation. Original metadata remains unlabeled. Generated/raw data are separate and Git-ignored.
- shield/simulation.py: four virtual tools and deterministic vulnerable agent; independent recorded command, permission, private-read and disclosure effects. Request-side harm counts even when a response is blocked. Legitimate outcomes compare fixture data.
- shield/experiments.py: four-method experiment runner, identical cases/checksums, rotated repeated execution, confusion matrices, precision/recall/F1/FPR, detection/success/task-success rates, paired latency, raw outcomes, code fingerprint, explicit NOT RUN/ERROR states.
- shield/api.py: FastAPI simulation/evaluation/dataset/activity API; retained exact-phase one-time approvals with expiry/replay protection; optional bearer authentication; origin/host checks; JSON-RPC mock initialize/tools-list/tools-call endpoint. MCP clients cannot select no-defense.
- frontend/: responsive React dashboard with live polling, request/response details, severity/explanations, simulation controls, approval/denial/session review, source exploration, four-method charts, confusion matrices and JSON export. No invented activity or missing-method scores.
- Dockerfile, compose.yaml, locked Python/npm dependencies, .env.example, .dockerignore, and GitHub Actions workflow added. README and docs/METHODOLOGY.md explain reproduction, citations, policy and limitations.
- Final verification on Windows / Python 3.10.4: **41 unittest tests passed**; Vite 6.4.4 production build passed; scripts/check_server.py passed against a live owned Uvicorn process (health, dashboard HTML and JS/CSS); pip check passed; npm audit reported zero vulnerabilities; docker compose config --quiet passed; git diff --check passed. CI workflow is authored but has not run remotely.
- Final recorded experiment: 90 test scenarios × 3 repeats. Baseline TP/FP/TN/FN = 0/0/90/180, attack success 100%, legitimate success 100%. Rules = 180/30/60/0, precision 85.71%, recall 100%, F1 92.31%, FPR 33.33%, attack success 0%, legitimate success 66.67%. These are controlled template simulation results only. Full raw report is local results/evaluation.json; tracked summary docs/EVALUATION.md.

## In Progress

- No other contributor ownership is documented. Codex's implementation and local verification are complete for this prototype increment. Independent research validation is not complete.

## Pending

1. Configure MCPSHIELD_LLM_MODEL and MCPSHIELD_LLM_API_KEY; explicitly run real LLM/hybrid experiments and retain provider/model details. No credentials were available in this session.
2. Start Docker Desktop's Linux engine; run docker compose up --build and verify the image/runtime. Compose syntax alone is verified.
3. Browser visual/interaction QA at desktop and mobile widths. Computer-use inventory returned no browsers/apps; browser QA could not run here.
4. Independently review scenario labels, fix upstream metadata encoding issues through a separately versioned normalization step, expand supported source coverage, audit fork/mirror identities, and freeze attack-family holdouts before academic claims or training.
5. Evaluate real-model agents and real workloads; add latency uncertainty estimates. No model training occurs in this repository.
6. For deployment beyond local research: complete MCP transport/upstream integration, durable audit/approval storage, per-user authorization and multi-process coordination. Current MCP endpoint is an explicitly documented JSON-RPC mock subset.

## Known Issues

- Rules intentionally retain a measured false-positive limitation: harmless text mentioning system prompt is blocked. The security-document negative control exposes it; do not report perfect legitimate-task performance.
- Small, template-generated suite with shared attack families across server splits; independent label adjudication pending. Current results cannot establish generalization to unseen attacks or real agents.
- Original metadata contains some character-encoding artifacts and sparse tool definitions. A GitHub-profile-only source URL was excluded. Original text is preserved; no source server is declared safe.
- LLM/hybrid real experiments NOT RUN (no model/key). Classifier tests use explicitly mocked transports only.
- Docker client exists but its Linux engine pipe is unavailable; Docker build/run NOT VERIFIED. No browser surface was available; visual QA NOT RUN. Live API/static asset checks do not substitute for visual QA.
- Sessions, approvals, activity and API evaluation cache are in memory; use one Uvicorn worker. History is capped at 500 boundaries; sessions expire after five minutes. Reports are ephemeral in the default container.
- Starlette emits a nonfatal httpx TestClient deprecation warning; all tests pass with the locked environment.
- Shell execution requires elevation in this session because the sandbox helper fails to initialize. Node child_process was used for filesystem/read-only work; approved elevated commands handled dependency/network/test operations.
- Pinned upstream repository has no repository-level license file; verify redistribution terms before sharing raw/derived metadata. Raw data and generated metadata remain ignored by Git.

## Technical Decisions

- Python package is shield to avoid Windows case-insensitive collision with preserved nested MCPShield/ repository. No unrelated refactors or nested repository changes.
- No untrusted servers or commands executed. All dangerous effects are virtual fixtures. Downloaded JSON is parsed as data only.
- ALLOWED proceeds; WARNING pauses and requires explicit True for that phase; BLOCKED cannot be approved. Request/response snapshots prevent mutation while waiting. Response approval never reruns the tool.
- Hybrid uses BLOCKED > WARNING > ALLOWED; rule blocks short-circuit and rule warnings cannot be downgraded. Missing/invalid LLM output denies execution and invalidates aggregate experimental metrics.
- Metadata does not supply malicious/benign labels. Authored labels apply to simulated interactions. Canonical repositories and near-duplicate source descriptions stay within one split; shared templates remain a documented limitation. No training is performed.
- Default experiments deny warnings and skip external LLM calls. Real calls require opt-in. API endpoint policy is server-controlled; only the dashboard experiment interface permits the unfiltered baseline.
- Frontend is repository-local, served by FastAPI after npm build; no separate hosting service required. Loopback deployment is the default. Publication of this continuation was subsequently authorized by the user.

## Recent Changes

- 2026-10-18: User authorized commit/push of the full prototype continuation. Fetched origin, confirmed no remote advancement, checked publishable paths and credential patterns; generated/raw datasets, reports, dependencies and the nested repository remain excluded.

- 2026-10-18: Created central handoff after inspection. No commits or pushes at that point.
- 2026-10-18: Added initial shield/__init__.py, shield/core.py, shield/benchmark.py, tests/test_core.py, README.md and .gitignore; eight tests and legacy smoke evaluation passed. Corrected Windows package-name collision and reran both commands successfully.
- 2026-10-18: User authorized the earlier commit/push; resolved sandbox Git/network restrictions and published a5cc5f6 to origin/main. Nested repository excluded.
- 2026-10-18: Continuation added dataset/detector/simulation/experiment/API modules, pinned downloader and provenance, React frontend/lockfile, deployment/CI, requirements locks, tests/test_system.py, scripts/check_server.py, and methodology/results docs; extended core/legacy benchmark and README. Intermediate checks passed 32, 36 and 40 tests before final 41-test pass.
- 2026-10-18: npm audit found a high-severity issue in initial Vite 6.3.5; patched to 6.4.4 and confirmed zero reported vulnerabilities. Added hard benign control, realistic argument injection and response snapshot regression tests. Excluded malformed GitHub-profile provenance; regenerated final 126 scenarios and 90-case test report.

## How to Continue

From repository root, activate the environment (or invoke .venv/Scripts/python.exe on Windows). Dependencies, downloaded raw data, generated scenarios and dashboard build already exist locally.

~~~sh
python -m unittest discover -s tests -v
python -m shield.experiments --split test --repeats 3
python -m uvicorn shield.api:app --host 127.0.0.1 --port 8000
~~~

Open http://127.0.0.1:8000. For a fresh checkout, follow README: install requirements, run scripts/fetch_corpus.py, python -m shield.dataset, npm ci/build in frontend. Use npm.cmd under restricted Windows PowerShell.

For external LLM experiments export the model/key variables, then add --include-llm. Do not replace unavailable predictions with fixtures. For containers start the Linux engine, then docker compose up --build. Reproduce results before making claims; raw metadata and generated artifacts are intentionally not committed. This continuation is being published with explicit user authorization; the pre-existing nested repository remains excluded.
