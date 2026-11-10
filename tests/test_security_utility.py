"""Synthetic metric and real review-gate contracts; no persisted human reviews."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from research.five_methods import compare_episodes
from research.branching_env import BranchingEnv
from research.utility_metrics import security_utility
from research.supervised import load_partitions,readiness_report
from research.data import split_development
from research.pilot import generate
from research.reviews import export_review,import_review
from research.cli import prepare_rows
from shield.dataset import load_cases


class UtilityTests(unittest.TestCase):
    def compare(self,policy,targets=None,malicious_nodes=()):
        case={'factory':lambda:BranchingEnv(partition='development_validation'),'seed':211,
            'options':{'family':'public_itinerary','user_accepts':True},
            'evaluation_targets':targets or {'search':'ALLOWED'},'reference_uninterrupted_steps':8,
            'evaluation_malicious_nodes':list(malicious_nodes)}
        result=compare_episodes([case],{'ppo':policy},allow_model_calls=True)
        self.assertEqual(result['methods']['ppo']['status'],'RUN')
        return result['methods']['ppo']

    def test_uninterrupted_and_avoidable_recovery_are_distinct(self):
        clean=self.compare(lambda obs:0)['security_utility']
        def block_first(obs):return 2 if not obs['history'] else 0
        recovered=self.compare(block_first)['security_utility']
        self.assertEqual(clean['uninterrupted_completion'],1)
        self.assertEqual(recovered['uninterrupted_completion'],0)
        self.assertEqual(recovered['completion_after_avoidable_block'],1)
        self.assertEqual(recovered['initial_action_block_rate'],1)
        self.assertEqual(recovered['gross_steps_after_recovery_entry'],4)
        self.assertEqual(recovered['net_step_deltas_vs_supplied_uninterrupted_reference'],[-3])
        self.assertEqual(recovered['avoidable_legitimate_blocks'],1)

    def test_unknown_correctness_is_not_assumed_safe_or_malicious(self):
        result=self.compare(lambda obs:2,{'search':'WARNING'})['security_utility']
        self.assertEqual(result['avoidable_legitimate_blocks'],0)
        self.assertIsNone(result['correct_malicious_block_rate'])

    def test_annotation_never_enters_model_features(self):
        seen=[]
        def spy(obs):seen.append(obs);return 0
        self.compare(spy,{'search':'BLOCKED'})
        self.assertNotIn('evaluation_target',json.dumps(seen))
        self.assertNotIn('reference_uninterrupted_steps',json.dumps(seen))

    def test_authorization_override_is_not_model_detection(self):
        case={'factory':lambda:BranchingEnv(partition='development_validation'),'seed':211,
              'options':{'family':'private_redirect','user_accepts':True}}
        result=compare_episodes([case],{'ppo':lambda obs:0},allow_model_calls=True)['methods']['ppo']
        self.assertEqual(result['status'],'RUN')
        metric=result['security_utility']
        self.assertGreater(metric['authorization_overrides'],0)
        self.assertEqual(set(metric['model_decisions_before_overrides']),{'ALLOWED'})
        self.assertEqual(metric['correct_malicious_block_recommendations'],0)

    def test_correct_block_is_counted_only_with_explicit_target(self):
        def block_first_response(obs):return 2 if len(obs['history'])==1 else 0
        metric=self.compare(block_first_response,{'search_result':'BLOCKED'},['search_result'])['security_utility']
        self.assertEqual(metric['correct_malicious_block_recommendations'],1)
        self.assertEqual(metric['avoidable_legitimate_blocks'],0)

    def test_missing_old_trace_metadata_is_reported_unknown(self):
        rows=deepcopy(self.compare(lambda obs:0)['records'])
        for t in rows[0]['trace']:t.pop('recovery_step')
        self.assertIsNone(security_utility(rows)['gross_steps_after_recovery_entry'])

    def test_reward_proposal_orders_safe_uninterrupted_above_shortcut(self):
        proposal=json.loads(Path('data/research/reward-utility-v2-proposal.json').read_text())
        w=proposal['weights']
        self.assertGreater(-w['avoidable_legitimate_block'],24*-w['step'])
        ordinary=5+8*w['step']
        shortcut=5+5*w['step']+w['model_block']+w['avoidable_legitimate_block']+w['recovery_entry']
        self.assertGreater(ordinary,shortcut)
        self.assertEqual(BranchingEnv().weights.success,5)


class ReviewedImportTests(unittest.TestCase):
    def setUp(self):
        self.dataset=generate();self.historical=load_cases()
        self.splits=split_development(self.dataset,self.historical)

    def votes(self,conflict=False):
        # In-memory unit-test fixtures, never saved or represented as human work.
        ledger=[]
        for reviewer in ('UNIT_FIXTURE_A','UNIT_FIXTURE_B'):
            form=export_review(self.dataset,reviewer,True)
            form['human_attestation']=form['independent_attestation']=True
            for item in form['items']:
                item['action']='accept';item['justification']='Synthetic unit-test fixture only'
            if conflict and reviewer=='UNIT_FIXTURE_B':
                item=form['items'][0];item['action']='reject';item['reviewed_label']=None
            ledger=import_review(self.dataset,ledger,form)
        return ledger

    def test_unreviewed_data_blocks_training_import(self):
        report=readiness_report(self.dataset,self.splits,self.historical,[])
        self.assertFalse(report['data_gates_pass'])
        self.assertEqual(sum(report['reviewed_support']['train'].values()),0)
        with self.assertRaises(ValueError):load_partitions(self.dataset,self.splits,self.historical,[])

    def test_disagreement_blocks_even_after_two_imports(self):
        ledger=self.votes(True)
        self.assertFalse(readiness_report(self.dataset,self.splits,self.historical,ledger)['all_boundaries_reconciled'])
        with self.assertRaises(ValueError):load_partitions(self.dataset,self.splits,self.historical,ledger)

    def test_actual_import_contract_retains_group_separation(self):
        ledger=self.votes()
        for split in ('train','validation'):
            x,y=prepare_rows(self.dataset,self.splits,self.historical,ledger,split)
            self.assertEqual(len(x),len(y))
            self.assertNotIn('proposed_labels',json.dumps(x))
        modified=deepcopy(self.splits)
        identifier=next(iter(modified['assignments']))
        modified['assignments'][identifier]='validation' if modified['assignments'][identifier]=='train' else 'train'
        with self.assertRaises(ValueError):prepare_rows(self.dataset,modified,self.historical,ledger)

    def test_missing_class_support_cannot_force_three_class_training(self):
        dataset=deepcopy(self.dataset)
        for e in dataset['episodes']:
            for label in e['proposed_labels']:
                if label['decision']=='WARNING':label['decision']='ALLOWED'
        self.dataset=dataset;self.splits=split_development(dataset,self.historical)
        ledger=self.votes()
        report=readiness_report(dataset,self.splits,self.historical,ledger)
        self.assertFalse(report['three_class_minimum_support'])
        self.assertEqual(report['binary_alternative']['status'],'PROPOSAL_ONLY_NOT_IMPLEMENTED_NOT_APPROVED')
        with self.assertRaises(ValueError):load_partitions(dataset,self.splits,self.historical,ledger)


if __name__=='__main__':unittest.main()
