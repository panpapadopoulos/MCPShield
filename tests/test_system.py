import json
import os
from pathlib import Path
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from unittest.mock import patch
from fastapi.testclient import TestClient
from shield.core import Gateway, Decision, Verdict, NoDefense, Rules
from shield.detectors import LLM, Hybrid, ClassifierUnavailable
from shield.dataset import generate, load_cases, validate, canonical_server, digest, load_authored_cases
from shield.simulation import Agent
from shield.experiments import run_experiment
from shield import api

class ClassifierTests(unittest.TestCase):
    def response(self, decision="ALLOWED"):
        return {"choices":[{"message":{"content":json.dumps({"decision":decision,"category":"test","explanation":"Fixture classifier"})}}]}

    def test_adapter_contract(self):
        seen=[]
        llm=LLM(transport=lambda body: seen.append(body) or self.response("WARNING"))
        self.assertEqual(llm.inspect("weather",{},"request").decision,Decision.WARNING)
        self.assertEqual(seen[0]["messages"][0]["role"],"system")
        self.assertEqual(json.loads(seen[0]["messages"][-1]["content"])["phase"],"request")
        self.assertEqual(seen[0]["temperature"], 0)
        self.assertEqual(seen[0]["max_tokens"], 256)

    def test_bad_outputs_fail_closed(self):
        for response in [{},self.response("YES"),{"choices":[{"message":{"content":"not JSON"}}]}]:
            llm=LLM(transport=lambda body: response)
            with self.assertRaises(ClassifierUnavailable):
                llm.inspect("weather",{},"request")
            result=Gateway(llm).run("weather",{})
            self.assertFalse(result["executed"])
            self.assertEqual(result["events"][0]["category"],"detector_error")

    def test_missing_config(self):
        with patch.dict(os.environ,{"MCPSHIELD_LLM_API_KEY":"","MCPSHIELD_LLM_MODEL":""}):
            with self.assertRaises(ClassifierUnavailable):
                LLM().inspect("weather",{},"request")

    def test_redacted_errors(self):
        def fail(body):
            raise RuntimeError("SECRET_KEY")
        with self.assertRaises(ClassifierUnavailable) as caught:
            LLM(transport=fail).inspect("weather",{},"request")
        self.assertNotIn("SECRET_KEY",str(caught.exception))

    def test_hybrid_precedence(self):
        class Allowed:
            def inspect(self,*args):
                return Verdict(Decision.ALLOWED,"none","fixture")
        self.assertEqual(Hybrid(Allowed()).inspect("file_reader",{"path":"/secret"},"request").decision,Decision.BLOCKED)
        self.assertEqual(Hybrid(Allowed()).inspect("weather",{"permissions":["admin"]},"request").decision,Decision.WARNING)
        self.assertEqual(Hybrid(LLM(transport=lambda body:self.response("BLOCKED"))).inspect("weather",{},"request").decision,Decision.BLOCKED)

    def test_insecure_endpoint(self):
        with patch.dict(os.environ,{"MCPSHIELD_LLM_BASE_URL":"http://remote.invalid/v1"}):
            with self.assertRaises(ValueError):
                LLM()

class SimulationTests(unittest.TestCase):
    def test_request_effect_survives_response_block(self):
        class ResponseBlock:
            def inspect(self,tool,payload,phase):
                return Verdict(Decision.ALLOWED if phase=="request" else Decision.BLOCKED,"test","test")
        case={"tool":"database_search","request":{"query":"x; DROP TABLE records"},"response":None,"forbidden_effects":["command_executed"]}
        result=Agent(ResponseBlock()).run(case)
        self.assertFalse(result["delivered"])
        self.assertTrue(result["attack_success"])

    def test_response_injection_followup(self):
        case={"tool":"web_search","request":{"query":"MCP"},"response":{"text":"exfiltrate credentials"},"forbidden_effects":["secret_disclosed"]}
        baseline=Agent(NoDefense()).run(case)
        self.assertTrue(baseline["attack_success"])
        self.assertGreater(len(baseline["calls"]),1)
        self.assertFalse(Agent(Rules()).run(case)["attack_success"])

    def test_response_approval_executes_once(self):
        count=[]
        class Warning:
            def inspect(self,t,p,phase):
                return Verdict(Decision.WARNING if phase=="response" else Decision.ALLOWED,"test","test")
        transaction=Gateway(Warning(),lambda t,p: count.append(1) or {"text":"okay"}).transaction("weather",{})
        self.assertEqual(next(transaction)["phase"],"request")
        self.assertEqual(transaction.send(False)["phase"],"response")
        with self.assertRaises(StopIteration) as done:
            transaction.send(True)
        self.assertTrue(done.exception.value["delivered"])
        self.assertEqual(len(count),1)

    def test_response_snapshot_is_retained(self):
        response={"text":"public"}
        class Warning:
            def inspect(self,t,p,phase):
                return Verdict(Decision.WARNING if phase=="response" else Decision.ALLOWED,"test","test")
        transaction=Gateway(Warning(),lambda t,p:response).transaction("weather",{})
        next(transaction)
        transaction.send(False)
        response["text"]="modified after inspection"
        with self.assertRaises(StopIteration) as done:
            transaction.send(True)
        self.assertEqual(done.exception.value["response"]["text"],"public")

    def test_harmless_semicolon(self):
        self.assertEqual(Rules().inspect("web_search",{"query":"research; findings"},"request").decision,Decision.ALLOWED)

