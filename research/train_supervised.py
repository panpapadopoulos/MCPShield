"""Readiness and explicitly approved reviewed-data training; no downloads."""
import argparse
from .cli import read
from .supervised import ModelConfig,load_partitions,train


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('dataset','splits','ledger','custody','model','revision','output'):
        parser.add_argument('--'+name,required=True)
    parser.add_argument('--historical',default='data/generated/scenarios-v2.json')
    parser.add_argument('--seed',type=int,default=11)
    parser.add_argument('--max-steps',type=int,default=64)
    parser.add_argument('--approve-reviewed-training',action='store_true')
    args=parser.parse_args()
    dataset,splits,ledger=read(args.dataset),read(args.splits),read(args.ledger)
    historical=read(args.historical)
    if not args.approve_reviewed_training:
        parser.exit(2,'Training not authorized; add the explicit flag only after actual run approval.\n')
    train(dataset,splits,historical,ledger,args.output,args.model,args.revision,
          ModelConfig(seed=args.seed,max_steps=args.max_steps),approved=True,custody_record=read(args.custody))


if __name__=='__main__':main()
