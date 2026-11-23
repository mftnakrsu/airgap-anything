"""Stub download tools for the fetch.sh tests, in a temporary folder that becomes the whole
PATH: the real skopeo, docker, hf or curl can never run, so no test touches the network.
The basic tools fetch.sh needs are linked into the same folder.

A stub does not parse the tool's options. It finds the argument that names a path inside
the bundle (BUNDLE in its environment) and writes a small file there, so the tests keep
working whatever exact options references/fetch.md records."""
from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

SYSTEM_TOOLS = (
    "sh", "dash", "awk", "sed", "df", "find", "head", "cut", "tr", "wc", "sort", "ls",
    "mkdir", "mv", "rm", "cp", "cat", "dirname", "basename",
    "sha256sum", "shasum", "md5sum", "md5", "sha512sum",
)

_FIND_TARGET = r'''
target=""
for arg in "$@"; do
  case $arg in
    *"$BUNDLE"/*) target=${arg#*"$BUNDLE"/}; target="$BUNDLE/${target%%:*}" ;;
  esac
done
'''

STUBS = {
    # An image copier: writes the archive it is asked for; prints a digest otherwise.
    "skopeo": "#!/bin/sh\n" + _FIND_TARGET + r'''
if [ -n "$target" ]; then
  [ -n "${STUB_FAIL_IMAGE:-}" ] && exit 1
  printf 'archive of %s\n' "$*" > "$target"
else
  echo "sha256:$(printf '%064d' 7)"
fi
''',
    # The Docker CLI: pull does nothing, save writes the archive, inspect prints a digest.
    "docker": "#!/bin/sh\n" + _FIND_TARGET + r'''
if [ -n "$target" ]; then printf 'archive\n' > "$target"; fi
case "$*" in *inspect*) echo "example@sha256:$(printf '%064d' 7)" ;; esac
''',
    # The Hugging Face CLI: fills the folder it is given with one weight and one config file.
    # STUB_HF_ARGS names a file that receives the arguments it was called with, one per line.
    "hf": "#!/bin/sh\n" + _FIND_TARGET + r'''
[ -n "${STUB_HF_ARGS:-}" ] && printf '%s\n' "$@" > "$STUB_HF_ARGS"
[ -n "${STUB_FAIL_MODEL:-}" ] && exit 1
mkdir -p "$target"
if [ -n "${STUB_PICKLE_ONLY:-}" ]; then printf 'w' > "$target/pytorch_model.bin"; else printf 'w' > "$target/model.safetensors"; fi
printf '{}' > "$target/config.json"
''',
    # curl: copies $STUB_FILES/<last part of the URL> to the file it is given; 22 when absent.
    "curl": "#!/bin/sh\n" + _FIND_TARGET + r'''
url=""
for arg in "$@"; do case $arg in https://*) url=$arg ;; esac; done
source="$STUB_FILES/${url##*/}"
[ -f "$source" ] || exit 22
cp "$source" "$target"
''',
}


def install_stubs(folder: Path, names=tuple(STUBS)) -> Path:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for tool in SYSTEM_TOOLS:
        found = shutil.which(tool)
        if found and not (folder / tool).exists():
            (folder / tool).symlink_to(found)
    for name in names:
        path = folder / name
        path.write_text(STUBS[name], encoding="utf-8")
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return folder


def stub_env(stubs: Path, bundle: Path, files: Path, **extra) -> dict:
    env = dict(os.environ, PATH=str(stubs),
               BUNDLE=str(Path(bundle).resolve()), STUB_FILES=str(files))
    env.update({key: str(value) for key, value in extra.items()})
    return env
