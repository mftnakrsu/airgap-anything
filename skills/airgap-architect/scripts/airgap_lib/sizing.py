"""Organization answers to hardware numbers. Memory only; never throughput."""
from __future__ import annotations

import math
from collections.abc import Callable

from .constants import GENERATIVE_ROLES, INTERACTIVE_USAGE
from .rules import Rules

# Answers size.py checks. workload.context_tokens and hardware.power_budget_kw are
# optional; hardware.ram_gb is needed only when there is no GPU.
SIZING_ANSWERS = (
    "org.users_total",
    "org.downtime_tolerance",
    "workload.usage",
    "workload.models",
    "workload.context_tokens",
    "hardware.gpus",
    "hardware.ram_gb",
    "hardware.power_budget_kw",
)
BYTES_PER_GB = 1e9
# The group of a model sized without a usage mix: every request, the model's own context.
IMPLICIT_GROUP = {"usage": None, "peak": 1.0, "context": None}


class SizingInputError(Exception):
    """An answer is unusable for sizing; `problems` lists 'question.id: reason'."""

    def __init__(self, problems: list[str]):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


def _ceil(value: float) -> int:
    # Rounding first keeps 9.000000000000002 from becoming 10.
    return math.ceil(round(value, 9))


def _peak_values(
    users: int, usage: dict, rules: Rules, sink: list[dict] | None = None
) -> dict[str, tuple[float, float]]:
    """Unrounded (low, high) requests in flight of each interactive group in use."""
    values: dict[str, tuple[float, float]] = {}
    for usage_type in INTERACTIVE_USAGE:
        share = usage.get(usage_type, 0)
        if share <= 0:
            continue
        active = rules.use(f"sizing.{usage_type}.active", sink)
        values[usage_type] = (
            users * share * active * rules.use(f"sizing.{usage_type}.duty_low", sink),
            users * share * active * rules.use(f"sizing.{usage_type}.duty_high", sink),
        )
    return values


def interactive_concurrency(
    users: int, usage: dict, rules: Rules, sink: list[dict] | None = None
) -> dict:
    """Peak requests in flight as a low-high range. Batch is excluded."""
    values = _peak_values(users, usage, rules, sink)
    low = sum(pair[0] for pair in values.values())
    high = sum(pair[1] for pair in values.values())
    by_usage = {
        usage_type: {"low": round(pair[0], 3), "high": round(pair[1], 3)}
        for usage_type, pair in values.items()
    }
    return {"low": max(1, _ceil(low)), "high": max(1, _ceil(high)), "by_usage": by_usage}


def user_groups(users: int, usage: dict, contexts: dict | None, rules: Rules) -> list[dict]:
    """Interactive groups with their unrounded peak in-flight value and their own context.

    Groups without load are left out. With no interactive group (batch only), one
    implicit group stands for every request.
    """
    peaks = {
        usage_type: pair[1] for usage_type, pair in _peak_values(users, usage, rules).items()
    }
    if sum(peaks.values()) <= 0:
        return [dict(IMPLICIT_GROUP)]
    contexts = contexts or {}
    return [
        {"usage": usage_type, "peak": peak, "context": contexts.get(usage_type)}
        for usage_type, peak in peaks.items()
    ]


def _apportion(total: int, peaks: list[float]) -> list[int]:
    """Split `total` whole requests across groups in proportion to `peaks`.

    Largest-remainder method: floor each quota, then give the remaining units to
    the largest fractional parts (ties go to the earlier group). Sums to `total`.
    """
    peak_sum = sum(peaks)
    quotas = [round(total * peak / peak_sum, 9) for peak in peaks]
    shares = [math.floor(quota) for quota in quotas]
    # Rounded fractions make exact ties real ties; the earlier group wins them.
    order = sorted(
        range(len(peaks)), key=lambda index: (round(shares[index] - quotas[index], 9), index)
    )
    for index in order[: total - sum(shares)]:
        shares[index] += 1
    return shares


def _place(runs: list[list[int]], tokens: int, count: int, capacity: int) -> None:
    """First-fit `count` requests of `tokens` into `runs` of identical replicas.

    A run is [replicas, free_tokens]. Runs keep the order in which the replicas
    were opened; a new replica opens with `capacity` free tokens. The result equals
    placing the requests one by one into the first replica that holds them.
    """
    remaining = count
    index = 0
    while remaining > 0 and index < len(runs):
        replicas, free = runs[index]
        per_replica = free // tokens
        if per_replica == 0:
            index += 1
            continue
        if remaining >= replicas * per_replica:
            runs[index][1] = free - per_replica * tokens
            remaining -= replicas * per_replica
            index += 1
            continue
        full, rest = divmod(remaining, per_replica)
        pieces = [[full, free - per_replica * tokens]] if full else []
        if rest:
            pieces.append([1, free - rest * tokens])
        left = replicas - full - (1 if rest else 0)
        if left:
            pieces.append([left, free])
        runs[index : index + 1] = pieces
        return
    if remaining > 0:
        per_replica = capacity // tokens
        full, rest = divmod(remaining, per_replica)
        if full:
            runs.append([full, capacity - per_replica * tokens])
        if rest:
            runs.append([1, capacity - rest * tokens])


