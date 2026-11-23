"""verify.sh and load.sh on small fake bundles, with POSIX sh and a stub docker.

They need coreutils' sha256sum. CI runs them on Linux; on a machine without
sha256sum they are skipped."""
import json
import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests import TRANSFER_TEMPLATES_DIR, transfer_projects
from transfer_lib.constants import GB
from transfer_lib.tools import COMMANDS, TEMPLATE_COMMANDS

SHELLS = [name for name in ("sh", "dash") if shutil.which(name)]
DOCKER_STUB = r"""#!/bin/sh
# Records each call; "image inspect" prints the ID it is asked about unless STUB_WRONG_ID is set;
# "info" prints STUB_DRIVER_STATUS (nothing by default, so the store is not detected).
echo "$*" >> "$DOCKER_CALLS"
case "$*" in
  *inspect*)
    if [ -n "${STUB_WRONG_ID:-}" ]; then echo "sha256:$(printf '%064d' 9)"; else for last in "$@"; do :; done; echo "$last"; fi ;;
  info*)
    printf '%s\n' "${STUB_DRIVER_STATUS:-}" ;;
esac
"""
# What the containerd image store page shows `docker info -f '{{ .DriverStatus }}'` printing
# (https://docs.docker.com/engine/storage/containerd/).
CONTAINERD_STATUS = "[[driver-type io.containerd.snapshotter.v1]]"


