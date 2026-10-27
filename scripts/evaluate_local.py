"""Run real local-model experiments with provenance and visible progress."""
import argparse
import json
from pathlib import Path
import sys
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shield.dataset import load_cases
from shield.detectors import LLM, PROMPT_VERSION
from shield.experiments import run_experiment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--smoke', action='store_true', help='One scenario per template in the selected split; not a full benchmark')
    parser.add_argument('--split', choices=['validation', 'test'], default='validation')
    parser.add_argument('--suite', choices=['original', 'expanded'], default='expanded')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    model = LLM()
    if model.base != 'http://127.0.0.1:11434/v1':
        parser.error('This runner requires the project local Ollama endpoint')
    with urlopen('http://127.0.0.1:11434/api/tags', timeout=5) as response:
        models = json.load(response)['models']
    installed = next((m for m in models if m['name'] == model.model), None)
    if installed is None:
        parser.error('Configured model is not installed in local Ollama')
    with urlopen('http://127.0.0.1:11434/api/version', timeout=5) as response:
        runtime_version = json.load(response)
    path = Path('data/generated/scenarios.json') if args.suite == 'original' else None
    cases = [c for c in load_cases(path) if c['split'] == args.split]
    if args.smoke:
        unique = {}
        for case in cases:
            unique.setdefault(case['template'], case)
        cases = list(unique.values())
    prompt_version_tag = PROMPT_VERSION.removeprefix('security-classifier-').replace('.', '-')
    output = args.output or Path(f'results/policy-{prompt_version_tag}-{model.output_format.replace("_", "-")}-{args.suite}-{args.split}' + ('-smoke' if args.smoke else '') + '.json')
    if output.exists() or output.with_suffix('.partial.jsonl').exists():
        parser.error(f'Refusing to overwrite prior evidence at {output}; choose a new --output')
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep incremental observations separate: an interrupted run is not a valid aggregate.
    partial = output.with_suffix('.partial.jsonl')
    with partial.open('w', encoding='utf-8') as journal:
        def progress(method, identifier, repeat, outcome, error):
            row = {'method': method, 'id': identifier, 'repeat': repeat,
                   'operational_error': error, 'outcome': outcome}
            journal.write(json.dumps(row) + '\n')
            journal.flush()
            print(f'{method} repeat={repeat + 1} {identifier} error={error}', flush=True)
        report = run_experiment(cases, args.repeats, include_llm=True, progress=progress)
    report['local_runtime'] = {'ollama': runtime_version, 'model': installed}
    report['evaluation_scope'] = f'{args.suite} {args.split}; development evaluation, not an independent unseen-attack study'
    report['smoke_only'] = args.smoke
    temporary = output.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2), encoding='utf-8')
    temporary.replace(output)
    print(json.dumps({name: {k: v for k, v in result.items() if k != 'records'}
                      for name, result in report['methods'].items()}, indent=2))
    print(f'Saved {output}', flush=True)
    return 0 if all(m['status'] == 'RUN' for m in report['methods'].values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
