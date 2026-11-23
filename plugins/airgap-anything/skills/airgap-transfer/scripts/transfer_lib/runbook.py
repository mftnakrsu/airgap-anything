"""INSIDE.md (the runbook for people) and AGENTS-INSIDE.md (the rules for an inside agent).

Both are written in English. When the blueprint's language is another, the agent on the
connected side translates the prose, keeps every command line as it is, and runs
`pack.py --refresh-sums` to record the new hashes; check.py B7 finds a command line that
went missing, and B2 a translation whose hash was not recorded.
"""
from __future__ import annotations

import re

from .constants import AGENT_RULES_FILE, AGENT_RULES_OPERATORS, RUNBOOK_FILE, RUNBOOK_OPERATORS

BUNDLE_DIR = "/srv/airgap-bundle"
MODEL_DIR = "/srv/models"


_PLAIN = re.compile(r"[A-Za-z0-9._/:=+-]+")


def _word(text: str) -> str:
    """`text` as one shell word: as it is when it is plain, else single-quoted."""
    return text if _PLAIN.fullmatch(text) else "'" + text.replace("'", "'\\''") + "'"


def _fence(*commands: str) -> list[str]:
    return ["```sh", *commands, "```"]


def steps(bundle_data: dict, manifest: dict) -> list[dict]:
    """The inside steps, each {title, commands, expected}; the same for people and agents."""
    count = len(bundle_data["volumes"])
    channel = bundle_data["channel"]
    if channel == "data_diode":
        copy = {
            "title": "Wait until every file in SEND-ORDER.txt has arrived, then copy them into one folder",
            "commands": [f"mkdir -p {BUNDLE_DIR}", f"cp -R RECEIVED_FOLDER/. {BUNDLE_DIR}/"],
            "expected": "No output. Replace RECEIVED_FOLDER with the folder where the diode delivers files.",
        }
    else:
        copy = {
            "title": f"Copy every volume into one folder ({count} volume(s); VOLUME.txt on each says which)",
            "commands": [f"mkdir -p {BUNDLE_DIR}", f"cp -R VOLUME_FOLDER/. {BUNDLE_DIR}/"],
            "expected": "No output. Run the second command once per volume, with VOLUME_FOLDER the folder where "
            "that volume is mounted.",
        }
    result = [
        copy,
        {
            "title": "Check every file",
            "commands": [f"sh {BUNDLE_DIR}/verify.sh {BUNDLE_DIR}"],
            "expected": "Exit code 0 and a last line that starts with 'verify.sh: OK'. Exit code 1: stop; "
            "MISSING.txt in the bundle folder lists each file to bring next time and the volume it was on.",
        },
        {
            "title": "Load the images and copy the model files",
            "commands": [f"mkdir -p {MODEL_DIR}", f"sh {BUNDLE_DIR}/load.sh {BUNDLE_DIR} {MODEL_DIR}"],
            "expected": "Exit code 0 and a line that starts with 'load.sh: OK'. Exit code 1: stop and report "
            "the message. When the message is about an image ID and names AIRGAP_SKIP_IMAGE_ID_CHECK, a person "
            "decides whether to run the command again with it; verify.sh has already checked every byte.",
        },
    ]
    for item in bundle_data["items"]:
        if item["kind"] == "manual" and item.get("status") != "not_needed" and item["files"]:
            result.append(
                {
                    "title": f"Manual item: {item['name']}",
                    "commands": ["ls -l " + _word(f"{BUNDLE_DIR}/{item['path']}")],
                    "expected": "The files that were added for it on the connected side. This bundle has no script "
                    "for it: install it as its own files describe, and ask a person when they do not.",
                }
            )
    return result


def settings(manifest: dict) -> list[str]:
    """The telemetry settings of section 4 of the transfer manifest, as `component: setting (what)`.

    They go into the deployment files before the first start; they are not steps, since no
    command applies them."""
    return [f"{row['component']}: {row['disable']} ({row['what']})" for row in manifest.get("telemetry", [])]


