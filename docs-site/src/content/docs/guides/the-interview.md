---
title: The interview
description: How the agent asks its questions, and what it does with "I don't know".
---

The interview fills the answers that the tier, the sizing and the decisions need. The full list, with every choice and every default, is on [Interview](/reference/architect/interview/).

## How it asks

- **Your files first.** Point the agent at a README, architecture notes or a hardware inventory. It fills every answer those already give and tells you in one message which answers it has and how many questions remain.
- **One question per message**, with the choices offered, in the language you write in. Question IDs and choice values stay in English.
- **"I don't know" is an answer.** The agent records `unknown`, applies the documented default, and adds the default to the blueprint's assumptions table, labelled `estimate`.
- **Four answers have no default:** how many people, how many departments, which models, and which GPUs.
- **It can resume.** Before the first question the agent creates the blueprint file with an Answers table, and records each answer there before it asks the next. The blueprint is the design's only state, so an interrupted interview picks up where it stopped.

## What it covers

| Topic | Examples |
|---|---|
| The organization | people, departments, whether departments may see each other's data, audit duty, acceptable downtime, who operates it, Kubernetes experience |
| Inside the network | who installs and later operates it: people, an agent on a local model, or people first and then an agent |
| The workload | chat, coding assistants, document question answering, batch jobs; the models and their sizes; how long a typical request is |
| The hardware | GPUs that exist or will be bought, system RAM when there is no GPU, power available, CPU architecture |
| What exists | identity provider, API gateway, cluster platform, registry |
| The gap | how files enter the network, and how often |

When you do not know the model yet, a size class is enough for a first sizing: S up to 15B parameters, M 16B to 80B, L 81B to 300B, XL above 300B.

GPU names are matched against the [GPU table](/reference/gpus/). A name that fits several variants with different memory, such as `H100` or `A100`, gets a follow-up question: the memory decides the sizing, and the vendor decides which images are carried in.
