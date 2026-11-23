"""What an image archive holds: the image ID and platform that docker load will see.

The archive layout is the "Combined Image JSON + Filesystem Changeset Format" of the
Docker Image Specification v1.3.0 (the v1 layout is still used "in `docker save` and
`docker load`"): a top-level manifest.json, an array with "an entry in the array for
each image", whose `Config` "references another file in the tar which includes the
image JSON" and whose `RepoTags` "lists references pointing to this image"; the image
JSON gives `os` and `architecture`, and "each image's ID is given by the SHA256 hash of
its configuration JSON".
  https://github.com/moby/docker-image-spec/blob/main/spec.md
  https://github.com/moby/docker-image-spec/blob/main/README.md
Since Docker Engine 25.0 "the `docker image save` tarball output is now OCI compliant"
(https://docs.docker.com/engine/release-notes/25.0/); the engine still writes
manifest.json next to index.json, with `Config` at blobs/sha256/<digest>
(moby daemon/internal/image/tarexport/save.go and daemon/containerd/image_exporter.go,
https://github.com/moby/moby/blob/8b0c45e42959ea5322cfb33bfb97a40ed64d4a07/daemon/internal/image/tarexport/save.go,
https://github.com/moby/moby/blob/8b0c45e42959ea5322cfb33bfb97a40ed64d4a07/daemon/containerd/image_exporter.go).
skopeo's docker-archive transport writes "the docker-save(1) formatted file" and, read
without a reference, "the archive must contain exactly one image"
(https://github.com/containers/image/blob/main/docs/containers-transports.5.md).
The CLI pages say only "Produces a tarred repository" and "It restores both images and
tags" (https://docs.docker.com/reference/cli/docker/image/save/,
https://docs.docker.com/reference/cli/docker/image/load/).
"""
from __future__ import annotations

import hashlib
import json
import tarfile
from pathlib import Path


class ArchiveError(Exception):
    """The file is not a single-image archive that docker load accepts."""


def read_image_archive(path: Path) -> dict:
    """{"id": "sha256:...", "platform": "linux/amd64", "tags": [...]} of a one-image archive."""
    path = Path(path)
    try:
        with tarfile.open(path, mode="r:") as tar:
            manifest = json.load(tar.extractfile("manifest.json"))
            if not isinstance(manifest, list) or len(manifest) != 1:
                count = len(manifest) if isinstance(manifest, list) else "no"
                raise ArchiveError(f"{path.name}: holds {count} images; one was expected")
            config_bytes = tar.extractfile(manifest[0]["Config"]).read()
        config = json.loads(config_bytes)
        if not isinstance(config, dict):
            raise TypeError("the image config is not a JSON object")
        tags = list(manifest[0].get("RepoTags") or [])
    except (tarfile.TarError, KeyError, AttributeError, TypeError, ValueError, OSError, RecursionError) as error:
        raise ArchiveError(f"{path.name}: not an image archive docker load reads ({error})") from None
    return {
        "id": "sha256:" + hashlib.sha256(config_bytes).hexdigest(),
        "platform": f"{config.get('os', '')}/{config.get('architecture', '')}",
        "tags": tags,
    }
