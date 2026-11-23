import hashlib
import io
import json
import os
import tarfile
import tempfile
import unittest
from pathlib import Path

from tests import transfer_projects
from transfer_lib.archive import ArchiveError, read_image_archive
from transfer_lib.constants import FAT32_MAX_FILE_BYTES, GB
from transfer_lib.hashing import hash_file, part_count
from transfer_lib.volumes import MAX_PARTS, assign_volumes, max_file_bytes, part_size, units_of, volume_capacity


class HashingTest(unittest.TestCase):
    def test_whole_and_part_hashes_in_one_read(self):
        data = os.urandom(3 * 1024 * 1024 + 5)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f"
            path.write_bytes(data)
            for size in (1024 * 1024 + 3, 2 * 1024 * 1024, len(data) - 1):
                with self.subTest(part_size=size):
                    whole, parts = hash_file(path, size)
                    self.assertEqual(whole, hashlib.sha256(data).hexdigest())
                    expected = [hashlib.sha256(data[i:i + size]).hexdigest() for i in range(0, len(data), size)]
                    self.assertEqual(parts, expected)
            self.assertEqual(hash_file(path, len(data))[1], [])
            self.assertEqual(hash_file(path)[1], [])

    def test_part_count(self):
        self.assertEqual(part_count(10, None), 0)
        self.assertEqual(part_count(10, 10), 0)
        self.assertEqual(part_count(11, 10), 2)

    def test_a_part_size_of_zero_or_less_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "f"
            path.write_bytes(b"abc")
            for size in (0, -1):
                with self.subTest(part_size=size):
                    with self.assertRaisesRegex(ValueError, "part size must be above 0"):
                        hash_file(path, size)
                    with self.assertRaisesRegex(ValueError, "part size must be above 0"):
                        part_count(3, size)


class VolumePlanTest(unittest.TestCase):
    def test_fat32_limit_and_reserve(self):
        answers = {"medium.capacity_gb": 1000, "medium.filesystem": "fat32"}
        self.assertEqual(max_file_bytes("removable_media", answers), FAT32_MAX_FILE_BYTES)
        self.assertEqual(volume_capacity("removable_media", answers), int(1000 * GB * 0.98))
        self.assertEqual(part_size("removable_media", answers), FAT32_MAX_FILE_BYTES)
        exfat = {"medium.capacity_gb": 1000, "medium.filesystem": "exfat"}
        self.assertIsNone(max_file_bytes("removable_media", exfat))
        self.assertEqual(part_size("removable_media", exfat), int(1000 * GB * 0.98))

    def test_sizes_are_whole_bytes(self):
        self.assertEqual(volume_capacity("removable_media", {"medium.capacity_gb": 1000}), 980 * GB)
        self.assertEqual(max_file_bytes("data_diode", {"channel.max_file_gb": 4.1}), 4_100_000_000)
        self.assertEqual(volume_capacity("removable_media", {"medium.capacity_gb": 4.1}), 4_018_000_000)
        self.assertEqual(volume_capacity("removable_media", {"medium.capacity_gb": 0.000000123}), 120)

    def test_sizes_that_cannot_be_bytes_do_not_raise(self):
        for value in (1e999, float("nan"), 1e300, 10**400, True, 1e-12):
            with self.subTest(value=value):
                medium = {"medium.capacity_gb": value, "medium.filesystem": "exfat"}
                self.assertIsNone(volume_capacity("removable_media", medium))
                self.assertIsNone(part_size("removable_media", medium))
                self.assertIsNone(max_file_bytes("data_diode", {"channel.max_file_gb": value}))
                self.assertIsNone(part_size("data_diode", {"channel.max_file_gb": value}))

    def test_channels_without_a_medium(self):
        self.assertEqual(max_file_bytes("data_diode", {"channel.max_file_gb": 4}), 4 * GB)
        self.assertIsNone(max_file_bytes("staging_host", {"channel.max_file_gb": "none"}))
        self.assertIsNone(volume_capacity("data_diode", {"channel.max_file_gb": 4}))
        self.assertIsNone(volume_capacity("other", {"medium.capacity_gb": "none"}))

    def test_large_files_are_cut_into_parts(self):
        files = [{"path": "models/m/w.safetensors", "size": 25, "sha256": "w", "parts": ["p1", "p2", "p3"]},
                 {"path": "packages/a/x", "size": 4, "sha256": "x", "parts": []}]
        units = units_of(files, 10)
        self.assertEqual(
            [(u["path"], u["size"], u["sha256"], u["of"]) for u in units],
            [
                ("models/m/w.safetensors.part001", 10, "p1", "models/m/w.safetensors"),
                ("models/m/w.safetensors.part002", 10, "p2", "models/m/w.safetensors"),
                ("models/m/w.safetensors.part003", 5, "p3", "models/m/w.safetensors"),
                ("packages/a/x", 4, "x", None),
            ],
        )

    def test_more_than_999_parts_is_refused(self):
        self.assertEqual(MAX_PARTS, 999)
        parts = [str(index) for index in range(1000)]
        last = units_of([{"path": "f", "size": 999, "sha256": "f", "parts": parts[:999]}], 1)[-1]
        self.assertEqual(last["path"], "f.part999")
        with self.assertRaisesRegex(ValueError, "f: would be cut into 1000 parts; at most 999"):
            units_of([{"path": "f", "size": 1000, "sha256": "f", "parts": parts}], 1)

    def test_first_fit_largest_first(self):
        units = [{"path": name, "size": size} for name, size in (("a", 3), ("b", 7), ("c", 5), ("d", 5), ("e", 2))]
        volumes = assign_volumes(units, 10)
        self.assertEqual([[u["path"] for u in volume] for volume in volumes], [["b", "a"], ["c", "d"], ["e"]])
        self.assertEqual([[u["path"] for u in volume] for volume in assign_volumes(units, None)], [["b", "c", "d", "a", "e"]])


