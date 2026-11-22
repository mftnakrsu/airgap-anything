import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests import projects, support
from airgap_lib.checks import lint_project, split_sections
from airgap_lib.constants import SECTION_MARKERS, section_marker
from airgap_lib.transfer import MANIFEST_FILENAME, MANIFEST_JSON_FILENAME


class LintTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.catalog = support.load_fixture_catalog(Path(self.tmp.name) / "catalog")

    def project(self, answers=None, decisions=None, verification="", isolation=False):
        self.path = projects.make_project(
            self.root, self.catalog, answers, decisions, verification, isolation
        )
        return self.path

    def lint(self, today=support.TODAY):
        return lint_project(self.path, self.catalog, self.root, today)

    def codes(self, today=support.TODAY):
        return [finding.code for finding in self.lint(today)]

    def edit(self, change, refresh_manifest=True):
        data = projects.edit_blueprint(self.path, change)
        if refresh_manifest:
            projects.write_manifests(self.path, self.catalog, data)
        return data

    def decision(self, data, layer):
        return next(d for d in data["decisions"] if d["layer"] == layer)


class CleanProjectTest(LintTestCase):
    def test_a_complete_project_has_no_findings(self):
        self.project()
        self.assertEqual(self.lint(), [])


class ErrorRulesTest(LintTestCase):
    def test_e1_schema_problem_stops_further_checks(self):
        self.project()
        self.edit(lambda data: data.pop("tier"), refresh_manifest=False)
        self.assertEqual(self.codes(), ["E1"])

    def test_e1_invalid_answer(self):
        self.project()
        self.edit(lambda data: data["answers"].update({"org.isolation": "strict"}))
        findings = self.lint()
        self.assertEqual(findings[0].code, "E1")
        self.assertIn("org.isolation", findings[0].message)

    def test_e1_invalid_context_tokens(self):
        self.project()
        self.edit(lambda data: data["answers"].update({"workload.context_tokens": {"batch": 4096}}))
        findings = self.lint()
        self.assertEqual(findings[0].code, "E1")
        self.assertIn("workload.context_tokens", findings[0].message)

    def test_e2_unknown_component(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "ui").update(components=["ghost"]),
            refresh_manifest=False,
        )
        self.assertIn("E2", self.codes())

    def test_e2_component_from_another_layer(self):
        self.project()
        self.edit(lambda data: self.decision(data, "ui").update(components=["delta-db"]))
        messages = [f.message for f in self.lint() if f.code == "E2"]
        self.assertEqual(messages, ["ui: 'delta-db' belongs to layer 'state'"])

    def test_e2_unknown_benchmark_component(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "llm-serving").update(benchmark=["ghost"]),
            refresh_manifest=False,
        )
        messages = [f.message for f in self.lint() if f.code == "E2"]
        self.assertEqual(messages, ["llm-serving: unknown component 'ghost'"])

    def test_e3_component_below_the_floor(self):
        answers = support.base_answers(**{"org.downtime_tolerance": "none"})
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(
            components=["beta-engine"], evidence="estimate"
        )
        self.project(answers, decisions, verification="llm-serving org.kubernetes_experience")
        self.assertEqual(self.codes(), ["E3"])

    def test_e3_override_is_reported_as_a_note_instead(self):
        answers = support.base_answers(**{"org.downtime_tolerance": "none"})
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(
            components=["beta-engine"],
            evidence="estimate",
            override={"reason": "Pilot phase runs on the small engine."},
        )
        self.project(answers, decisions, verification="llm-serving org.kubernetes_experience")
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["N1"])
        self.assertEqual(findings[0].severity, "note")
        self.assertEqual(
            findings[0].message,
            "llm-serving: override in effect: Pilot phase runs on the small engine.",
        )

    def test_e4_missing_decision_and_empty_rationale(self):
        self.project()
        self.edit(lambda data: data["decisions"].pop())
        self.edit(lambda data: self.decision(data, "ui").update(rationale="  "))
        messages = [f.message for f in self.lint() if f.code == "E4"]
        self.assertEqual(
            messages, ["ui: the decision has no rationale", "registry: no decision"]
        )

    def test_e5_required_gateway_is_empty(self):
        self.project()
        self.edit(lambda data: self.decision(data, "llm-gateway").update(components=[]))
        self.assertEqual(self.codes(), ["E5"])

    def test_e5_existing_gateway_counts(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "llm-gateway").update(
                components=[], existing=["corporate API gateway"]
            )
        )
        self.assertEqual(self.codes(), [])

    def test_e5_too_few_replicas(self):
        self.project(support.base_answers(**{"org.downtime_tolerance": "none"}),
                     verification="org.kubernetes_experience")
        self.edit(lambda data: data["sizing"]["models"][0].update(replicas=1))
        self.assertEqual(self.codes(), ["E5", "E6"])

    def test_e6_stale_sizing(self):
        self.project()
        self.edit(lambda data: data["answers"].update({"org.users_total": 20}))
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["E6"])
        self.assertIn("sizing is stale", findings[0].message)

    def test_e6_stale_tier(self):
        self.project()
        self.edit(lambda data: data["tier"].update(base="T3"))
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["E6"])
        self.assertIn("tier is stale", findings[0].message)

    def test_e7_missing_blueprint_file(self):
        self.project()
        (self.path.parent / "blueprint.md").unlink()
        self.assertEqual(self.codes(), ["E7"])

    def test_e7_missing_marker_and_missing_version(self):
        self.project()
        target = self.path.parent / "blueprint.md"
        text = target.read_text(encoding="utf-8")
        text = text.replace(section_marker("transfer"), "").replace("epsilon-ui 1.2.3", "epsilon-ui")
        target.write_text(text, encoding="utf-8")
        messages = [f.message for f in self.lint() if f.code == "E7"]
        self.assertEqual(len(messages), 2)
        self.assertIn("transfer", messages[0])
        self.assertIn("epsilon-ui", messages[1])

    def test_e7_isolation_design_marker(self):
        answers = support.base_answers(**{"org.isolation": "multi_level"})
        self.project(answers)
        self.assertEqual(self.codes(), ["E7"])
        self.project(answers, isolation=True)
        self.assertEqual(self.codes(), [])

    def test_e8_missing_and_stale_manifest(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "ui").update(rationale="Changed."),
            refresh_manifest=False,
        )
        self.assertEqual(self.codes(), ["E8", "E8"])
        (self.path.parent / MANIFEST_FILENAME).unlink()
        (self.path.parent / MANIFEST_JSON_FILENAME).unlink()
        self.assertEqual(self.codes(), ["E8", "E8"])

    def test_e8_checks_each_file_on_its_own(self):
        self.project()
        (self.path.parent / MANIFEST_JSON_FILENAME).unlink()
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["E8"])
        self.assertEqual(findings[0].message, "transfer-manifest.json not found; run manifest.py")
        self.project()
        (self.path.parent / MANIFEST_JSON_FILENAME).write_text('{"inputs_digest": "sha256:old"}', encoding="utf-8")
        findings = self.lint()
        self.assertEqual([f.message for f in findings], ["transfer-manifest.json is stale; run manifest.py again"])

    def test_e8_a_changed_cpu_arch_makes_both_files_stale(self):
        self.project()
        self.edit(lambda data: data["answers"].update({"hardware.cpu_arch": "arm64"}), refresh_manifest=False)
        self.assertEqual(self.codes(), ["E8", "E8"])

    def test_e9_estimate_decision_must_be_listed(self):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(
            components=["beta-engine"], evidence="estimate"
        )
        self.project(decisions=decisions)
        self.assertEqual(self.codes(), ["E9"])
        self.project(decisions=decisions, verification="Benchmark llm-serving before production.")
        self.assertEqual(self.codes(), [])

    def test_e9_label_must_be_the_weakest_input(self):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(components=["beta-engine"])
        self.project(decisions=decisions, verification="llm-serving")
        messages = [f.message for f in self.lint() if f.code == "E9"]
        self.assertEqual(len(messages), 1)
        self.assertIn("must be 'estimate'", messages[0])

    def test_e9_custom_components_count_as_estimates(self):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "ui").update(custom=["in-house portal"])
        self.project(decisions=decisions)
        self.assertEqual(self.codes(), ["E9", "E9"])

    def test_e9_benchmark_component_must_be_named_in_verification(self):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, "llm-serving").update(benchmark=["beta-engine"])
        self.project(decisions=decisions, verification="Benchmark llm-serving before production.")
        messages = [f.message for f in self.lint() if f.code == "E9"]
        self.assertEqual(
            messages,
            ["llm-serving: the benchmark component 'beta-engine' must be named in the "
             "verification section"],
        )
        self.project(decisions=decisions, verification="Benchmark beta-engine on this workload.")
        self.assertEqual(self.codes(), [])

    def test_benchmark_component_needs_no_version_line_or_requirements(self):
        decisions = support.base_decisions()
        # gamma-gateway requires delta-db, which is no longer chosen; as a benchmark
        # component it does not need it (E11), nor a version line (E7).
        self.decision({"decisions": decisions}, "state").update(components=[], existing=["db"])
        self.decision({"decisions": decisions}, "llm-gateway").update(components=[], existing=["gw"])
        self.decision({"decisions": decisions}, "llm-serving").update(
            benchmark=["beta-engine", "gamma-gateway"]
        )
        self.project(decisions=decisions, verification="Benchmark beta-engine and gamma-gateway.")
        self.assertEqual(self.codes(), [])

    def test_e9_kubernetes_risk_must_be_listed(self):
        self.project(support.base_answers(**{"org.downtime_tolerance": "none"}))
        self.assertEqual(self.codes(), ["E9"])

    def test_e10_hardware_does_not_fit(self):
        answers = support.base_answers(
            **{"workload.models": [{"role": "chat", "params_b": 671, "precision": "fp8"}],
               "hardware.gpus": [{"model": "TG141", "count": 4}]}
        )
        self.project(answers)
        self.assertEqual(self.codes(), ["E10"])
        self.edit(
            lambda data: self.decision(data, "llm-serving").update(
                override={"reason": "Four more GPUs are on order."}
            )
        )
        self.assertEqual(self.codes(), ["N1"])

    def test_e11_missing_required_component(self):
        self.project()
        self.edit(lambda data: self.decision(data, "state").update(components=[]))
        messages = [f.message for f in self.lint() if f.code == "E11"]
        self.assertEqual(len(messages), 1)
        self.assertIn("'gamma-gateway' requires 'delta-db'", messages[0])

    def test_e11_is_satisfied_by_existing_infrastructure(self):
        self.project()
        self.edit(
            lambda data: self.decision(data, "state").update(
                components=[], existing=["Delta-DB cluster run by the data team"]
            )
        )
        self.assertEqual(self.codes(), [])


