"""fetch.sh: the download script for the connected side (design spec section 8.4)."""
from __future__ import annotations

from .constants import FETCH_LOG, FETCH_STATE_DIR, MODEL_FILE_PATTERNS, PICKLE_PATTERNS
from .items import checksums_path
from .tools import COMMANDS, HASH_COMMANDS

MIN_FREE_KB = 1024 * 1024  # stop when less than 1 GiB is left in the bundle folder


def sh_quote(value: str) -> str:
    """One shell word, single-quoted."""
    return "'" + str(value).replace("'", "'\\''") + "'"


def _line(key: str) -> str:
    return COMMANDS[key].line


def _hash_function(tools: dict) -> list[str]:
    lines = [
        "hash_file() {  # hash_file LENGTH FILE: print the hex digest of FILE whose length is LENGTH",
        '  file=$2',
        '  case $1 in',
    ]
    for length, algorithm in (("32", "md5"), ("64", "sha256"), ("128", "sha512")):
        tool = tools.get(f"hash.{algorithm}")
        if tool:
            lines.append(f"    {length}) {_line(HASH_COMMANDS[(algorithm, tool)])} ;;")
    lines += ["    *) return 1 ;;", "  esac", "}"]
    return lines


_COMMON = r"""log() {  # log STATUS TEXT: one line in fetch.log and on the screen
  printf '%s %s\n' "$1" "$2" >> "$LOG"
  printf '%s %s\n' "$1" "$2"
}

fail() {  # fail TEXT: count a failed item and go on with the next one
  log FAILED "$1"
  FAILED=$((FAILED + 1))
  FAILURES="$FAILURES
  $1"
}

room() {  # stop the whole run on a full disk
  free=$(df -Pk "$BUNDLE" | awk 'NR == 2 { print $4 }')
  if [ "$free" -lt __MIN_FREE_KB__ ]; then
    log FAILED "disk full: less than 1 GiB left in $BUNDLE"
    exit 1
  fi
}

listed_hash() {  # listed_hash LIST NAME: "TAG HASH" for NAME in LIST; TAG is the algorithm named in a "TAG (name) = hash" line, - in other formats
  awk -v name="$2" '
    $1 ~ /^[0-9A-Fa-f]+$/ && NF >= 2 { f = $2; sub(/^\*/, "", f); g = f; sub(/.*\//, "", g); if (f == name || g == name) { print "-", tolower($1); exit } }
    $2 ~ /^\(/ && $(NF - 1) == "=" { f = $2; sub(/^\(/, "", f); sub(/\)$/, "", f); if (f == name) { print toupper($1), tolower($NF); exit } }
    NF == 1 && $1 ~ /^[0-9A-Fa-f]+$/ { only = tolower($1); count++ }
    END { if (count == 1 && NR == 1) print "-", only }
  ' "$1"
}
"""


def _local_copy() -> str:
    """Copy from a local model folder only the files the filter allows (and the pickle files
    when ALLOW_PICKLE is yes), each to the same relative path; .git folders are skipped. The
    filter is a `case` in a child shell, so no pattern is ever expanded against a folder."""
    allowed = "|".join(MODEL_FILE_PATTERNS)
    pickle = "|".join(PICKLE_PATTERNS)
    return (
        '    find -H "$4" -name .git -prune -o \\( -type f -o -type l \\) -exec sh -c \'\n'
        "      src=${1%/}; dest=$2; pickle=$3; shift 3\n"
        "      for file; do\n"
        '        [ -f "$file" ] || continue\n'
        '        rel=${file#"$src"/}; [ "$rel" != "$file" ] || exit 1\n'
        "        case ${rel##*/} in\n"
        f"          {allowed}) ;;\n"
        f'          {pickle}) [ "$pickle" = yes ] || continue ;;\n'
        "          *) continue ;;\n"
        "        esac\n"
        '        mkdir -p "$dest/$(dirname "$rel")" && cp "$file" "$dest/$rel" || exit 1\n'
        "      done\n"
        "    \' sh \"$4\" \"$dest\" \"$6\" {} + || return 1\n"
    )


