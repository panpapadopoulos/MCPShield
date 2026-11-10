"""Accounting/gates only; synthetic records below are not experiment evidence."""
import unittest
from pathlib import Path
import tempfile
from research.development_ablation import summarize,cases,execute


class DevelopmentResultTests(unittest.TestCase):
    def test_approval_required_before_output_or_training(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'unused'
            with self.assertRaises(PermissionError):execute(target)
            self.assertFalse(target.exists())

    def test_case_bank_balances_pairs_members_and_preferences(self):
        for partition in ('train','development_validation'):
            bank=cases(partition)
            self.assertEqual(len(bank),24)
            self.assertEqual(sum(c['member']=='legitimate' for c in bank),12)
            self.assertEqual(sum(c['user_accepts'] for c in bank),12)
        self.assertFalse({c['pair'] for c in cases('train')}&{c['pair'] for c in cases('development_validation')})

    def test_false_positive_probes_and_trajectory_interventions_are_separate(self):
        common={'task_success':False,'unsafe_outcome':False,'policy_interventions':1,
                'warning_steps':1,'steps':2,'approvals':1,'policy_overrides':0,'truncated':True,'return':-.27}
        rows=[{**common,'case':{'member':'legitimate'}},{**common,'case':{'member':'unsafe'},'unsafe_outcome':True}]
        probes=[{'member':'legitimate','action':0},{'member':'legitimate','action':2}]
        result=summarize(rows,probes)
        self.assertEqual(result['provisional_pivot_false_positive_rate'],.5)
        self.assertEqual(result['legitimate_episode_interventions'],1)
        self.assertEqual(result['warning_frequency'],.5)
        self.assertEqual(result['truncations'],2)
        self.assertEqual(result['unsafe_outcomes'],1)


if __name__=='__main__':unittest.main()