def replicas_needed(cached_tokens: int, requests: list[tuple[int, int]]) -> int:
    """Replicas that first-fit decreasing needs for `requests` of (tokens, count).

    A request's KV cache lives in one replica, so each replica holds whole requests
    and `cached_tokens` is the capacity of one replica. Every request must fit an
    empty replica.
    """
    runs: list[list[int]] = []
    for tokens, count in sorted(requests, key=lambda item: -item[0]):
        if count > 0:
            _place(runs, tokens, count, cached_tokens)
    return sum(run[0] for run in runs)


def model_weights_gb(model: dict, rules: Rules, sink: list[dict] | None = None) -> float:
    if model.get("weights_gb") is not None:
        return float(model["weights_gb"])
    if model.get("size_class") is not None:
        params_b = rules.use(f"sizing.size_class.{model['size_class']}", sink)
        precision = model.get("precision") or rules.use("sizing.default_precision", sink)
    else:
        params_b = model["params_b"]
        precision = model["precision"]
    return float(params_b * rules.use(f"sizing.bytes_per_param.{precision}", sink))


def _given_or_known(entry: dict, known: dict, key: str):
    """The answer's value, or the gpus.toml value when the answer omits it or gives null."""
    value = entry.get(key)
    return known.get(key) if value is None else value


def pick_primary_gpu(
    entries: list[dict], gpu_lookup: Callable[[str], dict | None]
) -> dict | None:
    """The GPU type sizing uses: the largest VRAM, then the larger count."""
    problems: list[str] = []
    candidates: list[dict] = []
    for index, entry in enumerate(entries):
        known = gpu_lookup(entry["model"]) or {}
        vram_gb = _given_or_known(entry, known, "vram_gb")
        if vram_gb is None:
            problems.append(
                f"hardware.gpus: item {index}: '{entry['model']}' is not in gpus.toml; supply vram_gb"
            )
            continue
        candidates.append(
            {
                "model": entry["model"],
                "vram_gb": vram_gb,
                "tdp_w": _given_or_known(entry, known, "tdp_w"),
                "count": entry["count"],
            }
        )
    if problems:
        raise SizingInputError(problems)
    if not candidates:
        return None
    return max(candidates, key=lambda gpu: (gpu["vram_gb"], gpu["count"]))


