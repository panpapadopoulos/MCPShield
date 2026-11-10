"""Real optional SetFit backend; synthetic smoke and reviewed runs remain distinct."""
import json
import os
from pathlib import Path
from dataclasses import asdict
from .cli import write_new,read
from .data import digest
from .supervised import LABELS,metrics,tree_hash,packages


def labels_from_predictions(values):
    values=values.tolist() if hasattr(values,"tolist") else list(values)
    result=[]
    for value in values:
        if isinstance(value,str) and value in LABELS:result.append(value)
        elif not isinstance(value,bool) and isinstance(value,int) and 0<=value<len(LABELS):result.append(LABELS[value])
        else:raise ValueError("Unknown classifier prediction")
    return result


def predict(model,texts):return labels_from_predictions(model.predict(texts))


def fit(partitions,destination,snapshot,config,*,evidence_kind,max_steps=None):
    """Called by reviewed-data gate or synthetic integration harness, never auto-downloads."""
    if evidence_kind not in ("REVIEWED_SUPERVISED_RUN","SYNTHETIC_PIPELINE_CHECK"):
        raise ValueError("Explicit evidence scope required")
    os.environ["HF_HUB_OFFLINE"]="1";os.environ["TRANSFORMERS_OFFLINE"]="1"
    import random,numpy as np,torch
    from sentence_transformers import SentenceTransformer
    from sklearn.linear_model import LogisticRegression
    from datasets import Dataset
    from setfit import SetFitModel,Trainer,TrainingArguments
    from .windowed_encoder import WindowedEncoder
    root=Path(destination)
    random.seed(config.seed);np.random.seed(config.seed);torch.manual_seed(config.seed)
    old_threads=torch.get_num_threads();torch.set_num_threads(1)
    old_deterministic=torch.are_deterministic_algorithms_enabled();torch.use_deterministic_algorithms(True)
    try:
        modules=read(Path(snapshot)/"modules.json")
        transformer=next(m for m in modules if m["type"].endswith(".Transformer"))
        model_root=(Path(snapshot)/transformer["path"]).resolve(strict=True)
        if not model_root.is_relative_to(Path(snapshot).resolve()):raise ValueError("Snapshot module escapes local directory")
        encoder=WindowedEncoder(model_root,max_seq_length=config.max_tokens,stride=min(32,config.max_tokens//4))
        body=SentenceTransformer(modules=[encoder],device="cpu")
        model=SetFitModel(model_body=body,model_head=LogisticRegression(C=config.head_c,max_iter=config.max_iter,random_state=config.seed),labels=list(LABELS))
        chunk_stats={}
        for split,rows in partitions.items():
            if set(rows['label'])!=set(LABELS):raise ValueError("Three-class support required")
            counts=[]
            for text in rows['text']:
                features=encoder.tokenize([text]);counts.append(len(features['document_index']))
            chunk_stats[split]={"documents":len(counts),"chunks":sum(counts),"max_chunks":max(counts)}
        training={split:Dataset.from_dict({"text":rows['text'],"label":[LABELS.index(y) for y in rows['label']]}) for split,rows in partitions.items()}
        args=TrainingArguments(output_dir=str(root/"checkpoints"),batch_size=config.batch_size,
            num_epochs=config.epochs,body_learning_rate=config.body_learning_rate,seed=config.seed,
            report_to="none",logging_steps=1,save_strategy="epoch",eval_strategy="no",
            max_steps=config.max_steps if max_steps is None else max_steps,sampling_strategy="unique",show_progress_bar=False)
        # Do not set max_length: our first module owns complete overflow windows.
        trainer=Trainer(model=model,args=args,train_dataset=training['train'],eval_dataset=training['validation'],
            metric=lambda predictions,expected:{"accuracy":float(np.mean(np.asarray(predictions)==np.asarray(expected)))})
        initial={k:v.detach().clone() for k,v in model.model_body.state_dict().items()}
        trainer.train()
        changed=any(not torch.equal(initial[k],v) for k,v in model.model_body.state_dict().items())
        if not changed:raise RuntimeError("Encoder weights did not update")
        model.save_pretrained(str(root/"model"))
        predictions=predict(model,partitions['validation']['text'])
        restored=SetFitModel.from_pretrained(str(root/"model"),local_files_only=True)
        reloaded=predict(restored,partitions['validation']['text'])
        if predictions!=reloaded:raise RuntimeError("SetFit checkpoint prediction mismatch")
        result={"evidence_kind":evidence_kind,"weights_updated":changed,"reload_verified":True,
            "label_order":list(LABELS),"preprocessing":"all-token overlapping windows; mean document embedding, one target per document",
            "chunk_stats":chunk_stats,"predictions":predictions,"labels":partitions['validation']['label'],
            "metrics":metrics(partitions['validation']['label'],predictions),"model_tree_sha256":tree_hash(root/"model"),
            "packages":packages(),"config":asdict(config)}
        write_new(root/"validation.json",result)
        write_new(root/"training-log.json",trainer.st_trainer.state.log_history)
        return result
    finally:
        torch.set_num_threads(old_threads);torch.use_deterministic_algorithms(old_deterministic)


class SavedClassifier:
    def __init__(self,run_dir,*,trusted_local=False):
        if trusted_local is not True:raise PermissionError("Only trusted local classifier checkpoints supported")
        from setfit import SetFitModel
        root=Path(run_dir);completion=read(root/"completion.json")
        if completion['status'] not in ('COMPLETED','SYNTHETIC_PIPELINE_COMPLETED') or tree_hash(root/"model")!=completion['model_tree_sha256']:
            raise ValueError("Classifier incomplete or checksum mismatch")
        self.model=SetFitModel.from_pretrained(str(root/"model"),local_files_only=True)
        self.evidence_kind=read(root/"validation.json")['evidence_kind']
    def __call__(self,observation):
        from .encoding import feature_text
        return LABELS.index(predict(self.model,[feature_text(observation)])[0])
