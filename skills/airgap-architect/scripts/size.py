#!/usr/bin/env python3
"""Size GPUs, servers and power and write sizing and assumptions to blueprint.json."""
from airgap_lib import cli
from airgap_lib.answers import resolve_answers
from airgap_lib.sizing import SIZING_ANSWERS, SizingInputError, compute_sizing


def main(argv=None) -> int:
    args = cli.make_parser(__doc__).parse_args(argv)
    catalog = cli.open_catalog(args.catalog)
    blueprint = cli.open_blueprint(args.blueprint)
    resolved, defaults_used, problems = resolve_answers(
        cli.answers_of(blueprint), catalog.rules, SIZING_ANSWERS
    )
    cli.fail_on_answer_problems(problems)
    try:
        sizing, constants_used = compute_sizing(resolved, catalog.rules, catalog.gpu)
    except SizingInputError as error:
        cli.fail_on_answer_problems(error.problems)
    except (ValueError, OverflowError) as error:
        cli.fail_on_unusable_value(error)
    blueprint["sizing"] = sizing
    blueprint["assumptions"] = defaults_used + constants_used
    cli.save_or_fail(args.blueprint, blueprint)
    concurrency = sizing["concurrency"]
    print(f"Peak concurrency: {concurrency['low']}-{concurrency['high']} requests in flight")
    for model in sizing["models"]:
        print(
            f"  {model['name'] or model['role']}: {model['replicas']} replica(s) x "
            f"{model['gpus_per_replica']} GPU(s), KV cache {model['kv']['status']}"
        )
        kv = model["kv"]
        if kv["status"] in ("computed", "insufficient"):
            print(
                f"    KV cache: {kv['demand_gb']} GB needed at peak; "
                f"{model['kv_headroom_gb']} GB per replica holds about {kv['sequences']} "
                f"requests of {kv['tokens_per_request']} tokens"
            )
            contexts = kv["context_by_usage"]
            if len(set(contexts.values())) >= 2:
                print(
                    "    context per group: "
                    + ", ".join(f"{name} {tokens}" for name, tokens in contexts.items())
                )
        for note in model["notes"]:
            print(f"    note: {note}")
    power = "unknown" if sizing["power_kw"] is None else f"{sizing['power_kw']} kW"
    print(
        f"Total: {sizing['total_gpus']} GPU(s), {sizing['servers']} server(s), "
        f"power {power}, fits: {sizing['fits']}"
    )
    for warning in sizing["warnings"]:
        print(f"! {warning}")
    print("Throughput is not predicted: benchmark before production.")
    return cli.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
