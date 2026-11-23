"""Names shared by every module of airgap-transfer."""
from __future__ import annotations

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_INPUT = 2
EXIT_ENVIRONMENT = 3

# Files in the project, under docs/airgap/.
AIRGAP_DIR = "docs/airgap"
BLUEPRINT_FILE = "blueprint.json"
MANIFEST_FILE = "transfer-manifest.json"
STATE_FILE = "transfer.json"
MANIFEST_SCHEMA_VERSION = 1
STATE_SCHEMA_VERSION = 1
BUNDLE_SCHEMA_VERSION = 1

# Answers of airgap-architect that this skill reads from blueprint.json.
CHANNELS = ("removable_media", "data_diode", "staging_host", "other")
MEDIUM_CHANNELS = ("removable_media", "other")
FILE_LIMIT_CHANNELS = ("data_diode", "staging_host")
OPERATORS = ("people", "local_agent", "people_then_agent")
RUNBOOK_OPERATORS = ("people", "people_then_agent")
AGENT_RULES_OPERATORS = ("local_agent", "people_then_agent")

FILESYSTEMS = ("fat32", "exfat", "ntfs", "ext4", "other")
GB = 10**9  # medium and file sizes are given in decimal gigabytes
FAT32_MAX_FILE_BYTES = 4 * 1024**3 - 1
VOLUME_RESERVE = 0.02

# The model file filter of design spec section 8.4, in one place.
MODEL_FILE_PATTERNS = (
    "*.safetensors",
    "*.json",
    "*.txt",
    "*.model",
    "*.tiktoken",
    "*.jinja",
    "*.md",
    "LICENSE*",
    "LICENCE*",
)
PICKLE_SUFFIXES = (".bin", ".pt", ".pth", ".pkl")
PICKLE_PATTERNS = tuple(f"*{suffix}" for suffix in PICKLE_SUFFIXES)

# The bundle folder.
FETCH_SCRIPT = "fetch.sh"
FETCH_LOG = "fetch.log"
FETCH_STATE_DIR = ".fetch"
CONNECTED_ONLY = (FETCH_SCRIPT, FETCH_LOG, FETCH_STATE_DIR)
BUNDLE_JSON = "bundle.json"
SUMS_FILE = "SHA256SUMS"
PARTS_FILE = "PARTS.txt"
VOLUMES_FILE = "VOLUMES.txt"
VOLUME_LABEL = "VOLUME.txt"
INVENTORY_MD = "INVENTORY.md"
INVENTORY_CSV = "INVENTORY.csv"
RUNBOOK_FILE = "INSIDE.md"
AGENT_RULES_FILE = "AGENTS-INSIDE.md"
SEND_ORDER_FILE = "SEND-ORDER.txt"
INSIDE_SCRIPTS = ("verify.sh", "load.sh")
PART_SUFFIX = ".part{:03d}"
