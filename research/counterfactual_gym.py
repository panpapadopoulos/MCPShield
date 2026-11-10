"""Gymnasium adapter for predeclared development probes; no training entry point."""
from .ppo_env import PPOEnv
from .ablations import Representation
from .counterfactuals import CounterfactualEnv,VERSION


class CounterfactualGymEnv(PPOEnv):
    def __init__(self,condition="B_field",*,partition="train",horizon=24,
                 episode_seeds=(101,103,107),weights=None):
        super().__init__(encoder=Representation(condition),horizon=horizon,episode_seeds=episode_seeds)
        self.partition=partition;self.task_suite=VERSION
        self.engine=CounterfactualEnv(horizon=horizon,partition=partition,weights=weights)
