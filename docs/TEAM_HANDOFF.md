# Teammate handoff

Updated October 26, 2026. This is the starting point for continuing MCPShield.
Use [current status](../PROJECT_STATUS.md) for the summary and
[problem/solution log](PROBLEM_SOLUTION_LOG.md) for the development history.

## 1. Get the complete working version

The repository root contains `shield/`, `frontend/`, `scripts/`, `tests/` and
`Dockerfile`. On the current machine it is
`C:\Users\panos\Desktop\MCPShield\MCPShield`; the outer folder contains checkpoints.
Run the commands below from the repository root.

The pre-continuation commit was `62aec72`. The user authorized publishing the
complete continuation, including this handoff. Update your clone to the commit
containing this guide; use `git log -1` to identify the revision. The earlier
handoff checkpoint remains a point-in-time local snapshot. Recorded experiment
evidence is transferred separately as explained below.

Git deliberately excludes model weights, dependencies, generated/raw data and
`results/`. Checkpoints are outside the repository at `../checkpoints/` and are
also not part of a clone. Teammates needing the recorded historical predictions
should receive the handoff `evidence.zip` in addition to source. Keep credentials
in local environment settings; the local Ollama key is only the `ollama` placeholder.

## 2. What is implemented and where

| Area | Files | Current behavior |
| --- | --- | --- |
| Gateway and access policy | `shield/core.py` | Request/response checkpoints, mandatory paths/tools/permissions, retained response approval, final blocks cannot be overridden |
| Rules / LLM / hybrid | `shield/detectors.py` | Explicit fixture authorization, real local classifier, schema validation, safe failure codes, contextual heuristic review |
| Virtual tools and agent | `shield/simulation.py` | Four tools, deterministic vulnerable agent, independently recorded virtual effects; no real dangerous execution |
| Data generation | `shield/dataset.py`, `data/authored_scenarios.json`, `data/coverage-manifest.json` | Preserve original adaptations and generate expanded v2; validate frozen authored bytes and groups |
| Metrics and experiment protocol | `shield/experiments.py` | Same cases for four methods, warning denial, real-model opt-in, raw observations and paired latency |
| API / approvals / activity | `shield/api.py` | FastAPI, one-time approval/expiry, per-session locking, mock JSON-RPC MCP subset |
| Dashboard | `frontend/src/main.jsx`, `style.css` | Activity, simulations, approval review, dataset explorer, measured comparison, JSON export |
| Local model launcher | `scripts/local_llm.ps1`, `check_llm.py` | Process-local Windows configuration and real connection probes |
| Versioned evaluation | `scripts/evaluate_local.py` | Validation by default, exact model provenance, journals, no evidence overwrites |
| Before/after analysis | `scripts/compare_versions.py` | Matching case/repetition sets, labels and baseline effects; separates added coverage |
| Deployment | `Dockerfile`, `compose.yaml`, `compose.local-llm.yaml` | Base app and optional namespace-local Ollama service with persistent model volume |
| Tests | `tests/test_core.py`, `test_system.py`, `test_policy_v2.py`, `test_reporting.py` | Enforcement, approvals, API, dataset intent/coverage, failures and runtime metadata |

The project still compares exactly **no defense, rules, LLM, hybrid**. No AutoML
or weight training was added. See [proposal alignment](PROPOSAL_ALIGNMENT.md).

## 3. Dataset counts and terminology

| Dataset | Legitimate | Malicious | Validation | Test/regression | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original adaptations | 42 | 84 | 36 | 90 | 126 |
| Added authored coverage | 20 | 12 | 12 | 20 | 32 |
| Current combined v2 | 62 | 96 | 48 | 110 | 158 |

The original 90 test cases contain 30 legitimate and 60 malicious interactions.
The expanded 110 contain 42 legitimate and 68 malicious interactions.

The original 126 are nine templates repeated over 14 selected repository sources
from pinned MCP metadata. Metadata is not a labeled attack dataset: our labels
describe authored interactions and expected virtual effects, not source-server
reputations. The added 32 are separately marked `authored_fixture` cases and give
both splits legitimate coverage of all four tools.

Validation tuned policy/prompts; no model weights were trained. The original test
was inspected in v1, and the authored additions are development regressions.
Neither is an untouched independent final evaluation. Preserve this distinction
in presentation/report claims. See [methodology](METHODOLOGY.md).

## 4. Fresh native setup (Windows)

