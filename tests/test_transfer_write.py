import contextlib
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import transfer_projects
import pack
from transfer_lib import pack_files
from transfer_lib.constants import GB


class WriteVolumeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project, self.bundle = transfer_projects.packed_project(
            Path(self.tmp.name), sizes={"model:example-70b": 50000},
            **{"medium.filesystem": "fat32", "medium.capacity_gb": 20000 / GB},
        )
        self.data = json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))

    def write(self, number, target):
        Path(target).mkdir(parents=True, exist_ok=True)
        return transfer_projects.run_script("pack.py", self.project, "--write-volume", str(number), "--to", str(target))

    def test_every_volume_is_written_with_parts_and_reads_back(self):
        total = len(self.data["volumes"])
        self.assertGreater(total, 1)
        for number in range(1, total + 1):
            target = Path(self.tmp.name) / f"medium{number}"
            result = self.write(number, target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(f"Wrote volume {number} of {total}", result.stdout)
            self.assertEqual((target / "VOLUME.txt").read_text(encoding="utf-8"), f"volume {number} of {total}\n")
            for name in ("bundle.json", "SHA256SUMS", "PARTS.txt", "VOLUMES.txt", "verify.sh", "load.sh", "INSIDE.md"):
                self.assertTrue((target / name).is_file(), name)
            for unit in self.data["volumes"][number - 1]["units"]:
                written = (target / unit["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(written).hexdigest(), unit["sha256"], unit["path"])
                self.assertLessEqual(len(written), 19600)

    def test_a_read_back_mismatch_is_reported(self):
        target = Path(self.tmp.name) / "medium"
        target.mkdir()
        with mock.patch.object(pack_files, "_read_back", return_value="0" * 64):
            bad = pack_files.write_volume(self.bundle, self.data, 1, target, ["bundle.json"])
        self.assertTrue(bad)

    def test_wrong_volume_or_target_is_exit_2(self):
        result = self.write(99, Path(self.tmp.name) / "medium")
        self.assertEqual(result.returncode, 2)
        self.assertIn("there is no volume 99", result.stderr)
        result = self.write(1, self.bundle / "inside")
        self.assertEqual(result.returncode, 2)
        self.assertIn("inside the bundle folder", result.stderr)
        result = transfer_projects.run_script("pack.py", self.project, "--write-volume", "1", "--to", str(Path(self.tmp.name) / "absent"))
        self.assertEqual(result.returncode, 2)
        self.assertIn("is not a folder", result.stderr)

    def test_write_volume_needs_to(self):
        result = transfer_projects.run_script("pack.py", self.project, "--write-volume", "1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--write-volume and --to go together", result.stderr)

    def test_each_written_file_is_synced_before_it_is_read_back(self):
        target = Path(self.tmp.name) / "medium"
        target.mkdir()
        generated = transfer_projects.load_state_of(self.project)["pack"]["generated"]
        with mock.patch.object(pack_files.os, "fsync", wraps=pack_files.os.fsync) as synced:
            self.assertEqual(pack_files.write_volume(self.bundle, self.data, 1, target, generated), [])
        files = len(self.data["volumes"][0]["units"]) + len(generated)
        self.assertGreaterEqual(synced.call_count, files)

    def test_a_medium_that_fails_is_exit_1(self):
        target = Path(self.tmp.name) / "medium"
        target.mkdir()
        stderr = io.StringIO()
        with mock.patch.object(pack_files, "_read_back", side_effect=OSError(5, "Input/output error")), \
                contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                pack.main(["--project-root", str(self.project), "--write-volume", "1", "--to", str(target)])
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("Input/output error", stderr.getvalue())
        self.assertIn("Write this volume again, or use another medium.", stderr.getvalue())

    def test_writing_a_volume_again_counts_its_old_copy_as_room(self):
        target = Path(self.tmp.name) / "medium"
        self.assertEqual(self.write(1, target).returncode, 0)
        generated = transfer_projects.load_state_of(self.project)["pack"]["generated"]
        full = shutil._ntuple_diskusage(10**6, 10**6, 0)
        with mock.patch.object(pack_files.shutil, "disk_usage", return_value=full):
            self.assertEqual(pack_files.write_volume(self.bundle, self.data, 1, target, generated), [])
            fresh = Path(self.tmp.name) / "fresh"
            fresh.mkdir()
            with self.assertRaises(pack_files.WriteError):
                pack_files.write_volume(self.bundle, self.data, 1, fresh, generated)


if __name__ == "__main__":
    unittest.main()
