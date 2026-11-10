"""Predeclared representations/plans. No fitting or scientific training."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
from pathlib import Path
from .encoding import HashEncoder,FieldHashEncoder,feature_text
from .branching_env import RewardWeights
from .counterfactuals import VERSION,PARTITIONS,generate_pair
from .data import digest

CONDITIONS=("A_original","B_field","C_field_no_history","D_field_history")


class Representation:
    def __init__(self,condition,dimensions=512):
        if condition not in CONDITIONS:raise ValueError("Unknown representation condition")
        self.condition,self.dimensions=condition,dimensions
        self.base=HashEncoder(dimensions) if condition=="A_original" else FieldHashEncoder(dimensions)

    def project(self,observation):
        result=deepcopy(observation)
        if self.condition=="C_field_no_history":
            result["history"]=[];result["history_omitted"]=0
            if "runtime" in result:
                result["runtime"]["last_approval"]="not_requested"
                result["runtime"]["recoveries_used"]=0
        return result

    def encode(self,observation):return self.base.encode(self.project(observation))

    def config(self):
        return {"version":"representation-ablation-v1","condition":self.condition,"dimensions":self.dimensions,
                "base":self.base.config(),"alias_of":"B_field" if self.condition=="D_field_history" else None}


def sensitivity_plan():
    primary=RewardWeights()
    from dataclasses import replace
    return {"primary":{"weights":asdict(primary),"horizon":24},
        "harm_20":{"weights":asdict(replace(primary,harm=20)),"horizon":24},
        "block_08":{"weights":asdict(replace(primary,block=.8)),"horizon":24},
        "failure_6":{"weights":asdict(replace(primary,failure=6)),"horizon":24},
        "warning_1":{"weights":asdict(replace(primary,warning=1)),"horizon":24},
        "completion_2":{"weights":asdict(replace(primary,success=2)),"horizon":24},
        "horizon_4":{"weights":asdict(primary),"horizon":4}}


def experiment_plan():
    cases=[{"partition":partition,"pair_group":pair,"seed":seed,"sha256":digest(generate_pair(seed,partition,pair))}
           for partition,pairs in PARTITIONS.items() for pair in pairs for seed in (11,23)]
    root=Path(__file__).resolve().parent
    return {"schema":"counterfactual-ablation-plan-v2","dataset_version":VERSION,"environment_version":VERSION,
        "observation_version":"mcp-sequential-observation-v1",
        "environment_source_sha256":digest({name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in
            ("counterfactuals.py","branching_env.py","task_suite.py","authorization.py","observations.py","encoding.py")}),
        "dependency_lock_sha256":hashlib.sha256((root/"requirements-ppo-lock.txt").read_bytes()).hexdigest(),
        "case_manifest":cases,"case_manifest_sha256":digest(cases),
        "representations":{name:Representation(name).config() for name in CONDITIONS},
        "reward_sensitivity":sensitivity_plan(),"proposed_primary":"primary (hypothesis, not selected by performance)",
        "training_seeds":[11,23,37],"training_seed_meaning":"optimizer initialization, not split assignment",
        "episode_seeds":[11,23],"reward_diagnostic_seeds":[11],"user_preferences":[True,False],"training_budget":64,
        "budget_scope":"Technical smoke ceiling only; scientific budget NOT APPROVED",
        "model":{"algorithm":"PPO","network":[32,32],"n_steps":16,"batch_size":16,"n_epochs":2,"device":"cpu",
            "learning_rate":.0003,"gamma":.99,"gae_lambda":.95,"clip_range":.2,"ent_coef":.01,
            "threads":1,"checkpoint_every":16},
        "authorization":"Same research.authorization.enforce gate for all conditions; overrides reported separately",
        "metrics":["task_success","unsafe_outcome","truncated","approvals","warning_steps","policy_overrides","return"],
        "evaluation":"Paired cases, seeds, user preferences and authorization gate identical across representations",
        "training_status":"NOT RUN","human_review":"UNREVIEWED","independent_final_test":"NOT ACCESSED",
        "readiness":"Engineering configurations only; no reviewed research population or scientific run authorization"}
