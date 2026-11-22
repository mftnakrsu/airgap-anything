#!/usr/bin/env python3
"""Compute the base tier and per-layer floors and write them to blueprint.json."""
from airgap_lib import cli
from airgap_lib.answers import resolve_answers
from airgap_lib.tiering import TIER_ANSWERS, compute_tier


def main(argv=None) -> int:
    args = cli.make_parser(__doc__).parse_args(argv)
    catalog = cli.open_catalog(args.catalog)
    blueprint = cli.open_blueprint(args.blueprint)
    resolved, _, problems = resolve_answers(
        cli.answers_of(blueprint), catalog.rules, TIER_ANSWERS
    )
    cli.fail_on_answer_problems(problems)
    try:
        tier = compute_tier(resolved, catalog.rules)
    except (ValueError, OverflowError) as error:
        cli.fail_on_unusable_value(error)
    blueprint["tier"] = tier
    cli.save_or_fail(args.blueprint, blueprint)
    print(f"Base tier: {tier['base']}")
    for layer, floor in tier["floors"].items():
        print(f"  {layer}: {floor}")
    for reason in tier["reasons"]:
        print(f"- {reason}")
    return cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
