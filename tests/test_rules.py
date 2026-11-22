import copy
import tomllib
import unittest

from tests import CATALOG_DIR
from airgap_lib.rules import REQUIRED_CONSTANTS, Rules, load_rules, validate_rules


def codes(findings):
    return [finding.code for finding in findings]


class ShippedRulesTest(unittest.TestCase):
    def setUp(self):
        self.rules = load_rules(CATALOG_DIR / "rules.toml")

    def test_shipped_rules_are_valid(self):
        self.assertEqual(validate_rules(self.rules), [])

    def test_every_required_constant_is_present(self):
        for key in REQUIRED_CONSTANTS:
            self.assertTrue(self.rules.has(key), key)

    def test_spec_thresholds(self):
        self.assertEqual(self.rules.value("tiers.t1_max_users"), 50)
        self.assertEqual(self.rules.value("tiers.t2_max_users"), 300)
        self.assertEqual(self.rules.value("tiers.t1_max_departments"), 1)
        self.assertEqual(self.rules.value("tiers.t2_max_departments"), 5)

    def test_precisions_come_from_bytes_per_param(self):
        self.assertEqual(
            set(self.rules.precisions()), {"fp32", "bf16", "fp16", "fp8", "int8", "int4"}
        )

    def test_use_records_a_constant_once(self):
        sink = []
        self.assertEqual(self.rules.use("sizing.overhead", sink), 0.10)
        self.rules.use("sizing.overhead", sink)
        self.assertEqual(len(sink), 1)
        self.assertEqual(set(sink[0]), {"id", "value", "evidence", "note"})
        self.assertEqual(sink[0]["id"], "sizing.overhead")
        self.assertTrue(sink[0]["note"])

    def test_default_answer(self):
        self.assertEqual(self.rules.default_answer("org.audit_required")["value"], True)
        self.assertEqual(self.rules.default_answer("workload.usage")["value"], {"chat": 1.0})
        self.assertIsNone(self.rules.default_answer("org.users_total"))
        self.assertEqual(self.rules.default_answer("hardware.cpu_arch")["value"], "amd64")
        self.assertEqual(self.rules.default_answer("inside.operator")["value"], "people")

    def test_four_escalators(self):
        self.assertEqual(
            [escalator["id"] for escalator in self.rules.escalators],
            ["audit", "isolation-per-department", "isolation-multi-level", "no-downtime"],
        )


class RulesValidationTest(unittest.TestCase):
    def test_missing_constants_are_c1(self):
        findings = validate_rules(Rules({"schema_version": 1}))
        self.assertIn("C1", codes(findings))
        self.assertTrue(any("tiers.t1_max_users" in f.message for f in findings))

    def test_estimate_without_notes_is_c4(self):
        rules = Rules({"schema_version": 1, "x": {"y": {"value": 1, "evidence": "estimate"}}})
        messages = [f.message for f in validate_rules(rules) if f.code == "C4"]
        self.assertTrue(any("x.y" in message for message in messages))

    def test_docs_without_sources_is_c4(self):
        rules = Rules({"schema_version": 1, "x": {"value": 1, "evidence": "docs", "notes": "n"}})
        self.assertIn("C4", codes(validate_rules(rules)))

    def test_escalator_with_unknown_layer_is_c1(self):
        rules = Rules(
            {
                "schema_version": 1,
                "escalators": [
                    {
                        "answer": "org.audit_required",
                        "equals": True,
                        "floors": {"no-such-layer": "T2"},
                        "requires": [],
                        "reason": "r",
                        "evidence": "estimate",
                        "notes": "n",
                    }
                ],
            }
        )
        self.assertTrue(
            any(f.code == "C1" and "escalators[0]" in f.message for f in validate_rules(rules))
        )

    def test_escalator_with_unknown_requirement_is_c1(self):
        rules = Rules(
            {
                "schema_version": 1,
                "escalators": [
                    {
                        "answer": "org.audit_required",
                        "equals": True,
                        "floors": {},
                        "requires": ["no_such_requirement"],
                        "reason": "r",
                        "evidence": "estimate",
                        "notes": "n",
                    }
                ],
            }
        )
        self.assertTrue(
            any(f.code == "C1" and "requires" in f.message for f in validate_rules(rules))
        )


def shipped_data():
    with (CATALOG_DIR / "rules.toml").open("rb") as handle:
        return tomllib.load(handle)


def c1_messages(data):
    return [f.message for f in validate_rules(Rules(data)) if f.code == "C1"]


class RuleValueValidationTest(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(shipped_data())

    def assertNamed(self, key):
        messages = c1_messages(self.data)
        self.assertTrue(any(key in message for message in messages), messages)

    def test_string_threshold_is_c1(self):
        self.data["tiers"]["t1_max_users"]["value"] = "abc"
        self.assertNamed("tiers.t1_max_users")

    def test_bool_where_int_expected_is_c1(self):
        self.data["lint"]["freshness_days"]["value"] = True
        self.assertNamed("lint.freshness_days")

    def test_share_above_one_is_c1(self):
        self.data["sizing"]["chat"]["duty_low"]["value"] = 5
        self.assertNamed("sizing.chat.duty_low")

    def test_duty_low_above_duty_high_is_c1(self):
        self.data["sizing"]["rag"]["duty_low"]["value"] = 0.5
        self.data["sizing"]["rag"]["duty_high"]["value"] = 0.25
        self.assertNamed("sizing.rag.duty_low")

    def test_equal_user_thresholds_are_c1(self):
        self.data["tiers"]["t1_max_users"]["value"] = 300
        self.assertNamed("tiers.t1_max_users")

    def test_unordered_gpu_group_sizes_are_c1(self):
        self.data["sizing"]["gpu_group_sizes"]["value"] = [1, 4, 2]
        self.assertNamed("sizing.gpu_group_sizes")

    def test_empty_gpu_group_sizes_are_c1(self):
        self.data["sizing"]["gpu_group_sizes"]["value"] = []
        self.assertNamed("sizing.gpu_group_sizes")

    def test_negative_overhead_and_zero_bytes_are_c1(self):
        self.data["sizing"]["overhead"]["value"] = -0.1
        self.data["sizing"]["bytes_per_param"]["int4"]["value"] = 0
        self.assertNamed("sizing.overhead")
        self.assertNamed("sizing.bytes_per_param.int4")

    def test_failed_field_is_not_compared_again(self):
        self.data["tiers"]["t1_max_users"]["value"] = "abc"
        messages = [m for m in c1_messages(self.data) if "tiers.t1_max_users" in m]
        self.assertEqual(len(messages), 1, messages)

    def test_missing_constant_is_reported_once(self):
        del self.data["sizing"]["overhead"]
        messages = [m for m in c1_messages(self.data) if "sizing.overhead" in m]
        self.assertEqual(len(messages), 1, messages)


class EscalatorIdValidationTest(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(shipped_data())

    def test_escalator_that_is_not_a_table_is_c1(self):
        self.data["escalators"][1] = "audit"
        messages = c1_messages(self.data)
        self.assertTrue(any("escalators[1]" in m and "table" in m for m in messages), messages)

    def test_escalator_without_id_is_c1(self):
        del self.data["escalators"][0]["id"]
        messages = c1_messages(self.data)
        self.assertTrue(any("escalators[0]" in m and "'id'" in m for m in messages), messages)

    def test_duplicate_escalator_id_is_c1(self):
        self.data["escalators"][1]["id"] = self.data["escalators"][0]["id"]
        messages = c1_messages(self.data)
        self.assertTrue(any("escalators[1]" in m and "duplicate" in m for m in messages), messages)


if __name__ == "__main__":
    unittest.main()
