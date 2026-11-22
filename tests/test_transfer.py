import tempfile
import unittest
from pathlib import Path

from tests import support
from airgap_lib.blueprint import inputs_digest
from airgap_lib.transfer import (
    UnknownComponentError,
    read_manifest_digest,
    render_manifest,
    split_image_ref,
)


class ImageRefTest(unittest.TestCase):
    def test_registry_host_is_split_off(self):
        self.assertEqual(
            split_image_ref("registry.example.test/team/app:1.0"),
            ("registry.example.test", "team/app:1.0"),
        )
        self.assertEqual(split_image_ref("localhost:5000/app:1.0"), ("localhost:5000", "app:1.0"))

    def test_refs_without_a_registry_are_kept_whole(self):
        self.assertEqual(split_image_ref("team/app:1.0"), ("", "team/app:1.0"))
        self.assertEqual(split_image_ref("app:1.0"), ("", "app:1.0"))


class ManifestTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        components = support.fixture_components()
        components[0] = support.component(
            "alpha-engine",
            "llm-serving",
            airgap={
                "images": [
                    {"ref": "registry.example.test/synthetic/alpha-engine:1.2.3", "digest": "sha256:abc"}
                ],
                "packages": ["alpha-cli 1.2.3 binary"],
                "runtime_downloads": ["model weights"],
                "telemetry": [{"what": "usage statistics", "disable": "ALPHA_TELEMETRY=0"}],
            },
            deeper_skills=[{"repo": "example/skills", "skill": "alpha-deployment"}],
        )
        self.catalog = support.load_fixture_catalog(Path(self.tmp.name), components)
        self.blueprint = {
            "project": "example",
            "answers": support.base_answers(),
            "decisions": support.base_decisions(),
        }
        self.text = render_manifest(self.blueprint, self.catalog, "2026-11-20")

    def test_header_carries_date_and_digest(self):
        self.assertIn("# Transfer manifest: example", self.text)
        self.assertIn("- Generated: 2026-11-20", self.text)
        self.assertEqual(read_manifest_digest(self.text), inputs_digest(self.blueprint))

    def test_hardware_line_follows_the_digest_line(self):
        lines = self.text.splitlines()
        digest_at = next(i for i, line in enumerate(lines) if line.startswith("- Decisions digest: "))
        self.assertEqual(lines[digest_at + 1], "- Hardware: nvidia")

    def test_seven_sections_in_order(self):
        headings = [line for line in self.text.splitlines() if line.startswith("## ")]
        self.assertEqual([heading[3] for heading in headings], list("1234567"))

    def test_image_row_has_target_path_and_known_digest(self):
        self.assertIn(
            "| alpha-engine | 1.2.3 | registry.example.test/synthetic/alpha-engine:1.2.3 "
            "| any | sha256:abc |  | REGISTRY_HOST/synthetic/alpha-engine:1.2.3 |",
            self.text,
        )

    def test_other_tables_are_filled_from_the_catalog(self):
        self.assertIn("| example-70b | chat | weights, tokenizer and configuration files |  |", self.text)
        self.assertIn("| alpha-engine | 1.2.3 | alpha-cli 1.2.3 binary |", self.text)
        self.assertIn("| alpha-engine | usage statistics | ALPHA_TELEMETRY=0 |", self.text)
        self.assertIn("| alpha-engine | model weights |", self.text)
        self.assertIn("| alpha-engine | example/skills | alpha-deployment |", self.text)

    def test_every_chosen_component_appears(self):
        for decision in self.blueprint["decisions"]:
            for component_id in decision["components"]:
                self.assertIn(f"| {component_id} |", self.text)

    def test_custom_components_are_listed_for_manual_work(self):
        self.blueprint["decisions"][2]["custom"] = ["in-house portal"]
        text = render_manifest(self.blueprint, self.catalog, "2026-11-20")
        self.assertIn("| custom: in-house portal |  | enumerate artifacts manually |", text)

    def test_without_benchmark_nothing_is_marked(self):
        self.assertNotIn("benchmark only", self.text)

    def test_empty_tables_say_none(self):
        blueprint = dict(self.blueprint, decisions=[])
        text = render_manifest(blueprint, self.catalog, "2026-11-20")
        self.assertIn("## 1. Container images\n\nNone.", text)

    def test_unknown_component_is_an_error(self):
        self.blueprint["decisions"][0]["components"] = ["ghost"]
        with self.assertRaises(UnknownComponentError) as caught:
            render_manifest(self.blueprint, self.catalog, "2026-11-20")
        self.assertEqual(caught.exception.component_ids, ["ghost"])

    def test_output_is_deterministic(self):
        self.assertEqual(self.text, render_manifest(self.blueprint, self.catalog, "2026-11-20"))

    def test_digest_is_absent_from_other_text(self):
        self.assertIsNone(read_manifest_digest("# Something else\n"))


