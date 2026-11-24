# Fetching

Fetching is the only step that downloads, and it runs on the connected workstation. Everything here is a command line from the tool's own documentation (sources at the end); fill in the values from the transfer manifest and the plan file, and change nothing else.

## Contents

- The approval rule
- When time is short
- Only the plan's items
- Commands per item kind
- Checking what arrived
- The tools and their sources

## The approval rule

Nothing is downloaded until the user has approved the plan in this conversation. Preparing a transfer ends at the plan.

When the plan is written, send one message with these parts, in this order, and end your turn:

1. The item count by kind (images, models, packages, project files, manual items).
2. The tools the commands use (`skopeo` or `docker`, `hf`, `curl`, `sha256sum`).
3. The bundle folder.
4. The sizes you know, and what is still unknown.
5. The question: "May I run the fetch commands, or will you run them yourself?"

Until the user answers yes to that message, fetch nothing into the bundle, a temporary folder or the Docker engine: no image, layer or blob, no `docker pull`, no package, no checksum file, no `git clone`, no bandwidth test, no single item "to test the commands", and nothing started in the background. Reading a model's page to find a commit hash is not a download. A changed plan needs a new yes.

| Thought | Reality |
|---|---|
| "The user asked me to prepare everything on the list" | That request is why you plan. The approval is a yes to the plan you showed. |
| "I'll start the downloads in the background while I write the rest" | A background download is a download. |
| "Only a clone, a bandwidth test, one image to try the commands" | Each one is a download. |
| "We leave in an hour" | The plan is one message. The approved commands are the fastest route there is. |

## When time is short

"Skip the checksums" and "just give me a `docker save` one-liner" have one answer: show the plan, and after the yes run the commands below. They pin every image to the manifest's platform and record its digest, check every package against its publisher's checksums, and `SHA256SUMS` covers every file. None of this adds a step for the user. Without a checksum list, nothing inside the network can tell a damaged copy from a good one, and a damaged file found inside costs another trip. Writing down that the checksums were skipped does not make the bundle checkable.

## Only the plan's items

Every image reference, model repository and commit, URL and file name comes from the transfer manifest and the plan file, at the manifest's version: no file from a branch such as `main` when the manifest pins a release. A file the manifest does not name goes in only as a manual item the user adds (`references/questions.md`).

## Commands per item kind

`B` is the bundle folder and `ARCH` the architecture of the manifest's `Platform:` line (`amd64` or `arm64`). `NAME` is the image reference with every character other than letters, digits, `.`, `_` and `-` replaced by `_` (`vllm/vllm-openai:v0.34.0` becomes `vllm_vllm-openai_v0.34.0`). Stop when free space in `B` falls below 1 GiB (`df -h B`).

Run each item on its own and record it in the plan's items table as `fetched` or `failed`, with the error (a project file is `copied`). A failed item does not stop the others; running its commands again fetches it again.

### Images, with `skopeo` (preferred: it needs no Docker daemon)

```sh
mkdir -p B/images/COMPONENT
skopeo --override-os linux --override-arch "ARCH" copy "docker://REF" "docker-archive:B/images/COMPONENT/NAME.tar:REF"
skopeo --override-os linux --override-arch "ARCH" inspect --no-tags --format '{{.Digest}}' "docker://REF" > B/images/COMPONENT/NAME.digest
```

The archive is single-platform and `docker load` accepts it; the tag after the second colon keeps the image's name. An image whose digest file is empty has failed.

### Images, with `docker`

```sh
mkdir -p B/images/COMPONENT
docker image pull --platform "linux/ARCH" "REF"
docker image save --platform "linux/ARCH" --output "B/images/COMPONENT/NAME.tar" "REF"
docker image inspect --format '{{.RepoDigests}}' "REF" > B/images/COMPONENT/NAME.digest
```

### Models from Hugging Face

```sh
hf download "REPO" --revision "REVISION" --local-dir "B/models/MODEL" --include "*.safetensors" --include "*.json" --include "*.txt" --include "*.model" --include "*.tiktoken" --include "*.jinja" --include "*.md" --include "LICENSE*" --include "LICENCE*"
```

