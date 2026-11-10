"""Synthetic mechanics, not human-reviewed data or learned-policy evidence."""
from copy import deepcopy
from dataclasses import replace
import json
import unittest
from research.task_suite import generate,validate,PARTITIONS,SOURCES
from research.branching_env import BranchingEnv,RewardWeights
from research.encoding import HashEncoder,FieldHashEncoder,feature_text
from research.validate_tasks import run, history_reference
from research.data import digest


class TaskTests(unittest.TestCase):
    def test_reproducible_graphs_provenance_and_disjoint_panels(self):
        self.assertFalse(set(PARTITIONS['train'])&set(PARTITIONS['development_validation']))
        self.assertFalse(set(SOURCES['train'])&set(SOURCES['development_validation']))
        for partition,families in PARTITIONS.items():
            for family in families:
                task=generate(11,partition,family)
                self.assertEqual(digest(task),digest(generate(11,partition,family)))
                self.assertTrue(validate(task))
                self.assertEqual(task['provenance']['human_review'],'UNREVIEWED')
                self.assertIn(task['provenance']['metadata_anchor']['record_id'],SOURCES[partition])
        with self.assertRaises(ValueError):generate(11,'train','private_redirect')

    def test_cycle_and_unpaired_response_rejected(self):
        task=generate(11,'train','public_report')
        task['nodes']['search']['allow']='search'
        with self.assertRaises(ValueError):validate(task)
        task=generate(11,'train','public_report');task['start']='notice'
        with self.assertRaises(ValueError):validate(task)

    def test_legitimate_multi_tool_requires_all_delivered_evidence(self):
        for partition,family in [('train','public_report'),('development_validation','public_itinerary')]:
            result=run(lambda obs:0,11,partition,family,True)
            self.assertTrue(result['task_success'])
            self.assertEqual(result['steps'],8)
            self.assertEqual(result['executions'],4)
            self.assertAlmostEqual(result['return'],5-8*.02)

    def test_delayed_disclosure_has_no_harm_until_sink_execution(self):
        env=BranchingEnv(partition='development_validation')
        obs,_=env.reset(seed=11,options={'family':'delayed_transfer'})
        for _ in range(6):obs,_,terminated,_,info=env.step(0)
        self.assertFalse(terminated);self.assertFalse(info['unsafe_outcome'])
        self.assertEqual(obs['current']['tool'],'web_search')
        _,reward,terminated,_,info=env.step(0)
        self.assertTrue(terminated);self.assertTrue(info['unsafe_outcome'])
        self.assertIn('secret_disclosed',info['effects'])
        self.assertAlmostEqual(reward,-10.02)
        with self.assertRaises(RuntimeError):env.step(2)

    def test_split_response_attack_and_safe_recovery(self):
        env=BranchingEnv();obs,_=env.reset(seed=11,options={'family':'split_directive'})
        env.step(0);obs,*_=env.step(0);env.step(0);obs,*_=env.step(2)
        self.assertEqual(obs['current']['arguments']['query'].split()[-2:],['municipal','alternative'])
        while True:
            obs,_,terminated,truncated,info=env.step(0)
            if terminated or truncated:break
        self.assertTrue(info['task_success']);self.assertFalse(info['unsafe_outcome'])
        self.assertEqual(info['recoveries'],1)

    def test_poisoned_description_delays_effect_and_can_be_blocked_early(self):
        env=BranchingEnv();obs,_=env.reset(seed=11,options={'family':'poisoned_catalog'})
        self.assertIn('Integration override',obs['current']['description'])
        obs,_,_,_,info=env.step(2)
        self.assertEqual(info['executions'],0);self.assertEqual(info['recoveries'],1)
        while True:
            obs,_,term,trunc,info=env.step(0)
            if term or trunc:break
        self.assertTrue(info['task_success'])

    def test_private_and_admin_constraints_cannot_be_approved_away(self):
        for partition,family in [('train','permission_escalation'),('development_validation','private_redirect')]:
            result=run(lambda obs:0,11,partition,family,True)
            self.assertTrue(result['task_success']);self.assertFalse(result['unsafe_outcome'])
            self.assertEqual(result['policy_overrides'],1)
            self.assertEqual(result['recoveries'],1)

    def test_warning_pauses_without_replay_then_approval_or_denial_branches(self):
        for preference in (True,False):
            env=BranchingEnv(partition='development_validation')
            env.reset(seed=11,options={'family':'scoped_archive','user_accepts':preference})
            for _ in range(4):env.step(0)
            count=len(env.executions)
            obs,reward,_,_,info=env.step(1)
            self.assertTrue(obs['runtime']['approval_pending']);self.assertEqual(len(env.executions),count)
            self.assertAlmostEqual(reward,-.27)
            obs,_,_,_,info=env.step(0)
            self.assertFalse(obs['runtime']['approval_pending'])
            self.assertEqual(len(env.executions),count+int(preference))
            self.assertEqual(info['approvals_accepted'],int(preference))
            self.assertEqual(info['approvals_rejected'],int(not preference))
            self.assertEqual(obs['runtime']['last_approval'],'approved' if preference else 'rejected')

    def test_no_oracle_for_generic_warning_on_malicious_response(self):
        env=BranchingEnv();env.reset(seed=11,options={'family':'split_directive','user_accepts':True})
        env.step(0);obs,*_=env.step(1)
        self.assertTrue(obs['runtime']['approval_pending'])
        obs,_,_,_,info=env.step(0)
        self.assertEqual(info['approvals_accepted'],1)
        self.assertEqual(obs['current']['tool'],'database_search')

    def test_block_all_and_warning_spam_do_not_earn_terminal_utility(self):
        for action in (1,2):
            result=run(lambda obs:action,11,'train','public_report',True)
            self.assertFalse(result['task_success']);self.assertLess(result['return'],0)
            self.assertTrue(result['terminated']);self.assertFalse(result['truncated'])
            self.assertLess(result['steps'],10)
            self.assertAlmostEqual(result['return'],-4.08 if action==1 else -3.44)

    def test_reward_terms_and_sensitivity_without_changing_outcomes(self):
        a=run(lambda obs:0,11,'train','split_directive',True,RewardWeights())
        b=run(lambda obs:0,11,'train','split_directive',True,RewardWeights(harm=20))
        self.assertTrue(a['unsafe_outcome']);self.assertTrue(b['unsafe_outcome'])
        self.assertAlmostEqual(a['return']-b['return'],10)
        with self.assertRaises(ValueError):RewardWeights(warning=-1)

    def test_observable_history_reference_beats_constant_block_on_authored_cases(self):
        for partition,families in PARTITIONS.items():
            for family in families:
                for preference in (True,False):
                    result=run(history_reference,11,partition,family,preference)
                    self.assertTrue(result['task_success'],family)
                    self.assertFalse(result['unsafe_outcome'],family)
                    self.assertGreater(result['return'],0)

    def test_truncation_returns_next_state_without_false_terminal_reward(self):
        env=BranchingEnv(horizon=1);before,_=env.reset(seed=11,options={'family':'public_report'})
        after,reward,term,trunc,info=env.step(0)
        self.assertFalse(term);self.assertTrue(trunc);self.assertEqual(after['current']['phase'],'response')
        self.assertEqual(info['reward_terms'],{'step':-.02})

    def test_future_and_ground_truth_not_observed(self):
        env=BranchingEnv();obs,_=env.reset(seed=11,options={'family':'split_directive'})
        text=feature_text(obs)
        for forbidden in ('split_directive','provenance','world','secret_disclosed',env.task['world']['secret']):
            self.assertNotIn(forbidden,text)
        altered=deepcopy(obs);altered['runtime'].update(expected_decision='BLOCKED',reward=100)
        self.assertEqual(feature_text(obs),feature_text(altered))
        env.step(0);env.step(0);obs,*_=env.step(0)
        self.assertIn(env.task['world']['secret'],feature_text(obs))
        self.assertEqual(len(obs['history']),3)


class EncoderTests(unittest.TestCase):
    def setUp(self):
        self.obs=BranchingEnv().reset(seed=11,options={'family':'public_report'})[0]

    def test_known_order_collision_is_real_and_new_encoder_distinguishes(self):
        a=deepcopy(self.obs);b=deepcopy(a)
        a['current']['arguments']={'query':'aaabaa'};b['current']['arguments']={'query':'aabaaa'}
        self.assertEqual(HashEncoder().encode(a),HashEncoder().encode(b))
        self.assertNotEqual(FieldHashEncoder().encode(a),FieldHashEncoder().encode(b))

    def test_context_phase_history_and_approval_are_encoded(self):
        for modify in (lambda o:o['authorized']['scope']['web_search'].update(permissions=['extra']),
                       lambda o:o['runtime'].update(approval_pending=True),
                       lambda o:o.update(history=[deepcopy(o['current'])]),
                       lambda o:o['current'].update(phase='response',response={'text':'ordinary data'})):
            changed=deepcopy(self.obs);modify(changed)
            self.assertNotEqual(FieldHashEncoder().encode(self.obs),FieldHashEncoder().encode(changed))


if __name__=='__main__':unittest.main()
