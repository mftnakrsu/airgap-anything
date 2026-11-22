"""Test package. Importing it puts the skill's scripts on sys.path."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "airgap-anything"
SKILL_DIR = PLUGIN_DIR / "skills" / "airgap-architect"
SCRIPTS_DIR = SKILL_DIR / "scripts"
CATALOG_DIR = SKILL_DIR / "catalog"
SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
