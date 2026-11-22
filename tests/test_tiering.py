import unittest

from tests import CATALOG_DIR, support
from airgap_lib.constants import LAYERS, REQUIREMENTS
from airgap_lib.rules import load_rules
from airgap_lib.tiering import base_tier, compute_tier


class BaseTierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def test_spec_vectors(self):
        # (users, departments) -> base tier, from design spec section 17.
        vectors = {
            (50, 1): "T1",
            (51, 1): "T2",
            (20, 2): "T2",
            (300, 5): "T2",
            (301, 1): "T3",
            (50, 6): "T3",
        }
        for (users, departments), expected in vectors.items():
            with self.subTest(users=users, departments=departments):
                self.assertEqual(base_tier(users, departments, self.rules), expected)


class ComputeTierTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def tier(self, **overrides):
        answers = {
            "org.users_total": 12,
            "org.departments": 1,
            "org.isolation": "none",
            "org.audit_required": False,
            "org.downtime_tolerance": "accepted",
            "org.kubernetes_experience": False,
        }
        answers.update(overrides)
        return compute_tier(answers, self.rules)

    def test_plain_small_team(self):
        tier = self.tier()
        self.assertEqual(tier["base"], "T1")
        self.assertEqual(tier["floors"], {layer: "T1" for layer in LAYERS})
        self.assertEqual(tier["requirements"], {name: False for name in REQUIREMENTS})
        self.assertEqual(tier["reasons"], [])

    def test_spec_vector_audit_raises_only_the_gateway(self):
        tier = self.tier(**{"org.audit_required": True})
        self.assertEqual(tier["base"], "T1")
        self.assertEqual(tier["floors"]["llm-gateway"], "T2")
        self.assertEqual(tier["floors"]["orchestration"], "T1")
        self.assertTrue(tier["requirements"]["gateway_non_empty"])
        self.assertEqual(len(tier["reasons"]), 1)
        self.assertIn("org.audit_required", tier["reasons"][0])

    def test_per_department_isolation(self):
        tier = self.tier(**{"org.isolation": "per_department"})
        self.assertEqual(tier["floors"]["llm-gateway"], "T2")
        self.assertEqual(tier["floors"]["identity"], "T2")
        self.assertTrue(tier["requirements"]["gateway_non_empty"])
        self.assertFalse(tier["requirements"]["isolation_design_section"])

    def test_multi_level_isolation(self):
        tier = self.tier(**{"org.isolation": "multi_level"})
        self.assertEqual(tier["floors"]["llm-gateway"], "T3")
        self.assertEqual(tier["floors"]["identity"], "T3")
        self.assertTrue(tier["requirements"]["isolation_design_section"])
        self.assertTrue(tier["requirements"]["gateway_non_empty"])

    def test_no_downtime_raises_three_layers_and_flags_kubernetes_risk(self):
        tier = self.tier(**{"org.downtime_tolerance": "none"})
        for layer in ("orchestration", "llm-serving", "state"):
            self.assertEqual(tier["floors"][layer], "T3", layer)
        self.assertEqual(tier["floors"]["ui"], "T1")
        self.assertTrue(tier["requirements"]["two_engine_replicas"])
        self.assertTrue(tier["requirements"]["kubernetes_risk_note"])

    def test_kubernetes_experience_removes_the_risk(self):
        tier = self.tier(**{"org.downtime_tolerance": "none", "org.kubernetes_experience": True})
        self.assertFalse(tier["requirements"]["kubernetes_risk_note"])

    def test_escalators_never_lower_a_floor(self):
        tier = self.tier(**{"org.users_total": 2000, "org.audit_required": True})
        self.assertEqual(tier["base"], "T3")
        self.assertEqual(tier["floors"]["llm-gateway"], "T3")

    def test_department_answers_from_support(self):
        tier = compute_tier(support.base_answers(), self.rules)
        self.assertEqual(tier["base"], "T2")
        self.assertEqual(set(tier["floors"].values()), {"T2"})
        self.assertTrue(tier["requirements"]["gateway_non_empty"])


if __name__ == "__main__":
    unittest.main()
