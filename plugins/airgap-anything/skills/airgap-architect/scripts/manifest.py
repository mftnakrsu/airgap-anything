"""Generate transfer-manifest.md and transfer-manifest.json from blueprint.json."""
from datetime import date
from pathlib import Path

from airgap_lib import cli
from airgap_lib.transfer import (
    MANIFEST_FILENAME,
    MANIFEST_JSON_FILENAME,
    UnknownComponentError,
    build_manifest,
    render_json,
    render_markdown,
)


def main(argv=None) -> int:
    parser = cli.make_parser(__doc__)
    parser.add_argument(
        "--out",
        help=f"Markdown output file (default: {MANIFEST_FILENAME} next to blueprint.json); "
        f"{MANIFEST_JSON_FILENAME} is written in the same directory",
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
        data = build_manifest(blueprint, catalog, args.date)
        texts = {"md": render_markdown(data), "json": render_json(data)}
    except UnknownComponentError as error:
        cli.fail(cli.EXIT_INPUT, [str(error)])
    except (ValueError, OverflowError) as error:
        cli.fail_on_unusable_value(error)
    out = Path(args.out) if args.out else Path(args.blueprint).parent / MANIFEST_FILENAME
    outputs = ((out, texts["md"]), (out.parent / MANIFEST_JSON_FILENAME, texts["json"]))
    for path, text in outputs:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        except OSError as error:
            cli.fail_on_write_error(path, error)
    for path, _ in outputs:
        print(f"Wrote {path}")
    return cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
