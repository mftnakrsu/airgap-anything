import unittest
from datetime import date

from tests import CATALOG_DIR
from airgap_lib.catalog import load_catalog, validate_catalog

# The sixteen components of design spec section 9.4 and the layer each belongs to.
V1_COMPONENTS = {
    "ollama": "llm-serving",
    "vllm": "llm-serving",
    "sglang": "llm-serving",
    "litellm": "llm-gateway",
    "kong": "llm-gateway",
    "open-webui": "ui",
    "keycloak": "identity",
    "prometheus": "observability",
    "grafana": "observability",
    "postgresql": "state",
    "valkey": "state",
    "docker-compose": "orchestration",
    "k3s": "orchestration",
    "rke2": "orchestration",
    "harbor": "registry",
    "distribution-registry": "registry",
}


class ShippedCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog, cls.load_findings = load_catalog(CATALOG_DIR)

    def test_the_shipped_catalog_has_no_errors(self):
        findings = self.load_findings + validate_catalog(self.catalog, date.today())
        errors = [f"{f.code} {f.message}" for f in findings if f.severity == "error"]
        self.assertEqual(errors, [])

    def test_the_sixteen_v1_components_are_present_in_their_layers(self):
        layers = {cid: entry["layer"] for cid, entry in self.catalog.components.items()}
        self.assertEqual(layers, V1_COMPONENTS)

    def test_gpu_rows_come_from_vendor_pages(self):
        self.assertGreaterEqual(len(self.catalog.gpus), 1)
        for row in self.catalog.gpus:
            self.assertNotEqual(row["evidence"], "estimate", row["model"])

    def test_every_alternative_is_in_the_same_layer(self):
        for cid, entry in self.catalog.components.items():
            for other in entry["choose"]["alternatives"]:
                self.assertEqual(
                    self.catalog.components[other]["layer"], entry["layer"], f"{cid} -> {other}"
                )


if __name__ == "__main__":
    unittest.main()
