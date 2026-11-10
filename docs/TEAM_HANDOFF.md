# Teammate setup and review guide

Updated November 9, 2026. Deadline: **November 23, 2026**.
[PROJECT_STATUS.md](../PROJECT_STATUS.md) is the authoritative overview;
[RESEARCH_REPORT.md](RESEARCH_REPORT.md) contains verified findings and pending work.

## Clone and repository layout

```powershell
git clone --branch research/ml-drl-development https://github.com/panpapadopoulos/MCPShield.git
cd MCPShield
```

Work in the directory containing shield, frontend, research and Dockerfile. Do
not initialize, reset or modify any separate preserved Git repository/checkpoint.

| Directory | Purpose |
| --- | --- |
| shield/ | Historical gateway, rules/Qwen/hybrid, simulator, API and experiments |
| frontend/ | React18/Vite dashboard and read-only research results panel |
| research/ | Observation/review/custody pipeline, SetFit, Gymnasium/PPO, evaluator and export CLI |
| data/ | Authored controls, provenance, project-authored pilot and proposed reward; no raw corpus |
| scripts/ | Pinned corpus retrieval, local model setup and historical evaluation utilities |
| tests/ | Pure contracts, app/API/data tests and opt-in synthetic optimizer checks |
| docs/ | Status, methodology, results summaries and reviewer instructions |
| .github/workflows/ | CI definition; not proof of a completed remote run |

Git excludes .local, model weights/checkpoints, environments, raw/generated
metadata, reviewer returns, custody payloads and results. You do not need the
owner's .local directory to run the app. Default research rows are NOT RUN until
compatible artifacts are produced. Historical summaries are public; raw prediction
artifacts require a separately authorized transfer with provenance/reuse checks.

## Install and run the application

Use Python3.11-3.13 and Node22.12+; Python3.13 is the tested optional ML runtime.
Commands are PowerShell from repository root. No model download or paid API is
needed for the baseline/rules app. No experiment is run by these startup commands.

