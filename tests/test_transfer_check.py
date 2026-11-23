import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import transfer_projects
from transfer_lib.checks import bundle_problems, check_bundle
from transfer_lib.constants import GB
from transfer_lib.inputs import channel_of, operator_of


class CheckTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def pack(self, **kwargs):
        self.project, self.bundle = transfer_projects.packed_project(Path(self.tmp.name), **kwargs)

    def bundle_data(self):
        return json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))

    def save_bundle_data(self, data):
        (self.bundle / "bundle.json").write_text(json.dumps(data), encoding="utf-8")

    def manifest(self):
        return json.loads((self.project / "docs/airgap/transfer-manifest.json").read_text(encoding="utf-8"))

    def blueprint_path(self):
        return self.project / "docs/airgap/blueprint.json"

    def change_blueprint(self, **answers):
        blueprint = json.loads(self.blueprint_path().read_text(encoding="utf-8"))
        blueprint["answers"].update(answers)
        self.blueprint_path().write_text(json.dumps(blueprint), encoding="utf-8")

    def findings(self, deep=False, environ=None):
        state = transfer_projects.load_state_of(self.project)
        blueprint = json.loads(self.blueprint_path().read_text(encoding="utf-8"))
        return check_bundle(self.bundle, state, self.bundle_data(), self.manifest(), operator=operator_of(blueprint),
                            channel=channel_of(blueprint), deep=deep, environ=environ or {})

    def messages(self, code, **kwargs):
        return [f.message for f in self.findings(**kwargs) if f.code == code]

    def codes(self, **kwargs):
        return sorted({finding.code for finding in self.findings(**kwargs)})


class CleanBundleTest(CheckTestCase):
    def test_a_packed_bundle_has_only_the_expected_warning(self):
        self.pack()
        self.assertEqual(self.codes(), ["BW1"])
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("BW1 warning: package:alpha-engine:install.sh", result.stdout)

    def test_without_bundle_json_it_is_exit_2(self):
        self.pack()
        (self.bundle / "bundle.json").unlink()
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 2)
        self.assertIn("bundle.json: file not found", result.stderr)


