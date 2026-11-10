"""Approved short CPU PPO development ablation. Never final scientific evidence."""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime,timezone
from importlib.metadata import version
from pathlib import Path
import hashlib
import random
import time
from .cli import read,write_new
from .data import digest
from .ablations import experiment_plan,Representation
from .counterfactuals import PARTITIONS,CounterfactualEnv,at_pivot,VERSION

EVIDENCE="TRAINED_SYNTHETIC_DEVELOPMENT_ONLY"


def cases(partition):
    return [{"partition":partition,"pair":pair,"member":member,"seed":seed,"user_accepts":preference}
            for pair in PARTITIONS[partition] for member in ("legitimate","unsafe")
            for seed in (11,23) for preference in (True,False)]


def summarize(records,probes):
    if not records or not probes:raise ValueError("Paired episode and fixed-pivot records required")
    legit=[r for r in records if r["case"]["member"]=="legitimate"]
    unsafe=[r for r in records if r["case"]["member"]=="unsafe"]
    negatives=[r for r in probes if r["member"]=="legitimate"]
    divide=lambda a,b:a/b if b else None
    return {"episodes":len(records),"legitimate_episodes":len(legit),
        "legitimate_completions":sum(r["task_success"] for r in legit),
        "legitimate_task_completion_rate":divide(sum(r["task_success"] for r in legit),len(legit)),
        "unsafe_outcomes":sum(r["unsafe_outcome"] for r in records),
        "unsafe_member_outcome_rate":divide(sum(r["unsafe_outcome"] for r in unsafe),len(unsafe)),
        "provisional_pivot_false_positives":sum(r["action"]!=0 for r in negatives),
        "provisional_pivot_negatives":len(negatives),
        "provisional_pivot_false_positive_rate":divide(sum(r["action"]!=0 for r in negatives),len(negatives)),
        "legitimate_episode_interventions":sum(r["policy_interventions"]>0 for r in legit),
        "warning_steps":sum(r["warning_steps"] for r in records),
        "warning_frequency":divide(sum(r["warning_steps"] for r in records),sum(r["steps"] for r in records)),
        "approval_requests":sum(r["approvals"] for r in records),
        "authorization_overrides":sum(r["policy_overrides"] for r in records),
        "truncations":sum(r["truncated"] for r in records),
        "mean_reward":sum(r["return"] for r in records)/len(records),
        "false_positive_scope":"Non-ALLOW recommendation on fixed legitimate pivot probes; authored UNREVIEWED targets, NOT independent FPR"}


def evaluate(policy):
    records=[];probes=[]
    for case in cases("development_validation"):
        env=CounterfactualEnv(partition=case["partition"])
        obs,_=env.reset(seed=case["seed"],options={"pair":case["pair"],"member":case["member"],"user_accepts":case["user_accepts"]})
        total=0;interventions=0
        while True:
            action=int(policy(deepcopy(obs)));interventions+=action!=0
            obs,reward,term,trunc,info=env.step(action);total+=reward
            if term or trunc:
                records.append({"case":case,"return":total,"policy_interventions":interventions,**info});break
    for pair in PARTITIONS["development_validation"]:
        for seed in (11,23):
            for member in ("legitimate","unsafe"):
                obs,proposal=at_pivot(seed,"development_validation",pair,member)
                probes.append({"pair":pair,"seed":seed,"member":member,"proposed":proposal,"action":int(policy(obs)),
                    "observation_sha256":digest(obs)})
    return {"evidence_kind":EVIDENCE,"records":records,"fixed_pivot_probes":probes,"summary":summarize(records,probes)}


