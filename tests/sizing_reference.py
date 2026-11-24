"""The procedure of references/sizing.md, written out once in Python for the repository's checks.

The skill does not use this file: an agent follows the markdown. The tests use it to check that
the worked examples in sizing.md and the expected numbers of the eval scenarios follow from the
constants in sizing.md, so that a changed constant cannot leave an example behind.
"""
from __future__ import annotations

import math

ACTIVE = {"chat": 0.20, "rag": 0.20, "code_assistant": 0.30}
IN_FLIGHT = {"chat": (0.25, 0.50), "rag": (0.25, 0.50), "code_assistant": (0.70, 1.00)}
BYTES_PER_PARAM = {"fp32": 4, "bf16": 2, "fp16": 2, "fp8": 1, "int8": 1, "int4": 0.5}
SIZE_CLASS = {"S": 8, "M": 32, "L": 120, "XL": 671}
OVERHEAD = 0.10
UTILIZATION = 0.90
GROUPS = (1, 2, 4, 8)
DEFAULT_CONTEXT = 8192
OUTPUT_TOKENS = 1024
HA_REPLICAS = 2
GPUS_PER_SERVER = 8
POWER_FACTOR = 1.8


def ceil(value: float) -> int:
    return math.ceil(round(value, 9))


def concurrency(users: int, usage: dict) -> tuple[int, int, dict]:
    groups = {}
    for group, share in usage.items():
        if group in ACTIVE and share > 0:
            low, high = IN_FLIGHT[group]
            groups[group] = (users * share * ACTIVE[group] * low, users * share * ACTIVE[group] * high)
    low = max(1, ceil(sum(pair[0] for pair in groups.values())))
    high = max(1, ceil(sum(pair[1] for pair in groups.values())))
    return low, high, groups


def required_gb(model: dict) -> float:
    if model.get("weights_gb") is not None:
        weights = model["weights_gb"]
    elif model.get("size_class"):
        weights = SIZE_CLASS[model["size_class"]] * BYTES_PER_PARAM[model.get("precision") or "bf16"]
    else:
        weights = model["params_b"] * BYTES_PER_PARAM[model["precision"]]
    return round(weights * (1 + OVERHEAD), 3)


def _replicas(cached: int, requests: list[tuple[int, float]], minimum: int) -> int:
    total = sum(in_flight / (cached // tokens) for tokens, in_flight in requests)
    return max(minimum, ceil(total))


def size_model(model: dict, gpu: dict, groups: dict, contexts: dict, minimum: int) -> dict:
    required = required_gb(model)
    usable = {g: round(g * gpu["vram_gb"] * UTILIZATION, 3) for g in GROUPS}
    fitting = [g for g in GROUPS if usable[g] >= required]
    result = {"required_gb": required, "group": None, "replicas": minimum, "kv": "not_applicable", "notes": []}
    if not fitting:
        result["notes"].append("weights do not fit")
        return result
    result["group"] = fitting[0]
    arch = model.get("arch")
    if model["role"] not in ("chat", "code"):
        return result
    if arch is None:
        result["kv"] = "unknown"
        return result
    per_token = 2 * arch["layers"] * arch["kv_heads"] * arch["head_dim"] * BYTES_PER_PARAM[arch.get("kv_dtype") or "fp16"]
    fallback = model.get("context_tokens") or DEFAULT_CONTEXT
    requests = [((contexts.get(g) or fallback) + OUTPUT_TOKENS, ceil(pair[1])) for g, pair in groups.items()]
    longest = max(tokens for tokens, _ in requests)

    def cached(g: int) -> int:
        return int(round((usable[g] - required) * 10**9 / per_token, 6) // 1)

    holding = [g for g in fitting if cached(g) >= longest]
    if not holding:
        result["kv"] = "insufficient"
        return result
    group = holding[0]
    result.update(group=group, kv="computed", bytes_per_token=per_token, cached_tokens=cached(group))
    result["replicas"] = _replicas(cached(group), requests, minimum)
    result["kv_demand_gb"] = round(sum(t * n for t, n in requests) * per_token / 10**9, 1)
    chosen = result["replicas"] * group
    options = [(_replicas(cached(g), requests, minimum) * g, g) for g in holding if g > group]
    if options and min(options)[0] < chosen:
        result["notes"].append(f"with {min(options)[1]}-GPU replicas the memory model needs {min(options)[0]} GPUs instead of {chosen}")
    return result


def size(answers: dict) -> dict:
    users = answers["org.users_total"]
    low, high, groups = concurrency(users, answers.get("workload.usage", {"chat": 1.0}))
    minimum = HA_REPLICAS if answers.get("org.downtime_tolerance") == "none" else 1
    gpus = answers["hardware.gpus"]
    if not gpus:
        required = round(sum(required_gb(m) for m in answers["workload.models"]), 3)
        return {"concurrency": (low, high), "total_gpus": 0, "servers": 1, "power_kw": None,
                "ram_required_gb": required, "fits": required <= answers["hardware.ram_gb"]}
    gpu = max(gpus, key=lambda g: (g["vram_gb"], g["count"]))
    contexts = answers.get("workload.context_tokens") or {}
    models = [size_model(m, gpu, groups, contexts, minimum) for m in answers["workload.models"]]
    total = sum(m["replicas"] * m["group"] for m in models if m["group"])
    placed = all(m["group"] and m["kv"] != "insufficient" for m in models)
    power = round(total * gpu["tdp_w"] * POWER_FACTOR / 1000, 1) if gpu.get("tdp_w") else None
    return {"concurrency": (low, high), "models": models, "total_gpus": total,
            "servers": max(1, ceil(total / GPUS_PER_SERVER)), "power_kw": power,
            "fits": placed and total <= gpu["count"]}