class ErrorCodesTest(CheckTestCase):
    def test_b1_missing_file_and_unsettled_manual_item(self):
        self.pack()
        (self.bundle / "packages/alpha-engine/install.sh").unlink()
        self.assertIn("B1", self.codes())
        transfer_projects.update_state(self.project, lambda state: state.update(manual=[]))
        messages = [f.message for f in self.findings() if f.code == "B1"]
        self.assertIn("manual:alpha-engine: runtime download 1: not settled; add files under manual/ or mark it not needed with a reason", messages)
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 1)

    def test_b2_size_and_deep_hash(self):
        self.pack()
        path = self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64"
        data = path.read_bytes()
        path.write_bytes(data + b"!")
        self.assertIn("B2", self.codes())
        path.write_bytes(b"X" + data[1:])
        self.assertNotIn("B2", self.codes())
        self.assertIn("B2", self.codes(deep=True))

    def test_b2_missing_line_in_sha256sums(self):
        self.pack()
        sums = self.bundle / "SHA256SUMS"
        sums.write_text("".join(line + "\n" for line in sums.read_text(encoding="utf-8").splitlines() if "install.sh" not in line), encoding="utf-8")
        self.assertIn("packages/alpha-engine/install.sh: no matching line in SHA256SUMS", [f.message for f in self.findings()])

    def test_b2_a_generated_file_that_changed_or_is_missing(self):
        self.pack()
        verify = self.bundle / "verify.sh"
        verify.write_text(verify.read_text(encoding="utf-8") + "# edited\n", encoding="utf-8")
        self.assertEqual(self.messages("B2"), ["verify.sh: its SHA-256 differs from SHA256SUMS; run pack.py again"])
        for name in ("verify.sh", "load.sh", "VOLUMES.txt", "PARTS.txt", "INVENTORY.csv"):
            (self.bundle / name).unlink()
        self.assertEqual(sorted(self.messages("B2")), sorted(
            f"{name} is missing; run pack.py again" for name in ("verify.sh", "load.sh", "VOLUMES.txt", "PARTS.txt", "INVENTORY.csv")))
        self.assertEqual(transfer_projects.run_script("check.py", self.project).returncode, 1)

    def test_b2_a_generated_file_without_a_line_in_sha256sums(self):
        self.pack()
        sums = self.bundle / "SHA256SUMS"
        sums.write_text("".join(line + "\n" for line in sums.read_text(encoding="utf-8").splitlines() if not line.endswith("  load.sh")), encoding="utf-8")
        self.assertEqual(self.messages("B2"), ["load.sh: no line in SHA256SUMS; run pack.py again"])

    def test_b2_a_missing_sha256sums_is_one_finding(self):
        self.pack()
        (self.bundle / "SHA256SUMS").unlink()
        self.assertEqual(self.messages("B2"), ["SHA256SUMS is missing; run pack.py again"])

    def test_b3_a_file_over_the_channel_limit(self):
        self.pack(**{"medium.filesystem": "fat32"})
        data = self.bundle_data()
        data["volumes"][0]["units"][0]["size"] = 4 * 1024**3
        self.save_bundle_data(data)
        self.assertIn("B3", self.codes())

    def test_b4_a_volume_over_the_medium(self):
        self.pack(**{"medium.capacity_gb": 20000 / GB})
        data = self.bundle_data()
        data["volumes"][0]["bytes"] = 19601
        self.save_bundle_data(data)
        self.assertIn("B4", self.codes())

    def test_b4_the_capacity_answer_lowered_after_packing(self):
        self.pack(**{"medium.capacity_gb": 20000 / GB})
        transfer_projects.update_state(self.project, lambda state: state["answers"].update({"medium.capacity_gb": 100 / GB}))
        messages = self.messages("B4")
        self.assertTrue(messages)
        self.assertIn("the medium holds 98 after the reserve", messages[0])
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("B4 error: volume 1:", result.stdout)

    def test_b5_bundle_from_another_manifest(self):
        self.pack()
        data = self.bundle_data()
        data["manifest_digest"] = "sha256:" + "0" * 64
        self.save_bundle_data(data)
        self.assertIn("B5", self.codes())

    def test_b5_the_blueprint_changed_inside_operator_or_channel_after_packing(self):
        self.pack()
        self.change_blueprint(**{"inside.operator": "local_agent", "transfer.channel": "other"})
        self.assertEqual(self.messages("B5"), [
            "bundle.json was packed for inside.operator people; the blueprint now says local_agent; run pack.py again",
            "bundle.json was packed for transfer.channel removable_media; the blueprint now says other; run pack.py again",
        ])
        self.assertEqual(self.messages("B7"), ["AGENTS-INSIDE.md is missing; inside.operator is local_agent"])
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("B7 error: AGENTS-INSIDE.md is missing", result.stdout)

    def test_b6_pickle_weights_without_permission(self):
        self.pack()
        data = self.bundle_data()
        model = next(item for item in data["items"] if item["kind"] == "model")
        model["files"].append({"path": "models/example-70b/pytorch_model.bin", "size": 1, "sha256": "0" * 64, "pickle": True})
        self.save_bundle_data(data)
        self.assertIn("B6", self.codes())
        model["allow_pickle"] = True
        self.save_bundle_data(data)
        self.assertNotIn("B6", self.codes())

    def test_b7_missing_runbook_or_lost_command(self):
        self.pack()
        runbook = self.bundle / "INSIDE.md"
        text = runbook.read_text(encoding="utf-8")
        runbook.write_text(text.replace("sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle", "verify the bundle"), encoding="utf-8")
        messages = [f.message for f in self.findings() if f.code == "B7"]
        self.assertEqual(messages, ["INSIDE.md lacks the command line(s): sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle"])
        runbook.unlink()
        self.assertEqual([f.message for f in self.findings() if f.code == "B7"], ["INSIDE.md is missing; inside.operator is people"])

    def test_b7_agent_rules_for_a_local_agent(self):
        self.pack(architect_answers={"inside.operator": "local_agent"})
        self.assertEqual(self.codes(), ["BW1"])
        rules = self.bundle / "AGENTS-INSIDE.md"
        rules.write_text(rules.read_text(encoding="utf-8").replace("sh /srv/airgap-bundle/load.sh", "run load.sh"), encoding="utf-8")
        self.assertEqual(self.messages("B7"), [
            "AGENTS-INSIDE.md lacks the command line(s): sh /srv/airgap-bundle/load.sh /srv/airgap-bundle /srv/models"])
        rules.unlink()
        self.assertEqual(self.messages("B7"), ["AGENTS-INSIDE.md is missing; inside.operator is local_agent"])
        self.assertEqual(self.messages("B2"), [])

    def test_a_translated_runbook_is_b2_until_pack_refreshes_the_sums(self):
        self.pack()
        runbook = self.bundle / "INSIDE.md"
        text = runbook.read_text(encoding="utf-8").replace("Check every file", "Her dosyayı denetle")
        runbook.write_text(text, encoding="utf-8")
        self.assertNotIn("B7", self.codes())
        self.assertEqual(self.messages("B2"), [
            "INSIDE.md: its SHA-256 differs from SHA256SUMS; after translating it, run pack.py --refresh-sums, else run pack.py again"])
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(self.codes(), ["BW1"])
        self.assertEqual(runbook.read_text(encoding="utf-8"), text)

    def test_b8_token_like_values(self):
        self.pack()
        (self.bundle / "manual").mkdir(exist_ok=True)
        (self.bundle / "manual/notes.txt").write_text("token hf_" + "a1B2" * 9, encoding="utf-8")
        self.assertIn("B8", self.codes())
        (self.bundle / "manual/notes.txt").write_text("the secret is s3cr3t-value", encoding="utf-8")
        self.assertNotIn("B8", self.codes())
        self.assertIn("B8", self.codes(environ={"HF_TOKEN": "s3cr3t-value"}))


