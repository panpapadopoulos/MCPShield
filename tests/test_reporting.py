"""Keep provider runtime provenance separate from prompt filename tags."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from scripts import evaluate_local


class ReportingTests(unittest.TestCase):
    def test_runtime_version_is_not_replaced_by_prompt_tag(self):
        model = SimpleNamespace(base='http://127.0.0.1:11434/v1', model='fixture-model', output_format='json_schema')
        responses = [io.BytesIO(json.dumps({'models': [{'name': 'fixture-model', 'digest': 'fixture-digest'}]}).encode()),
                     io.BytesIO(b'{"version":"0.40.11"}')]
        report = {'methods': {name: {'status': 'RUN'} for name in ('no_defense', 'rules', 'llm', 'hybrid')}}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'report.json'
            with patch.object(sys, 'argv', ['evaluate_local.py', '--output', str(output)]), \
                 patch.object(evaluate_local, 'LLM', return_value=model), \
                 patch.object(evaluate_local, 'urlopen', side_effect=responses), \
                 patch.object(evaluate_local, 'load_cases', return_value=[{'id': 'fixture', 'split': 'validation'}]), \
                 patch.object(evaluate_local, 'run_experiment', return_value=report), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(evaluate_local.main(), 0)
            saved = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(saved['local_runtime']['ollama'], {'version': '0.40.11'})
            self.assertEqual(saved['local_runtime']['model']['digest'], 'fixture-digest')


if __name__ == '__main__':
    unittest.main()
