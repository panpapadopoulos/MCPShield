"""Bounded engineering diagnostics, never a scientific PPO experiment."""
from dataclasses import asdict
from collections import Counter
import argparse
import hashlib
from itertools import combinations
from pathlib import Path
from .branching_env import BranchingEnv, RewardWeights
from .task_suite import PARTITIONS, generate, SUITE_VERSION
from .encoding import HashEncoder, FieldHashEncoder, feature_text
from .cli import write_new
from .data import digest


def run(policy,seed,partition,family,user_accepts,weights=None,observations=None):
    env=BranchingEnv(partition=partition,weights=weights)
    obs,_=env.reset(seed=seed,options={"family":family,"user_accepts":user_accepts})
    total=0
    while True:
        if observations is not None:observations.setdefault(digest(obs),obs)
        obs,reward,terminated,truncated,info=env.step(policy(obs))
        assert abs(sum(info["reward_terms"].values())-reward)<1e-9
        total+=reward
        if terminated or truncated:
            assert abs(total-info["total_reward"])<1e-9
            return {"return":total,**info,"provenance":env.task["provenance"]}


def history_reference(observation):
    """Fixture-only sanity controller, NOT a learned detector or scientific baseline.

    Uses only returned phrase fields and actual request permissions. No family,
    node, secret ledger or future events are supplied to it.
    """
    if observation["runtime"]["approval_pending"]:return 0
    current=observation["current"]
    if current["phase"]=="request":
        if current["requested_permissions"]:
            grant=observation["authorized"]["scope"].get(current["tool"],{})
            extra=set(current["requested_permissions"])-set(grant.get("permissions",[]))
            if extra and extra<=set(grant.get("consent_permissions",[])):return 1
        if current["tool"]=="web_search":
            def values(value):
                if isinstance(value,dict):
                    for key,item in value.items():
                        if key in ("phrase","access_phrase","diagnostic_value") and isinstance(item,str):yield item
                        yield from values(item)
                elif isinstance(value,list):
                    for item in value:yield from values(item)
            known=[value for event in observation["history"] for value in values(event.get("response",{}))]
            if any(value in str(current["arguments"].get("query","")) for value in known):return 2
    return 0


def encoder_report(observations):
    old,new=HashEncoder(),FieldHashEncoder()
    rows=[]
    for obs in list(observations)[:32]:
        text=feature_text(obs)
        grams={text[i:i+3] for i in range(len(text)-2)}
        used={int.from_bytes(hashlib.blake2b(t.encode(),digest_size=8).digest()[:4],"little")%old.dimensions for t in grams}
        tokens=set(new.features(obs))
        used_new={int.from_bytes(hashlib.blake2b(t.encode(),digest_size=8).digest()[:4],"little")%(new.dimensions-12) for t in tokens}
        rows.append({"old_distinct_ngrams":len(grams),"old_occupied_buckets":len(used),
            "old_collision_fraction":1-len(used)/len(grams),"new_distinct_field_features":len(tokens),
            "new_occupied_buckets":len(used_new),"new_collision_fraction":1-len(used_new)/len(tokens)})
    from copy import deepcopy
    a=deepcopy(observations[0]);b=deepcopy(a)
    a["current"]["arguments"]={"query":"aaabaa"};b["current"]["arguments"]={"query":"aabaaa"}
    return {"observations_sampled":len(rows),"bucket_diagnostics":rows,
        "known_trigram_order_collision":{"old_vectors_equal":old.encode(a)==old.encode(b),"field_vectors_equal":new.encode(a)==new.encode(b)},
        "scope":"Finite engineering probes only. Neither encoder is proven semantically sufficient; collision fractions are not comparable accuracy scores."}


def validate_suite():
    policies={"always_allow":lambda obs:0,"always_warn":lambda obs:1,"always_block":lambda obs:2,
              "warn_then_resolve":lambda obs:0 if obs["runtime"]["approval_pending"] else 1,
              "history_reference":history_reference}
    weights={"default":RewardWeights(),"larger_harm_cost":RewardWeights(harm=20),
             "lower_approval_cost":RewardWeights(warning=.1)}
    records=[];observations={}
    for name,w in weights.items():
        for partition,families in PARTITIONS.items():
            for family in families:
                for seed in (11,23):
                    for preference in (True,False):
                        for policy_name,policy in policies.items():
                            row=run(policy,seed,partition,family,preference,w,observations)
                            records.append({"weights":name,"policy":policy_name,"seed":seed,
                                            "partition":partition,"family":family,"user_accepts":preference,**row})
    summary={}
    for name in weights:
        summary[name]={}
        for policy in policies:
            rows=[r for r in records if r["weights"]==name and r["policy"]==policy]
            summary[name][policy]={"episodes":len(rows),"task_completions":sum(r["task_success"] for r in rows),
                "unsafe_outcomes":sum(r["unsafe_outcome"] for r in rows),"approvals":sum(r["approvals"] for r in rows),
                "accepted":sum(r["approvals_accepted"] for r in rows),"rejected":sum(r["approvals_rejected"] for r in rows),
                "warning_steps":sum(r["warning_steps"] for r in rows),
                "overrides":sum(r["policy_overrides"] for r in rows),"mean_return":sum(r["return"] for r in rows)/len(rows),
                "truncations":sum(r["truncated"] for r in rows)}
    return {"evidence_kind":"SYNTHETIC_ENVIRONMENT_DIAGNOSTICS","suite":SUITE_VERSION,"human_review":"UNREVIEWED",
        "reward_weights":{k:asdict(v) for k,v in weights.items()},"summary":summary,"records":records,
        "encoder":encoder_report(list(observations.values())),
        "claim":"Checks mechanics and failure modes, not security efficacy or reward optimality; no rewards selected using final-test data"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default=".local/research-phase2/branching-validation-v2.json")
    args=parser.parse_args()
    result=validate_suite();write_new(args.output,result)
    print(f"{len(result['records'])} deterministic synthetic diagnostic episodes; no PPO optimization. Saved {args.output}")


if __name__=="__main__":main()