class WarningCodesTest(CheckTestCase):
    def test_bw1_and_bw2(self):
        self.pack()
        data = self.bundle_data()
        image = next(item for item in data["items"] if item["kind"] == "image")
        image["source"]["digest"] = ""
        self.save_bundle_data(data)
        findings = self.findings()
        self.assertIn("BW2", [f.code for f in findings])
        self.assertTrue(all(f.severity == "warning" for f in findings if f.code.startswith("BW")))


class UnreadableFilesTest(CheckTestCase):
    def test_b2_a_sha256sums_that_is_not_utf8_is_one_finding(self):
        self.pack()
        (self.bundle / "SHA256SUMS").write_bytes(b"\xff\xfe\x00")
        self.assertEqual([f.message for f in self.findings() if f.code == "B2"], ["SHA256SUMS is not readable as UTF-8"])
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("B2 error: SHA256SUMS is not readable as UTF-8", result.stdout)

    def test_b2_still_compares_sizes_when_sha256sums_is_not_utf8(self):
        self.pack()
        (self.bundle / "SHA256SUMS").write_bytes(b"\xff\xfe\x00")
        path = self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64"
        path.write_bytes(path.read_bytes() + b"!")
        messages = [f.message for f in self.findings() if f.code == "B2"]
        self.assertEqual(len(messages), 2)
        self.assertIn("packages/alpha-engine/alpha-cli-1.2.3-amd64: 10 bytes, bundle.json says 9", messages)

    def test_b7_a_runbook_that_is_not_utf8(self):
        self.pack()
        (self.bundle / "INSIDE.md").write_bytes(b"\xff\xfe\x00")
        self.assertEqual([f.message for f in self.findings() if f.code == "B7"], ["INSIDE.md is not readable as UTF-8"])
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_b8_a_file_that_cannot_be_read(self):
        self.pack()
        (self.bundle / "manual").mkdir(exist_ok=True)
        (self.bundle / "manual/locked.txt").write_text("nothing", encoding="utf-8")
        read_bytes = Path.read_bytes

        def locked(path):
            if path.name == "locked.txt":
                raise PermissionError(13, "Permission denied")
            return read_bytes(path)

        with mock.patch.object(Path, "read_bytes", locked):
            messages = [f.message for f in self.findings() if f.code == "B8"]
        self.assertEqual(messages, ["manual/locked.txt cannot be read; check it by hand"])


