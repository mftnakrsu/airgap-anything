"""Pack a fetched bundle: checksums, volume plan, inventory, inside scripts and runbook.

With --write-volume N --to FOLDER, copy volume N onto a mounted medium and read it back.
"""
from datetime import datetime, timezone
from pathlib import Path

from transfer_lib import cli
from transfer_lib.bundle import PackError, build_bundle, stray_files
from transfer_lib.constants import BUNDLE_JSON, EXIT_FINDINGS, EXIT_INPUT, EXIT_OK
from transfer_lib.inputs import InputError, channel_of, language_of, load_inputs, operator_of, read_json
from transfer_lib.pack_files import MediumError, WriteError, write_generated, write_volume
from transfer_lib.questions import answer_problems
from transfer_lib.state import load_state, save_state, state_path


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__)
    parser.add_argument("--write-volume", type=int, metavar="N", help="copy volume N to --to")
    parser.add_argument("--to", metavar="FOLDER", help="the folder of the mounted medium")
    args = parser.parse_args(argv)
    if (args.write_volume is None) != (args.to is None):
        parser.error("--write-volume and --to go together")
    root = Path(args.project_root)
    try:
        blueprint, manifest = load_inputs(root)
        path = state_path(root)
        state = load_state(path)
        meta = {"project": blueprint.get("project", ""), "channel": channel_of(blueprint),
                "operator": operator_of(blueprint), "language": language_of(blueprint)}
    except InputError as error:
        cli.fail(EXIT_INPUT, [str(error)])
    if not state["plan"].get("items"):
        cli.fail(EXIT_INPUT, ["transfer.json has no plan: run plan.py first"])
    if state["manifest_digest"] != manifest["inputs_digest"]:
        cli.fail(EXIT_INPUT, ["transfer-manifest.json changed after the plan was made: run plan.py again"])
    # transfer.json can be edited after plan.py: an answer that no longer fits must never
    # turn into "no limit" (one unlimited volume, no splitting) without a word.
    problems = answer_problems(state["answers"], meta["channel"], manifest, root)
    if problems:
        cli.fail(EXIT_INPUT, ["Missing or invalid answers in transfer.json:"] + [f"  {p}" for p in problems]
                 + ["Fix them, run plan.py again, then pack.py."])
    bundle = Path(state["answers"]["bundle.path"])
    if args.write_volume is not None:
        try:
            bundle_data = read_json(bundle / BUNDLE_JSON)
        except InputError as error:
            cli.fail(EXIT_INPUT, [str(error), "Run pack.py without --write-volume first."])
        if bundle_data.get("manifest_digest") != manifest["inputs_digest"]:
            cli.fail(EXIT_INPUT, ["bundle.json was packed from another manifest: run pack.py again"])
        generated = state["pack"].get("generated") or []
        try:
            bad = write_volume(bundle, bundle_data, args.write_volume, Path(args.to), generated)
        except MediumError as error:
            cli.fail(EXIT_FINDINGS, [f"cannot write volume {args.write_volume}: {error}",
                                     "The medium may be faulty. Write this volume again, or use another medium."])
        except (WriteError, OSError) as error:
            cli.fail(EXIT_INPUT, [f"cannot write volume {args.write_volume}: {error}"])
        if bad:
            cli.fail(EXIT_FINDINGS, [f"read-back mismatch on {Path(args.to)}: " + ", ".join(bad),
                                     "The medium may be faulty. Write this volume again, or use another medium."])
        total = len(bundle_data["volumes"])
        print(f"Wrote volume {args.write_volume} of {total} to {args.to}; every file read back matches.")
        return EXIT_OK
    try:
        bundle_data = build_bundle(bundle, state, manifest, meta)
    except PackError as error:
        cli.fail(EXIT_INPUT, ["The bundle cannot be packed yet:"] + [f"  {p}" for p in error.problems])
    except OSError as error:
        cli.fail(EXIT_INPUT, [f"cannot read the bundle folder {bundle}: {error}"])
    try:
        generated = write_generated(bundle, bundle_data, manifest)
    except OSError as error:
        cli.fail(EXIT_INPUT, [f"cannot write into the bundle folder {bundle}: {error}"])
    total = sum(volume["bytes"] for volume in bundle_data["volumes"])
    state["pack"] = {
        "volumes": [{"number": v["number"], "bytes": v["bytes"], "files": len(v["units"])} for v in bundle_data["volumes"]],
        "total_bytes": total,
        "generated": generated,
        "packed": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    save_state(path, state)
    print(f"Packed {bundle}: {total:,} bytes on {len(bundle_data['volumes'])} volume(s).")
    for volume in bundle_data["volumes"]:
        print(f"  volume {volume['number']}: {volume['bytes']:,} bytes, {len(volume['units'])} file(s)")
    strays = stray_files(bundle, bundle_data, set(generated))
    if strays:
        print("Not carried, because no item claims them: " + ", ".join(strays))
    if meta["language"] != "en":
        print(f"The runbook files are in English. Translate their prose into '{meta['language']}' and keep "
              "every command line, file name and key exactly as written.")
    print("Next: check.py; then pack.py --write-volume N --to FOLDER for each volume.")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
