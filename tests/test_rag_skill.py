"""Content the airgap-rag skill must carry, from its spec (2026-11-24-airgap-rag-design.md)."""
import unittest

from tests import RAG_DIR, TRANSFER_DIR

REFS = RAG_DIR / "references"
KEYS = ("platform", "consumers", "sources", "doc_types", "languages", "updates", "access", "hardware")


def read(name):
    return (REFS / name).read_text(encoding="utf-8")


class ReferencesTest(unittest.TestCase):
    def test_interview_keys_platform_choice_and_fast_path(self):
        text = read("interview.md")
        for key in KEYS:
            with self.subTest(key=key):
                self.assertIn(f"`{key}`", text)
        for option in ("Open WebUI", "RAGFlow", "something else"):
            self.assertIn(option, text)
        self.assertRegex(text, r"(?i)fast path")
        self.assertIn("unverified", text)

    def test_decisions_cover_platforms_and_alternatives(self):
        text = read("decisions.md")
        for name in ("`catalog/ragflow.md`", "Onyx", "WeKnora", "AnythingLLM", "Dify", "LightRAG"):
            self.assertIn(name, text)

    def test_extraction_has_three_tiers_and_the_cloud_rule(self):
        text = read("extraction.md")
        for word in ("pypdf", "`catalog/docling-serve.md`", "pdftotext", "PDF_EXTRACT_IMAGES",
                     "ENABLE_MARKDOWN_HEADER_TEXT_SPLITTER", "CHUNK_MIN_SIZE_TARGET"):
            with self.subTest(word=word):
                self.assertIn(word, text)
        self.assertRegex(text, r"(?i)never .*cloud")

    def test_models_reference_wires_open_webui_to_vllm(self):
        text = read("models.md")
        for word in ("RAG_EMBEDDING_ENGINE", "RAG_EXTERNAL_RERANKER_URL", "/v1/rerank",
                     "ENABLE_RAG_HYBRID_SEARCH", "OFFLINE_MODE"):
            with self.subTest(word=word):
                self.assertIn(word, text)

    def test_sizing_has_the_steps_and_sources(self):
        text = read("sizing.md")
        for word in ("3.1", "0.49", "4 × ", "pg_relation_size", "estimate", "fast path"):
            with self.subTest(word=word):
                self.assertIn(word, text)

    def test_ingestion_uses_the_api_without_keys_in_files(self):
        text = read("ingestion.md")
        for word in ("ENABLE_API_KEYS", "/api/v1/files/", "knowledge_id", "process/status",
                     "/access/update", "/api/v1/retrieval/query/collection", "v0.13.4",
                     "/api/v1/knowledge/$KB_ID/files", "/files/pending", "/api/v1/groups/",
                     "/sync/diff", "/sync/cleanup", "/file/remove", "curl -sS --fail"):
            with self.subTest(word=word):
                self.assertIn(word, text)
        self.assertNotRegex(text, r"sk-[A-Za-z0-9]{8,}")
        # The directory scanner's rule (tests/test_packaging.py, PROSE_DOWNLOAD): no curl followed on its
        # line by a pipe or a URL. The source line of the man page holds curl only inside its own URL.
        for line in text.splitlines():
            self.assertNotRegex(line, r"(?i)\bcurl\b.*(\||https?://)")

    def test_wiki_and_verification(self):
        self.assertIn("mcp-server-git", read("wiki.md"))
        text = read("verification.md")
        for word in ("/v1/capabilities", "strace -f -e trace=connect", "BYPASS_ADMIN_ACCESS_CONTROL"):
            with self.subTest(word=word):
                self.assertIn(word, text)


class HandOverTest(unittest.TestCase):
    def test_rows_from_airgap_rag_are_marked_and_accepted(self):
        rag = (RAG_DIR / "SKILL.md").read_text(encoding="utf-8")
        transfer = (TRANSFER_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("(from airgap-rag)", rag)
        self.assertIn("(from airgap-rag)", transfer)
        self.assertIn("docs/airgap/rag.md", transfer)

    def test_rag_md_lists_the_names_the_marked_rows_use(self):
        # Section-2 rows carry the Model name, not a catalog id: rag.md must list that name,
        # and the transfer must look for it in the Model cell, or it refuses the row.
        rag = (RAG_DIR / "SKILL.md").read_text(encoding="utf-8")
        step9 = rag.split("9. **rag.md.**", 1)[1].split("10. **Manifest.**", 1)[0]
        self.assertIn("Model names", step9)
        self.assertIn("Model cell", (TRANSFER_DIR / "SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
