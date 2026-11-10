"""One predefined CPU development protocol. Writes/preflights by default; never auto-runs."""
from dataclasses import asdict
from pathlib import Path
import argparse
import hashlib
import random
import time
from .cli import read,write_new
from .data import digest
from .branching_env import RewardWeights
from .task_suite import PARTITIONS,generate


def protocol():
    return {'version':'bounded-ppo-development-v2','purpose':'DEVELOPMENT_ONLY_NOT_SCIENTIFIC',
        'optimizer_seeds':[11,23,37],'steps_per_seed':10240,'total_steps':30720,'wall_seconds_per_seed':900,
        'suite':'branching-development-v1','encoder':{'version':'field-position-hash-v1','dimensions':512,'position_bins':8},
        'network':[32,32],'n_steps':128,'batch_size':64,'n_epochs':4,'learning_rate':.0003,
        'gamma':.99,'gae_lambda':.95,'clip_range':.2,'ent_coef':.01,'horizon':24,'threads':1,
        'rewards':asdict(RewardWeights()),'approval_protocol':'shared automatic receive pending response; same for all five methods',
        'train_episode_seeds':[101,103,107],'development_validation_seeds':[211,223,227],
        'train_families':list(PARTITIONS['train']),'development_validation_families':list(PARTITIONS['development_validation']),
        'sampler':'seed-shuffled cyclic family x episode-seed x approval-preference bank',
        'training_family_sampling_weights':{'public_report':3,'split_directive':1,'poisoned_catalog':1,'permission_escalation':1},
        'sampling_note':'Reweights existing tasks, not additional independent examples; no claimed human labels',
        'constants':['ALLOW','WARN','BLOCK'],'reward_selection':'primary unchanged, no parameter search',
        'review_status':'UNREVIEWED','final_test':'NOT ACCESSED','status':'PROPOSED_NOT_RUN',
        'scientific_training':'DISABLED; reviewed protocol/tasks and separate authorization still required'}


def bank(partition,p):
    seeds=p['train_episode_seeds'] if partition=='train' else p['development_validation_seeds']
    return [{'partition':partition,'family':family,'seed':seed,'user_accepts':preference}
        for family in PARTITIONS[partition] for seed in seeds for preference in (True,False)]


def preflight(p):
    if p!=protocol():raise ValueError('Only the single predefined protocol is supported')
    if set(p['train_episode_seeds'])&set(p['development_validation_seeds']):raise ValueError('Seed overlap')
    if set(p['train_families'])&set(p['development_validation_families']):raise ValueError('Family overlap')
    manifest={}
    for split in ('train','development_validation'):
        manifest[split]=[{'case':case,'task_sha256':digest(generate(case['seed'],split,case['family']))} for case in bank(split,p)]
    return manifest


