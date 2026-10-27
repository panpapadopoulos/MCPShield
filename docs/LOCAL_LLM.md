# Local LLM continuation

For team coordination, current task ownership/workstreams and artifact transfer,
start with [TEAM_HANDOFF.md](TEAM_HANDOFF.md). Older v2 runtime-version fields
have a documented reporting correction; use the handoff's provenance note when
reading those reports.

The original presentation checkpoint is outside this repository at
`../checkpoints/2026-10-26-before-local-llm/`. It contains the original source,
checksums and a statement of verified versus historical progress.

This continuation uses Ollama with `qwen2.5:3b` as a small local starting model.
Its effectiveness must be measured; installing a model does not establish safety.
No hosted API account or paid API key is required. The 3B model has its own Qwen
research license; see https://ollama.com/library/qwen2.5:3b.

## Windows

Install Ollama from https://ollama.com/download/windows or extract the official
Windows AMD64 release into `.local/ollama/` so it contains `ollama.exe`.
Install Python requirements and build the frontend as described in README.md.

From the repository root, use separate PowerShell terminals:

```powershell
# Terminal 1: keep the local model server running
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 serve

# Terminal 2: first-time model download, then a real classification check
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 pull
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 check
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 smoke

# Start the dashboard with the same local model settings
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 dashboard
```

Open http://127.0.0.1:8000 and select LLM or Hybrid. Rules remain the default.
The model files stay in `.local/models`, ignored by Git. The script sets process
environment variables and disables Ollama cloud features; it does not change
system environment settings. If another Ollama server already owns port 11434,
use that server or stop it explicitly before starting the project server.

## Versioned evaluation

Calibrate on validation, freeze the configuration, then perform a separately
labeled regression evaluation. All four proposed methods receive the same cases.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 evaluate -Split validation -Suite expanded -Repeats 1
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 evaluate -Split test -Suite expanded -Repeats 1
```

The reports are `results/policy-v2-2-json-schema-expanded-validation.json` and
`results/policy-v2-2-json-schema-expanded-test.json`. `-Suite original` selects the preserved
126-case corpus adaptations; expanded selects the 158-case combined suite.
Default evaluation uses validation, not test. Local scripts explicitly select json_schema output; generic remote endpoints retain json_object unless configured otherwise. Use three repetitions for repeated
trials, with a fresh output name:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/local_llm.ps1 evaluate -Split test -Repeats 3 -Output results/policy-v2-2-json-schema-expanded-test-r3.json
```

The runner refuses to overwrite any existing final report or partial journal.
It records prompt/policy versions, model digest, source mix and raw outcomes.
A `.partial.jsonl` file is an interrupted-run journal, not a completed aggregate.
The smoke action selects one example per template in the chosen split; it is
not a full benchmark. Native CPU experiments can take many minutes.

The original v1 evidence remains in `results/history` and in the separate source/
evidence checkpoint. Prompt-v1 severely overblocked legitimate cases. Current
fixes and measured verification are tracked in `PROBLEM_SOLUTION_LOG.md`.
These are development comparisons: the original test has already been inspected
and new authored fixtures are regressions, not independently reviewed attacks.

The dashboard's Run evaluation button always runs three repetitions and writes
`results/evaluation.json`; CLI runs use separate versioned files. Warnings are
denied in automated experiments; approvals are a separate interactive condition.

## Docker with a local model

An optional overlay runs Ollama in the application's network namespace. The
classifier still uses loopback HTTP; there is no relaxed remote HTTP exception,
and port 11434 is not published to the host.

```powershell
docker compose -f compose.yaml -f compose.local-llm.yaml up --build -d
docker compose -f compose.yaml -f compose.local-llm.yaml exec ollama ollama pull qwen2.5:3b
docker compose -f compose.yaml -f compose.local-llm.yaml exec mcpshield python scripts/check_llm.py
```

Pull the model before trying LLM/hybrid calls. Model files persist in a named
Docker volume. The normal dashboard is http://127.0.0.1:8000; stop a native
dashboard using that port first. Use `docker compose ... down` with the same
two files to stop these services. The base Compose file alone still runs the
application without starting a model service. Host-Ollama integration is separate;
`127.0.0.1` inside a container is not the Windows host.

## Fair before/after analysis

```powershell
.venv/Scripts/python.exe scripts/compare_versions.py --before results/history/local-llm-v1-test.json --after results/policy-v2-2-json-schema-expanded-test.json
```

This requires all four methods to have valid completed runs. It verifies that
original case IDs, labels and baseline effects match, and reports the original
90 cases separately from the 20 new regression-test cases. It refuses to overwrite
its comparison output. Never compare aggregate rates from different case mixes
as if only the detector had changed.