def size_model(
    model: dict,
    concurrency_high: int,
    gpu: dict | None,
    min_replicas: int,
    rules: Rules,
    sink: list[dict] | None = None,
    *,
    groups: list[dict] | None = None,
) -> dict:
    """Size one model. `groups` is the output of `user_groups`; the default is one implicit group."""
    weights = model_weights_gb(model, rules, sink)
    required = weights * (1 + rules.use("sizing.overhead", sink))
    result = {
        "name": model.get("name", ""),
        "role": model["role"],
        "weights_gb": round(weights, 3),
        "required_gb": round(required, 3),
        "gpus_per_replica": None,
        "usable_gb": None,
        "kv_headroom_gb": None,
        "kv": {"status": "not_applicable"},
        "replicas": max(1, min_replicas),
        "gpus": None,
        "notes": [],
    }
    if gpu is None:
        result.update(gpus_per_replica=0, gpus=0)
        return result

    utilization = rules.use("sizing.gpu_memory_utilization", sink)

    def usable(group: int) -> float:
        return group * gpu["vram_gb"] * utilization

    fitting = [
        group
        for group in sorted(rules.use("sizing.gpu_group_sizes", sink))
        if usable(group) >= required
    ]
    if not fitting:
        result["notes"].append("the weights do not fit the largest allowed GPU group")
        return result

    group = fitting[0]
    arch = model.get("arch")
    if model["role"] in GENERATIVE_ROLES and arch is None:
        result["kv"] = {"status": "unknown"}
        result["notes"].append("KV-cache capacity is unknown; measure it with a benchmark")
    elif model["role"] in GENERATIVE_ROLES:
        dtype = arch.get("kv_dtype") or rules.use("sizing.default_kv_dtype", sink)
        bytes_per_token = (
            2
            * arch["layers"]
            * arch["kv_heads"]
            * arch["head_dim"]
            * rules.use(f"sizing.bytes_per_param.{dtype}", sink)
        )
        fallback_context = model.get("context_tokens") or rules.use(
            "sizing.default_context_tokens", sink
        )
        output_tokens = rules.use("sizing.default_output_tokens", sink)
        groups = groups or [IMPLICIT_GROUP]
        contexts = [item["context"] or fallback_context for item in groups]
        tokens_each = [context + output_tokens for context in contexts]
        in_flight = _apportion(concurrency_high, [item["peak"] for item in groups])
        requests = list(zip(tokens_each, in_flight))
        longest = max(tokens_each)

        def cached(candidate: int) -> int:
            return int((usable(candidate) - required) * BYTES_PER_GB // bytes_per_token)

        cached_tokens = 0
        for candidate in fitting:
            group = candidate
            cached_tokens = cached(candidate)
            if cached_tokens >= longest:
                break
        demand_tokens = sum(tokens * count for tokens, count in requests)
        mean_tokens = demand_tokens / concurrency_high
        fits_longest = cached_tokens >= longest
        named = [
            (item["usage"], context, count)
            for item, context, count in zip(groups, contexts, in_flight)
            if item["usage"] is not None
        ]
        result["kv"] = {
            "status": "computed" if fits_longest else "insufficient",
            "bytes_per_token": bytes_per_token,
            "cached_tokens": cached_tokens,
            "tokens_per_request": round(mean_tokens),
            "sequences": round(cached_tokens / mean_tokens, 2),
            "demand_tokens": demand_tokens,
            "demand_gb": round(demand_tokens * bytes_per_token / BYTES_PER_GB, 1),
            "context_by_usage": {name: context for name, context, _ in named},
            "in_flight_by_usage": {name: count for name, _, count in named},
        }
        if fits_longest:
            result["replicas"] = max(result["replicas"], replicas_needed(cached_tokens, requests))
            chosen_total = result["replicas"] * group
            alternatives = []
            for larger in fitting:
                larger_cached = cached(larger)
                if larger > group and larger_cached >= longest:
                    count = max(min_replicas, replicas_needed(larger_cached, requests))
                    alternatives.append((count * larger, larger))
            if alternatives and min(alternatives)[0] < chosen_total:
                total, larger = min(alternatives)
                result["notes"].append(
                    f"with {larger}-GPU replicas the memory model needs {total} GPUs instead "
                    f"of {chosen_total}; tensor parallelism adds synchronization overhead, "
                    "so benchmark throughput before choosing it"
                )
        else:
            result["notes"].append(
                "the KV cache cannot hold one request of the longest context "
                "on the largest allowed GPU group"
            )
    result.update(
        gpus_per_replica=group,
        usable_gb=round(usable(group), 3),
        kv_headroom_gb=round(usable(group) - required, 3),
        gpus=result["replicas"] * group,
    )
    return result


def compute_sizing(
    answers: dict, rules: Rules, gpu_lookup: Callable[[str], dict | None]
) -> tuple[dict, list[dict]]:
    """Return (sizing, assumptions). `answers` must be resolved and valid."""
    sink: list[dict] = []
    concurrency = interactive_concurrency(
        answers["org.users_total"], answers["workload.usage"], rules, sink
    )
    min_replicas = 1
    if answers.get("org.downtime_tolerance") == "none":
        min_replicas = rules.use("sizing.ha_min_replicas", sink)
    entries = answers["hardware.gpus"]
    gpu = pick_primary_gpu(entries, gpu_lookup)
    warnings: list[str] = []
    if len(entries) > 1:
        warnings.append(
            "several GPU types were given; only the largest-VRAM type is used for sizing"
        )
    groups = user_groups(
        answers["org.users_total"],
        answers["workload.usage"],
        answers.get("workload.context_tokens"),
        rules,
    )
    models = [
        size_model(model, concurrency["high"], gpu, min_replicas, rules, sink, groups=groups)
        for model in answers["workload.models"]
    ]
    sizing = {
        "concurrency": concurrency,
        "gpu": gpu,
        "models": models,
        "cpu_only": gpu is None,
        "benchmark_required": True,
    }
    if gpu is None:
        ram_gb = answers.get("hardware.ram_gb")
        if ram_gb is None:
            raise SizingInputError(
                ["hardware.ram_gb: missing (required when hardware.gpus is empty)"]
            )
        ram_required = round(sum(model["required_gb"] for model in models), 3)
        warnings.append(
            "CPU inference suits only a few concurrent users; benchmark before relying on it"
        )
        sizing.update(
            total_gpus=0,
            servers=1,
            power_kw=None,
            power_within_budget=None,
            ram_required_gb=ram_required,
            fits=ram_required <= ram_gb,
        )
    else:
        complete = all(
            model["gpus"] is not None and model["kv"]["status"] != "insufficient"
            for model in models
        )
        total_gpus = sum(model["gpus"] or 0 for model in models)
        servers = max(1, math.ceil(total_gpus / rules.use("sizing.gpus_per_server", sink)))
        power_kw = None
        if gpu["tdp_w"] is not None:
            factor = rules.use("sizing.power_system_factor", sink)
            power_kw = round(total_gpus * gpu["tdp_w"] * factor / 1000, 1)
        budget = answers.get("hardware.power_budget_kw")
        within_budget = None if power_kw is None or budget is None else power_kw <= budget
        if within_budget is False:
            warnings.append("the power estimate exceeds hardware.power_budget_kw")
        sizing.update(
            total_gpus=total_gpus,
            servers=servers,
            power_kw=power_kw,
            power_within_budget=within_budget,
            fits=complete and total_gpus <= gpu["count"],
        )
    sizing["warnings"] = warnings
    return sizing, sink
