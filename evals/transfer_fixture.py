"""Build a transfer scenario on disk for the behavior runs of evals/README.md: a finished
architect project, and with --fetched a fake fetched bundle of small files with its plan file,
so that the pack phase runs without downloads.

    python3 evals/transfer_fixture.py --scenario department --out DIR [--variant fat32] [--fetched]

DIR gets project/ (docs/airgap/blueprint.md and transfer-manifest.md, copied from
evals/transfer-scenarios/NAME/project/) and, with --fetched, bundle/ and
project/docs/airgap/transfer-plan.md with every item fetched and every manual item settled.
Repository tooling, standard library only; the skills themselves ship no code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCENARIOS = REPO_ROOT / "evals" / "transfer-scenarios"
FAT32_MAX_FILE_BYTES = 4 * 1024**3 - 1


def safe_name(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", text).strip("._-")


def table(manifest: str, heading: str) -> list[list[str]]:
    section = manifest.split(f"\n## {heading}\n", 1)[1].split("\n## ", 1)[0]
    rows = [[c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]] for line in section.splitlines() if line.startswith("| ")]
    return rows[1:]  # without the header; the separator row starts with "|---"


def plain(cell: str) -> str:
    return cell.replace("`", "").replace(" (benchmark only)", "").strip()


def build(name: str, out: Path, variant: str | None = None, fetched: bool = False) -> tuple[Path, Path]:
    folder = SCENARIOS / name
    project, bundle = Path(out) / "project", Path(out) / "bundle"
    shutil.copytree(folder / "project", project, dirs_exist_ok=True)
    if not fetched:
        return project, bundle
    answers = json.loads((folder / f"transfer{'-' + variant if variant else ''}.json").read_text(encoding="utf-8"))
    manifest = (project / "docs" / "airgap" / "transfer-manifest.md").read_text(encoding="utf-8")
    bundle.mkdir(parents=True, exist_ok=True)
    items = []

    def write(path: str, data: bytes) -> int:
        target = bundle / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return len(data)

    for component, _, ref, *_ in table(manifest, "1. Container images"):
        c, r = plain(component), plain(ref)
        path = f"images/{safe_name(c)}/{safe_name(r)}.tar"
        size = write(path, f"fake image archive {r}\n".encode())
        write(path[:-4] + ".digest", ("sha256:" + hashlib.sha256(r.encode()).hexdigest() + "\n").encode())
        items.append(("image", c, f"`{r}`", path, size, "fetched"))
    for model, *_ in table(manifest, "2. Model artifacts"):
        source = answers["models"][model]
        path = f"models/{safe_name(model)}"
        size = write(f"{path}/model.safetensors", f"fake weights {model}\n".encode())
        size += write(f"{path}/config.json", b"{}\n")
        size += write(f"{path}/tokenizer.json", b"{}\n")
        size += write(f"{path}/LICENSE", f"License of {model} (fixture)\n".encode())
        if variant == "fat32":
            with (bundle / path / "model.safetensors").open("r+b") as handle:  # sparse: takes no room
                handle.truncate(FAT32_MAX_FILE_BYTES + 1)
            size = FAT32_MAX_FILE_BYTES + 1 + 3
        items.append(("model", "", f"`{source['repo']}` at `{source['revision']}`", path, size, "fetched"))
    manual = []
    for component, _, file, _, url, sums in table(manifest, "3. Packages and binaries"):
        if component.startswith("custom: "):
            manual.append((component.removeprefix("custom: "), "added"))
            continue
        c, f = plain(component), plain(file)
        data = f"fake package {f}\n".encode()
        path = f"packages/{safe_name(c)}/{f}"
        size = write(path, data)
        if sums.startswith("https://"):
            name = safe_name(sums.rsplit("/", 1)[-1])
            # The hash the publisher's file name promises: an md5sum list holds md5 hashes.
            digest = hashlib.md5 if "md5" in name.lower() else hashlib.sha512 if "512" in name else hashlib.sha256
            write(f"packages/{safe_name(c)}/checksums/{name}", f"{digest(data).hexdigest()}  {f}\n".encode())
        items.append(("package", c, url, path, size, "fetched"))
    for component, text in table(manifest, "5. Runtime downloads to stage in advance"):
        manual.append((f"{plain(component)}: runtime download: {text[:60].rstrip()}", "not needed"))
    for component, repo, skill in table(manifest, "6. Per-tool skills"):
        manual.append((f"{plain(component)}: per-tool skill {plain(skill)} from {plain(repo)}", "not needed"))
    for item, status in manual:
        path = f"manual/{safe_name(item)[:60]}"
        if status == "added":
            size = write(f"{path}/README.txt", f"Files the user added for: {item}\n".encode())
            items.append(("manual", "", item, path, size, "added"))
        else:
            items.append(("manual", "", item, "", 0, "not needed: the fixture's user says the inside already has it"))

    header = re.search(r"^# Transfer manifest: (.*)$", manifest, re.M).group(1)
    blueprint = (project / "docs" / "airgap" / "blueprint.md").read_text(encoding="utf-8")
    answer = dict(re.findall(r"^\| `([a-z_.]+)` \| ([^|]+) \|", blueprint, re.M))
    platform = re.search(r"^- Platform: (.*)$", manifest, re.M).group(1)
    hardware = re.search(r"^- Hardware: (.*)$", manifest, re.M).group(1)
    lines = [
        f"# Transfer plan: {header}", "",
        f"- Manifest: docs/airgap/transfer-manifest.md, generated {re.search(r'^- Generated: (.*)$', manifest, re.M).group(1)}",
        "- Blueprint: docs/airgap/blueprint.md",
        f"- Channel: {answer['transfer.channel'].strip()} · Inside: {answer['inside.operator'].strip()} · Platform: {platform} · Hardware: {hardware}",
        f"- Bundle: {bundle.resolve()}",
        "- Approved: 2026-11-24, \"yes, fetch everything\" (fixture)", "",
        "## Answers", "", "| ID | Answer |", "|---|---|",
    ]
    for key, value in answers.items():
        shown = str(bundle.resolve()) if key == "bundle.path" else (value if isinstance(value, str) else json.dumps(value))
        lines.append(f"| `{key}` | {shown} |")
    lines += ["", "## Items", "", "| # | Kind | Component | Source | Bundle path | Size | Status |", "|---|---|---|---|---|---|---|"]
    for number, (kind, component, source, path, size, status) in enumerate(items, start=1):
        lines.append(f"| {number} | {kind} | {f'`{component}`' if component else ''} | {source} | {f'`{path}`' if path else ''} | {size or ''} | {status} |")
    lines += ["", "## Volumes", "", "Not packed yet.", ""]
    (project / "docs" / "airgap" / "transfer-plan.md").write_text("\n".join(lines), encoding="utf-8")
    return project, bundle


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scenario", required=True, choices=sorted(p.name for p in SCENARIOS.iterdir() if p.is_dir()))
    parser.add_argument("--out", required=True)
    parser.add_argument("--variant")
    parser.add_argument("--fetched", action="store_true")
    args = parser.parse_args(argv)
    project, bundle = build(args.scenario, Path(args.out), args.variant, args.fetched)
    print(f"project: {project}")
    if args.fetched:
        print(f"bundle: {bundle}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
