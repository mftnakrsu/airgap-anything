# Contributing

## The rule: nothing from memory

Every value in the catalog has a source that was opened when the value was written, or a note from someone who ran the thing. A value with neither is labeled `estimate`.

This applies to people and to coding agents alike. If you are an agent: do not fill in a version, an image name, a license, a setting or a number from what you remember, even when you are sure. Open the page, copy the value, record the URL.

## Evidence labels

| Label | Meaning | Required fields |
|---|---|---|
| `field` | Verified in a real deployment by a named person | `verified_by`, and `notes` with hardware and context |
| `docs` | Taken from official project or vendor documentation, or, where the documentation is silent, from the project's source code at the release tag; a statement taken from source code says so | at least one URL in `sources` |
| `estimate` | Reasoned, or taken from community sources | `notes` stating the basis |

Every item in `sources` is a full `http://` or `https://` URL. Lint checks this for every `docs` entry, GPU row and rule, and reports `C4` when a source is not such a URL.

An entry carries one label for the whole entry. Use `docs` only when the version, the license, the artifacts under `[airgap]` and every statement under `[choose]` each trace to a URL in `sources`. If one of them does not, the entry is `estimate` and `notes` names the unsourced fields.

## Adding or updating a component

1. Copy the template below to `plugins/airgap-anything/skills/airgap-architect/catalog/components/`. The file name is the component ID plus `.toml`. An ID is lower-case words of letters and digits joined by single hyphens (the pattern `[a-z0-9]+(-[a-z0-9]+)*`, for example `distribution-registry`); lint reports `C1` for any other ID and `C2` when the ID and the file name differ.
2. Fill it from the project's official sources. Record every URL you used in `evidence.sources`.

   | Field | Where the value comes from |
   |---|---|
   | `version` | The latest stable release on the project's release page. That is the highest stable version, which is not always the release GitHub marks as latest: a project that patches an older line can publish that patch after a newer release. An exact version, never `latest`. When other entries list this component in `requires` and their documentation names the versions they support, pin the newest release that all of them support, and say why in `airgap.notes`. |
   | `license` | The SPDX identifier of the repository's license file. If the project has paid editions, say in `choose.caveats` which features need them. |
   | `airgap.images` | One row per image the official installation documentation names for a hardware class, with the tag of that exact version. Leave `digest` empty unless the publisher documents it. `hardware` lists the classes the image is for, drawn from `nvidia`, `amd`, `intel` and `cpu`; leave it out when the image is for any hardware. The transfer manifest lists only the rows that match the hardware in the blueprint. Do not list aliases of the same image (the same digest under another tag) or images that are only needed to build. |
   | `airgap.packages` | One table per file that the official offline or air-gap installation needs: `file` exactly as the release names it; `arch`, one of `amd64`, `arm64` or `any` (scripts and archives that run on either); `url`, the download URL as the release page or the official documentation gives it, also recorded in `evidence.sources`; and `checksums`, the URL of the publisher's checksum file that lists this file, or `""` when the publisher has none (an md5 list counts). Give rows for `amd64` and, where the release publishes them, for `arm64`; the transfer manifest lists the rows for the blueprint's `hardware.cpu_arch` and the `any` rows. When the entry lists container images, list here only what the image route needs; other install routes (wheels, OS packages, tarballs) go into `airgap.notes`. Lint reports `C5` for a row without `file`, `arch` or `url`, or with another `arch`, and `C6` when `url` or a non-empty `checksums` is not a full `https://` URL. |
   | `airgap.runtime_downloads` | What the software fetches while it runs: models, plugins, update checks. |
   | `airgap.telemetry` | Each telemetry, analytics or update-check feature the documentation describes, with the documented setting that turns it off. If the documentation says nothing, leave the list empty and say so in `airgap.notes`. |
   | `airgap.license_server` | `true` when any license check needs network access. |
   | `requires` | Other catalog components the documentation says it needs, for example a database. Component IDs only, each the ID of an existing file in `catalog/components/`; lint reports `C3` otherwise. If that entry is not written yet, leave the ID out and add it in the change that adds that entry. |
   | `tiers` | The floors at which the component is still adequate. A component fit for T3 also lists T1 and T2. |
   | `choose` | Short statements, each traceable to a source. `alternatives` holds component IDs, not product names, under the same rule as `requires`: each must be the ID of an existing file in `catalog/components/`, or lint reports `C3`. Leave out an alternative whose entry is not written yet and add it in the change that adds that entry. |
   | `deeper_skills` | Per-tool skills that exist today. Open the repository and confirm the skill folder is there. |

3. Set `last_verified` to today.
4. Choose the evidence label by the rule above.
5. Run the checks (see "Running the checks").
6. In the pull request, list what you verified and what you could not.

