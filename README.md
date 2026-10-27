# MCPShield

Detecting and preventing unsafe AI tool calls · CS 52560, Purdue University Northwest.

A runnable security research system with request and response enforcement, four virtual MCP tools, a vulnerable deterministic agent, four detector configurations, reproducible corpus-backed scenarios, and a React/FastAPI dashboard. All tool effects are simulated in memory; no untrusted server, shell command, private file, database, or external search is executed.

**Continuing this project? Start with the [teammate handoff](docs/TEAM_HANDOFF.md)**
for current status, implemented tasks, setup, dataset counts, experiment artifacts
and workstreams. [PROJECT_STATUS.md](PROJECT_STATUS.md) is the current summary;
older status text is preserved separately as history.

## Quick start

Use Python 3.10+ (3.11 recommended) and Node 22.12+. Commands below run from the repository root; activate the virtual environment before continuing.

~~~sh
python -m venv .venv
# Windows PowerShell: .venv/Scripts/Activate.ps1
# Windows if activation is restricted: invoke .venv/Scripts/python.exe directly
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/fetch_corpus.py
python -m shield.dataset
npm --prefix frontend ci
npm --prefix frontend run build
python -m shield.experiments --repeats 3
python -m uvicorn shield.api:app --host 127.0.0.1 --port 8000
~~~

On Windows with restricted PowerShell scripts, use npm.cmd instead of npm. Open **http://127.0.0.1:8000**. API reference: **http://127.0.0.1:8000/docs**. Vite development mode: npm --prefix frontend run dev (proxies /api to port 8000).

The dashboard includes polling tool activity, request/response details, severity and explanations, exact-phase approval/denial, attack simulations, source metadata, dataset counts, four-method comparison charts, confusion matrices, and JSON report export. It displays only observed activity and evaluated results. The approval flow can resume a retained response without executing the tool again.

## Tests and experiments

~~~sh
python -m unittest discover -s tests -v
python scripts/check_server.py
python -m shield.experiments --split test --repeats 3 --output results/evaluation.json
~~~

The default report runs baseline and rules. LLM and hybrid remain **NOT RUN** unless opted into with model/credentials. The legacy synthetic smoke command remains available: python -m shield.benchmark.

Repetitions rotate execution order; all methods use exactly the same scenario IDs and checksum. Reports retain raw decisions, observable effects, task outcomes, timing samples, confusion matrices, precision, recall, F1, false-positive rate, attack detection/success, legitimate task success, mean/p95 latency, and paired added latency. Classifier failures deny the interaction and invalidate that method's aggregate scores; unavailable calls never become synthetic predictions. Undefined metric denominators produce null. See [methodology](docs/METHODOLOGY.md), [current v2 results](docs/POLICY_V2_RESULTS.md), and [historical baseline results](docs/EVALUATION.md).

## Real LLM configuration

For a local model without paid API calls, see [Windows Ollama setup](docs/LOCAL_LLM.md).
The [historical v1 local-model results](docs/LOCAL_LLM_RESULTS.md) document substantial
false positives. The [v2 fixes and measurements](docs/POLICY_V2_RESULTS.md) track the
subsequent validation-based corrections without overwriting that evidence.

Export these environment variables in the process that runs the API or experiments. .env.example documents them; plain Python does not automatically load .env. Docker Compose does.

~~~text
MCPSHIELD_LLM_MODEL=<model supporting Chat Completions JSON output>
MCPSHIELD_LLM_API_KEY=<provider API key>
MCPSHIELD_LLM_BASE_URL=https://api.openai.com/v1
MCPSHIELD_LLM_TIMEOUT=20
~~~

