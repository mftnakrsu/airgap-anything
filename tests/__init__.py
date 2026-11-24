"""Repository checks. The skills ship no code, so these tests check the markdown they ship:
structure, links, the catalog, the packaging rules, and that the worked numbers add up."""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "airgap-anything"
SKILLS_DIR = PLUGIN_DIR / "skills"
SKILL_DIR = SKILLS_DIR / "airgap-architect"
CATALOG_DIR = SKILL_DIR / "catalog"
TRANSFER_DIR = SKILLS_DIR / "airgap-transfer"
AGENT_DIR = SKILLS_DIR / "airgap-agent"
AGENT_CATALOG_DIR = AGENT_DIR / "catalog"
AGENT_TOOLS = ("qwen-code", "codex-cli", "opencode", "claude-code")
RAG_DIR = SKILLS_DIR / "airgap-rag"
RAG_CATALOG_DIR = RAG_DIR / "catalog"
RAG_ENTRIES = ("docling-serve", "pgvector", "qdrant", "ragflow",
               "qwen3-embedding", "bge-m3", "qwen3-reranker", "bge-reranker-v2-m3")
RAG_KINDS = ("extractor", "vector-store", "rag-platform", "embedding-model", "reranker-model")
APIS = ("chat-completions", "responses", "anthropic-messages")
SKILL_DIRS = (SKILL_DIR, TRANSFER_DIR, AGENT_DIR, RAG_DIR)
SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"
LAYERS = ("llm-serving", "llm-gateway", "ui", "identity", "observability", "orchestration", "state", "registry")
EVIDENCE_LEVELS = ("estimate", "docs", "field")
