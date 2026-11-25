"""Content the airgap-install skill must carry, and the shape of its eval scenarios."""
import json
import re
import unittest

from tests import INSTALL_DIR, REPO_ROOT, TRANSFER_DIR

INSTALL_SCENARIOS = REPO_ROOT / "evals" / "install-scenarios"

REFS = INSTALL_DIR / "references"
REFERENCES = ("questions", "plan", "compose", "kubernetes", "clusters", "runbook")


def read(name):
    return (REFS / f"{name}.md").read_text(encoding="utf-8")


def code_blocks(text, language="sh"):
    """The lines of every ```LANGUAGE block, also inside an outer four-backtick template."""
    return re.findall(rf"^```{language}\n(.*?)^```$", text, flags=re.S | re.M)


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


class PathsTest(unittest.TestCase):
    ROOTS = ("/", "PROJECT_FOLDER", "HARBOR_DIR")

    def test_every_cd_in_the_runbook_is_absolute(self):
        for block in code_blocks(read("runbook")):
            for target in re.findall(r"(?:^|&& )cd (\S+)", block, flags=re.M):
                with self.subTest(target=target):
                    self.assertTrue(target.startswith(self.ROOTS), target)

    def test_compose_blocks_start_in_the_absolute_compose_folder(self):
        for block in code_blocks(read("runbook")):
            if "docker compose" in block and "HARBOR_DIR" not in block:
                with self.subTest(block=block[:60]):
                    self.assertTrue(block.startswith("cd PROJECT_FOLDER/docs/airgap/install/compose\n"))

    def test_kubernetes_files_are_named_by_absolute_paths(self):
        for name in ("runbook", "clusters"):
            for block in code_blocks(read(name)):
                for path in re.findall(r"(?:-f|cp) (\S*kubernetes/\S+)", block):
                    with self.subTest(name=name, path=path):
                        self.assertTrue(path.startswith("PROJECT_FOLDER/docs/airgap/install/"), path)

    def test_bundle_copies_and_installs_in_clusters_use_absolute_paths(self):
        for block in code_blocks(read("clusters")):
            for line in block.splitlines():
                words = line.split()
                if not words or words[0] not in ("cp", "yum"):
                    continue
                sources = [w for w in words[1:] if not w.startswith("-") and w not in ("install",)]
                if words[0] == "cp":
                    sources = sources[:-1]
                for source in sources:
                    with self.subTest(line=line, source=source):
                        self.assertTrue(source.startswith(("/srv/airgap-bundle/", "PROJECT_FOLDER/", "/root/", "/etc/")), source)

    def test_rke2_kubernetes_blocks_put_kubectl_on_the_path(self):
        text = read("runbook")
        template = text[text.index("## INSTALL.md template"):text.index("## AGENTS-INSTALL.md template")]
        blocks = [block for block in code_blocks(template)
                  if re.search(r"^kubectl ", block, flags=re.M)]
        self.assertGreaterEqual(len(blocks), 5)
        for block in blocks:
            with self.subTest(block=block[:60]):
                self.assertIn("export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin", block)


class ExposureTest(unittest.TestCase):
    def test_kubernetes_holds_an_ingress_template(self):
        text = read("kubernetes")
        exposure = section(text, "## Exposure: the Ingress")
        for word in ("kind: Ingress", "networking.k8s.io/v1", "GATEWAY_HOSTNAME", "pathType: Prefix", "70-ingress.yaml"):
            with self.subTest(word=word):
                self.assertIn(word, exposure)

    def test_k3s_keeps_traefik_and_ships_its_config(self):
        text = read("clusters")
        self.assertNotRegex(text, r"--disable[= ]traefik'")
        self.assertIn("traefik-config.yaml", text)
        self.assertIn("traefik-config.yaml", (INSTALL_DIR / "SKILL.md").read_text(encoding="utf-8"))
        self.assertIn("traefik-config.yaml", section(read("runbook"), "## 6. Egress settings applied"))


class ScenarioTest(unittest.TestCase):
    def scenarios(self):
        return sorted(p for p in INSTALL_SCENARIOS.iterdir() if p.is_dir())

    def test_two_phases_except_unapproved(self):
        for folder in self.scenarios():
            expected = json.loads((folder / "expected.json").read_text(encoding="utf-8"))
            with self.subTest(scenario=folder.name):
                if folder.name == "unapproved":
                    self.assertTrue(expected["writes_nothing"])
                    self.assertNotIn("phase_a", expected)
                    continue
                self.assertEqual(expected["phase_a"]["only_files"], ["docs/airgap/install/plan.md"])
                phase_b = expected["phase_b"]
                self.assertTrue(any("script" in item for item in phase_b["must_not"]))
                self.assertIn("docs/airgap/install/INSIDE.md", phase_b["must_not_files"])
                self.assertIn("docs/airgap/install/", phase_b["manifest_marker"]["required_rows"])
                self.assertEqual(phase_b["manifest_marker"]["marker"], "(from airgap-install)")


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

    def test_the_rules_allow_only_the_plan_before_approval(self):
        self.assertIn("Before the plan is approved, only `docs/airgap/install/plan.md` is written",
                      section(self.text, "## Rules"))


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
