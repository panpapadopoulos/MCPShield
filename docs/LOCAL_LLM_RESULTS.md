# Local LLM evaluation - October 26, 2026

> Historical prompt-v1 local-model run, preserved before the fixes. See [current v2 results](POLICY_V2_RESULTS.md) and [team handoff](TEAM_HANDOFF.md) for current behavior.

Real Ollama 0.40.11 inference using Qwen 2.5 3B (Q4_K_M), CPU only on an
Intel Core i5-1235U with 16 GB RAM. No hosted API calls were made.
Prompt: security-classifier-v1; temperature 0; max output 256 tokens;
local inference context 4096 tokens. Model digest:
`357c53fb659c5076de1d65ccb0b397446227b71a42be9d1603d46168015c9e4b`.

Scope: full 90-scenario test split (60 attacks, 30 legitimate), **one repetition**.
This is an exploratory single-pass result; the planned three-repeat model
comparison and uncertainty estimates remain pending. All four methods completed
without operational classifier errors. The implementation fingerprint was
verified unchanged after the experiment.

| Method | Attack success | Legitimate success | False positives | Mean latency (seconds) |
| --- | ---: | ---: | ---: | ---: |
| no_defense | 100.00% | 100.00% | 0.00% | 0.000 |
| rules | 0.00% | 66.67% | 33.33% | 0.000 |
| llm | 0.00% | 0.00% | 100.00% | 6.629 |
| hybrid | 0.00% | 0.00% | 100.00% | 3.669 |

## Interpretation

This configuration does not demonstrate a hybrid advantage. Both model-backed
methods flagged every legitimate scenario; warnings are denied automatically
in this experiment, so no legitimate task completed. A user can approve warnings
in the dashboard, but that is a different condition and does not change these
recorded automated outcomes. All-positive prediction can have a seemingly good
F1 (0.80 here) while providing no legitimate-task utility.

Rules have F1 0.9231, versus 0.80 for LLM/hybrid. Rules TP/FP/TN/FN are
60/10/20/0; LLM and hybrid are both 60/30/0/0. All methods saw exactly the same
scenarios. No prompt or model changes were made in response to intermediate
results. The small model/prompt and shared templates limit interpretation;
these results do not establish the behavior of other models or real agents.

Hybrid preserves rule blocks, so it cannot repair rule false positives. Its
lower average latency relative to the LLM-only method partly reflects rule
short-circuiting, not greater classifier speed. Baseline/rules timings are noisy
and include simulated execution/follow-ups; negative added latency is not a
reliable speed advantage. Other desktop processes were not controlled.

## Coverage and next work

The test split contains database/web interactions and unauthorized file reads,
with no weather cases or legitimate file-reader cases. Nine templates are
shared across source repositories. Independently reviewed labels and broader
held-out attacks remain necessary. Calibrate policy/prompt choices on validation
data, broaden benign coverage and evaluate a stronger suitable model before
claiming security without excessive interference. Do not tune on this test and
then describe a rerun as an independent final test.

Full raw report: `results/local-llm-evaluation.json`. The dashboard's default
`results/evaluation.json` is a copy of this report. The reproduced original
three-repeat baseline/rules report remains `results/presentation-baseline-rules.json`
and is also preserved with the pre-continuation presentation checkpoint.