class WarningRulesTest(LintTestCase):
    def test_w1_stale_component_in_use(self):
        self.project()
        self.assertEqual(self.codes(today=date(2027, 11, 20)), ["W1"] * 8)

    def test_w2_unknown_answer(self):
        self.project(support.base_answers(**{"transfer.channel": "unknown"}))
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["W2"])
        self.assertEqual(findings[0].severity, "warning")

    def test_w3_missing_agent_block(self):
        self.project()
        (self.root / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")
        self.assertEqual(self.codes(), ["W3"])
        (self.root / "AGENTS.md").unlink()
        self.assertEqual(self.codes(), ["W3"])


class VerificationTokenTest(LintTestCase):
    def estimate_decisions(self, layer):
        decisions = support.base_decisions()
        self.decision({"decisions": decisions}, layer).update(
            custom=["in-house component"], evidence="estimate"
        )
        return decisions

    def test_e9_layer_inside_other_words_does_not_count(self):
        self.project(
            decisions=self.estimate_decisions("ui"),
            verification="Run the load-test suite. Measure the time required to build and "
            "restore a backup. Read the quick guide for open-webui.",
        )
        messages = [f.message for f in self.lint() if f.code == "E9"]
        self.assertEqual(len(messages), 1)
        self.assertIn("ui: the decision rests on an estimate", messages[0])

    def test_e9_layer_named_as_a_token_counts(self):
        self.project(
            decisions=self.estimate_decisions("ui"),
            verification="Run the load-test suite.\nBenchmark ui before go-live.",
        )
        self.assertEqual(self.codes(), [])

    def test_e9_state_is_not_found_in_stateful(self):
        self.project(
            decisions=self.estimate_decisions("state"),
            verification="Check that stateful services restart.",
        )
        self.assertEqual(self.codes(), ["E9"])


class VersionLineTest(LintTestCase):
    """E7 counts the catalog version only whole, and only as the catalog writes it."""

    def e7_messages(self, version, line):
        """E7 messages when epsilon-ui is pinned to `version` and its decisions line is `line`."""
        components = [
            support.component("epsilon-ui", "ui", version=version)
            if entry["id"] == "epsilon-ui"
            else entry
            for entry in support.fixture_components()
        ]
        self.catalog = support.load_fixture_catalog(Path(self.tmp.name) / "catalog", components)
        self.project()
        target = self.path.parent / "blueprint.md"
        text = target.read_text(encoding="utf-8")
        old = f"- ui: epsilon-ui {version}\n"
        self.assertIn(old, text)
        target.write_text(text.replace(old, line + "\n"), encoding="utf-8")
        return [f.message for f in self.lint() if f.code == "E7"]

    def test_a_longer_version_does_not_name_the_pin(self):
        for version, line in (
            ("1.2.3", "- ui: epsilon-ui 1.2.30"),
            ("1.2.3", "- ui: epsilon-ui 11.2.3"),
            ("1.2.3", "- ui: epsilon-ui 1.2.3-rc1"),
            ("1.2.3", "- ui: epsilon-ui 1.2.3+build"),
            ("1.2.3", "- ui: epsilon-ui 1.2.3rc1 and 0.1.2.3"),
            ("18.7", "- ui: epsilon-ui 18.7.1"),
            ("v1.2.3", "- ui: epsilon-ui 1.2.3"),
        ):
            with self.subTest(version=version, line=line):
                self.assertEqual(
                    self.e7_messages(version, line),
                    [
                        "the decisions section needs a line naming 'epsilon-ui' with "
                        f"version {version}"
                    ],
                )

    def test_the_pin_followed_by_a_space_punctuation_or_the_line_end_counts(self):
        for version, line in (
            ("1.2.3", "- ui: epsilon-ui 1.2.3"),
            ("1.2.3", "- ui: epsilon-ui 1.2.3 (the pinned release)"),
            ("1.2.3", "| ui | epsilon-ui | 1.2.3 | docs |"),
            ("1.2.3", "- ui: epsilon-ui 1.2.3: the rationale."),
            ("1.2.3", "- ui: epsilon-ui (1.2.3), pinned; 1.2.30 is newer."),
            ("1.2.3", "- ui: registry.example.test/synthetic/epsilon-ui:1.2.3."),
            ("18.7", "- ui: epsilon-ui 18.7."),
            ("v1.2.3", "- ui: epsilon-ui v1.2.3"),
            ("v1.2.3+k3s1", "- ui: epsilon-ui `v1.2.3+k3s1`, as pinned"),
        ):
            with self.subTest(version=version, line=line):
                self.assertEqual(self.e7_messages(version, line), [])


class MalformedSizingTest(LintTestCase):
    def no_downtime_project(self):
        self.project(
            support.base_answers(**{"org.downtime_tolerance": "none"}),
            verification="org.kubernetes_experience",
        )

    def assert_e6_without_crash(self, change):
        self.no_downtime_project()
        self.edit(change)
        self.assertIn("E6", self.codes())

    def test_models_that_are_not_a_list(self):
        self.assert_e6_without_crash(lambda data: data["sizing"].update(models=5))

    def test_models_that_are_null(self):
        self.assert_e6_without_crash(lambda data: data["sizing"].update(models=None))

    def test_replicas_that_are_not_an_integer(self):
        self.assert_e6_without_crash(
            lambda data: data["sizing"]["models"][0].update(replicas="2")
        )

    def test_replicas_that_are_a_boolean(self):
        self.assert_e6_without_crash(
            lambda data: data["sizing"]["models"][0].update(replicas=True)
        )


class UnreadableFilesTest(LintTestCase):
    def test_non_utf8_agents_file_is_a_w3_finding(self):
        self.project()
        (self.root / "AGENTS.md").write_bytes(b"\xff\xfe\x00bad")
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["W3"])
        self.assertIn("AGENTS.md cannot be read", findings[0].message)

    def test_non_utf8_blueprint_file_is_an_e7_finding(self):
        self.project()
        (self.path.parent / "blueprint.md").write_bytes(b"\xff\xfe\x00bad")
        findings = self.lint()
        self.assertEqual([f.code for f in findings], ["E7"])
        self.assertIn("cannot be read", findings[0].message)
        self.assertNotIn("not found", findings[0].message)

    def test_non_utf8_manifest_is_an_e8_finding(self):
        for name in (MANIFEST_FILENAME, MANIFEST_JSON_FILENAME):
            with self.subTest(name=name):
                self.project()
                (self.path.parent / name).write_bytes(b"\xff\xfe\x00bad")
                findings = self.lint()
                self.assertEqual([f.code for f in findings], ["E8"])
                self.assertEqual(findings[0].message, f"{name} cannot be read: it is not valid UTF-8")

    def test_blueprint_path_below_a_regular_file(self):
        self.project()
        self.edit(lambda data: data.update(blueprint_path="AGENTS.md/blueprint.md"))
        findings = [f for f in self.lint() if f.code == "E7"]
        self.assertEqual(len(findings), 1)
        self.assertIn("cannot be read", findings[0].message)

    def test_blueprint_path_with_a_nul_character(self):
        self.project()
        self.edit(lambda data: data.update(blueprint_path="docs/\x00blueprint.md"))
        self.assertIn("E7", self.codes())

    def test_blueprint_path_that_is_a_directory(self):
        self.project()
        self.edit(lambda data: data.update(blueprint_path="docs"))
        findings = [f for f in self.lint() if f.code == "E7"]
        self.assertEqual(len(findings), 1)
        self.assertIn("cannot be read", findings[0].message)


class SectionsTest(unittest.TestCase):
    def test_sections_are_split_at_markers(self):
        text = "\n".join(f"{section_marker(name)}\nbody of {name}" for name in SECTION_MARKERS)
        sections, problems = split_sections(text)
        self.assertEqual(problems, [])
        self.assertEqual(list(sections), list(SECTION_MARKERS))
        self.assertIn("body of sizing", sections["sizing"])
        self.assertNotIn("body of transfer", sections["sizing"])

    def test_out_of_order_markers_are_reported(self):
        names = list(SECTION_MARKERS)
        names[0], names[1] = names[1], names[0]
        text = "\n".join(section_marker(name) for name in names)
        self.assertEqual(split_sections(text)[1], ["section markers are out of order"])


if __name__ == "__main__":
    unittest.main()