def execute(output,*,approved=False):
    if approved is not True:raise PermissionError("Explicit approval for this bounded development ablation required")
    plan=read(".local/research-phase2/counterfactual-v2/plan.json")
    if digest(plan)!=digest(experiment_plan()):raise ValueError("Architecture/configuration differs from the frozen plan")
    if plan["training_budget"]!=64:raise ValueError("Only the approved fixed64-step budget is supported")
    import numpy as np
    import torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.logger import configure
    from .counterfactual_gym import CounterfactualGymEnv
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    write_new(root/"frozen-plan.json",plan)
    protocol={"evidence_kind":EVIDENCE,"plan_sha256":digest(plan),"deadline":"2026-11-23",
        "conditions":["A_original","B_field","C_field_no_history"],"alias":{"D_field_history":"B_field"},
        "sampler":"Seed-shuffled cyclic training case bank; order matched per optimizer seed, trajectories action-dependent",
        "training_cases":cases("train"),"evaluation_cases":cases("development_validation"),
        "seeds":plan["training_seeds"],"steps_per_model":64,"total_step_ceiling":576,
        "wall_time_ceiling_s":180,"threads":1,"packages":{p:version(p) for p in ("torch","stable-baselines3","gymnasium","numpy")},
        "source_sha256":digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))}),
        "false_positives":"Fixed-pivot non-ALLOW proposals on legitimate members, separately from on-policy episode interventions",
        "independent_final_test":"NOT ACCESSED","human_reviews":"NOT USED; authored synthetic semantics only",
        "started_utc":datetime.now(timezone.utc).isoformat()}
    write_new(root/"protocol.json",protocol)
    started=time.perf_counter();old_threads=torch.get_num_threads();old_deterministic=torch.are_deterministic_algorithms_enabled()
    results={};checkpoint_hashes={};env=None;model=None
    try:
        torch.set_num_threads(1);torch.use_deterministic_algorithms(True)
        for condition in protocol["conditions"]:
            results[condition]=[]
            for seed in protocol["seeds"]:
                if time.perf_counter()-started>180:raise TimeoutError("Development ablation wall-time ceiling")
                destination=root/condition/str(seed);destination.mkdir(parents=True)
                class TrainingBank(CounterfactualGymEnv):
                    def __init__(self):
                        super().__init__(condition,partition="train",horizon=24)
                        self.bank=cases("train");random.Random(seed).shuffle(self.bank)
                        self.index=0;self.assigned=[]
                    def reset(self,*,seed=None,options=None):
                        case=self.bank[self.index%len(self.bank)];self.index+=1;self.assigned.append(case)
                        observation,info=self.engine.reset(seed=case["seed"],options={"pair":case["pair"],"member":case["member"],"user_accepts":case["user_accepts"]})
                        return self._encode(observation),info
                env=TrainingBank();m=plan["model"]
                model=PPO("MlpPolicy",env,seed=seed,device="cpu",learning_rate=m["learning_rate"],
                    n_steps=m["n_steps"],batch_size=m["batch_size"],n_epochs=m["n_epochs"],gamma=m["gamma"],
                    gae_lambda=m["gae_lambda"],clip_range=m["clip_range"],ent_coef=m["ent_coef"],
                    policy_kwargs={"net_arch":{"pi":m["network"],"vf":m["network"]}},verbose=0)
                model.set_logger(configure(str(destination/"logs"),["csv","json"]))
                initial={k:v.detach().clone() for k,v in model.policy.state_dict().items()}
                class Budget(BaseCallback):
                    def _on_step(self):
                        if self.num_timesteps>64 or time.perf_counter()-started>180:raise TimeoutError("Approved budget exceeded")
                        if self.num_timesteps%16==0:self.model.save(destination/f"checkpoint-{self.num_timesteps}.zip")
                        return True
                model.learn(total_timesteps=64,callback=Budget(),log_interval=1)
                model.logger.dump(step=64);model.logger.close()
                if model.num_timesteps!=64:raise ValueError("Training budget mismatch")
                changed=any(not torch.equal(initial[k],v) for k,v in model.policy.state_dict().items())
                if not changed:raise ValueError("No optimizer update occurred")
                model.save(destination/"policy.zip")
                restored=PPO.load(destination/"policy.zip",device="cpu")
                encoder=Representation(condition)
                def policy(obs):
                    vector=np.asarray(encoder.encode(obs),dtype=np.float32)
                    action,_=restored.predict(vector,deterministic=True);return int(action)
                probe,_=at_pivot(11,"development_validation","terminology","legitimate")
                vector=np.asarray(encoder.encode(probe),dtype=np.float32)
                if int(model.predict(vector,deterministic=True)[0])!=policy(probe):raise ValueError("Reload mismatch")
                evaluation=evaluate(policy)
                record={"seed":seed,"timesteps":64,"weights_updated":changed,"reload_verified":True,
                    "training_assignments":env.assigned,"unique_assigned_cases":len({digest(c) for c in env.assigned}),
                    "evaluation":evaluation}
                write_new(destination/"results.json",record);results[condition].append(record)
                checkpoint_hashes[f"{condition}/{seed}/policy.zip"]=hashlib.sha256((destination/"policy.zip").read_bytes()).hexdigest()
                env.close();env=None;model=None
        results["D_field_history"]={"alias_of":"B_field","reason":"Identical representation; reuses trained models/predictions, no independent replication"}
        constants={name:evaluate(lambda obs,action=action:action) for name,action in (("ALLOW",0),("WARN",1),("BLOCK",2))}
        summary={}
        for name,rows in results.items():
            if name=="D_field_history":continue
            summary[name]={key:sum(r["evaluation"]["summary"][key] for r in rows)/len(rows)
                for key in ("legitimate_task_completion_rate","unsafe_outcomes","unsafe_member_outcome_rate",
                    "provisional_pivot_false_positive_rate","warning_frequency","truncations","mean_reward")}
        report={"status":"COMPLETED_DEVELOPMENT_ONLY","evidence_kind":EVIDENCE,"results":results,"mean_across_optimizer_seeds":summary,
            "constants":constants,"protocol_sha256":digest(protocol),"checkpoints":checkpoint_hashes,
            "optimizer_steps_total":576,"wall_time_s":time.perf_counter()-started,
            "claim":"Actual trained synthetic development policies; no independent validation or generalization claim"}
        write_new(root/"report.json",report)
        write_new(root/"completion.json",{"status":report["status"],"report_sha256":digest(report),"optimizer_steps_total":576})
        return report
    except BaseException as exc:
        write_new(root/"completion.json",{"status":"INTERRUPTED" if isinstance(exc,KeyboardInterrupt) else "ERROR","error_type":type(exc).__name__,
            "claim":"Incomplete ablation; no complete aggregate results"})
        raise
    finally:
        if model is not None:model.logger.close()
        if env is not None:env.close()
        torch.set_num_threads(old_threads);torch.use_deterministic_algorithms(old_deterministic)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-development-diagnostics",action="store_true")
    parser.add_argument("--output",default=".local/research-phase2/trained-development-ablation-v1")
    args=parser.parse_args();report=execute(args.output,approved=args.approve_development_diagnostics)
    import json
    print(json.dumps({"trained":report["mean_across_optimizer_seeds"],"constants":{k:v["summary"] for k,v in report["constants"].items()},"wall_time_s":report["wall_time_s"]},indent=2))


if __name__=="__main__":main()