class InvalidInputTest(CheckTestCase):
    def exit_2(self):
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        return result.stderr

    def test_a_bundle_path_answer_that_is_missing_or_not_a_path(self):
        self.pack()
        for value in ("(missing)", None, 5, "", "  ", ["a"]):
            with self.subTest(value=value):
                def change(state):
                    if value == "(missing)":
                        state["answers"].pop("bundle.path")
                    else:
                        state["answers"]["bundle.path"] = value
                transfer_projects.update_state(self.project, change)
                self.assertIn("the answer 'bundle.path' is missing or is not a path", self.exit_2())

    def test_a_bundle_json_that_lacks_what_check_reads(self):
        self.pack()

        def a_file(data):
            return next(item for item in data["items"] if item["files"])["files"][0]

        cases = [
            ("no items", lambda d: d.pop("items"), "items: missing or not a list of objects"),
            ("an item without files", lambda d: next(i for i in d["items"] if i["files"]).pop("files"), ".files: missing or not a list"),
            ("an item without a source", lambda d: d["items"][0].pop("source"), "items[0].source: missing or not an object"),
            ("a file without a size", lambda d: a_file(d).pop("size"), ".size: missing or not a whole number"),
            ("a file with a text size", lambda d: a_file(d).update(size="9"), ".size: missing or not a whole number"),
            ("no volumes", lambda d: d.pop("volumes"), "volumes: missing or not a list of objects"),
            ("a volume without units", lambda d: d["volumes"][0].pop("units"), "volumes[0].units: missing or not a list"),
            ("a volume without bytes", lambda d: d["volumes"][0].pop("bytes"), "volumes[0].bytes: missing or not a whole number"),
            ("a unit with a text size", lambda d: d["volumes"][0]["units"][0].update(size="big"), "units[0].size: missing or not a whole number"),
            ("a text capacity", lambda d: d.update(volume_capacity="big"), "volume_capacity: missing or not a whole number or null"),
            ("no operator", lambda d: d.pop("operator"), "operator: must be one of"),
            ("no channel", lambda d: d.pop("channel"), "channel: missing or not text"),
        ]
        intact = self.bundle_data()
        for name, damage, expected in cases:
            with self.subTest(name):
                data = copy.deepcopy(intact)
                damage(data)
                self.save_bundle_data(data)
                message = self.exit_2()
                self.assertIn("bundle.json: not a complete bundle.json:", message)
                self.assertIn(expected, message)

    def test_many_problems_are_summarized(self):
        self.pack()
        data = self.bundle_data()
        data["items"] = [{} for _ in range(12)]
        self.save_bundle_data(data)
        message = self.exit_2()
        self.assertEqual(message.count("\n  items["), 10)
        self.assertIn("  ... and 38 more", message)

    def test_an_invalid_answer_stops_check(self):
        self.pack()
        transfer_projects.update_state(self.project, lambda state: state["answers"].update({"medium.capacity_gb": "lots"}))
        message = self.exit_2()
        self.assertIn("medium.capacity_gb: must be a number of gigabytes", message)
        transfer_projects.update_state(self.project, lambda state: state["answers"].update({"medium.capacity_gb": 1000}))
        transfer_projects.update_state(self.project, lambda state: state["answers"].pop("medium.filesystem"))
        self.assertIn("medium.filesystem: missing", self.exit_2())

    def test_a_local_model_folder_that_is_gone_does_not_stop_check(self):
        # The model is in the bundle already; the folder it was copied from is not needed.
        self.pack()
        transfer_projects.update_state(self.project, lambda state: state["answers"].update(
            {"models": {"example-70b": {"source": "local", "path": str(Path(self.tmp.name) / "gone")}}}))
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_truncated_bundle_json(self):
        self.pack()
        (self.bundle / "bundle.json").write_text('{"items": [', encoding="utf-8")
        self.assertIn("bundle.json: invalid JSON", self.exit_2())

    def test_bundle_problems_is_empty_for_what_pack_writes(self):
        self.pack()
        self.assertEqual(bundle_problems(self.bundle_data()), [])

    def test_bundle_problems_accepts_split_files_and_added_manual_items(self):
        self.project, self.bundle = transfer_projects.planned_project(Path(self.tmp.name), **{"medium.capacity_gb": 20000 / GB})
        items = transfer_projects.load_state_of(self.project)["plan"]["items"]
        model = next(item["id"] for item in items if item["kind"] == "model")
        transfer_projects.fake_fetch(self.bundle, items, {model: 30000})
        (self.bundle / "manual/tokenizer").mkdir(parents=True)
        (self.bundle / "manual/tokenizer/tok.json").write_text("{}", encoding="utf-8")
        transfer_projects.update_state(self.project, lambda state: state.update(manual=[
            {"item": "alpha-engine: runtime download 1", "status": "added", "path": "manual/tokenizer"},
            {"item": "Docker Engine 29 packages", "status": "not_needed", "reason": "Already staged."},
        ]))
        result = transfer_projects.run_script("pack.py", self.project)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = self.bundle_data()
        self.assertTrue(any(unit["of"] for volume in data["volumes"] for unit in volume["units"]))
        self.assertEqual(bundle_problems(data), [])
        self.assertEqual(transfer_projects.run_script("check.py", self.project).returncode, 0)


@unittest.skipUnless(shutil.which("sha256sum"), "needs coreutils sha256sum")
class CheckThenVerifyTest(CheckTestCase):
    """A bundle that check.py passes also passes verify.sh."""

    def check_and_verify(self):
        result = transfer_projects.run_script("check.py", self.project)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = subprocess.run(["sh", str(self.bundle / "verify.sh"), str(self.bundle)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("verify.sh: OK", result.stdout)

    def test_a_plain_bundle(self):
        self.pack()
        self.check_and_verify()

    def test_a_translated_bundle_after_refresh_sums(self):
        self.pack(language="tr", architect_answers={"inside.operator": "people_then_agent"})
        for name in ("INSIDE.md", "AGENTS-INSIDE.md"):
            path = self.bundle / name
            path.write_text(path.read_text(encoding="utf-8").replace("## Steps", "## Adımlar"), encoding="utf-8")
        self.assertEqual(transfer_projects.run_script("check.py", self.project).returncode, 1)
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.check_and_verify()


if __name__ == "__main__":
    unittest.main()
