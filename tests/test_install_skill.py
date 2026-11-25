"""Content the airgap-install skill must carry, from its spec (2026-11-25-airgap-install-design.md)."""
import re
import unittest

from tests import INSTALL_DIR, TRANSFER_DIR

REFS = INSTALL_DIR / "references"
REFERENCES = ("questions", "plan", "compose", "kubernetes", "clusters", "runbook")


def read(name):
    return (REFS / f"{name}.md").read_text(encoding="utf-8")


def section(text, heading):
    """The text from a heading to the next level-two heading, or to the end."""
    start = text.index(heading)
    end = text.find("\n## ", start + len(heading))
    return text[start:] if end == -1 else text[start:end]


class ReferencesTest(unittest.TestCase):
    def test_every_reference_exists_and_ends_with_sources(self):
        for name in REFERENCES:
            with self.subTest(name=name):
                self.assertIn("## Sources", read(name))

    def test_questions_have_defaults_and_the_approval_question(self):
        text = read("questions")
        for word in ("host", "TLS", "inside.operator", "approved", "Default"):
            with self.subTest(word=word):
                self.assertIn(word, text)

    def test_plan_has_the_start_order_and_the_approval_line(self):
        text = read("plan")
        self.assertIn("Blueprint approved by the user on", text)
        order_text = section(text, "## Start order")
        order = ["registry", "state", "serving", "extraction", "gateway", "UI", "observability"]
        positions = [order_text.index(word) for word in order]
        self.assertEqual(positions, sorted(positions))

    def test_compose_template_never_pulls_and_reserves_gpus(self):
        text = read("compose")
        for word in ("pull_policy: never", "reservations:", "capabilities: [gpu]", "healthcheck:",
                     "service_healthy", "internal: true", ".env.example"):
            with self.subTest(word=word):
                self.assertIn(word, text)
        self.assertNotRegex(text, r"image: \S+:latest\b")

    def test_kubernetes_manifests_use_the_local_registry_and_numbered_files(self):
        text = read("kubernetes")
        for word in ("imagePullPolicy", "nvidia.com/gpu", "00-namespace.yaml", "--from-literal"):
            with self.subTest(word=word):
                self.assertIn(word, text)

    def test_clusters_cover_three_paths_and_never_install_an_existing_one(self):
        text = read("clusters")
        for word in ("## k3s", "## RKE2", "## Existing cluster", "INSTALL_K3S_SKIP_DOWNLOAD=true",
                     "INSTALL_RKE2_ARTIFACT_PATH", "registries.yaml"):
            with self.subTest(word=word):
                self.assertIn(word, text)
        existing = text.split("## Existing cluster", 1)[1].split("\n## ", 1)[0]
        self.assertNotIn("install.sh", existing)

    def test_runbook_steps_have_expect_and_if_not(self):
        text = read("runbook")
        for word in ("## INSTALL.md template", "## AGENTS-INSTALL.md template", "Why:", "Expect:",
                     "If not:", "nvidia-smi", "nvidia-datacenter-bringup", "/v1/models",
                     "docs/airgap/agents.md", "docs/airgap/rag.md", "openssl rand", "chmod 600",
                     "unverified"):
            with self.subTest(word=word):
                self.assertIn(word, text)

    def test_no_secret_values_and_no_download_lines(self):
        for name in REFERENCES:
            text = read(name)
            with self.subTest(name=name):
                self.assertNotRegex(text, r"sk-[A-Za-z0-9]{8,}")
                for line in text.splitlines():
                    self.assertNotRegex(line, r"(?i)\bcurl\b.*(\||https?://)")
                self.assertIsNone(re.search(r"(?i)\bdocker (compose )?pull\b", text))


class SkillTest(unittest.TestCase):
    def setUp(self):
        self.text = (INSTALL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_short_and_names_every_reference(self):
        self.assertLess(len(self.text.splitlines()), 200)
        for name in REFERENCES:
            with self.subTest(name=name):
                self.assertIn(f"references/{name}.md", self.text)

    def test_workflow_checklist_rules_and_self_check(self):
        self.assertGreaterEqual(self.text.count("- [ ] "), 8)
        for word in ("## Rules", "## Self-check", "## Common mistakes", "pull_policy: never",
                     "blueprint §5", "unverified", "airgap-architect", "docs/airgap/agents.md",
                     "(from airgap-rag)"):
            with self.subTest(word=word):
                self.assertIn(word, self.text)

    def test_the_rules_forbid_programs_and_scripts(self):
        self.assertIn("programs or scripts", section(self.text, "## Rules"))


class HandOverTest(unittest.TestCase):
    def test_transfer_accepts_rows_from_airgap_install_and_hands_off(self):
        install = (INSTALL_DIR / "SKILL.md").read_text(encoding="utf-8")
        transfer = (TRANSFER_DIR / "SKILL.md").read_text(encoding="utf-8")
        inside = (TRANSFER_DIR / "references" / "inside.md").read_text(encoding="utf-8")
        self.assertIn("(from airgap-install)", install)
        self.assertIn("(from airgap-install)", transfer)
        self.assertIn("docs/airgap/install/", transfer)
        self.assertIn("continue with `install/INSTALL.md`", inside)


if __name__ == "__main__":
    unittest.main()
