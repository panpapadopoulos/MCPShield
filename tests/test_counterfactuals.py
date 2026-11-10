"""Matched synthetic semantics and configuration checks, not validated research labels."""
from copy import deepcopy
from dataclasses import asdict
import unittest
from research.counterfactuals import PARTITIONS,generate_pair,CounterfactualEnv,at_pivot
from research.ablations import Representation,CONDITIONS,experiment_plan,sensitivity_plan
from research.counterfactual_checks import rollout,representation_checks
from research.branching_env import RewardWeights
from research.authorization import enforce
from research.encoding import feature_text,encoder_from_config
from research.data import digest


class CounterfactualTests(unittest.TestCase):
    def test_pairs_reproducible_and_exclusively_grouped(self):
        groups=[]
        for split,pairs in PARTITIONS.items():
            for pair in pairs:
                spec=generate_pair(11,split,pair)
                self.assertEqual(digest(spec),digest(generate_pair(11,split,pair)))
                for task in spec['members'].values():
                    self.assertEqual(task['provenance']['pair_group'],pair)
                    self.assertEqual(task['provenance']['partition'],split)
                    self.assertEqual(task['provenance']['human_review'],'UNREVIEWED')
                groups.append(pair)
        self.assertEqual(len(groups),len(set(groups)))
        with self.assertRaises(ValueError):generate_pair(11,'train','history_classification')

    def test_file_pair_differs_only_in_resource_scope(self):
        spec=generate_pair(11,'train','file_scope')
        a,b=deepcopy(spec['members']['legitimate']),deepcopy(spec['members']['unsafe'])
        a.pop('provenance');b.pop('provenance')
        a['authorized']['scope']['file_reader']['resources'].remove('/public/notice.txt')
        self.assertEqual(a,b)
        for member,decision in [('legitimate','ALLOWED'),('unsafe','BLOCKED')]:
            obs,_=at_pivot(11,'train','file_scope',member)
            self.assertEqual(enforce(obs,'ALLOWED')['effective'],decision)

    def test_all_pair_differences_are_limited_to_declared_factor_and_its_transition(self):
        def differences(a,b,path=''):
            if isinstance(a,dict) and isinstance(b,dict):
                return {p for key in set(a)|set(b) for p in differences(a.get(key),b.get(key),path+'/'+key)}
            return set() if a==b else {path}
        allowed={
            'file_scope':{'/authorized/scope/file_reader/resources'},
            'permission_scope':{'/authorized/scope/database_search/permissions'},
            'instruction_override':{'/nodes/search_result/response/instruction','/nodes/search_result/allow'},
            'terminology':{'/nodes/search_result/response/instruction','/nodes/search_result/allow'},
            'followup_scope':{'/authorized/scope/web_search/permissions'},
            'history_classification':{'/nodes/notice/response/reference_classification'}}
        for split,pairs in PARTITIONS.items():
            for pair in pairs:
                spec=generate_pair(11,split,pair)
                a,b=deepcopy(spec['members']['legitimate']),deepcopy(spec['members']['unsafe'])
                a.pop('provenance');b.pop('provenance')
                self.assertEqual(differences(a,b),allowed[pair],pair)

    def test_permission_pair_differs_only_in_grant(self):
        spec=generate_pair(11,'train','permission_scope')
        a,b=deepcopy(spec['members']['legitimate']),deepcopy(spec['members']['unsafe'])
        a.pop('provenance');b.pop('provenance');a['authorized']['scope']['database_search']['permissions']=[]
        self.assertEqual(a,b)
        for member,decision in [('legitimate','ALLOWED'),('unsafe','BLOCKED')]:
            obs,_=at_pivot(11,'train','permission_scope',member)
            self.assertEqual(enforce(obs,'ALLOWED')['effective'],decision)

    def test_sharing_scope_and_history_control_actual_egress(self):
        for pair in ('followup_scope','history_classification'):
            for member,harm in [('legitimate',False),('unsafe',True)]:
                result=rollout(lambda obs:0,11,'development_validation',pair,member,True,RewardWeights(),24)
                self.assertEqual(result['unsafe_outcome'],harm)
                self.assertEqual(result['task_success'],not harm)

    def test_response_directive_semantics_and_recovery(self):
        for split,pair in [('train','instruction_override'),('development_validation','terminology')]:
            for member,harm in [('legitimate',False),('unsafe',True)]:
                result=rollout(lambda obs:0,11,split,pair,member,True,RewardWeights(),24)
                self.assertEqual(result['unsafe_outcome'],harm)
                self.assertEqual(result['task_success'],not harm)
            env=CounterfactualEnv(partition=split)
            env.reset(seed=11,options={'pair':pair,'member':'unsafe'})
            while env.node!='search_result':env.step(0)
            obs,*_=env.step(2)
            while True:
                obs,_,term,trunc,info=env.step(0)
                if term or trunc:break
            self.assertTrue(info['task_success']);self.assertFalse(info['unsafe_outcome'])

    def test_no_unobservable_future_decision_proposals(self):
        a,_=at_pivot(11,'development_validation','history_classification','legitimate')
        b,_=at_pivot(11,'development_validation','history_classification','unsafe')
        self.assertEqual(a['current'],b['current'])
        self.assertEqual(a['authorized'],b['authorized'])
        self.assertNotEqual(a['history'],b['history'])
        altered=deepcopy(a);altered.update(proposed_decision='BLOCKED',member='unsafe',future_effects=['secret_disclosed'])
        self.assertEqual(feature_text(a),feature_text(altered))


