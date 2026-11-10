"""Approved development comparison/export and read-only dashboard artifact adapter."""
import argparse
from copy import deepcopy
from pathlib import Path
import hashlib
from .cli import read,write_new
from .data import digest
from .five_methods import METHODS,VERSION

SCHEMA='research-dashboard-v1'


def dashboard(path):
    result={'schema':SCHEMA,'evidence_kind':'PENDING','independent_validation':'NOT PERFORMED',
        'version':VERSION,'methods':{m:{'status':'NOT RUN','reason':'No published compatible evaluation artifact'} for m in METHODS}}
    if not Path(path).exists():return result
    envelope=read(path)
    if envelope.get('schema')!=SCHEMA or envelope.get('evidence_kind')!='DEVELOPMENT_ONLY':raise ValueError('Unsupported evidence envelope')
    comparison=envelope['comparison']
    if digest(comparison)!=envelope['comparison_sha256'] or comparison.get('version')!=VERSION:raise ValueError('Artifact hash/version mismatch')
    if envelope.get('models',{})!=comparison.get('experiment_provenance',{}).get('models',{}):raise ValueError('Model identities disagree with hashed provenance')
    if set(comparison['methods'])!=set(METHODS):raise ValueError('Five methods required')
    result.update(evidence_kind='DEVELOPMENT_ONLY',comparison_sha256=envelope['comparison_sha256'],
        allocation_sha256=comparison['case_allocation_sha256'],provenance=comparison['experiment_provenance'])
    for name,row in comparison['methods'].items():
        if row['status'] not in ('RUN','NOT RUN','ERROR'):raise ValueError('Invalid method status')
        if row['status']!='RUN':
            result['methods'][name]={'status':row['status'],'reason':row.get('reason','No valid result')};continue
        model=envelope.get('models',{}).get(name,{})
        if name in ('setfit','ppo','pretrained_qwen'):
            identity=model.get('sha256','')
            if len(identity)!=64 or any(c not in '0123456789abcdef' for c in identity):
                result['methods'][name]={'status':'NOT RUN','reason':'Missing verified model/checkpoint identity'};continue
            if name=='setfit' and model.get('evidence_kind')!='REVIEWED_SUPERVISED_RUN':
                result['methods'][name]={'status':'NOT RUN','reason':'No completed reviewed-data SetFit checkpoint'};continue
        result['methods'][name]={'status':'RUN','summary':deepcopy(row['summary']),
            'security_utility':deepcopy(row['security_utility']),'model_identity':model}
    return result


def compare(output,*,approved=False,setfit_run=None,ppo_run=None,ppo_seed=11,include_qwen=False):
    if approved is not True:raise PermissionError('Explicit development comparison approval required')
    if Path(output).exists():raise ValueError('Use a new output artifact')
    from .five_methods import compare_episodes,ContextQwen
    from .branching_env import BranchingEnv
    from .ppo_next import protocol,bank
    providers={};models={}
    if setfit_run:
        from .setfit_backend import SavedClassifier
        classifier=SavedClassifier(setfit_run,trusted_local=True)
        if classifier.evidence_kind!='REVIEWED_SUPERVISED_RUN':raise ValueError('Synthetic classifier cannot enter this comparison')
        providers['setfit']=classifier
        models['setfit']={'sha256':read(Path(setfit_run)/'completion.json')['model_tree_sha256'],'evidence_kind':classifier.evidence_kind,
            'training_provenance_sha256':digest(read(Path(setfit_run)/'provenance.json'))}
    if ppo_run:
        if ppo_seed not in (11,23,37):raise ValueError('Choose a predefined seed, not a validation-selected best seed')
        import numpy as np,torch
        from stable_baselines3 import PPO
        from .encoding import FieldHashEncoder
        root=Path(ppo_run);completion=read(root/'completion.json')
        if completion['status']!='COMPLETED_DEVELOPMENT_ONLY' or read(root/'protocol.json')!=protocol():raise ValueError('Incompatible PPO protocol')
        checkpoint=root/str(ppo_seed)/'policy.zip'
        sha=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        if sha!=read(root/str(ppo_seed)/'results.json')['checkpoint_sha256']:raise ValueError('PPO checkpoint hash mismatch')
        torch.set_num_threads(1)
        model=PPO.load(checkpoint,device='cpu');encoder=FieldHashEncoder()
        if model.num_timesteps!=protocol()['steps_per_seed'] or model.observation_space.shape!=(encoder.dimensions,) or model.action_space.n!=3:
            raise ValueError('PPO checkpoint budget/observation/action contract mismatch')
        providers['ppo']=lambda obs:int(model.predict(np.asarray(encoder.encode(obs),dtype=np.float32),deterministic=True)[0])
        models['ppo']={'sha256':sha,'seed':ppo_seed,'evidence_kind':'TRAINED_SYNTHETIC_DEVELOPMENT_ONLY',
            'selection':'Explicit predefined seed; no ranking or tuning performed'}
    if include_qwen:
        from urllib.request import urlopen
        from urllib.parse import urlparse
        qwen=ContextQwen();base=urlparse(qwen.client.base)
        # Query actual local Ollama identity; never guess a checkpoint digest.
        import json
        with urlopen(base.scheme+'://'+base.netloc+'/api/tags',timeout=10) as response:tags=json.load(response)
        matches=[m for m in tags['models'] if m.get('name')==qwen.client.model or m.get('model')==qwen.client.model]
        if len(matches)!=1:raise ValueError('Exact local Qwen model identity unavailable')
        models['pretrained_qwen']={'sha256':matches[0]['digest'].removeprefix('sha256:'),'prompt':qwen.provenance}
        providers['pretrained_qwen']=qwen
    p=protocol()
    cases=[{'factory':lambda:BranchingEnv(partition='development_validation'),'seed':c['seed'],
        'options':{'family':c['family'],'user_accepts':c['user_accepts']}} for c in bank('development_validation',p)]
    comparison=compare_episodes(cases,providers,allow_model_calls=True,provenance={
        'scope':'Fixed synthetic branching development validation; NOT the independently reviewed boundary dataset or final test',
        'models':models,'protocol_sha256':digest(p),'human_reviews':'NOT ASSERTED',
        'distribution_shift':'SetFit boundary training versus sequential simulator observations must be reported',
        'final_test':'NOT ACCESSED'})
    envelope={'schema':SCHEMA,'evidence_kind':'DEVELOPMENT_ONLY','models':models,
        'comparison':comparison,'comparison_sha256':digest(comparison)}
    # write_new never overwrites earlier results; validate the published envelope.
    write_new(output,envelope)
    dashboard(output)
    return envelope


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--setfit-run');parser.add_argument('--ppo-run')
    parser.add_argument('--ppo-seed',type=int,default=11);parser.add_argument('--include-qwen',action='store_true')
    parser.add_argument('--approve-development-comparison',action='store_true')
    args=parser.parse_args()
    compare(args.output,approved=args.approve_development_comparison,setfit_run=args.setfit_run,
        ppo_run=args.ppo_run,ppo_seed=args.ppo_seed,include_qwen=args.include_qwen)


if __name__=='__main__':main()
