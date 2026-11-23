# verify.sh: written by airgap-transfer. Checks a bundle inside the network with POSIX sh
# and coreutils only: no Python, no network. Do not edit it.
#
#   sh verify.sh [bundle folder]
#
# Exit 0: every file is present and matches SHA256SUMS; the last line names the next step.
# Exit 1: a file is missing or damaged; MISSING.txt lists each one, its expected SHA-256,
#         the volume it was on and what to bring next time.
# Exit 2: wrong arguments, or the folder is not a bundle.
#
# Each file is hashed on its own with `sha256sum < FILE | cut -d ' ' -f 1` (coreutils: the
# untagged output is "checksum, a space, a flag, and the file name"). The script does not
# read the per-file lines of `sha256sum -c`: the coreutils manual (v9.12) does not specify
# their wording, and says a file name with problematic characters is printed quoted.
set -eu

if [ "$#" -gt 1 ]; then
  echo "usage: sh verify.sh [bundle folder]" >&2
  exit 2
fi
DIR=${1:-.}
if [ ! -d "$DIR" ]; then
  echo "verify.sh: $DIR is not a folder" >&2
  exit 2
fi
cd "$DIR"
for name in SHA256SUMS VOLUMES.txt PARTS.txt; do
  if [ ! -f "$name" ]; then
    echo "verify.sh: $name is missing, so $DIR is not a bundle folder" >&2
    exit 2
  fi
done
rm -f MISSING.txt .verified
MISSING=0
TOTAL=$(awk '$1 !~ /^#/ && $1 + 0 > n { n = $1 + 0 } END { print n + 0 }' VOLUMES.txt)

hash_of() {  # hash_of FILE: the SHA-256 of FILE
  sha256sum < "$1" | cut -d ' ' -f 1
}

missing() {  # missing PATH SHA256 VOLUME BRING
  if [ "$MISSING" -eq 0 ]; then
    printf 'file\texpected sha256\tvolume\tbring next time\n' > MISSING.txt
  fi
  printf '%s\t%s\t%s\t%s\n' "$1" "$2" "$3" "$4" >> MISSING.txt
  MISSING=$((MISSING + 1))
}

volume_of() {  # volume_of PATH: the volume(s) a file, or the parts of a split file, came on
  awk -v p="$1" '$1 !~ /^#/ { f = $0; sub(/^[^ ]+ [^ ]+ [^ ]+ /, "", f); g = f; sub(/\.part[0-9][0-9][0-9]$/, "", g); if ((f == p || g == p) && index("," v ",", "," $1 ",") == 0) v = v (v == "" ? "" : ",") $1 } END { print v }' VOLUMES.txt
}

part_of() {  # part_of PATH N: the name of part N of PATH
  printf '%s.part%03d' "$1" "$2"
}

# 1. Every whole file and every part of VOLUMES.txt is there; each part is hashed now.
#    A part may be gone because an earlier run joined it into its file.
while read -r volume size hash path; do
  case $volume in '#'* | '') continue ;; esac
  case $path in
    *.part[0-9][0-9][0-9])
      if [ ! -f "$path" ]; then
        [ -f "${path%.part[0-9][0-9][0-9]}" ] && continue
        missing "$path" "$hash" "$volume" "volume $volume of $TOTAL"
      elif [ "$(hash_of "$path")" != "$hash" ]; then
        missing "$path" "$hash" "$volume" "a new copy of volume $volume of $TOTAL"
      fi
      ;;
    *)
      if [ ! -f "$path" ]; then
        missing "$path" "$hash" "$volume" "volume $volume of $TOTAL"
      elif [ "$(wc -c < "$path" | tr -d ' ')" != "$size" ]; then
        missing "$path" "$hash" "$volume" "a new copy of volume $volume of $TOTAL"
      fi
      ;;
  esac
done < VOLUMES.txt
if [ "$MISSING" -gt 0 ]; then
  echo "verify.sh: $MISSING file(s) missing or damaged; see $DIR/MISSING.txt" >&2
  exit 1
fi

# 2. Join each split file whose parts are all here, in order. When some parts are gone, the
#    file joined by an earlier run stays, and step 3 checks it.
while read -r count hash path; do
  case $count in '#'* | '') continue ;; esac
  complete=yes
  i=1
  while [ "$i" -le "$count" ]; do
    [ -f "$(part_of "$path" "$i")" ] || complete=no
    i=$((i + 1))
  done
  [ "$complete" = yes ] || continue
  rm -f "$path.joining"
  i=1
  while [ "$i" -le "$count" ]; do
    cat "$(part_of "$path" "$i")" >> "$path.joining"
    i=$((i + 1))
  done
  mv -f "$path.joining" "$path"
done < PARTS.txt

# 3. Every file of SHA256SUMS against its hash; joined files are checked here as wholes.
FILES=0
while read -r hash path; do
  [ -n "$path" ] || continue
  FILES=$((FILES + 1))
  volume=$(volume_of "$path")
  case $volume in
    *,*) bring="new copies of volumes $volume of $TOTAL" ;;
    ?*) bring="a new copy of volume $volume of $TOTAL" ;;
  esac
  if [ -z "$volume" ]; then
    volume=every
    bring="a new copy of any volume"
  fi
  if [ ! -f "$path" ]; then
    missing "$path" "$hash" "$volume" "$bring"
  elif [ "$(hash_of "$path")" != "$hash" ]; then
    missing "$path" "$hash" "$volume" "$bring"
  fi
done < SHA256SUMS
if [ "$MISSING" -gt 0 ]; then
  echo "verify.sh: $MISSING file(s) do not match SHA256SUMS; see $DIR/MISSING.txt" >&2
  exit 1
fi

# 4. Remove the parts of joined files and leave the marker load.sh looks for.
while read -r count hash path; do
  case $count in '#'* | '') continue ;; esac
  i=1
  while [ "$i" -le "$count" ]; do
    rm -f "$(part_of "$path" "$i")"
    i=$((i + 1))
  done
done < PARTS.txt
sha256sum SHA256SUMS > .verified
echo "verify.sh: OK, $FILES files match SHA256SUMS. Next: sh load.sh $DIR MODEL_FOLDER"
