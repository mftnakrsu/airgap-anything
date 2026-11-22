import json
import unittest

from tests import CATALOG_DIR, SCENARIOS_DIR
from airgap_lib.answers import resolve_answers
from airgap_lib.catalog import load_catalog
from airgap_lib.sizing import compute_sizing
from airgap_lib.tiering import compute_tier

SCENARIOS = ("department", "enterprise", "lab")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


class ScenarioTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.load_findings = load_catalog(CATALOG_DIR)

    def test_the_three_scenarios_exist_with_all_files(self):
        self.assertEqual(self.load_findings, [])
        found = sorted(path.name for path in SCENARIOS_DIR.iterdir() if path.is_dir())
        self.assertEqual(found, list(SCENARIOS))
        for name in SCENARIOS:
            for file_name in ("answers.json", "expected.json", "prompt.md"):
                path = SCENARIOS_DIR / name / file_name
                self.assertTrue(path.is_file() and path.stat().st_size > 0, str(path))

    def test_tier_and_sizing_match_the_expectations(self):
        rules = self.catalog.rules
        for name in SCENARIOS:
            with self.subTest(scenario=name):
                answers = read_json(SCENARIOS_DIR / name / "answers.json")
                expected = read_json(SCENARIOS_DIR / name / "expected.json")["deterministic"]
                resolved, _, problems = resolve_answers(answers, rules)
                self.assertEqual(problems, [])

                tier = compute_tier(resolved, rules)
                self.assertEqual(tier["base"], expected["tier"]["base"])
                self.assertEqual(tier["floors"], expected["tier"]["floors"])
                self.assertEqual(tier["requirements"], expected["tier"]["requirements"])

                sizing, _ = compute_sizing(resolved, rules, self.catalog.gpu)
                self.assertEqual(
                    {key: sizing["concurrency"][key] for key in ("low", "high")},
                    expected["sizing"]["concurrency"],
                )
                for key in ("total_gpus", "servers", "power_kw", "fits"):
                    self.assertEqual(sizing[key], expected["sizing"][key], key)
                models = [
                    {
                        "gpus_per_replica": model["gpus_per_replica"],
                        "replicas": model["replicas"],
                        "kv_status": model["kv"]["status"],
                    }
                    for model in sizing["models"]
                ]
                self.assertEqual(models, expected["sizing"]["models"])


if __name__ == "__main__":
    unittest.main()
