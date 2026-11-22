---
title: Tiers and sizing
description: Why organizational complexity and GPU count are two separate answers.
---

## The tier: how complex the organization is

| Tier | Typical shape |
|---|---|
| T1 | a single team |
| T2 | a department, or several teams with their own budgets |
| T3 | an enterprise |

The base tier comes from the number of people and departments. Some answers raise single layers above it, as **floors**: an audit duty raises the gateway, separated departments raise the gateway and identity, a zero-downtime requirement raises the serving, orchestration and state layers. A floor is the lowest tier a layer may be designed for. Going below one needs an override with a reason, which lint reports and the blueprint lists.

The tier selects patterns, such as "gateway or not" and "Compose or Kubernetes". It never counts hardware. The thresholds live in `catalog/rules.toml`, each with its evidence label.

## Sizing: how much hardware

`size.py` computes the GPU count from the models, the kind of use and the number of people: how many requests are in flight at peak, how much memory the weights and the cache need, and how many GPUs, servers and kilowatts follow.

So a 40-person team that serves a very large model can need many GPUs at T1, and a 2,000-person company that serves a small model can need few at T3.

## Memory, not speed

Sizing covers memory. Published throughput numbers for inference engines conflict, so the design does not predict speed: every blueprint carries a "benchmark before production" step, and the verification section names what to measure.
