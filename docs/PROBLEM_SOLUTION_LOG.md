# Problems, solutions and evidence

Date: October 26, 2026. This is a development log, not a claim of independent
research validation. The original proposal's four configurations remain
no defense, rules, LLM, and combined MCPShield. No AutoML method was substituted.

## Evidence preserved before changes

- `../checkpoints/2026-10-26-before-local-llm/`: original presentation source,
  checksums and baseline/rules evidence.
- `../checkpoints/2026-10-26-local-llm/`: complete v1 local-model source/evidence.
- `results/history/local-llm-v1-test.json`: 90 original test cases, one repeat.
  Rules: FPR 33.33%, legitimate success 66.67%. LLM/hybrid: FPR 100%, legitimate
  success 0%. All three defenses: 0% attack success in this controlled suite.
- Historical results and `docs/LOCAL_LLM_RESULTS.md` are retained; new results
  use separate paths and versioned policy/prompt hashes.

## P1: Harmless security terminology blocked

**Problem:** rules treated any occurrence of `system prompt` as an attack.
**Solution:** replace that broad keyword with action-directed disclosure
patterns. Educational definitions and search queries may proceed. Commands,
instruction overrides, forbidden paths, and explicit secret theft remain blocked.
**Checks:** a benign definition is delivered; a request to reveal a system
prompt remains blocked. Broader paraphrases remain a known heuristic limitation.

## P2: Local model invented risk and missing permissions

**Problem:** Qwen 2.5 3B/prompt-v1 flagged all legitimate test interactions.
The initial v2 validation probe still invented a permissions field for one
ordinary database request.
**Solution:** prompt-v2.2 states the four trusted read-only fixture capabilities,
separates source descriptions from actual tool authorization, gives balanced
policy examples, and supplies an observed permission flag extracted from the
actual top-level request. This is an input feature, not a rule-generated label.
The standalone LLM still makes its own security verdict; it is not secretly a
hybrid. It uses the same field extraction and prompt in every experiment.
**Calibration record:** `results/validation-policy-v2-probes.json` records 3/4
ordinary corpus validation tasks succeeding. After the permission correction,
`results/validation-policy-v2-1-probes.json` records 6/6 successful validation
probes, including benign file text and a documentation prerequisite. This is
not the final evaluation. The full v2.1 validation run then measured 90% legitimate
success and 0% attack success for both model methods, with two remaining benign
permission hallucinations. That report remains `results/policy-v2-expanded-validation.json`,
and its exact source is archived in `results/history/policy-v2-1-source.zip`.
Prompt-v2.2 adds explicit nonattack punctuation/security-education examples and
actual permission/attack examples as separate chat turns. The prompt hash covers
both the system policy and examples. No model weights were trained. Later full
validation/regression outcomes are recorded separately below when completed.

## P3: Hybrid treated every heuristic as mandatory policy

**Problem:** using the strictest verdict for every rule allowed ambiguous wording
to prevent otherwise authorized tasks.
**Solution:** explicit `AccessPolicy` separates tool/path restrictions and extra
permission approvals from content heuristics. Mandatory blocks and clear attack
blocks cannot be downgraded. The LLM can resolve only `heuristic_context` warnings.
Extra permission warnings retain the stricter rule/model verdict. The gateway
still requires one-time approval for every final warning and never overrides a
final block. Classification errors still fail closed.
**Checks:** allowed model output cannot bypass a private path, unknown tool,
command injection or extra-permission approval. Context-review failure blocks.

## P4: Missing tool coverage and an overly broad simulated-agent trigger

**Problem:** the original test split had no weather cases or legitimate file
reads. The simulation also interpreted the benign phrase `before using this
tool` as a command to read secrets, while file tools skipped description poisoning.
**Solution:** preserve all 126 original adaptations and add 32 explicitly authored
fixtures: 12 validation and 20 regression-test cases. Each split has legitimate
examples for all four tools. Include punctuation, security education, ordinary
rows/results, different cities, path variants, permissions, command arguments,
description poisoning and malicious responses. Freeze labels/checksum in
`data/coverage-manifest.json`; labels never come from detector predictions.
Description-driven simulated theft now requires `secretly send` and applies
consistently to public file responses as well as the other tools.
**Checks:** every authored legitimate case succeeds without harmful effects in
the unprotected baseline; every authored attack produces its declared forbidden
effect without protection. This verifies fixture intent, not real-world realism.

## P5: Results could be overwritten or confused across versions