Prerequisites: Python 3.10+ (3.11 recommended), Node 22.12+, internet for initial
dependency/corpus/model downloads, and Ollama installed or extracted locally.
Use explicit virtual-environment Python commands to avoid the wrong interpreter.

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/fetch_corpus.py
.venv/Scripts/python.exe -m shield.dataset
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Generation writes both `data/generated/scenarios.json` (original 126) and
`data/generated/scenarios-v2.json` (default combined 158). The tracked authored
fixture files use LF line endings so their raw checksum matches on Windows/Linux.

For Ollama, follow [LOCAL_LLM.md](LOCAL_LLM.md). The measured model is
`qwen2.5:3b`, native runtime Ollama 0.40.11. If the local server is already
listening on port 11434, use that server after checking its model/configuration.
For a fresh server, keep terminal 1 open:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 serve
```

In terminal 2, download once, check, then start the dashboard:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 pull
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 check
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 dashboard
```

Dashboard: http://127.0.0.1:8000. API reference: http://127.0.0.1:8000/docs.
The helper sets process-local model/endpoint/key/output-format variables; it does
not load `.env` automatically. The default model files are in `.local/models`.
The three connection probes are not benchmark evidence. Cold model loading and
CPU inference can take seconds or longer. Run one Uvicorn worker.

For Linux/macOS native Python setup, use the activation commands in [README](../README.md).
The Windows launcher is PowerShell-specific; the Docker route below is an alternative.

## 5. Docker setup including the local model

Docker's Linux engine must be running, and host port 8000 must be available.

```sh
docker compose -f compose.yaml -f compose.local-llm.yaml up --build -d
docker compose -f compose.yaml -f compose.local-llm.yaml exec ollama ollama pull qwen2.5:3b
docker compose -f compose.yaml -f compose.local-llm.yaml exec mcpshield python scripts/check_llm.py
```

Open http://127.0.0.1:8000. Stop with:

```sh
docker compose -f compose.yaml -f compose.local-llm.yaml down
```

The model shares the application's network namespace and uses loopback HTTP;
port 11434 is not published. Model weights persist in a named volume. Verification
reused native model weights read-only; the normal setup downloads into the volume.
The base Compose file alone starts the app without a model server. Reports and
approval sessions are ephemeral in the default container; export required evidence.
Rebuild from source to include the latest reporting-script fix.

## 6. Run experiments and preserve evidence

