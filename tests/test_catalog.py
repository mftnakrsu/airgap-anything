import tempfile
import unittest
from datetime import date, datetime
from pathlib import Path

from tests import support
from airgap_lib.catalog import (
    load_catalog,
    validate_catalog,
    validate_component,
    validate_gpus,
)


def codes(findings):
    return [finding.code for finding in findings]


class CatalogLoadingTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def test_fixture_catalog_loads_and_validates(self):
        catalog, findings = load_catalog(support.make_catalog(self.root))
        self.assertEqual(findings, [])
        self.assertEqual(len(catalog.components), 9)
        self.assertEqual(validate_catalog(catalog, support.TODAY), [])

    def test_gpu_lookup_ignores_case_and_punctuation(self):
        catalog = support.load_fixture_catalog(self.root)
        self.assertEqual(catalog.gpu("tg-141")["vram_gb"], 141)
        self.assertEqual(catalog.gpu("TEST GPU 141")["tdp_w"], 700)
        self.assertIsNone(catalog.gpu("no such gpu"))

    def test_file_name_must_match_id(self):
        support.make_catalog(self.root)
        entry = support.component("mismatch", "ui")
        (self.root / "components" / "other-name.toml").write_text(
            support.component_toml(entry), encoding="utf-8"
        )
        catalog, findings = load_catalog(self.root)
        self.assertEqual(codes(findings), ["C2"])
        self.assertNotIn("mismatch", catalog.components)

    def test_unparsable_file_is_c2(self):
        support.make_catalog(self.root)
        (self.root / "components" / "broken.toml").write_text("id = = 1\n", encoding="utf-8")
        _, findings = load_catalog(self.root)
        self.assertEqual(codes(findings), ["C2"])

    def test_unreadable_file_is_c2_and_others_still_load(self):
        support.make_catalog(self.root)
        (self.root / "components" / "garbled.toml").write_bytes(b"\xff\xfe")
        catalog, findings = load_catalog(self.root)
        self.assertEqual(codes(findings), ["C2"])
        self.assertIn("garbled.toml", findings[0].message)
        self.assertNotIn("garbled", catalog.components)
        self.assertEqual(len(catalog.components), 9)

    def test_stale_entry_is_w1(self):
        old = support.component("epsilon-ui", "ui", last_verified=date(2026, 1, 1))
        components = [c for c in support.fixture_components() if c["id"] != "epsilon-ui"] + [old]
        catalog = support.load_fixture_catalog(self.root, components)
        findings = validate_catalog(catalog, support.TODAY)
        self.assertEqual(codes(findings), ["W1"])
        self.assertIn("epsilon-ui", findings[0].message)

    def test_datetime_last_verified_is_c1_and_does_not_crash(self):
        entry = support.component(
            "epsilon-ui", "ui", last_verified=datetime(2026, 11, 20, 10, 0, 0)
        )
        components = [c for c in support.fixture_components() if c["id"] != "epsilon-ui"] + [entry]
        catalog, findings = load_catalog(support.make_catalog(self.root, components))
        self.assertEqual(findings, [])
        result = validate_catalog(catalog, support.TODAY)
        self.assertEqual(codes(result), ["C1"])
        self.assertIn("last_verified", result[0].message)


class GpuValidationTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def check(self, row_toml):
        """Findings from validate_gpus for one [[gpu]] row, loaded through a catalog."""
        gpus_toml = "schema_version = 1\n\n[[gpu]]\n" + row_toml
        catalog, findings = load_catalog(support.make_catalog(self.root, gpus_toml=gpus_toml))
        self.assertEqual(findings, [])
        return validate_gpus(catalog.gpus)

    def row(self, **replace):
        """A valid row as TOML lines, with some keys replaced (None drops the key)."""
        fields = {
            "model": '"Test GPU 141"',
            "aliases": '["TG141"]',
            "vendor": '"nvidia"',
            "vram_gb": "141",
            "tdp_w": "700",
            "evidence": '"estimate"',
            "notes": '"Synthetic row for tests."',
            "last_verified": "2026-11-20",
        }
        fields.update(replace)
        return "".join(f"{key} = {value}\n" for key, value in fields.items() if value is not None)

    def test_valid_row(self):
        self.assertEqual(self.check(self.row()), [])

    def test_tdp_is_optional(self):
        self.assertEqual(self.check(self.row(tdp_w=None)), [])

    def test_unknown_key_is_c1(self):
        findings = self.check(self.row(vram="80"))
        self.assertEqual(codes(findings), ["C1"])
        self.assertIn("unknown key 'vram'", findings[0].message)

    def test_missing_model_is_c1(self):
        self.assertEqual(codes(self.check(self.row(model=None))), ["C1"])

    def test_aliases_must_be_strings(self):
        findings = self.check(self.row(aliases="[1, 2]"))
        self.assertEqual(codes(findings), ["C1"])
        self.assertIn("aliases", findings[0].message)

    def test_missing_vram_is_c1(self):
        findings = self.check(self.row(vram_gb=None))
        self.assertEqual(codes(findings), ["C1"])
        self.assertIn("vram_gb", findings[0].message)

    def test_non_positive_vram_is_c1(self):
        findings = self.check(self.row(vram_gb="0"))
        self.assertEqual(codes(findings), ["C1"])
        self.assertIn("vram_gb", findings[0].message)

    def test_bad_tdp_is_c1(self):
        for bad in ("-5", '"700"', "true"):
            with self.subTest(tdp_w=bad):
                findings = self.check(self.row(tdp_w=bad))
                self.assertEqual(codes(findings), ["C1"])
                self.assertIn("tdp_w", findings[0].message)

    def test_quoted_last_verified_is_c1(self):
        findings = self.check(self.row(last_verified='"2026-11-20"'))
        self.assertEqual(codes(findings), ["C1"])
        self.assertIn("last_verified", findings[0].message)

    def test_datetime_last_verified_is_c1_and_does_not_crash(self):
        gpus_toml = "schema_version = 1\n\n[[gpu]]\n" + self.row(last_verified="2026-11-20T10:00:00")
        catalog, findings = load_catalog(support.make_catalog(self.root, gpus_toml=gpus_toml))
        self.assertEqual(findings, [])
        result = validate_catalog(catalog, support.TODAY)
        self.assertEqual(codes(result), ["C1"])
        self.assertIn("last_verified", result[0].message)

    def test_docs_without_a_source_is_c4(self):
        self.assertEqual(codes(self.check(self.row(evidence='"docs"'))), ["C4"])

    def test_vendor_is_required_and_limited(self):
        for bad in (None, '"apple"', "1"):
            with self.subTest(vendor=bad):
                findings = self.check(self.row(vendor=bad))
                self.assertEqual(codes(findings), ["C1"])
                self.assertIn("vendor must be one of nvidia, amd, intel", findings[0].message)
                self.assertIn("gpu[0]", findings[0].message)

    def test_each_vendor_is_accepted(self):
        for vendor in ("nvidia", "amd", "intel"):
            with self.subTest(vendor=vendor):
                self.assertEqual(self.check(self.row(vendor=f'"{vendor}"')), [])

    def check_rows(self, *row_tomls):
        """Findings from validate_gpus for several [[gpu]] rows, in file order."""
        gpus_toml = "schema_version = 1\n" + "".join("\n[[gpu]]\n" + row for row in row_tomls)
        catalog, findings = load_catalog(support.make_catalog(self.root, gpus_toml=gpus_toml))
        self.assertEqual(findings, [])
        return validate_gpus(catalog.gpus)

    def test_non_finite_numbers_are_c1(self):
        for key, bad in (("vram_gb", "nan"), ("vram_gb", "inf"), ("tdp_w", "inf")):
            with self.subTest(key=key, value=bad):
                findings = self.check(self.row(**{key: bad}))
                self.assertEqual(codes(findings), ["C1"])
                self.assertEqual(
                    findings[0].message,
                    f"gpus.toml: gpu[0]: {key} must be a number above 0",
                )

    def test_placeholder_in_a_row_is_c1(self):
        findings = self.check(self.row(notes='"<notes>"'))
        self.assertEqual(codes(findings), ["C1"])
        self.assertEqual(findings[0].message, "gpus.toml: gpu[0]: notes still holds a placeholder")

    def test_placeholder_paths_in_lists(self):
        findings = self.check(self.row(aliases='["<alias>"]'))
        self.assertIn(
            "gpus.toml: gpu[0]: aliases[0] still holds a placeholder",
            [finding.message for finding in findings],
        )

    def test_shared_alias_is_c1_on_the_later_row(self):
        findings = self.check_rows(
            self.row(model='"A100 40GB"', aliases='["A100"]'),
            self.row(model='"A100 80GB"', aliases='["A100"]'),
        )
        self.assertEqual(codes(findings), ["C1"])
        self.assertEqual(
            findings[0].message,
            "gpus.toml: gpu[1]: name 'A100' is already used by gpu[0]",
        )

    def test_names_collide_after_normalization(self):
        findings = self.check_rows(
            self.row(model='"A100 40GB"', aliases='["A100"]'),
            self.row(model='"A100 80GB"', aliases='["a-100"]'),
        )
        self.assertEqual(codes(findings), ["C1"])
        self.assertEqual(
            findings[0].message,
            "gpus.toml: gpu[1]: name 'a-100' is already used by gpu[0]",
        )

    def test_variants_without_a_shared_name_are_fine(self):
        findings = self.check_rows(
            self.row(model='"A100 40GB"', aliases='[]'),
            self.row(model='"A100 80GB"', aliases='[]'),
        )
        self.assertEqual(findings, [])

    def test_name_without_letters_or_digits_is_c1(self):
        findings = self.check(self.row(aliases='["--"]'))
        self.assertEqual(codes(findings), ["C1"])
        self.assertEqual(
            findings[0].message,
            "gpus.toml: gpu[0]: name '--' has no letters or digits",
        )

    def test_same_name_twice_within_one_row_is_fine(self):
        findings = self.check(self.row(model='"H200"', aliases='["H200", "NVIDIA H200"]'))
        self.assertEqual(findings, [])


