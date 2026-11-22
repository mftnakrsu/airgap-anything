"""Check a blueprint against the catalog, or check the catalog alone."""
from datetime import date
from pathlib import Path

from airgap_lib import cli
from airgap_lib.answers import validate_defaults
from airgap_lib.blueprint import BlueprintError
from airgap_lib.catalog import load_catalog, validate_catalog
from airgap_lib.checks import lint_project
from airgap_lib.findings import format_json, format_text, has_errors


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__, blueprint_required=False)
    parser.add_argument(
        "--catalog-only", action="store_true", help="validate the catalog and stop"
    )
    parser.add_argument(
        "--project-root",
        default=".",
        help="directory that blueprint_path and AGENTS.md are relative to (default: .)",
    )
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument(
        "--today",
        type=cli.iso_date,
        default=date.today().isoformat(),
        help="date used for freshness checks, YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args(argv)
    today = date.fromisoformat(args.today)
    if args.catalog_only:
        try:
            catalog, findings = load_catalog(Path(args.catalog))
        except (OSError, ValueError) as error:
            cli.fail(cli.EXIT_ENVIRONMENT, [f"cannot read the catalog: {error}"])
        findings = findings + validate_catalog(catalog, today) + validate_defaults(catalog.rules)
    else:
        if not args.blueprint:
            parser.error("--blueprint is required unless --catalog-only is given")
        catalog = cli.open_catalog(args.catalog)
        try:
            findings = lint_project(
                Path(args.blueprint), catalog, Path(args.project_root), today
            )
        except BlueprintError as error:
            cli.fail(cli.EXIT_INPUT, [str(error)])
        except (ValueError, OverflowError) as error:
            cli.fail_on_unusable_value(error)
    print(format_json(findings) if args.format == "json" else format_text(findings))
    return cli.EXIT_LINT_ERRORS if has_errors(findings) else cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
