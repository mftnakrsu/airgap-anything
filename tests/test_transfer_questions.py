import tempfile
import unittest
from pathlib import Path

from transfer_lib.questions import answer_problems, include_benchmark, inside_git_repository, needed_questions

COMMIT = "0123456789abcdef0123456789abcdef01234567"
MANIFEST = {"models": [{"name": "chat-model", "role": "chat"}], "images": [], "packages": []}


class NeededQuestionsTest(unittest.TestCase):
    def test_per_channel(self):
        self.assertEqual(needed_questions("removable_media", MANIFEST),
                         ["bundle.path", "models", "medium.capacity_gb", "medium.filesystem"])
        self.assertEqual(needed_questions("data_diode", MANIFEST), ["bundle.path", "models", "channel.max_file_gb"])
        self.assertEqual(needed_questions("staging_host", MANIFEST), ["bundle.path", "models", "channel.max_file_gb"])
        self.assertEqual(needed_questions("other", MANIFEST),
                         ["bundle.path", "models", "medium.capacity_gb", "medium.filesystem"])

    def test_other_without_a_medium_skips_the_filesystem(self):
        self.assertEqual(needed_questions("other", MANIFEST, {"medium.capacity_gb": "none"}),
                         ["bundle.path", "models", "medium.capacity_gb"])

    def test_models_and_benchmark_only_when_the_manifest_has_them(self):
        manifest = {"models": [], "images": [{"benchmark": True}], "packages": []}
        self.assertEqual(needed_questions("data_diode", manifest), ["bundle.path", "channel.max_file_gb", "include_benchmark"])

    def test_include_benchmark_defaults_to_true(self):
        self.assertTrue(include_benchmark({}))
        self.assertFalse(include_benchmark({"include_benchmark": False}))


class AnswerProblemsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name) / "project"
        self.project.mkdir()
        self.answers = {
            "bundle.path": str(Path(self.tmp.name) / "bundle"),
            "models": {"chat-model": {"source": "huggingface", "repo": "example/chat", "revision": COMMIT}},
            "medium.capacity_gb": 1000,
            "medium.filesystem": "exfat",
        }

    def problems(self, channel="removable_media", **changes):
        answers = dict(self.answers, **changes)
        return answer_problems(answers, channel, MANIFEST, self.project)

    def test_complete_answers_pass(self):
        self.assertEqual(self.problems(), [])

    def test_missing_answers_are_listed(self):
        self.assertEqual(answer_problems({}, "data_diode", MANIFEST, self.project),
                         ["bundle.path: missing", "models: missing", "channel.max_file_gb: missing"])

    def test_bundle_path_must_be_absolute_and_outside_git(self):
        self.assertEqual(self.problems(**{"bundle.path": "bundle"}), ["bundle.path: must be an absolute path"])
        inside = str(self.project / "bundle")
        self.assertEqual(self.problems(**{"bundle.path": inside}),
                         ["bundle.path: must be outside the git repository: a bundle can be hundreds of gigabytes"])
        repo = Path(self.tmp.name) / "repo"
        (repo / ".git").mkdir(parents=True)
        self.assertTrue(inside_git_repository(repo / "a" / "b"))
        self.assertEqual(self.problems(**{"bundle.path": str(repo / "bundle")}),
                         ["bundle.path: must be outside the git repository: a bundle can be hundreds of gigabytes"])

    def test_model_sources(self):
        local = Path(self.tmp.name) / "weights"
        local.mkdir()
        good = [
            {"source": "huggingface", "repo": "example/chat", "revision": COMMIT},
            {"source": "huggingface", "repo": "example/chat", "revision": COMMIT, "allow_pickle": True},
            {"source": "local", "path": str(local)},
        ]
        for source in good:
            with self.subTest(source=source):
                self.assertEqual(self.problems(models={"chat-model": source}), [])
        bad = [
            ({"source": "huggingface", "repo": "chat", "revision": COMMIT}, "'chat-model': repo must be <organization>/<name>"),
            ({"source": "huggingface", "repo": "example/chat", "revision": "main"},
             "'chat-model': revision must be the full 40-character commit hash; a tag or branch cannot be recorded as what was fetched"),
            ({"source": "local", "path": "weights"}, "'chat-model': path must be an absolute path to an existing folder"),
            ({"source": "ftp"}, "'chat-model': source must be huggingface or local"),
            ({"source": "local", "path": str(local), "allow_pickle": "yes"}, "'chat-model': allow_pickle must be true or false"),
        ]
        for source, message in bad:
            with self.subTest(source=source):
                self.assertEqual(self.problems(models={"chat-model": source}), [f"models: {message}"])
        self.assertEqual(self.problems(models={}), ["models: 'chat-model': missing; give its source"])
        self.assertEqual(self.problems(models={"chat-model": good[0], "other": good[0]}),
                         ["models: 'other': not a model of the manifest"])

    def test_medium_answers(self):
        self.assertEqual(self.problems(**{"medium.capacity_gb": 0}),
                         ["medium.capacity_gb: must be a number of gigabytes above 0 and at most 1000000"])
        self.assertEqual(self.problems(**{"medium.filesystem": "hfs"}),
                         ["medium.filesystem: must be one of fat32, exfat, ntfs, ext4, other"])
        self.assertEqual(self.problems("other", **{"medium.capacity_gb": "none", "medium.filesystem": None}), [])

    def test_sizes_that_cannot_be_bytes_are_problems(self):
        for value in (1e999, float("nan"), 1e300, 10**400, 1_000_001, 1e-12, True):
            with self.subTest(value=value):
                self.assertEqual(self.problems(**{"medium.capacity_gb": value}),
                                 ["medium.capacity_gb: must be a number of gigabytes above 0 and at most 1000000"])
                self.assertEqual(
                    self.problems("data_diode", **{"channel.max_file_gb": value}),
                    ["channel.max_file_gb: must be a number of gigabytes above 0 and at most 1000000, or 'none'"],
                )
        self.assertEqual(self.problems(**{"medium.capacity_gb": 1_000_000}), [])

    def test_file_limit_answers(self):
        for value in (4, 0.5, "none"):
            self.assertEqual(self.problems("data_diode", **{"channel.max_file_gb": value}), [])
        self.assertEqual(self.problems("staging_host", **{"channel.max_file_gb": -1}),
                         ["channel.max_file_gb: must be a number of gigabytes above 0 and at most 1000000, or 'none'"])
