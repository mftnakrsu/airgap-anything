import copy
import unittest

from tests import CATALOG_DIR, support
from airgap_lib.answers import QUESTIONS, REQUIRED_IDS, resolve_answers, validate_defaults
from airgap_lib.rules import Rules, load_rules


class ResolveAnswersTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def problems(self, answers, needed=None):
        return resolve_answers(answers, self.rules, needed)[2]

    def test_question_table_matches_the_spec(self):
        self.assertEqual(len(QUESTIONS), 19)
        self.assertEqual(len(REQUIRED_IDS), 14)

    def test_complete_answers_have_no_problems(self):
        resolved, assumptions, problems = resolve_answers(support.base_answers(), self.rules)
        self.assertEqual(problems, [])
        self.assertEqual(assumptions, [])
        self.assertEqual(resolved, support.base_answers())

    def test_missing_required_answer_is_listed_by_id(self):
        answers = support.base_answers()
        del answers["org.isolation"]
        self.assertEqual(self.problems(answers), ["org.isolation: missing"])

    def test_unknown_uses_the_documented_default(self):
        answers = support.base_answers(**{"org.audit_required": "unknown"})
        resolved, assumptions, problems = resolve_answers(answers, self.rules)
        self.assertEqual(problems, [])
        self.assertIs(resolved["org.audit_required"], True)
        self.assertEqual(
            assumptions,
            [
                {
                    "id": "answers.org.audit_required",
                    "value": True,
                    "evidence": "estimate",
                    "note": "answer was 'unknown'; default applied",
                }
            ],
        )

    def test_unknown_without_a_default_is_a_problem(self):
        answers = support.base_answers(**{"org.users_total": "unknown"})
        self.assertEqual(
            self.problems(answers),
            ["org.users_total: must be answered; 'unknown' has no default"],
        )

    def test_unknown_optional_answer_is_dropped(self):
        answers = support.base_answers(**{"transfer.cadence": "unknown"})
        resolved, assumptions, problems = resolve_answers(answers, self.rules)
        self.assertEqual(problems, [])
        self.assertEqual(assumptions, [])
        self.assertNotIn("transfer.cadence", resolved)

    def test_context_tokens_per_group_is_optional_and_valid(self):
        answers = support.base_answers(
            **{"workload.context_tokens": {"chat": 8192, "code_assistant": 32768, "rag": 16384}}
        )
        resolved, assumptions, problems = resolve_answers(answers, self.rules)
        self.assertEqual(problems, [])
        self.assertEqual(assumptions, [])
        self.assertEqual(resolved["workload.context_tokens"]["code_assistant"], 32768)
        self.assertEqual(self.problems(support.base_answers()), [])

    def test_context_tokens_problems(self):
        cases = [
            ({}, "must be a non-empty map of usage type to tokens"),
            ("long", "must be a non-empty map of usage type to tokens"),
            ({"batch": 4096}, "batch has no interactive context; give chat, code_assistant or rag"),
            ({"video": 4096}, "unknown usage type 'video'"),
            ({"chat": 0}, "tokens for 'chat' must be a whole number above 0"),
            ({"chat": -1}, "tokens for 'chat' must be a whole number above 0"),
            ({"chat": 8.5}, "tokens for 'chat' must be a whole number above 0"),
            ({"chat": True}, "tokens for 'chat' must be a whole number above 0"),
        ]
        for value, message in cases:
            with self.subTest(value=value):
                answers = support.base_answers(**{"workload.context_tokens": value})
                self.assertEqual(self.problems(answers), [f"workload.context_tokens: {message}"])

    def test_context_tokens_for_an_absent_group_is_allowed(self):
        answers = support.base_answers(**{"workload.context_tokens": {"rag": 4096}})
        self.assertEqual(self.problems(answers), [])

    def test_unknown_context_tokens_is_dropped(self):
        answers = support.base_answers(**{"workload.context_tokens": "unknown"})
        resolved, assumptions, problems = resolve_answers(answers, self.rules)
        self.assertEqual(problems, [])
        self.assertEqual(assumptions, [])
        self.assertNotIn("workload.context_tokens", resolved)

    def test_needed_limits_which_answers_are_checked(self):
        answers = {"org.users_total": 12, "org.departments": 1, "workload.usage": "nonsense"}
        self.assertEqual(self.problems(answers, ("org.users_total", "org.departments")), [])
        self.assertIn("org.isolation: missing", self.problems(answers))

    def test_assumptions_are_recorded_for_answers_outside_needed(self):
        answers = support.base_answers(**{"transfer.channel": "unknown"})
        _, assumptions, _ = resolve_answers(answers, self.rules, ("org.users_total",))
        self.assertEqual([item["id"] for item in assumptions], ["answers.transfer.channel"])

    def test_counts_reject_booleans_and_zero(self):
        self.assertTrue(self.problems(support.base_answers(**{"org.users_total": True})))
        self.assertTrue(self.problems(support.base_answers(**{"org.departments": 0})))

    def test_boolean_rejects_numbers(self):
        self.assertEqual(
            self.problems(support.base_answers(**{"org.audit_required": 1})),
            ["org.audit_required: must be true or false"],
        )

    def test_enum_lists_the_choices(self):
        problems = self.problems(support.base_answers(**{"org.isolation": "strict"}))
        self.assertEqual(
            problems, ["org.isolation: must be one of none, per_department, multi_level"]
        )

    def test_usage_shares_must_sum_to_one(self):
        problems = self.problems(support.base_answers(**{"workload.usage": {"chat": 0.5}}))
        self.assertEqual(problems, ["workload.usage: shares must sum to 1"])

    def test_usage_rejects_unknown_types(self):
        problems = self.problems(support.base_answers(**{"workload.usage": {"poetry": 1.0}}))
        self.assertEqual(problems, ["workload.usage: unknown usage type 'poetry'"])

    def test_model_needs_exactly_one_size(self):
        both = [{"role": "chat", "params_b": 70, "precision": "fp8", "weights_gb": 70}]
        neither = [{"role": "chat"}]
        for models in (both, neither):
            problems = self.problems(support.base_answers(**{"workload.models": models}))
            self.assertEqual(
                problems,
                ["workload.models: item 0: give exactly one of weights_gb, params_b, size_class"],
            )

    def test_model_with_params_needs_a_known_precision(self):
        models = [{"role": "chat", "params_b": 70, "precision": "fp12"}]
        problems = self.problems(support.base_answers(**{"workload.models": models}))
        self.assertEqual(len(problems), 1)
        self.assertIn("precision must be one of", problems[0])

    def test_size_class_and_weights_are_accepted(self):
        models = [
            {"role": "chat", "size_class": "M"},
            {"role": "embedding", "weights_gb": 2.5},
        ]
        self.assertEqual(self.problems(support.base_answers(**{"workload.models": models})), [])

    def test_arch_numbers_must_be_whole_and_positive(self):
        models = [
            {
                "role": "chat",
                "params_b": 70,
                "precision": "fp8",
                "arch": {"layers": 80, "kv_heads": 0, "head_dim": 128},
            }
        ]
        problems = self.problems(support.base_answers(**{"workload.models": models}))
        self.assertEqual(
            problems, ["workload.models: item 0: arch.kv_heads must be a whole number above 0"]
        )

    def test_gpu_entries_need_model_and_count(self):
        problems = self.problems(support.base_answers(**{"hardware.gpus": [{"model": "X"}]}))
        self.assertEqual(
            problems, ["hardware.gpus: item 0: count must be a whole number of 1 or more"]
        )

    def test_gpu_vendor_is_optional_and_limited(self):
        def gpus(**extra):
            return support.base_answers(**{"hardware.gpus": [{"model": "TG141", "count": 8, **extra}]})

        self.assertEqual(self.problems(gpus()), [])
        self.assertEqual(self.problems(gpus(vendor="nvidia")), [])
        self.assertEqual(
            self.problems(gpus(vendor="apple")),
            ["hardware.gpus: item 0: vendor must be one of nvidia, amd, intel"],
        )

    def test_no_gpu_requires_ram(self):
        answers = support.base_answers(**{"hardware.gpus": []})
        self.assertEqual(
            self.problems(answers),
            ["hardware.ram_gb: missing (required when hardware.gpus is empty)"],
        )
        answers["hardware.ram_gb"] = 256
        self.assertEqual(self.problems(answers), [])


class AnswerDefaultsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def rules_with_default(self, question_id, value):
        data = copy.deepcopy(self.rules.data)
        table = data.setdefault("defaults", {})
        *parents, leaf = question_id.split(".")
        for part in parents:
            table = table.setdefault(part, {})
        table[leaf] = {"value": value, "evidence": "estimate", "notes": "test"}
        return Rules(data)

    def test_shipped_defaults_pass(self):
        self.assertEqual(validate_defaults(self.rules), [])

    def test_default_outside_the_choices_is_reported(self):
        findings = validate_defaults(self.rules_with_default("org.isolation", "per_dept"))
        self.assertEqual([finding.code for finding in findings], ["C1"])
        self.assertIn("defaults.org.isolation", findings[0].message)
        self.assertIn("must be one of", findings[0].message)

    def test_default_for_a_question_that_must_be_answered_is_reported(self):
        findings = validate_defaults(self.rules_with_default("org.users_total", 10))
        self.assertEqual([finding.code for finding in findings], ["C1"])
        self.assertIn("defaults.org.users_total", findings[0].message)

    def test_default_for_an_unknown_question_is_reported(self):
        findings = validate_defaults(self.rules_with_default("org.nonsense", "x"))
        self.assertEqual([finding.code for finding in findings], ["C1"])
        self.assertIn("defaults.org.nonsense", findings[0].message)

    def test_usage_default_must_sum_to_one(self):
        findings = validate_defaults(self.rules_with_default("workload.usage", {"chat": 0.5}))
        self.assertEqual([finding.code for finding in findings], ["C1"])
        self.assertIn("defaults.workload.usage", findings[0].message)
        self.assertIn("shares must sum to 1", findings[0].message)

    def test_resolve_refuses_an_invalid_default(self):
        rules = self.rules_with_default("org.isolation", "per_dept")
        answers = support.base_answers(**{"org.isolation": "unknown"})
        resolved, assumptions, problems = resolve_answers(answers, rules)
        self.assertEqual(
            problems,
            [
                "org.isolation: default in rules.toml is invalid: "
                "must be one of none, per_department, multi_level"
            ],
        )
        self.assertEqual(resolved["org.isolation"], "unknown")
        self.assertEqual(assumptions, [])


if __name__ == "__main__":
    unittest.main()