class BenchmarkManifestTest(unittest.TestCase):
    """A decision's `benchmark` components are listed, marked, in every section."""

    MARK = "beta-engine (benchmark only)"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        components = support.fixture_components()
        components[1] = support.component(
            "beta-engine",
            "llm-serving",
            airgap={
                "images": [
                    {"ref": "registry.example.test/synthetic/beta-nv:1", "hardware": ["nvidia"]},
                    {"ref": "registry.example.test/synthetic/beta-intel:1", "hardware": ["intel"]},
                ],
                "packages": ["beta-cli binary"],
                "runtime_downloads": ["tokenizer data"],
                "telemetry": [{"what": "beta usage ping", "disable": "BETA_PING=0"}],
            },
            deeper_skills=[{"repo": "example/skills", "skill": "beta-deployment"}],
        )
        self.catalog = support.load_fixture_catalog(Path(self.tmp.name), components)
        self.blueprint = {
            "project": "example",
            "answers": support.base_answers(),
            "decisions": support.base_decisions(),
        }
        self.blueprint["decisions"][0]["benchmark"] = ["beta-engine"]

    def render(self, blueprint=None):
        return render_manifest(blueprint or self.blueprint, self.catalog, "2026-11-20")

    def test_every_section_lists_the_component_marked(self):
        text = self.render()
        self.assertIn(
            f"| {self.MARK} | 1.2.3 | registry.example.test/synthetic/beta-nv:1 "
            "| nvidia | ",
            text,
        )
        self.assertIn(f"| {self.MARK} | 1.2.3 | beta-cli binary |", text)
        self.assertIn(f"| {self.MARK} | beta usage ping | BETA_PING=0 |", text)
        self.assertIn(f"| {self.MARK} | tokenizer data |", text)
        self.assertIn(f"| {self.MARK} | example/skills | beta-deployment |", text)

    def test_every_row_naming_the_component_is_marked(self):
        for line in self.render().splitlines():
            if "| beta-engine" in line:
                self.assertIn(self.MARK, line)

    def test_images_are_filtered_by_hardware_class(self):
        text = self.render()
        self.assertNotIn("beta-intel", text)
        self.blueprint["answers"]["hardware.gpus"] = [
            {"model": "Z", "count": 1, "vram_gb": 16, "vendor": "intel"}
        ]
        text = self.render()
        self.assertIn("beta-intel", text)
        self.assertNotIn("beta-nv", text)

    def test_unknown_hardware_lists_every_variant(self):
        self.blueprint["answers"]["hardware.gpus"] = [{"model": "Z", "count": 1, "vram_gb": 16}]
        text = self.render()
        self.assertIn("beta-nv", text)
        self.assertIn("beta-intel", text)

    def test_no_image_for_the_hardware_class_behaves_as_for_a_chosen_component(self):
        self.blueprint["answers"]["hardware.gpus"] = [
            {"model": "Z", "count": 1, "vram_gb": 16, "vendor": "amd"}
        ]
        text = self.render()
        self.assertNotIn("beta-nv", text)
        self.assertIn(
            "- beta-engine (benchmark only): the catalog lists no image for amd hardware; "
            "check the entry's notes before carrying.",
            text,
        )

    def test_a_chosen_component_is_not_marked(self):
        self.blueprint["decisions"][1]["benchmark"] = ["alpha-engine"]
        text = self.render()
        self.assertNotIn("alpha-engine (benchmark only)", text)
        self.assertIn("| alpha-engine | 1.2.3 | registry.example.test/synthetic/alpha-engine:1.2.3", text)

    def test_unknown_benchmark_component_is_an_error(self):
        self.blueprint["decisions"][0]["benchmark"] = ["ghost"]
        with self.assertRaises(UnknownComponentError) as caught:
            self.render()
        self.assertEqual(caught.exception.component_ids, ["ghost"])

    def test_digest_covers_the_benchmark(self):
        text = self.render()
        self.assertEqual(read_manifest_digest(text), inputs_digest(self.blueprint))
        del self.blueprint["decisions"][0]["benchmark"]
        self.assertNotEqual(read_manifest_digest(text), inputs_digest(self.blueprint))


HEADER = "| Component | Version | Image | For | Digest | Size | Target path |"