class AblationTests(unittest.TestCase):
    def test_equal_dimensions_and_explicit_alias(self):
        a,_=at_pivot(11,'train','file_scope','legitimate')
        for name in CONDITIONS:
            encoder=Representation(name)
            self.assertEqual(len(encoder.encode(a)),512)
            self.assertEqual(encoder_from_config(encoder.config()).encode(a),encoder.encode(a))
        self.assertEqual(Representation('B_field').encode(a),Representation('D_field_history').encode(a))
        self.assertEqual(Representation('D_field_history').config()['alias_of'],'B_field')

    def test_history_ablation_removes_classification_and_proxies(self):
        a,_=at_pivot(11,'development_validation','history_classification','legitimate')
        b,_=at_pivot(11,'development_validation','history_classification','unsafe')
        self.assertEqual(Representation('C_field_no_history').encode(a),Representation('C_field_no_history').encode(b))
        for name in ('A_original','B_field','D_field_history'):
            self.assertNotEqual(Representation(name).encode(a),Representation(name).encode(b))
        projected=Representation('C_field_no_history').project(a)
        self.assertEqual(projected['history'],[]);self.assertEqual(projected['history_omitted'],0)

    def test_all_context_pairs_distinguished_by_full_representations(self):
        report=representation_checks()
        self.assertEqual(len(report['rows']),12)
        for row in report['rows']:
            self.assertTrue(row['B_D_alias_verified'])
            for name in ('A_original','B_field','D_field_history'):
                self.assertTrue(row['representations'][name]['distinguishes'],row['pair_group'])

    def test_predeclared_plan_keeps_budget_and_seed_controls_fixed(self):
        plan=experiment_plan()
        self.assertEqual(digest(plan),digest(experiment_plan()))
        self.assertEqual(plan['training_status'],'NOT RUN')
        self.assertEqual(plan['training_budget'],64)
        for representation in plan['representations'].values():self.assertEqual(representation['dimensions'],512)
        self.assertEqual(len(plan['reward_sensitivity']),7)

    def test_sensitivity_changes_one_parameter_at_a_time(self):
        primary=sensitivity_plan()['primary']
        for name,setting in sensitivity_plan().items():
            if name=='primary':continue
            changes=sum(v!=primary['weights'][k] for k,v in setting['weights'].items())+int(setting['horizon']!=primary['horizon'])
            self.assertEqual(changes,1,name)

    def test_harm_cost_and_timeout_findings_are_reported_not_optimized(self):
        a=rollout(lambda o:0,11,'development_validation','followup_scope','unsafe',True,RewardWeights(),24)
        b=rollout(lambda o:0,11,'development_validation','followup_scope','unsafe',True,RewardWeights(harm=20),24)
        self.assertAlmostEqual(a['return']-b['return'],10)
        timeout=rollout(lambda o:1,11,'train','file_scope','legitimate',True,RewardWeights(),1)
        complete=rollout(lambda o:1,11,'train','file_scope','legitimate',True,RewardWeights(),24)
        self.assertTrue(timeout['truncated']);self.assertFalse(timeout['task_success'])
        self.assertGreater(timeout['return'],complete['return'])


if __name__=='__main__':unittest.main()
