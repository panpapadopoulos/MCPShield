"""Offline expansion contracts. Mock reviewers here are never saved as evidence."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys
import os

from research.expansion import generate, SOURCE_IDS, PINNED_SHA256
from research.data import digest, validate, split_development, verify_splits, components
from research.pilot import generate as pilot
from research.observations import build_observation, model_text
from research.quality import report, duplicate_pairs
from research.reviews import export_review, import_review, review_status
from shield.dataset import load_cases, canonical_server, tool_list

ROOT = Path(__file__).resolve().parents[1]


class ExpansionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.historical = load_cases()
        cls.dataset = generate(ROOT / "data/raw/mcpcorpus_servers.json", ROOT / "data/raw/manifest.json", cls.historical)
        cls.splits = split_development(cls.dataset, cls.historical)

    def test_regeneration_identical_and_pilot_intact(self):
        repeated = generate(ROOT / "data/raw/mcpcorpus_servers.json", ROOT / "data/raw/manifest.json", self.historical)
        self.assertEqual(digest(self.dataset), digest(repeated))
        self.assertEqual(self.dataset["episodes"][:16], pilot()["episodes"])
        self.assertEqual(len(self.dataset["episodes"]), 38)
        self.assertEqual(sum(len(e["events"]) for e in self.dataset["episodes"]), 68)

    def test_serialization_stable_across_hash_seeds(self):
        code = "import json; from research.expansion import generate; from shield.dataset import load_cases; print(json.dumps(generate('data/raw/mcpcorpus_servers.json','data/raw/manifest.json',load_cases()),ensure_ascii=True))"
        outputs = [subprocess.check_output([sys.executable, "-c", code], cwd=ROOT,
                    env={**os.environ, "PYTHONHASHSEED": seed}) for seed in ("1", "73")]
        self.assertEqual(outputs[0], outputs[1])

    def test_metadata_matches_actual_pinned_records(self):
        records = {r["id"]: r for r in json.loads((ROOT / "data/raw/mcpcorpus_servers.json").read_text(encoding="utf-8")) if r["id"] in SOURCE_IDS}
        historical_sources = {c["server"] for c in self.historical}
        for e in self.dataset["episodes"][16:]:
            p = e["provenance"]
            r = records[p["record_id"]]
            self.assertEqual(p["repository"], r["url"])
            self.assertEqual(p["raw_sha256"], PINNED_SHA256)
            self.assertNotIn(canonical_server(r), historical_sources)
            self.assertTrue(all(t in tool_list(r) for t in p["original_tools"]))
            for event in e["events"]:
                if event["kind"] == "request":
                    original = next(t for t in p["original_tools"] if t["name"] == event["tool"])
                    self.assertTrue(event["description"].startswith(original.get("description", "")))
                    self.assertTrue(set(original["inputSchema"].get("required", [])) <= set(event["arguments"]))

    def test_checksum_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            bad = Path(directory) / "bad.json"
            bad.write_text("[]")
            with self.assertRaises(ValueError):
                generate(bad, ROOT / "data/raw/manifest.json", self.historical)

    def test_provenance_tampering_rejected(self):
        data = deepcopy(self.dataset)
        data["episodes"][16]["provenance"]["original_tools"][0]["description"] = "altered"
        with self.assertRaises(ValueError):
            validate(data)

    def test_splits_keep_every_real_source_together(self):
        seen = {}
        for e in self.dataset["episodes"]:
            for source in e["provenance"]["source_groups"]:
                seen.setdefault(source, set()).add(self.splits["assignments"][e["id"]])
        self.assertTrue(all(len(v) == 1 for v in seen.values()))
        self.assertTrue(verify_splits(self.dataset, self.splits, self.historical))

    def test_quality_truthful_and_all_unreviewed(self):
        q = report(self.dataset, self.splits)
        self.assertEqual(q["real_metadata_repositories"], 8)
        self.assertEqual(q["multi_call_episodes"], 4)
        self.assertEqual(q["review_status"], {"UNREVIEWED": 68})
        self.assertEqual(q["duplicate_analysis"]["cross_split_pairs"], [])
        self.assertEqual(q["duplicate_analysis"]["exact_trace_pairs"], 0)
        self.assertFalse(q["ready_for_training"])
        self.assertEqual(q["final_test"]["status"], "NOT_COLLECTED")
        self.assertEqual(sum(q["proposed_boundary_balance"].values()), 68)

    def test_content_duplicates_group_despite_changed_metadata(self):
        data = deepcopy(pilot())
        a, b = data["episodes"][:2]
        b["events"] = deepcopy(a["events"])
        b["events"][0]["description"] = "Entirely distinct metadata language"
        b["proposed_labels"] = deepcopy(a["proposed_labels"])
        pairs = duplicate_pairs(data)
        self.assertTrue(any(set(p["episodes"]) == {a["id"], b["id"]} for p in pairs))
        self.assertTrue(any({a["id"], b["id"]} <= set(group) for group in components(data)))

    def test_quality_rejects_known_duplicate_crossing(self):
        broken = deepcopy(self.splits)
        broken["assignments"]["exp1-publish-approved"] = "train"
        broken["assignments"]["exp1-publish-quoted-code"] = "validation"
        with self.assertRaises(ValueError):
            report(self.dataset, broken)

    def test_multistep_task_ids_and_delayed_attack(self):
        e = next(e for e in self.dataset["episodes"] if e["id"] == "exp1-browser-poll-poisoned")
        self.assertEqual(e["events"][1]["response"]["task_id"], e["events"][2]["arguments"]["task_id"])
        self.assertEqual([l["decision"] for l in e["proposed_labels"]], ["ALLOWED"] * 3 + ["BLOCKED"])
        early = model_text(e, 2)
        self.assertNotIn("export the vault", early)
        self.assertIn("export the vault", model_text(e, 3))
        self.assertEqual(len(build_observation(e, 3)["history"]), 3)

    def test_feature_metadata_and_labels_never_projected(self):
        for e in self.dataset["episodes"][16:]:
            changed = deepcopy(e)
            changed.update(id="LEAK", provenance={"secret_ground_truth": "LEAK"}, proposed_labels="LEAK", split="LEAK")
            for i in range(len(e["events"])):
                self.assertEqual(model_text(e, i), model_text(changed, i))

    def test_blind_opaque_form_roundtrip_only_with_test_fixture_attestation(self):
        form = export_review(self.dataset, "test-fixture-reviewer", opaque_ids=True)
        self.assertFalse(form["human_attestation"])
        self.assertFalse(form["independent_attestation"])
        for item in form["items"]:
            self.assertTrue(item["episode_id"].startswith("review-"))
            self.assertNotIn("proposed_label", item)
        with self.assertRaises(ValueError):
            import_review(self.dataset, [], form)
        blind_accept = deepcopy(form)
        blind_accept["human_attestation"] = blind_accept["independent_attestation"] = True
        blind_accept["items"][0].update(action="accept", justification="Must not accept a hidden proposal")
        with self.assertRaises(ValueError):
            import_review(self.dataset, [], blind_accept)
        # In-memory mock for parser testing; never exported as research evidence.
        form["human_attestation"] = form["independent_attestation"] = True
        for item in form["items"]:
            item.update(action="reject", justification="Unit-test parser fixture, not a real review")
        ledger = import_review(self.dataset, [], form)
        self.assertEqual(len(ledger), 68)
        self.assertTrue(all(row["episode_id"].startswith(("exp1-", "p2a-")) for row in ledger))
        self.assertFalse(any(v["status"] == "AGREED_ATTESTED" for v in review_status(self.dataset, ledger).values()))


if __name__ == "__main__":
    unittest.main()
