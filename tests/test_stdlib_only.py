import ast
import sys
import unittest

from tests import SCRIPTS_DIR, TRANSFER_SCRIPTS_DIR

# Each skill may import only the standard library and its own package: an installer can copy
# one skill folder without the other.
LOCAL_PACKAGES = {SCRIPTS_DIR: {"airgap_lib"}, TRANSFER_SCRIPTS_DIR: {"transfer_lib"}}
NETWORK_MODULES = {
    "asyncio", "ftplib", "http", "imaplib", "poplib", "smtplib", "socket",
    "socketserver", "ssl", "telnetlib", "urllib", "webbrowser", "xmlrpc",
}


def imported_modules(path):
    """Top-level names of every absolute import in a Python file."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name.split(".")[0]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module.split(".")[0]


class StandardLibraryOnlyTest(unittest.TestCase):
    def setUp(self):
        self.files = {root: sorted(root.rglob("*.py")) for root in LOCAL_PACKAGES}

    def test_all_scripts_are_found(self):
        names = {path.name for path in self.files[SCRIPTS_DIR]}
        self.assertTrue({"tier.py", "size.py", "manifest.py", "lint.py"} <= names)
        names = {path.name for path in self.files[TRANSFER_SCRIPTS_DIR]}
        self.assertTrue({"plan.py", "pack.py", "check.py"} <= names)

    def test_only_the_standard_library_and_the_skills_own_package_are_imported(self):
        offenders = [
            f"{path.relative_to(root.parent)}: {module}"
            for root, files in self.files.items()
            for path in files
            for module in imported_modules(path)
            if module not in sys.stdlib_module_names and module not in LOCAL_PACKAGES[root]
        ]
        self.assertEqual(offenders, [])

    def test_no_network_module_is_imported(self):
        offenders = [
            f"{path.relative_to(root.parent)}: {module}"
            for root, files in self.files.items()
            for path in files
            for module in imported_modules(path)
            if module in NETWORK_MODULES
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