Keep Ollama running. Develop against validation, record settings, then freeze
before a new evaluation. Existing output names already contain evidence on the
current machine, so choose fresh names for continuation runs:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 evaluate -Split validation -Repeats 1 -Output results/team-validation-r1.json
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 evaluate -Split test -Repeats 3 -Output results/team-regression-r3.json
```

`-Suite original` selects the original data; `-Suite expanded` is the default.
The local runner opts into actual model calls and refuses an existing final file
or partial journal. Partial JSONL preserves observations after interruption and
has no valid aggregate by itself. `ERROR` methods have no aggregate efficacy
score. Do not replace unavailable outputs with predictions or classify errors
as successful attack detections.

The default `python -m shield.experiments` runs baseline/rules and leaves model
methods NOT RUN. That is expected without explicit opt-in. The dashboard's
Run evaluation action starts three repetitions, controlled by its real-LLM checkbox,
and overwrites the rolling `results/evaluation.json`; versioned CLI files remain
separate. A loaded report can have one repetition while the next-run control says three.

To reproduce the fair comparison after receiving the v1 raw report:

```powershell
.venv/Scripts/python.exe scripts/compare_versions.py --before results/history/local-llm-v1-test.json --after results/policy-v2-2-json-schema-expanded-test.json --output results/team-comparison.json
```

It requires four successful methods, unchanged original labels/baseline outcomes
and matching case/repetition sets. Original 90-case and new 20-case metrics are
separate; changing case mix is not evidence of a better detector.

## 7. Evidence and progress to read first

| File / location | Meaning |
| --- | --- |
| `docs/POLICY_V2_RESULTS.md` | Latest validation, regression, fair comparison, limitations |
| `docs/PROBLEM_SOLUTION_LOG.md` | Each failure, implemented correction, verification and remaining issues |
| `docs/PRESENTATION.md` | Demo sequence and accurate presentation wording |
| `data/policy-v2-freeze.json` | Frozen classifier source/settings, prompt/schema/model/dataset hashes |
| `results/policy-v2-2-json-schema-expanded-validation.json` | Final 48-case validation, one repeat |
| `results/policy-v2-2-json-schema-expanded-test.json` | Final 110-case regression, one repeat |
| `results/policy-v2-comparison.json` | Paired original-case comparison and separate coverage summary |
| `results/policy-v2-remaining-errors.json` | Exact two model false blocks and standalone encoded-path miss |
| `results/history/` | Original v1 evidence and intermediate source archives |
| `../checkpoints/2026-10-26-team-handoff/` | Updated source/evidence archives and readable handoff documents |

Results/models/checkpoints are local artifacts, not guaranteed to arrive with a
Git clone. Preserve the original presentation, v1 model and policy-v2 checkpoints.

Known provenance correction: older v2 exports have `local_runtime.ollama` equal
to `v2-2` because a filename-tag variable replaced runtime metadata. That is not
an Ollama version. The runner is fixed and covered by `test_reporting.py`; future
exports keep the actual version object. Earlier v1 evidence and the pinned Docker
image establish runtime 0.40.11. Historical reports stay untouched; scores, model
digests and classifier settings are unaffected. The freeze hashes `shield/*.py`;
this subsequent metadata-only correction is in `scripts/evaluate_local.py`.

## 8. Tasks available for teammates

Owners are unassigned; the team should claim workstreams explicitly.

| Priority / workstream | Starting files | Next action and completion evidence |
| --- | --- | --- |
| High: model false positives | `detectors.py`, remaining-errors JSON | Add independently authored validation controls for source-metadata confusion; compare prompt/model choices, freeze a new configuration, retain both security and utility results |
| High: robustness coverage | `data/authored_scenarios.json`, `dataset.py`, policy tests | Extend encoding/traversal and benign-encoding coverage; preserve the LLM-only/hybrid distinction and prove every attack's baseline effect |
| High: independent evaluation | Dataset manifests, methodology | Obtain independent label review, audit duplicate/fork identities and encoding, freeze new attack-family-disjoint cases before model changes; document reviewer/provenance |
| Medium: repeated measurements | `evaluate_local.py`, `experiments.py` | Run three-repeat trials under a fresh output name; record hardware/runtime, rotated order and uncertainty without treating repeats as independent examples |
| Medium: latency / model selection | `detectors.py`, local model guide | Evaluate suitable alternatives on validation, measure end-to-end security/utility/latency, keep actual model digests and failed runs |
| Distribution / report | README, proposal map, results, checkpoints | Make sure teammates receive latest source and ignored evidence; keep current results distinct from historical notes |
| Optional extensions | `api.py`, `core.py`, `simulation.py` | Real MCP transport, real-model agents, durable approvals and multi-user/multi-worker support require separate design and validation |

Current expanded-suite results: rules prevent all attacks and complete 41/42
legitimate tasks; hybrid prevents all attacks and completes 40/42; standalone LLM
completes 40/42 but misses one encoded-path attack. Thus hybrid is not generally
better than rules on this suite. Model inference adds seconds. Keep these findings
visible while improving the system.

## 9. Completion checklist for the next increment

1. Record the claimed workstream and intended change in the problem/solution log.
2. Preserve historical source/reports and version changed data, prompts and policies.
3. Use validation for choices; freeze a genuinely new evaluation for new claims.
4. Keep mandatory hybrid restrictions, final approval/block semantics, fail-closed
   errors and response-without-replay behavior covered by tests.
5. Run relevant tests/builds, actual local-model checks for detector changes, and
   all four methods on identical cases. Store raw outcomes and fresh output names.
6. Update current status, measured results, proposal map if scope changes, and this
   handoff. Record what passed, what failed, what remains open and who owns it.

The current newest native suite has 55 passing tests. Policy-v2 previously passed
54 tests on both Windows and Linux Docker; those recorded runs predate the new
metadata regression. Browser and container connection checks establish runnable
integration, not independent real-agent security or deployment hardening.

The automated Windows browser helpers/tooling currently live in ignored `.local/`
(`check_browser.cjs`, `check_live_llm.cjs`, and the Playwright installation).
Screenshots/API traces are in the evidence archive. The handoff checkpoint also
contains `qa-tooling.zip`: extract it into the source root to restore helper
scripts and the Playwright package/lock files, then install the tooling:

```powershell
npm.cmd --prefix .local/browser ci
$env:PLAYWRIGHT_BROWSERS_PATH = Join-Path (Get-Location) '.local/browsers'
node .local/browser/node_modules/playwright/cli.js install chromium
node .local/check_browser.cjs
node .local/check_live_llm.cjs
```

The live helper requires local Ollama with the recorded Qwen model. These are
Windows helpers, not a maintained cross-platform CI suite. The browser flow
performs a baseline-only evaluation and updates the rolling report. Restore the
preserved model report and restart the dashboard afterward when preparing a demo:

```powershell
Copy-Item results/policy-v2-2-json-schema-expanded-test.json results/evaluation.json
```

A Git clone alone does not include this tooling or historical report. The
presentation's manual demo sequence is an alternative verification path. A
maintained cross-platform browser suite is a possible testing workstream.
