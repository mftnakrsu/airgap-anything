import tempfile
import unittest
from pathlib import Path

from tests import support
from airgap_lib.blueprint import (
    BlueprintError,
    benchmark_components,
    chosen_components,
    decision_for,
    has_override,
    inputs_digest,
    load_blueprint,
    save_blueprint,
    validate_schema,
)


class BlueprintFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_save_creates_directories_and_round_trips_unicode(self):
        path = self.root / "docs" / "airgap" / "blueprint.json"
        data = {"project": "örnek", "answers": {"org.users_total": 12}}
        save_blueprint(path, data)
        text = path.read_text(encoding="utf-8")
        self.assertIn("örnek", text)
        self.assertTrue(text.endswith("\n"))
        self.assertEqual(load_blueprint(path), data)

    def test_missing_file(self):
        with self.assertRaises(BlueprintError) as caught:
            load_blueprint(self.root / "nope.json")
        self.assertIn("file not found", str(caught.exception))

    def test_invalid_json(self):
        path = self.root / "blueprint.json"
        path.write_text("{ not json", encoding="utf-8")
        with self.assertRaises(BlueprintError) as caught:
            load_blueprint(path)
        self.assertIn("invalid JSON", str(caught.exception))

    def test_top_level_must_be_an_object(self):
        path = self.root / "blueprint.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaises(BlueprintError):
            load_blueprint(path)


class UnreadableFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_non_finite_numbers_are_rejected_on_load(self):
        for literal in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(literal=literal):
                path = self.root / "blueprint.json"
                path.write_text('{"answers": {"x": %s}}' % literal, encoding="utf-8")
                with self.assertRaises(BlueprintError) as caught:
                    load_blueprint(path)
                self.assertIn("non-finite number " + literal, str(caught.exception))

    def test_non_finite_numbers_are_rejected_on_save_and_digest(self):
        path = self.root / "out" / "blueprint.json"
        with self.assertRaises(BlueprintError):
            save_blueprint(path, {"answers": {"x": float("nan")}})
        self.assertFalse(path.exists())
        previous = self.root / "blueprint.json"
        save_blueprint(previous, {"a": 1})
        with self.assertRaises(BlueprintError):
            save_blueprint(previous, {"a": float("inf")})
        self.assertEqual(load_blueprint(previous), {"a": 1})
        with self.assertRaises(ValueError):
            inputs_digest({"decisions": [], "answers": {"workload.models": [float("nan")]}})

    def test_non_utf8_file(self):
        path = self.root / "blueprint.json"
        path.write_bytes(b"\xff\xfe{}")
        with self.assertRaises(BlueprintError) as caught:
            load_blueprint(path)
        self.assertIn("UTF-8", str(caught.exception))

    def test_directory_instead_of_file(self):
        with self.assertRaises(BlueprintError) as caught:
            load_blueprint(self.root)
        self.assertIn("cannot be read", str(caught.exception))

    def test_deeply_nested_file(self):
        path = self.root / "blueprint.json"
        path.write_text("[" * 100000 + "]" * 100000, encoding="utf-8")
        with self.assertRaises(BlueprintError):
            load_blueprint(path)
        path.write_text("[" * 100000, encoding="utf-8")
        with self.assertRaises(BlueprintError):
            load_blueprint(path)


def valid_blueprint() -> dict:
    return {
        "schema_version": 1,
        "project": "example",
        "created": "2026-11-20",
        "language": "en",
        "blueprint_path": "docs/airgap/blueprint.md",
        "answers": support.base_answers(),
        "assumptions": [
            {"id": "sizing.overhead", "value": 0.1, "evidence": "estimate", "note": "default"}
        ],
        "tier": {},
        "sizing": {},
        "decisions": support.base_decisions(),
    }


