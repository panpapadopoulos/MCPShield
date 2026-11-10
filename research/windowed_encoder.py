"""Differentiable, document-level window pooling. Local transformers only."""
import json
from pathlib import Path
import torch
from transformers import AutoModel,AutoTokenizer


class WindowedEncoder(torch.nn.Module):
    def __init__(self,model_path,max_seq_length=256,stride=32,max_chunks=64):
        super().__init__()
        self.model=AutoModel.from_pretrained(str(model_path),local_files_only=True,trust_remote_code=False)
        self.tokenizer=AutoTokenizer.from_pretrained(str(model_path),local_files_only=True,use_fast=True,trust_remote_code=False)
        if not self.tokenizer.is_fast:raise ValueError("Fast tokenizer required for complete overflow mapping")
        limit=self.model.config.max_position_embeddings
        if not 8<=max_seq_length<=limit or not 0<=stride<max_seq_length-2 or max_chunks<1:
            raise ValueError("Invalid tokenizer window budget")
        self.max_seq_length,self.stride,self.max_chunks=max_seq_length,stride,max_chunks

    def tokenize(self,texts):
        encoded=self.tokenizer(texts,padding=True,truncation=True,max_length=self.max_seq_length,
            stride=self.stride,return_overflowing_tokens=True,return_tensors="pt")
        mapping=encoded.pop("overflow_to_sample_mapping")
        counts=torch.bincount(mapping,minlength=len(texts))
        if torch.any(counts>self.max_chunks):raise ValueError("Document exceeds explicit chunk ceiling; nothing silently dropped")
        encoded["document_index"]=mapping
        return dict(encoded)

    def forward(self,features):
        inputs={k:features[k] for k in ("input_ids","attention_mask","token_type_ids") if k in features}
        hidden=self.model(**inputs).last_hidden_state
        mask=features["attention_mask"].unsqueeze(-1).to(hidden.dtype)
        chunks=(hidden*mask).sum(1)/mask.sum(1).clamp(min=1)
        indices=features["document_index"]
        documents=chunks.new_zeros((int(indices.max().item())+1,chunks.shape[1]))
        documents=documents.index_add(0,indices,chunks)
        counts=torch.bincount(indices,minlength=documents.shape[0]).to(documents.dtype).unsqueeze(-1)
        features["sentence_embedding"]=documents/counts.clamp(min=1)
        return features

    def get_sentence_embedding_dimension(self):return self.model.config.hidden_size

    def save(self,output_path,safe_serialization=True,**kwargs):
        root=Path(output_path);root.mkdir(parents=True,exist_ok=True)
        self.model.save_pretrained(root/"transformer",safe_serialization=True)
        self.tokenizer.save_pretrained(root/"transformer")
        (root/"window_config.json").write_text(json.dumps({"max_seq_length":self.max_seq_length,
            "stride":self.stride,"max_chunks":self.max_chunks}),encoding="utf-8")

    @staticmethod
    def load(input_path):
        root=Path(input_path)
        config=json.loads((root/"window_config.json").read_text(encoding="utf-8"))
        return WindowedEncoder(root/"transformer",**config)
