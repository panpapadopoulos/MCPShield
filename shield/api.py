"""Local research API. All tool activity is simulated; approvals resume exact state."""
from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
import hmac
import json
import os
from pathlib import Path
import secrets
from threading import RLock, Lock
from time import monotonic
from typing import Any, Literal, Optional
from urllib.parse import urlparse
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ConfigDict, StrictBool
from .core import Decision
from .dataset import load_cases, statistics
from .detectors import detector, LLM
from .experiments import run_experiment
from .simulation import Agent

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="MCPShield", version="0.2.0")
app.add_middleware(TrustedHostMiddleware, allowed_hosts=os.getenv("MCPSHIELD_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(","))
lock = RLock()
evaluation_lock = Lock()
sessions = {}
activity = deque(maxlen=500)
latest_report = None
sequence = 0
TTL = 300

@app.middleware("http")
async def request_boundary(request: Request, call_next):
    origin = request.headers.get("origin")
    if origin and urlparse(origin).netloc != request.headers.get("host"):
        from fastapi.responses import JSONResponse
        return JSONResponse({"detail": "Cross-origin access is disabled"},status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'"
    return response

def authorize(authorization: Optional[str] = Header(None)):
    expected = os.getenv("MCPSHIELD_API_TOKEN", "")
    if expected and not hmac.compare_digest(authorization or "", "Bearer " + expected):
        raise HTTPException(401,"Valid bearer token required")

class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario_id: str = Field(max_length=100)
    method: Literal["no_defense","rules","llm","hybrid"] = "rules"

class ApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    approval_id: str = Field(max_length=100)
    approved: StrictBool

class EvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    repeats: int = Field(default=3,ge=1,le=5)
    include_llm: bool = False
    split: Literal["test","validation","all"] = "test"

def configured_llm():
    try:
        return LLM()
    except (ValueError, TypeError):
        raise HTTPException(503,"Invalid classifier endpoint or timeout configuration")

def cases():
    try:
        return load_cases()
    except (FileNotFoundError, ValueError):
        raise HTTPException(503,"Generate dataset first: python -m shield.dataset")

def add_event(session, checkpoint):
    global sequence
    sequence += 1
    entry = {"sequence": sequence,"session_id": session["id"],"timestamp": datetime.now(timezone.utc).isoformat(),
             "scenario_id": session["scenario_id"],"method": session["method"],
             "severity": {"ALLOWED":"info","WARNING":"medium","BLOCKED":"high"}[checkpoint["decision"]],
             **deepcopy(checkpoint)}
    activity.append(entry)
    session["events"].append(entry)

def advance(session, approved=None):
    transaction = session["transaction"]
    try:
        checkpoint = next(transaction) if session["status"] == "new" else transaction.send(approved is True)
        while True:
            add_event(session,checkpoint)
            if checkpoint["decision"] == Decision.WARNING.value:
                session.update(status="approval_required",pending=checkpoint,approval_id=secrets.token_urlsafe(24))
                return
            checkpoint = transaction.send(False)
    except StopIteration as done:
        session.update(status="completed",result=done.value,pending=None,approval_id=None)
        session.pop("transaction",None)

def public_session(session):
    return deepcopy({k:v for k,v in session.items() if k not in ("transaction","created")})

def cleanup():
    for key in list(sessions):
        session = sessions[key]
        if monotonic() - session["created"] > TTL:
            transaction = session.pop("transaction",None)
            if transaction:
                transaction.close()
            del sessions[key]

@app.get("/api/health")
def health():
    return {"status":"ok","simulation_only":True}

@app.get("/api/config", dependencies=[Depends(authorize)])
def config():
    llm = configured_llm()
    return {"methods":["no_defense","rules","llm","hybrid"], "llm_configured":llm.configured,
            "model":llm.model or None,"approval_ttl_seconds":TTL, "simulation_only":True}

@app.get("/api/scenarios", dependencies=[Depends(authorize)])
def scenario_list():
    return cases()

@app.get("/api/dataset", dependencies=[Depends(authorize)])
def dataset_stats():
    return statistics(cases())

@app.get("/api/activity", dependencies=[Depends(authorize)])
def events(after: int = 0):
    with lock:
        return {"events":[deepcopy(e) for e in activity if e["sequence"] > after],"latest_sequence":sequence}

@app.post("/api/simulations", dependencies=[Depends(authorize)])
def simulate(body: SimulationRequest):
    case = next((x for x in cases() if x["id"] == body.scenario_id),None)
    if case is None:
        raise HTTPException(404,"Unknown scenario")
    if body.method in ("llm","hybrid") and not configured_llm().configured:
        raise HTTPException(503,"Real LLM model/credentials are not configured")
    with lock:
        cleanup()
        if len(sessions) >= 100:
            raise HTTPException(429,"Session capacity reached; retry after expiry")
        identifier = secrets.token_urlsafe(18)
        session = {"id":identifier,"scenario_id":body.scenario_id,"method":body.method,
                   "status":"new","created":monotonic(),"events":[],"pending":None,"approval_id":None,
                   "transaction":Agent(detector(body.method)).transaction(deepcopy(case))}
        sessions[identifier] = session
        advance(session)
        return public_session(session)

@app.post("/api/simulations/{identifier}/approval", dependencies=[Depends(authorize)])
def approval(identifier: str, body: ApprovalRequest):
    with lock:
        cleanup()
        session = sessions.get(identifier)
        if session is None:
            raise HTTPException(404,"Session missing or expired")
        if session["status"] != "approval_required" or not hmac.compare_digest(session["approval_id"],body.approval_id):
            raise HTTPException(409,"Approval is stale, already consumed, or does not match")
        session["approval_id"] = None
        session["pending"] = None
        advance(session,body.approved)
        return public_session(session)

@app.get("/api/evaluation", dependencies=[Depends(authorize)])
def evaluation():
    if latest_report is not None:
        return latest_report
    path = ROOT / "results/evaluation.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"methods":{name:{"status":"NOT RUN","reason":"Start evaluation"} for name in ("no_defense","rules","llm","hybrid")}}

@app.post("/api/evaluation", dependencies=[Depends(authorize)])
def evaluate(body: EvaluationRequest):
    global latest_report
    if not evaluation_lock.acquire(blocking=False):
        raise HTTPException(409,"Evaluation is already running")
    try:
        selected = cases()
        if body.split != "all":
            selected = [c for c in selected if c["split"] == body.split]
        report = run_experiment(selected,body.repeats,body.include_llm)
        output = ROOT / "results/evaluation.json"
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(report,indent=2),encoding="utf-8")
        latest_report = report
        return report
    finally:
        evaluation_lock.release()

DIST = ROOT / "frontend/dist"
if DIST.exists():
    app.mount("/assets",StaticFiles(directory=DIST / "assets"),name="assets")

@app.get("/", include_in_schema=False)
def dashboard():
    if not (DIST / "index.html").exists():
        raise HTTPException(503,"Build dashboard: cd frontend && npm ci && npm run build")
    return FileResponse(DIST / "index.html")

@app.get("/api/simulations/{identifier}", dependencies=[Depends(authorize)])
def get_simulation(identifier: str):
    with lock:
        cleanup()
        if identifier not in sessions:
            raise HTTPException(404,"Session missing or expired")
        return public_session(sessions[identifier])

class RPCRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    jsonrpc: Literal["2.0"] = "2.0"
    id: Any = None
    method: str = Field(max_length=100)
    params: dict = Field(default_factory=dict)

@app.post("/api/mcp", dependencies=[Depends(authorize)])
def mcp(body: RPCRequest):
    """JSON-RPC mock MCP subset. No upstream server processes are launched."""
    from fastapi.responses import Response
    from .dataset import REQUESTS
    if body.id is None:
        return Response(status_code=202)
    envelope = {"jsonrpc":"2.0","id":body.id}
    if body.method == "initialize":
        return {**envelope,"result":{"protocolVersion":"2024-11-05","capabilities":{"tools":{}},"serverInfo":{"name":"MCPShield sandbox","version":"0.2.0"}}}
    if body.method == "tools/list":
        tools=[]
        for name,request in REQUESTS.items():
            tools.append({"name":name,"description":"Deterministic in-memory " + name,
                          "inputSchema":{"type":"object","properties":{k:{"type":"string"} for k in request},"required":list(request)}})
        return {**envelope,"result":{"tools":tools}}
    if body.method != "tools/call":
        return {**envelope,"error":{"code":-32601,"message":"Method not found"}}
    tool=body.params.get("name")
    arguments=body.params.get("arguments",{})
    if not isinstance(tool,str) or not isinstance(arguments,dict) or len(json.dumps(arguments)) > 32000:
        return {**envelope,"error":{"code":-32602,"message":"Invalid tool arguments"}}
    method=os.getenv("MCPSHIELD_METHOD","rules")
    if method not in ("rules","llm","hybrid"):
        raise HTTPException(503,"MCP endpoint requires rules, llm, or hybrid policy")
    if method in ("llm","hybrid") and not LLM().configured:
        raise HTTPException(503,"LLM classifier is not configured")
    case={"tool":tool,"request":arguments,"response":None,"forbidden_effects":[]}
    with lock:
        cleanup()
        if len(sessions)>=100:
            raise HTTPException(429,"Session capacity reached")
        identifier=secrets.token_urlsafe(18)
        session={"id":identifier,"scenario_id":"mcp-client-call","method":method,"status":"new",
                 "created":monotonic(),"events":[],"pending":None,"approval_id":None,
                 "transaction":Agent(detector(method)).transaction(case)}
        sessions[identifier]=session
        advance(session)
        if session["status"]=="approval_required":
            return {**envelope,"error":{"code":-32001,"message":"Approval required","data":{"session_id":identifier}}}
        result=session["result"]
        if not result["delivered"]:
            return {**envelope,"result":{"isError":True,"content":[{"type":"text","text":"MCPShield denied this interaction"}],"_meta":{"session_id":identifier}}}
        return {**envelope,"result":{"isError":False,"content":[{"type":"text","text":json.dumps(result["response"])}],"_meta":{"session_id":identifier}}}
