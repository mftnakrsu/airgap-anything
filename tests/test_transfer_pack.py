import csv
import hashlib
import io
import json
import unittest
import tempfile
from pathlib import Path
from unittest import mock

from tests import transfer_projects
from transfer_lib import bundle as bundle_module
from transfer_lib.constants import FAT32_MAX_FILE_BYTES, GB


class PackScriptTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def packed(self, **kwargs):
        self.project, self.bundle = transfer_projects.packed_project(Path(self.tmp.name), **kwargs)
        self.data = json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))
        return self.data

    def test_bundle_json_records_every_item(self):
        data = self.packed()
        manifest = json.loads((self.project / "docs/airgap/transfer-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(data["manifest_digest"], manifest["inputs_digest"])
        self.assertEqual((data["platform"], data["channel"], data["operator"]), ("linux/amd64", "removable_media", "people"))
        kinds = [item["kind"] for item in data["items"]]
        self.assertEqual(kinds.count("image"), 8)
        image = next(item for item in data["items"] if item["kind"] == "image")
        self.assertEqual(image["source"]["digest"], "sha256:" + "a" * 64)
        self.assertRegex(image["source"]["image_id"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual([Path(f["path"]).suffix for f in image["files"]], [".tar", ".digest", ".id"])
        model = next(item for item in data["items"] if item["kind"] == "model")
        self.assertEqual(model["source"]["revision"], transfer_projects.COMMIT)
        manual = next(item for item in data["items"] if item["kind"] == "manual")
        self.assertEqual((manual["status"], manual["files"]), ("not_needed", []))

    def test_sha256sums_is_coreutils_format_and_covers_every_file(self):
        self.packed()
        lines = (self.bundle / "SHA256SUMS").read_text(encoding="utf-8").splitlines()
        listed = {}
        for line in lines:
            self.assertRegex(line, r"^[0-9a-f]{64}  \S")
            digest, name = line.split("  ", 1)
            listed[name] = digest
        for name, digest in listed.items():
            self.assertEqual(hashlib.sha256((self.bundle / name).read_bytes()).hexdigest(), digest, name)
        self.assertIn("bundle.json", listed)
        self.assertIn("verify.sh", listed)
        self.assertNotIn("fetch.sh", listed)
        self.assertNotIn("SHA256SUMS", listed)

    def test_one_volume_on_a_large_exfat_disk(self):
        data = self.packed()
        self.assertEqual(len(data["volumes"]), 1)
        self.assertEqual((self.bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:], [])

    def test_fat32_splits_files_over_the_limit(self):
        # A medium of 20,000 bytes makes the parts small; the rule is the same at 4 GiB.
        data = self.packed(sizes={"model:example-70b": 50000},
                           **{"medium.filesystem": "fat32", "medium.capacity_gb": 20000 / GB})
        self.assertEqual(data["part_size"], 19600)
        parts = (self.bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:]
        weights = hashlib.sha256(b"w" * 50000).hexdigest()
        self.assertEqual(parts, [f"3 {weights} models/example-70b/model.safetensors"])
        for volume in data["volumes"]:
            self.assertLessEqual(volume["bytes"], 19600)
        volumes = (self.bundle / "VOLUMES.txt").read_text(encoding="utf-8")
        self.assertIn("models/example-70b/model.safetensors.part003", volumes)
        self.assertFalse((self.bundle / "models/example-70b/model.safetensors.part001").exists())

    def test_a_file_one_byte_over_the_fat32_limit_becomes_two_parts(self):
        # A sparse file: 4 GiB on paper, almost nothing on disk; hashing it reads 4 GiB of zeros.
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name), **{"medium.filesystem": "fat32"})
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        weights = bundle / "models/example-70b/model.safetensors"
        with weights.open("r+b") as handle:
            handle.truncate(FAT32_MAX_FILE_BYTES + 1)
        transfer_projects.settle_manual(project)
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        parts = (bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:]
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0].startswith("2 ") and parts[0].endswith(" models/example-70b/model.safetensors"))
        sizes = [line.split()[1] for line in (bundle / "VOLUMES.txt").read_text(encoding="utf-8").splitlines()
                 if ".part" in line and not line.startswith("#")]
        self.assertEqual(sizes, [str(FAT32_MAX_FILE_BYTES), "1"])

    def test_inventory_lists_files_largest_first_with_licences(self):
        self.packed(sizes={"model:example-70b": 50000})
        rows = list(csv.DictReader(io.StringIO((self.bundle / "INVENTORY.csv").read_text(encoding="utf-8"))))
        self.assertEqual(list(rows[0]), ["path", "size", "sha256", "kind", "component", "version", "source", "licence", "pickle"])
        self.assertEqual(rows[0]["path"], "models/example-70b/model.safetensors")
        sizes = [int(row["size"]) for row in rows]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertEqual(rows[0]["licence"], "see LICENSE")
        self.assertEqual(rows[0]["source"], f"huggingface example/model-70b at {transfer_projects.COMMIT}")
        package = next(row for row in rows if row["path"].endswith("alpha-cli-1.2.3-amd64"))
        self.assertEqual((package["kind"], package["licence"]), ("package", "MIT"))
        text = (self.bundle / "INVENTORY.md").read_text(encoding="utf-8")
        self.assertIn("## Not carried", text)
        self.assertIn("alpha-engine: runtime download 1: Staged by the operator", text)

    def test_runbook_and_agent_rules_follow_inside_operator(self):
        cases = {"people": {"INSIDE.md"}, "local_agent": {"AGENTS-INSIDE.md"},
                 "people_then_agent": {"INSIDE.md", "AGENTS-INSIDE.md"}}
        for index, (operator, expected) in enumerate(cases.items()):
            with self.subTest(operator=operator):
                project, bundle = transfer_projects.packed_project(
                    Path(self.tmp.name) / str(index), architect_answers={"inside.operator": operator}
                )
                found = {name for name in ("INSIDE.md", "AGENTS-INSIDE.md") if (bundle / name).exists()}
                self.assertEqual(found, expected)
        rules = (bundle / "AGENTS-INSIDE.md").read_text(encoding="utf-8")
        for phrase in ("Never download", "Check the exit code", "Never improvise", "MISSING.txt"):
            self.assertIn(phrase, rules)
        runbook = (bundle / "INSIDE.md").read_text(encoding="utf-8")
        self.assertIn("sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle", runbook)
        self.assertIn("ALPHA_PING=0", runbook)
        for word in ("curl", "wget", "pip install", "docker pull", "hf download"):
            self.assertNotIn(word, runbook)

    def test_data_diode_gets_a_send_order(self):
        self.packed(architect_answers={"transfer.channel": "data_diode"}, answers=None,
                    **{"channel.max_file_gb": "none"})
        order = (self.bundle / "SEND-ORDER.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(order[:3], ["bundle.json", "SHA256SUMS", "SEND-ORDER.txt"])
        self.assertIn("models/example-70b/model.safetensors", order)

    def test_unsettled_manual_items_stop_pack(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name))
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2)
        self.assertIn("manual:alpha-engine: runtime download 1: not settled", result.stderr)

    def test_an_image_for_another_platform_stops_pack(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name))
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"], arch="arm64")
        transfer_projects.settle_manual(project)
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2)
        self.assertIn("holds an image for linux/arm64, not linux/amd64", result.stderr)

    def test_an_added_manual_item_is_carried(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name))
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        (bundle / "manual/docker-engine").mkdir(parents=True)
        (bundle / "manual/docker-engine/engine.deb").write_bytes(b"deb")
        (bundle / "manual/tokenizer").mkdir(parents=True)
        (bundle / "manual/tokenizer/tok.json").write_text("{}", encoding="utf-8")
        transfer_projects.update_state(project, lambda state: state.update(manual=[
            {"item": "alpha-engine: runtime download 1", "status": "added", "path": "manual/tokenizer"},
            {"item": "Docker Engine 29 packages", "status": "added", "path": "manual/docker-engine"},
        ]))
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        sums = (bundle / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertIn("manual/docker-engine/engine.deb", sums)
        self.assertIn("manual/tokenizer/tok.json", sums)
        self.assertIn("ls -l /srv/airgap-bundle/manual/docker-engine", (bundle / "INSIDE.md").read_text(encoding="utf-8"))

    def test_pack_records_its_result_in_transfer_json(self):
        self.packed()
        state = transfer_projects.load_state_of(self.project)
        self.assertEqual(state["pack"]["total_bytes"], sum(v["bytes"] for v in self.data["volumes"]))
        self.assertEqual(len(state["pack"]["volumes"]), 1)
        self.assertIn("bundle.json", state["pack"]["generated"])
        self.assertEqual(state["pack"]["generated"][-1], "SHA256SUMS")

    def test_another_language_is_reported_for_translation(self):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name), language="tr")
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        transfer_projects.settle_manual(project)
        result = transfer_projects.run_script("pack.py", project)
        self.assertIn("Translate their prose into 'tr'", result.stdout)
        self.assertIn("keep every command line, file name and key exactly as written, then run pack.py --refresh-sums",
                      result.stdout)

    def test_refresh_sums_rewrites_only_the_lines_of_the_translated_documents(self):
        self.packed(architect_answers={"inside.operator": "people_then_agent"})
        sums = self.bundle / "SHA256SUMS"
        before = sums.read_text(encoding="utf-8").splitlines()
        runbook = self.bundle / "INSIDE.md"
        runbook.write_text(runbook.read_text(encoding="utf-8").replace("Check every file", "Her dosyayı denetle"),
                           encoding="utf-8")
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("INSIDE.md, AGENTS-INSIDE.md", result.stdout)
        self.assertIn("--write-volume", result.stdout)
        after = sums.read_text(encoding="utf-8").splitlines()
        changed = [(old, new) for old, new in zip(before, after) if old != new]
        self.assertEqual(len(before), len(after))
        self.assertEqual([new.split("  ", 1)[1] for _, new in changed], ["INSIDE.md"])
        self.assertIn(f"{hashlib.sha256(runbook.read_bytes()).hexdigest()}  INSIDE.md", after)

    def test_refresh_sums_refuses_a_document_that_lost_a_command_line(self):
        self.packed()
        sums = self.bundle / "SHA256SUMS"
        before = sums.read_text(encoding="utf-8")
        runbook = self.bundle / "INSIDE.md"
        runbook.write_text(runbook.read_text(encoding="utf-8").replace(
            "sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle", "verify the bundle"), encoding="utf-8")
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("INSIDE.md lacks the command line(s): sh /srv/airgap-bundle/verify.sh /srv/airgap-bundle", result.stderr)
        self.assertEqual(sums.read_text(encoding="utf-8"), before)
        runbook.unlink()
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("INSIDE.md is missing", result.stderr)

    def test_refresh_sums_needs_a_packed_bundle(self):
        project, bundle = self.fetched()
        result = transfer_projects.run_script("pack.py", project, "--refresh-sums")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Run pack.py without --refresh-sums first.", result.stderr)
        self.packed()
        (self.bundle / "SHA256SUMS").unlink()
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("SHA256SUMS is missing; run pack.py again", result.stderr)

    def test_refresh_sums_refuses_a_bundle_packed_for_another_operator(self):
        self.packed()
        path = self.project / "docs/airgap/blueprint.json"
        blueprint = json.loads(path.read_text(encoding="utf-8"))
        blueprint["answers"]["inside.operator"] = "local_agent"
        path.write_text(json.dumps(blueprint), encoding="utf-8")
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("run pack.py again", result.stderr)

    def test_refresh_sums_does_not_go_with_write_volume(self):
        self.packed()
        result = transfer_projects.run_script("pack.py", self.project, "--refresh-sums", "--write-volume", "1",
                                              "--to", str(self.tmp.name))
        self.assertEqual(result.returncode, 2)
        self.assertIn("--refresh-sums", result.stderr)

    def fetched(self, **kwargs):
        project, bundle = transfer_projects.planned_project(Path(self.tmp.name), **kwargs)
        transfer_projects.fake_fetch(bundle, transfer_projects.load_state_of(project)["plan"]["items"])
        transfer_projects.settle_manual(project)
        return project, bundle

    def test_an_answer_edited_after_the_plan_stops_pack(self):
        # Ruling A: an invalid capacity must never pack as one unlimited volume.
        project, bundle = self.fetched()
        transfer_projects.update_state(project, lambda state: state["answers"].update({"medium.capacity_gb": "lots"}))
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("medium.capacity_gb: must be a number of gigabytes", result.stderr)
        self.assertFalse((bundle / "bundle.json").exists())

    def test_a_file_needing_more_than_999_parts_stops_pack_before_hashing(self):
        # Ruling B: 1,000,000 bytes in parts of 980 bytes is 1021 parts.
        project, bundle = transfer_projects.planned_project(
            Path(self.tmp.name), **{"medium.filesystem": "fat32", "medium.capacity_gb": 1000 / GB})
        state = transfer_projects.load_state_of(project)
        transfer_projects.fake_fetch(bundle, state["plan"]["items"], {"model:example-70b": 1_000_000})
        transfer_projects.settle_manual(project)
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("models/example-70b/model.safetensors: 1,000,000 bytes would be cut into 1021 parts", result.stderr)
        self.assertIn("Use a larger medium (medium.capacity_gb) or a larger file limit", result.stderr)
        state = transfer_projects.load_state_of(project)
        meta = {"project": "example", "channel": "removable_media", "operator": "people", "language": "en"}
        manifest = json.loads((project / "docs/airgap/transfer-manifest.json").read_text(encoding="utf-8"))
        with mock.patch.object(bundle_module, "hash_file") as hashed:
            with self.assertRaises(bundle_module.PackError):
                bundle_module.build_bundle(bundle, state, manifest, meta)
        hashed.assert_not_called()

    def test_an_added_manual_path_must_stay_inside_manual(self):
        # Ruling C: a '..' escape and a link that points outside are both refused.
        project, bundle = self.fetched()
        outside = Path(self.tmp.name) / "x"
        outside.mkdir()
        (outside / "secret.txt").write_text("not for the bundle", encoding="utf-8")
        (bundle / "manual/linked").mkdir(parents=True)
        (bundle / "manual/linked/secret.txt").symlink_to(outside / "secret.txt")
        for path, expected in (("manual/../../x", "lies outside"), ("manual/linked", "is a link to")):
            with self.subTest(path=path):
                transfer_projects.update_state(project, lambda state: state.update(manual=[
                    {"item": "alpha-engine: runtime download 1", "status": "added", "path": path}]))
                result = transfer_projects.run_script("pack.py", project)
                self.assertEqual(result.returncode, 2, result.stdout)
                self.assertIn(f"manual:alpha-engine: runtime download 1: {path}", result.stderr)
                self.assertIn(expected, result.stderr)
                self.assertFalse((bundle / "SHA256SUMS").exists())

    def test_fetch_leftovers_are_never_packed(self):
        # Ruling D: fetch.sh, fetch.log, .fetch/, dot-folders and partial downloads stay out.
        project, bundle = self.fetched()
        (bundle / "fetch.sh").write_text("echo\n", encoding="utf-8")
        (bundle / "fetch.log").write_text("OK\n", encoding="utf-8")
        (bundle / ".fetch").mkdir()
        (bundle / ".fetch/example-70b.done").write_text("key\n", encoding="utf-8")
        (bundle / "models/example-70b/.cache/huggingface").mkdir(parents=True)
        (bundle / "models/example-70b/.cache/huggingface/model.safetensors.metadata").write_text("x", encoding="utf-8")
        partial = bundle / "models/example-70b/extra.safetensors.download"
        partial.write_bytes(b"half")
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("models/example-70b/extra.safetensors.download: a partial download left by fetch.sh", result.stderr)
        partial.unlink()
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Not carried, because", result.stdout)
        for name in ("SHA256SUMS", "VOLUMES.txt", "INVENTORY.csv"):
            text = (bundle / name).read_text(encoding="utf-8")
            for leftover in ("fetch.sh", "fetch.log", ".fetch", ".cache", ".download"):
                self.assertNotIn(leftover, text, f"{name}: {leftover}")

    def test_a_linked_folder_cannot_carry_a_file_from_outside(self):
        # Ruling C, review round 1: manual/alias -> manual/real, whose secret.txt links outside.
        project, bundle = self.fetched()
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("not for the bundle", encoding="utf-8")
        (bundle / "manual/real").mkdir(parents=True)
        (bundle / "manual/real/secret.txt").symlink_to(outside)
        (bundle / "manual/alias").symlink_to(bundle / "manual/real", target_is_directory=True)
        transfer_projects.update_state(project, lambda state: state.update(manual=[
            {"item": "alpha-engine: runtime download 1", "status": "added", "path": "manual/alias"}]))
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("manual/alias/secret.txt is a link to", result.stderr)
        self.assertFalse((bundle / "SHA256SUMS").exists())

    def test_a_link_to_a_file_inside_manual_is_carried(self):
        # Links that stay inside manual/ are allowed: the file is carried under the link's name.
        project, bundle = self.fetched()
        (bundle / "manual/tok").mkdir(parents=True)
        (bundle / "manual/tok/real.json").write_text("{}", encoding="utf-8")
        (bundle / "manual/tok/link.json").symlink_to(bundle / "manual/tok/real.json")
        transfer_projects.update_state(project, lambda state: state.update(manual=[
            {"item": "alpha-engine: runtime download 1", "status": "added", "path": "manual/tok"}]))
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        sums = (bundle / "SHA256SUMS").read_text(encoding="utf-8")
        self.assertIn("  manual/tok/real.json\n", sums)
        self.assertIn("  manual/tok/link.json\n", sums)

    def test_manual_itself_must_not_be_a_link(self):
        project, bundle = self.fetched()
        elsewhere = Path(self.tmp.name) / "elsewhere"
        (elsewhere / "docker-engine").mkdir(parents=True)
        (elsewhere / "docker-engine/engine.deb").write_bytes(b"deb")
        (bundle / "manual").symlink_to(elsewhere, target_is_directory=True)
        transfer_projects.update_state(project, lambda state: state.update(manual=[
            {"item": "alpha-engine: runtime download 1", "status": "added", "path": "manual/docker-engine"}]))
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("make manual/ a real folder", result.stderr)


if __name__ == "__main__":
    unittest.main()
