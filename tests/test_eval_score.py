import contextlib
import importlib.util
import io
import json
import unittest

from tests import REPO_ROOT, SCENARIOS_DIR

SCORE_PATH = REPO_ROOT / "evals" / "score.py"


def load_score_module():
    spec = importlib.util.spec_from_file_location("eval_score", SCORE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decision(layer, components=(), existing=(), custom=()):
    return {
        "layer": layer,
        "components": list(components),
        "existing": list(existing),
        "custom": list(custom),
    }


class EvalScoreTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.score = load_score_module()

    def rows(self, decisions, expected):
        return self.score.score({"decisions": decisions}, {"decisions": expected})

    def test_components_must_match_in_any_order(self):
        decisions = [decision("observability", ["grafana", "prometheus"])]
        expected = {"observability": {"components": ["prometheus", "grafana"]}}
        self.assertEqual(self.rows(decisions, expected), [("observability", "components", True)])
        expected = {"observability": {"components": ["prometheus"]}}
        self.assertEqual(self.rows(decisions, expected), [("observability", "components", False)])

    def test_includes_allows_extra_components(self):
        decisions = [decision("state", ["postgresql", "valkey"])]
        self.assertEqual(
            self.rows(decisions, {"state": {"includes": ["postgresql"]}}),
            [("state", "includes", True)],
        )
        self.assertEqual(
            self.rows(decisions, {"state": {"includes": ["harbor"]}}),
            [("state", "includes", False)],
        )

    def test_mentions_reads_components_and_existing_ignoring_case(self):
        decisions = [decision("llm-gateway", ["litellm"], ["Kong, run by the platform team"])]
        expected = {"llm-gateway": {"includes": ["litellm"], "mentions": ["kong"]}}
        self.assertEqual(
            self.rows(decisions, expected),
            [("llm-gateway", "includes", True), ("llm-gateway", "mentions", True)],
        )

    def test_empty_true_and_false(self):
        empty = [decision("identity")]
        filled = [decision("identity", existing=["corporate directory"])]
        self.assertEqual(self.rows(empty, {"identity": {"empty": True}}), [("identity", "empty", True)])
        self.assertEqual(self.rows(filled, {"identity": {"empty": True}}), [("identity", "empty", False)])
        self.assertEqual(self.rows(filled, {"identity": {"empty": False}}), [("identity", "empty", True)])

    def test_a_missing_decision_fails_components_and_empty(self):
        expected = {"ui": {"components": ["open-webui"]}, "identity": {"empty": True}}
        self.assertEqual(
            self.rows([], expected), [("ui", "components", False), ("identity", "empty", False)]
        )

    def test_unknown_check_names_are_rejected(self):
        with self.assertRaises(ValueError):
            self.rows([decision("ui")], {"ui": {"contains": ["x"]}})

    def test_every_scenario_uses_only_known_checks(self):
        known = {"components", "includes", "mentions", "empty"}
        for path in sorted(SCENARIOS_DIR.glob("*/expected.json")):
            expected = json.loads(path.read_text(encoding="utf-8"))
            for layer, checks in expected["decisions"].items():
                self.assertTrue(set(checks) <= known, f"{path.parent.name}: {layer}")

    def test_command_line_reports_and_exits_1_on_failures(self):
        # answers.json has no decisions, so every check fails.
        blueprint = SCENARIOS_DIR / "lab" / "answers.json"
        expected = SCENARIOS_DIR / "lab" / "expected.json"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = self.score.main(["--blueprint", str(blueprint), "--expected", str(expected)])
        self.assertEqual(code, 1)
        self.assertIn("FAIL  llm-serving: components", output.getvalue())
        self.assertIn("0 of 7 checks passed", output.getvalue())


if __name__ == "__main__":
    unittest.main()
