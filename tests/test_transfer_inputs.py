import json
import tempfile
import unittest
from pathlib import Path

from tests import projects, support, transfer_projects
from airgap_lib.blueprint import inputs_digest
from transfer_lib.inputs import (
    InputError,
    architect_digest,
    blueprint_answer,
    channel_of,
    language_of,
    load_inputs,
    operator_of,
)
from transfer_lib.state import load_state, new_state, save_state, state_problems


class ArchitectDigestTest(unittest.TestCase):
    """The transfer skill repeats architect's digest; the two must never drift apart."""

    def test_both_skills_compute_the_same_digest(self):
        with tempfile.TemporaryDirectory() as tmp:
            catalog = support.load_fixture_catalog(Path(tmp))
            cases = [
                projects.build_blueprint(catalog),
                projects.build_blueprint(catalog, support.base_answers(**{"hardware.cpu_arch": "arm64"})),
                {"answers": {}, "decisions": []},
                {"answers": {"workload.models": [{"name": "ü", "role": "chat", "weights_gb": 1.5}]}},
            ]
            for blueprint in cases:
                with self.subTest(blueprint=str(blueprint)[:60]):
                    self.assertEqual(architect_digest(blueprint), inputs_digest(blueprint))


class LoadInputsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        catalog = transfer_projects.transfer_catalog(Path(self.tmp.name) / "catalog")
        self.project = transfer_projects.make_project(Path(self.tmp.name) / "project", catalog)
        self.folder = self.project / "docs" / "airgap"

    def error(self):
        with self.assertRaises(InputError) as caught:
            load_inputs(self.project)
        return str(caught.exception)

    def test_a_finished_project_loads(self):
        blueprint, manifest = load_inputs(self.project)
        self.assertEqual(manifest["platform"], "linux/amd64")
        self.assertEqual(manifest["inputs_digest"], architect_digest(blueprint))

    def test_missing_files_name_the_architect_step(self):
        (self.folder / "transfer-manifest.json").unlink()
        self.assertIn("run airgap-architect's manifest.py first", self.error())
        (self.folder / "blueprint.json").unlink()
        self.assertIn("design the system with airgap-architect first", self.error())

    def test_a_manifest_older_than_the_blueprint_is_refused(self):
        data = json.loads((self.folder / "blueprint.json").read_text(encoding="utf-8"))
        data["answers"]["hardware.cpu_arch"] = "arm64"
        (self.folder / "blueprint.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("is older than blueprint.json", self.error())

    def test_a_manifest_without_platform_is_refused(self):
        data = json.loads((self.folder / "transfer-manifest.json").read_text(encoding="utf-8"))
        data["platform"] = ""
        (self.folder / "transfer-manifest.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("answer hardware.cpu_arch", self.error())

    def test_another_schema_version_is_refused(self):
        data = json.loads((self.folder / "transfer-manifest.json").read_text(encoding="utf-8"))
        data["schema_version"] = 2
        (self.folder / "transfer-manifest.json").write_text(json.dumps(data), encoding="utf-8")
        self.assertIn("schema_version must be 1", self.error())

    def test_invalid_json_is_an_input_error(self):
        (self.folder / "transfer-manifest.json").write_text("{", encoding="utf-8")
        self.assertIn("invalid JSON", self.error())


class BlueprintAnswerTest(unittest.TestCase):
    def test_unknown_takes_the_default_architect_recorded(self):
        blueprint = {
            "answers": {"transfer.channel": "unknown", "inside.operator": "local_agent"},
            "assumptions": [{"id": "answers.transfer.channel", "value": "removable_media", "evidence": "estimate"}],
        }
        self.assertEqual(blueprint_answer(blueprint, "transfer.channel"), "removable_media")
        self.assertEqual(channel_of(blueprint), "removable_media")
        self.assertEqual(operator_of(blueprint), "local_agent")

    def test_an_unusable_answer_is_an_input_error(self):
        for key, function in (("transfer.channel", channel_of), ("inside.operator", operator_of)):
            with self.subTest(key=key):
                with self.assertRaises(InputError):
                    function({"answers": {key: "unknown"}, "assumptions": []})

    def test_language_defaults_to_english(self):
        self.assertEqual(language_of({"language": "tr"}), "tr")
        self.assertEqual(language_of({}), "en")


class StateTest(unittest.TestCase):
    def test_a_new_state_is_valid_and_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "docs" / "airgap" / "transfer.json"
            state = new_state("sha256:abc")
            save_state(path, state)
            self.assertEqual(load_state(path), state)
            self.assertEqual(state_problems(state), [])

    def test_manual_entries_are_checked(self):
        state = new_state("sha256:abc")
        state["manual"] = [
            {"item": "a", "status": "added", "path": "elsewhere/a"},
            {"item": "b", "status": "not_needed"},
            {"item": "c", "status": "maybe"},
            {"status": "added"},
        ]
        self.assertEqual(
            state_problems(state),
            [
                "manual[0]: an added item needs a 'path' under manual/",
                "manual[1]: an item marked not needed needs a 'reason'",
                "manual[2].status must be one of added, not_needed",
                "manual[3] needs an 'item' name",
            ],
        )

    def test_wrong_types_are_listed(self):
        state = new_state("sha256:abc")
        state["answers"] = []
        state["schema_version"] = True
        self.assertEqual(state_problems(state), ["'schema_version' must be of type int", "'answers' must be of type dict"])


if __name__ == "__main__":
    unittest.main()
