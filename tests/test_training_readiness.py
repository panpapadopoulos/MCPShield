"""Readiness contracts and optional tiny-transformer integration, not research evidence."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research.branching_env import BranchingEnv
from research.five_methods import boundary,ContentRules,ContextQwen,compare_boundaries,compare_episodes
from research.ppo_next import protocol,preflight,bank,run
from research.setfit_backend import labels_from_predictions
from research.provision_minilm import provision


class ReadinessTests(unittest.TestCase):
    def test_download_and_full_ppo_run_require_approval(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'unused'
            with self.assertRaises(PermissionError):provision(target)
            with self.assertRaises(PermissionError):run(protocol(),target)
            self.assertFalse(target.exists())

    def test_predefined_protocol_is_bounded_and_separated(self):
        p=protocol();manifest=preflight(p)
        self.assertEqual(p['total_steps'],30720)
        self.assertEqual(p['steps_per_seed']%p['n_steps'],0)
        self.assertEqual(len(bank('train',p)),24)
        self.assertFalse(set(p['train_episode_seeds'])&set(p['development_validation_seeds']))
        self.assertEqual(set(manifest),{'train','development_validation'})
        altered=deepcopy(p);altered['steps_per_seed']*=2
        with self.assertRaises(ValueError):preflight(altered)

    def test_label_encoding_accepts_actual_list_and_integer_outputs(self):
        self.assertEqual(labels_from_predictions([0,1,2]),['ALLOWED','WARNING','BLOCKED'])
        self.assertEqual(labels_from_predictions(['BLOCKED']),['BLOCKED'])
        with self.assertRaises(ValueError):labels_from_predictions([3])

    def test_rules_have_no_historical_path_assumption(self):
        env=BranchingEnv();obs,_=env.reset(seed=11,options={'family':'public_report'})
        env.step(0);obs,*_=env.step(0)
        self.assertEqual(obs['current']['arguments']['path'],'/public/notice.txt')
        self.assertEqual(boundary(obs,ContentRules())['effective'],'ALLOWED')
        obs['authorized']['scope']['file_reader']['resources']=[]
        self.assertEqual(boundary(obs,lambda o:0)['effective'],'BLOCKED')

    def test_equivalent_feature_projection_and_missing_model_status(self):
        obs=BranchingEnv().reset(seed=11)[0]
        obs['expected_decision']='BLOCKED'
        seen=[]
        def spy(value):seen.append(value);return 0
        result=compare_boundaries([obs],{'pretrained_qwen':spy,'setfit':spy,'ppo':spy},allow_model_calls=True)
        self.assertEqual(seen[0],seen[1]);self.assertEqual(seen[1],seen[2])
        self.assertNotIn('expected_decision',seen[0])
        disabled=compare_boundaries([obs])
        self.assertEqual(disabled['methods']['setfit']['status'],'NOT RUN')

    def test_qwen_contextual_payload_and_local_only_gate(self):
        captured=[]
        def fixture_transport(body):
            captured.append(body)
            return {'choices':[{'message':{'content':json.dumps({'decision':'ALLOWED','category':'none','explanation':'Unit-test output only'})}}]}
        with patch.dict(os.environ,{'MCPSHIELD_LLM_BASE_URL':'http://127.0.0.1:11434/v1','MCPSHIELD_LLM_MODEL':'qwen2.5:3b'}):
            adapter=ContextQwen(fixture_transport)
            obs=BranchingEnv().reset(seed=11)[0]
            self.assertEqual(adapter(obs),0)
            self.assertEqual(json.loads(captured[0]['messages'][1]['content'])['authorized'],obs['authorized'])
            self.assertNotIn('/public/readme.txt',captured[0]['messages'][0]['content'])
        with patch.dict(os.environ,{'MCPSHIELD_LLM_BASE_URL':'https://api.openai.com/v1'}):
            with self.assertRaises(ValueError):ContextQwen(fixture_transport)

    def test_shared_approval_protocol_and_error_status(self):
        cases=[{'factory':lambda:BranchingEnv(partition='development_validation'),'seed':11,
            'options':{'family':'scoped_archive','user_accepts':True}}]
        report=compare_episodes(cases,{'ppo':lambda o:1},allow_model_calls=True)
        trace=report['methods']['ppo']['records'][0]['trace']
        self.assertTrue(any(row['action_source']=='shared_approval_driver' for row in trace))
        def invalid(obs):raise RuntimeError('fixture-only')
        result=compare_boundaries([BranchingEnv().reset(seed=11)[0]],{'ppo':invalid},allow_model_calls=True)
        self.assertEqual(result['methods']['ppo']['status'],'ERROR')


AVAILABLE=os.getenv('MCPSHIELD_SETFIT_INTEGRATION')=='1' and importlib.util.find_spec('setfit') is not None


@unittest.skipUnless(AVAILABLE,'Set MCPSHIELD_SETFIT_INTEGRATION=1 in isolated CPU ML environment')
class SetFitIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from research.setfit_smoke import execute
        cls.directory=tempfile.TemporaryDirectory();cls.root=Path(cls.directory.name)/'run'
        cls.result=execute(cls.root,approved=True)
    @classmethod
    def tearDownClass(cls):cls.directory.cleanup()

    def test_real_encoder_training_and_checkpoint(self):
        self.assertTrue(self.result['weights_updated']);self.assertTrue(self.result['reload_verified'])
        self.assertEqual(self.result['evidence_kind'],'SYNTHETIC_PIPELINE_CHECK')
        self.assertGreater(self.result['chunk_stats']['train']['chunks'],self.result['chunk_stats']['train']['documents'])

    def test_tail_tokens_and_document_cardinality(self):
        from research.setfit_backend import SavedClassifier
        saved=SavedClassifier(self.root,trusted_local=True)
        encoder=saved.model.model_body[0]
        features=encoder.tokenize(['public '*100+'attack','weather'])
        self.assertIn(encoder.tokenizer.convert_tokens_to_ids('attack'),features['input_ids'][-2].tolist()+features['input_ids'][-3].tolist())
        output=encoder(features)['sentence_embedding']
        self.assertEqual(tuple(output.shape),(2,24))
        encoder.max_chunks=1
        with self.assertRaises(ValueError):encoder.tokenize(['public '*100])

    def test_fixture_not_misrepresented_as_research_classifier(self):
        from research.setfit_backend import SavedClassifier
        saved=SavedClassifier(self.root,trusted_local=True)
        obs=BranchingEnv().reset(seed=11)[0]
        self.assertEqual(compare_boundaries([obs],{'setfit':saved},allow_model_calls=True)['methods']['setfit']['status'],'NOT RUN')


if __name__=='__main__':unittest.main()