def run(p,output,*,approved=False):
    if approved is not True:raise PermissionError('Explicit approval for the proposed 30,720-step development run required')
    manifest=preflight(p)
    import numpy as np,torch
    from stable_baselines3 import PPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.logger import configure
    from .ppo_env import PPOEnv
    from .encoding import FieldHashEncoder
    from .five_methods import compare_episodes
    from .branching_env import BranchingEnv
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    write_new(root/'protocol.json',p);write_new(root/'task-manifest.json',manifest)
    write_new(root/'source.json',{'sha256':digest({f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(Path(__file__).parent.glob('*.py'))})})
    old_threads=torch.get_num_threads();torch.set_num_threads(1)
    try:
        validation_cases=[{'factory':lambda:BranchingEnv(partition='development_validation'),'seed':c['seed'],
            'options':{'family':c['family'],'user_accepts':c['user_accepts']}} for c in bank('development_validation',p)]
        constants={}
        for name,action in (('ALLOW',0),('WARN',1),('BLOCK',2)):
            result=compare_episodes(validation_cases,{'ppo':lambda obs,a=action:a},allow_model_calls=True)
            constants[name]=result['methods']['ppo']
        write_new(root/'constant-policies.json',{'kind':'CONSTANT_POLICIES_NOT_TRAINED_MODELS','results':constants})
        reports=[]
        for seed in p['optimizer_seeds']:
            destination=root/str(seed);destination.mkdir();started=time.perf_counter()
            class TrainingEnv(PPOEnv):
                def __init__(self):
                    super().__init__(encoder=FieldHashEncoder(),horizon=24,task_suite=p['suite'])
                    self.cases=[case for case in bank('train',p) for _ in range(p['training_family_sampling_weights'][case['family']])]
                    random.Random(seed).shuffle(self.cases);self.index=0
                def reset(self,*,seed=None,options=None):
                    case=self.cases[self.index%len(self.cases)];self.index+=1
                    obs,info=self.engine.reset(seed=case['seed'],options={'family':case['family'],'user_accepts':case['user_accepts']})
                    return self._encode(obs),info
                def step(self,action):
                    family=self.engine.task['provenance']['family']
                    obs,reward,term,trunc,info=super().step(action)
                    if not term and not trunc and self.engine.pending:
                        obs,extra,term,trunc,info=super().step(0);reward+=extra
                    info['task_family']=family
                    return obs,reward,term,trunc,info
            env=TrainingEnv();model=None
            try:
                model=PPO('MlpPolicy',env,seed=seed,device='cpu',n_steps=p['n_steps'],batch_size=p['batch_size'],n_epochs=p['n_epochs'],
                    learning_rate=p['learning_rate'],gamma=p['gamma'],gae_lambda=p['gae_lambda'],clip_range=p['clip_range'],ent_coef=p['ent_coef'],
                    policy_kwargs={'net_arch':{'pi':p['network'],'vf':p['network']}},verbose=0)
                model.set_logger(configure(str(destination/'logs'),['csv','json']))
                class Budget(BaseCallback):
                    def _on_step(self):
                        if time.perf_counter()-started>p['wall_seconds_per_seed']:raise TimeoutError('Per-seed budget')
                        if self.num_timesteps%2048==0:self.model.save(destination/f'checkpoint-{self.num_timesteps}.zip')
                        return True
                model.learn(total_timesteps=p['steps_per_seed'],callback=Budget());model.save(destination/'policy.zip')
                model.logger.dump(step=model.num_timesteps)
                encoder=FieldHashEncoder()
                def policy(obs):return int(model.predict(np.asarray(encoder.encode(obs),dtype=np.float32),deterministic=True)[0])
                evaluation=compare_episodes(validation_cases,{'ppo':policy},allow_model_calls=True)
                result={'seed':seed,'timesteps':model.num_timesteps,'evaluation':evaluation,'evidence_kind':p['purpose'],
                    'checkpoint_sha256':hashlib.sha256((destination/'policy.zip').read_bytes()).hexdigest()}
                write_new(destination/'results.json',result);reports.append(result)
            finally:
                if model is not None:model.logger.close()
                env.close()
        write_new(root/'completion.json',{'status':'COMPLETED_DEVELOPMENT_ONLY','protocol_sha256':digest(p),'results_sha256':digest(reports)})
    except BaseException as exc:
        write_new(root/'completion.json',{'status':'ERROR_OR_INTERRUPTED','error_type':type(exc).__name__});raise
    finally:torch.set_num_threads(old_threads)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write-protocol');parser.add_argument('--run-protocol');parser.add_argument('--output')
    parser.add_argument('--approve-bounded-development',action='store_true')
    args=parser.parse_args()
    if args.write_protocol:
        p=protocol();preflight(p);write_new(args.write_protocol,p);print('Protocol prepared; training NOT RUN')
    elif args.run_protocol and args.output:run(read(args.run_protocol),args.output,approved=args.approve_bounded_development)
    else:parser.error('Write a protocol, or supply run protocol and fresh output with explicit approval')


if __name__=='__main__':main()
