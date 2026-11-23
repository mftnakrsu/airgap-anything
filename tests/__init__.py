"""Test package. Importing it puts the scripts of both skills on sys.path.

The two skills ship separately and never import each other; their packages,
`airgap_lib` and `transfer_lib`, have different names, so tests can use both.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "airgap-anything"
SKILLS_DIR = PLUGIN_DIR / "skills"
SKILL_DIR = SKILLS_DIR / "airgap-architect"
SCRIPTS_DIR = SKILL_DIR / "scripts"
CATALOG_DIR = SKILL_DIR / "catalog"
TRANSFER_DIR = SKILLS_DIR / "airgap-transfer"
TRANSFER_SCRIPTS_DIR = TRANSFER_DIR / "scripts"
TRANSFER_TEMPLATES_DIR = TRANSFER_DIR / "templates"
SKILL_DIRS = (SKILL_DIR, TRANSFER_DIR)
SCENARIOS_DIR = REPO_ROOT / "evals" / "scenarios"

for _scripts in (SCRIPTS_DIR, TRANSFER_SCRIPTS_DIR):
    if str(_scripts) not in sys.path:
        sys.path.insert(0, str(_scripts))
