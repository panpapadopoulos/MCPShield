"""PPO-compatible vector wrapper, separate from the original byte adapter."""
import numpy as np
from gymnasium import spaces
from .gym_env import MCPTaskEnv
from .encoding import HashEncoder


class PPOEnv(MCPTaskEnv):
    def __init__(self, *, encoder=None, horizon=24, episode_seeds=(101, 103, 107), task_suite="foundation-v2", partition="train"):
        super().__init__(horizon=horizon)
        self.encoder = encoder or HashEncoder()
        if task_suite not in ("foundation-v2","branching-development-v1"):
            raise ValueError("Unknown task suite")
        self.task_suite,self.partition=task_suite,partition
        if task_suite=="branching-development-v1":
            from .branching_env import BranchingEnv
            self.engine=BranchingEnv(horizon=horizon,partition=partition)
        if not episode_seeds or len(set(episode_seeds)) != len(episode_seeds) or any(type(s) is not int or s < 0 for s in episode_seeds):
            raise ValueError("Nonempty unique episode seeds required")
        self.episode_seeds = tuple(episode_seeds)
        self.observation_space = spaces.Box(-1.0, 1.0, (self.encoder.dimensions,), dtype=np.float32)

    def _encode(self, observation):
        return np.asarray(self.encoder.encode(observation), dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        # Training RNG selects only from its declared episode-seed partition.
        # Explicit reset seed gives repeatable selection but is not a test ID feature.
        import gymnasium as gym
        gym.Env.reset(self, seed=seed)
        choice = int(self.np_random.integers(0, len(self.episode_seeds)))
        self.last_episode_seed = self.episode_seeds[choice]
        observation, info = self.engine.reset(seed=self.last_episode_seed, options=options)
        return self._encode(observation), info