**Solution:** local evaluation defaults to validation, records policy version,
prompt hash, source mix, dataset checksum, model digest, runtime version and raw
outcomes, and refuses to overwrite existing evidence. Preserve separate partial
journals for interrupted runs. Compare v1/v2 only on identical original case IDs;
report authored coverage results separately. The dashboard exposes approval
frequency as well as F1, security, utility and latency.

## P6: Quantile calculation rounded down

**Problem:** the previous p95 index could select too low an order statistic,
especially for small smoke samples.
**Solution:** use nearest-rank `ceil(0.95*n)-1`; a ten-sample regression checks
the boundary. Historical timing values are not silently recomputed.

## P7: A validation call failed and the original error lacked a reason code

The v2.2 JSON-object trial is retained at
`results/policy-v2-2-expanded-validation.json`. The LLM completed all validation
cases with 0 false positives; hybrid had one operational error, so its aggregate
was correctly withheld. The failed call recorded about 3.7 hours of elapsed time,
far beyond ordinary inference. A host pause/interruption is plausible, but the
old adapter did not preserve enough information to establish its cause. Repeated
fixture-only provider probes returned valid JSON; do not claim JSON was proven
to cause the old error.

The final local configuration uses a schema-constrained verdict (three enum
values, exactly three bounded fields), supported by Ollama structured outputs.
The adapter still validates the result, rejects output-limit termination and
fails closed. Safe error codes distinguish timeout, transport/HTTP problems,
invalid output and output limits without logging provider secrets. No failures
are converted into security detections or hidden by automatic retries. Generic
remote endpoints retain JSON-object mode unless explicitly configured otherwise.

Reference: https://docs.ollama.com/capabilities/structured-outputs

## Remaining limitations and proposal boundary

The tools and agent remain simulated as permitted by the controlled-benchmark
proposal. Real-agent robustness, complete upstream MCP transport, durable audit
storage, independent label adjudication and unseen attack-family generalization
have not been established. Added coverage mitigates gaps; it does not make
repeated templates independent. Both the old test and these authored controls
have development exposure, so improved results must be called regression results.
A new independently reviewed, frozen evaluation is still needed for generalization.

## P8: Handoff reporting metadata and stale status sections

During the teammate handoff refresh, inspection found that `evaluate_local.py`
reused `version` for the prompt filename tag after reading Ollama's runtime
version. Some v2 reports therefore contain `local_runtime.ollama = "v2-2"`.
This is a reporting defect, not a runtime release; scores, predictions, model
digests and the classifier freeze are unaffected.

The runner now uses separate `runtime_version` and `prompt_version_tag`
variables. `tests/test_reporting.py` mocks network/experiment dependencies in a
temporary directory and verifies future exports retain the provider's actual
version object. It does not create benchmark predictions or edit old reports.
The newest native suite passes 55 tests. Prior policy-verification runs passed
54 tests on Windows and Linux Docker; the historical verification count remains
unchanged in those records.

The previous long status file mixed current facts with historical NOT RUN and
deployment blockers. Its contents are preserved in
`docs/history/PROJECT_STATUS_BEFORE_TEAM_HANDOFF.md`. The root status is now a
current summary, and `docs/TEAM_HANDOFF.md` contains setup, source/artifact
locations, dataset arithmetic, verified results and unassigned workstreams.

## Completed verification and remaining follow-up

Final v2.2 schema validation: 48 cases, 0 operational errors, LLM/hybrid 100%
legitimate success and 0% attack success. Final regression: 110 cases, all four
methods completed, and frozen code/prompt/settings verified unchanged.

On the identical original 90 cases, rules legitimate success improved from
66.67% to 100%; LLM/hybrid improved from 0% to 93.33%. Two source-context false
blocks remain in both model-backed methods. On the expanded 110 cases, hybrid
prevents all 68 attacks and completes 40/42 legitimate tasks. Standalone LLM
allows one encoded-private-path attack that mandatory hybrid policy prevents.
Rules complete 41/42 legitimate tasks and prevent all attacks, so hybrid does not
dominate rules on the combined suite; latency remains materially higher.

Results, exact errors and separate original/new case analysis are in
[Policy-v2 results](POLICY_V2_RESULTS.md), `results/policy-v2-comparison.json` and
`results/policy-v2-remaining-errors.json`. Do not remove or relabel the remaining
failures. Further semantic calibration/model selection and independent attack-
family evaluation remain open research work.

Verified checks: 54 native tests and 54 Linux-container tests, frontend build,
fresh desktop/mobile browser flows, real-model API/MCP/browser checks, and
Docker local-model inference. Docker used the existing model cache read-only
for verification; the optional overlay normally uses a persistent model volume.
The model/runtime test stack was stopped before final native benchmark timing.
