# Recorded simulation results

Run timestamp (UTC): 2026-10-18T23:50:20.886958+00:00. Python 3.10.4.

Command: python -m shield.experiments --split test --repeats 3

The final validated dataset contains 126 scenarios from 14 canonical source repositories. One candidate with only a GitHub profile URL was excluded. Test: 90 scenarios (60 malicious, 30 legitimate); validation: 36. Three repetitions produce 270 observations per method; repetitions are not independent examples.

| Configuration | Precision | Recall | F1 | False-positive rate | Attack success | Legitimate success |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no_defense | undefined | 0.00% | 0.00% | 0.00% | 100.00% | 100.00% |
| rules | 85.71% | 100.00% | 92.31% | 33.33% | 0.00% | 66.67% |
| llm | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |
| hybrid | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN | NOT RUN |

LLM and hybrid were not run: no configured model/API key. Unit-test classifier fixtures are not experimental predictions.

| Configuration | TP | FP | TN | FN | Mean latency (ms) | Paired added latency (ms) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| no_defense | 0 | 0 | 90 | 180 | 0.058424 | 0.000000 |
| rules | 180 | 30 | 60 | 0 | 0.048959 | -0.009465 |

Rules detect all template attacks in this small suite but also block the benign security-document control. That control accounts for 30 false positives across repetitions. This is a measured limitation, not a claim of general efficacy.

Negative added latency can result from avoiding baseline follow-up work and noisy microsecond timing. Do not interpret this run as a reliable performance advantage. No confidence intervals or independent agent study were performed.

The dashboard shows comparison bars, confusion matrices, per-call outcomes and exportable raw JSON. Full report: ignored results/evaluation.json; regenerate using the command above.

Test scenario SHA-256: 68d548d3f65b674391d1f77c73d67b93b448b8a2c1804318c559c1ca4ca9a91e

Implementation SHA-256: 32bede019672008b65a57ec785c450e9c3dfb045a5b9bc2b28e3332e1fef952d

See [methodology](METHODOLOGY.md) for split construction, virtual effect oracles, shared-template leakage limitations and outstanding independent review.
