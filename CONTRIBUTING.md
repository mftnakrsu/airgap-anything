# Contributing

The skills are markdown, so most contributions are a small pull request: a new catalog entry, a re-verified version, a field note from a real deployment, a better sentence in a reference file.

## The rule: nothing from memory

Every value in the catalog has a source that was opened when the value was written, or a note from someone who ran the thing. A value with neither is labeled `estimate`.

This applies to people and to coding agents alike. If you are an agent: do not fill in a version, an image name, a license, a setting or a number from what you remember, even when you are sure. Open the page, copy the value, record the URL.

## Evidence labels

| Label | Meaning | What the entry needs |
|---|---|---|
| `field` | Verified in a real deployment by a named person | "Verified by:" with your GitHub handle, and the version, hardware and context in the evidence notes |
| `docs` | Taken from official project or vendor documentation, or, where the documentation is silent, from the project's source code at the release tag; a statement taken from source code says so | at least one `https://` URL under "Sources:" |
| `estimate` | Reasoned, or taken from community sources | evidence notes that state the basis |

An entry carries one label for the whole entry. Use `docs` only when the version, the license, everything under "Carry in" and every statement under "Choose when", "Avoid when" and "Caveats" trace to a URL in its sources. If one of them does not, the entry is `estimate` and its notes name the unsourced parts.

## Adding or updating a component

1. Copy the template below to `plugins/airgap-anything/skills/airgap-architect/catalog/`. The file name is the component ID plus `.md`; an ID is lower-case words of letters and digits joined by single hyphens, for example `distribution-registry`.
2. Fill it from the project's official sources and list every URL you used under "Sources:".

   | Part | Where the value comes from |
   |---|---|
   | Version | The latest stable release on the project's release page: the highest stable version, which is not always the release GitHub marks as latest. An exact version, never `latest`. When other entries list this component under Requires and their documentation names the versions they support, pin the newest release that all of them support, and say why in the air-gap notes. |
   | License | The SPDX identifier of the repository's license file. If the project has paid editions, say in the caveats which features need them. |
   | Tiers | The floors at which the component is still adequate. A component fit for T3 also lists T1 and T2. |
   | Requires | Other catalog components the documentation says it needs, for example a database: IDs of existing entries only. |
   | Images | One row per image the official installation documentation names for a hardware class (`nvidia`, `amd`, `intel`, `cpu`, or `any`), with the tag of that exact version. Write "not recorded" for the digest unless the publisher documents it. No aliases of the same image and no images that are only needed to build. |
   | Packages | One row per file that the official offline installation needs: the file exactly as the release names it, its architecture (`amd64`, `arm64` or `any`), the download URL, and the URL of the publisher's checksum file, or "none published". |
   | Runtime downloads | What the software fetches while it runs: models, plugins, update checks. |
   | Telemetry and egress | Each telemetry, analytics or update-check feature the documentation describes, with the documented setting that turns it off. If the documentation says nothing, write "None documented." and say so in the air-gap notes. |
   | License server | Whether any license check needs network access. |
   | Choose when, Avoid when, Caveats | Short statements, each traceable to a source. |
   | Alternatives | IDs of existing entries, not product names. |
   | Per-tool skills | Skills that exist today. Open the repository and confirm the skill folder is there. |

3. Set "Last verified" to today and choose the evidence label by the rule above.
4. Add the entry to the catalog table in `plugins/airgap-anything/skills/airgap-architect/SKILL.md`, under its layer, and to "Components used in this file" of the layer guide that can choose it.
5. Run the checks (see "Running the checks").
6. In the pull request, list what you verified and what you could not.

### Template

````markdown
# Display Name (`component-id`)

One sentence on what it is.

| Field | Value |
|---|---|
| Layer | `llm-serving` |
| Version | `1.2.3` |
| License | Apache-2.0 |
| Tiers | T1, T2, T3 |
| Requires | none |
| Evidence | docs |
| Last verified | 2026-01-01 |

## Choose when

- Condition, with where the documentation says so.

