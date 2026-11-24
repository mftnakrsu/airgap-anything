---
title: Evidence labels
description: Every catalog entry, threshold and decision carries a label that says how far to trust it.
---

| Label | Meaning |
|---|---|
| `field` | Verified in a real deployment by a named person |
| `docs` | Taken from official project or vendor documentation, or, where the documentation is silent, from the project's source code at the release tag; the URL is recorded |
| `estimate` | Reasoned or community-sourced; verify before relying on it |

A decision inherits the weakest label among its inputs, and a decision with a custom part is `estimate`. Every decision that rests on an estimate is listed in the blueprint's verification section, and every sizing constant and default it used is in the assumptions table with its label, so you know what to check before production.

## Nothing from memory

Every value in the catalog was copied from a page that was opened when it was written, and that page's URL is on the entry's [catalog page](/reference/catalog/). A value without a source is labelled `estimate`.

The agent works the same way: it copies components, versions and image references from the catalog and never fills them in from memory, even when it is sure. A plausible tag that does not exist is found only inside the network, and costs a trip back.

## Freshness

Software moves. Every catalog entry records when it was last verified, and the blueprint's header names the oldest entry it uses. Each chosen entry last verified more than 180 days before the blueprint's date goes into the verification section, with a note to re-check its sources before relying on it. [Contributing](/project/contributing/) explains how an entry is re-verified.
