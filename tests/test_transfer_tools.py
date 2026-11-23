import unittest

from tests.test_transfer_items import MANIFEST, SOURCE
from transfer_lib.items import build_items
from transfer_lib.tools import COMMANDS, MissingToolError, find_tools


class ToolsTest(unittest.TestCase):
    def items(self):
        return build_items(MANIFEST, {"models": {"chat model": SOURCE}})

    def test_the_preferred_tool_is_chosen(self):
        everything = lambda name: f"/usr/bin/{name}"  # noqa: E731
        tools = find_tools(self.items(), everything)
        self.assertEqual(tools["images"], "skopeo")
        self.assertEqual((tools["models"], tools["packages"]), ("hf", "curl"))
        self.assertEqual(tools["hash.md5"], "md5sum")

    def test_docker_is_used_without_the_copier(self):
        tools = find_tools(self.items(), lambda name: None if name == "skopeo" else name)
        self.assertEqual(tools["images"], "docker")

    def test_a_missing_tool_names_what_needs_it(self):
        with self.assertRaises(MissingToolError) as caught:
            find_tools(self.items(), lambda name: None if name in ("hf", "curl") else name)
        self.assertEqual(caught.exception.missing, {"hf": ["model:chat model"], "curl": ["package:alpha:alpha-1-amd64.tgz"]})

    def test_only_the_tools_the_items_need(self):
        self.assertEqual(find_tools([], lambda name: None), {})


class CommandTableTest(unittest.TestCase):
    """Each command line is filled from the tool's documentation (references/fetch.md)."""

    def test_every_command_is_filled_and_sourced(self):
        for key, command in COMMANDS.items():
            with self.subTest(command=key):
                self.assertTrue(command.line.strip(), "fill `line` from the documentation")
                self.assertTrue(command.source.startswith("https://"), "record the page in `source`")
                for variable in command.uses:
                    self.assertIn(variable, command.line)
                if command.uses:
                    self.assertTrue(command.line.startswith(command.tool + " "), command.line)


if __name__ == "__main__":
    unittest.main()
