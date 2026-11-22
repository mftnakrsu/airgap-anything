"""Names shared by every module."""
from __future__ import annotations

from collections.abc import Iterable

SCHEMA_VERSION = 1  # blueprint.json
COMPONENT_SCHEMA_VERSION = 2  # catalog component entries

TIERS = ("T1", "T2", "T3")
LAYERS = (
    "llm-serving",
    "llm-gateway",
    "ui",
    "identity",
    "observability",
    "orchestration",
    "state",
    "registry",
)
# Weakest first: a decision carries the weakest label among its inputs.
EVIDENCE_LEVELS = ("estimate", "docs", "field")

USAGE_TYPES = ("chat", "code_assistant", "rag", "batch")
INTERACTIVE_USAGE = ("chat", "code_assistant", "rag")
MODEL_ROLES = ("chat", "code", "embedding", "rerank")
GENERATIVE_ROLES = ("chat", "code")
SIZE_CLASSES = ("S", "M", "L", "XL")

# GPU vendors, and the hardware classes a container image can be built for.
GPU_VENDORS = ("nvidia", "amd", "intel")
HARDWARE_CLASSES = GPU_VENDORS + ("cpu",)

# CPU architectures of the servers inside, and who works inside the network.
CPU_ARCHES = ("amd64", "arm64")
INSIDE_OPERATORS = ("people", "local_agent", "people_then_agent")
AGENT_OPERATORS = ("local_agent", "people_then_agent")
# What a package row of a catalog entry is built for; "any" is architecture-free.
PACKAGE_ARCHES = CPU_ARCHES + ("any",)

# Requirements an escalator in rules.toml may switch on.
ESCALATOR_REQUIREMENTS = (
    "gateway_non_empty",
    "isolation_design_section",
    "two_engine_replicas",
)
REQUIREMENTS = ESCALATOR_REQUIREMENTS + ("kubernetes_risk_note",)

# Language-independent anchors in the blueprint Markdown file.
SECTION_MARKERS = (
    "context",
    "tier",
    "architecture",
    "decisions",
    "sizing",
    "transfer",
    "data-flow",
    "operations",
    "verification",
    "out-of-scope",
)
ISOLATION_MARKER = "isolation-design"
AGENT_BLOCK_START = "<!-- airgap-architect:start -->"
AGENT_BLOCK_END = "<!-- airgap-architect:end -->"

UNKNOWN = "unknown"


def tier_index(tier: str) -> int:
    return TIERS.index(tier)


def max_tier(a: str, b: str) -> str:
    return a if tier_index(a) >= tier_index(b) else b


def weakest(levels: Iterable[str]) -> str:
    """Weakest evidence label in `levels`; 'field' when `levels` is empty."""
    found = [EVIDENCE_LEVELS.index(level) for level in levels]
    return EVIDENCE_LEVELS[min(found)] if found else "field"


def section_marker(name: str) -> str:
    return f"<!-- airgap:section {name} -->"
