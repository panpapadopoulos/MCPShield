"""Compare identical historical cases separately from added coverage controls."""
import argparse
import json
from pathlib import Path
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from shield.experiments import METHODS, metrics


def compare(before, after):
    for report in (before, after):
        if any(report['methods'][name]['status'] != 'RUN' for name in METHODS):
            raise ValueError('Comparison requires all four methods to complete without operational errors')
    original = {r['id']: r for r in before['methods']['no_defense']['records']}
    baseline = after['methods']['no_defense']['records']
    current_ids = {r['id'] for r in baseline}
    if not original.keys() <= current_ids:
        raise ValueError('Original case IDs are missing; not a paired development comparison')
    for row in baseline:
        if row['id'] in original:
            for key in ('malicious', 'executed', 'delivered', 'effects', 'task_success', 'attack_success'):
                if row[key] != original[row['id']][key]:
                    raise ValueError(f'Baseline changed for {row["id"]}: {key}')
    paired = {(r['id'], r['repeat']): r['latency_ms'] for r in baseline}
    result = {
        'scope': 'Development regression; original test previously inspected; added fixtures author-reviewed only',
        'original_unique_cases': len(original),
        'added_unique_cases': len(current_ids - original.keys()),
        'before_code_sha256': before['code_sha256'], 'after_code_sha256': after['code_sha256'],
        'before_prompt_version': before['prompt_version'], 'after_prompt_version': after['prompt_version'],
        'baseline_outcomes_unchanged': True, 'methods': {},
    }
    for name in METHODS:
        method = after['methods'][name]
        if len(method['records']) != len(paired) or {(r['id'], r['repeat']) for r in method['records']} != paired.keys():
            raise ValueError(f'Method {name} used a different case/repetition set')
        sections = {}
        for section, is_original in (('original_after', True), ('added_coverage', False)):
            rows = [r for r in method['records'] if (r['id'] in original) == is_original]
            if not rows:
                sections[section] = None
                continue
            for row in rows:
                if is_original and row['malicious'] != original[row['id']]['malicious']:
                    raise ValueError('Historical labels changed')
            scores = metrics(rows)
            scores['additional_latency_ms'] = statistics.mean(r['latency_ms'] - paired[(r['id'], r['repeat'])] for r in rows)
            sections[section] = {'observations': len(rows), **scores}
        result['methods'][name] = {
            'original_before': {k: v for k, v in before['methods'][name].items() if k != 'records'},
            **sections,
        }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path('results/policy-v2-comparison.json'))
    args = parser.parse_args()
    result = compare(json.loads(args.before.read_text(encoding='utf-8')), json.loads(args.after.read_text(encoding='utf-8')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(result, output, indent=2)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
