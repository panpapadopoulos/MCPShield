# Alignment with the MCPShield proposal

The fixes refine the proposed system; they do not replace its research question
or any of its four configurations.

| Proposal commitment | Implementation and verification |
| --- | --- |
| Inspect requests before execution and responses before model delivery | Resumable gateway; both phases retained; denied payloads are not delivered |
| No-defense baseline | Same deterministic vulnerable agent and fixtures, without classification |
| Rule-based defense | Explicit access policy, command/instruction indicators and contextual warnings |
| LLM-based defense | Real local pretrained Qwen classifier, strict JSON validation; no hidden rules verdict substituted |
| Combined MCPShield | Mandatory rule restrictions plus LLM review; only weak heuristic warnings can be resolved |
| Same scenarios for all four methods | Identical IDs/checksum per report; raw outcomes retained |
| Controlled normal/malicious dataset and four simulated tools | Original adaptations preserved plus separately identified authored four-tool coverage controls |
| Safe/malicious labels and expected decisions | Authored intent/effects, frozen manifests, no labels inferred from predictions |
| Precision, recall, F1, FPR, detection, legitimate success and added latency | Existing metrics retained; attack success and approval frequency provide additional context |
| Allowed / approval / blocked dashboard | Same three final states and one-time phase-specific approval; model and source provenance visible |
| Reproducible local Docker deployment | Pinned corpus/dependencies, versioned source/data, build and runtime verification |
| GitHub repository and documentation | Repository-local implementation, problem/solution log and reproducible commands; this turn does not publish or push |

The proposal does not require a hosted paid LLM, model training, AutoML, or a
production upstream proxy. A local pretrained LLM fulfills its classifier method.
Pure LLM and hybrid remain distinct experimental configurations. Rule and prompt
changes are calibrated on validation examples; already inspected test cases are
used only for disclosed development regression comparisons.

Mandatory policy cannot be weakened by the model. Every final WARNING still
requires explicit approval, every final BLOCKED verdict stops, and classifier
errors deny execution. Simulations never touch real private files or execute
untrusted commands.

Proposal completion does not itself establish the desired research outcome.
Any claim that hybrid improves security without excessive interference must be
supported by measured security/utility/latency results. Independent label review
and new held-out attacks remain research limitations, not completed fixes.