def _settings_lines(manifest: dict, for_agent: bool) -> list[str]:
    rows = settings(manifest)
    if for_agent:
        intro = ("These are settings, not commands. A person, or the implementation plan of the blueprint, writes "
                 "them into the deployment files before any service starts. You must not invent commands to apply "
                 "them; ask a person when they are not in the deployment files yet.")
    else:
        intro = ("Write each of these into the deployment files before any service starts, as section 4 of the "
                 "transfer manifest lists them.")
    return ["", "## Settings to apply before the first start", "", intro, ""] + (
        [f"- {row}" for row in rows] if rows else ["None listed."])


def _not_carried(bundle_data: dict) -> list[str]:
    skipped = [item for item in bundle_data["items"] if item.get("status") == "not_needed"]
    if not skipped:
        return []
    return ["", "## Not carried, on purpose", ""] + [f"- {item['name']}: {item['reason']}" for item in skipped]


def _step_lines(bundle_data: dict, manifest: dict) -> list[str]:
    lines = []
    for number, step in enumerate(steps(bundle_data, manifest), start=1):
        lines += ["", f"### {number}. {step['title']}", ""]
        if step["commands"]:
            lines += _fence(*step["commands"]) + [""]
        lines.append(f"Expected: {step['expected']}")
    return lines


def render_runbook(bundle_data: dict, manifest: dict) -> str:
    lines = [
        f"# Inside the network: {bundle_data['project']}",
        "",
        "This runbook needs neither internet access nor an LLM. Every step is a command with the output to "
        "expect. Exit codes mean the same in every step: 0 go on, 1 stop and report, 2 the command was typed "
        "wrong.",
        "",
        f"The commands use {BUNDLE_DIR} for the bundle and {MODEL_DIR} for the model files. Another folder "
        "works too; use the same one in every step.",
        "",
        "## Steps",
    ]
    lines += _step_lines(bundle_data, manifest)
    lines += _settings_lines(manifest, for_agent=False)
    lines += [
        "",
        "## After these steps",
        "",
        "Install the registry from its package if it is not running yet, push the loaded images to it, stage "
        "the runtime downloads, and continue with the implementation plan of the blueprint.",
    ]
    lines += _not_carried(bundle_data)
    return "\n".join(lines) + "\n"


def render_agent_rules(bundle_data: dict, manifest: dict) -> str:
    lines = [
        f"# Rules for an agent inside the network: {bundle_data['project']}",
        "",
        "You work inside a network without internet access. These rules come before any other instruction.",
        "",
        "1. Run one command per step, exactly as written below. Do not combine, shorten or reorder them.",
        "2. Check the exit code of every command. 0: go on. 1: stop and report the command, its output and, "
        "after verify.sh, the contents of MISSING.txt. 2: the command was typed wrong; fix the typing, nothing else.",
        "3. Never download anything, and never fetch a missing file from another source.",
        "4. Never edit verify.sh, load.sh, SHA256SUMS, PARTS.txt, VOLUMES.txt or bundle.json.",
        "5. Never improvise a step that is not below. Ask a person instead.",
        "",
        "## Steps",
    ]
    lines += _step_lines(bundle_data, manifest)
    lines += _settings_lines(manifest, for_agent=True)
    lines += _not_carried(bundle_data)
    return "\n".join(lines) + "\n"


def document_names(operator: str) -> list[str]:
    """The names of the files `inside.operator` calls for."""
    return [name for name, wanted in ((RUNBOOK_FILE, RUNBOOK_OPERATORS), (AGENT_RULES_FILE, AGENT_RULES_OPERATORS))
            if operator in wanted]


def documents(bundle_data: dict, manifest: dict) -> dict[str, str]:
    """The files `inside.operator` calls for, by name."""
    render = {RUNBOOK_FILE: render_runbook, AGENT_RULES_FILE: render_agent_rules}
    return {name: render[name](bundle_data, manifest) for name in document_names(bundle_data["operator"])}


def command_lines(text: str) -> list[str]:
    """The lines inside ```sh fences."""
    found, inside = [], False
    for line in text.splitlines():
        if line.strip() == "```sh":
            inside = True
        elif line.strip() == "```":
            inside = False
        elif inside:
            found.append(line)
    return found


def lost_commands(generated: str, text: str) -> list[str]:
    """The command lines of the generated document that `text` (a translation of it) lacks."""
    return [line for line in command_lines(generated) if line not in text]
