"""Bounded counterfactual/ablation diagnostics; no model fitting or final test."""
from dataclasses import asdict
from pathlib import Path
import argparse
import hashlib
from .ablations import experiment_plan,Representation,CONDITIONS,sensitivity_plan
from .counterfactuals import PARTITIONS,generate_pair,at_pivot,CounterfactualEnv
from .branching_env import RewardWeights
from .cli import write_new
from .data import digest
from .encoding import feature_text


def representation_checks():
    rows=[]
    for partition,pairs in PARTITIONS.items():
        for pair in pairs:
            for seed in (11,23):
                a,expected_a=at_pivot(seed,partition,pair,"legitimate")
                b,expected_b=at_pivot(seed,partition,pair,"unsafe")
                rows.append({"partition":partition,"pair_group":pair,"seed":seed,
                    "proposal":[expected_a,expected_b],"observation_sha256":[digest(a),digest(b)],
                    "representations":{name:{"distinguishes":Representation(name).encode(a)!=Representation(name).encode(b),
                        "feature_sha256":[digest(Representation(name).encode(a)),digest(Representation(name).encode(b))]}
                        for name in CONDITIONS},
                    "B_D_alias_verified":Representation("B_field").encode(a)==Representation("D_field_history").encode(a)})
    return {"status":"SYNTHETIC_REPRESENTATION_CHECKS","rows":rows,
            "scope":"Distinguishability, not a prediction/accuracy or semantic sufficiency result. C intentionally lacks history."}


def rollout(policy,seed,partition,pair,member,user_accepts,weights,horizon):
    env=CounterfactualEnv(partition=partition,weights=weights,horizon=horizon)
    obs,_=env.reset(seed=seed,options={"pair":pair,"member":member,"user_accepts":user_accepts})
    total=0;terms={}
    while True:
        action=policy(obs)
        obs,reward,term,trunc,info=env.step(action)
        total+=reward
        for name,value in info["reward_terms"].items():terms[name]=terms.get(name,0)+value
        if term or trunc:
            assert abs(sum(terms.values())-total)<1e-8 and abs(total-info["total_reward"])<1e-8
            return {"return":total,"reward_totals":terms,**info}


def sensitivity_checks(plan):
    policies={"ALLOW":lambda obs:0,"WARN":lambda obs:1,"BLOCK":lambda obs:2,
        "WARN_RESOLVE":lambda obs:0 if obs["runtime"]["approval_pending"] else 1}
    records=[]
    for name,setting in plan["reward_sensitivity"].items():
        for partition,pairs in PARTITIONS.items():
            for pair in pairs:
                for member in ("legitimate","unsafe"):
                    for preference in (True,False):
                        for policy_name,policy in policies.items():
                            result=rollout(policy,11,partition,pair,member,preference,
                                           RewardWeights(**setting["weights"]),setting["horizon"])
                            records.append({"configuration":name,"partition":partition,"pair_group":pair,
                                "member":member,"user_accepts":preference,"policy":policy_name,**result})
    summary={}
    for name in plan["reward_sensitivity"]:
        summary[name]={}
        for policy in policies:
            rows=[r for r in records if r["configuration"]==name and r["policy"]==policy]
            summary[name][policy]={"episodes":len(rows),"completions":sum(r["task_success"] for r in rows),
                "unsafe_outcomes":sum(r["unsafe_outcome"] for r in rows),"truncations":sum(r["truncated"] for r in rows),
                "approvals":sum(r["approvals"] for r in rows),"warning_steps":sum(r["warning_steps"] for r in rows),
                "authorization_overrides":sum(r["policy_overrides"] for r in rows),"mean_return":sum(r["return"] for r in rows)/len(rows)}
    return {"summary":summary,"records":records,"diagnostic_episode_seed":11,
        "reward_only_selection_permitted":False,
        "note":"A timeout is incomplete, NOT successful attack prevention. Weight/horizon rankings do not establish learned-policy efficacy."}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default=".local/research-phase2/counterfactual-v2")
    args=parser.parse_args(argv)
    root=Path(args.output)
    plan=experiment_plan()
    # Write predeclaration before any diagnostic scoring. Never choose weights from scores.
    write_new(root/"plan.json",plan)
    result={"evidence_kind":"SYNTHETIC_DIAGNOSTICS_ONLY","plan_sha256":digest(plan),
        "source_sha256":digest({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))}),
        "representation":representation_checks(),"sensitivity":sensitivity_checks(plan),
        "training":"NOT RUN","human_review":"UNREVIEWED","independent_final_test":"NOT ACCESSED"}
    write_new(root/"diagnostics.json",result)
    write_new(root/"artifacts.json",{"plan_sha256":digest(plan),"diagnostics_sha256":digest(result)})
    print(f"12 matched pair instances; {len(result['sensitivity']['records'])} deterministic policy/weight diagnostics. No training. Saved {root}")


if __name__=="__main__":main()
