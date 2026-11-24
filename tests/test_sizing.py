"""The worked examples of references/sizing.md and the expected numbers of the eval scenarios
follow from the constants in sizing.md (computed by tests/sizing_reference.py)."""
import json
import unittest

from tests import SCENARIOS_DIR, SKILL_DIR
from tests.sizing_reference import size

SIZING_MD = (SKILL_DIR / "references" / "sizing.md").read_text(encoding="utf-8")
ENTERPRISE = {
    "org.users_total": 2000,
    "org.downtime_tolerance": "none",
    "workload.usage": {"chat": 0.7, "code_assistant": 0.2, "rag": 0.1},
    "workload.models": [{"role": "chat", "params_b": 70, "precision": "fp8", "context_tokens": 8192,
                         "arch": {"layers": 80, "kv_heads": 8, "head_dim": 128, "kv_dtype": "fp16"}}],
    "hardware.gpus": [{"model": "example", "count": 24, "vram_gb": 141, "tdp_w": 700}],
}


def section(title):
    return SIZING_MD.split(f"\n### {title}\n", 1)[1].split("\n### ", 1)[0]


class WorkedExamplesTest(unittest.TestCase):
    def test_department(self):
        result = size({
            "org.users_total": 180, "org.downtime_tolerance": "planned_only", "workload.usage": {"chat": 1.0},
            "workload.models": [{"role": "chat", "params_b": 671, "precision": "fp8"}],
            "hardware.gpus": [{"model": "example", "count": 8, "vram_gb": 141, "tdp_w": 700}],
        })
        self.assertEqual(result["concurrency"], (9, 18))
        self.assertEqual((result["models"][0]["group"], result["total_gpus"], result["power_kw"]), (8, 8, 10.1))
        text = section("Department: KV unknown")
        for number in ("Range 9 to 18", "738.1 GB", "8 GPUs", "10.1 kW"):
            self.assertIn(number, text)

    def test_enterprise(self):
        result = size(ENTERPRISE)
        model = result["models"][0]
        self.assertEqual(result["concurrency"], (164, 280))
        self.assertEqual((model["cached_tokens"], model["replicas"], model["kv_demand_gb"]), (152282, 18, 845.6))
        self.assertEqual((result["total_gpus"], result["servers"], result["power_kw"]), (18, 3, 22.7))
        self.assertEqual(model["notes"], ["with 4-GPU replicas the memory model needs 8 GPUs instead of 18"])
        text = section("Enterprise: KV known")
        for number in ("Range 164 to 280", "152,282", "rounded up 18", "845.6 GB", "22.7 kW", "8 GPUs instead of 18"):
            self.assertIn(number, text)

    def test_mixed_contexts(self):
        answers = dict(ENTERPRISE, **{"workload.context_tokens": {"code_assistant": 32768, "chat": 8192}})
        result = size(answers)
        self.assertEqual(result["models"][0]["replicas"], 40)
        self.assertFalse(result["fits"])
        self.assertIn("with 8-GPU replicas the memory model needs 16 GPUs instead of 40", result["models"][0]["notes"])
        self.assertIn("= 40", section("Mixed contexts"))

    def test_cpu_only(self):
        result = size({"org.users_total": 12, "workload.usage": {"chat": 1.0}, "hardware.gpus": [], "hardware.ram_gb": 64,
                       "workload.models": [{"role": "chat", "params_b": 8, "precision": "fp8"}]})
        self.assertEqual((result["concurrency"], result["ram_required_gb"], result["fits"]), ((1, 2), 8.8, True))
        self.assertIn("8.8 GB", section("CPU only"))


class ScenarioTest(unittest.TestCase):
    def test_expected_sizing_of_every_scenario(self):
        for folder in sorted(p for p in SCENARIOS_DIR.iterdir() if p.is_dir()):
            answers = json.loads((folder / "answers.json").read_text(encoding="utf-8"))
            expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))["sizing"]
            result = size(answers)
            with self.subTest(scenario=folder.name):
                self.assertEqual(list(result["concurrency"]), [expected["concurrency"]["low"], expected["concurrency"]["high"]])
                self.assertEqual(
                    [{"gpus_per_replica": m["group"], "replicas": m["replicas"], "kv_status": m["kv"]} for m in result["models"]],
                    expected["models"],
                )
                for key in ("total_gpus", "servers", "power_kw", "fits"):
                    self.assertEqual(result[key], expected[key], key)


if __name__ == "__main__":
    unittest.main()
