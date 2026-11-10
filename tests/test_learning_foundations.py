"""Synthetic contract checks only. No training, real reviewer votes or model results."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research.supervised import metrics, ModelConfig, train, load_partitions, tree_hash, Predictor
from research.sequential import SequentialEnv, rollout
from research.comparison import diagnostic_comparison
from research.custody import development_exclusions, register_seal, release_gate
from research.data import digest
from research.pilot import generate
from research.reviews import export_review, import_review, disagreement_report
from research.reviewer_ui import render
from shield.dataset import load_cases


class LearningTests(unittest.TestCase):
    def test_training_requires_approval_before_dependencies_or_data(self):
        with self.assertRaises(PermissionError):
            train(None, None, None, None, "unused", "unused", "unused")

    def test_partitions_use_only_reviewed_inputs_and_no_overlap(self):
        def fake_prepare(dataset, splits, historical, ledger, split):
            return [{"current": {"phase": "request", "arguments": {"text": split + str(i)}}} for i in range(6)], ["ALLOWED", "WARNING", "BLOCKED"] * 2
        with patch("research.supervised.prepare_rows", side_effect=fake_prepare):
            result = load_partitions({}, {}, [], [])
        self.assertEqual(set(result), {"train", "validation"})
        self.assertEqual(set(result["train"]), {"text", "label"})
        with patch("research.supervised.prepare_rows", return_value=([{}], ["ALLOWED"])):
            with self.assertRaises(ValueError):
                load_partitions({}, {}, [], [])

    def test_three_class_metrics_and_nulls(self):
        result = metrics(["ALLOWED", "WARNING", "BLOCKED"], ["ALLOWED"] * 3)
        self.assertAlmostEqual(result["accuracy"], 1/3)
        self.assertEqual(result["confusion_matrix"], [[1,0,0],[1,0,0],[1,0,0]])
        self.assertIsNone(result["per_class"]["WARNING"]["precision"])
        with self.assertRaises(ValueError):
            metrics([], [])

    def test_config_and_model_snapshot_hash(self):
        ModelConfig().validate()
        with self.assertRaises(ValueError):
            ModelConfig(batch_size=0).validate()
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / "config.json"
            p.write_text("fixture-only")
            before = tree_hash(directory)
            p.write_text("changed fixture")
            self.assertNotEqual(before, tree_hash(directory))

    def test_predictor_only_sees_observation_prefix(self):
        class ArrayFixture:
            def tolist(self): return ["WARNING"]
        class FakeModel:
            def predict(self, text):
                self.text = text
                return ArrayFixture()
        e = next(e for e in generate()["episodes"] if len(e["events"]) > 1)
        fake = FakeModel()
        self.assertEqual(Predictor(fake).predict(e, 0), "WARNING")
        self.assertNotIn("proposed_labels", fake.text[0])
        self.assertNotIn(e["id"], fake.text[0])
        self.assertNotIn('"response":', fake.text[0])


class SequentialTests(unittest.TestCase):
    @staticmethod
    def safe_policy(obs):
        current = obs["current"]
        return 2 if current["phase"] == "response" and "FIXTURE_SECRET_42" in json.dumps(current.get("response")) else 0

    def test_allow_clean_succeeds_but_allow_poisoned_causes_real_virtual_sink_effect(self):
        clean = rollout(lambda obs: 0, options={"variant":"clean"})
        bad = rollout(lambda obs: 0, options={"variant":"poisoned"})
        self.assertTrue(clean["task_success"])
        self.assertGreater(clean["steps"], 1)
        self.assertTrue(bad["unsafe_outcome"])
        self.assertIn("secret_disclosed", bad["effects"])
        self.assertLess(bad["return"], clean["return"])

    def test_block_all_and_warn_all_do_not_hack_reward(self):
        for policy in (lambda obs: 1, lambda obs: 2):
            result = rollout(policy, options={"variant":"clean"})
            self.assertFalse(result["task_success"])
            self.assertLess(result["return"], 0)
            self.assertLessEqual(result["steps"], 2)

    def test_block_result_opens_recovery_then_task_completes(self):
        result = rollout(self.safe_policy, options={"variant":"poisoned"})
        self.assertTrue(result["task_success"])
        self.assertFalse(result["unsafe_outcome"])
        self.assertEqual(result["blocks"], 1)
        self.assertGreater(result["steps"], 4)

    def test_authorization_blocks_for_every_policy_and_records_override(self):
        result = rollout(lambda obs: 0, options={"variant":"unauthorized"})
        self.assertTrue(result["task_success"])
        self.assertEqual(result["policy_overrides"], 1)
        self.assertNotIn("private_file_read", result["effects"])

    def test_scoped_consent_uses_user_preference_not_attack_label(self):
        yes = rollout(lambda obs: 0, options={"variant":"consent", "consent_accept":True})
        no = rollout(lambda obs: 0, options={"variant":"consent", "consent_accept":False})
        self.assertTrue(yes["task_success"])
        self.assertTrue(no["task_success"])
        self.assertEqual(yes["approvals"], 1)
        self.assertGreater(no["steps"], yes["steps"])

    def test_seed_determinism_and_truncation_and_no_replay(self):
        self.assertEqual(rollout(lambda obs: 0, seed=23), rollout(lambda obs: 0, seed=23))
        env = SequentialEnv(horizon=1)
        obs, _ = env.reset(seed=11, options={"variant":"clean"})
        self.assertNotIn("response", obs["current"])
        obs, reward, terminated, truncated, info = env.step(0)
        self.assertFalse(terminated)
        self.assertTrue(truncated)
        with self.assertRaises(RuntimeError):
            env.step(0)

    def test_future_state_and_outcome_ledger_not_policy_features(self):
        env = SequentialEnv()
        obs, _ = env.reset(seed=1, options={"variant":"poisoned"})
        text = json.dumps(obs)
        for key in ("poisoned", "FIXTURE_SECRET_42", "nodes", "effects", "reward", "variant"):
            self.assertNotIn(key, text)
        obs, *_ = env.step(0)
        self.assertEqual(len(obs["history"]), 1)
        self.assertIn("FIXTURE_SECRET_42", json.dumps(obs))

    def test_comparison_unavailable_methods_never_get_scores(self):
        report = diagnostic_comparison(seeds=(11,))
        for method in ("pretrained_qwen", "supervised", "drl"):
            self.assertEqual(report["methods"][method]["status"], "NOT RUN")
        self.assertEqual(report["methods"]["rules"]["status"], "SYNTHETIC_DIAGNOSTIC_ONLY")

    def test_same_current_call_has_different_recovery_history_and_consequences(self):
        env = SequentialEnv()
        initial, _ = env.reset(seed=11, options={"variant":"archive_recovery", "consent_accept":True})
        # Decline optional archive, then observe that the alternative is unavailable.
        env.step(2)
        env.step(0)
        retry, *_ = env.step(0)
        self.assertEqual(initial["current"], retry["current"])
        self.assertEqual(initial["history"], [])
        self.assertGreater(len(retry["history"]), 0)
        _, _, terminated, _, info = env.step(2)
        self.assertTrue(terminated)
        self.assertFalse(info["task_success"])
        # The same prefix followed by scoped consent instead can finish the task.
        env.reset(seed=11, options={"variant":"archive_recovery", "consent_accept":True})
        for action in (2,0,0,1,0,0,0):
            _, _, terminated, truncated, info = env.step(action)
        self.assertTrue(info["task_success"])


class ReviewReadinessTests(unittest.TestCase):
    def test_offline_ui_blank_and_safe_embedding(self):
        form = export_review(generate(), "fixture-only", opaque_ids=True)
        html = render(form)
        self.assertIn("slice(0,x.event_index+1)", html)
        self.assertNotIn("fetch(", html)
        self.assertNotIn('type="checkbox" checked', html)
        form["items"][0]["events"][0]["description"] = "</script><script>BAD</script>"
        self.assertNotIn("</script><script>BAD", render(form))
        form["human_attestation"] = True
        with self.assertRaises(ValueError):
            render(form)

    def test_ambiguous_warning_disagreement_remains_unresolved(self):
        dataset = generate()
        ledger = []
        for name, decision in (("fixture-A", "WARNING"),("fixture-B", "ALLOWED")):
            form = export_review(dataset, name, opaque_ids=True)
            form["items"] = [form["items"][-1]]
            form["human_attestation"] = form["independent_attestation"] = True
            item = form["items"][0]
            item.update(action="modify", justification="Synthetic parser test, not a human review",
                reviewed_label={"event_index":item["event_index"],"decision":decision,"attack_category":"ambiguous_instruction","rationale":"Fixture disagreement"})
            ledger = import_review(dataset, ledger, form)
        report = disagreement_report(dataset, ledger)
        self.assertEqual(len(report["unresolved"]), 1)
        self.assertEqual(len(report["unresolved"][0]["votes"]), 2)


class CustodyTests(unittest.TestCase):
    def setUp(self):
        self.exclusions = development_exclusions(generate(), load_cases())
        self.seal = {"schema":"custodian-seal-v1","custodian":"fixture-custodian","reviewers":["fixture-A","fixture-B"],
            "payload_sha256":"a"*64,"labels_sha256":"b"*64,"reviews_sha256":"c"*64,"exclusions_sha256":digest(self.exclusions),
            "source_groups":["fixture-only-new-source"],"template_groups":["fixture-only-template"],
            "derivation_families":["fixture-only-family"],"sealed_utc":"2026-11-09T10:00:00+00:00",
            "independent_collection_attested":True,"semantic_separation_attested":True}

    def test_metadata_registration_no_examples_and_overlap_fail_closed(self):
        self.assertEqual(register_seal(self.exclusions, self.seal)["status"], "SEALED_ATTESTED_NOT_INSPECTED")
        self.seal["source_groups"] = [self.exclusions["source_groups"][0]]
        with self.assertRaises(ValueError): register_seal(self.exclusions, self.seal)

    def test_release_requires_approval_and_freeze_after_sealing(self):
        freeze={"model_sha256":"d"*64,"protocol_sha256":"e"*64,"development_sha256":self.exclusions["development_sha256"],
                "seal_sha256":digest(self.seal),"frozen_utc":"2026-11-09T11:00:00+00:00"}
        with self.assertRaises(PermissionError): release_gate(self.exclusions, self.seal, freeze)
        self.assertEqual(release_gate(self.exclusions,self.seal,freeze,approved=True)["status"],"RELEASE_AUTHORIZED_METADATA_ONLY")
        freeze["frozen_utc"]="2026-11-08T10:00:00+00:00"
        with self.assertRaises(ValueError):release_gate(self.exclusions,self.seal,freeze,approved=True)

    def test_reject_final_example_payloads(self):
        self.seal["examples"] = ["do not ingest final examples in development"]
        with self.assertRaises(ValueError): register_seal(self.exclusions, self.seal)


if __name__ == "__main__": unittest.main()
