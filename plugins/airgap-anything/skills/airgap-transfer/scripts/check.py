"""Check a packed bundle: errors B1-B8, warnings BW1-BW2."""
import sys
from pathlib import Path

from transfer_lib import cli
from transfer_lib.checks import bundle_problems, check_bundle
from transfer_lib.constants import BUNDLE_JSON, EXIT_FINDINGS, EXIT_INPUT, EXIT_OK
from transfer_lib.findings import format_json, format_text, has_errors
from transfer_lib.inputs import InputError, load_inputs, read_json
from transfer_lib.state import load_state, state_path

MAX_SHOWN = 10  # problems listed when bundle.json does not fit


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__)
    parser.add_argument("--deep", action="store_true", help="recompute the SHA-256 of every file")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    root = Path(args.project_root)
    try:
        _, manifest = load_inputs(root)
        path = state_path(root)
        state = load_state(path)
        if not state["plan"].get("items"):
            raise InputError("transfer.json has no plan: run plan.py first")
        given = state["answers"].get("bundle.path")
        if not isinstance(given, str) or not given.strip():
            raise InputError(f"{path}: the answer 'bundle.path' is missing or is not a path: set it and run plan.py again")
        bundle = Path(given)
        bundle_data = read_json(bundle / BUNDLE_JSON)
    except InputError as error:
        cli.fail(EXIT_INPUT, [str(error)])
    problems = bundle_problems(bundle_data)
    if problems:
        lines = [f"  {problem}" for problem in problems[:MAX_SHOWN]]
        if len(problems) > MAX_SHOWN:
            lines.append(f"  ... and {len(problems) - MAX_SHOWN} more")
        cli.fail(EXIT_INPUT, [f"{bundle / BUNDLE_JSON}: not a complete bundle.json:", *lines, "Run pack.py again."])
    findings = check_bundle(bundle, state, bundle_data, manifest, deep=args.deep, project_files=[path])
    print(format_json(findings) if args.format == "json" else format_text(findings))
    return EXIT_FINDINGS if has_errors(findings) else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