Then run python -m shield.experiments --include-llm --repeats 3 or enable real LLM calls in the dashboard. Calls send scenario payloads to the configured provider and may incur its normal costs. A local OpenAI-compatible endpoint can use loopback HTTP with a nonempty placeholder key. Remote endpoints must use HTTPS. No model is hardcoded. The adapter uses [Chat Completions JSON output](https://developers.openai.com/api/reference/resources/chat), validates every response, and redacts provider errors.

Hybrid precedence (fixture-policy-v2): mandatory access violations and high-confidence rule blocks short-circuit. Extra permissions always retain WARNING or a stricter model decision. The model can resolve only `heuristic_context` warnings, such as a benign documentation prerequisite. Other decisions use BLOCKED > WARNING > ALLOWED. Model failures fail closed. Final WARNING requires explicit one-time approval; final BLOCKED cannot be overridden.

## MCP mock endpoint

POST /api/mcp accepts a JSON-RPC subset: initialize, tools/list and tools/call. Example body:

~~~json
{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"file_reader","arguments":{"path":"/public/readme.txt"}}}
~~~

The endpoint enforces MCPSHIELD_METHOD (rules by default; llm/hybrid also supported). Clients cannot select the no-defense configuration. Denials return an error tool result with no tool response data. Warnings return JSON-RPC error -32001 with a session ID; the dashboard can review it from the activity feed. After approval, retrieve /api/simulations/{session_id} for the completed outcome. This is a mock JSON-RPC endpoint, not a complete MCP Streamable HTTP implementation or upstream proxy.

For Python integration, Gateway(detector, executor=trusted_callable).run(tool, request) inspects both boundaries. The executor receives the tool name and arguments; the default allowlist is the four mock names. Gateway.transaction yields phase checkpoints and retains state during approval. Do not connect the deliberately vulnerable simulation executor to real systems.

## Data and provenance

The downloader fetches only inert JSON at MCPCorpus revision 295fe37cd972ea9aa1b48578b2d7bcc40a72ee12 and verifies its pinned SHA-256. The snapshot contains 13,875 unlabeled metadata records. Fourteen canonical repositories have parsed tools matching the supported mappings, producing **126 scenarios**: 42 legitimate interactions and 84 attacks. These are simulated adaptations, not historical malicious interactions or labels for the original servers.

The original scenarios remain in `data/generated/scenarios.json`. Generation also
creates the default `scenarios-v2.json`: **158 cases** (48 validation, 110 test),
adding 32 checksum-frozen authored regressions with legitimate coverage for all
four tools. Authored cases are marked separately; they are development controls,
not independently reviewed unseen attacks. See the [problem/solution log](docs/PROBLEM_SOLUTION_LOG.md)
and [proposal alignment](docs/PROPOSAL_ALIGNMENT.md).

Raw downloads (data/raw), generated scenarios (data/generated), and reports (results) remain separate and ignored by Git. [data/provenance.json](data/provenance.json) records the immutable source, hash and licensing caveat. Run the commands above to regenerate. The pinned source has no repository-level license file; confirm redistribution terms before sharing raw or derived metadata. No upstream Python scripts are imported or executed.

References: [Lin et al., arXiv:2506.23474](https://arxiv.org/abs/2506.23474), [Snakinya/MCPCorpus](https://github.com/Snakinya/MCPCorpus). Metadata alone is never automatically labeled benign.

## Docker

~~~sh
docker compose up --build
~~~

Open http://127.0.0.1:8000. The multi-stage build compiles React and downloads the checksum-pinned metadata. Runtime uses a nonroot user, drops Linux capabilities, and binds to loopback on the host. Docker Desktop's Linux engine must be running. Build-time npm, PyPI and GitHub access is required. Results and pending approvals are ephemeral across container replacement. Configure a Docker volume if you need persistent reports.

Set MCPSHIELD_API_TOKEN to require bearer authorization on API data and mutations; enter it in the dashboard connection settings. The token is tab-session-only. Cross-origin requests are rejected. This is a single-process local research console; run one Uvicorn worker. Multi-user identity, durable approvals, real MCP transports, independent label review, real-model agent studies, and deployment hardening remain outside the validated prototype.

See [PROJECT_STATUS.md](PROJECT_STATUS.md) for verification and handoff. Preserve the pre-existing nested MCPShield/.git repository.
