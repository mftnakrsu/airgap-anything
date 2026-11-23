"""fetch.sh run for real with stub download tools: no network, small files."""
import hashlib
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import fetch_stubs, transfer_projects
from transfer_lib.constants import MODEL_FILE_PATTERNS
from transfer_lib.tools import COMMANDS

SHELLS = [name for name in ("sh", "dash") if shutil.which(name)]


@unittest.skipUnless(shutil.which("sha256sum") or shutil.which("shasum"), "needs a SHA-256 tool")
class FetchScriptRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        catalog = transfer_projects.transfer_catalog(tmp / "catalog")
        self.project = transfer_projects.make_project(tmp / "project", catalog)
        self.bundle = tmp / "bundle"
        self.files = tmp / "files"
        self.files.mkdir()
        self.serve("alpha-cli-1.2.3-amd64", b"cli binary")
        self.serve("install.sh", b"echo install\n")
        self.serve("SHA256SUMS", f"{hashlib.sha256(b'cli binary').hexdigest()}  alpha-cli-1.2.3-amd64\n".encode())
        self.stubs = fetch_stubs.install_stubs(tmp / "stubs")

    def serve(self, name, data):
        (self.files / name).write_bytes(data)

    def plan(self, **env):
        transfer_projects.write_state(self.project, transfer_projects.default_answers(self.bundle))
        self.env = fetch_stubs.stub_env(self.stubs, self.bundle, self.files, **env)
        result = transfer_projects.run_script("plan.py", self.project, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)

    def fetch(self, shell="sh", cwd=None):
        return subprocess.run([shell, str(self.bundle / "fetch.sh")], capture_output=True, text=True,
                              env=self.env, cwd=cwd)

    def log(self):
        return (self.bundle / "fetch.log").read_text(encoding="utf-8")

    def test_every_item_is_fetched_and_a_second_run_skips_them(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                shutil.rmtree(self.bundle, ignore_errors=True)
                self.plan()
                result = self.fetch(shell)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual((self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64").read_bytes(), b"cli binary")
                self.assertTrue((self.bundle / "packages/alpha-engine/checksums/SHA256SUMS").is_file())
                self.assertTrue((self.bundle / "models/example-70b/model.safetensors").is_file())
                digest = self.bundle / "images/alpha-engine/registry.example.test_synthetic_alpha-engine_1.2.3.digest"
                self.assertRegex(digest.read_text(encoding="utf-8"), r"^sha256:[0-9a-f]{64}\n$")
                self.assertNotIn("FAILED", self.log())
                again = self.fetch(shell)
                self.assertEqual(again.returncode, 0)
                self.assertIn("OK package alpha-cli-1.2.3-amd64 (already present)", again.stdout)

    def test_a_failed_download_is_logged_and_the_others_go_on(self):
        (self.files / "install.sh").unlink()
        self.plan()
        result = self.fetch()
        self.assertEqual(result.returncode, 1)
        self.assertIn("FAILED package install.sh", self.log())
        self.assertIn("OK package alpha-cli-1.2.3-amd64", self.log())
        self.assertIn("1 item(s) failed:", result.stderr)
        self.assertFalse((self.bundle / "packages/alpha-engine/install.sh.download").exists())
        self.serve("install.sh", b"echo install\n")
        self.assertEqual(self.fetch().returncode, 0)

    def test_a_checksum_mismatch_deletes_the_file_and_stops(self):
        self.serve("SHA256SUMS", ("0" * 64 + "  alpha-cli-1.2.3-amd64\n").encode())
        self.plan()
        result = self.fetch()
        self.assertEqual(result.returncode, 1)
        self.assertIn("checksum does not match", self.log())
        self.assertFalse((self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64").exists())
        self.assertNotIn("install.sh", self.log())

    def test_other_checksum_list_formats(self):
        digest = hashlib.sha256(b"cli binary").hexdigest()
        for text in (f"SHA256 (alpha-cli-1.2.3-amd64) = {digest}\n", f"{digest.upper()} *dist/alpha-cli-1.2.3-amd64\n"):
            with self.subTest(text=text):
                shutil.rmtree(self.bundle, ignore_errors=True)
                self.serve("SHA256SUMS", text.encode())
                self.plan()
                self.assertEqual(self.fetch().returncode, 0, self.log())

    def test_an_unsupported_checksum_algorithm_fails_the_item_and_keeps_the_file(self):
        # A SHA-1 list (40 hex characters) is neither md5, sha256 nor sha512. The file is not
        # known to be bad, so it is kept (as .download, never as the finished file), the item
        # fails, the other items still run, and the run ends with exit 1.
        sha1 = hashlib.sha1(b"cli binary").hexdigest()
        self.assertEqual(len(sha1), 40)
        for shell in SHELLS:
            with self.subTest(shell=shell):
                shutil.rmtree(self.bundle, ignore_errors=True)
                self.serve("SHA256SUMS", f"{sha1}  alpha-cli-1.2.3-amd64\n".encode())
                self.plan()
                result = self.fetch(shell)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("FAILED package alpha-cli-1.2.3-amd64: unsupported checksum algorithm", self.log())
                self.assertNotIn("checksum does not match", self.log())
                kept = self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64.download"
                self.assertEqual(kept.read_bytes(), b"cli binary")
                self.assertFalse((self.bundle / "packages/alpha-engine/alpha-cli-1.2.3-amd64").exists())
                self.assertIn("OK package install.sh", self.log())
                self.assertIn("1 item(s) failed:", result.stderr)
                self.assertIn("package alpha-cli-1.2.3-amd64", result.stderr)

    def test_a_model_without_safetensors_fails(self):
        self.plan(STUB_PICKLE_ONLY=1)
        self.assertEqual(self.fetch().returncode, 1)
        self.assertIn("model example-70b: no safetensors weights", self.log())

    def test_docker_is_used_when_the_copier_is_missing(self):
        (self.stubs / "skopeo").unlink()
        self.plan()
        self.assertIn(COMMANDS["docker.save"].line, (self.bundle / "fetch.sh").read_text(encoding="utf-8"))
        self.assertEqual(self.fetch().returncode, 0, self.log())

    def test_model_patterns_reach_hf_literally_whatever_the_current_folder_holds(self):
        # The patterns are split from an unquoted variable; with pathname expansion on,
        # *.safetensors would turn into x.safetensors here.
        elsewhere = Path(self.tmp.name) / "elsewhere"
        elsewhere.mkdir()
        for name in ("x.safetensors", "notes.json", "README.md", "LICENSE", "tokenizer.model"):
            (elsewhere / name).write_text("", encoding="utf-8")
        for shell in SHELLS:
            with self.subTest(shell=shell):
                shutil.rmtree(self.bundle, ignore_errors=True)
                args = Path(self.tmp.name) / f"hf-args-{shell}.txt"
                self.plan(STUB_HF_ARGS=args)
                result = self.fetch(shell, cwd=elsewhere)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr + self.log())
                received = args.read_text(encoding="utf-8").splitlines()
                after = [received[i + 1] for i, word in enumerate(received[:-1]) if word == "--include"]
                self.assertEqual(after, list(MODEL_FILE_PATTERNS))
                for name in ("x.safetensors", "notes.json", "README.md", "LICENSE", "tokenizer.model"):
                    self.assertNotIn(name, received)


if __name__ == "__main__":
    unittest.main()
