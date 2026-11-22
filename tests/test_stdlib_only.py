import ast
import sys
import unittest

from tests import SCRIPTS_DIR

LOCAL_PACKAGES = {"airgap_lib"}
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
        self.files = sorted(SCRIPTS_DIR.rglob("*.py"))

    def test_all_scripts_are_found(self):
        names = {path.name for path in self.files}
        self.assertTrue({"tier.py", "size.py", "manifest.py", "lint.py"} <= names)

    def test_only_the_standard_library_is_imported(self):
        offenders = [
            f"{path.relative_to(SCRIPTS_DIR)}: {module}"
            for path in self.files
            for module in imported_modules(path)
            if module not in sys.stdlib_module_names and module not in LOCAL_PACKAGES
        ]
        self.assertEqual(offenders, [])

    def test_no_network_module_is_imported(self):
        offenders = [
            f"{path.relative_to(SCRIPTS_DIR)}: {module}"
            for path in self.files
            for module in imported_modules(path)
            if module in NETWORK_MODULES
        ]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
