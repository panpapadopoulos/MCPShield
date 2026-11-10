"""Bounded PPO infrastructure smoke tests. Research training is deliberately gated."""
import argparse
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import math
from pathlib import Path
import time
from .cli import write_new
from .data import digest
from .encoding import HashEncoder, encoder_from_config
from .sequential import ENV_VERSION, ACTIONS


@dataclass(frozen=True)
class PPOConfig:
    seed: int = 11
    total_timesteps: int = 64
    n_steps: int = 16
    batch_size: int = 16
    n_epochs: int = 2
    learning_rate: float = 3e-4
    gamma: float = .99
    gae_lambda: float = .95
    clip_range: float = .2
    ent_coef: float = .01
    hidden: tuple = (32, 32)
    dimensions: int = 256
    horizon: int = 24
    train_seeds: tuple = (101, 103, 107)
    validation_seeds: tuple = (211, 223)
    checkpoint_every: int = 16
    wall_time_limit_s: int = 30
    task_suite: str = "foundation-v2"
    encoder_version: str = "signed-char-hash-v1"

    def encoder(self):
        return encoder_from_config({"version":self.encoder_version,"dimensions":self.dimensions})

    def environment_version(self):
        return ENV_VERSION if self.task_suite=="foundation-v2" else "branching-development-v1"

    def validate(self):
        integers = (self.seed, self.total_timesteps, self.n_steps, self.batch_size, self.n_epochs, self.dimensions, self.horizon, self.checkpoint_every, self.wall_time_limit_s)
        if any(type(x) is not int for x in integers) or self.seed < 0 or min(integers[1:]) < 1:
            raise ValueError("Positive integer PPO dimensions/budgets required")
        if self.n_steps < 2 or self.batch_size < 2 or self.n_steps % self.batch_size or self.total_timesteps % self.n_steps:
            raise ValueError("Require full rollouts and divisible minibatches; no hidden step overshoot")
        if self.total_timesteps > 64 or self.n_epochs > 2 or self.n_steps > 64 or self.horizon > 24 or len(self.hidden) != 2 or any(type(x) is not int or not 1 <= x <= 64 for x in self.hidden) or self.dimensions > 512 or self.wall_time_limit_s > 60:
            raise ValueError("Infrastructure smoke budget exceeded; research runs require a future reviewed task pipeline")
        for value in (self.learning_rate, self.gamma, self.gae_lambda, self.clip_range, self.ent_coef):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Invalid PPO coefficient")
        if self.learning_rate == 0 or self.clip_range == 0:
            raise ValueError("Positive learning rate and clip range required")
        for seeds in (self.train_seeds, self.validation_seeds):
            if not seeds or len(seeds) > 32 or len(set(seeds)) != len(seeds) or any(type(s) is not int or s < 0 for s in seeds):
                raise ValueError("Unique nonnegative seed partitions required")
        if set(self.train_seeds) & set(self.validation_seeds):
            raise ValueError("Training and validation episode seeds must be disjoint")
        if self.task_suite not in ("foundation-v2","branching-development-v1"):
            raise ValueError("Unknown task suite")
        self.encoder()


def validate_mode(mode, config, approved):
    if mode != "synthetic-smoke":
        raise PermissionError("Research training is disabled: reviewed branching tasks, encoder/reward validation and explicit approval are required")
    if approved is not True:
        raise PermissionError("Explicit synthetic smoke-test opt-in required")
    config.validate()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def evaluate(model, config):
    """Developer validation fixtures only; no final-test loader or files."""
    from .ppo_env import PPOEnv
    env = PPOEnv(encoder=config.encoder(), horizon=config.horizon,
                 episode_seeds=config.validation_seeds,task_suite=config.task_suite,partition="development_validation")
    rows = []
    try:
        for seed in config.validation_seeds:
            observation, _ = env.reset(seed=seed)
            total = 0.0
            while True:
                action, _ = model.predict(observation, deterministic=True)
                observation, reward, terminated, truncated, info = env.step(int(action))
                total += reward
                if terminated or truncated:
                    rows.append({"reset_seed": seed, "episode_seed":env.last_episode_seed, "return": total, **info})
                    break
    finally:
        env.close()
    return {"evidence_kind": "SYNTHETIC_SMOKE_ONLY", "records": rows,
            "scope": "Developer fixture validation only; no independently held-out test or generalization claim"}


def verify_checkpoint(run_dir, filename="policy.zip"):
    """Only trusted locally produced SB3 archives; never load user-uploaded pickle."""
    run = Path(run_dir).resolve(strict=True)
    from .cli import read
    if Path(filename).name != filename or filename not in read(run / "artifacts.json")["files"]:
        raise ValueError("Checkpoint must be a named run artifact")
    path = run / filename
    if path.is_symlink() or _sha(path) != read(run / "artifacts.json")["files"][filename]:
        raise ValueError("Checkpoint checksum mismatch")
    completion = read(run / "completion.json")
    if completion["status"] != "SMOKE_COMPLETED":
        raise ValueError("Only completed smoke checkpoints are eligible")
    if completion["provenance_sha256"] != digest(read(run / "provenance.json")) or completion["artifacts_sha256"] != digest(read(run / "artifacts.json")):
        raise ValueError("Run manifest checksum mismatch")
    return path


