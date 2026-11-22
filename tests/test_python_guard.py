import unittest

import tests  # noqa: F401  (puts the scripts directory on sys.path)
import airgap_lib


class PythonGuardTest(unittest.TestCase):
    def test_old_interpreter_gets_a_message_naming_both_versions(self):
        message = airgap_lib.check_python((3, 10, 12))
        self.assertIn("3.11", message)
        self.assertIn("3.10", message)

    def test_supported_interpreters_pass(self):
        self.assertIsNone(airgap_lib.check_python((3, 11, 0)))
        self.assertIsNone(airgap_lib.check_python((3, 13, 1)))


if __name__ == "__main__":
    unittest.main()
