import json
import unittest

import tests  # noqa: F401  (puts the scripts directory on sys.path)
from airgap_lib.constants import (
    LAYERS,
    SECTION_MARKERS,
    TIERS,
    max_tier,
    section_marker,
    tier_index,
    weakest,
)
from airgap_lib.evidence import evidence_problems
from airgap_lib.findings import Finding, format_json, format_text, has_errors


class ConstantsTest(unittest.TestCase):
    def test_tiers_and_layers_of_the_spec(self):
        self.assertEqual(TIERS, ("T1", "T2", "T3"))
        self.assertEqual(
            LAYERS,
            (
                "llm-serving", "llm-gateway", "ui", "identity",
                "observability", "orchestration", "state", "registry",
            ),
        )
        self.assertEqual(len(SECTION_MARKERS), 10)

    def test_tier_order(self):
        self.assertEqual(tier_index("T2"), 1)
        self.assertEqual(max_tier("T1", "T3"), "T3")
        self.assertEqual(max_tier("T2", "T2"), "T2")
        self.assertEqual(max_tier("T3", "T1"), "T3")

    def test_weakest_evidence_label(self):
        self.assertEqual(weakest(["docs", "field"]), "docs")
        self.assertEqual(weakest(["field", "estimate", "docs"]), "estimate")
        self.assertEqual(weakest(["field"]), "field")
        self.assertEqual(weakest([]), "field")

    def test_section_marker_text(self):
        self.assertEqual(section_marker("sizing"), "<!-- airgap:section sizing -->")


class EvidencePolicyTest(unittest.TestCase):
    def test_docs_needs_a_url(self):
        self.assertEqual(evidence_problems("docs", ["https://example.test/a"], "", ""), [])
        self.assertEqual(len(evidence_problems("docs", [], "", "")), 1)
        self.assertEqual(len(evidence_problems("docs", ["not a url"], "", "")), 1)
        self.assertEqual(len(evidence_problems("docs", None, "", "")), 1)

    def test_field_needs_a_verifier_and_notes(self):
        self.assertEqual(evidence_problems("field", [], "someone", "2x GPU, lab"), [])
        self.assertEqual(len(evidence_problems("field", [], "", "")), 2)

    def test_estimate_needs_notes(self):
        self.assertEqual(evidence_problems("estimate", [], "", "reasoned from X"), [])
        self.assertEqual(len(evidence_problems("estimate", [], "", "  ")), 1)

    def test_unknown_level(self):
        problems = evidence_problems("rumour", [], "", "")
        self.assertEqual(problems, ["evidence level must be one of estimate, docs, field"])


class FindingsTest(unittest.TestCase):
    def setUp(self):
        self.findings = [Finding("E3", "broken"), Finding("W1", "old"), Finding("C1", "bad")]

    def test_severity_comes_from_the_code_letter(self):
        self.assertEqual([f.severity for f in self.findings], ["error", "warning", "error"])

    def test_notes_are_a_third_severity(self):
        self.assertEqual(Finding("N1", "override").severity, "note")

    def test_has_errors(self):
        self.assertTrue(has_errors(self.findings))
        self.assertFalse(has_errors([Finding("W2", "unknown answer"), Finding("N1", "override")]))
        self.assertFalse(has_errors([]))

    def test_text_report(self):
        self.assertEqual(format_text([]), "OK: no findings")
        lines = format_text(self.findings).splitlines()
        self.assertEqual(lines[0], "E3 error: broken")
        self.assertEqual(lines[1], "W1 warning: old")
        self.assertEqual(lines[-1], "2 error(s), 1 warning(s), 0 note(s)")

    def test_json_report(self):
        report = json.loads(format_json(self.findings))
        self.assertEqual(report[1], {"code": "W1", "severity": "warning", "message": "old"})


if __name__ == "__main__":
    unittest.main()
