import random
import unittest

from tests import CATALOG_DIR
from airgap_lib.constants import EVIDENCE_LEVELS
from airgap_lib.rules import load_rules
from airgap_lib.sizing import (
    SizingInputError,
    compute_sizing,
    interactive_concurrency,
    model_weights_gb,
    pick_primary_gpu,
    replicas_needed,
    size_model,
)


def no_gpu_table(model):
    return None


def answers(**overrides):
    base = {
        "org.users_total": 180,
        "org.downtime_tolerance": "planned_only",
        "workload.usage": {"chat": 1.0},
        "workload.models": [{"name": "m", "role": "chat", "params_b": 70, "precision": "fp8"}],
        "hardware.gpus": [{"model": "big", "count": 8, "vram_gb": 141, "tdp_w": 700}],
    }
    base.update(overrides)
    return base


class SizingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = load_rules(CATALOG_DIR / "rules.toml")

    def size(self, **overrides):
        return compute_sizing(answers(**overrides), self.rules, no_gpu_table)


class ConcurrencyTest(SizingTestCase):
    def test_spec_example_180_chat_users(self):
        result = interactive_concurrency(180, {"chat": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (9, 18))

    def test_exact_products_are_not_rounded_up_by_float_noise(self):
        result = interactive_concurrency(300, {"chat": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (15, 30))

    def test_mixed_usage_adds_up(self):
        usage = {"chat": 0.7, "code_assistant": 0.2, "rag": 0.1}
        result = interactive_concurrency(2000, usage, self.rules)
        self.assertEqual((result["low"], result["high"]), (164, 280))
        self.assertEqual(set(result["by_usage"]), {"chat", "code_assistant", "rag"})

    def test_batch_is_excluded_and_the_minimum_is_one(self):
        result = interactive_concurrency(500, {"batch": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (1, 1))
        self.assertEqual(result["by_usage"], {})

    def test_small_team_low_end_rounds_up_to_one(self):
        result = interactive_concurrency(12, {"chat": 1.0}, self.rules)
        self.assertEqual((result["low"], result["high"]), (1, 2))


class WeightsTest(SizingTestCase):
    def test_params_times_bytes(self):
        self.assertEqual(model_weights_gb({"params_b": 70, "precision": "bf16"}, self.rules), 140.0)
        self.assertEqual(model_weights_gb({"params_b": 30, "precision": "int4"}, self.rules), 15.0)

    def test_given_weight_size_wins(self):
        model = {"weights_gb": 42.5, "params_b": 70, "precision": "bf16"}
        self.assertEqual(model_weights_gb(model, self.rules), 42.5)

    def test_size_class_uses_the_default_precision_and_records_it(self):
        sink = []
        self.assertEqual(model_weights_gb({"size_class": "M"}, self.rules, sink), 64.0)
        self.assertEqual(
            [item["id"] for item in sink],
            ["sizing.size_class.M", "sizing.default_precision", "sizing.bytes_per_param.bf16"],
        )


class GpusPerReplicaTest(SizingTestCase):
    def group(self, params_b, precision, vram_gb):
        gpu = {"model": "x", "vram_gb": vram_gb, "tdp_w": None, "count": 8}
        model = {"role": "chat", "params_b": params_b, "precision": precision}
        return size_model(model, 1, gpu, 1, self.rules)["gpus_per_replica"]

    def test_spec_vectors_on_141_gb_gpus(self):
        self.assertEqual(self.group(70, "fp8", 141), 1)
        self.assertEqual(self.group(70, "bf16", 141), 2)
        self.assertEqual(self.group(235, "fp8", 141), 4)
        self.assertEqual(self.group(671, "fp8", 141), 8)

    def test_spec_vector_on_a_24_gb_gpu(self):
        self.assertEqual(self.group(30, "int4", 24), 1)

    def test_weights_that_fit_no_group(self):
        gpu = {"model": "x", "vram_gb": 24, "tdp_w": None, "count": 8}
        result = size_model({"role": "chat", "params_b": 671, "precision": "fp8"}, 1, gpu, 1, self.rules)
        self.assertIsNone(result["gpus_per_replica"])
        self.assertIsNone(result["gpus"])
        self.assertIn("do not fit", result["notes"][0])


class KvCacheTest(SizingTestCase):
    ARCH = {"layers": 80, "kv_heads": 8, "head_dim": 128, "kv_dtype": "fp16"}

    def test_unknown_without_architecture_numbers(self):
        sizing, _ = self.size()
        model = sizing["models"][0]
        self.assertEqual(model["kv"], {"status": "unknown"})
        self.assertEqual(model["replicas"], 1)
        self.assertIn("benchmark", model["notes"][0])

    USAGE = {"chat": 0.7, "code_assistant": 0.2, "rag": 0.1}

    def mixed(self, gpus=24, model_extra=None, contexts=None):
        """2,000 users, 0.7 chat / 0.2 code_assistant / 0.1 rag: peak 140 + 120 + 20 = 280."""
        model = {"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}
        model.update(model_extra or {})
        overrides = {
            "org.users_total": 2000,
            "workload.usage": self.USAGE,
            "workload.models": [model],
            "hardware.gpus": [{"model": "big", "count": gpus, "vram_gb": 141}],
        }
        if contexts is not None:
            overrides["workload.context_tokens"] = contexts
        sizing, _ = self.size(**overrides)
        return sizing, sizing["models"][0]

    def test_replicas_follow_kv_capacity(self):
        # 2,000 users, 280 requests in flight at peak, everyone at 8192 + 1024 = 9216 tokens.
        # One replica holds floor(152,282 / 9,216) = 16 whole requests: ceil(280 / 16) = 18
        # replicas. Demand is 280 x 9,216 = 2,580,480 tokens, 845.6 GB; the mean request is
        # 9,216 tokens and a replica holds 152,282 / 9,216 = 16.52 of them.
        sizing, model = self.mixed()
        self.assertEqual(model["kv"]["bytes_per_token"], 327680)
        self.assertEqual(model["kv"]["cached_tokens"], 152282)
        self.assertEqual(model["kv"]["tokens_per_request"], 9216)
        self.assertEqual(model["kv"]["sequences"], 16.52)
        self.assertEqual(model["kv"]["demand_tokens"], 2580480)
        self.assertEqual(model["kv"]["demand_gb"], 845.6)
        self.assertEqual(model["replicas"], 18)
        self.assertEqual(sizing["total_gpus"], 18)
        self.assertEqual(sizing["servers"], 3)
        self.assertTrue(sizing["fits"])

    def test_the_kv_record_has_exactly_the_documented_fields(self):
        _, model = self.mixed()
        self.assertEqual(
            set(model["kv"]),
            {
                "status",
                "bytes_per_token",
                "cached_tokens",
                "tokens_per_request",
                "sequences",
                "demand_tokens",
                "demand_gb",
                "context_by_usage",
                "in_flight_by_usage",
            },
        )
        self.assertEqual(
            model["kv"]["context_by_usage"],
            {"chat": 8192, "code_assistant": 8192, "rag": 8192},
        )
        self.assertEqual(
            model["kv"]["in_flight_by_usage"], {"chat": 140, "code_assistant": 120, "rag": 20}
        )

    def test_more_replicas_than_gpus_do_not_fit(self):
        # Weights and KV cache fit, but 18 replicas of one GPU exceed 16 GPUs.
        sizing, model = self.mixed(gpus=16)
        self.assertEqual(model["kv"]["status"], "computed")
        self.assertEqual(sizing["total_gpus"], 18)
        self.assertFalse(sizing["fits"])

    def test_context_per_group_changes_the_sizing(self):
        # Per request: chat 9,216, code_assistant 33,792, rag 17,408 tokens. In flight 140,
        # 120, 20. A replica holds 152,282 tokens. code_assistant first: 4 per replica
        # (135,168 tokens), 30 replicas with 17,114 free. rag next: it does not fit that
        # space, so 8 per new replica: 3 replicas. chat last: 1 into each of the 30
        # replicas, 1 into each of 2 rag replicas (13,018 free), 8 into the third (82,650
        # free): 40 placed; the other 100 need 7 replicas of 16. Total 30 + 3 + 7 = 40.
        # Demand 140 x 9,216 + 120 x 33,792 + 20 x 17,408 = 5,693,440 tokens, 1,865.6 GB;
        # the mean request is 5,693,440 / 280 = 20,334 tokens: 152,282 / 20,333.7 = 7.49.
        contexts = {"chat": 8192, "code_assistant": 32768, "rag": 16384}
        sizing, model = self.mixed(contexts=contexts)
        self.assertEqual(model["kv"]["context_by_usage"], contexts)
        self.assertEqual(list(model["kv"]["context_by_usage"]), ["chat", "code_assistant", "rag"])
        self.assertEqual(model["kv"]["tokens_per_request"], 20334)
        self.assertEqual(model["kv"]["sequences"], 7.49)
        self.assertEqual(model["kv"]["demand_tokens"], 5693440)
        self.assertEqual(model["kv"]["demand_gb"], 1865.6)
        self.assertEqual(model["replicas"], 40)
        self.assertEqual(sizing["total_gpus"], 40)
        self.assertFalse(sizing["fits"])

    def test_one_group_context_leaves_the_others_at_the_default(self):
        # chat and rag at 9,216: 140 x 9,216 + 120 x 33,792 + 20 x 9,216 = 5,529,600 tokens,
        # 5,529,600 x 327,680 / 1e9 = 1,811.9 GB; mean 19,748.6; 152,282 / 19,748.6 = 7.71.
        sizing, model = self.mixed(contexts={"code_assistant": 32768})
        self.assertEqual(model["kv"]["tokens_per_request"], 19749)
        self.assertEqual(model["kv"]["sequences"], 7.71)
        self.assertEqual(model["kv"]["demand_tokens"], 5529600)
        self.assertEqual(model["kv"]["demand_gb"], 1811.9)
        self.assertEqual(model["replicas"], 39)

    def test_the_model_context_applies_to_groups_without_their_own(self):
        # chat and rag at 4,096 + 1,024 = 5,120: 140 x 5,120 + 120 x 33,792 + 20 x 5,120
        # = 4,874,240 tokens = 1,597.2 GB; mean 4,874,240 / 280 = 17,408; 152,282 / 17,408 = 8.75.
        _, model = self.mixed(
            contexts={"code_assistant": 32768}, model_extra={"context_tokens": 4096}
        )
        self.assertEqual(model["kv"]["demand_tokens"], 4874240)
        self.assertEqual(model["kv"]["demand_gb"], 1597.2)
        self.assertEqual(model["kv"]["tokens_per_request"], 17408)
        self.assertEqual(model["kv"]["sequences"], 8.75)
        self.assertEqual(
            model["kv"]["context_by_usage"], {"chat": 4096, "code_assistant": 32768, "rag": 4096}
        )
        self.assertEqual(model["replicas"], 33)

    def test_a_long_group_context_needs_whole_request_packing(self):
        # code_assistant 100,000 (101,024 per request): one fits a replica next to 5 short
        # ones; 120 of them need 120 replicas, pooled tokens would suggest 90.
        # Demand 140 x 9,216 + 120 x 101,024 + 20 x 9,216 = 13,597,440 tokens, 4,455.6 GB.
        _, model = self.mixed(contexts={"code_assistant": 100000})
        self.assertEqual(model["replicas"], 120)
        self.assertEqual(model["kv"]["demand_tokens"], 13597440)
        self.assertEqual(model["kv"]["demand_gb"], 4455.6)
        self.assertEqual(model["kv"]["tokens_per_request"], 48562)
        self.assertEqual(model["kv"]["sequences"], 3.14)

    def test_a_group_context_for_a_group_without_users_has_no_effect(self):
        models = [{"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}]
        base, _ = self.size(**{"workload.usage": {"chat": 1.0}, "workload.models": models})
        for usage in ({"chat": 1.0}, {"chat": 1.0, "rag": 0}):
            with self.subTest(usage=usage):
                sizing, _ = self.size(
                    **{
                        "workload.usage": usage,
                        "workload.models": models,
                        "workload.context_tokens": {"rag": 3000000},
                    }
                )
                self.assertEqual(sizing, base)

    def test_batch_only_usage_uses_one_implicit_group(self):
        models = [{"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}]
        for contexts in (None, {"chat": 100000}):
            with self.subTest(contexts=contexts):
                overrides = {"workload.usage": {"batch": 1.0}, "workload.models": models}
                if contexts:
                    overrides["workload.context_tokens"] = contexts
                sizing, _ = self.size(**overrides)
                kv = sizing["models"][0]["kv"]
                self.assertEqual(kv["context_by_usage"], {})
                self.assertEqual(kv["in_flight_by_usage"], {})
                self.assertEqual(kv["tokens_per_request"], 9216)
                self.assertEqual(kv["demand_tokens"], 9216)

    def in_flight(self, users, usage, contexts=None):
        models = [{"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}]
        overrides = {"org.users_total": users, "workload.usage": usage, "workload.models": models}
        if contexts:
            overrides["workload.context_tokens"] = contexts
        sizing, _ = self.size(**overrides)
        return sizing, sizing["models"][0]

    def test_a_tie_between_fractions_goes_to_the_earlier_group(self):
        # 40 users, chat 0.05 / code_assistant 0.2 / rag 0.1 / batch 0.65: peaks 0.2, 2.4, 0.4
        # (sum 3.0), concurrency_high 3, quotas 0.2, 2.4, 0.4. Floors 0, 2, 0; one unit is
        # left; code_assistant and rag tie on 0.4 and code_assistant comes first.
        usage = {"chat": 0.05, "code_assistant": 0.2, "rag": 0.1, "batch": 0.65}
        sizing, model = self.in_flight(40, usage)
        self.assertEqual(sizing["concurrency"]["high"], 3)
        self.assertEqual(
            model["kv"]["in_flight_by_usage"], {"chat": 0, "code_assistant": 3, "rag": 0}
        )

    def test_a_tie_between_fractions_does_not_depend_on_float_noise(self):
        # 250 users, chat 0.35 / code_assistant 0.4 / rag 0.1 / batch 0.15: peaks 8.75, 30,
        # 2.5 (sum 41.25), concurrency_high 42, quotas 8.909, 30.545, 2.545. Floors 8, 30, 2;
        # two units are left: chat (0.909), then code_assistant before rag (both 0.545).
        # Contexts 8k / 32k / 16k: 9 x 9,216 + 31 x 33,792 + 2 x 17,408 tokens; a replica
        # holds 152,282: 4 code_assistant requests each, 8 replicas for 31 of them (the
        # last holds 3) and the rest fit beside them: 9 replicas.
        usage = {"chat": 0.35, "code_assistant": 0.4, "rag": 0.1, "batch": 0.15}
        contexts = {"chat": 8192, "code_assistant": 32768, "rag": 16384}
        sizing, model = self.in_flight(250, usage, contexts)
        self.assertEqual(sizing["concurrency"]["high"], 42)
        self.assertEqual(
            model["kv"]["in_flight_by_usage"], {"chat": 9, "code_assistant": 31, "rag": 2}
        )
        self.assertEqual(model["replicas"], 9)

    def test_in_flight_requests_are_split_by_largest_remainder(self):
        # 7 users, chat 0.4 / code_assistant 0.3 / rag 0.3: peaks 0.28, 0.63, 0.21 (sum 1.12),
        # concurrency_high 2. Quotas 0.5, 1.125, 0.375: floors 0, 1, 0 and the spare unit
        # goes to the largest fraction (chat). rag keeps no requests but still counts
        # for the longest request: 200,000 + 1,024 tokens need 2 GPUs.
        usage = {"chat": 0.4, "code_assistant": 0.3, "rag": 0.3}
        models = [{"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}]
        sizing, _ = self.size(
            **{
                "org.users_total": 7,
                "workload.usage": usage,
                "workload.models": models,
                "workload.context_tokens": {"rag": 200000},
            }
        )
        self.assertEqual(sizing["concurrency"]["high"], 2)
        model = sizing["models"][0]
        self.assertEqual(
            model["kv"]["in_flight_by_usage"], {"chat": 1, "code_assistant": 1, "rag": 0}
        )
        self.assertEqual(model["kv"]["demand_tokens"], 2 * 9216)
        self.assertEqual(model["gpus_per_replica"], 2)

    def test_group_grows_until_the_longest_request_fits(self):
        # 115 GB of weights plus overhead (126.5 GB) leave 0.4 GB of cache on one GPU:
        # 1,220 tokens, too few for a 200,000 + 1,024 token request. Two GPUs leave
        # 127.3 GB: 388,488 tokens, one code_assistant request each (27 in flight, 27
        # replicas) and the 9 chat requests fit beside them: 54 GPUs. Demand
        # 9 x 9,216 + 27 x 201,024 = 5,510,592 tokens, 1,805.7 GB, mean 153,072 tokens.
        usage = {"chat": 0.5, "code_assistant": 0.5}
        models = [{"role": "chat", "weights_gb": 115, "arch": self.ARCH}]
        sizing, _ = self.size(
            **{
                "workload.usage": usage,
                "workload.models": models,
                "workload.context_tokens": {"code_assistant": 200000},
            }
        )
        model = sizing["models"][0]
        self.assertEqual(model["gpus_per_replica"], 2)
        self.assertEqual(model["kv"]["status"], "computed")
        self.assertEqual(model["kv"]["cached_tokens"], 388488)
        self.assertEqual(model["kv"]["context_by_usage"]["code_assistant"], 200000)
        self.assertEqual(model["kv"]["in_flight_by_usage"], {"chat": 9, "code_assistant": 27})
        self.assertEqual(model["replicas"], 27)
        self.assertEqual(sizing["total_gpus"], 54)
        self.assertEqual(model["kv"]["demand_tokens"], 5510592)
        self.assertEqual(model["kv"]["demand_gb"], 1805.7)
        self.assertEqual(model["kv"]["tokens_per_request"], 153072)
        self.assertEqual(model["kv"]["sequences"], 2.54)

    def test_the_model_context_can_grow_the_group(self):
        # 70B fp8 on 141 GB GPUs: one GPU caches 152,282 tokens, enough for the default
        # 8,192 + 1,024 = 9,216 token request. With the model's context of 200,000
        # (201,024 per request) one GPU is too small; two GPUs cache
        # floor((253.8 - 77) x 1e9 / 327,680) = 539,550 tokens.
        arch_model = {"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}
        plain, _ = self.size(**{"workload.models": [arch_model]})
        self.assertEqual(plain["models"][0]["gpus_per_replica"], 1)
        long, _ = self.size(**{"workload.models": [{**arch_model, "context_tokens": 200000}]})
        model = long["models"][0]
        self.assertEqual(model["gpus_per_replica"], 2)
        self.assertEqual(model["kv"]["status"], "computed")
        self.assertEqual(model["kv"]["cached_tokens"], 539550)

    def test_insufficient_kv_capacity_does_not_fit(self):
        # Eight GPUs leave 888.7 GB: 2,712,097 tokens, fewer than 4,000,000 + 1,024.
        usage = {"chat": 0.5, "code_assistant": 0.5}
        models = [{"role": "chat", "weights_gb": 115, "arch": self.ARCH}]
        sizing, _ = self.size(
            **{
                "workload.usage": usage,
                "workload.models": models,
                "workload.context_tokens": {"code_assistant": 4000000},
            }
        )
        model = sizing["models"][0]
        self.assertEqual(model["kv"]["status"], "insufficient")
        self.assertEqual(model["kv"]["cached_tokens"], 2712097)
        self.assertEqual(model["gpus_per_replica"], 8)
        self.assertIn("longest context", model["notes"][0])
        self.assertFalse(sizing["fits"])

    def test_a_larger_group_that_needs_fewer_gpus_is_noted(self):
        # One context for everyone: 18 one-GPU replicas, or 1 eight-GPU replica holding
        # about 310 requests (8 GPUs), or 2 four-GPU replicas holding about 142 each (8 GPUs). The smaller group wins the tie.
        _, model = self.mixed()
        self.assertEqual(model["gpus_per_replica"], 1)
        self.assertEqual(
            model["notes"],
            [
                "with 4-GPU replicas the memory model needs 8 GPUs instead of 18; "
                "tensor parallelism adds synchronization overhead, "
                "so benchmark throughput before choosing it"
            ],
        )

    def test_the_note_counts_the_replica_minimum(self):
        # 400 chat users: 400 x 0.2 x 0.5 = 40 requests in flight; one GPU holds
        # floor(152,282 / 9,216) = 16 of them: ceil(40 / 16) = 3 replicas, 3 GPUs. With no
        # downtime allowed the minimum is 2 replicas, so a 2-GPU replica (58 requests)
        # still means 2 replicas = 4 GPUs, not 2 x 1 = 2 GPUs: no cheaper group, no note.
        sizing, _ = self.size(
            **{
                "org.downtime_tolerance": "none",
                "org.users_total": 400,
                "workload.models": [
                    {"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}
                ],
            }
        )
        model = sizing["models"][0]
        self.assertEqual(model["replicas"], 3)
        self.assertEqual(model["notes"], [])

    def test_the_note_counts_the_replica_minimum_with_a_cheaper_group(self):
        # 2,000 users with downtime "none": 18 replicas; 4-GPU replicas: 2 x 4 = 8 GPUs.
        sizing, _ = self.size(
            **{
                "org.downtime_tolerance": "none",
                "org.users_total": 2000,
                "workload.usage": self.USAGE,
                "workload.models": [
                    {"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}
                ],
            }
        )
        self.assertIn(
            "with 4-GPU replicas the memory model needs 8 GPUs instead of 18",
            sizing["models"][0]["notes"][0],
        )

    def test_notes_name_larger_groups_for_mixed_and_long_contexts(self):
        _, model = self.mixed(contexts={"chat": 8192, "code_assistant": 32768, "rag": 16384})
        self.assertIn("with 8-GPU replicas the memory model needs 16 GPUs instead of 40", model["notes"][0])
        usage = {"chat": 0.5, "code_assistant": 0.5}
        sizing, _ = self.size(
            **{
                "workload.usage": usage,
                "workload.models": [{"role": "chat", "weights_gb": 115, "arch": self.ARCH}],
                "workload.context_tokens": {"code_assistant": 200000},
            }
        )
        self.assertIn(
            "with 4-GPU replicas the memory model needs 24 GPUs instead of 54",
            sizing["models"][0]["notes"][0],
        )

    def test_no_note_when_the_chosen_group_is_the_cheapest(self):
        sizing, _ = self.size(
            **{"workload.models": [{"role": "chat", "params_b": 70, "precision": "fp8", "arch": self.ARCH}]}
        )
        # 18 requests of 9,216 tokens: 2 one-GPU replicas; a 4-GPU replica would cost 4 GPUs.
        self.assertEqual(sizing["models"][0]["replicas"], 2)
        self.assertEqual(sizing["models"][0]["notes"], [])

    def test_embedding_models_skip_kv_sizing(self):
        models = [{"role": "embedding", "weights_gb": 2.5, "arch": self.ARCH}]
        sizing, _ = self.size(**{"workload.models": models})
        self.assertEqual(sizing["models"][0]["kv"], {"status": "not_applicable"})


class ReplicasNeededTest(unittest.TestCase):
    @staticmethod
    def one_by_one(cached, requests):
        replicas = []
        for tokens, count in sorted(requests, key=lambda item: -item[0]):
            for _ in range(count):
                for index, free in enumerate(replicas):
                    if free >= tokens:
                        replicas[index] -= tokens
                        break
                else:
                    replicas.append(cached - tokens)
        return len(replicas)

    def test_whole_requests_are_packed_first_fit_decreasing(self):
        self.assertEqual(replicas_needed(10, [(6, 3)]), 3)
        self.assertEqual(replicas_needed(10, [(6, 2), (4, 2)]), 2)
        self.assertEqual(replicas_needed(10, [(3, 7)]), 3)
        self.assertEqual(replicas_needed(10, [(5, 0)]), 0)

    def test_runs_give_the_same_count_as_placing_requests_one_by_one(self):
        rng = random.Random(12)
        for _ in range(300):
            cached = rng.randint(20, 400)
            requests = [(rng.randint(1, cached), rng.randint(0, 40)) for _ in range(rng.randint(1, 4))]
            with self.subTest(cached=cached, requests=requests):
                self.assertEqual(
                    replicas_needed(cached, requests), self.one_by_one(cached, requests)
                )


class TotalsTest(SizingTestCase):
    def test_spec_example_totals(self):
        models = [{"role": "chat", "params_b": 671, "precision": "fp8"}]
        sizing, _ = self.size(**{"workload.models": models})
        self.assertEqual(sizing["total_gpus"], 8)
        self.assertEqual(sizing["servers"], 1)
        self.assertEqual(sizing["power_kw"], 10.1)
        self.assertIs(sizing["fits"], True)
        self.assertIs(sizing["benchmark_required"], True)

    def test_too_few_gpus_do_not_fit(self):
        models = [{"role": "chat", "params_b": 671, "precision": "fp8"}]
        gpus = [{"model": "big", "count": 4, "vram_gb": 141}]
        sizing, _ = self.size(**{"workload.models": models, "hardware.gpus": gpus})
        self.assertIs(sizing["fits"], False)
        self.assertIsNone(sizing["power_kw"])

    def test_no_downtime_doubles_the_replicas(self):
        sizing, assumptions = self.size(**{"org.downtime_tolerance": "none"})
        self.assertEqual(sizing["models"][0]["replicas"], 2)
        self.assertEqual(sizing["total_gpus"], 2)
        self.assertIn("sizing.ha_min_replicas", [item["id"] for item in assumptions])

    def test_power_budget(self):
        sizing, _ = self.size(**{"hardware.power_budget_kw": 1.0})
        self.assertEqual(sizing["power_kw"], 1.3)
        self.assertIs(sizing["power_within_budget"], False)
        self.assertIn("power", sizing["warnings"][0])

    def test_assumptions_list_every_constant_used(self):
        _, assumptions = self.size()
        ids = [item["id"] for item in assumptions]
        self.assertEqual(len(ids), len(set(ids)))
        for expected in (
            "sizing.chat.active",
            "sizing.chat.duty_low",
            "sizing.chat.duty_high",
            "sizing.bytes_per_param.fp8",
            "sizing.overhead",
            "sizing.gpu_memory_utilization",
            "sizing.gpu_group_sizes",
            "sizing.gpus_per_server",
            "sizing.power_system_factor",
        ):
            self.assertIn(expected, ids)
        for item in assumptions:
            self.assertEqual(set(item), {"id", "value", "evidence", "note"})
            self.assertIn(item["evidence"], EVIDENCE_LEVELS)


class HardwareTest(SizingTestCase):
    def test_largest_vram_type_is_primary(self):
        entries = [
            {"model": "small", "count": 4, "vram_gb": 24},
            {"model": "big", "count": 2, "vram_gb": 141},
        ]
        self.assertEqual(pick_primary_gpu(entries, no_gpu_table)["model"], "big")
        sizing, _ = self.size(**{"hardware.gpus": entries})
        self.assertIn("several GPU types", sizing["warnings"][0])

    def test_table_supplies_missing_vram_and_tdp(self):
        table = {"known": {"vram_gb": 48, "tdp_w": 300}}
        gpu = pick_primary_gpu([{"model": "known", "count": 2}], table.get)
        self.assertEqual(gpu, {"model": "known", "vram_gb": 48, "tdp_w": 300, "count": 2})

    def test_table_supplies_vram_and_tdp_given_as_null(self):
        # answers.py accepts an explicit null; it means the same as a missing key.
        table = {"known": {"vram_gb": 48, "tdp_w": 300}}
        entry = {"model": "known", "count": 2, "vram_gb": None, "tdp_w": None}
        gpu = pick_primary_gpu([entry], table.get)
        self.assertEqual(gpu, {"model": "known", "vram_gb": 48, "tdp_w": 300, "count": 2})

    def test_unknown_gpu_without_vram_is_an_input_error(self):
        with self.assertRaises(SizingInputError) as caught:
            self.size(**{"hardware.gpus": [{"model": "mystery", "count": 1}]})
        self.assertEqual(
            caught.exception.problems,
            ["hardware.gpus: item 0: 'mystery' is not in gpus.toml; supply vram_gb"],
        )

    def test_cpu_only_compares_weights_with_ram(self):
        models = [{"role": "chat", "params_b": 8, "precision": "int4"}]
        sizing, _ = self.size(
            **{"hardware.gpus": [], "hardware.ram_gb": 64, "workload.models": models}
        )
        self.assertIs(sizing["cpu_only"], True)
        self.assertEqual(sizing["total_gpus"], 0)
        self.assertEqual(sizing["ram_required_gb"], 4.4)
        self.assertIs(sizing["fits"], True)
        self.assertIn("CPU inference", sizing["warnings"][0])

    def test_cpu_only_without_ram_is_an_input_error(self):
        with self.assertRaises(SizingInputError):
            self.size(**{"hardware.gpus": []})


if __name__ == "__main__":
    unittest.main()