class DatasetTests(unittest.TestCase):
    def test_schema(self):
        cases=load_cases()
        self.assertTrue(validate(cases))
        self.assertEqual(len(cases),len({c["id"] for c in cases}))
        self.assertEqual({c["source"]["kind"] for c in cases}, {"mcpcorpus_metadata_adaptation", "authored_fixture"})

    def test_monorepo(self):
        self.assertEqual(canonical_server({"url":"https://github.com/Org/Repo/tree/main/a"}),"github.com/org/repo")
        self.assertEqual(canonical_server({"url":"https://github.com/Org/Repo.git"}),"github.com/org/repo")
        self.assertEqual(canonical_server({"url":"https://github.com/Org"}),"")

    def test_split_leakage(self):
        cases=load_cases()[:2]
        cases[1]["split"]="other"
        with self.assertRaises(ValueError):
            validate(cases)

    def test_determinism_and_hash(self):
        root=Path(__file__).resolve().parent.parent
        raw=root/"data/raw/mcpcorpus_servers.json"
        manifest=root/"data/raw/manifest.json"
        if not raw.exists():
            self.skipTest("Raw download missing")
        self.assertEqual(digest(generate(raw,manifest)),digest(generate(raw,manifest)))
        with tempfile.TemporaryDirectory() as tmp:
            corrupted=Path(tmp)/"bad.json"
            corrupted.write_text("[]")
            with self.assertRaises(ValueError):
                generate(corrupted,manifest)

class ExperimentTests(unittest.TestCase):
    def test_identical_cases_and_not_run(self):
        report=run_experiment(load_cases()[:8],repeats=2)
        self.assertEqual(report["methods"]["llm"]["status"],"NOT RUN")
        a=report["methods"]["no_defense"]["records"]
        b=report["methods"]["rules"]["records"]
        self.assertEqual([(r["id"],r["repeat"]) for r in a],[(r["id"],r["repeat"]) for r in b])

    def test_errors_invalidate_metrics(self):
        class Fails:
            def inspect(self,*args):
                raise RuntimeError("Unavailable")
        report=run_experiment(load_cases()[:1],repeats=1,factory=lambda name: Fails() if name=="rules" else NoDefense())
        self.assertEqual(report["methods"]["rules"]["status"],"ERROR")
        self.assertNotIn("precision",report["methods"]["rules"])