```powershell
python -m venv .venv
$appPy = '.\.venv\Scripts\python.exe'
& $appPy -m pip install -r requirements.txt
& $appPy -m pip install -r research/requirements-gym.txt
& $appPy scripts/fetch_corpus.py
& $appPy -m shield.dataset
npm.cmd --prefix frontend ci --no-audit --no-fund
npm.cmd --prefix frontend run build
& $appPy -m uvicorn shield.api:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 or /docs. In a second terminal, frontend development
mode is `npm.cmd --prefix frontend run dev`; Vite proxies /api to backend8000.
On POSIX use .venv/bin/python and npm instead of the Windows command names.
The app is an ASGI source application, not a wheel package. For authentication,
set MCPSHIELD_API_TOKEN before starting the server and enter the same value in the
browser's API connection settings. Use your own token; never commit it. Plain
Python does not automatically load .env. Compose does. All dangerous effects are
simulated; do not connect the vulnerable agent to real private resources.

## Reproduce data and run tests

The downloader retrieves inert JSON from pinned MCPCorpus revision
295fe37cd972ea9aa1b48578b2d7bcc40a72ee12, verifies its SHA-256, and never executes
upstream code. Reuse terms remain unverified: keep downloaded/generated metadata
local. Historical generation creates126 original and158 combined scenarios.

```powershell
& $appPy -m research.cli generate
& $appPy -m research.expand_cli
& $appPy -m research.reviewer_ui
& $appPy -m unittest discover -s tests -v
& $appPy -m pip check
```

The first command reproduces the project-authored pilot and verifies its committed
manifest. The second generates38 episodes/68 UNREVIEWED boundaries under
ignored data/generated and blank review exports under ignored .local. The third
creates two standalone offline reviewer HTML pages. No human attestation or
scientific training occurs. Commands refuse conflicting artifact overwrites;
use fresh output paths when deliberately creating a new version. Send reviewers
their own REVIEW.html/INSTRUCTIONS.md; use [REVIEW_GUIDELINES.md](REVIEW_GUIDELINES.md)
for import/adjudication instructions. Never manufacture votes or erase dissent.

Gymnasium is needed for collected environment tests; it is not a model dependency.
Default discovery includes198 tests with11 optional optimizer checks skipped.
Those checks require a separate CPU ML environment and explicit opt-in, and their
setup performs synthetic optimization. They do not require reviewed scientific
checkpoints and must not be called independent efficacy experiments.

## Optional ML dependencies, checkpoints and training gates

Install only if reviewing/running ML; keep it separate from the app environment:

```powershell
py -3.13 -m venv .local/ml-venv
$ml = '.\.local\ml-venv\Scripts\python.exe'
& $ml -m pip install torch==2.6.0+cpu --index-url https://download.pytorch.org/whl/cpu
& $ml -m pip install -r research/requirements-ml-lock.txt
& $ml -m pip check
```

The lock records the tested Windows CPU runtime; other platforms may need their
own verified lock. MiniLM (~91MB) and Qwen are not in Git. Explicitly approved
MiniLM provisioning uses `python -m research.provision_minilm --approve-download`;
its revision is1110a243fdf4706b3f48f1d95db1a4f5529b4d41. Do not run provisioning or
training just to inspect source. [TRAINING_READINESS.md](TRAINING_READINESS.md)
defines reviewed-data inputs/approval and exact training entry points. Optional
synthetic optimizer tests, only with separate authorization to execute them:

```powershell
$env:MCPSHIELD_SETFIT_INTEGRATION='1'
$env:MCPSHIELD_PPO_INTEGRATION='1'
& $ml -m unittest discover -s tests -p test_training_readiness.py
& $ml -m unittest discover -s tests -p test_ppo.py
```

Currently all68 research boundaries are UNREVIEWED and final data is NOT_COLLECTED.
Two attested agreeing independent reviews per boundary, adequate class/group
support, immutable grouped allocations, historical exclusions, custody registration
and explicit run approval are required. Binary scope is only a proposal if WARNING
support is inadequate. No reviewed-data MiniLM or independent final evaluation exists.

## Models, previous results and five-method dashboard

Read [POLICY_V2_RESULTS.md](POLICY_V2_RESULTS.md) for historical real local Qwen,
rules and hybrid findings; [TRAINED_DEVELOPMENT_RESULTS.md](TRAINED_DEVELOPMENT_RESULTS.md)
for the first PPO ablation; [RESEARCH_REPORT.md](RESEARCH_REPORT.md) for the longer
PPO run, recovery exploit and pending scientific results. Raw results are ignored,
so the absence of a report in a fresh clone means NOT RUN, not zero attack success.
The original historical experiment UI remains operational; it can generate new
local reports, so preserve existing evidence and use fresh output paths.

The new Evaluation panel reads /api/research-evaluation. It never trains or runs
inference. `research.delivery --help` documents the approved development comparison
CLI. It accepts real reviewed SetFit/PPO checkpoints and opt-in local Qwen, records
actual model identities and produces a fresh checksum envelope. Its24-case bank
is synthetic development validation, not the reviewed corpus or independent test.

Example command shape AFTER checkpoint availability and separate run approval:

```powershell
& $ml -m research.delivery --setfit-run PATH_TO_REVIEWED_SETFIT_RUN --ppo-run PATH_TO_COMPLETED_PPO_RUN --ppo-seed 11 --include-qwen --output .local/research-phase2/dashboard-comparison-v2.json --approve-development-comparison
```

Qwen must be installed/running locally; configure MCPSHIELD_LLM_BASE_URL to
http://127.0.0.1:11434/v1, MCPSHIELD_LLM_MODEL to the exact installed model and
MCPSHIELD_LLM_API_KEY to a local placeholder. Missing/invalid checkpoint identities
cannot publish model scores. The current artifact format is DEVELOPMENT_ONLY.
Use the default artifact path or set MCPSHIELD_RESEARCH_REPORT before API startup,
then Refresh results. Recommendations, authorization overrides, uninterrupted
completion and unsafe effects stay separate. No final-test command is provided:
release/schema compatibility/frozen protocol still require independent action.

Docker recipe/Compose exist, but the CURRENT image build/startup is unverified
because Docker Desktop Linux engine was unavailable during QA. When it is running,
use `docker compose build --no-cache`, `docker compose up -d`, and check
http://127.0.0.1:8000/api/health before claiming container readiness.

## What to review and finish

Review trust-boundary projection, review/historical-exclusion gates, saved model
provenance, common authorization, incomplete artifact handling, interrupted utility,
recovery exploit accounting and honest pending report sections. Reward-utility-v2
is PROPOSED / NOT EVALUATED, inactive. No additional architecture or PPO search is
required. Do not assume the zero-harm PPO seeds recognize attacks.

Critical path to November23: owner-coordinated reviews/custody -> approved SetFit
run -> approved common comparison -> model/protocol freeze -> authorized independent
evaluation -> verified artifact/report completion and final demo/regressions.
Positive PPO improvement is not required; preserve the negative results. Review
or custody delays, sparse class support, unknown classifier behavior and Docker
availability remain risks. Do not replace missing evidence with synthetic scores.