class SchemaTest(unittest.TestCase):
    def setUp(self):
        self.data = valid_blueprint()

    def test_complete_blueprint_is_valid(self):
        self.assertEqual(validate_schema(self.data), [])

    def test_assumptions_need_id_value_and_evidence(self):
        self.data["assumptions"].append({"id": "x", "evidence": "docs"})
        self.assertEqual(
            validate_schema(self.data),
            ["assumptions[1] needs id, value and a valid evidence label"],
        )

    def test_missing_key(self):
        del self.data["decisions"]
        self.assertEqual(validate_schema(self.data), ["missing key 'decisions'"])

    def test_wrong_type(self):
        self.data["schema_version"] = True
        self.assertEqual(validate_schema(self.data), ["'schema_version' must be of type int"])

    def test_created_must_be_a_date(self):
        self.data["created"] = "yesterday"
        self.assertEqual(validate_schema(self.data), ["'created' must be a date like 2026-11-20"])

    def test_duplicate_layer(self):
        self.data["decisions"].append(dict(self.data["decisions"][0]))
        self.assertEqual(
            validate_schema(self.data), ["decisions[8]: second decision for layer 'llm-serving'"]
        )

    def test_unhashable_layer_is_reported_without_crashing(self):
        for layer in (["a"], {"x": 1}):
            with self.subTest(layer=layer):
                self.data["decisions"][0]["layer"] = layer
                problems = validate_schema(self.data)
                self.assertEqual(len(problems), 1)
                self.assertTrue(problems[0].startswith("decisions[0].layer must be one of"))

    def test_decision_fields(self):
        decision = self.data["decisions"][0]
        decision["components"] = "alpha-engine"
        decision["evidence"] = "rumour"
        del decision["override"]
        problems = validate_schema(self.data)
        self.assertEqual(len(problems), 3)
        self.assertTrue(all(problem.startswith("decisions[0]") for problem in problems))

    def test_override_needs_a_reason(self):
        self.data["decisions"][0]["override"] = {"reason": " "}
        self.assertEqual(
            validate_schema(self.data),
            ["decisions[0].override must be null or an object with a reason"],
        )
        self.data["decisions"][0]["override"] = {"reason": "Pilot only."}
        self.assertEqual(validate_schema(self.data), [])
        self.assertTrue(has_override(self.data["decisions"][0]))

    def test_benchmark_is_optional_and_a_valid_list_passes(self):
        decision = self.data["decisions"][0]
        self.assertNotIn("benchmark", decision)
        decision["benchmark"] = []
        self.assertEqual(validate_schema(self.data), [])
        decision["benchmark"] = ["beta-engine"]
        self.assertEqual(validate_schema(self.data), [])

    def test_benchmark_must_be_a_list_of_strings(self):
        for value in ("beta-engine", None, ["beta-engine", 3], {"a": 1}):
            with self.subTest(value=value):
                self.data["decisions"][0]["benchmark"] = value
                self.assertEqual(
                    validate_schema(self.data),
                    ["decisions[0].benchmark must be a list of strings"],
                )

    def test_benchmark_rejects_a_duplicate(self):
        self.data["decisions"][0]["benchmark"] = ["beta-engine", "beta-engine"]
        self.assertEqual(
            validate_schema(self.data),
            ["decisions[0].benchmark lists 'beta-engine' more than once"],
        )

    def test_benchmark_rejects_an_id_the_decision_also_chooses(self):
        self.data["decisions"][0]["benchmark"] = ["alpha-engine"]
        self.assertEqual(
            validate_schema(self.data),
            ["decisions[0].benchmark lists 'alpha-engine', which is also in components"],
        )

    def test_benchmark_may_name_an_id_chosen_in_another_decision(self):
        self.data["decisions"][0]["benchmark"] = ["gamma-gateway"]
        self.assertEqual(validate_schema(self.data), [])