class ComponentValidationTest(unittest.TestCase):
    def check(self, entry, known=("x",)):
        return validate_component(entry, set(known))

    def test_valid_component(self):
        self.assertEqual(self.check(support.component("x", "ui")), [])

    def test_latest_is_not_a_version(self):
        self.assertIn("C1", codes(self.check(support.component("x", "ui", version="latest"))))

    def test_placeholder_values_are_rejected(self):
        findings = self.check(support.component("x", "ui", version="<exact version>"))
        self.assertTrue(any(f.code == "C1" and "placeholder" in f.message for f in findings))

    def test_nested_placeholder_is_rejected(self):
        entry = support.component("x", "ui", airgap={"images": [{"ref": "<registry/repository:tag>", "digest": ""}]})
        findings = self.check(entry)
        self.assertTrue(any("airgap.images[0].ref" in f.message for f in findings))

    def image_findings(self, image):
        entry = support.component("x", "ui", airgap={"images": [image]})
        return self.check(entry)

    def test_image_hardware_is_accepted(self):
        for hardware in (["nvidia"], ["nvidia", "cpu"], ["amd", "intel"]):
            with self.subTest(hardware=hardware):
                image = {"ref": "r.example.test/a:1", "digest": "", "hardware": hardware}
                self.assertEqual(self.image_findings(image), [])

    def test_bad_image_hardware_is_c1(self):
        message = "airgap.images[0].hardware must be a non-empty list of: nvidia, amd, intel, cpu"
        for bad in ([], ["nvidia", "nvidia"], ["tpu"], "nvidia", [1]):
            with self.subTest(hardware=bad):
                image = {"ref": "r.example.test/a:1", "digest": "", "hardware": bad}
                findings = self.image_findings(image)
                self.assertEqual(codes(findings), ["C1"])
                self.assertEqual(findings[0].message, f"x: {message}")

    def test_unknown_image_key_is_c1(self):
        findings = self.image_findings({"ref": "r.example.test/a:1", "digest": "", "arch": "x"})
        self.assertEqual(codes(findings), ["C1"])
        self.assertEqual(findings[0].message, "x: unknown key 'airgap.images[0].arch'")

    def test_packages_take_no_hardware_key(self):
        entry = support.component("x", "ui", airgap={"packages": [{"name": "a", "hardware": ["cpu"]}]})
        self.assertIn("C1", codes(self.check(entry)))

    def test_unknown_layer_and_tier(self):
        self.assertIn("C1", codes(self.check(support.component("x", "no-such-layer"))))
        self.assertIn("C1", codes(self.check(support.component("x", "ui", tiers=["T4"]))))
        self.assertIn("C1", codes(self.check(support.component("x", "ui", tiers=[]))))

    def test_unknown_key_is_c1(self):
        entry = support.component("x", "ui")
        entry["telemetery"] = []
        findings = self.check(entry)
        self.assertTrue(any("unknown key 'telemetery'" in f.message for f in findings))

    def test_missing_table_is_c1(self):
        entry = support.component("x", "ui")
        del entry["airgap"]
        self.assertTrue(any("[airgap]" in f.message for f in self.check(entry)))

    def test_quoted_date_is_c1(self):
        entry = support.component("x", "ui", last_verified="2026-11-20")
        self.assertTrue(any("last_verified" in f.message for f in self.check(entry)))

    def test_docs_needs_a_url(self):
        entry = support.component("x", "ui", evidence={"level": "docs", "sources": []})
        self.assertEqual(codes(self.check(entry)), ["C4"])

    def test_field_needs_verifier_and_notes(self):
        entry = support.component("x", "ui", evidence={"level": "field", "sources": []})
        self.assertEqual(codes(self.check(entry)), ["C4", "C4"])

    def test_estimate_needs_notes(self):
        entry = support.component("x", "ui", evidence={"level": "estimate", "sources": [], "notes": " "})
        self.assertEqual(codes(self.check(entry)), ["C4"])

    def test_unknown_reference_is_c3(self):
        entry = support.component("x", "ui", requires=["ghost"], choose={"alternatives": ["phantom"]})
        self.assertEqual(codes(self.check(entry)), ["C3", "C3"])

    def test_bad_id_is_c1(self):
        self.assertIn("C1", codes(self.check(support.component("Bad_ID", "ui"), known=("Bad_ID",))))


if __name__ == "__main__":
    unittest.main()
