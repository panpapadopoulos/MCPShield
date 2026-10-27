# MCPShield - current project status

Updated: October 26, 2026. Teammates should start with
[TEAM_HANDOFF.md](docs/TEAM_HANDOFF.md). Historical status text is preserved in
[the archived handoff](docs/history/PROJECT_STATUS_BEFORE_TEAM_HANDOFF.md).
This file supersedes old statements that LLM experiments, browser QA or Docker
verification have not run.

## Current implementation

Runnable local research prototype: React dashboard -> FastAPI -> resumable
request/response gateway -> four in-memory tools and a deterministic vulnerable
agent. Four configurations remain no defense, rules, real local LLM and hybrid.
All dangerous effects are simulated; this is not a production upstream MCP proxy.

Implemented and checked:

- Request and response inspection, fail-closed errors, explicit phase-specific
  one-time approvals, replay/expiry protection, retained responses without tool replay.
- Explicit tool/path/permission policy plus content rules. Hybrid cannot downgrade
  mandatory access violations, clear rule blocks or extra-permission approval.
  It may resolve only weak heuristic-context warnings.
- Local Qwen 2.5 3B via Ollama 0.40.11, prompt security-classifier-v2.2,
  policy fixture-policy-v2, temperature 0, max output 256, schema-constrained JSON.
  The classifier is pretrained; no model weights were trained.
- Source-backed corpus adaptations and separately labeled authored coverage cases;
  immutable corpus checksum, authored manifest, split/group checks and policy freeze.
- Four-method experiment runner with actual model calls, raw outcomes, hashes,
  confusion matrices, proposed metrics, approval frequency and latency.
- Live activity, approvals, dataset explorer, charts, JSON export and provenance UI.
- Locked dependencies, CI definition, native launch commands, base Docker package
  and optional fully local model overlay. CI definition is not proof of a remote run.
- Comparison utility verifies unchanged original case labels and baseline effects,
  and reports old cases separately from added coverage.

## Dataset counts

| Version / source | Validation | Test / regression | Total |
| --- | ---: | ---: | ---: |
| Original corpus adaptations | 36 | 90 | 126 |
| Added authored fixtures | 12 | 20 | 32 |
| Current combined v2 | 48 | 110 | 158 |

The original test has 30 legitimate and 60 malicious cases. The expanded test
has 42 legitimate and 68 malicious cases. The 126 original cases repeat nine
scenario templates over 14 repository sources; they are not 126 independent
real-world attack records. Validation calibrated prompts/policy, not model weights.
The inspected test and authored additions are development regressions. Independent
label review and unseen attack-family evaluation remain open.

## Measured results

Final expanded test: one repetition, all four methods RUN, no operational errors.

| Method | Attack success | Legitimate success | False positives | Mean latency |
| --- | ---: | ---: | ---: | ---: |
| No defense | 100% | 100% | 0% | 0.146 ms |
| Rules | 0% | 97.62% | 2.38% | 0.151 ms |
| LLM | 1.47% | 95.24% | 4.76% | 7.166 s |
| Hybrid | 0% | 95.24% | 4.76% | 4.714 s |

On identical original 90 cases, rules legitimate success improved from 66.67%
to 100%; LLM/hybrid improved from 0% to 93.33%. Source IDs, labels and all
unprotected baseline effects were verified unchanged. The validation run had
48 cases; both model-backed methods completed all 20 legitimate cases and
prevented all 28 attacks. Validation performance is not test performance.

See [measured results](docs/POLICY_V2_RESULTS.md) and
[problem/solution history](docs/PROBLEM_SOLUTION_LOG.md). Rules outperform hybrid
on combined-suite utility and latency; no general hybrid-superiority claim is made.

## Verification and recent handoff correction

- Policy-v2 verification: 54 tests passed on Windows and in Linux Docker; Vite
  build, live assets, fresh desktop/mobile flows, real-model API/MCP/browser and
  namespace-local Docker model probes passed.
- Handoff refresh: **55 native tests passed**, including a new reporter regression.
  The reporter reused a prompt filename tag as the Ollama runtime-version value.
  Future exports now retain the actual runtime version. Detector code, labels,
  predictions, timing values and historical reports were not changed by this fix.
- Some older v2 reports have local_runtime.ollama = "v2-2"; that is the known
  reporting defect, not an Ollama release. Recorded native v1 evidence and the
  pinned Docker image establish Ollama 0.40.11. Preserve the original reports and
  cite this correction instead of silently editing their metadata.
- The detector freeze remains in data/policy-v2-freeze.json. It fingerprints
  shield/*.py and classifier settings; full source snapshots also cover scripts.

## Remaining work

1. Investigate the two model false blocks using new validation examples. Do not
   tune the completed regression test until perfect and call it independent.
2. Retain the standalone LLM encoded-private-path miss as a regression. Hybrid
   policy already prevents it. Keep LLM-only distinct from hybrid.
3. Independently review labels, audit metadata encoding/forks, and freeze a new
   attack-family-disjoint evaluation before making generalization claims.
4. Run repeated trials with fresh output names, hardware/runtime details and
   uncertainty estimates. Current model results are single-pass.
5. Evaluate latency improvements and model alternatives on validation data.
6. Real-model agents, complete MCP transport, durable storage, multi-user identity
   and multi-worker coordination are separate extensions beyond this prototype.

Detailed workstreams and completion criteria are in the team handoff. No teammate
ownership has been assigned in this documentation.

## Repository and artifact handoff

The pre-continuation commit was 62aec72. The user authorized committing and
pushing the complete continuation and handoff. This status is included in that
publication commit; use git log -1 for its revision. Source, fixtures, evaluation
scripts and current documentation are included; ignored runtime/evidence files
remain separately transferable artifacts.

Raw corpus, generated scenarios, results, dependencies and model files are ignored
by Git. Rebuild datasets from the source instructions; transfer raw experiment
artifacts separately when teammates need the historical comparisons.

Checkpoints outside the repository, relative to its root:

- ../checkpoints/2026-10-26-before-local-llm/: original presentation source/evidence.
- ../checkpoints/2026-10-26-local-llm/: v1 real-model run and source.
- ../checkpoints/2026-10-26-policy-v2/: frozen classifier and completed regressions.
- ../checkpoints/2026-10-26-team-handoff/: refreshed docs and reporter metadata fix.

Start with [team handoff](docs/TEAM_HANDOFF.md), [setup](README.md),
[local model commands](docs/LOCAL_LLM.md), and [presentation notes](docs/PRESENTATION.md).