### Template

```toml
schema_version = 2
id = "<component id>"
name = "<display name>"
layer = "<llm-serving | llm-gateway | ui | identity | observability | orchestration | state | registry>"
summary = "<one sentence>"
tiers = ["T1", "T2", "T3"]
requires = [] # component IDs of existing entries only
version = "<exact version>"
license = "<SPDX identifier>"
last_verified = 2026-01-01

[evidence]
level = "docs"
sources = ["<URL>"]
verified_by = ""
notes = ""

[airgap]
images = [{ ref = "<registry/repository:tag>", digest = "" }]
packages = [{ file = "<file name>", arch = "<amd64 | arm64 | any>", url = "<URL>", checksums = "" }]
runtime_downloads = []
telemetry = [{ what = "<what is sent>", disable = "<documented setting>" }]
license_server = false
notes = ""

[choose]
when = ["<condition>"]
avoid_when = ["<condition>"]
alternatives = [] # component IDs of existing entries only, not product names
caveats = []

[[deeper_skills]]
repo = "<owner/repository>"
skill = "<skill name>"
```

Lint rejects an entry that still contains a value in angle brackets.

## Verifying an entry in the field

When you have run a component in a real air-gapped deployment:

1. Set `evidence.level = "field"`.
2. Put your GitHub handle in `verified_by`.
3. In `notes`, state the version you ran, the hardware, and what you confirmed: that it installs offline, that the telemetry setting works, that nothing tries to reach the internet.
4. Set `last_verified` to the date of the deployment.

Keep the URLs in `sources`.

## GPU rows

`plugins/airgap-anything/skills/airgap-architect/catalog/gpus.toml` has one `[[gpu]]` row per model. Start a new row from the commented row template at the top of that file (lines 4 to 13), which lists every field. Memory and power come from the vendor's specification page; record the URL in `sources`. Leave `tdp_w` out when the vendor does not publish it. `vendor` is required and is one of `nvidia`, `amd` or `intel`; the transfer manifest uses it to choose the image variant when the user gives a model but no vendor.

No two rows may share a name: lint reports `C1` when a model or alias of one row matches a model or alias of another once case and punctuation are ignored. Give each variant its own name, for example `A100 40GB` and `A100 80GB`, and leave out a bare `A100` that would fit both.

## Thresholds and defaults

`plugins/airgap-anything/skills/airgap-architect/catalog/rules.toml` holds the tier thresholds, the escalators, the sizing defaults and the defaults for "unknown" answers. Most are estimates. To replace one, change `value`, set `evidence` to `field` or `docs`, and fill `verified_by` or `sources`. Tests pin the starting values, so update the affected tests in the same pull request and say why the number changed.

## Decision tables

The tables in `plugins/airgap-anything/skills/airgap-architect/references/layers/` carry one evidence label per row. A row becomes `docs` only when official documentation supports the whole step from its condition to its choice (a threshold the design spec picked is never documented, so such a row stays `estimate`); put the URL in the Basis column.

## The README demo

`assets/demo/terminal-light.svg` and `terminal-dark.svg` are generated from the real output of the four scripts on `design/demo/department-blueprint.json`; do not edit them. The README shows only `terminal-dark.svg`. Every image in the README either brings its own background or is transparent and reads on both GitHub page colours, because the browser picks a `<picture>` source by the computer's colour scheme while GitHub draws the page in the GitHub theme. `tests/test_readme.py` checks this, and `assets/brand/BRAND.md` explains it. The "How it works" diagram, `assets/brand/how-it-works.svg`, is the transparent kind: change `design/brand/tools/build_how_it_works.py` and rerun it, never the SVG. The light variant is for pages that set their own background. Rebuild with `python3 design/demo/build_demo.py` from the repository root. The build fails while a catalog entry used by that blueprint is stale (lint reports W1): refresh the catalog first.

## Running the checks

Python 3.11 or newer, no packages to install.

```bash
python3 -m unittest discover -s tests -t . -v
python3 plugins/airgap-anything/skills/airgap-architect/scripts/lint.py --catalog-only
```

Both must pass. Warnings (codes that start with W) do not fail the build.

## The documentation site

The site in `docs-site/` shows every catalog entry, the GPU table, the interview questions, the scripts, the lint codes, this guide and a worked example. Those pages are generated from the files they describe, so after you change a catalog entry, a GPU row, the design spec, `references/interview.md`, the demo blueprint, the README's Install section or this file, run:

```bash
python3 docs-site/scripts/generate_reference.py
```

and commit the pages it writes. The tests fail when a page is out of date. To preview the site you need Node.js 24: `cd docs-site && npm ci && npm run dev`.
