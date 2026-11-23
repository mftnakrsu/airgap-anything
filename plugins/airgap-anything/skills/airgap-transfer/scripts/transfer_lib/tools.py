"""The tools fetch.sh runs on the connected side, and the command lines it uses.

Every command line comes from the tool's own documentation, read when this file was
written, with the page in `source` (principle "nothing from memory"). A line is a
shell snippet that may use only the variables in `uses`; fetch.sh sets them before
it runs the line. references/fetch.md repeats each source.
"""
from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass

COPIER = "skopeo"  # the daemonless image copier, preferred over the Docker CLI
IMAGE_TOOLS = (COPIER, "docker")
HASH_TOOLS = {
    "md5": ("md5sum", "md5"),
    "sha256": ("sha256sum", "shasum"),
    "sha512": ("sha512sum", "shasum"),
}


@dataclass(frozen=True)
class Command:
    tool: str
    does: str
    uses: tuple[str, ...]
    line: str
    source: str


# Pages read on 2026-11-23. skopeo v1.25.2 (the repository moved from containers/ to
# podman-container-tools/), containers-transports(5) of go.podman.io/image v5.42.1 (the
# version skopeo v1.25.2 builds with), Docker CLI and Engine API v1.57, huggingface_hub
# v2.4.0, curl 8.23.1, GNU coreutils 9.12, macOS md5(1) of text_cmds-199, shasum of perl.
_SKOPEO = "https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/"
_DOCKER = "https://docs.docker.com/reference/cli/docker/image/"
_COREUTILS = "https://www.gnu.org/software/coreutils/manual/html_node/"
# Pages the lines also rely on (references/fetch.md lists them with each key):
#   skopeo global options --override-os/--override-arch: https://github.com/podman-container-tools/skopeo/blob/v1.25.2/docs/skopeo.1.md
#   docker-archive: transport: https://github.com/podman-container-tools/container-libs/blob/image/v5.42.1/image/docs/containers-transports.5.md
#   fields Id and RepoDigests of `docker image inspect`: https://docs.docker.com/reference/api/engine/version/v1.57.yaml (ImageInspect)
#   untagged output "checksum, a space, a flag, and the file name": https://github.com/coreutils/coreutils/blob/v9.12/doc/coreutils.texi (cksum output modes)
#   `cut -d ' ' -f 1`: https://pubs.opengroup.org/onlinepubs/9799919799/utilities/cut.html
# Hash lines read the file on standard input so that no file name (and no escaped one) is printed.