@unittest.skipUnless(shutil.which("sha256sum"), "needs coreutils sha256sum")
class InsideScriptsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        self.project, self.bundle = transfer_projects.packed_project(
            tmp, sizes={"model:example-70b": 50000},
            **{"medium.filesystem": "fat32", "medium.capacity_gb": 20000 / GB},
        )
        data = json.loads((self.bundle / "bundle.json").read_text(encoding="utf-8"))
        self.volumes = len(data["volumes"])
        self.inside = tmp / "inside"
        self.inside.mkdir()
        for number in range(1, self.volumes + 1):
            medium = tmp / f"medium{number}"
            medium.mkdir()
            result = transfer_projects.run_script("pack.py", self.project, "--write-volume", str(number), "--to", str(medium))
            self.assertEqual(result.returncode, 0, result.stderr)
            shutil.copytree(medium, self.inside, dirs_exist_ok=True)
        self.stubs = tmp / "stubs"
        self.stubs.mkdir()
        docker = self.stubs / "docker"
        docker.write_text(DOCKER_STUB, encoding="utf-8")
        docker.chmod(docker.stat().st_mode | stat.S_IXUSR)
        self.env = dict(os.environ, PATH=f"{self.stubs}{os.pathsep}{os.environ['PATH']}", DOCKER_CALLS=str(tmp / "calls"))

    def run_sh(self, script, *args, shell="sh", env=None):
        return subprocess.run([shell, str(self.inside / script), *args], capture_output=True, text=True, env=env or self.env)

    def missing(self):
        return (self.inside / "MISSING.txt").read_text(encoding="utf-8").splitlines()

    def test_the_templates_are_posix_sh_without_a_shebang(self):
        for name in ("verify.sh", "load.sh"):
            text = (TRANSFER_TEMPLATES_DIR / name).read_text(encoding="utf-8")
            self.assertFalse(text.startswith("#!"), name)
            self.assertIn("set -eu", text)
            for word in ("python", "curl", "wget", "[[", "local "):
                self.assertNotIn(word, text, f"{name}: {word}")
        copied = (self.inside / "load.sh").read_text(encoding="utf-8")
        self.assertNotIn("{{docker.", copied)
        for key in TEMPLATE_COMMANDS:
            self.assertIn("{{" + key + "}}", (TRANSFER_TEMPLATES_DIR / "load.sh").read_text(encoding="utf-8"))
            self.assertIn(COMMANDS[key].line, copied)
        self.assertEqual((self.inside / "verify.sh").read_text(encoding="utf-8"),
                         (TRANSFER_TEMPLATES_DIR / "verify.sh").read_text(encoding="utf-8"))

    def test_verify_passes_and_joins_the_parts(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.run_sh("verify.sh", str(self.inside), shell=shell)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("verify.sh: OK", result.stdout.splitlines()[-1])
                self.assertEqual((self.inside / "models/example-70b/model.safetensors").read_bytes(), b"w" * 50000)
                self.assertFalse((self.inside / "models/example-70b/model.safetensors.part001").exists())
                self.assertTrue((self.inside / ".verified").is_file())

    def test_one_changed_byte_is_found(self):
        path = self.inside / "packages/alpha-engine/alpha-cli-1.2.3-amd64"
        data = bytearray(path.read_bytes())
        data[0] ^= 1
        path.write_bytes(bytes(data))
        result = self.run_sh("verify.sh", str(self.inside))
        self.assertEqual(result.returncode, 1)
        lines = self.missing()
        self.assertEqual(lines[0], "file\texpected sha256\tvolume\tbring next time")
        self.assertTrue(lines[1].startswith("packages/alpha-engine/alpha-cli-1.2.3-amd64\t"))
        self.assertIn("a new copy of volume", lines[1])

    def test_one_missing_part_is_found_with_its_volume(self):
        part = self.inside / "models/example-70b/model.safetensors.part002"
        part.unlink()
        result = self.run_sh("verify.sh", str(self.inside))
        self.assertEqual(result.returncode, 1)
        row = self.missing()[1].split("\t")
        self.assertEqual(row[0], "models/example-70b/model.safetensors.part002")
        self.assertRegex(row[1], r"^[0-9a-f]{64}$")
        self.assertEqual(row[3], f"volume {row[2]} of {self.volumes}")

    def test_verify_arguments(self):
        self.assertEqual(self.run_sh("verify.sh", "a", "b").returncode, 2)
        self.assertEqual(self.run_sh("verify.sh", str(self.inside / "nothing")).returncode, 2)

    def test_load_refuses_before_verify(self):
        result = self.run_sh("load.sh", str(self.inside), str(Path(self.tmp.name) / "models"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("run sh verify.sh", result.stderr)

    def test_load_after_verify_loads_every_image_and_copies_models(self):
        self.assertEqual(self.run_sh("verify.sh", str(self.inside)).returncode, 0)
        models = Path(self.tmp.name) / "models"
        result = self.run_sh("load.sh", str(self.inside), str(models))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = Path(self.env["DOCKER_CALLS"]).read_text(encoding="utf-8").splitlines()
        self.assertEqual(sum(1 for call in calls if "load" in call), 8)
        self.assertTrue((models / "example-70b" / "model.safetensors").is_file())
        self.assertIn("load.sh: OK", result.stdout)

    def load_with(self, shell, **env):
        self.assertEqual(self.run_sh("verify.sh", str(self.inside), shell=shell).returncode, 0)
        models = Path(self.tmp.name) / f"models-{shell}"
        return self.run_sh("load.sh", str(self.inside), str(models), shell=shell, env=dict(self.env, **env))

    def test_load_stops_on_another_image_id(self):
        # Without the documented containerd signal, another ID stops load.sh and names the way out.
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.load_with(shell, STUB_WRONG_ID="1")
                self.assertEqual(result.returncode, 1)
                self.assertIn("did not load as sha256:", result.stderr)
                self.assertIn("containerd image store", result.stderr)
                self.assertIn("AIRGAP_SKIP_IMAGE_ID_CHECK=1 sh load.sh", result.stderr)

    def test_load_with_the_classic_store_and_the_same_id_is_ok(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.load_with(shell, STUB_DRIVER_STATUS="[[Backing Filesystem extfs]]")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("load.sh: OK", result.stdout)
                self.assertNotIn("note:", result.stdout)

    def test_another_id_on_the_containerd_store_is_a_note(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                result = self.load_with(shell, STUB_WRONG_ID="1", STUB_DRIVER_STATUS=CONTAINERD_STATUS)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("load.sh: note: loaded images/", result.stdout)
                self.assertIn("reports the digest of the image manifest as the", result.stdout)
                self.assertIn("checked the bytes of the archive against SHA256SUMS", result.stdout)
                self.assertIn("load.sh: OK", result.stdout)

    def test_the_override_skips_the_id_check_and_says_so(self):
        for shell in SHELLS:
            with self.subTest(shell=shell):
                Path(self.env["DOCKER_CALLS"]).unlink(missing_ok=True)
                result = self.load_with(shell, STUB_WRONG_ID="1", AIRGAP_SKIP_IMAGE_ID_CHECK="1")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.count("image ID check skipped (AIRGAP_SKIP_IMAGE_ID_CHECK=1)"), 8)
                calls = Path(self.env["DOCKER_CALLS"]).read_text(encoding="utf-8")
                self.assertNotIn("inspect", calls)

    def test_load_after_a_change_to_sha256sums_needs_verify_again(self):
        self.assertEqual(self.run_sh("verify.sh", str(self.inside)).returncode, 0)
        with (self.inside / "SHA256SUMS").open("a", encoding="utf-8") as handle:
            handle.write("0" * 64 + "  extra\n")
        self.assertEqual(self.run_sh("load.sh", str(self.inside), "models").returncode, 1)

    def test_load_arguments(self):
        self.assertEqual(self.run_sh("load.sh", "a", "b", "c").returncode, 2)

    def test_an_archive_not_in_sha256sums_is_never_loaded(self):
        self.assertEqual(self.run_sh("verify.sh", str(self.inside)).returncode, 0)
        stray = self.inside / "images/extra/stray.tar"
        stray.parent.mkdir(parents=True)
        stray.write_bytes(b"not listed")
        for shell in SHELLS:
            with self.subTest(shell=shell):
                Path(self.env["DOCKER_CALLS"]).unlink(missing_ok=True)
                result = self.run_sh("load.sh", str(self.inside), str(Path(self.tmp.name) / "models"), shell=shell)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("not loaded, because SHA256SUMS does not list it: images/extra/stray.tar", result.stdout)
                calls = Path(self.env["DOCKER_CALLS"]).read_text(encoding="utf-8")
                self.assertNotIn("stray.tar", calls)
                self.assertEqual(sum(1 for call in calls.splitlines() if "load" in call), 8)


if __name__ == "__main__":
    unittest.main()