class DigestTest(unittest.TestCase):
    def setUp(self):
        self.data = {
            "answers": {"workload.models": [{"role": "chat", "weights_gb": 10}]},
            "decisions": support.base_decisions(),
        }

    def test_digest_is_stable_and_prefixed(self):
        digest = inputs_digest(self.data)
        self.assertTrue(digest.startswith("sha256:"))
        self.assertEqual(len(digest), len("sha256:") + 64)
        self.assertEqual(digest, inputs_digest(dict(self.data)))

    def test_digest_changes_with_decisions_and_models(self):
        before = inputs_digest(self.data)
        self.data["decisions"][0]["components"] = ["beta-engine"]
        after_decision = inputs_digest(self.data)
        self.assertNotEqual(before, after_decision)
        self.data["answers"]["workload.models"][0]["weights_gb"] = 20
        self.assertNotEqual(after_decision, inputs_digest(self.data))

    def test_digest_changes_with_gpus(self):
        before = inputs_digest(self.data)
        self.data["answers"]["hardware.gpus"] = [{"model": "TG141", "count": 8}]
        with_gpus = inputs_digest(self.data)
        self.assertNotEqual(before, with_gpus)
        self.data["answers"]["hardware.gpus"][0]["vendor"] = "nvidia"
        self.assertNotEqual(with_gpus, inputs_digest(self.data))

    def test_digest_changes_with_benchmark(self):
        before = inputs_digest(self.data)
        self.data["decisions"][0]["benchmark"] = ["beta-engine"]
        with_benchmark = inputs_digest(self.data)
        self.assertNotEqual(before, with_benchmark)
        self.data["decisions"][0]["benchmark"] = ["beta-engine", "gamma-engine"]
        self.assertNotEqual(with_benchmark, inputs_digest(self.data))

    def test_digest_changes_with_cpu_arch(self):
        before = inputs_digest(self.data)
        self.data["answers"]["hardware.cpu_arch"] = "amd64"
        amd64 = inputs_digest(self.data)
        self.assertNotEqual(before, amd64)
        self.data["answers"]["hardware.cpu_arch"] = "arm64"
        self.assertNotEqual(amd64, inputs_digest(self.data))

    def test_digest_ignores_other_answers(self):
        before = inputs_digest(self.data)
        self.data["answers"]["inside.operator"] = "local_agent"
        self.data["answers"]["transfer.channel"] = "data_diode"
        self.assertEqual(before, inputs_digest(self.data))

    def test_digest_ignores_other_keys(self):
        before = inputs_digest(self.data)
        self.data["project"] = "renamed"
        self.assertEqual(before, inputs_digest(self.data))

    def test_chosen_components_keep_order_without_duplicates(self):
        self.data["decisions"][1]["components"] = ["gamma-gateway", "alpha-engine"]
        self.assertEqual(chosen_components(self.data)[:2], ["alpha-engine", "gamma-gateway"])
        self.assertEqual(decision_for(self.data, "state")["components"], ["delta-db"])
        self.assertIsNone(decision_for({"decisions": []}, "state"))

    def test_benchmark_components_keep_order_without_duplicates(self):
        self.assertEqual(benchmark_components(self.data), [])
        self.data["decisions"][0]["benchmark"] = ["beta-engine", "sglang-like"]
        self.data["decisions"][1]["benchmark"] = ["sglang-like", "other"]
        self.assertEqual(
            benchmark_components(self.data), ["beta-engine", "sglang-like", "other"]
        )

    def test_benchmark_components_leave_out_chosen_components(self):
        self.data["decisions"][0]["benchmark"] = ["beta-engine", "delta-db"]
        self.assertEqual(benchmark_components(self.data), ["beta-engine"])

    def test_benchmark_components_ignore_malformed_values(self):
        self.data["decisions"][0]["benchmark"] = "beta-engine"
        self.data["decisions"][1]["benchmark"] = ["beta-engine", 3, None]
        self.assertEqual(benchmark_components(self.data), ["beta-engine"])


if __name__ == "__main__":
    unittest.main()