class PPOPolicy:
    """Observation-only adapter for synthetic comparison, not final evaluation."""
    evidence_kind = "SYNTHETIC_SMOKE_ONLY"

    def __init__(self, run_dir, *, trusted_local=False):
        if trusted_local is not True:
            raise PermissionError("Only explicitly trusted locally produced SB3 checkpoints may be loaded")
        path = verify_checkpoint(run_dir)
        from .cli import read
        from stable_baselines3 import PPO
        config = read(Path(run_dir) / "provenance.json")["encoder"]
        self.encoder = encoder_from_config(config)
        self.model = PPO.load(path, device="cpu")

    def __call__(self, observation):
        import numpy as np
        vector = np.asarray(self.encoder.encode(observation), dtype=np.float32)
        action, _ = self.model.predict(vector, deterministic=True)
        return int(action)


def smoke(output, config=PPOConfig(), *, approved=False, mode="synthetic-smoke", resume_from=None):
    validate_mode(mode, config, approved)  # Before imports/files; no review bypass.
    # Optional runtime imports: app dependencies and commands remain unchanged.
    import numpy as np
    import torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.logger import configure
    from stable_baselines3.common.monitor import Monitor
    from .ppo_env import PPOEnv
    from .cli import read
    parent, parent_steps = None, 0
    if resume_from is not None:
        checkpoint = verify_checkpoint(resume_from)
        parent = read(Path(resume_from) / "provenance.json")
        parent_steps = read(Path(resume_from) / "completion.json")["timesteps"]
        expected = asdict(config)
        # JSON serializes tuples as lists; compare canonical forms via digest.
        if digest({k:v for k,v in parent["config"].items() if k != "total_timesteps"}) != digest({k:v for k,v in expected.items() if k != "total_timesteps"}):
            raise ValueError("Resume configuration differs from parent")
        if parent["environment"] != config.environment_version() or parent["encoder"] != config.encoder().config() or not parent_steps < config.total_timesteps:
            raise ValueError("Incompatible checkpoint or no remaining smoke budget")
    output = Path(output)
    started = time.perf_counter()
    encoder = config.encoder()
    provenance = {"schema": "ppo-infrastructure-v1", "evidence_kind": "SYNTHETIC_SMOKE_ONLY",
        "config": asdict(config), "encoder": encoder.config(), "environment": config.environment_version(),
        "actions": list(ACTIONS), "policy": "MlpPolicy", "device": "cpu", "threads": 1,
        "source_sha256": digest({p.name: _sha(p) for p in sorted(Path(__file__).parent.glob("*.py"))}),
        "packages": {p: version(p) for p in ("stable-baselines3", "torch", "gymnasium", "numpy")},
        "dataset": "Built-in synthetic task fixtures; no research labels loaded",
        "final_test": "NOT ACCESSED", "started_utc": datetime.now(timezone.utc).isoformat()}
    if parent is not None:
        if parent["source_sha256"] != provenance["source_sha256"] or parent["packages"] != provenance["packages"]:
            raise ValueError("Resume source/runtime mismatch; start a fresh smoke instead")
        provenance["parent_checkpoint_sha256"] = _sha(checkpoint)
        provenance["resume_semantics"] = "Optimizer restored; environment starts fresh episodes, NOT an exact trajectory/RNG resume"
    task_manifest=None
    if config.task_suite=="branching-development-v1":
        from .task_suite import generate
        task_manifest={partition:[{"seed":seed,"task_sha256":digest(task),"provenance":task["provenance"]}
                         for seed in seeds for task in [generate(seed,partition)]]
                       for partition,seeds in (("train",config.train_seeds),("development_validation",config.validation_seeds))}
        provenance["task_manifest_sha256"]=digest(task_manifest)
        provenance["dataset"]="Authored UNREVIEWED branching developer tasks with pinned metadata; no independent final test"
    output.mkdir(parents=True, exist_ok=False)
    write_new(output / "provenance.json", provenance)
    if task_manifest is not None:write_new(output / "task-manifest.json",task_manifest)
    write_new(output / "status-initial.json", {"status": "STARTED", "evidence_kind": "SYNTHETIC_SMOKE_ONLY"})
    env = None
    model = None
    old_threads = torch.get_num_threads()
    old_deterministic = torch.are_deterministic_algorithms_enabled()
    try:
        torch.set_num_threads(1)
        torch.use_deterministic_algorithms(True)
        env = Monitor(PPOEnv(encoder=encoder, horizon=config.horizon, episode_seeds=config.train_seeds,task_suite=config.task_suite),
                      filename=str(output / "episodes.monitor.csv"))
        model = PPO.load(checkpoint, env=env, device="cpu", force_reset=True) if parent is not None else PPO("MlpPolicy", env, learning_rate=config.learning_rate, n_steps=config.n_steps,
            batch_size=config.batch_size, n_epochs=config.n_epochs, gamma=config.gamma,
            gae_lambda=config.gae_lambda, clip_range=config.clip_range, ent_coef=config.ent_coef,
            policy_kwargs={"net_arch": {"pi": list(config.hidden), "vf": list(config.hidden)}},
            seed=config.seed, device="cpu", verbose=0)
        model.set_logger(configure(str(output / "logs"), ["csv", "json"]))
        initial_weights = {name: value.detach().clone() for name,value in model.policy.state_dict().items()}
        checkpoints = []
        episodes = []

        class ArtifactsCallback(BaseCallback):
            def _on_step(self):
                if time.perf_counter()-started > config.wall_time_limit_s:
                    raise TimeoutError("Smoke wall-time budget exceeded")
                for done, info in zip(self.locals["dones"], self.locals["infos"]):
                    if done:
                        episodes.append({"timesteps": self.num_timesteps,
                            **{k:info[k] for k in ("task_success", "unsafe_outcome", "approvals", "blocks", "policy_overrides")}})
                if self.num_timesteps % config.checkpoint_every == 0:
                    filename = f"checkpoint-{self.num_timesteps}.zip"
                    self.model.save(output / filename)
                    checkpoints.append(filename)
                return True

        model.learn(total_timesteps=config.total_timesteps-parent_steps, callback=ArtifactsCallback(),
                    log_interval=1, reset_num_timesteps=parent is None)
        model.logger.dump(step=model.num_timesteps)
        model.logger.close()
        if model.num_timesteps != config.total_timesteps:
            raise RuntimeError("Unexpected training budget")
        changed = any(not torch.equal(initial_weights[name], value) for name,value in model.policy.state_dict().items())
        if not changed:
            raise RuntimeError("Smoke test did not exercise optimizer updates")
        model.save(output / "policy.zip")
        scores = evaluate(model, config)
        write_new(output / "validation-smoke.json", scores)
        write_new(output / "episode-outcomes.json", {"evidence_kind":"SYNTHETIC_SMOKE_ONLY", "records":episodes})
        files = {p.relative_to(output).as_posix(): _sha(p) for p in sorted(output.rglob("*")) if p.is_file()}
        artifact_manifest = {"files": files}
        write_new(output / "artifacts.json", artifact_manifest)
        # Test serialization with a fresh instance, fixed observation, and no more learning.
        restored = PPO.load(output / "policy.zip", device="cpu")
        check_env = PPOEnv(encoder=encoder, episode_seeds=config.validation_seeds,task_suite=config.task_suite,partition="development_validation")
        try:
            observation, _ = check_env.reset(seed=config.validation_seeds[0])
            before, _ = model.predict(observation, deterministic=True)
            after, _ = restored.predict(observation, deterministic=True)
            if not np.array_equal(before, after):
                raise RuntimeError("Reload prediction mismatch")
        finally:
            check_env.close()
        write_new(output / "completion.json", {"status":"SMOKE_COMPLETED", "evidence_kind":"SYNTHETIC_SMOKE_ONLY",
            "timesteps":model.num_timesteps, "weights_updated":changed, "reload_verified":True,
            "wall_time_s":time.perf_counter()-started, "provenance_sha256":digest(provenance),
            "artifacts_sha256":digest(artifact_manifest),
            "claim":"Optimizer/checkpoint infrastructure exercised; no efficacy or generalization conclusion"})
        verify_checkpoint(output)
        return output
    except BaseException as exc:
        if not (output / "completion.json").exists():
            write_new(output / "completion.json", {"status":"INTERRUPTED" if isinstance(exc,KeyboardInterrupt) else "ERROR",
                "evidence_kind":"SYNTHETIC_SMOKE_ONLY", "error_type":type(exc).__name__,
                "claim":"Incomplete run; no valid model-performance results"})
        raise
    finally:
        if model is not None:
            model.logger.close()
        if env is not None:
            env.close()
        torch.set_num_threads(old_threads)
        torch.use_deterministic_algorithms(old_deterministic)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("synthetic-smoke", "research"), default="synthetic-smoke")
    parser.add_argument("--allow-synthetic-smoke", action="store_true")
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=64)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--resume-from")
    parser.add_argument("--task-suite",choices=("foundation-v2","branching-development-v1"),default="foundation-v2")
    parser.add_argument("--encoder",choices=("signed-char-hash-v1","field-position-hash-v1"),default="signed-char-hash-v1")
    args = parser.parse_args(argv)
    try:
        path = smoke(args.output, PPOConfig(seed=args.seed,total_timesteps=args.steps,task_suite=args.task_suite,
                     encoder_version=args.encoder,dimensions=512 if args.encoder=="field-position-hash-v1" else 256),
                     approved=args.allow_synthetic_smoke, mode=args.mode, resume_from=args.resume_from)
        print(f"Synthetic infrastructure check saved to {path}; NOT research evidence")
    except (PermissionError, ValueError, ImportError) as exc:
        parser.exit(2,str(exc)+"\n")


if __name__ == "__main__":
    main()