def _archive(manifest: bytes, config: bytes) -> bytes:
    """A tar with this manifest.json and config file (the config at blobs/sha256/c)."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in (("manifest.json", manifest), ("blobs/sha256/c", config)):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


class ArchiveTest(unittest.TestCase):
    def test_reads_id_and_platform(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.tar"
            path.write_bytes(transfer_projects.image_archive("example/a:1", "arm64"))
            image = read_image_archive(path)
            self.assertEqual(image["platform"], "linux/arm64")
            self.assertRegex(image["id"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(image["tags"], ["example/a:1"])
            path.write_bytes(b"not a tar")
            with self.assertRaises(ArchiveError):
                read_image_archive(path)

    def test_a_malformed_config_is_an_archive_error(self):
        manifest = json.dumps([{"Config": "blobs/sha256/c", "RepoTags": ["example/a:1"], "Layers": []}]).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.tar"
            for config in (b"{not json", b"\xff\xfe", b"[1, 2]"):
                with self.subTest(config=config):
                    path.write_bytes(_archive(manifest, config))
                    with self.assertRaisesRegex(ArchiveError, "a.tar: not an image archive"):
                        read_image_archive(path)

    def test_deep_nesting_and_link_loops_are_archive_errors(self):
        deep = b"[" * 200000
        manifest = json.dumps([{"Config": "blobs/sha256/c", "RepoTags": [], "Layers": []}]).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.tar"
            for name, data in (("manifest", _archive(deep, b"{}")), ("config", _archive(manifest, deep))):
                with self.subTest(deep=name):
                    path.write_bytes(data)
                    with self.assertRaisesRegex(ArchiveError, "a.tar: not an image archive"):
                        read_image_archive(path)
            with self.subTest("symlink loop"):
                with tarfile.open(path, mode="w") as tar:
                    link = tarfile.TarInfo("manifest.json")
                    link.type, link.linkname = tarfile.SYMTYPE, "manifest.json"
                    tar.addfile(link)
                with self.assertRaisesRegex(ArchiveError, "a.tar: not an image archive"):
                    read_image_archive(path)

    def test_more_than_one_image_is_an_archive_error(self):
        entry = {"Config": "blobs/sha256/c", "RepoTags": [], "Layers": []}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "a.tar"
            path.write_bytes(_archive(json.dumps([entry, entry]).encode(), b"{}"))
            with self.assertRaisesRegex(ArchiveError, "holds 2 images; one was expected"):
                read_image_archive(path)


if __name__ == "__main__":
    unittest.main()