class HardwareManifestTest(unittest.TestCase):
    A = "registry.example.test/synthetic/a:1"
    B = "registry.example.test/synthetic/b:1"
    C = "registry.example.test/synthetic/c:1"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.images = [
            {"ref": self.A, "digest": "", "hardware": ["nvidia", "cpu"]},
            {"ref": self.B, "digest": "", "hardware": ["amd"]},
            {"ref": self.C, "digest": ""},
        ]
        self.catalog = self.catalog_with(self.images)

    def catalog_with(self, images, extra=()):
        components = support.fixture_components()
        components[0] = support.component("alpha-engine", "llm-serving", airgap={"images": images})
        root = Path(self.tmp.name) / f"catalog{len(list(Path(self.tmp.name).iterdir()))}"
        return support.load_fixture_catalog(root, components)

    def manifest(self, gpus, catalog=None):
        blueprint = {
            "project": "example",
            "answers": support.base_answers(**{"hardware.gpus": gpus}),
            "decisions": support.base_decisions(),
        }
        return render_manifest(blueprint, catalog or self.catalog, "2026-11-20")

    def listed(self, text):
        return [ref for ref in (self.A, self.B, self.C) if f"| {ref} |" in text]

    def test_vendor_answer_selects_nvidia_images(self):
        text = self.manifest([{"model": "Unlisted X", "count": 2, "vram_gb": 80, "vendor": "nvidia"}])
        self.assertEqual(self.listed(text), [self.A, self.C])
        self.assertIn("- Hardware: nvidia", text)
        self.assertIn(HEADER, text)
        self.assertIn(f"| {self.A} | nvidia, cpu |", text)
        self.assertIn(f"| {self.C} | any |", text)

    def test_gpu_table_vendor_is_used_without_an_answer(self):
        text = self.manifest([{"model": "TG141", "count": 8}])
        self.assertEqual(self.listed(text), [self.A, self.C])
        self.assertIn("- Hardware: nvidia", text)

    def test_vendor_answer_beats_the_table(self):
        text = self.manifest([{"model": "TG141", "count": 8, "vendor": "amd"}])
        self.assertEqual(self.listed(text), [self.B, self.C])
        self.assertIn("- Hardware: amd", text)

    def test_no_gpu_means_cpu(self):
        text = self.manifest([])
        self.assertEqual(self.listed(text), [self.A, self.C])
        self.assertIn("- Hardware: cpu", text)

    def test_primary_gpu_decides(self):
        gpus = [
            {"model": "Small", "count": 4, "vram_gb": 24, "vendor": "amd"},
            {"model": "Big", "count": 1, "vram_gb": 80, "vendor": "nvidia"},
        ]
        self.assertIn("- Hardware: nvidia", self.manifest(gpus))

    def test_unknown_gpu_lists_everything(self):
        text = self.manifest([{"model": "Mystery", "count": 1, "vram_gb": 80}])
        self.assertEqual(self.listed(text), [self.A, self.B, self.C])
        self.assertIn(
            "- Hardware: unknown; carry only the image rows for your hardware", text
        )
        self.assertNotIn("the catalog lists no image", text)

    def test_gpu_without_vram_does_not_raise(self):
        text = self.manifest([{"model": "Mystery", "count": 1}])
        self.assertEqual(self.listed(text), [self.A, self.B, self.C])
        self.assertIn("- Hardware: unknown;", text)

    def test_unfinished_blueprint_is_unknown(self):
        for answers in ({}, {"hardware.gpus": "TG141"}):
            with self.subTest(answers=answers):
                blueprint = {"project": "example", "answers": answers, "decisions": support.base_decisions()}
                text = render_manifest(blueprint, self.catalog, "2026-11-20")
                self.assertIn("- Hardware: unknown;", text)
                self.assertEqual(self.listed(text), [self.A, self.B, self.C])

    def test_missing_variant_line(self):
        catalog = self.catalog_with(self.images[:2])
        text = self.manifest([{"model": "Z", "count": 1, "vram_gb": 16, "vendor": "intel"}], catalog)
        self.assertEqual(self.listed(text), [])
        self.assertIn(
            "- alpha-engine: the catalog lists no image for intel hardware; "
            "check the entry's notes before carrying.",
            text,
        )
        # The line sits right after the images table, before section 2.
        before_models = text.split("## 2. Model artifacts")[0]
        self.assertTrue(before_models.rstrip().endswith("before carrying."))

    def test_components_without_hardware_keys_never_get_the_line(self):
        catalog = self.catalog_with([self.images[2]])
        for vendor in ("nvidia", "amd", "intel"):
            with self.subTest(vendor=vendor):
                text = self.manifest([{"model": "Z", "count": 1, "vram_gb": 16, "vendor": vendor}], catalog)
                self.assertNotIn("the catalog lists no image", text)

    def test_component_with_no_images_gets_no_line(self):
        catalog = self.catalog_with([])
        text = self.manifest([{"model": "Z", "count": 1, "vram_gb": 16, "vendor": "intel"}], catalog)
        self.assertNotIn("the catalog lists no image", text)

    def test_digest_still_reads_back(self):
        gpus = [{"model": "TG141", "count": 8}]
        text = self.manifest(gpus)
        blueprint = {
            "project": "example",
            "answers": support.base_answers(**{"hardware.gpus": gpus}),
            "decisions": support.base_decisions(),
        }
        self.assertEqual(read_manifest_digest(text), inputs_digest(blueprint))


if __name__ == "__main__":
    unittest.main()
