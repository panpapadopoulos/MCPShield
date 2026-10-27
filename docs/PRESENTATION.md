# Presentation — October 27, 2026

## What we built

MCPShield is a local security research prototype that checks requests before
simulated tool execution and checks responses before delivery to a deterministic
agent. Allowed calls proceed, warnings pause for one-time approval, and blocks
cannot be overridden. The four tools have no external side effects.

## Historical v1 baseline result (preserved)

October 26 verification: 126 generated scenarios; the test split has 90 scenarios
(60 attacks and 30 legitimate interactions). Three repetitions give 270
observations, not 270 independent examples.

| Configuration | Attack success | Legitimate task success | False-positive rate |
| --- | ---: | ---: | ---: |
| No defense | 100% | 100% | 0% |
| Rules | 0% | 66.67% | 33.33% |

Rules precision: 85.71%; recall: 100%; F1: 92.31%.
Report: `results/presentation-baseline-rules.json`.
The checkpoint predates local LLM work; do not attribute later results to it.

## Demo sequence

1. Start the API and open http://127.0.0.1:8000.
2. Run a legitimate scenario under rules; inspect both allowed boundaries.
3. Run a private-file scenario; show execution was prevented.
4. Run an excessive-permissions scenario; deny it, then run another and approve
   it once. Explain that user approval can authorize the simulated privilege grant.
5. Run a response-injection scenario and inspect the response boundary.
6. Show the quoted-security-document scenario now being allowed; explain the v1 keyword-rule false positive and its recorded fix.
7. Show evaluation results and explain the security/utility tradeoff.

## Limits to state explicitly

- Nine shared templates across 14 source repositories; corpus metadata is
  provenance, not independent malicious examples or validated labels.
- The 90-case test split covers database/web calls and unauthorized file reads;
  it has no weather cases or legitimate file-reader cases. Four implemented
  tools does not imply balanced four-tool evaluation coverage.
- The agent is deterministic; no evidence yet about real LLM agent robustness.
- Rules scan all serialized text. Quoted security terminology causes false positives.
- Hybrid preserves every rule block, so it cannot repair those false positives.
- The model classifier itself can be attacked through its untrusted input.
- Local-model continuation replaces the inference-wide global lock with
  per-session locks so activity polling can continue during slow classification.
  This remains a single-user, single-process local console.
- The MCP endpoint is a JSON-RPC mock subset, not a full upstream MCP proxy.
- Approvals and activity are ephemeral. The continuation passed desktop/mobile
  browser checks and a Docker build/runtime check on October 26.

## Current fixes and next research milestone

The working version now uses the proposal-aligned policy/prompt fixes described
in [v2 results](POLICY_V2_RESULTS.md). All 20 legitimate validation cases completed
under LLM/hybrid, with 0% attack success across 28 malicious validation cases.
The final regression run completed on 110 cases: hybrid prevented all 68 attacks
and completed 40/42 legitimate tasks (95.24%). Rules completed 41/42 (97.62%)
and also prevented all attacks. Standalone LLM completed 40/42 but allowed one
encoded-private-path attack, which hybrid blocked. Show these measured tradeoffs.

On the identical original 90 cases, rules legitimate success improved from
66.67% to 100%; LLM/hybrid improved from 0% to 93.33%. Two model false blocks
remain, so do not claim perfect classification. Use the saved report during the
presentation; a fresh full local experiment takes many minutes.
The original v1 source/results remain in separate checkpoints.

Explain that validation is used for calibration, and that the existing test and
new authored cases are disclosed development regressions, not an independent
unseen-attack study. Local inference still adds seconds. Independent label review,
new held-out attack families and repeated model trials remain future work.