def _functions(plan: dict) -> str:
    tools = plan["tools"]
    parts = [_COMMON.replace("__MIN_FREE_KB__", str(MIN_FREE_KB))]
    parts.append("\n".join(_hash_function(tools)) + "\n")
    image_tool = tools.get("images")
    if image_tool:
        if image_tool == "docker":
            get = f"  {_line('docker.pull')} || return 1\n  {_line('docker.save')} || {{ rm -f \"$out\"; return 1; }}\n"
            digest = _line("docker.digest")
        else:
            get = f"  {_line(image_tool + '.copy')} || {{ rm -f \"$out\"; return 1; }}\n"
            digest = _line(image_tool + ".digest")
        parts.append(
            "fetch_image() {  # fetch_image REF ARCHIVE\n"
            '  ref=$1; archive="$BUNDLE/$2"; digest_file="${archive%.tar}.digest"\n'
            '  if [ -s "$archive" ] && [ -s "$digest_file" ]; then log OK "image $ref (already present)"; return 0; fi\n'
            "  room\n"
            '  mkdir -p "$(dirname "$archive")" || return 1\n'
            '  out="$archive.download"; rm -f "$out"\n'
            + get
            + f'  digest=$({digest} | sed -n \'s/.*\\(sha256:[0-9a-f]\\{{64\\}}\\).*/\\1/p\' | head -n 1)\n'
            '  if [ -z "$digest" ]; then rm -f "$out"; log FAILED "image $ref: no digest reported"; return 1; fi\n'
            '  mv "$out" "$archive" || return 1\n'
            "  printf '%s\\n' \"$digest\" > \"$digest_file\" || return 1\n"
            '  log OK "image $ref $digest"\n'
            "}\n"
        )
    if tools.get("models") or any(i["kind"] == "model" for i in plan["items"]):
        include = _line("hf.include") if tools.get("models") else ""
        parts.append(
            "fetch_model() {  # fetch_model NAME FOLDER SOURCE REPO_OR_PATH REVISION ALLOW_PICKLE\n"
            '  dest="$BUNDLE/$2"; done_file="$BUNDLE/' + FETCH_STATE_DIR + '/$(basename "$2").done"; key="$3 $4 $5 $6"\n'
            # The done file holds the key of what was fetched: source, repository or path,
            # revision and pickle setting. Another key means the folder holds something else;
            # it is never deleted here (it can be tens of GB, and hf keeps stale files), so the
            # item fails until the folder is deleted. Without the folder the marker is stale.
            '  if [ -f "$done_file" ]; then\n'
            '    held=$(cat "$done_file")\n'
            '    if [ "$held" = "$key" ]; then log OK "model $1 (already present)"; return 0; fi\n'
            '    if [ -d "$dest" ]; then log FAILED "model $1: $2 holds $held; delete it to fetch $key"; return 1; fi\n'
            "  fi\n"
            "  room\n"
            '  mkdir -p "$dest" "$BUNDLE/' + FETCH_STATE_DIR + '" || return 1\n'
            '  patterns="' + " ".join(MODEL_FILE_PATTERNS) + '"\n'
            '  if [ "$6" = yes ]; then patterns="$patterns ' + " ".join(PICKLE_PATTERNS) + '"; fi\n'
            '  if [ "$3" = local ]; then\n'
            + _local_copy()
            + "  else\n"
            '    repo=$4; revision=$5; include_args=""\n'
            f'    for pattern in $patterns; do include_args="$include_args {include} $pattern"; done\n'
            + (f"    {_line('hf.download')} || return 1\n" if tools.get("models") else "    return 1\n")
            + "  fi\n"
            '  if [ "$6" != yes ] && [ -z "$(find "$dest" -type f -name \'*.safetensors\' | head -n 1)" ]; then\n'
            '    log FAILED "model $1: no safetensors weights; allow pickle files for it in transfer.json or choose another source"\n'
            "    return 1\n"
            "  fi\n"
            '  printf \'%s\\n\' "$key" > "$done_file" || return 1\n'
            '  log OK "model $1 $5"\n'
            "}\n"
        )
    if tools.get("packages"):
        parts.append(
            "fetch_package() {  # fetch_package FILE PATH URL CHECKSUMS_URL CHECKSUMS_PATH\n"
            '  name=$1; target="$BUNDLE/$2"\n'
            '  if [ -s "$target" ]; then log OK "package $name (already present)"; return 0; fi\n'
            "  room\n"
            '  mkdir -p "$(dirname "$target")" || return 1\n'
            '  url=$3; out="$target.download"; rm -f "$out"\n'
            f"  {_line('curl.download')} || {{ rm -f \"$out\"; return 1; }}\n"
            '  if [ -n "$4" ]; then\n'
            '    list="$BUNDLE/$5"; mkdir -p "$(dirname "$list")" || return 1\n'
            '    url=$4; out_file=$out; out="$list.download"\n'
            f"    {_line('curl.download')} || {{ rm -f \"$out\" \"$out_file\"; return 1; }}\n"
            '    mv "$out" "$list" || return 1\n'
            '    out=$out_file\n'
            '    listing=$(listed_hash "$list" "$name")\n'
            '    if [ -z "$listing" ]; then rm -f "$out"; log FAILED "package $name: not listed in $4"; return 1; fi\n'
            '    tag=${listing%% *}; expected=${listing#* }\n'
            # Only md5, sha256 and sha512 can be checked. A "TAG (name) = hash" line names its
            # algorithm; any tag but those is unsupported even when the length fits (BLAKE2b is
            # as long as SHA-512, SHA3-256 as SHA-256). A plain list names none, so its length
            # decides, except that a list called B2SUMS or *b2* or *sha3* is one of the others.
            # Such a file says nothing about the download, so it stays, as .download and never
            # as the finished file, and only this item fails.
            '    why=""\n'
            "    case $tag in\n"
            "      MD5|SHA256|SHA512|SHA2-256|SHA2-512) ;;\n"
            "      -) case $(printf '%s' \"${4##*/}\" | tr 'A-Z' 'a-z') in *b2*|*sha3*) why=\"a list called ${4##*/}\" ;; esac ;;\n"
            '      *) why="the tag $tag" ;;\n'
            "    esac\n"
            '    case ${#expected} in 32|64|128) ;; *) why="a hash of ${#expected} characters" ;; esac\n'
            '    if [ -n "$why" ]; then\n'
            '      log FAILED "package $name: unsupported checksum algorithm ($why in $4; only md5, sha256 and sha512 are checked); the file was kept unverified as $out"\n'
            "      return 1\n"
            "    fi\n"
            '    actual=$(hash_file "${#expected}" "$out" | tr "A-F" "a-f") || actual=""\n'
            '    if [ "$actual" != "$expected" ]; then\n'
            '      rm -f "$out"\n'
            '      log FAILED "package $name: checksum does not match $4; the file was deleted"\n'
            "      exit 1\n"
            "    fi\n"
            "  fi\n"
            '  mv "$out" "$target" || return 1\n'
            '  log OK "package $name"\n'
            "}\n"
        )
    return "\n".join(parts)


