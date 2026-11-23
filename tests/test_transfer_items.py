import unittest

import tests  # noqa: F401  (puts both skills' scripts on sys.path)
from transfer_lib.items import build_items, checksums_path, image_archive, safe_name

MANIFEST = {
    "images": [
        {"component": "alpha", "version": "1", "ref": "registry.example.test/a/alpha:1", "digest": "", "license": "MIT", "benchmark": False},
        {"component": "beta", "version": "2", "ref": "beta:2", "digest": "", "license": "MIT", "benchmark": True},
    ],
    "models": [{"name": "chat model", "role": "chat"}],
    "packages": [
        {"component": "alpha", "version": "1", "file": "alpha-1-amd64.tgz", "arch": "amd64",
         "url": "https://downloads.example.test/alpha-1-amd64.tgz", "checksums": "https://downloads.example.test/md5sum",
         "license": "MIT", "benchmark": False},
    ],
    "custom": [{"layer": "orchestration", "name": "Docker Engine (outside the catalog)"}],
    "runtime_downloads": [{"component": "alpha", "text": "Tokenizer files.", "benchmark": False},
                          {"component": "beta", "text": "Price table.", "benchmark": True}],
}
SOURCE = {"source": "huggingface", "repo": "example/chat", "revision": "0" * 40}


class ItemsTest(unittest.TestCase):
    def items(self, **answers):
        return build_items(MANIFEST, {"models": {"chat model": SOURCE}, **answers})

    def test_one_item_per_image_model_package_and_manual_item(self):
        self.assertEqual(
            [item["id"] for item in self.items()],
            [
                "image:alpha:registry.example.test/a/alpha:1",
                "image:beta:beta:2",
                "model:chat model",
                "package:alpha:alpha-1-amd64.tgz",
                "manual:Docker Engine (outside the catalog)",
                "manual:alpha: runtime download 1",
                "manual:beta: runtime download 1",
            ],
        )

    def test_benchmark_rows_can_be_left_out(self):
        ids = [item["id"] for item in self.items(include_benchmark=False)]
        self.assertNotIn("image:beta:beta:2", ids)
        self.assertNotIn("manual:beta: runtime download 1", ids)

    def test_paths_in_the_bundle(self):
        items = {item["id"]: item for item in self.items()}
        self.assertEqual(items["image:alpha:registry.example.test/a/alpha:1"]["path"],
                         "images/alpha/registry.example.test_a_alpha_1.tar")
        self.assertEqual(items["model:chat model"]["path"], "models/chat_model")
        self.assertEqual(items["model:chat model"]["source"], SOURCE)
        package = items["package:alpha:alpha-1-amd64.tgz"]
        self.assertEqual(package["path"], "packages/alpha/alpha-1-amd64.tgz")
        self.assertEqual(checksums_path(package), "packages/alpha/checksums/md5sum")
        self.assertEqual(items["manual:Docker Engine (outside the catalog)"]["path"],
                         "manual/Docker_Engine_outside_the_catalog")

    def test_safe_names(self):
        self.assertEqual(safe_name("one very large chat model"), "one_very_large_chat_model")
        self.assertEqual(safe_name("../.."), "item")
        self.assertEqual(image_archive("vllm", "vllm/vllm-openai:v0.34.0"), "images/vllm/vllm_vllm-openai_v0.34.0.tar")


if __name__ == "__main__":
    unittest.main()
