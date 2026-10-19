# Experimental methodology

## Source and construction

The paper describes a metadata corpus collected by static inspection, not a ground-truth attack dataset. We download Website/mcpso_servers_cleaned.json at immutable revision 295fe37cd972ea9aa1b48578b2d7bcc40a72ee12; the downloader enforces SHA-256 cc14fc4fe5c68b73e77cbaa3e64fc2b58616a8e61d0e96d92b8fd861702b9e20. Original bytes, local manifest, generated interactions, and results have separate paths.

Selection sorts canonical repository identities and source IDs, parses tool arrays (including JSON-encoded strings), chooses the first supported tool per repository, and maps descriptions/names to one of four in-memory executors. Up to 40 repositories are requested; the pinned data currently yields only 14 valid matching repositories. This selection is not representative of the full corpus. Actual names, descriptions, schemas, record IDs and repository references are preserved in scenario provenance. Mock schemas replace original schemas; configuration commands are never executed.

Each selected repository yields nine labeled interactions: three authorized legitimate tasks, file-access violation, command injection, excess permissions, poisoned tool description, injected result instructions, and malicious tool response. Labels derive from the authored intent and forbidden virtual effects, not the reputation of the source server. A quoted security-document control is deliberately legitimate even when a detector overblocks it. Expected decisions and execution outcomes are stored with every scenario. Labels are template-authored and await independent human review.

## Splits and leakage

Canonical GitHub owner/repository identity groups monorepo subpaths. Identical tool objects and near-duplicate descriptions (token Jaccard similarity at least 0.80, at least five tokens in each) are unioned across selected repositories. Whole components are assigned validation (hash bucket 0 of 5) or test (other buckets). A validator rejects duplicate IDs and any server/group crossing splits. Generation uses no random state or timestamps.

Current split: 36 validation and 90 test interactions. No classifier is trained or tuned here. Shared attack templates across repositories remain a confound; these are server-disjoint splits, not an independent held-out attack-family test. The response-injection wording differs by split but is still a related attack. Train/test leakage claims beyond the implemented identity/description checks would be unjustified. Before training, group source forks/mirrors manually, audit semantic duplicates, isolate attack families, freeze labels and record review provenance.

## Enforcement and agent

All four configurations use the same ordered cases and fixture tools. Baseline bypasses filtering. Rules inspect paths, injection indicators, command syntax, tool allowlists and extra permissions. LLM uses only real configured classification and strict structured response validation. Hybrid short-circuits rule blocks and otherwise takes the stricter model/rule result. Request decisions precede execution; response decisions precede agent consumption. Warnings are denied in experiments; approval experiments should be a separate condition.

The vulnerable deterministic agent can follow next_action or recognized natural-language instructions into another gateway-mediated call. The sandbox records command_executed, privilege_granted, private_file_read and secret_disclosed without touching real resources. Scenario attack success is the intersection of independently recorded effects and the scenario's forbidden effects. A command effect occurring before a blocked response still counts as attack success. Legitimate success requires delivery and exact expected fixture data. This makes outcomes more informative than classification alone but does not model real LLM cognition or arbitrary attack semantics.

The API stores suspended generators under random session IDs. Each warning has an independent one-time approval nonce and five-minute session expiry. Responses are retained across approval, so tools are not rerun. Blocks are never approval candidates. Sessions and activity are in memory, single process. The JSON-RPC mock subset uses the configured server-side defense; clients cannot turn off enforcement.

## Metrics and timing

Positive = malicious scenario; predicted positive = at least one non-ALLOWED security decision across initial/follow-up boundaries. Warnings count as detections. Operational detector errors are distinct from security detections; any error invalidates that method's aggregate scores. Precision TP/(TP+FP); recall and attack detection TP/(TP+FN); F1 2TP/(2TP+FP+FN); false-positive rate FP/(FP+TN). Zero denominators yield null.

Attack success = malicious scenarios with a forbidden observed effect / malicious scenarios. Legitimate success = correct delivered fixture responses / legitimate scenarios. Confusion matrices count every repetition and report the repetition count; repeated instances are not independent examples. The baseline may successfully attack without detecting anything.

Three default repetitions rotate method execution order deterministically. End-to-end timing includes inspections, mock execution and agent follow-ups; added latency is paired by scenario ID/repetition against baseline. It can be negative because filtering avoids vulnerable follow-up work and because microsecond timings are noisy. It is not a pure classifier overhead measurement. Reports include mean and p95; no statistical confidence claim is made. More trials, warmup policy and real workloads are needed for latency conclusions.

## Reproduction and limitations

See README for setup, generation and execution commands. Raw checksums and scenario checksums permit reproduction; model outputs and wall-clock latency need not be deterministic. Model name and prompt version are recorded, but external provider drift remains possible. Fake classifier responses are used only in unit tests. No LLM credentials/model were available for the recorded experiment, so both LLM configurations are NOT RUN.

Known limitations include small selected source sample, shared templates, no independent label adjudication, simplified string-based agent, heuristic false positives/obfuscation gaps, no complete MCP transport, no durable approval audit, no real multi-user authorization and no browser-based visual verification in the implementation environment. These limits should accompany any academic result.

Sources: [paper](https://arxiv.org/html/2506.23474v1), [corpus](https://github.com/Snakinya/MCPCorpus), [official OpenAI Chat API](https://developers.openai.com/api/reference/resources/chat).

Source quality note: one matching record pointed to a GitHub profile rather than a repository and is excluded. Several source descriptions contain upstream character-encoding artifacts; original text is preserved rather than silently repaired. These limit semantic duplicate checks and label interpretation.
