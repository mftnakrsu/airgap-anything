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
MAX_SIZE_GB = 10**6  # a size answer above this (a petabyte) is taken for a typing error


def size_bytes(value) -> int | None:
    """Whole bytes of a size given in decimal gigabytes, or None when `value` is not a
    number above 0 and at most MAX_SIZE_GB (so never a bool, NaN, infinity or 1e300),
    or when it is less than one byte."""
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 < value <= MAX_SIZE_GB:
        return None
    size = round(value * GB)
    return size if size >= 1 else None

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
