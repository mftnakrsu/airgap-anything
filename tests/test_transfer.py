import json
import tempfile
import unittest
from pathlib import Path

from tests import support
from airgap_lib.blueprint import inputs_digest
from airgap_lib.transfer import (
    MANIFEST_JSON_SCHEMA_VERSION,
    UnknownComponentError,
    build_manifest,
    read_manifest_digest,
    read_manifest_json_digest,
    render_json,
    render_manifest,
    render_markdown,
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
                "packages": [support.package("alpha-cli-1.2.3-amd64", checksums="https://downloads.example.test/SHA256SUMS")],
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

    def test_hardware_and_platform_lines_follow_the_digest_line(self):
        lines = self.text.splitlines()
        digest_at = next(i for i, line in enumerate(lines) if line.startswith("- Decisions digest: "))
        self.assertEqual(lines[digest_at + 1], "- Hardware: nvidia")
        self.assertEqual(lines[digest_at + 2], "- Platform: linux/amd64")

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
        self.assertIn(
            "| alpha-engine | 1.2.3 | alpha-cli-1.2.3-amd64 | amd64 "
            "| https://downloads.example.test/alpha-cli-1.2.3-amd64 "
            "| https://downloads.example.test/SHA256SUMS |",
            self.text,
        )
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
        self.assertIn("| custom: in-house portal |  | enumerate artifacts manually |  |  |  |", text)

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
                "packages": [support.package("beta-cli")],
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
        self.assertIn(f"| {self.MARK} | 1.2.3 | beta-cli | amd64 | ", text)
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


class ArchitectureManifestTest(unittest.TestCase):
    """Package rows follow hardware.cpu_arch; `any` rows always come along."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog = self.catalog_with(
            [
                support.package("alpha-1.2.3-amd64.tgz", "amd64"),
                support.package("alpha-1.2.3-arm64.tgz", "arm64"),
                support.package("install.sh", "any"),
            ]
        )

    def catalog_with(self, packages):
        components = support.fixture_components()
        components[0] = support.component("alpha-engine", "llm-serving", airgap={"packages": packages})
        root = Path(self.tmp.name) / f"catalog{len(list(Path(self.tmp.name).iterdir()))}"
        return support.load_fixture_catalog(root, components)

    def blueprint(self, arch):
        answers = support.base_answers()
        if arch is None:
            del answers["hardware.cpu_arch"]
        else:
            answers["hardware.cpu_arch"] = arch
        return {"project": "example", "answers": answers, "decisions": support.base_decisions()}

    def files(self, arch, catalog=None):
        data = build_manifest(self.blueprint(arch), catalog or self.catalog, "2026-11-20")
        return [row["file"] for row in data["packages"]]

    def test_amd64_takes_amd64_and_any_rows(self):
        self.assertEqual(self.files("amd64"), ["alpha-1.2.3-amd64.tgz", "install.sh"])

    def test_arm64_takes_arm64_and_any_rows(self):
        self.assertEqual(self.files("arm64"), ["alpha-1.2.3-arm64.tgz", "install.sh"])

    def test_unknown_takes_the_default_from_rules(self):
        self.assertEqual(self.files("unknown"), ["alpha-1.2.3-amd64.tgz", "install.sh"])
        text = render_manifest(self.blueprint("unknown"), self.catalog, "2026-11-20")
        self.assertIn("- Platform: linux/amd64", text)

    def test_unanswered_lists_every_row_and_says_so(self):
        for arch in (None, "sparc"):
            with self.subTest(arch=arch):
                self.assertEqual(len(self.files(arch)), 3)
                text = render_manifest(self.blueprint(arch), self.catalog, "2026-11-20")
                self.assertIn(
                    "- Platform: unknown; carry only the package rows for your CPU architecture", text
                )
                self.assertEqual(build_manifest(self.blueprint(arch), self.catalog, "2026-11-20")["platform"], "")

    def test_a_component_without_rows_for_the_platform_gets_a_line(self):
        catalog = self.catalog_with([support.package("alpha-1.2.3-amd64.tgz", "amd64")])
        self.assertEqual(self.files("arm64", catalog), [])
        text = render_manifest(self.blueprint("arm64"), catalog, "2026-11-20")
        line = "- alpha-engine: the catalog lists no package for linux/arm64; check the entry's notes before carrying."
        self.assertIn(line, text)
        # The line sits right after the packages table, before section 4.
        self.assertTrue(text.split("## 4. ")[0].rstrip().endswith("before carrying."))

    def test_package_row_columns(self):
        text = render_manifest(self.blueprint("arm64"), self.catalog, "2026-11-20")
        self.assertIn("| Component | Version | File | Arch | URL | Checksums |", text)
        self.assertIn(
            "| alpha-engine | 1.2.3 | alpha-1.2.3-arm64.tgz | arm64 "
            "| https://downloads.example.test/alpha-1.2.3-arm64.tgz |  |",
            text,
        )


class ManifestJsonTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        components = support.fixture_components()
        components[0] = support.component(
            "alpha-engine",
            "llm-serving",
            airgap={
                "images": [{"ref": "registry.example.test/synthetic/alpha:1", "digest": "", "hardware": ["nvidia"]}],
                "packages": [support.package("alpha-cli", "amd64", "https://downloads.example.test/SUMS")],
                "runtime_downloads": ["tokenizer data"],
                "telemetry": [{"what": "usage ping", "disable": "ALPHA_PING=0"}],
            },
            deeper_skills=[{"repo": "example/skills", "skill": "alpha-deployment"}],
        )
        self.catalog = support.load_fixture_catalog(Path(self.tmp.name), components)
        self.blueprint = {
            "project": "example",
            "answers": support.base_answers(),
            "decisions": support.base_decisions(),
        }
        self.blueprint["decisions"][0]["benchmark"] = ["beta-engine"]
        self.blueprint["decisions"][5]["custom"] = ["Docker Engine (outside the catalog)"]
        self.data = build_manifest(self.blueprint, self.catalog, "2026-11-20")

    def test_top_level_keys_of_schema_version_1(self):
        self.assertEqual(
            list(self.data),
            [
                "schema_version", "project", "generated", "inputs_digest", "hardware_class",
                "platform", "images", "models", "packages", "custom", "telemetry",
                "runtime_downloads", "skills", "missing_variants",
            ],
        )
        self.assertEqual(self.data["schema_version"], MANIFEST_JSON_SCHEMA_VERSION)
        self.assertEqual(self.data["schema_version"], 1)
        self.assertEqual(self.data["inputs_digest"], inputs_digest(self.blueprint))
        self.assertEqual((self.data["hardware_class"], self.data["platform"]), ("nvidia", "linux/amd64"))

    def test_rows(self):
        self.assertEqual(
            self.data["images"][0],
            {
                "component": "alpha-engine",
                "version": "1.2.3",
                "ref": "registry.example.test/synthetic/alpha:1",
                "hardware": ["nvidia"],
                "digest": "",
                "target": "REGISTRY_HOST/synthetic/alpha:1",
                "license": "MIT",
                "benchmark": False,
            },
        )
        self.assertEqual(
            self.data["packages"],
            [
                {
                    "component": "alpha-engine",
                    "version": "1.2.3",
                    "file": "alpha-cli",
                    "arch": "amd64",
                    "url": "https://downloads.example.test/alpha-cli",
                    "checksums": "https://downloads.example.test/SUMS",
                    "license": "MIT",
                    "benchmark": False,
                }
            ],
        )
        self.assertEqual(self.data["models"], [{"name": "example-70b", "role": "chat"}])
        self.assertEqual(self.data["custom"], [{"layer": "orchestration", "name": "Docker Engine (outside the catalog)"}])
        self.assertEqual(
            self.data["runtime_downloads"],
            [{"component": "alpha-engine", "text": "tokenizer data", "benchmark": False}],
        )
        self.assertEqual(
            self.data["skills"],
            [{"component": "alpha-engine", "repo": "example/skills", "skill": "alpha-deployment", "benchmark": False}],
        )

    def test_benchmark_rows_are_flagged(self):
        beta = [row for row in self.data["images"] if row["component"] == "beta-engine"]
        self.assertEqual([row["benchmark"] for row in beta], [True])

    def test_an_image_for_any_hardware_has_an_empty_list(self):
        gamma = next(row for row in self.data["images"] if row["component"] == "gamma-gateway")
        self.assertEqual(gamma["hardware"], [])

    def test_markdown_and_json_come_from_the_same_rows(self):
        self.assertEqual(render_markdown(self.data), render_manifest(self.blueprint, self.catalog, "2026-11-20"))
        text = render_json(self.data)
        self.assertTrue(text.endswith("}\n"))
        self.assertEqual(json.loads(text), self.data)
        self.assertEqual(read_manifest_json_digest(text), inputs_digest(self.blueprint))

    def test_json_digest_reader_tolerates_other_text(self):
        for text in ("", "not json", "[]", '{"inputs_digest": 5}'):
            with self.subTest(text=text):
                self.assertIsNone(read_manifest_json_digest(text))


if __name__ == "__main__":
    unittest.main()
