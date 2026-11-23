"""Plan a transfer: the item list, the tools on this machine and fetch.sh."""
from datetime import datetime, timezone
from pathlib import Path

from transfer_lib import cli
from transfer_lib.constants import EXIT_ENVIRONMENT, EXIT_INPUT, EXIT_OK, FETCH_SCRIPT, PICKLE_SUFFIXES
from transfer_lib.fetch_script import render_fetch_script
from transfer_lib.inputs import InputError, channel_of, load_inputs
from transfer_lib.items import build_items
from transfer_lib.questions import answer_problems, needed_questions
from transfer_lib.state import load_state, new_state, save_state, state_path
from transfer_lib.tools import MissingToolError, find_tools


def local_model_problems(items: list[dict]) -> list[str]:
    """A local model folder without safetensors weights stops the plan (exit 2)."""
    problems = []
    for item in items:
        if item["kind"] != "model" or item["source"].get("source") != "local" or item["allow_pickle"]:
            continue
        files = [p for p in Path(item["source"]["path"]).rglob("*") if p.is_file()]
        if not any(p.suffix == ".safetensors" for p in files):
            pickles = [p.name for p in files if p.suffix in PICKLE_SUFFIXES]
            problems.append(
                f"models: '{item['name']}': {item['source']['path']} holds no safetensors weights"
                + (f" (pickle files: {', '.join(sorted(pickles)[:3])})" if pickles else "")
                + "; set allow_pickle to true for it only if the scanning rules permit pickle files"
            )
    return problems


def known_sizes(blueprint: dict, items: list[dict]) -> list[str]:
    """Sizes known before the fetch: the weights architect sized, local model folders."""
    lines = []
    sized = (blueprint.get("sizing") or {}).get("models") or []
    for index, item in enumerate(i for i in items if i["kind"] == "model"):
        if item["source"].get("source") == "local":
            total = sum(p.stat().st_size for p in Path(item["source"]["path"]).rglob("*") if p.is_file())
            lines.append(f"  model {item['name']}: {total / 1e9:.1f} GB in {item['source']['path']}")
        elif index < len(sized) and isinstance(sized[index], dict) and sized[index].get("weights_gb"):
            lines.append(f"  model {item['name']}: about {sized[index]['weights_gb']} GB of weights (architect's sizing)")
    return lines


def main(argv=None) -> int:
    args = cli.make_parser(__doc__).parse_args(argv)
    root = Path(args.project_root)
    try:
        blueprint, manifest = load_inputs(root)
        channel = channel_of(blueprint)
        path = state_path(root)
        if not path.exists():
            save_state(path, new_state(manifest["inputs_digest"]))
            print(f"Wrote {path}")
        state = load_state(path)
    except InputError as error:
        cli.fail(EXIT_INPUT, [str(error)])
    answers = state["answers"]
    problems = answer_problems(answers, channel, manifest, root)
    if problems:
        asked = needed_questions(channel, manifest, answers)
        cli.fail(EXIT_INPUT, ["Missing or invalid answers in transfer.json:"] + [f"  {p}" for p in problems]
                 + ["Questions for this transfer: " + ", ".join(asked)])
    items = build_items(manifest, answers)
    problems = local_model_problems(items)
    if problems:
        cli.fail(EXIT_INPUT, problems)
    try:
        tools = find_tools(items)
    except MissingToolError as error:
        cli.fail(EXIT_ENVIRONMENT, [f"{tool} is not on PATH; it is needed for: {', '.join(needs)}"
                                    for tool, needs in error.missing.items()])
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    state["manifest_digest"] = manifest["inputs_digest"]
    state["plan"] = {"items": items, "tools": tools, "platform": manifest["platform"],
                     "channel": channel, "planned": generated}
    bundle = Path(answers["bundle.path"])
    script = bundle / FETCH_SCRIPT
    try:
        bundle.mkdir(parents=True, exist_ok=True)
        script.write_text(render_fetch_script(state["plan"], manifest["platform"], generated), encoding="utf-8")
        save_state(path, state)
    except OSError as error:
        cli.fail(EXIT_INPUT, [f"cannot write {script}: {error.strerror or type(error).__name__}"])
    counts = {}
    for item in items:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    print(f"Plan: {len(items)} items (" + ", ".join(f"{n} {k}" for k, n in counts.items()) + ")")
    print("Tools: " + (", ".join(f"{job} with {tool}" for job, tool in tools.items()) or "none needed"))
    print(f"Bundle folder: {bundle}")
    sizes = known_sizes(blueprint, items)
    print("Known sizes:" if sizes else "Known sizes: none before the fetch; images and packages are sized when fetched")
    for line in sizes:
        print(line)
    print(f"Wrote {script}. Show this plan to the user; run sh {script} only after they approve it.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
