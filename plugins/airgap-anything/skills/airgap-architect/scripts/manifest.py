"""Generate transfer-manifest.md from the decisions in blueprint.json."""
from datetime import date
from pathlib import Path

from airgap_lib import cli
from airgap_lib.transfer import MANIFEST_FILENAME, UnknownComponentError, render_manifest


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__)
    parser.add_argument(
        "--out", help=f"output file (default: {MANIFEST_FILENAME} next to blueprint.json)"
    )
    parser.add_argument(
        "--date",
        type=cli.iso_date,
        default=date.today().isoformat(),
        help="generation date as YYYY-MM-DD (default: today)",
    )
    args = parser.parse_args(argv)
    catalog = cli.open_catalog(args.catalog)
    blueprint = cli.open_blueprint(args.blueprint)
    cli.answers_of(blueprint)  # exit 2 unless 'answers' is an object, as in tier.py
    try:
        text = render_manifest(blueprint, catalog, args.date)
    except UnknownComponentError as error:
        cli.fail(cli.EXIT_INPUT, [str(error)])
    except (ValueError, OverflowError) as error:
        cli.fail_on_unusable_value(error)
    out = Path(args.out) if args.out else Path(args.blueprint).parent / MANIFEST_FILENAME
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    except OSError as error:
        cli.fail_on_write_error(out, error)
    print(f"Wrote {out}")
    return cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