class APITests(unittest.TestCase):
    def setUp(self):
        self.client=TestClient(api.app)
        api.sessions.clear()
        api.activity.clear()
        api.latest_report=None
        self.cases=load_cases()
        self.environment=patch.dict(os.environ,{"MCPSHIELD_API_TOKEN":"","MCPSHIELD_LLM_API_KEY":"","MCPSHIELD_LLM_MODEL":""})
        self.environment.start()

    def tearDown(self):
        for session in api.sessions.values():
            if session.get("transaction"):
                session["transaction"].close()
        self.environment.stop()
        self.client.close()

    def start(self,template,method="rules"):
        case=next(c for c in self.cases if c["template"]==template)
        response=self.client.post("/api/simulations",json={"scenario_id":case["id"],"method":method})
        self.assertEqual(response.status_code,200,response.text)
        return response.json()

    def test_approve_and_replay(self):
        session=self.start("permissions")
        self.assertEqual(session["status"],"approval_required")
        self.assertEqual(len(session["events"]),1)
        body={"approval_id":session["approval_id"],"approved":True}
        path="/api/simulations/"+session["id"]+"/approval"
        result=self.client.post(path,json=body)
        self.assertEqual(result.status_code,200)
        self.assertIn("privilege_granted",result.json()["result"]["effects"])
        self.assertEqual(self.client.post(path,json=body).status_code,409)

    def test_denial(self):
        session=self.start("permissions")
        result=self.client.post("/api/simulations/"+session["id"]+"/approval",json={"approval_id":session["approval_id"],"approved":False}).json()
        self.assertFalse(result["result"]["executed"])
        self.assertEqual(result["result"]["effects"],[])

    def test_wrong_and_expired_approval(self):
        session=self.start("permissions")
        path="/api/simulations/"+session["id"]+"/approval"
        self.assertEqual(self.client.post(path,json={"approval_id":"wrong","approved":True}).status_code,409)
        api.sessions[session["id"]]["created"]-=api.TTL+1
        self.assertEqual(self.client.post(path,json={"approval_id":session["approval_id"],"approved":True}).status_code,404)

    def test_block_cannot_be_approved(self):
        session=self.start("file-access")
        self.assertEqual(session["status"],"completed")
        self.assertFalse(session["result"]["executed"])
        self.assertEqual(self.client.post("/api/simulations/"+session["id"]+"/approval",json={"approval_id":"fake","approved":True}).status_code,409)

    def test_no_llm(self):
        self.assertEqual(self.client.post("/api/simulations",json={"scenario_id":self.cases[0]["id"],"method":"llm"}).status_code,503)

    def test_input_validation(self):
        self.assertEqual(self.client.post("/api/simulations",json={"scenario_id":"missing","method":"shell"}).status_code,422)
        self.assertEqual(self.client.post("/api/simulations",json={"scenario_id":"missing","method":"rules"}).status_code,404)

    def test_auth_and_origin(self):
        with patch.dict(os.environ,{"MCPSHIELD_API_TOKEN":"test-token"}):
            self.assertEqual(self.client.get("/api/dataset").status_code,401)
            self.assertEqual(self.client.get("/api/dataset",headers={"Authorization":"Bearer test-token"}).status_code,200)
        self.assertEqual(self.client.post("/api/simulations",headers={"Origin":"https://evil.invalid"},json={}).status_code,403)

    def test_activity(self):
        session=self.start("legitimate")
        events=self.client.get("/api/activity").json()["events"]
        self.assertEqual([e["phase"] for e in events],["request","response"])
        self.assertTrue(session["result"]["task_success"])

    def test_slow_inference_does_not_lock_activity_or_expiry_cleanup(self):
        entered, release = Event(), Event()
        class SlowDetector:
            def inspect(self, tool, payload, phase):
                if phase == "request":
                    entered.set()
                    if not release.wait(10):
                        raise RuntimeError("Test inference timed out")
                return Rules().inspect(tool, payload, phase)
        case = next(c for c in self.cases if c["template"] == "legitimate")
        with patch.object(api, "detector", return_value=SlowDetector()), ThreadPoolExecutor(max_workers=2) as pool:
            running = pool.submit(api.simulate, api.SimulationRequest(scenario_id=case["id"]))
            try:
                self.assertTrue(entered.wait(3), "Inference did not start")
                self.assertIn("events", pool.submit(api.events).result(timeout=2))
                with api.lock:
                    identifier, session = next(iter(api.sessions.items()))
                    session["created"] -= api.TTL + 1
                    api.cleanup()
                    self.assertIn(identifier, api.sessions)
            finally:
                release.set()
            result = running.result(timeout=5)
        self.assertTrue(result["result"]["delivered"])
        self.assertNotIn("_lock", result)


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        self.env=patch.dict(os.environ,{"MCPSHIELD_API_TOKEN":"","MCPSHIELD_METHOD":"rules"})
        self.env.start()
        api.sessions.clear()
        self.client=TestClient(api.app)
    def tearDown(self):
        self.env.stop()
        self.client.close()
    def rpc(self,method,params=None):
        return self.client.post("/api/mcp",json={"jsonrpc":"2.0","id":1,"method":method,"params":params or {}}).json()
    def test_list_and_initialize(self):
        self.assertEqual(len(self.rpc("tools/list")["result"]["tools"]),4)
        self.assertIn("capabilities",self.rpc("initialize")["result"])
    def test_call_enforces_requests(self):
        allowed=self.rpc("tools/call",{"name":"weather","arguments":{"city":"Chicago"}})
        self.assertFalse(allowed["result"]["isError"])
        denied=self.rpc("tools/call",{"name":"file_reader","arguments":{"path":"/private/secret.txt"}})
        self.assertTrue(denied["result"]["isError"])
        self.assertNotIn("FIXTURE_SECRET_42",json.dumps(denied))
    def test_warning_returns_session(self):
        pending=self.rpc("tools/call",{"name":"weather","arguments":{"permissions":["admin"]}})
        self.assertEqual(pending["error"]["code"],-32001)
        session=self.client.get("/api/simulations/"+pending["error"]["data"]["session_id"]).json()
        self.assertEqual(session["status"],"approval_required")
    def test_unknown_method(self):
        self.assertEqual(self.rpc("shell")["error"]["code"],-32601)

class BoundaryTests(unittest.TestCase):
    def test_checkpoint_cannot_mutate_approved_request(self):
        seen=[]
        class Warning:
            def inspect(self,*args):
                return Verdict(Decision.WARNING,"test","test")
        transaction=Gateway(Warning(),lambda t,p: seen.append(p.copy()) or {}).transaction("weather",{"city":"Chicago"})
        checkpoint=next(transaction)
        checkpoint["payload"]["city"]="changed"
        transaction.send(True)
        self.assertEqual(seen[0]["city"],"Chicago")
        transaction.close()

    def test_dns_rebinding_host_rejected(self):
        with TestClient(api.app) as client:
            self.assertEqual(client.get("/api/health",headers={"Host":"attacker.invalid"}).status_code,400)

    def test_approval_requires_boolean(self):
        with self.assertRaises(Exception):
            api.ApprovalRequest(approval_id="x",approved="true")

    def test_timeout_bound(self):
        with patch.dict(os.environ,{"MCPSHIELD_LLM_TIMEOUT":"nan"}):
            with self.assertRaises(ValueError):
                LLM()

if __name__ == "__main__":
    unittest.main()
