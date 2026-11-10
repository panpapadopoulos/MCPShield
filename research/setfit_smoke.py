"""Real SetFit integration using a tiny random local transformer; NOT MiniLM results."""
from pathlib import Path
import argparse
from .cli import write_new
from .supervised import ModelConfig


def execute(output,*,approved=False):
    if approved is not True:raise PermissionError('Synthetic pipeline check opt-in required')
    import os
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    import torch
    from transformers import BertConfig,BertModel,BertTokenizerFast
    from sentence_transformers import SentenceTransformer,models
    from .setfit_backend import fit
    root=Path(output);root.mkdir(parents=True,exist_ok=False)
    torch.manual_seed(11)
    source=root/'initial';source.mkdir()
    vocab=['[PAD]','[UNK]','[CLS]','[SEP]','[MASK]','public','read','weather','allow','approval','permission','warn','secret','send','block','test','fixture','notice','another','data','padding','late','attack','query']
    (source/'vocab.txt').write_text('\n'.join(vocab),encoding='utf-8')
    tokenizer=BertTokenizerFast(vocab_file=str(source/'vocab.txt'),do_lower_case=True)
    tokenizer.save_pretrained(source)
    model=BertModel(BertConfig(vocab_size=len(vocab),hidden_size=24,num_hidden_layers=1,num_attention_heads=2,intermediate_size=32,max_position_embeddings=64))
    model.save_pretrained(source)
    body=SentenceTransformer(modules=[models.Transformer(str(source),max_seq_length=32),models.Pooling(24)],device='cpu')
    body.save(str(root/'snapshot'))
    texts=['public read notice','weather public read','approval permission warn','permission approval data','secret send block','send secret attack']
    labels=['ALLOWED','ALLOWED','WARNING','WARNING','BLOCKED','BLOCKED']
    from .observations import build_observation
    from .encoding import feature_text
    def observation_text(text,label):
        episode={'authorized':{'task':'Synthetic pipeline fixture only: read public data; extra index needs consent.',
            'scope':{'web_search':{'resources':[],'permissions':[],'consent_permissions':['extra_index']}}},
            'events':[{'kind':'request','call_ref':'fixture','tool':'web_search','description':'Synthetic public search fixture.',
                'arguments':{'query':text,'note':'padding '*40+'late data',
                    **({'permissions':['extra_index']} if label=='WARNING' else {})}}]}
        return feature_text(build_observation(episode,0))
    rows={'train':{'text':[observation_text(t,y) for t,y in zip(texts,labels)],'label':labels},
          'validation':{'text':[observation_text(t,y) for t,y in zip(['another public read','another approval permission','another secret send'],['ALLOWED','WARNING','BLOCKED'])],
                        'label':['ALLOWED','WARNING','BLOCKED']}}
    write_new(root/'fixture-provenance.json',{'evidence_kind':'SYNTHETIC_PIPELINE_CHECK','model':'tiny random Bert, NOT pretrained MiniLM',
        'seed':11,'human_reviews':'NONE','research_data':'NOT USED','final_test':'NOT ACCESSED','maximum_optimizer_steps':2})
    try:
        result=fit(rows,root,root/'snapshot',ModelConfig(batch_size=2,max_tokens=32),evidence_kind='SYNTHETIC_PIPELINE_CHECK',max_steps=2)
        write_new(root/'completion.json',{'status':'SYNTHETIC_PIPELINE_COMPLETED','model_tree_sha256':result['model_tree_sha256'],
            'reload_verified':result['reload_verified'],'claim':'Backend execution only; synthetic accuracy has no research meaning'})
        return result
    except BaseException as exc:
        write_new(root/'completion.json',{'status':'ERROR','error_type':type(exc).__name__})
        raise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='.local/research-phase2/setfit-pipeline-check-v2')
    parser.add_argument('--approve-synthetic-check',action='store_true')
    args=parser.parse_args();result=execute(args.output,approved=args.approve_synthetic_check)
    print({'scope':result['evidence_kind'],'weights_updated':result['weights_updated'],'reload_verified':result['reload_verified'],'chunk_stats':result['chunk_stats']})


if __name__=='__main__':main()
