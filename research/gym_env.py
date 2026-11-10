"""Optional real Gymnasium adapter; no PPO/SB3 or model weights needed."""
import json
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from .sequential import SequentialEnv


class MCPTaskEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, horizon=24, max_bytes=16384):
        super().__init__()
        self.engine = SequentialEnv(horizon)
        self.max_bytes = max_bytes
        self.action_space = spaces.Discrete(3)
        self.observation_space = spaces.Dict({"utf8": spaces.Box(0, 255, (max_bytes,), dtype=np.uint8),
                                             "length": spaces.Discrete(max_bytes + 1)})

    def _encode(self, observation):
        raw = json.dumps(observation, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(raw) > self.max_bytes:
            raise ValueError("Observation exceeds adapter capacity; truncation is forbidden")
        array = np.zeros(self.max_bytes, dtype=np.uint8)
        array[:len(raw)] = np.frombuffer(raw, dtype=np.uint8)
        return {"utf8": array, "length": len(raw)}

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        if seed is not None:
            self.action_space.seed(seed)
        observation, info = self.engine.reset(seed=seed if seed is not None else int(self.np_random.integers(0, 2**31)), options=options)
        return self._encode(observation), info

    def step(self, action):
        if not self.action_space.contains(action):
            raise ValueError("Invalid action")
        observation, reward, terminated, truncated, info = self.engine.step(int(action))
        return self._encode(observation), float(reward), terminated, truncated, info
