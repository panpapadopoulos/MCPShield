"""Artifact/UI API contracts using synthetic fixtures, never experimental scores."""
import tempfile
from pathlib import Path
from unittest.mock import patch
import unittest
from fastapi.testclient import TestClient
from shield.api import app
from research.delivery import dashboard,compare,SCHEMA
from research.five_methods import compare_episodes,METHODS
from research.branching_env import BranchingEnv
from research.cli import write_new
from research.data import digest


class DeliveryTests(unittest.TestCase):
    def fixture(self):
        cases=[{'factory':lambda:BranchingEnv(partition='development_validation'),'seed':211,
                'options':{'family':'public_itinerary','user_accepts':True}}]
        report=compare_episodes(cases,{},provenance={'scope':'UNIT TEST ONLY'})
        return {'schema':SCHEMA,'evidence_kind':'DEVELOPMENT_ONLY','models':{},
            'comparison':report,'comparison_sha256':digest(report)}

    def test_missing_artifact_is_five_not_run_methods(self):
        with tempfile.TemporaryDirectory() as temp:
            result=dashboard(Path(temp)/'missing.json')
        self.assertEqual(set(result['methods']),set(METHODS))
        self.assertTrue(all(r['status']=='NOT RUN' for r in result['methods'].values()))

    def test_development_artifact_keeps_utility_and_override_fields(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fixture.json';write_new(path,self.fixture());result=dashboard(path)
        self.assertEqual(result['evidence_kind'],'DEVELOPMENT_ONLY')
        self.assertEqual(result['independent_validation'],'NOT PERFORMED')
        self.assertIn('model_decisions_before_overrides',result['methods']['rules']['security_utility'])
        self.assertIn('authorization_overrides',result['methods']['rules']['security_utility'])

    def test_synthetic_setfit_and_missing_ppo_identity_never_show_scores(self):
        envelope=self.fixture();report=envelope['comparison']
        report['methods']['setfit']=report['methods']['rules']
        report['methods']['ppo']=report['methods']['rules']
        envelope['models']['setfit']={'sha256':'a'*64,'evidence_kind':'SYNTHETIC_PIPELINE_CHECK'}
        report['experiment_provenance']['models']=envelope['models']
        envelope['comparison_sha256']=digest(report)
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fixture.json';write_new(path,envelope);result=dashboard(path)
        for method in ('setfit','ppo'):
            self.assertEqual(result['methods'][method]['status'],'NOT RUN')
            self.assertNotIn('summary',result['methods'][method])

    def test_tampered_or_unjustified_validation_envelope_rejected(self):
        for mutate in (lambda e:e['comparison'].update(version='old'),
                       lambda e:e.update(evidence_kind='INDEPENDENTLY_VALIDATED')):
            with tempfile.TemporaryDirectory() as temp:
                envelope=self.fixture();mutate(envelope);path=Path(temp)/'fixture.json';write_new(path,envelope)
                with self.assertRaises(ValueError):dashboard(path)

    def test_comparison_requires_approval_before_model_imports(self):
        with self.assertRaises(PermissionError):compare('unused.json')

    def test_approved_export_contract_with_single_synthetic_fixture(self):
        fixture=[{'family':'public_itinerary','seed':211,'user_accepts':True}]
        with tempfile.TemporaryDirectory() as temp,patch('research.ppo_next.bank',return_value=fixture):
            path=Path(temp)/'fixture.json'
            compare(path,approved=True)
            result=dashboard(path)
            self.assertEqual(result['methods']['rules']['status'],'RUN')
            self.assertEqual(result['methods']['setfit']['status'],'NOT RUN')
            self.assertEqual(result['methods']['ppo']['status'],'NOT RUN')
            with self.assertRaises(ValueError):compare(path,approved=True)

    def test_read_only_endpoint_auth_missing_and_corrupt_artifact(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'fixture.json'
            with patch.dict('os.environ',{'MCPSHIELD_RESEARCH_REPORT':str(path),'MCPSHIELD_API_TOKEN':'fixture-token'}):
                with TestClient(app) as client:
                    self.assertEqual(client.get('/api/research-evaluation').status_code,401)
                    headers={'Authorization':'Bearer fixture-token'}
                    self.assertEqual(client.get('/api/research-evaluation',headers=headers).status_code,200)
                    path.write_text('invalid',encoding='utf-8')
                    result=client.get('/api/research-evaluation',headers=headers)
                    self.assertEqual(result.status_code,503)
                    self.assertNotIn('summary',result.json())


if __name__=='__main__':unittest.main()
