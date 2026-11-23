import json
import tempfile
import unittest
from pathlib import Path

from tests import fetch_stubs, support, transfer_projects
from tests.test_transfer_items import MANIFEST, SOURCE
from transfer_lib.constants import MODEL_FILE_PATTERNS, PICKLE_PATTERNS
from transfer_lib.fetch_script import render_fetch_script, sh_quote
from transfer_lib.items import build_items
from transfer_lib.tools import find_tools


class FetchScriptTextTest(unittest.TestCase):
    def setUp(self):
        items = build_items(MANIFEST, {"models": {"chat model": SOURCE}})
        tools = find_tools(items, lambda name: name)
        self.text = render_fetch_script({"items": items, "tools": tools}, "linux/arm64", "2026-11-22T10:00:00Z")

    def test_posix_header(self):
        lines = self.text.splitlines()
        self.assertFalse(self.text.startswith("#!"))
        self.assertIn("set -eu", lines)
        self.assertIn("PLATFORM='linux/arm64'", lines)
        self.assertIn("ARCH='arm64'", lines)
        self.assertNotIn("HF_TOKEN", self.text)

    def test_globbing_is_off_before_any_function_runs(self):
        # The model patterns (*.json, ...) are split from an unquoted variable; with
        # globbing on they would expand against the folder fetch.sh is started from.
        lines = self.text.splitlines()
        self.assertIn("set -f", lines)
        self.assertLess(lines.index("set -f"), min(i for i, line in enumerate(lines) if line.startswith("log() {")))

    def test_one_call_per_item_and_no_call_for_manual_items(self):
        calls = [line for line in self.text.splitlines() if line.startswith("fetch_") and " || fail " in line]
        self.assertEqual(len(calls), 4)
        self.assertIn("fetch_image 'beta:2' 'images/beta/beta_2.tar' || fail 'image beta:2'", calls)
        self.assertIn(
            "fetch_package 'alpha-1-amd64.tgz' 'packages/alpha/alpha-1-amd64.tgz' "
            "'https://downloads.example.test/alpha-1-amd64.tgz' 'https://downloads.example.test/md5sum' "
            "'packages/alpha/checksums/md5sum' || fail 'package alpha-1-amd64.tgz'",
            calls,
        )
        self.assertIn(
            "fetch_model 'chat model' 'models/chat_model' 'huggingface' 'example/chat' '" + "0" * 40 + "' 'no' "
            "|| fail 'model chat model'",
            calls,
        )

    def test_the_model_filter_is_in_the_script(self):
        self.assertIn('patterns="' + " ".join(MODEL_FILE_PATTERNS) + '"', self.text)
        self.assertIn(" ".join(PICKLE_PATTERNS), self.text)

    def test_quoting(self):
        self.assertEqual(sh_quote("it's"), "'it'\\''s'")


class PlanScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        catalog = transfer_projects.transfer_catalog(tmp / "catalog")
        self.project = transfer_projects.make_project(tmp / "project", catalog)
        self.bundle = tmp / "bundle"
        self.stubs = fetch_stubs.install_stubs(tmp / "stubs")
        self.env = fetch_stubs.stub_env(self.stubs, self.bundle, tmp)

    def plan(self, env=None):
        return transfer_projects.run_script("plan.py", self.project, env=env or self.env)

    def test_first_run_writes_transfer_json_and_lists_the_questions(self):
        result = self.plan()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertTrue((self.project / "docs" / "airgap" / "transfer.json").is_file())
        self.assertIn("bundle.path: missing", result.stderr)
        self.assertIn("Questions for this transfer: bundle.path, models, medium.capacity_gb, medium.filesystem", result.stderr)

    def test_a_complete_plan_writes_fetch_sh_and_the_plan(self):
        transfer_projects.write_state(self.project, transfer_projects.default_answers(self.bundle))
        result = self.plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.bundle / "fetch.sh").is_file())
        self.assertIn("Plan: 12 items (8 image, 1 model, 2 package, 1 manual)", result.stdout)
        self.assertIn("about 70.0 GB of weights", result.stdout)
        self.assertIn("only after they approve it", result.stdout)
        state = transfer_projects.load_state_of(self.project)
        self.assertEqual(state["plan"]["platform"], "linux/amd64")
        self.assertEqual(state["plan"]["tools"]["images"], "skopeo")
        self.assertEqual([i["file"] for i in state["plan"]["items"] if i["kind"] == "package"],
                         ["alpha-cli-1.2.3-amd64", "install.sh"])

    def test_arm64_takes_the_arm64_package(self):
        catalog = transfer_projects.transfer_catalog(Path(self.tmp.name) / "catalog-arm")
        project = transfer_projects.make_project(
            Path(self.tmp.name) / "arm", catalog, support.base_answers(**{"hardware.cpu_arch": "arm64"})
        )
        transfer_projects.write_state(project, transfer_projects.default_answers(self.bundle))
        result = transfer_projects.run_script("plan.py", project, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("ARCH='arm64'", (self.bundle / "fetch.sh").read_text(encoding="utf-8"))
        state = transfer_projects.load_state_of(project)
        self.assertIn("alpha-cli-1.2.3-arm64", [i.get("file") for i in state["plan"]["items"]])

    def test_a_missing_tool_is_exit_3(self):
        transfer_projects.write_state(self.project, transfer_projects.default_answers(self.bundle))
        (self.stubs / "hf").unlink()
        env = self.env
        result = self.plan(env)
        self.assertEqual(result.returncode, 3)
        self.assertIn("hf is not on PATH; it is needed for: model:example-70b", result.stderr)

    def test_a_stale_manifest_is_exit_2(self):
        blueprint = self.project / "docs" / "airgap" / "blueprint.json"
        data = json.loads(blueprint.read_text(encoding="utf-8"))
        data["decisions"][0]["rationale"] = "Changed."
        blueprint.write_text(json.dumps(data), encoding="utf-8")
        result = self.plan()
        self.assertEqual(result.returncode, 2)
        self.assertIn("run airgap-architect's manifest.py again", result.stderr)

    def test_a_local_model_without_safetensors_is_exit_2(self):
        weights = Path(self.tmp.name) / "weights"
        weights.mkdir()
        (weights / "pytorch_model.bin").write_bytes(b"w")
        answers = transfer_projects.default_answers(self.bundle, models={"example-70b": {"source": "local", "path": str(weights)}})
        transfer_projects.write_state(self.project, answers)
        result = self.plan()
        self.assertEqual(result.returncode, 2)
        self.assertIn("holds no safetensors weights (pickle files: pytorch_model.bin)", result.stderr)
        answers["models"]["example-70b"]["allow_pickle"] = True
        transfer_projects.write_state(self.project, answers)
        self.assertEqual(self.plan().returncode, 0)


if __name__ == "__main__":
    unittest.main()