## Avoid when

- Condition.

## Alternatives

`other-component-id`.

## Caveats

- What a design must know.

## Carry in

### Images

| Image | Hardware | Digest |
|---|---|---|
| `registry.example/org/name:1.2.3` | any | not recorded |

### Packages

None.

### Runtime downloads to stage in advance

None.

### Telemetry and egress to switch off before the first start

1. What is sent, and where.
   Switch off: the documented setting.

### License server

None: no license check needs connectivity.

### Air-gap notes

What the offline installation needs beyond the tables, and what was not verified.

## Per-tool skills

- `skill-name` in `owner/repository`

## Evidence

Level: docs.

Notes on what was read and when.

Sources:

- https://example.org/docs/page
````

`tests/test_catalog.py` checks the fields, the order of the sections, pinned image references, that IDs under Requires and Alternatives exist, and that sources are listed.

## Verifying an entry in the field

When you have run a component in a real air-gapped deployment:

1. Set "Evidence" to `field`.
2. Add "Verified by: your GitHub handle." under "## Evidence".
3. In the notes, state the version you ran, the hardware, and what you confirmed: that it installs offline, that the telemetry setting works, that nothing tries to reach the internet.
4. Set "Last verified" to the date of the deployment, and keep the URLs under "Sources:".

## GPU rows

`plugins/airgap-anything/skills/airgap-architect/references/gpus.md` has one table row per GPU model and a "Notes and sources" subsection per row. Memory and power come from the vendor's specification page; record the URL. Write `unknown` for power when the vendor does not publish it. The vendor is `nvidia`, `amd` or `intel`: the transfer manifest uses it to choose the image variant. Give each variant its own name, for example `A100 40GB` and `A100 80GB`, and leave out a bare `A100` that would fit both.

## Thresholds, defaults and sizing constants

The tier thresholds are in `references/tiers.md`, the defaults for "unknown" answers in `references/interview.md`, and the sizing constants in `references/sizing.md`, each with its evidence label and basis. Most are estimates. To replace one, change the value and its label, add the source or the field note, and update the worked examples of `references/sizing.md` and the matching numbers in `tests/sizing_reference.py` and the eval scenarios in the same pull request; `tests/test_sizing.py` fails until they agree. Say in the pull request why the number changed.

## Layer guides

The guides in `plugins/airgap-anything/skills/airgap-architect/references/layers/` carry one evidence label per case. A case becomes `docs` only when official documentation supports the whole step from its condition to its choice (a threshold this project picked is never documented, so such a case stays `estimate`); put the URL in its "Why" column.

## Changing what a skill makes the agent do

A change to a `SKILL.md` or a reference file changes behavior. Rerun the skill's protocol in `evals/README.md` and record the results under `evals/results/`. A change to a `description` also needs the triggering suite (`evals/README.md`, "Triggering").

## Images in the README

Every image in the README either brings its own background or is transparent and reads on both GitHub page colours, because the browser picks a `<picture>` source by the computer's colour scheme while GitHub draws the page in the GitHub theme. `tests/test_readme.py` checks this, and `assets/brand/BRAND.md` explains it. The "How it works" diagram, `assets/brand/how-it-works.svg`, is the transparent kind: change `design/brand/tools/build_how_it_works.py` and rerun it, never the SVG.

## Running the checks

Python 3.11 or newer, no packages to install. The skills themselves need no Python; these checks are for the repository.

```bash
python3 -m unittest discover -s tests -t . -v
claude plugin validate plugins/airgap-anything --profile directory
```

## The documentation site

The site in `docs-site/` shows each skill's workflow and references, every catalog entry, the GPU table, this guide and the department example. Those pages are generated from the files they describe, so after you change a skill file, a catalog entry, `references/gpus.md`, the example in `examples/department/`, the README's Install section or this file, run:

```bash
python3 docs-site/scripts/generate_reference.py
```

and commit the pages it writes. The tests fail when a page is out of date. To preview the site you need Node.js 24: `cd docs-site && npm ci && npm run dev`.
