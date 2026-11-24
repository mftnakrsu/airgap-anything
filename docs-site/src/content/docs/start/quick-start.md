---
title: Quick start
description: Ask your agent in your own words; the skill starts by itself and interviews you.
---

## Ask in your own words

On a machine with internet access, open your project and ask, for example:

> Design an air-gapped LLM platform for my organization.

> We need to run an LLM chat service for about 200 engineers on a network that has no internet access. Help me design it.

> Kurumumuzda internete kapalı bir ağda üç departmana hizmet verecek bir LLM platformu kurmamız gerekiyor. Bunu nasıl tasarlarız?

You do not need to name the skill. Claude Code reads the skill's description and starts it when a request is about designing, planning or sizing a system for an air-gapped, offline or on-premises network. A [test suite](/project/testing/) checks this in English and Turkish, and checks that unrelated requests leave the skill alone.

## Or start it yourself

| Installed as | Command |
|---|---|
| Claude Code plugin | `/airgap-anything:airgap-architect` |
| Personal or project skill (the `npx skills` and offline routes) | `/airgap-architect` |

Write your request after the command, or start with the command alone.

## What happens next

1. The agent tells you which answers it already found in your files and how many questions remain.
2. It asks the rest one at a time. "I don't know" is a valid answer; a documented default is used and recorded as an assumption. See [The interview](/guides/the-interview/).
3. The agent works out the tier and the sizing step by step and writes every number into the blueprint, chooses one component per layer from the catalog, and writes the list of what to carry in.
4. It checks the blueprint against its self-review list and asks for your approval. Nothing is built before you approve.
5. Once you approve, ask for the transfer in your own words, for example "prepare everything in the transfer manifest for our USB disks". `airgap-transfer` shows its plan and downloads nothing before you say yes. See [Carrying it in](/guides/carrying-it-in/). For coding agents inside the network, ask for them the same way: see [Coding agents inside](/guides/coding-agents/). To make your documents searchable inside, see [Searchable documents inside](/guides/searchable-documents/).

[What you get](/guides/what-you-get/) describes the files.
