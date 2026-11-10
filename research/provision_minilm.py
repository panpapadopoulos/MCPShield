"""Explicit optional ~91MB public model download; never invoked by training."""
import argparse
from pathlib import Path
from .cli import write_new
from .supervised import tree_hash

MODEL='sentence-transformers/all-MiniLM-L6-v2'
REVISION='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
FILES=['config.json','config_sentence_transformers.json','modules.json','sentence_bert_config.json',
       'tokenizer.json','tokenizer_config.json','special_tokens_map.json','vocab.txt','model.safetensors','1_Pooling/config.json','README.md']


def provision(output,*,approved=False):
    if approved is not True:raise PermissionError('Approve the roughly91MB MiniLM download before proceeding')
    root=Path(output)
    if root.exists():raise ValueError('Use a new local snapshot directory')
    from huggingface_hub import snapshot_download
    snapshot_download(MODEL,revision=REVISION,local_dir=str(root),allow_patterns=FILES,token=False)
    write_new(root.parent/(root.name+'-provenance.json'),{'model_id':MODEL,'revision':REVISION,'tree_sha256':tree_hash(root),
        'source':'https://huggingface.co/'+MODEL+'/tree/'+REVISION,'license':'apache-2.0','weight_format':'safetensors only; no alternate exports'})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='.local/models/minilm-pinned')
    parser.add_argument('--approve-download',action='store_true')
    args=parser.parse_args();provision(args.output,approved=args.approve_download)


if __name__=='__main__':main()
