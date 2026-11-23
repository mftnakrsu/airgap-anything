import json
import unittest

import tests  # noqa: F401  (puts both skills' scripts on sys.path)
import transfer_lib
from transfer_lib.constants import FAT32_MAX_FILE_BYTES, GB, PICKLE_SUFFIXES, VOLUME_RESERVE
from transfer_lib.findings import Finding, format_json, format_text, has_errors


class PythonGuardTest(unittest.TestCase):
    def test_old_interpreter_gets_a_message_naming_both_versions(self):
        message = transfer_lib.check_python((3, 10, 12))
        self.assertIn("airgap-transfer", message)
        self.assertIn("3.11", message)
        self.assertIn("3.10", message)

    def test_supported_interpreters_pass(self):
        self.assertIsNone(transfer_lib.check_python((3, 11, 0)))
        self.assertIsNone(transfer_lib.check_python((3, 13, 1)))


class ConstantsTest(unittest.TestCase):
    def test_the_values_of_the_spec(self):
        self.assertEqual(FAT32_MAX_FILE_BYTES, 4 * 1024**3 - 1)
        self.assertEqual(VOLUME_RESERVE, 0.02)
        self.assertEqual(GB, 1_000_000_000)
        self.assertEqual(PICKLE_SUFFIXES, (".bin", ".pt", ".pth", ".pkl"))


class FindingsTest(unittest.TestCase):
    def test_b_codes_are_errors_and_bw_codes_warnings(self):
        self.assertEqual(Finding("B3", "x").severity, "error")
        self.assertEqual(Finding("BW1", "x").severity, "warning")
        self.assertTrue(has_errors([Finding("B1", "x")]))
        self.assertFalse(has_errors([Finding("BW2", "x")]))

    def test_reports(self):
        self.assertEqual(format_text([]), "OK: no findings")
        text = format_text([Finding("B2", "size"), Finding("BW1", "no list")])
        self.assertEqual(text.splitlines(), ["B2 error: size", "BW1 warning: no list", "1 error(s), 1 warning(s)"])
        self.assertEqual(json.loads(format_json([Finding("BW1", "no list")])),
                         [{"code": "BW1", "severity": "warning", "message": "no list"}])


if __name__ == "__main__":
    unittest.main()
