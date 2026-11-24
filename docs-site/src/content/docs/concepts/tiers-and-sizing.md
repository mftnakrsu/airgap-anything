---
title: Tiers and sizing
description: Why organizational complexity and GPU count are two separate answers.
---

## The tier: how complex the organization is

| Tier | Typical shape | People | Departments |
|---|---|---|---|
| T1 | a single team | 50 or fewer | 1 |
| T2 | a department, or several teams with their own budgets | 51 to 300 | 2 to 5 |
| T3 | an enterprise | more than 300 | more than 5 |

The base tier is the higher of two: one from the number of people, one from the number of departments. Some answers raise single layers above it, as **floors**: an audit duty raises the gateway, separated departments raise the gateway and identity (to T3 when data also has classification levels), a zero-downtime requirement raises the serving, orchestration and state layers. A floor is the lowest tier a layer may be designed for. Going below one is your decision, never the agent's: it is recorded as an override with your reason, and the blueprint's tier section lists every override.

The tier selects patterns, such as "gateway or not" and "Compose or Kubernetes". It never counts hardware. The thresholds and floors are on [Tiers and floors](/reference/architect/tiers/), each with its evidence label and its basis.

## Sizing: how much hardware

The agent follows the [sizing procedure](/reference/architect/sizing/) for every model: how many requests are in flight at peak, how much memory the weights need, the smallest group of 1, 2, 4 or 8 GPUs that holds them, the KV cache when the model's architecture is known, the replicas, and the GPUs, servers and kilowatts that follow. It writes every step's inputs and result into the blueprint's sizing section, so you can check each number with a calculator. For 180 people who only chat:

- Concurrency: 180 × 0.20 × 0.25 = 9 to 180 × 0.20 × 0.50 = 18 requests in flight.
- A 671B model at fp8: 671 GB of weights, 738.1 GB with 10 % overhead.
- On 141 GB GPUs, of which 90 % is usable: 4 GPUs give 507.6 GB, 8 give 1,015.2 GB, so one replica spans 8 GPUs.

The constants behind these steps, such as the share of people active in the peak hour or the share of GPU memory the engine may use, are listed on the sizing page with their basis. Unless the table says otherwise they are `estimate`, and the blueprint's assumptions table names every one the design used, so you can replace them with measurements.

When the hardware does not fit, the agent offers the options: a lower precision, a smaller model, more GPUs, a shorter context for one group of users, or a larger GPU group per replica. You choose; going ahead on hardware that does not fit is an override.

So a 40-person team that serves a very large model can need many GPUs at T1, and a 2,000-person company that serves a small model can need few at T3.

## Memory, not speed

Sizing covers memory. Published throughput numbers for inference engines conflict, so the design does not predict speed: every blueprint carries a "benchmark before production" step, and the verification section names what to measure.
