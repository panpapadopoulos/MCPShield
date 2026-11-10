"""Real optional Gymnasium contract checks. No policy training."""
import json
import unittest
try:
    from research.gym_env import MCPTaskEnv
    from gymnasium.utils.env_checker import check_env
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


@unittest.skipUnless(AVAILABLE, "Optional Gymnasium test dependencies not installed")
class GymTests(unittest.TestCase):
    def test_actual_gym_contract(self):
        env = MCPTaskEnv()
        check_env(env, skip_render_check=True)
        env.close()

    def test_encoding_contains_only_observation(self):
        env = MCPTaskEnv()
        observation, _ = env.reset(seed=11, options={"variant":"poisoned"})
        self.assertTrue(env.observation_space.contains(observation))
        decoded = json.loads(bytes(observation["utf8"][:observation["length"]]))
        self.assertNotIn("response", decoded["current"])
        self.assertNotIn("effects", decoded)

    def test_no_silent_truncation(self):
        with self.assertRaises(ValueError):
            MCPTaskEnv(max_bytes=8).reset(seed=11)

    def test_branching_vector_adapter_contract_and_pending_state(self):
        from research.ppo_env import PPOEnv
        from research.encoding import FieldHashEncoder
        env=PPOEnv(encoder=FieldHashEncoder(),task_suite='branching-development-v1',partition='development_validation')
        check_env(env,skip_render_check=True)
        obs,_=env.reset(seed=11,options={'family':'scoped_archive','user_accepts':True})
        for _ in range(4):obs,*_=env.step(0)
        before=obs.copy();count=len(env.engine.executions)
        pending,_,_,_,info=env.step(1)
        self.assertTrue(env.observation_space.contains(pending))
        self.assertFalse((before==pending).all())
        self.assertEqual(len(env.engine.executions),count)
        env.close()

    def test_counterfactual_adapters_keep_equal_spaces_across_ablations(self):
        from research.counterfactual_gym import CounterfactualGymEnv
        from research.ablations import CONDITIONS
        for condition in CONDITIONS:
            env=CounterfactualGymEnv(condition)
            check_env(env,skip_render_check=True)
            obs,_=env.reset(seed=11,options={'pair':'file_scope','member':'unsafe'})
            self.assertEqual(obs.shape,(512,))
            self.assertTrue(env.observation_space.contains(obs))
            env.close()


if __name__ == "__main__": unittest.main()
