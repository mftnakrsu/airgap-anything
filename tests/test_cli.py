import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from tests import SCRIPTS_DIR, projects, support
from airgap_lib.blueprint import load_blueprint, save_blueprint
from airgap_lib.catalog import load_catalog
from airgap_lib.transfer import MANIFEST_FILENAME, MANIFEST_JSON_FILENAME


class CliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.catalog_dir = support.make_catalog(Path(self.tmp.name) / "catalog")
        self.root = Path(self.tmp.name) / "project"
        self.blueprint = self.root / "docs" / "airgap" / "blueprint.json"

    def start(self, answers=None):
        """Write the blueprint.json an interview leaves behind: answers only."""
        save_blueprint(
            self.blueprint,
            {
                "schema_version": 1,
                "project": "example",
                "created": "2026-11-20",
                "language": "en",
                "blueprint_path": "docs/airgap/blueprint.md",
                "answers": support.base_answers() if answers is None else answers,
                "assumptions": [],
                "tier": {},
                "sizing": {},
                "decisions": [],
            },
        )

    def run_script(self, name, *args, catalog=True):
        command = [sys.executable, str(SCRIPTS_DIR / name)]
        if catalog:
            command += ["--catalog", str(self.catalog_dir)]
        return subprocess.run(command + list(args), capture_output=True, text=True)

    def with_blueprint(self, name, *args):
        return self.run_script(name, "--blueprint", str(self.blueprint), *args)

    def lint(self, *args):
        return self.with_blueprint(
            "lint.py", "--project-root", str(self.root), "--today", "2026-11-20", *args
        )


class PipelineTest(CliTestCase):
    def test_tier_size_manifest_lint_in_order(self):
        self.start()

        tier = self.with_blueprint("tier.py")
        self.assertEqual(tier.returncode, 0, tier.stderr)
        self.assertIn("Base tier: T2", tier.stdout)
        self.assertEqual(load_blueprint(self.blueprint)["tier"]["base"], "T2")

        size = self.with_blueprint("size.py")
        self.assertEqual(size.returncode, 0, size.stderr)
        self.assertIn("Peak concurrency: 9-18", size.stdout)
        self.assertIn("benchmark before production", size.stdout)
        data = load_blueprint(self.blueprint)
        self.assertEqual(data["sizing"]["total_gpus"], 1)
        self.assertIn("sizing.overhead", [item["id"] for item in data["assumptions"]])

        data = projects.edit_blueprint(
            self.blueprint, lambda d: d.update(decisions=support.base_decisions())
        )
        manifest = self.with_blueprint("manifest.py", "--date", "2026-11-20")
        self.assertEqual(manifest.returncode, 0, manifest.stderr)
        self.assertTrue((self.blueprint.parent / MANIFEST_FILENAME).is_file())
        self.assertTrue((self.blueprint.parent / MANIFEST_JSON_FILENAME).is_file())
        self.assertEqual(
            manifest.stdout.splitlines(),
            [f"Wrote {self.blueprint.parent / MANIFEST_FILENAME}", f"Wrote {self.blueprint.parent / MANIFEST_JSON_FILENAME}"],
        )

        catalog, _ = load_catalog(self.catalog_dir)
        (self.blueprint.parent / "blueprint.md").write_text(
            projects.blueprint_markdown(data, catalog), encoding="utf-8"
        )
        (self.root / "AGENTS.md").write_text(projects.AGENTS_TEXT, encoding="utf-8")
        lint = self.lint()
        self.assertEqual(lint.returncode, 0, lint.stdout + lint.stderr)
        self.assertIn("OK: no findings", lint.stdout)


