"""Each skill against the Agent Skills specification and Anthropic's checklist for effective skills
(https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, "Checklist for
effective Skills"): frontmatter, SKILL.md under 500 lines, every file one level deep from SKILL.md,
a table of contents in long references, no scripts."""
import re
import unittest

from tests import SKILL_DIRS

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.S)
PATH = re.compile(r"`((?:references|catalog)/[A-Za-z0-9_./-]+\.md)`")


def frontmatter(skill_dir):
    match = FRONTMATTER.match((skill_dir / "SKILL.md").read_text(encoding="utf-8"))
    assert match, skill_dir
    fields = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def markdown_files(skill_dir):
    return sorted(p for p in skill_dir.rglob("*") if p.is_file())


class FrontmatterTest(unittest.TestCase):
    def test_name_matches_the_folder_and_the_specification(self):
        for skill_dir in SKILL_DIRS:
            name = frontmatter(skill_dir)["name"]
            with self.subTest(skill=skill_dir.name):
                self.assertEqual(name, skill_dir.name)
                self.assertRegex(name, r"^[a-z0-9]+(-[a-z0-9]+)*$")
                self.assertLessEqual(len(name), 64)

    def test_description_says_what_and_when_in_the_third_person(self):
        for skill_dir in SKILL_DIRS:
            description = frontmatter(skill_dir)["description"]
            with self.subTest(skill=skill_dir.name):
                self.assertLessEqual(len(description), 1024)
                self.assertIn("Use when", description)
                self.assertFalse(re.match(r"(I|You|We)\b", description), "third person")
                self.assertNotIn("<", description)


class StructureTest(unittest.TestCase):
    def test_skill_md_is_under_500_lines(self):
        for skill_dir in SKILL_DIRS:
            with self.subTest(skill=skill_dir.name):
                self.assertLess(len((skill_dir / "SKILL.md").read_text(encoding="utf-8").splitlines()), 500)

    def test_a_skill_ships_markdown_only(self):
        for skill_dir in SKILL_DIRS:
            for path in markdown_files(skill_dir):
                with self.subTest(path=path.relative_to(skill_dir).as_posix()):
                    self.assertEqual(path.suffix, ".md")

    def test_every_path_a_skill_names_exists(self):
        for skill_dir in SKILL_DIRS:
            for path in markdown_files(skill_dir):
                for named in PATH.findall(path.read_text(encoding="utf-8")):
                    with self.subTest(file=path.name, named=named):
                        self.assertTrue((skill_dir / named).is_file())

    def test_every_file_is_one_level_deep_from_skill_md(self):
        # SKILL.md names every reference and catalog file itself, so an agent never has to
        # follow a chain of files to find one.
        for skill_dir in SKILL_DIRS:
            named = set(PATH.findall((skill_dir / "SKILL.md").read_text(encoding="utf-8")))
            for path in markdown_files(skill_dir):
                relative = path.relative_to(skill_dir).as_posix()
                if relative != "SKILL.md":
                    with self.subTest(file=relative):
                        self.assertIn(relative, named)

    def test_long_references_open_with_contents(self):
        for skill_dir in SKILL_DIRS:
            for path in sorted((skill_dir / "references").rglob("*.md")):
                text = path.read_text(encoding="utf-8")
                if len(text.splitlines()) > 100:
                    with self.subTest(file=path.name):
                        self.assertIn("\n## Contents\n", text[:600])

    def test_no_windows_paths(self):
        for skill_dir in SKILL_DIRS:
            for path in markdown_files(skill_dir):
                with self.subTest(file=path.name):
                    self.assertNotRegex(path.read_text(encoding="utf-8"), r"`(references|catalog)\\")

    def test_the_workflow_is_a_copyable_checklist(self):
        for skill_dir in SKILL_DIRS:
            text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=skill_dir.name):
                self.assertIn("## Workflow", text)
                self.assertGreaterEqual(text.count("- [ ] "), 8)
                self.assertIn("## Self-", text)


if __name__ == "__main__":
    unittest.main()
