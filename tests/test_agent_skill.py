"""Content the airgap-agent skill must carry, from its spec (2026-11-24-airgap-agent-design.md)."""
import unittest

from tests import AGENT_DIR, TRANSFER_DIR

REFS = AGENT_DIR / "references"
KEYS = ("users", "tools", "models", "claude_route", "internal_tools", "permissions", "os", "central")


def read(name):
    return (REFS / name).read_text(encoding="utf-8")


class ReferencesTest(unittest.TestCase):
    def test_interview_has_every_key_with_a_default(self):
        text = read("interview.md")
        for key in KEYS:
            with self.subTest(key=key):
                row = next(l for l in text.splitlines() if l.startswith("| ") and f"`{key}`" in l)
                self.assertGreaterEqual(row.count("|"), 5, "question and default columns")
        self.assertIn("edit with approval", text)

    def test_decisions_cover_every_tool_and_the_claude_rule(self):
        text = read("decisions.md")
        for tool in ("qwen-code", "codex-cli", "opencode", "claude-code"):
            self.assertIn(f"`catalog/{tool}.md`", text)
        self.assertIn("https://code.claude.com/docs/en/llm-gateway", text)
        for other in ("Goose", "Crush", "Aider", "Cline", "Kilo Code", "Continue"):
            self.assertIn(other, text)

    def test_serving_has_parsers_for_both_engines_and_the_api_per_tool(self):
        text = read("serving.md")
        for word in ("vLLM", "SGLang", "qwen3_coder", "--served-model-name", "/v1/responses", "/v1/messages", "LiteLLM"):
            with self.subTest(word=word):
                self.assertIn(word, text)
        self.assertIn("not documented", text, "families without a documented parser are named, not guessed")

    def test_mcp_lists_offline_servers_and_keeps_fetch_off(self):
        text = read("mcp.md")
        for name in ("mcp-server-git", "gitea-mcp", "GitLab", "Outline", "mcp-atlassian", "MCP Toolbox", "--no-index"):
            with self.subTest(name=name):
                self.assertIn(name, text)
        self.assertRegex(text, r"`fetch`[^\n]*off")

    def test_templates_have_one_section_per_tool_and_no_secrets(self):
        text = read("templates.md")
        for heading in ("## Qwen Code", "## Codex CLI", "## opencode", "## Claude Code"):
            self.assertIn(heading, text)
        self.assertIn('"approvalMode"', text)
        self.assertNotRegex(text, r"sk-[A-Za-z0-9]{8,}")

    def test_verification_has_the_three_checks(self):
        text = read("verification.md")
        for word in ("SHA256SUMS", "tool call", "strace -f -e trace=connect", "deny log", "man7.org",
                     'qwen -p "', 'codex exec "', 'opencode run "', 'claude -p "', "function_call"):
            with self.subTest(word=word):
                self.assertIn(word, text)


class TransferCarriesProjectFilesTest(unittest.TestCase):
    def test_a_project_file_item_is_copied_not_fetched(self):
        fetch = (TRANSFER_DIR / "references" / "fetch.md").read_text(encoding="utf-8")
        bundle = (TRANSFER_DIR / "references" / "bundle.md").read_text(encoding="utf-8")
        self.assertIn("**Project files.**", fetch)
        self.assertRegex(fetch, r"(?i)copied into the bundle")
        self.assertIn("| file |", bundle)
        self.assertIn("files/", bundle)
        self.assertIn("files/docs/airgap/agents/qwen-code/", bundle)
        self.assertIn("cp -R", fetch)


if __name__ == "__main__":
    unittest.main()