def _calls(plan: dict) -> list[str]:
    calls = []
    for item in plan["items"]:
        if item["kind"] == "image":
            calls.append(
                f"fetch_image {sh_quote(item['ref'])} {sh_quote(item['path'])} || fail {sh_quote('image ' + item['ref'])}"
            )
        elif item["kind"] == "model":
            source = item["source"]
            where = source.get("repo") if source.get("source") == "huggingface" else source.get("path")
            calls.append(
                "fetch_model "
                + " ".join(
                    sh_quote(value)
                    for value in (
                        item["name"],
                        item["path"],
                        source.get("source", ""),
                        where or "",
                        source.get("revision", ""),
                        "yes" if item.get("allow_pickle") else "no",
                    )
                )
                + f" || fail {sh_quote('model ' + item['name'])}"
            )
        elif item["kind"] == "package":
            calls.append(
                "fetch_package "
                + " ".join(
                    sh_quote(value)
                    for value in (item["file"], item["path"], item["url"], item["checksums"], checksums_path(item) or "")
                )
                + f" || fail {sh_quote('package ' + item['file'])}"
            )
    return calls


def render_fetch_script(plan: dict, platform: str, generated: str) -> str:
    """POSIX sh for the plan; `platform` is the manifest's, for example linux/amd64."""
    arch = platform.split("/", 1)[1]
    header = [
        "# fetch.sh: written by airgap-transfer's plan.py on " + generated + ". Do not edit it;",
        "# change the design or the answers and run plan.py again.",
        "# Downloads every item of the plan into this folder. Run it only after the plan",
        "# was approved: sh fetch.sh. A second run fetches only what is missing.",
        "set -eu",
        # The model file patterns (*.json, ...) are split from unquoted variables; with
        # pathname expansion on they would expand against the folder fetch.sh is run from.
        # Nothing in this script relies on expansion, so it is off from here on.
        "set -f",
        # CDPATH= keeps cd from printing the folder (and from doubling BUNDLE) when it is exported.
        'BUNDLE=$(CDPATH= cd -P -- "$(dirname -- "$0")" && pwd)',
        f'LOG="$BUNDLE/{FETCH_LOG}"',
        f"PLATFORM={sh_quote(platform)}",
        f"ARCH={sh_quote(arch)}",
        "FAILED=0",
        'FAILURES=""',
        "",
    ]
    footer = [
        "",
        'if [ "$FAILED" -gt 0 ]; then',
        "  printf 'fetch.sh: %s item(s) failed:%s\\nRun sh fetch.sh again to fetch only those.\\n' \"$FAILED\" \"$FAILURES\" >&2",
        "  exit 1",
        "fi",
        'log OK "every item is in $BUNDLE; next: pack.py"',
        "",
    ]
    return "\n".join(header) + _functions(plan) + "\n" + "\n".join(_calls(plan)) + "\n" + "\n".join(footer)
