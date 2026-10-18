# MCPShield

Security research prototype for CS 52560, Purdue University Northwest. This first increment provides a Python standard-library-only security gateway and four deterministic in-memory mock tools. No real commands, private files, network tools, or untrusted servers are executed.

## Run

Python 3.9 or later, from the repository root:

~~~sh
python -m unittest discover -s tests -v
python -m shield.benchmark --output results/smoke.json
~~~

The report contains per-interaction request/response decisions, confusion matrices, precision, recall, F1, false-positive rate, attack detection/success rates, legitimate delivery success, and local latency. LLM and hybrid are explicitly NOT RUN; adapters and dashboard are pending. No credentials are required for this increment.

## Enforcement

Gateway checks requests before calling a mock tool and checks responses before delivery. ALLOWED proceeds; WARNING requires a trusted explicit callback returning True; BLOCKED always stops. Response denial retains execution status but suppresses the response. Approval is bound to the current tool, payload, phase, and verdict by a synchronous callback; no remote approval API exists yet. Rules are heuristics, not a complete security boundary for real MCP tools.

## Methodology and provenance

References: [MCPCorpus paper](https://arxiv.org/abs/2506.23474), [source repository](https://github.com/Snakinya/MCPCorpus). Reviewed 2026-10-18. MCPCorpus describes ecosystem metadata, not labeled malicious/benign interactions. No corpus records have been downloaded or labeled here.

The nine versioned scenarios in shield/benchmark.py are hand-authored smoke tests with IDs, provenance, mock server/tool, request/response, attack category, labels, expected decisions, and expected outcomes. They are not a research benchmark. All methods receive the same ordered cases and the report records their SHA-256. There is no training or train/test split. Before research evaluation, import immutable corpus records separately from generated scenarios; canonicalize server identities and group all related and near-duplicate scenarios within one split. Review labels independently and freeze a held-out suite.

The simulated agent consumes delivered data. File attacks measure delivery of a fixture secret and response attacks measure delivery of injected text. Other attacks currently measure unsafe request reachability, not actual command execution or real agent compromise. Legitimate success currently measures delivery, not semantic task completion. Single-pass latency is noisy; repeated paired experiments and uncertainty estimates remain pending. Smoke-suite scores cannot support general security claims.

See PROJECT_STATUS.md for verified progress and next steps. Preserve the pre-existing nested MCPShield/.git repository. Implementation publication was subsequently authorized by the user.
