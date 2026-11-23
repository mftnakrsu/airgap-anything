# fetch.sh

`plan.py` writes `<bundle>/fetch.sh`. It is POSIX sh and runs on the connected workstation. It is the only thing that downloads.

## The approval rule

Nothing is downloaded until the user has approved the plan in this conversation. Preparing a transfer ends at the plan.

When `plan.py` exits 0, send one message with these parts, in this order, and end your turn:

1. The item count by kind, from the `Plan:` line of `plan.py`.
2. The tools `plan.py` chose, from its `Tools:` line.
3. The bundle folder.
4. The known sizes, from its `Known sizes` lines.
5. The question: "May I run `sh <bundle>/fetch.sh`, or will you run it yourself?"

Until the user answers yes to that message:

- Fetch nothing into the bundle, a temporary folder or the Docker engine: no image, layer or blob, no `docker pull`, no package, no checksum file, no `git clone`, no range request or bandwidth test, no single item "to test the script". Reading a model's page to find a commit hash is not a download.
- Start nothing in the background that downloads.

`plan.py` itself reads only the project's files; it needs no network. A new `plan.py` run needs a new approval when the items changed.

| Thought | Reality |
|---|---|
| "The user asked me to prepare everything on the list" | That request is why you plan. The approval is a yes to the plan you showed. |
| "I'll start the downloads in the background while I write the rest" | A background download is a download. |
| "Only a clone, a bandwidth test, one image to try the script" | Each one is a download. |
| "We leave in an hour" | The plan is one message. The approved `fetch.sh` is the fastest route there is. |

## When time is short

"Skip the checksums" and "just give me a one-liner" have one answer: show the plan, and after the yes the one command is `sh <bundle>/fetch.sh`. It pins every image to the manifest's platform, records each image's registry digest, and checks every package against the publisher's checksum file as it arrives. Then `pack.py` writes `SHA256SUMS`, and `verify.sh` checks every file against it inside. You run no extra step for any of this.

The checksum list is not optional. Writing down that the checksums were skipped does not make the bundle checkable: inside the network nothing can then tell a damaged copy from a good one, and a damaged file found inside costs another trip.

## Only the plan's items

Every image reference, model repository and commit, URL and file name `fetch.sh` uses comes from `transfer-manifest.json` and `transfer.json`, at the manifest's version. Fetch nothing beside them yourself: no file from a branch such as `main` when the manifest pins a release. A file the manifest does not name goes in only as a manual item the user adds (`references/questions.md`, "Manual items").

## What it does

- `set -eu`; one function per item kind; every item logged as `OK` or `FAILED` in `<bundle>/fetch.log`.
- A failed download is logged and the script goes on with the other items, then exits 1 and lists the failures. Running it again fetches only what is missing.
- A file whose publisher checksum does not match is deleted, logged, and the script stops with exit 1. The checksum file may use md5, SHA-256 or SHA-512; the algorithm a line names, or else the length of the hash, tells which. A checksum file in another algorithm fails that item and leaves the download as `<file>.download`, unverified.
- Less than 1 GiB free in the bundle folder stops the script.
- Images are written as single-platform archives that `docker load` accepts, for the manifest's `platform`, with the registry digest in `<name>.digest` next to each archive. An image without a reported digest fails.
- Models are downloaded at the pinned commit. The model file filter takes safetensors weights, configuration, tokenizer and template files and licence files, and leaves out pickle-based weights (`.bin`, `.pt`, `.pth`, `.pkl`) unless `allow_pickle` is set for that model. A model without safetensors weights fails. A model folder that holds another repository, commit or pickle setting fails until the user deletes it.
- Packages are downloaded from `url`; the publisher's checksum file, when the manifest names one, is kept under `packages/<component>/checksums/` and carried with the package.
- A Hugging Face token comes only from `HF_TOKEN` in the environment. The script never writes it to a file.

## The tools and their commands

`plan.py` looks for these on `PATH` without running them, and exits 3 naming any that is missing and the items that need it. The image copier is preferred to the Docker CLI because it needs no daemon. The three `docker` commands marked "used by load.sh inside" are written into `load.sh` by `pack.py`. Every command line was taken from the page in the last column when it was written.

