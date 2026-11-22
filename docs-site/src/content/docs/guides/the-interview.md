---
title: The interview
description: How the agent asks its questions, and what it does with "I don't know".
---

The interview fills the answers that the scripts and the decisions need. The full list is on [Interview questions](/reference/interview-questions/).

## How it asks

- **Your files first.** Point the agent at a README, architecture notes or a hardware inventory. It fills every answer those already give and tells you how many questions remain.
- **One question per message**, with the choices offered, in the language you write in. Stored values stay in English.
- **"I don't know" is an answer.** The scripts then use the default from the catalog's rules and record it as an assumption that the blueprint lists for verification.
- **Four answers have no default:** how many people, how many departments, which models, and which GPUs.
- **It can resume.** Each answer is written to `docs/airgap/blueprint.json` before the next question, so an interrupted interview picks up where it stopped.

## What it covers

| Topic | Examples |
|---|---|
| The organization | people, departments, whether departments may see each other's data, audit duty, acceptable downtime, who operates it |
| The workload | chat, coding assistants, document question answering, batch jobs; the models and their sizes |
| The hardware | GPUs that exist or will be bought, power available |
| What exists | identity provider, API gateway, cluster platform, registry |
| The gap | how files enter the network, and how often |

When you do not know the model yet, a size class (S, M, L, XL) is enough for a first sizing.
