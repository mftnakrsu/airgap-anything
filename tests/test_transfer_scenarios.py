"""The three transfer scenarios of evals/transfer-scenarios/, packed and checked end to end
with fake fetched bundles: no downloads."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests import REPO_ROOT, transfer_projects

sys.path.insert(0, str(REPO_ROOT / "evals"))
import transfer_fixture  # noqa: E402

EXPECTED = {
    "department": {"channel": "removable_media", "operator": "people_then_agent", "files": {"INSIDE.md", "AGENTS-INSIDE.md"}},
    "lab": {"channel": "data_diode", "operator": "people", "files": {"INSIDE.md", "SEND-ORDER.txt"}},
    "enterprise": {"channel": "staging_host", "operator": "local_agent", "files": {"AGENTS-INSIDE.md"}},
}


class TransferScenarioTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def build(self, name, variant=None):
        project, bundle = transfer_fixture.build(name, Path(self.tmp.name) / (variant or name), variant, fetched=True)
        result = transfer_projects.run_script("pack.py", project)
        self.assertEqual(result.returncode, 0, result.stderr)
        check = transfer_projects.run_script("check.py", project)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        return project, bundle, json.loads((bundle / "bundle.json").read_text(encoding="utf-8"))

    def test_the_three_scenarios_pack_and_check_clean(self):
        self.assertEqual(sorted(EXPECTED), sorted(p.name for p in transfer_fixture.SCENARIOS.iterdir() if p.is_dir()))
        for name, expected in EXPECTED.items():
            with self.subTest(scenario=name):
                project, bundle, data = self.build(name)
                self.assertEqual((data["channel"], data["operator"]), (expected["channel"], expected["operator"]))
                for file in expected["files"]:
                    self.assertTrue((bundle / file).is_file(), file)
                for file in {"INSIDE.md", "AGENTS-INSIDE.md", "SEND-ORDER.txt"} - expected["files"]:
                    self.assertFalse((bundle / file).exists(), file)

    def test_enterprise_carries_the_benchmark_engine(self):
        _, _, data = self.build("enterprise")
        self.assertIn("sglang", {item.get("component") for item in data["items"]})

    def test_department_on_fat32_splits_the_large_model_file(self):
        _, bundle, data = self.build("department", "fat32")
        parts = (bundle / "PARTS.txt").read_text(encoding="utf-8").splitlines()[1:]
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0].startswith("2 "))
        self.assertEqual(data["part_size"], 4 * 1024**3 - 1)


if __name__ == "__main__":
    unittest.main()