| Key | Tool | Does | Command line | Source |
|---|---|---|---|---|
| `skopeo.copy` | `skopeo` | copy the image $ref for linux/$ARCH into a single-platform archive at $out that docker load accepts | `skopeo --override-os linux --override-arch "$ARCH" copy "docker://$ref" "docker-archive:$out:$ref"` | https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/skopeo-copy.1.md |
| `skopeo.digest` | `skopeo` | print the registry digest (sha256:...) of $ref for linux/$ARCH | `skopeo --override-os linux --override-arch "$ARCH" inspect --no-tags --format '{{.Digest}}' "docker://$ref"` | https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/skopeo-inspect.1.md |
| `docker.pull` | `docker` | pull $ref for $PLATFORM | `docker image pull --platform "$PLATFORM" "$ref"` | https://docs.docker.com/reference/cli/docker/image/pull/ |
| `docker.save` | `docker` | write $ref for $PLATFORM as a single-platform archive at $out | `docker image save --platform "$PLATFORM" --output "$out" "$ref"` | https://docs.docker.com/reference/cli/docker/image/save/ |
| `docker.digest` | `docker` | print the registry digest (sha256:...) of the pulled $ref | `docker image inspect --format '{{.RepoDigests}}' "$ref"` | https://docs.docker.com/reference/cli/docker/image/inspect/ |
| `docker.load` | `docker` | load the image archive $archive (used by load.sh inside) | `docker image load --input "$archive"` | https://docs.docker.com/reference/cli/docker/image/load/ |
| `docker.image_id` | `docker` | print the image ID (sha256:...) of the loaded image $expected (used by load.sh inside) | `docker image inspect --format '{{.Id}}' "$expected"` | https://docs.docker.com/reference/cli/docker/image/inspect/ |
| `docker.store` | `docker` | print the storage driver status, which names io.containerd.snapshotter.v1 when the engine uses the containerd image store (used by load.sh inside) | `docker info -f '{{ .DriverStatus }}'` | https://docs.docker.com/engine/storage/containerd/ |
| `hf.download` | `hf` | download the files of $repo matching $include_args at commit $revision into the folder $dest | `hf download "$repo" --revision "$revision" --local-dir "$dest" $include_args` | https://huggingface.co/docs/huggingface_hub/v2.4.0/en/guides/cli |
| `hf.include` | `hf` | the option that names one file pattern for hf.download; fetch.sh repeats it per pattern | `--include` | https://huggingface.co/docs/huggingface_hub/v2.4.0/en/package_reference/cli |
| `curl.download` | `curl` | download $url to the file $out, failing on an HTTP error | `curl --fail --location --silent --show-error --output "$out" "$url"` | https://curl.se/docs/manpage.html |
| `md5sum.hash` | `md5sum` | print only the md5 of $file | `md5sum < "$file" \| cut -d ' ' -f 1` | https://www.gnu.org/software/coreutils/manual/html_node/md5sum-invocation.html |
| `md5.hash` | `md5` | print only the md5 of $file | `md5 -q "$file"` | https://github.com/apple-oss-distributions/text_cmds/blob/text_cmds-199/md5/md5.1 |
| `sha256sum.hash` | `sha256sum` | print only the SHA-256 of $file | `sha256sum < "$file" \| cut -d ' ' -f 1` | https://www.gnu.org/software/coreutils/manual/html_node/sha2-utilities.html |
| `shasum.sha256` | `shasum` | print only the SHA-256 of $file | `shasum -a 256 < "$file" \| cut -d ' ' -f 1` | https://perldoc.perl.org/shasum |
| `sha512sum.hash` | `sha512sum` | print only the SHA-512 of $file | `sha512sum < "$file" \| cut -d ' ' -f 1` | https://www.gnu.org/software/coreutils/manual/html_node/sha2-utilities.html |
| `shasum.sha512` | `shasum` | print only the SHA-512 of $file | `shasum -a 512 < "$file" \| cut -d ' ' -f 1` | https://perldoc.perl.org/shasum |

The lines also rely on these pages:

- The skopeo options `--override-os` and `--override-arch`: https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/skopeo.1.md
- The `docker-archive:` transport: https://github.com/podman-container-tools/container-libs/blob/image/v5.42.1/image/docs/containers-transports.5.md
- The fields `Id` and `RepoDigests` of `docker image inspect` (ImageInspect): https://docs.docker.com/reference/api/engine/version/v1.57.yaml
- The untagged output of the coreutils hash tools, "checksum, a space, a flag, and the file name": https://github.com/coreutils/coreutils/blob/v9.12/doc/coreutils.texi
- `cut -d ' ' -f 1`: https://pubs.opengroup.org/onlinepubs/9799919799/utilities/cut.html

## Image archives

`pack.py` reads `manifest.json` in each archive: it must name exactly one image, whose configuration names the manifest's platform. The image ID, the SHA-256 of that configuration, goes into `<name>.id`; `load.sh` checks it inside after `docker load`. The layout is described in https://github.com/moby/docker-image-spec/blob/main/spec.md and https://github.com/moby/docker-image-spec/blob/main/README.md.