COMMANDS: dict[str, Command] = {
    "skopeo.copy": Command(
        "skopeo",
        "copy the image $ref for linux/$ARCH into a single-platform archive at $out that docker load accepts",
        ("$ref", "$ARCH", "$out"),
        'skopeo --override-os linux --override-arch "$ARCH" copy "docker://$ref" "docker-archive:$out:$ref"',
        _SKOPEO + "skopeo-copy.1.md",
    ),
    "skopeo.digest": Command(
        "skopeo",
        "print the registry digest (sha256:...) of $ref for linux/$ARCH",
        ("$ref", "$ARCH"),
        "skopeo --override-os linux --override-arch \"$ARCH\" inspect --no-tags --format '{{.Digest}}' \"docker://$ref\"",
        _SKOPEO + "skopeo-inspect.1.md",
    ),
    "docker.pull": Command(
        "docker",
        "pull $ref for $PLATFORM",
        ("$ref", "$PLATFORM"),
        'docker image pull --platform "$PLATFORM" "$ref"',
        _DOCKER + "pull/",
    ),
    "docker.save": Command(
        "docker",
        "write $ref for $PLATFORM as a single-platform archive at $out",
        ("$ref", "$PLATFORM", "$out"),
        'docker image save --platform "$PLATFORM" --output "$out" "$ref"',
        _DOCKER + "save/",
    ),
    "docker.digest": Command(
        "docker",
        "print the registry digest (sha256:...) of the pulled $ref",
        ("$ref",),
        "docker image inspect --format '{{.RepoDigests}}' \"$ref\"",
        _DOCKER + "inspect/",
    ),
    "docker.load": Command(
        "docker",
        "load the image archive $archive (used by load.sh inside)",
        ("$archive",),
        'docker image load --input "$archive"',
        _DOCKER + "load/",
    ),
    "docker.image_id": Command(
        "docker",
        "print the image ID (sha256:...) of the loaded image $expected (used by load.sh inside)",
        ("$expected",),
        "docker image inspect --format '{{.Id}}' \"$expected\"",
        _DOCKER + "inspect/",
    ),
    "hf.download": Command(
        "hf",
        "download the files of $repo matching $include_args at commit $revision into the folder $dest",
        ("$repo", "$revision", "$dest", "$include_args"),
        # $include_args is unquoted on purpose: it holds one `--include PATTERN` per pattern.
        'hf download "$repo" --revision "$revision" --local-dir "$dest" $include_args',
        "https://huggingface.co/docs/huggingface_hub/v2.4.0/en/guides/cli",
    ),
    "hf.include": Command(
        "hf",
        "the option that names one file pattern for hf.download; fetch.sh repeats it per pattern",
        (),
        "--include",
        "https://huggingface.co/docs/huggingface_hub/v2.4.0/en/package_reference/cli",
    ),
    "curl.download": Command(
        "curl",
        "download $url to the file $out, failing on an HTTP error",
        ("$url", "$out"),
        'curl --fail --location --silent --show-error --output "$out" "$url"',
        "https://curl.se/docs/manpage.html",
    ),
    "md5sum.hash": Command(
        "md5sum", "print only the md5 of $file", ("$file",),
        "md5sum < \"$file\" | cut -d ' ' -f 1", _COREUTILS + "md5sum-invocation.html",
    ),
    "md5.hash": Command(
        "md5", "print only the md5 of $file", ("$file",),
        'md5 -q "$file"', "https://github.com/apple-oss-distributions/text_cmds/blob/text_cmds-199/md5/md5.1",
    ),
    "sha256sum.hash": Command(
        "sha256sum", "print only the SHA-256 of $file", ("$file",),
        "sha256sum < \"$file\" | cut -d ' ' -f 1", _COREUTILS + "sha2-utilities.html",
    ),
    "shasum.sha256": Command(
        "shasum", "print only the SHA-256 of $file", ("$file",),
        "shasum -a 256 < \"$file\" | cut -d ' ' -f 1", "https://perldoc.perl.org/shasum",
    ),
    "sha512sum.hash": Command(
        "sha512sum", "print only the SHA-512 of $file", ("$file",),
        "sha512sum < \"$file\" | cut -d ' ' -f 1", _COREUTILS + "sha2-utilities.html",
    ),
    "shasum.sha512": Command(
        "shasum", "print only the SHA-512 of $file", ("$file",),
        "shasum -a 512 < \"$file\" | cut -d ' ' -f 1", "https://perldoc.perl.org/shasum",
    ),
}

# The commands load.sh runs inside; pack.py writes their lines into its copy of the template.
TEMPLATE_COMMANDS = ("docker.load", "docker.image_id")

# Which command computes which hash with which tool.
HASH_COMMANDS = {
    ("md5", "md5sum"): "md5sum.hash",
    ("md5", "md5"): "md5.hash",
    ("sha256", "sha256sum"): "sha256sum.hash",
    ("sha256", "shasum"): "shasum.sha256",
    ("sha512", "sha512sum"): "sha512sum.hash",
    ("sha512", "shasum"): "shasum.sha512",
}


class MissingToolError(Exception):
    def __init__(self, missing: dict[str, list[str]]):
        lines = [f"{tool} (needed for {', '.join(needs)})" for tool, needs in missing.items()]
        super().__init__("missing tools: " + "; ".join(lines))
        self.missing = missing


def find_tools(items: list[dict], which: Callable[[str], str | None] = shutil.which) -> dict:
    """The tool chosen for each job the items need; MissingToolError when one is absent."""
    tools: dict[str, str] = {}
    missing: dict[str, list[str]] = {}

    def need(job: str, candidates: tuple[str, ...], users: list[str]) -> None:
        if not users:
            return
        found = next((name for name in candidates if which(name)), None)
        if found:
            tools[job] = found
        else:
            missing[" or ".join(candidates)] = users

    def ids(kind, test=lambda item: True):
        return [item["id"] for item in items if item["kind"] == kind and test(item)]

    need("images", IMAGE_TOOLS, ids("image"))
    need("models", ("hf",), ids("model", lambda item: item["source"].get("source") == "huggingface"))
    packages = ids("package")
    need("packages", ("curl",), packages)
    listed = ids("package", lambda item: bool(item.get("checksums")))
    for algorithm, candidates in HASH_TOOLS.items():
        need(f"hash.{algorithm}", candidates, listed)
    if missing:
        raise MissingToolError(missing)
    return tools