The filter takes safetensors weights, configuration, tokenizer, template and license files, and leaves out pickle-based weights. For a model whose pickle files the user allowed, add `--include "*.bin" --include "*.pt" --include "*.pth" --include "*.pkl"`. A model folder without a `.safetensors` file has failed, unless pickle files were allowed and arrived. A token comes only from `HF_TOKEN` in the environment; never write it into a command or a file.

A local model: `cp -R "PATH/." "B/models/MODEL/"`.

### Packages

```sh
mkdir -p B/packages/COMPONENT/checksums
curl --fail --location --silent --show-error --output "B/packages/COMPONENT/FILE" "URL"
curl --fail --location --silent --show-error --output "B/packages/COMPONENT/checksums/SUMSFILE" "CHECKSUMS_URL"
```

The second line only when the manifest names a publisher checksum file for the package; `SUMSFILE` is the last part of its URL.

**Project files.** A manifest row whose source is a path in the project (for example `docs/airgap/agents/qwen-code/`) is copied into the bundle under `files/` with its folder structure, and its files go into `SHA256SUMS` like any other. Nothing is downloaded.

## Checking what arrived

1. **Publisher checksums.** For each package with a checksum file, in `B/packages/COMPONENT/`, check it with the tool that matches the algorithm (the line names it, or the hash length tells: 32 hex characters md5, 64 SHA-256, 128 SHA-512):

   ```sh
   cd B/packages/COMPONENT && sha256sum -c --ignore-missing checksums/SUMSFILE
   ```

   `--ignore-missing` skips the other files the publisher lists, so only the downloaded file is checked; when the list does not name it, the command fails with "no file was verified". Use `md5sum` or `sha512sum` the same way for the other algorithms. A mismatch: delete the file, record the item as failed, and stop. A package without a publisher checksum file is recorded as such in the inventory: its first hash is the one taken on the connected side.
2. **Pickle files.** `find B/models \( -name '*.bin' -o -name '*.pt' -o -name '*.pth' -o -name '*.pkl' \)` lists nothing, except in the folders of models whose pickle files the user allowed.
3. **Digests.** Every `.digest` file holds a digest (`sha256:` followed by 64 hex characters).

## The tools and their sources

Every command line above was taken from these pages; a changed line needs its page read again.

| Tool | Command | Source |
|---|---|---|
| `skopeo` | `copy` with `--override-os` and `--override-arch` into `docker-archive:` | https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/skopeo-copy.1.md, https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/skopeo.1.md, https://github.com/podman-container-tools/container-libs/blob/image/v5.42.1/image/docs/containers-transports.5.md |
| `skopeo` | `inspect --no-tags --format '{{.Digest}}'` | https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/skopeo-inspect.1.md |
| `docker` | `image pull --platform` | https://docs.docker.com/reference/cli/docker/image/pull/ |
| `docker` | `image save --platform --output` | https://docs.docker.com/reference/cli/docker/image/save/ |
| `docker` | `image inspect --format '{{.RepoDigests}}'` | https://docs.docker.com/reference/cli/docker/image/inspect/ |
| `docker` | `image load --input` (inside) | https://docs.docker.com/reference/cli/docker/image/load/ |
| `hf` | `download REPO --revision --local-dir --include` (one `--include` per pattern) | https://huggingface.co/docs/huggingface_hub/v2.4.0/en/guides/cli, https://huggingface.co/docs/huggingface_hub/v2.4.0/en/package_reference/cli |
| `sha256sum`, `md5sum`, `sha512sum` | `-c` reads `HASH  FILE` lines and exits non-zero when a listed file cannot be read or does not match; `--quiet` prints only failures; `--ignore-missing` skips listed files that are absent | https://github.com/coreutils/coreutils/blob/v9.12/doc/coreutils.texi (sections "cksum invocation" and "md5sum invocation"), https://www.gnu.org/software/coreutils/manual/html_node/sha2-utilities.html |
| `split` | `-b SIZE` bytes per part, `-a 3` three-digit suffixes, `--numeric-suffixes=1` counting from 1 | https://github.com/coreutils/coreutils/blob/v9.12/doc/coreutils.texi (section "split invocation") |

The downloads under Packages, with the options `--fail --location --silent --show-error --output`: https://curl.se/docs/manpage.html