class KvCacheReportTest(CliTestCase):
    ARCH = {"layers": 80, "kv_heads": 8, "head_dim": 128, "kv_dtype": "fp16"}

    def size_with(self, **overrides):
        models = [
            {"name": "example-70b", "role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}
        ]
        gpus = [{"model": "big", "count": 24, "vram_gb": 141}]
        self.start(
            support.base_answers(
                **{
                    "org.users_total": 2000,
                    "workload.usage": {"chat": 0.7, "code_assistant": 0.2, "rag": 0.1},
                    "workload.models": models,
                    "hardware.gpus": gpus,
                    **overrides,
                }
            )
        )
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_size_prints_the_kv_cache_needed_at_peak(self):
        # 280 x 9,216 tokens x 327,680 bytes = 845.6 GB; 49.9 GB of headroom per replica.
        output = self.size_with()
        self.assertIn(
            "    KV cache: 845.6 GB needed at peak; 49.9 GB per replica holds about "
            "16.52 requests of 9216 tokens",
            output,
        )
        self.assertNotIn("context per group", output)

    def test_size_prints_the_notes_of_a_model(self):
        output = self.size_with()
        self.assertIn(
            "    note: with 4-GPU replicas the memory model needs 8 GPUs instead of 18; "
            "tensor parallelism adds synchronization overhead, "
            "so benchmark throughput before choosing it",
            output,
        )

    def test_size_prints_the_context_per_group_when_they_differ(self):
        contexts = {"chat": 8192, "code_assistant": 32768, "rag": 16384}
        output = self.size_with(**{"workload.context_tokens": contexts})
        self.assertIn("KV cache: 1865.6 GB needed at peak", output)
        self.assertIn("    context per group: chat 8192, code_assistant 32768, rag 16384", output)

    def test_size_prints_no_kv_line_without_architecture_numbers(self):
        self.start()
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("KV cache:", result.stdout)


class SizeTotalLineTest(CliTestCase):
    def total_line(self, **answers):
        self.start(support.base_answers(**answers))
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        return next(line for line in result.stdout.splitlines() if line.startswith("Total:"))

    def test_known_power_is_printed_in_kw(self):
        self.assertEqual(
            self.total_line(), "Total: 1 GPU(s), 1 server(s), power 1.3 kW, fits: True"
        )

    def test_unknown_power_is_printed_as_unknown(self):
        gpus = [{"model": "unlisted", "count": 8, "vram_gb": 141}]
        self.assertEqual(
            self.total_line(**{"hardware.gpus": gpus}),
            "Total: 1 GPU(s), 1 server(s), power unknown, fits: True",
        )

    def test_a_cpu_only_design_keeps_one_server(self):
        # Without GPUs the design still runs on one host; only the power is unknown.
        self.assertEqual(
            self.total_line(**{"hardware.gpus": [], "hardware.ram_gb": 256}),
            "Total: 0 GPU(s), 1 server(s), power unknown, fits: True",
        )


class TierAndSizeExitCodesTest(CliTestCase):
    def test_missing_answers_exit_2_and_are_listed_by_id(self):
        answers = support.base_answers()
        del answers["org.isolation"]
        self.start(answers)
        result = self.with_blueprint("tier.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("org.isolation: missing", result.stderr)
        self.assertEqual(load_blueprint(self.blueprint)["tier"], {})

    def test_tier_ignores_answers_it_does_not_need(self):
        answers = support.base_answers()
        del answers["workload.models"]
        self.start(answers)
        self.assertEqual(self.with_blueprint("tier.py").returncode, 0)
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("workload.models: missing", result.stderr)

    def test_missing_blueprint_file_exits_2(self):
        result = self.with_blueprint("tier.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("file not found", result.stderr)

    def test_unknown_gpu_without_vram_exits_2(self):
        self.start(support.base_answers(**{"hardware.gpus": [{"model": "mystery", "count": 1}]}))
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("supply vram_gb", result.stderr)

    def test_known_gpu_with_null_vram_and_tdp_uses_the_gpu_table(self):
        gpus = [{"model": "TG141", "count": 8, "vram_gb": None, "tdp_w": None}]
        self.start(support.base_answers(**{"hardware.gpus": gpus}))
        result = self.with_blueprint("size.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        gpu = load_blueprint(self.blueprint)["sizing"]["gpu"]
        self.assertEqual((gpu["vram_gb"], gpu["tdp_w"]), (141, 700))

    def test_unknown_answers_become_assumptions(self):
        self.start(support.base_answers(**{"org.audit_required": "unknown"}))
        self.assertEqual(self.with_blueprint("size.py").returncode, 0)
        ids = [item["id"] for item in load_blueprint(self.blueprint)["assumptions"]]
        self.assertEqual(ids[0], "answers.org.audit_required")

    def test_unreadable_catalog_exits_3(self):
        self.start()
        result = self.run_script(
            "tier.py", "--catalog", str(self.root / "nowhere"), "--blueprint", str(self.blueprint),
            catalog=False,
        )
        self.assertEqual(result.returncode, 3)
        self.assertIn("cannot read the catalog", result.stderr)


class ManifestCliTest(CliTestCase):
    def test_unknown_component_exits_2(self):
        self.start()
        decisions = support.base_decisions()
        decisions[0]["components"] = ["ghost"]
        projects.edit_blueprint(self.blueprint, lambda d: d.update(decisions=decisions))
        result = self.with_blueprint("manifest.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ghost", result.stderr)

    def test_unknown_benchmark_component_exits_2(self):
        self.start()
        decisions = support.base_decisions()
        decisions[0]["benchmark"] = ["ghost"]
        projects.edit_blueprint(self.blueprint, lambda d: d.update(decisions=decisions))
        result = self.with_blueprint("manifest.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("ghost", result.stderr)

    def test_out_option(self):
        self.start()
        target = self.root / "elsewhere" / "manifest.md"
        result = self.with_blueprint("manifest.py", "--out", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(target.is_file())
        self.assertTrue((target.parent / MANIFEST_JSON_FILENAME).is_file())

    def test_answers_that_are_not_an_object_exit_2_as_in_tier_and_size(self):
        for value in (["chat"], "chat", 5, [], None):
            with self.subTest(answers=value):
                self.start()
                (self.blueprint.parent / MANIFEST_FILENAME).unlink(missing_ok=True)
                projects.edit_blueprint(self.blueprint, lambda d: d.update(answers=value))
                result = self.with_blueprint("manifest.py")
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertIn("no 'answers' object", result.stderr)
                for other in ("tier.py", "size.py"):
                    self.assertEqual(result.stderr, self.with_blueprint(other).stderr, other)
                self.assertFalse((self.blueprint.parent / MANIFEST_FILENAME).exists())


class LintCliTest(CliTestCase):
    def test_errors_exit_1_and_json_is_parseable(self):
        self.start()
        result = self.lint("--format", "json")
        self.assertEqual(result.returncode, 1)
        findings = json.loads(result.stdout)
        self.assertIn("E4", [finding["code"] for finding in findings])
        self.assertEqual(
            set(findings[0]), {"code", "severity", "message"}
        )

    def test_catalog_only_passes_on_a_valid_catalog(self):
        result = self.run_script("lint.py", "--catalog-only", "--today", "2026-11-20")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("OK: no findings", result.stdout)

    def test_catalog_only_fails_on_a_bad_entry(self):
        bad = support.component("bad-entry", "ui", version="latest")
        (self.catalog_dir / "components" / "bad-entry.toml").write_text(
            support.component_toml(bad), encoding="utf-8"
        )
        result = self.run_script("lint.py", "--catalog-only", "--today", "2026-11-20")
        self.assertEqual(result.returncode, 1)
        self.assertIn("C1 error: bad-entry", result.stdout)

    def test_blueprint_is_required_without_catalog_only(self):
        result = self.run_script("lint.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--blueprint is required", result.stderr)

    def test_default_catalog_is_the_shipped_one(self):
        result = self.run_script("lint.py", "--catalog-only", catalog=False)
        self.assertNotEqual(result.returncode, 3, result.stderr)


class InvalidCatalogTest(CliTestCase):
    """A catalog that loads but fails C1, C3 or C4 stops every script (exit 3)."""

    def break_reference(self):
        bad = support.component("gamma-gateway", "llm-gateway", requires=["delta-db", "ghost"])
        (self.catalog_dir / "components" / "gamma-gateway.toml").write_text(
            support.component_toml(bad), encoding="utf-8"
        )

    def break_default(self):
        rules = self.catalog_dir / "rules.toml"
        text = rules.read_text(encoding="utf-8")
        old = '[defaults.org.isolation]\nvalue = "per_department"'
        self.assertIn(old, text)
        rules.write_text(
            text.replace(old, '[defaults.org.isolation]\nvalue = "per_dept"'), encoding="utf-8"
        )

    def test_dangling_requires_exits_3_with_the_finding(self):
        self.start()
        self.break_reference()
        result = self.with_blueprint("tier.py")
        self.assertEqual(result.returncode, 3)
        self.assertIn("C3 error", result.stderr)
        self.assertIn("ghost", result.stderr)
        self.assertIn("lint.py --catalog-only", result.stderr)
        self.assertEqual(load_blueprint(self.blueprint)["tier"], {})

    def test_bad_answer_default_exits_3_in_every_script(self):
        self.start()
        self.break_default()
        for name in ("tier.py", "size.py", "manifest.py"):
            with self.subTest(script=name):
                result = self.with_blueprint(name)
                self.assertEqual(result.returncode, 3, result.stderr)
                self.assertIn("defaults.org.isolation", result.stderr)
                self.assertIn("lint.py --catalog-only", result.stderr)
        result = self.lint()
        self.assertEqual(result.returncode, 3, result.stdout)
        self.assertIn("defaults.org.isolation", result.stderr)

    def test_warnings_alone_do_not_stop_the_scripts(self):
        self.start()
        stale = support.component("delta-db", "state", last_verified=date(2020, 1, 1))
        (self.catalog_dir / "components" / "delta-db.toml").write_text(
            support.component_toml(stale), encoding="utf-8"
        )
        result = self.run_script("lint.py", "--catalog-only")
        self.assertIn("W1 warning", result.stdout)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.with_blueprint("tier.py").returncode, 0)


class CatalogOnlyDefaultsTest(CliTestCase):
    def test_catalog_only_reports_a_bad_answer_default(self):
        rules = self.catalog_dir / "rules.toml"
        rules.write_text(
            rules.read_text(encoding="utf-8").replace(
                '[defaults.org.isolation]\nvalue = "per_department"',
                '[defaults.org.isolation]\nvalue = "per_dept"',
            ),
            encoding="utf-8",
        )
        result = self.run_script("lint.py", "--catalog-only", "--today", "2026-11-20")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("C1 error", result.stdout)
        self.assertIn("defaults.org.isolation", result.stdout)


class UnusableValueTest(CliTestCase):
    """json parses 1e309 to infinity and big integers stay exact: exit 2, no traceback."""

    MESSAGE = "blueprint.json holds a value the scripts cannot use"

    def start_with_text(self, old, new, **answers):
        self.start(support.base_answers(**answers))
        text = self.blueprint.read_text(encoding="utf-8")
        self.assertIn(old, text)
        self.blueprint.write_text(text.replace(old, new), encoding="utf-8")

    def assert_exit_2_without_traceback(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn(self.MESSAGE, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def infinite_weights(self):
        models = [
            {"name": "example-70b", "role": "chat", "weights_gb": 12345, "precision": "fp8"}
        ]
        self.start_with_text("12345", "1e309", **{"workload.models": models})

    def test_infinite_weights_exit_2_in_manifest(self):
        self.infinite_weights()
        self.assert_exit_2_without_traceback(self.with_blueprint("manifest.py"))

    def test_infinite_weights_exit_2_in_lint(self):
        """lint compares the manifest digest, so it needs a complete project."""
        models = [
            {"name": "example-70b", "role": "chat", "weights_gb": 12345, "precision": "fp8"}
        ]
        catalog, _ = load_catalog(self.catalog_dir)
        projects.make_project(
            self.root, catalog, answers=support.base_answers(**{"workload.models": models})
        )
        text = self.blueprint.read_text(encoding="utf-8")
        old = '"weights_gb": 12345,'
        self.assertIn(old, text)
        self.blueprint.write_text(text.replace(old, '"weights_gb": 1e309,'), encoding="utf-8")
        self.assert_exit_2_without_traceback(self.lint())

    def test_infinite_weights_exit_2_in_size(self):
        self.infinite_weights()
        self.assert_exit_2_without_traceback(self.with_blueprint("size.py"))

    def test_huge_user_count_exits_2_in_size(self):
        self.start_with_text("180", "1" + "0" * 400, **{"org.users_total": 180})
        self.assert_exit_2_without_traceback(self.with_blueprint("size.py"))

    def test_huge_user_count_is_still_a_valid_tier_input(self):
        self.start_with_text("180", "1" + "0" * 400, **{"org.users_total": 180})
        result = self.with_blueprint("tier.py")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Base tier: T3", result.stdout)


class OptionAndWriteErrorTest(CliTestCase):
    """Bad options and unwritable outputs are input problems (exit 2), never a traceback."""

    def assert_exit_2(self, result):
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_today_exits_2(self):
        self.start()
        for value in ("notadate", "2026-13-45", "20261120"):
            for extra in ((), ("--catalog-only",)):
                with self.subTest(value=value, extra=extra):
                    result = self.run_script("lint.py", "--today", value, *extra)
                    self.assert_exit_2(result)
                    self.assertIn("YYYY-MM-DD", result.stderr)

    def test_invalid_manifest_date_exits_2_and_writes_nothing(self):
        self.start()
        result = self.with_blueprint("manifest.py", "--date", "notadate")
        self.assert_exit_2(result)
        self.assertFalse((self.blueprint.parent / MANIFEST_FILENAME).exists())

    def test_valid_manifest_date_is_written_as_given(self):
        self.start()
        self.assertEqual(self.with_blueprint("manifest.py", "--date", "2026-11-20").returncode, 0)
        text = (self.blueprint.parent / MANIFEST_FILENAME).read_text(encoding="utf-8")
        self.assertIn("- Generated: 2026-11-20", text)

    def test_manifest_out_that_is_a_directory_exits_2(self):
        self.start()
        target = self.root / "a-directory"
        target.mkdir()
        result = self.with_blueprint("manifest.py", "--out", str(target))
        self.assert_exit_2(result)
        self.assertIn(str(target), result.stderr)

    def test_manifest_out_below_a_file_exits_2(self):
        self.start()
        result = self.with_blueprint("manifest.py", "--out", str(self.blueprint / "x.md"))
        self.assert_exit_2(result)

    def test_read_only_blueprint_exits_2_in_tier_and_size(self):
        self.start()
        self.blueprint.chmod(stat.S_IRUSR)
        self.addCleanup(self.blueprint.chmod, stat.S_IRUSR | stat.S_IWUSR)
        if os.access(self.blueprint, os.W_OK):
            self.skipTest("this user can write a read-only file (running as root?)")
        for name in ("tier.py", "size.py"):
            with self.subTest(script=name):
                result = self.with_blueprint(name)
                self.assert_exit_2(result)
                self.assertIn(str(self.blueprint), result.stderr)


if __name__ == "__main__":
    unittest.main()
