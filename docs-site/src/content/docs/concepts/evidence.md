---
title: Evidence labels
description: Every catalog entry, threshold and decision carries a label that says how far to trust it.
---

| Label | Meaning |
|---|---|
| `field` | Verified in a real deployment by a named person |
| `docs` | Taken from official project or vendor documentation, or, where the documentation is silent, from the project's source code at the release tag; the URL is recorded |
| `estimate` | Reasoned or community-sourced; verify before relying on it |

A decision inherits the weakest label among its inputs. Every decision that rests on an estimate is listed in the blueprint's verification section, so you know what to check before production.

## Nothing from memory

Every value in the catalog was copied from a page that was opened when it was written, and that page's URL is on the entry's [catalog page](/reference/catalog/). A value without a source is labelled `estimate`.

## Freshness

Software moves. Lint warns (W1) when a catalog entry a blueprint uses was last verified more than 180 days earlier. [Contributing](/project/contributing/) explains how an entry is re-verified.
