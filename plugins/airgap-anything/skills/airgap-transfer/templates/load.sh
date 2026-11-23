# load.sh: written by airgap-transfer. Loads a verified bundle inside the network with
# POSIX sh, coreutils and docker only: no Python, no network. Do not edit it.
# pack.py fills the docker command lines from transfer_lib/tools.py, where each has its source.
#
#   sh load.sh [bundle folder] [model folder]
#
# Exit 0: every image is loaded and the model folders are copied; the last lines name the
#         next steps.
# Exit 1: stop and report the message (verify.sh has not passed, docker is missing, an image
#         did not load, or it loaded with another image ID).
# Exit 2: wrong arguments.
#
# The image ID check. bundle.json and <name>.id hold the SHA-256 of each image's config. The
# Engine API documents the Id of an inspected image as "a content-addressable digest calculated
# from the image's configuration" (ImageInspect.Id,
# https://docs.docker.com/reference/api/engine/version/v1.57.yaml). For a multi-platform image
# store it also says "ID is the content-addressable ID of an image and is the same as the digest
# of the image manifest" (ImageManifestSummary.ID, same page). The containerd image store is
# detected only by the signal its documentation gives: `docker info -f '{{ .DriverStatus }}'`
# prints driver-type io.containerd.snapshotter.v1 inside double brackets
# (https://docs.docker.com/engine/storage/containerd/). On that store another ID is a note; on
# any other store it stops the script. verify.sh has checked every byte against SHA256SUMS
# either way. AIRGAP_SKIP_IMAGE_ID_CHECK=1 skips the comparison and says so.
set -eu

if [ "$#" -gt 2 ]; then
  echo "usage: sh load.sh [bundle folder] [model folder]" >&2
  exit 2
fi
DIR=${1:-.}
MODELS=${2:-}
if [ ! -d "$DIR" ]; then
  echo "load.sh: $DIR is not a folder" >&2
  exit 2
fi
case $MODELS in
  '' | /*) ;;
  *) MODELS=$(pwd)/$MODELS ;;
esac
cd "$DIR"
if [ ! -f .verified ] || ! sha256sum -c --status .verified > /dev/null 2>&1; then
  echo "load.sh: verify.sh has not passed on this folder since SHA256SUMS last changed; run sh verify.sh $DIR first" >&2
  exit 1
fi
if [ -d models ] && [ -z "$MODELS" ]; then
  echo "usage: sh load.sh [bundle folder] [model folder]; this bundle has models, so give the model folder" >&2
  exit 2
fi

if [ -d images ]; then
  if ! command -v docker > /dev/null 2>&1; then
    echo "load.sh: docker is not on PATH; install Docker Engine from the manual items first" >&2
    exit 1
  fi
  STORE=classic
  case $({{docker.store}} < /dev/null 2> /dev/null || true) in
    *'driver-type io.containerd.snapshotter.v1'*) STORE=containerd ;;
  esac
  # Only the archives SHA256SUMS lists, which verify.sh checked; any other .tar is reported and
  # never loaded.
  awk '{ f = $0; sub(/^[^ ]+  /, "", f); if (f ~ /^images\/.*\.tar$/) print f }' SHA256SUMS | sort > .load-list
  find images -type f -name '*.tar' | sort > .load-found
  while read -r archive; do
    grep -F -x -q -e "$archive" .load-list || echo "load.sh: not loaded, because SHA256SUMS does not list it: $archive"
  done < .load-found
  rm -f .load-found
  while read -r archive; do
    expected=$(cat "${archive%.tar}.id")
    if ! {{docker.load}} < /dev/null > /dev/null; then
      echo "load.sh: docker load failed for $archive" >&2
      exit 1
    fi
    if [ "${AIRGAP_SKIP_IMAGE_ID_CHECK:-}" = 1 ]; then
      echo "load.sh: loaded $archive; image ID check skipped (AIRGAP_SKIP_IMAGE_ID_CHECK=1); verify.sh checked its bytes against SHA256SUMS"
      continue
    fi
    loaded=$({{docker.image_id}} < /dev/null 2> /dev/null || true)
    if [ "$loaded" = "$expected" ]; then
      echo "load.sh: loaded $archive ($expected)"
    elif [ "$STORE" = containerd ]; then
      echo "load.sh: note: loaded $archive; docker reports the image ID ${loaded:-(none)}, not the config digest $expected."
      echo "  This engine uses the containerd image store, which reports the digest of the image manifest as the"
      echo "  image ID. verify.sh has already checked the bytes of the archive against SHA256SUMS, so load.sh goes on."
    else
      echo "load.sh: $archive did not load as $expected (docker reports ${loaded:-no image with that ID})." >&2
      echo "  With the classic image store the image ID is the SHA-256 of the image config, so this is another image." >&2
      echo "  If this engine uses the containerd image store, it reports the manifest digest as the image ID instead," >&2
      echo "  and docker info did not show that store here. verify.sh has checked every byte against SHA256SUMS;" >&2
      echo "  a person may decide to skip this comparison with: AIRGAP_SKIP_IMAGE_ID_CHECK=1 sh load.sh $DIR ${MODELS:-MODEL_FOLDER}" >&2
      exit 1
    fi
  done < .load-list
  rm -f .load-list
fi

if [ -d models ]; then
  mkdir -p "$MODELS"
  for folder in models/*; do
    [ -d "$folder" ] || continue
    cp -R "$folder" "$MODELS/"
    echo "load.sh: copied $folder to $MODELS"
  done
fi

echo "load.sh: OK. Packages are in $DIR/packages and manual items in $DIR/manual, where they stay."
echo "Next: install the registry from its package if it is not running, push the loaded images to it"
echo "(the settings listed in INSIDE.md / AGENTS-INSIDE.md go into the deployment files before any"
echo "service starts), stage the runtime downloads, and continue with the implementation plan."
