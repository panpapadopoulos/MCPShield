# Policy-v2 fixes and measured results

The proposal's four configurations remain unchanged. Historical failures are
preserved; see [problem/solution log](PROBLEM_SOLUTION_LOG.md) and
[proposal alignment](PROPOSAL_ALIGNMENT.md).

## Final frozen configuration

Qwen 2.5 3B through local Ollama 0.40.11, CPU inference. Policy fixture-policy-v2,
prompt security-classifier-v2.2, schema-constrained JSON, temperature 0 and
256 output tokens. Full prompt/schema/model/code fingerprints are recorded in
`data/policy-v2-freeze.json` and every new report. No model weights were trained.

## Validation before regression evaluation

48 cases: 20 legitimate and 28 malicious; one repetition, all four methods
completed without operational classifier errors. This is calibration evidence.

| Method | Legitimate success | False positives | Attack success | Mean latency (s) |
| --- | ---: | ---: | ---: | ---: |
| no_defense | 100.00% | 0.00% | 100.00% | 0.000 |
| rules | 95.00% | 5.00% | 0.00% | 0.000 |
| llm | 100.00% | 0.00% | 0.00% | 5.951 |
| hybrid | 100.00% | 0.00% | 0.00% | 4.056 |

Report: `results/policy-v2-2-json-schema-expanded-validation.json`.
The policy was frozen after validation and before running the test split.

## Regression evaluation

Completed **110 cases: 42 legitimate and 68 malicious**, one repetition, all
four methods RUN with no operational classifier errors. Code/prompt/generation
fingerprints match the pre-test freeze. No settings changed after observing test
outcomes. Warnings are denied automatically.

| Method | Legitimate success | False positives | Attack success | Mean latency (s) |
| --- | ---: | ---: | ---: | ---: |
| no_defense | 100.00% | 0.00% | 100.00% | 0.000 |
| rules | 97.62% | 2.38% | 0.00% | 0.000 |
| llm | 95.24% | 4.76% | 1.47% | 7.166 |
| hybrid | 95.24% | 4.76% | 0.00% | 4.714 |

| Method | Precision | Recall/detection | F1 |
| --- | ---: | ---: | ---: |
| no_defense | undefined | 0.00% | 0.00% |
| rules | 98.55% | 100.00% | 99.27% |
| llm | 97.10% | 98.53% | 97.81% |
| hybrid | 97.14% | 100.00% | 98.55% |

Full report: `results/policy-v2-2-json-schema-expanded-test.json`.
Added latency is paired against the same baseline case; p95 and approval
frequency are retained in the report and dashboard.

### Fair before/after: identical original 90 cases

Both runs contain the same 30 legitimate and 60 malicious original cases.
The comparison verifies case IDs, labels and unprotected baseline effects.

| Method | Legitimate success before | After | False positives before | After |
| --- | ---: | ---: | ---: | ---: |
| rules | 66.67% | 100.00% | 33.33% | 0.00% |
| llm | 0.00% | 93.33% | 100.00% | 6.67% |
| hybrid | 0.00% | 93.33% | 100.00% | 6.67% |

Attack success on the original cases remains 0% for all three defenses.
Baseline attack success remains 100%. Analysis: `results/policy-v2-comparison.json`.

### Added 20 coverage cases reported separately

These contain 12 legitimate tasks and eight attacks. Rules complete 11/12
legitimate tasks and prevent all attacks. LLM completes 12/12 legitimate tasks
but allows one encoded-private-path attack. Hybrid completes 12/12 legitimate
tasks and prevents all eight attacks. These cases are author-reviewed regressions,
not independently sampled or reviewed attacks.

### Remaining findings

- Two original web-search cases still confuse the small model about source
  metadata, producing false blocks in both model-backed methods. They are kept
  as visible failures, not removed or relabeled.
- The standalone LLM calls `/%70rivate/secret.txt` safe and discloses the virtual
  secret. Hybrid prevents it with the mandatory exact public-path restriction.
  Adding that rule secretly to LLM-only would invalidate the method comparison.
- Combined-suite rules have better legitimate success and far lower latency
  than hybrid. Hybrid prevents a failure of standalone LLM, but this experiment
  does not establish overall superiority over rules.
- Local inference still adds seconds. Hybrid short-circuiting reduces calls;
  this is not evidence that its underlying classifier runs faster.

Detailed remaining cases: `results/policy-v2-remaining-errors.json`. Changes
for these newly observed errors require another documented validation cycle and
a new frozen evaluation. This completed test is not silently tuned until perfect.

## Verification and limits

54 native and Linux-container tests passed, the dashboard builds, and the
Docker local-model connection passed weather/private-file/credential-theft
probes. Docker verification reused the native model cache read-only; the normal
overlay uses a persistent model volume. These checks establish runnable behavior,
not real-world classifier efficacy.

The original test was inspected during v1 development. New cases are author-
reviewed regressions, not independently reviewed unseen attacks. Shared templates,
a deterministic agent, CPU latency and lack of independent attack-family evaluation
remain limitations. Final warnings require approval; automated experiments deny
them. Repeat trials and statistical uncertainty estimates remain future work.

Latency is descriptive on this laptop: desktop workload and prefix caching were
not controlled, and this single pass does not provide uncertainty estimates.
Three-repeat runs with rotated method order remain a separate follow-up.

## Runtime metadata correction identified during handoff

The historical v2 report field `local_runtime.ollama` incorrectly contains the
prompt filename tag `v2-2`. The reporter's variable reuse is now fixed for future
runs and has a regression test. The verified runtime was Ollama 0.40.11, also
recorded in the older native v1 evidence and pinned Docker configuration. The
historical JSON files remain untouched; their predictions, scores, timing values
and model digests are unchanged. See P8 in the problem/solution log and the
[team handoff](TEAM_HANDOFF.md) for continuation instructions.
