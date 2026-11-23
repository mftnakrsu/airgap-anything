"""Builders for airgap-transfer tests: a finished architect project, transfer.json answers
and a fake fetched bundle. The architect side is built with airgap-architect's own code,
so these tests also check that the two skills agree on the manifest."""
from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

from airgap_lib.catalog import Catalog
from tests import projects, support
from transfer_lib.items import checksums_path
from transfer_lib.state import new_state, save_state, state_path

COMMIT = "0123456789abcdef0123456789abcdef01234567"
SUMS_URL = "https://downloads.example.test/alpha/SHA256SUMS"


def transfer_catalog(root: Path, sums_url: str = SUMS_URL) -> Catalog:
    """The fixture catalog with packages on the engine: one per architecture and a script.
    `sums_url` is where the publisher's checksum list of the two binaries lives."""
    components = support.fixture_components()
    components[0] = support.component(
        "alpha-engine",
        "llm-serving",
        airgap={
            "images": [{"ref": "registry.example.test/synthetic/alpha-engine:1.2.3", "digest": ""}],
            "packages": [
                support.package("alpha-cli-1.2.3-amd64", "amd64", sums_url),
                support.package("alpha-cli-1.2.3-arm64", "arm64", sums_url),
                support.package("install.sh", "any"),
            ],
            "runtime_downloads": ["Tokenizer data, fetched on first start."],
            "telemetry": [{"what": "usage ping", "disable": "ALPHA_PING=0"}],
        },
    )
    return support.load_fixture_catalog(Path(root), components)


def make_project(root: Path, catalog: Catalog, answers=None, decisions=None, language="en") -> Path:
    """A project with blueprint.json and both manifest files; returns the project root."""
    blueprint = projects.build_blueprint(catalog, answers, decisions)
    blueprint["language"] = language
    projects.write_project(Path(root), catalog, blueprint)
    return Path(root)


def default_answers(bundle: Path, **overrides) -> dict:
    answers = {
        "bundle.path": str(bundle),
        "models": {"example-70b": {"source": "huggingface", "repo": "example/model-70b", "revision": COMMIT}},
        "medium.capacity_gb": 1000,
        "medium.filesystem": "exfat",
    }
    answers.update(overrides)
    return answers


def write_state(project: Path, answers: dict, manual=(), plan=None) -> Path:
    manifest = json.loads((project / "docs" / "airgap" / "transfer-manifest.json").read_text(encoding="utf-8"))
    state = new_state(manifest["inputs_digest"])
    state["answers"] = answers
    state["manual"] = list(manual)
    if plan is not None:
        state["plan"] = plan
    path = state_path(project)
    save_state(path, state)
    return path


def image_archive(ref: str, arch: str = "amd64", payload: bytes = b"layer") -> bytes:
    """A small archive in the layout docker load reads: manifest.json, a config, a layer."""
    config = json.dumps({"architecture": arch, "os": "linux"}).encode()
    config_name = "blobs/sha256/" + hashlib.sha256(config).hexdigest()
    layer_name = "blobs/sha256/" + hashlib.sha256(payload).hexdigest()
    manifest = json.dumps([{"Config": config_name, "RepoTags": [ref], "Layers": [layer_name]}]).encode()
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, data in (("manifest.json", manifest), (config_name, config), (layer_name, payload)):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def fake_fetch(bundle: Path, items: list[dict], sizes: dict | None = None, arch: str = "amd64") -> None:
    """Write what fetch.sh would leave for every non-manual item. `sizes` maps an item id
    to the number of bytes of its main file (default: a few bytes)."""
    sizes = sizes or {}
    bundle = Path(bundle)
    lists: dict[Path, list[str]] = {}
    for item in items:
        target = bundle / item["path"]
        size = sizes.get(item["id"])
        if item["kind"] == "image":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(image_archive(item["ref"], arch, b"x" * (size or 5)))
            target.with_suffix(".digest").write_text("sha256:" + "a" * 64 + "\n", encoding="utf-8")
        elif item["kind"] == "model":
            target.mkdir(parents=True, exist_ok=True)
            (target / "model.safetensors").write_bytes(b"w" * (size or 7))
            (target / "config.json").write_text("{}", encoding="utf-8")
            (target / "LICENSE").write_text("Example licence\n", encoding="utf-8")
        elif item["kind"] == "package":
            target.parent.mkdir(parents=True, exist_ok=True)
            data = (item["file"].encode() * ((size or 9) // max(1, len(item["file"])) + 1))[: size or 9]
            target.write_bytes(data)
            listed = checksums_path(item)
            if listed:
                lists.setdefault(bundle / listed, []).append(f"{hashlib.sha256(data).hexdigest()}  {item['file']}")
    for path, lines in lists.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_script(name: str, project: Path, *args, env=None):
    """Run one of airgap-transfer's scripts as the agent does; returns the CompletedProcess."""
    import subprocess
    import sys

    from tests import TRANSFER_SCRIPTS_DIR

    command = [sys.executable, str(TRANSFER_SCRIPTS_DIR / name), "--project-root", str(project), *args]
    return subprocess.run(command, capture_output=True, text=True, env=env)


def planned_project(tmp: Path, answers=None, architect_answers=None, decisions=None, language="en", **transfer):
    """A project whose transfer.json has answers and a plan (made without plan.py, so no
    tools are needed), and an empty bundle folder. Returns (project, bundle)."""
    from transfer_lib.inputs import channel_of
    from transfer_lib.items import build_items

    tmp = Path(tmp)
    catalog = transfer_catalog(tmp / "catalog")
    architect_answers = support.base_answers(**(architect_answers or {}))
    project = make_project(tmp / "project", catalog, architect_answers, decisions, language)
    bundle = tmp / "bundle"
    bundle.mkdir(exist_ok=True)
    answers = default_answers(bundle, **transfer) if answers is None else answers
    folder = project / "docs" / "airgap"
    manifest = json.loads((folder / "transfer-manifest.json").read_text(encoding="utf-8"))
    blueprint = json.loads((folder / "blueprint.json").read_text(encoding="utf-8"))
    plan = {
        "items": build_items(manifest, answers),
        "tools": {},
        "platform": manifest["platform"],
        "channel": channel_of(blueprint),
        "planned": "2026-11-22T10:00:00Z",
    }
    write_state(project, answers, plan=plan)
    return project, bundle


def load_state_of(project: Path) -> dict:
    from transfer_lib.state import load_state, state_path

    return load_state(state_path(project))


def update_state(project: Path, change) -> dict:
    from transfer_lib.state import save_state, state_path

    state = load_state_of(project)
    change(state)
    save_state(state_path(project), state)
    return state


def settle_manual(project: Path) -> None:
    """Mark every manual item of the plan 'not needed', with a reason."""
    def change(state):
        state["manual"] = [
            {"item": item["name"], "status": "not_needed", "reason": "Staged by the operator from an earlier transfer."}
            for item in state["plan"]["items"]
            if item["kind"] == "manual"
        ]
    update_state(project, change)


def packed_project(tmp: Path, sizes=None, **kwargs):
    """planned_project, fetched with fake files, manual items settled and packed with pack.py.
    Returns (project, bundle)."""
    project, bundle = planned_project(tmp, **kwargs)
    fake_fetch(bundle, load_state_of(project)["plan"]["items"], sizes)
    settle_manual(project)
    result = run_script("pack.py", project)
    assert result.returncode == 0, result.stdout + result.stderr
    return project, bundle
