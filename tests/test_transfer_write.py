import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests import transfer_projects
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


if __name__ == "__main__":
    unittest.main()
