"""PPO infrastructure tests. Opt-in integration uses at most 64 synthetic steps/run."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
import json
import math
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from research.encoding import HashEncoder, feature_text
from research.observations import build_observation
from research.pilot import generate
from research.ppo import PPOConfig, validate_mode, smoke, verify_checkpoint


class PPOContracts(unittest.TestCase):
    def test_research_mode_and_no_opt_in_fail_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/"should-not-exist"
            with self.assertRaises(PermissionError): smoke(output, approved=True, mode="research")
            with self.assertRaises(PermissionError): smoke(output)
            self.assertFalse(output.exists())

    def test_budget_and_rollout_validation(self):
        PPOConfig().validate()
        for config in (replace(PPOConfig(),total_timesteps=65),replace(PPOConfig(),n_epochs=100),
                       replace(PPOConfig(),batch_size=3),replace(PPOConfig(),learning_rate=float("nan")),
                       replace(PPOConfig(),hidden=(10000,10000)),replace(PPOConfig(),wall_time_limit_s=3600)):
            with self.assertRaises(ValueError):config.validate()

    def test_seed_partitions_cannot_overlap(self):
        with self.assertRaises(ValueError): replace(PPOConfig(),validation_seeds=(101,)).validate()

    def test_encoder_only_observable_fields(self):
        episode=generate()["episodes"][0]
        obs=build_observation(episode,0)
        altered=deepcopy(obs)
        altered.update(id="hidden",malicious=True,expected_decision="BLOCKED",reward=100,info={"effects":["hidden"]})
        altered["current"]["expected_decision"]="BLOCKED"
        altered["current"]["response"]={"future":"not available at request time"}
        encoder=HashEncoder()
        self.assertEqual(feature_text(obs),feature_text(altered))
        self.assertEqual(encoder.encode(obs),encoder.encode(altered))
        self.assertAlmostEqual(sum(x*x for x in encoder.encode(obs)),1)

    def test_encoder_preserves_history_context_and_has_no_fit(self):
        episode=next(e for e in generate()["episodes"] if len(e["events"])==4)
        obs=build_observation(episode,3)
        no_history={**obs,"history":[]}
        self.assertNotEqual(HashEncoder().encode(obs),HashEncoder().encode(no_history))
        self.assertEqual(HashEncoder().encode(obs),HashEncoder().encode(obs))
        self.assertFalse(hasattr(HashEncoder(),"fit"))

    def test_truncation_returns_post_transition_observation(self):
        from research.sequential import SequentialEnv
        env=SequentialEnv(horizon=1)
        before,_=env.reset(seed=11,options={"variant":"clean"})
        after,_,terminated,truncated,_=env.step(0)
        self.assertEqual(before["current"]["phase"],"request")
        self.assertTrue(truncated)
        self.assertFalse(terminated)
        self.assertEqual(after["current"]["phase"],"response")

    def test_supervised_control_shares_features_without_training_or_label_access(self):
        from research.supervised import load_encoded_partitions
        obs=build_observation(generate()["episodes"][0],0)
        encoder=HashEncoder()
        data={"train":{"text":[json.dumps(obs)],"label":["ALLOWED"]},
              "validation":{"text":[json.dumps(obs)],"label":["WARNING"]}}
        with patch("research.supervised.load_partitions",return_value=data):
            rows=load_encoded_partitions({}, {}, [], [], encoder)
        self.assertEqual(rows["train"]["features"], rows["validation"]["features"])
        self.assertEqual(rows["train"]["features"][0], encoder.encode(obs))
        self.assertNotEqual(rows["train"]["labels"],rows["validation"]["labels"])


INTEGRATION = os.getenv("MCPSHIELD_PPO_INTEGRATION") == "1" and importlib.util.find_spec("stable_baselines3") is not None


@unittest.skipUnless(INTEGRATION,"Set MCPSHIELD_PPO_INTEGRATION=1 in the isolated PPO environment")
class PPOIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=tempfile.TemporaryDirectory()
        cls.root=Path(cls.directory.name)
        cls.config=replace(PPOConfig(),total_timesteps=32)
        cls.parent=smoke(cls.root/"parent",cls.config,approved=True)

    @classmethod
    def tearDownClass(cls):cls.directory.cleanup()

    def test_real_gym_and_sb3_vector_space(self):
        from research.ppo_env import PPOEnv
        from stable_baselines3.common.env_checker import check_env
        env=PPOEnv()
        check_env(env,warn=True)
        obs,_=env.reset(seed=11)
        self.assertTrue(env.observation_space.contains(obs))
        self.assertTrue(all(math.isfinite(x) for x in obs))
        env.close()

    def test_real_optimizer_checkpoint_and_logs(self):
        completion=json.loads((self.parent/"completion.json").read_text())
        self.assertEqual(completion["status"],"SMOKE_COMPLETED")
        self.assertTrue(completion["weights_updated"])
        self.assertTrue(completion["reload_verified"])
        self.assertTrue(verify_checkpoint(self.parent).exists())
        self.assertTrue((self.parent/"checkpoint-16.zip").exists())
        log=(self.parent/"logs/progress.csv").read_text()
        self.assertIn("train/policy_gradient_loss",log)

    def test_resume_optimizer_to_cumulative_cap(self):
        resumed=smoke(self.root/"resumed",PPOConfig(),approved=True,resume_from=self.parent)
        completion=json.loads((resumed/"completion.json").read_text())
        self.assertEqual(completion["timesteps"],64)
        self.assertTrue(completion["reload_verified"])
        with self.assertRaises(ValueError):
            smoke(self.root/"over-cap",PPOConfig(),approved=True,resume_from=resumed)

    def test_fixed_seed_repeats_policy_weights(self):
        from stable_baselines3 import PPO
        import torch
        repeated=smoke(self.root/"repeat",self.config,approved=True)
        a=PPO.load(self.parent/"policy.zip",device="cpu")
        b=PPO.load(repeated/"policy.zip",device="cpu")
        self.assertTrue(all(torch.equal(x,b.policy.state_dict()[name]) for name,x in a.policy.state_dict().items()))

    def test_interrupted_runs_are_not_valid_checkpoints(self):
        output=self.root/"interrupted"
        with patch("stable_baselines3.PPO.learn",side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):smoke(output,self.config,approved=True)
        self.assertEqual(json.loads((output/"completion.json").read_text())["status"],"INTERRUPTED")
        self.assertFalse((output/"policy.zip").exists())

    def test_checkpoint_tampering_detected_without_loading(self):
        import shutil
        output=self.root/"tamper"
        shutil.copytree(self.parent,output)
        with (output/"policy.zip").open("ab") as stream:stream.write(b"tamper")
        with self.assertRaises(ValueError):verify_checkpoint(output)

    def test_policy_adapter_receives_no_evaluator_information(self):
        from research.ppo import PPOPolicy
        with self.assertRaises(PermissionError):PPOPolicy(self.parent)
        policy=PPOPolicy(self.parent,trusted_local=True)
        obs=build_observation(generate()["episodes"][0],0)
        changed={**obs,"labels":"hidden","effects":["hidden"],"reward":100}
        self.assertEqual(policy(obs),policy(changed))
        self.assertIn(policy(obs),(0,1,2))

    def test_expanded_task_suite_real_ppo_and_reload(self):
        config=replace(self.config,task_suite="branching-development-v1",encoder_version="field-position-hash-v1",dimensions=512)
        output=smoke(self.root/"branching",config,approved=True)
        provenance=json.loads((output/"provenance.json").read_text())
        manifest=json.loads((output/"task-manifest.json").read_text())
        self.assertEqual(provenance["environment"],"branching-development-v1")
        self.assertEqual(provenance["encoder"]["version"],"field-position-hash-v1")
        self.assertTrue(verify_checkpoint(output).exists())
        train_sources={x["provenance"]["metadata_anchor"]["source_group"] for x in manifest["train"]}
        val_sources={x["provenance"]["metadata_anchor"]["source_group"] for x in manifest["development_validation"]}
        self.assertFalse(train_sources&val_sources)
        from research.ppo import PPOPolicy
        from research.branching_env import BranchingEnv
        policy=PPOPolicy(output,trusted_local=True)
        observation,_=BranchingEnv().reset(seed=11)
        self.assertIn(policy(observation),(0,1,2))


if __name__=="__main__":unittest.main()
