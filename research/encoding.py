"""Shared, deterministic feature hashing; no learned vocabulary or model downloads."""
from dataclasses import dataclass, asdict
import hashlib
import math
from .observations import canonical, authorized_task, OBSERVATION_VERSION, SEQUENTIAL_OBSERVATION_VERSION


def feature_text(observation):
    """Project only observable fields, never labels/info or caller-added metadata."""
    if observation.get("schema") not in (OBSERVATION_VERSION,SEQUENTIAL_OBSERVATION_VERSION):
        raise ValueError("A versioned observation is required, not a dataset row")

    def boundary(item):
        if item["phase"] not in ("request", "response") or not isinstance(item["arguments"], dict):
            raise ValueError("Invalid observation boundary")
        result = {k: item[k] for k in ("phase", "tool", "description", "arguments", "requested_permissions")}
        if item["phase"] == "response":
            result["response"] = item["response"]
        return result

    result={"schema": observation["schema"], "authorized": authorized_task(observation["authorized"]),
                      "current": boundary(observation["current"]),
                      "history": [boundary(item) for item in observation["history"]],
                      "history_omitted": observation["history_omitted"]}
    if observation["schema"]==SEQUENTIAL_OBSERVATION_VERSION:
        runtime=observation["runtime"]
        if type(runtime["approval_pending"]) is not bool or runtime["last_approval"] not in ("not_requested","pending","approved","rejected","cancelled") or any(type(runtime[k]) is not int or runtime[k]<0 for k in ("steps_remaining","recoveries_used")):
            raise ValueError("Invalid observable runtime state")
        result["runtime"]={k:runtime[k] for k in ("approval_pending","last_approval","steps_remaining","recoveries_used")}
    return canonical(result)


@dataclass(frozen=True)
class HashEncoder:
    dimensions: int = 256
    ngram: int = 3
    version: str = "signed-char-hash-v1"

    def __post_init__(self):
        if type(self.dimensions) is not int or not 16 <= self.dimensions <= 4096 or self.ngram not in (2, 3, 4):
            raise ValueError("Invalid hashing configuration")

    def config(self):
        return asdict(self)

    def encode(self, observation):
        text = feature_text(observation)
        vector = [0.0] * self.dimensions
        for i in range(max(1, len(text) - self.ngram + 1)):
            hashed = hashlib.blake2b(text[i:i+self.ngram].encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(hashed[:4], "little") % self.dimensions
            vector[index] += 1 if hashed[4] & 1 else -1
        norm = math.sqrt(sum(x*x for x in vector)) or 1
        return [x / norm for x in vector]


@dataclass(frozen=True)
class FieldHashEncoder:
    """Field and position-aware hashing plus explicit observable context slots.

    No attack keywords or labels. Improves known order-loss cases; collisions
    remain inevitable and semantic sufficiency is NOT established.
    """
    dimensions: int = 512
    position_bins: int = 8
    version: str = "field-position-hash-v1"

    def __post_init__(self):
        if type(self.dimensions) is not int or not 32<=self.dimensions<=4096 or self.position_bins!=8:
            raise ValueError("Invalid field encoder configuration")

    def config(self):return asdict(self)

    def features(self,observation):
        import json
        data=json.loads(feature_text(observation))
        def walk(value,path):
            if isinstance(value,dict):
                for key in sorted(value):yield from walk(value[key],path+"/"+key)
            elif isinstance(value,list):
                for i,item in enumerate(value):yield from walk(item,path+"/"+str(i))
            else:
                text=str(value).casefold()
                count=max(1,len(text)-2)
                for i in range(count):
                    yield path+":"+str(min(7,i*8//count))+":"+text[i:i+3]
        return list(walk(data,""))

    def encode(self,observation):
        vector=[0.0]*self.dimensions
        for token in self.features(observation):
            hashed=hashlib.blake2b(token.encode(),digest_size=8).digest()
            vector[int.from_bytes(hashed[:4],"little")%(self.dimensions-12)]+=1 if hashed[4]&1 else -1
        norm=math.sqrt(sum(x*x for x in vector)) or 1
        vector=[x/norm for x in vector]
        current=observation["current"];runtime=observation.get("runtime",{})
        grant=observation["authorized"]["scope"].get(current["tool"],{})
        vector[-12:]=[float(current["phase"]=="request"),float(current["phase"]=="response"),
            float(runtime.get("approval_pending",False)),min(1,runtime.get("steps_remaining",0)/24),
            min(1,len(observation["history"])/8),min(1,len(current["requested_permissions"])/4),
            min(1,len(grant.get("permissions",[]))/4),float(bool(grant)),
            float(runtime.get("last_approval")=="approved"),float(runtime.get("last_approval")=="rejected"),
            min(1,runtime.get("recoveries_used",0)/4),min(1,observation["history_omitted"]/8)]
        return vector


def encoder_from_config(config):
    if config.get("version")=="representation-ablation-v1":
        from .ablations import Representation
        encoder=Representation(config["condition"],config["dimensions"])
        if encoder.config()!=config:raise ValueError("Ablation configuration mismatch")
        return encoder
    factories={"signed-char-hash-v1":HashEncoder,"field-position-hash-v1":FieldHashEncoder}
    if config.get("version") not in factories:raise ValueError("Unknown encoder version")
    return factories[config["version"]](**config)
