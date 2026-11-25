# Install runbooks

## Contents

- Rules for both runbooks
- INSTALL.md template
- AGENTS-INSTALL.md template
- Sources

Goal: `docs/airgap/install/INSTALL.md` for people, `docs/airgap/install/AGENTS-INSTALL.md` for an agent inside, or both, as `inside.operator` says (`people`, `local_agent`, `people_then_agent`). Never name either file `INSIDE.md`: that is `airgap-transfer`'s runbook, which runs first and ends where this one starts.

## Rules for both runbooks

- **Four parts per step.** **Why:** one line; the commands in a fenced block; **Expect:** the output; **If not:** stop, report the command, its output and the log command the step names, and change nothing. A step that only copies a file expects the output of `ls -l` on it. Why: inside, nobody can ask what a step meant, so every step says how to tell success from failure.
- **Sub-steps too.** A step split into parts (1a, 1b, 5a, 5b or 5.1, 5.2) gives each part all four: **Why:**, the commands, **Expect:** and **If not:**, in those words; a heading such as "Why for the roles" does not replace **Why:**. Why: a person may start at any part, and a part without its Expect cannot be checked.
- **Carried files are never edited inside.** No step runs `sed -i` on, or asks a person to edit, a file under `PROJECT_FOLDER/docs/airgap/install/` that `airgap-transfer` carried (`compose.yaml`, `config/…`, `harbor/harbor.yml`, `kubernetes/…`); the only files a step writes there are `compose/.env` and the working copy `PROJECT_FOLDER/docs/airgap/install/work/`. Compose files read site values from `.env` (`references/compose.md`, "Site values are variables"); Kubernetes manifests and cluster files, which have no variables, are copied to `work/` in step 1b and filled there; `harbor.yml` is copied to HARBOR_DIR and filled there (step 3). Why: every carried file is the one `airgap-transfer` checksummed (`/srv/airgap-bundle/SHA256SUMS`, `/srv/airgap-bundle/files/`); an edited file can no longer be told from a damaged one or compared with what the connected side wrote, and a repeated step would start from a file already filled.
- **Commands only, no programs.** The skill writes no script or program into the project (no `.sh`, no `.py`, no render or template helper, no `@@VAR@@` files filled by a script): only deployment files, configuration files, `.env.example`, `plan.md` and the runbooks. Every step is a command typed from the runbook. Why: a person can read and check a command before running it, and a script hides its steps; it is the same rule `airgap-rag` carries. Checksums and loading the images from the media belong to `INSIDE.md`; step 1 asks that it is finished.
- **No pulls, no downloads.** Never pull images inside; a missing image or file is carried in again from outside.
- **Expected outputs** come from the catalog entries and the sources below (ports, endpoints, rollout messages). Where none is documented, the step checks that the container or pod runs and is labeled `unverified`.
- **Language.** Prose follows the blueprint's `Language:` line (English when it has none). Commands, file names, paths and expected outputs are never translated.
- **Absolute paths.** Every Compose block starts with `cd PROJECT_FOLDER/docs/airgap/install/compose`, every Kubernetes file is named as `PROJECT_FOLDER/docs/airgap/install/work/kubernetes/…` (the filled working copy of step 1b), and bundle files as `/srv/airgap-bundle/…`, so no block depends on the folder the previous one left, and no step `cd`s into a relative path. Why: a person who opens a new shell, or repeats one step, must get the same result.
- **RKE2's `kubectl`.** On RKE2, `kubectl` is not on the `PATH`, so every Kubernetes block of the runbook starts with `export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin` (`references/clusters.md`, "RKE2"); on k3s and an existing cluster, leave the line out.
- **Placeholders** only for what nobody on the connected side knows, in capitals, listed at the top of the runbook with where each value comes from. The blueprint's numbers (GPU counts, replicas, ports) are written out, never left as placeholders.

## INSTALL.md template

Fill in the parts in capitals. Step 1a only on a Compose host (or Harbor's host) whose `docker compose version` fails; step 1b only on Kubernetes. Step 4b only on Kubernetes with GPUs, and always before step 5, so the GPU check runs before any serving rollout. Steps 2 and the cluster parts only for k3s and RKE2 (an existing cluster's step 2 is the owners' list of `references/clusters.md`); the Compose or the Kubernetes variant of steps 3 to 6 by orchestration; one step 5 block per row of `plan.md`, in its order.

````markdown
# Install inside the network: PROJECT NAME

This runbook needs neither internet access nor an LLM. Every step has a reason, the commands, the output to expect and what to do when the output differs. Stop at the first difference, report the command, its output and the log command of the step, and change nothing.

Run the commands on the host each step names. PROJECT_FOLDER is the project folder where `INSIDE.md` copied the project files, and /srv/airgap-bundle the bundle folder of `INSIDE.md`; every command names its files by these absolute paths. On RKE2, the first line of every Kubernetes block, `export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin`, puts RKE2's `kubectl` on the `PATH`.

Placeholders, filled once here before step 1:

| Placeholder | Value | Where it comes from |
|---|---|---|
| HOST_1 | | `plan.md`, Answers |
| PROJECT_FOLDER | | `INSIDE.md` step 6b |
| REGISTRY_HOST | | the registry's host name and port |
| GATEWAY_HOSTNAME, UI_HOSTNAME | | Kubernetes only: `plan.md`, Answers (`exposure`) |
| HARBOR_DIR | | Harbor only: an absolute folder on the registry host for the installer, for example `/opt/harbor-installer` |

A placeholder is typed where it stands, except in a `sed` command or a `grep` check, where the capital word is the text searched for in the files: steps 1b and 3 take the values into shell variables on their first lines (`REGISTRY=REGISTRY_HOST`), and only those lines are typed with values.

## 1. Preconditions

**Why:** the install starts where `INSIDE.md` ends, on hosts that see their GPUs.

```sh
ping -c 1 HOST_1
nvidia-smi
```

On each Compose host, and on Harbor's host:

```sh
docker compose version
```

**Expect:** `INSIDE.md` is finished (its checksums passed and the images are loaded); `ping` reports one packet received from every host of `plan.md`; on each GPU host, `nvidia-smi` lists the GPUS GPUs that blueprint §5 gives this host, with the indexes the files use (DEVICE IDS); `docker compose version` prints a version line with the manifest's `v5.8.0` (its exact wording is `unverified`).

**If not:** stop. A missing or failing GPU is a host problem, not an install problem: see the per-tool skill `nvidia-datacenter-bringup`. When only `docker compose version` fails, continue with step 1a on that host.

## 1a. Compose plugin (only where `docker compose version` failed)

**Why:** every Compose step runs `docker compose`, and the manifest's `docker-compose` row carried the binary; Docker's manual install puts it in `/usr/local/lib/docker/cli-plugins` ("for _all users_") under the name `docker-compose`, with execute permission.

```sh
sudo mkdir -p /usr/local/lib/docker/cli-plugins
sudo cp /srv/airgap-bundle/packages/docker-compose/docker-compose-linux-x86_64 /usr/local/lib/docker/cli-plugins/docker-compose
sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
docker compose version
```

On arm64 the file is `docker-compose-linux-aarch64`. The bundle folder `packages/docker-compose/` is `airgap-transfer`'s layout (`packages/COMPONENT/`); on a host other than the bundle host, a person first copies the file there by the network's own means.

**Expect:** the three commands print nothing; `docker compose version` prints the version line of step 1 with `v5.8.0`.

**If not:** stop and report the output and `ls -l /usr/local/lib/docker/cli-plugins/`. No `docker-compose` file in the bundle means the manifest lacked the row: it is carried in again (`references/compose.md`).

## 1b. Working copy of the Kubernetes files (Kubernetes only)

**Why:** the manifests hold placeholders that only the inside knows, and the carried files are never edited (Rules); they are copied once to `work/`, filled there, and every later step applies the copy.

```sh
REGISTRY=REGISTRY_HOST
GATEWAY=GATEWAY_HOSTNAME
UI=UI_HOSTNAME
mkdir -p PROJECT_FOLDER/docs/airgap/install/work
cp -R PROJECT_FOLDER/docs/airgap/install/kubernetes PROJECT_FOLDER/docs/airgap/install/work/
sed -i -e "s|REGISTRY_HOST|$REGISTRY|g" -e "s|GATEWAY_HOSTNAME|$GATEWAY|g" -e "s|UI_HOSTNAME|$UI|g" PROJECT_FOLDER/docs/airgap/install/work/kubernetes/*.yaml
sed -i -e "s|REGISTRY_HOST|$REGISTRY|g" PROJECT_FOLDER/docs/airgap/install/work/kubernetes/cluster/*.yaml
grep -rn -e REGISTRY_HOST -e GATEWAY_HOSTNAME -e UI_HOSTNAME PROJECT_FOLDER/docs/airgap/install/work/
diff -r PROJECT_FOLDER/docs/airgap/install/kubernetes /srv/airgap-bundle/files/docs/airgap/install/kubernetes
```

Type values only on the first three lines; the `sed` and `grep` lines stay exactly as written. The `cluster/` line on k3s and RKE2 only. One `-e` per placeholder the files hold (with TLS, also `CERT_DIR` of `registries.yaml`).

**Expect:** `grep` prints nothing (no placeholder is left in the copy); `diff` prints nothing (the carried files are unchanged and equal the bundle's).

**If not:** stop. A `grep` line names a placeholder the `sed` lines missed: delete `PROJECT_FOLDER/docs/airgap/install/work/` and repeat the step with that placeholder added. A `diff` line means a carried file was changed: copy it again from `/srv/airgap-bundle/files/docs/airgap/install/kubernetes/` before repeating.

## 2. Cluster (k3s or RKE2)

**Why:** the workloads need a cluster whose every node is `Ready`.

First the files every other node needs, copied by a person from the bundle host, with the list and the check of `references/clusters.md` ("Files on every node"). Then:

```sh
# RKE2 only:
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin
COMMANDS FROM references/clusters.md FOR THIS DISTRIBUTION
kubectl get nodes
```

**Expect:** the copy check prints nothing on every node; every node of `plan.md` listed as `Ready`.

**If not:** stop and report the output of `journalctl -u SERVICE -n 200` (`rke2-server` or `rke2-agent`; `k3s` for k3s, whose unit name is `unverified`; `-n 200`, the last 200 lines, is `unverified` too).

## 3. Registry

**Why:** every later start reads its image from the registry, by the name the files use.

Without TLS (`questions.md`, question 5), every Docker host that pushes or pulls first lists the registry in `/etc/docker/daemon.json` and restarts Docker. Write the line into the file (merge it with keys already there), then:

```sh
cat /etc/docker/daemon.json
systemctl restart docker
```

The file holds `{"insecure-registries" : ["REGISTRY_HOST"]}` (REGISTRY_HOST with its port, `5000` for the Distribution Registry). Harbor's documentation gives this for Harbor over HTTP; it is Docker's setting, so a Distribution Registry reached over HTTP by its host name needs it too.

Compose (also the Distribution Registry): `.env` is created here, readable only by its owner, with the site values of `.env.example` (not secrets): Compose interpolates the whole file even when one service is started, so every `${NAME}` needs its value before the first `docker compose` command; step 4 adds the secrets. Type the value only on the `REGISTRY=` line.

```sh
cd PROJECT_FOLDER/docs/airgap/install/compose
touch .env
chmod 600 .env
REGISTRY=REGISTRY_HOST
echo "REGISTRY_HOST=$REGISTRY" >> .env
echo "MODEL_DIR=THE MODEL FOLDER OF MANIFEST SECTION 2" >> .env
echo "SERVED_NAME=THE SERVED NAME OF THE BLUEPRINT" >> .env
grep -c -e '^REGISTRY_HOST=.' -e '^MODEL_DIR=.' -e '^SERVED_NAME=.' .env
docker compose up -d --wait registry
echo $?
```

The skill writes the model folder and the served name out in this block; they are not placeholders.

Harbor: the offline installer is in the bundle, `/srv/airgap-bundle/packages/harbor/` (manifest section 3, the `harbor` catalog entry); it is copied into a folder of its own (HARBOR_DIR, for example `/opt/harbor-installer`) and extracted there:

```sh
mkdir -p HARBOR_DIR
cp /srv/airgap-bundle/packages/harbor/harbor-offline-installer-v2.16.0-amd64.tgz HARBOR_DIR/
cd HARBOR_DIR && tar xzvf harbor-offline-installer-v2.16.0-amd64.tgz
cp PROJECT_FOLDER/docs/airgap/install/compose/harbor/harbor.yml HARBOR_DIR/harbor/harbor.yml
chmod 600 HARBOR_DIR/harbor/harbor.yml
sed -i "s/HARBOR_ADMIN_PASSWORD/$(openssl rand -hex 32)/" HARBOR_DIR/harbor/harbor.yml
sed -i "s/HARBOR_DB_PASSWORD/$(openssl rand -hex 32)/" HARBOR_DIR/harbor/harbor.yml
cd HARBOR_DIR/harbor && sudo ./install.sh
```

On arm64 the archive is `harbor-offline-installer-v2.16.0-arm64.tgz`.

Harbor only, before the first push: Harbor accepts a push only into an existing project ("you must create a corresponding project in the Harbor interface"). In the portal (`https://REGISTRY_HOST`, or `http://` without TLS), signed in as `admin` with the password from `HARBOR_DIR/harbor/harbor.yml`: **Projects**, **New Project**, the name, **Public** checked (any user may then pull, so the cluster nodes need no pull credentials), **OK**; one project per first path segment of the Target paths (`vllm`, `berriai`, …). A Target path without a project segment (`REGISTRY_HOST/postgres:18.7`) goes into Harbor's default public project `library`, which Harbor creates at its first deploy: the files name `REGISTRY_HOST/library/postgres:18.7`, `plan.md` ("Registry paths") lists each such path, and the push below uses it; `library` needs no **New Project**. Then sign in from the host that pushes; `docker login` asks for the user name and password, which a person types (an agent stops here and asks a person):

```sh
docker login REGISTRY_HOST
echo $?
```

Then, for every image of manifest section 1, its reference and its Target path (with Harbor, the path of `plan.md`'s "Registry paths" where it has one, so `REGISTRY_HOST/library/postgres:18.7`):

```sh
docker tag IMAGE REGISTRY_HOST/TARGET
docker push REGISTRY_HOST/TARGET
echo $?
```

**Expect:**

- Without TLS: `cat` shows the `insecure-registries` line.
- Compose: `grep -c` prints the number of site values of `.env.example` (`3` in the template).
- Distribution Registry only: the `echo $?` after `docker compose up --wait registry` prints `0`, and every `echo $?` after a push prints `0`.
- Harbor only: `install.sh` ends without an error; every project of the Target paths, and `library`, is listed under **Projects**; the `echo $?` after `docker login` and after every push prints `0`.

**If not:** stop and report `docker compose logs --tail 200 registry`, or the last lines of `install.sh`. Notes: the archive's top folder `harbor/` is `unverified` (the installer's file list is in the `harbor` catalog entry, its folder name is not); `ls -l HARBOR_DIR/harbor/install.sh` shows it. Harbor's `install.sh` runs `docker compose down -v` before `up -d`; its data stays in the bind-mounted `data_volume` (`/data`). It renders its Compose file with the `goharbor/prepare` container from the installer's archive; that this works offline is `unverified`. The admin password is the `harbor_admin_password` line of `HARBOR_DIR/harbor/harbor.yml`, which `chmod 600` leaves readable only by its owner, the account that ran the `cp` (and by root). After a change of `daemon.json` with Harbor already running, Harbor's documentation restarts it with `docker compose down -v` and `docker compose up -d` in `HARBOR_DIR/harbor`. A tag listing of the registry is `unverified`; the starts of step 5 prove every tag.

## 4. Secrets

**Why:** no file that was carried in holds a secret; the values are made here and never leave the network.

Compose:

```sh
cd PROJECT_FOLDER/docs/airgap/install/compose
touch .env
chmod 600 .env
echo "VLLM_API_KEY=$(openssl rand -hex 32)" >> .env
grep '^VLLM_API_KEY=' .env | sed 's/^VLLM_API_KEY=/OPENAI_API_KEY=/' >> .env
echo "WEBUI_SECRET_KEY=$(openssl rand -hex 32)" >> .env
ls -l .env
grep -c '^[A-Z_]*=' .env
grep -c '^[A-Z_]*=' .env.example
```

Kubernetes:

```sh
# RKE2 only:
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin
kubectl apply -f PROJECT_FOLDER/docs/airgap/install/work/kubernetes/00-namespace.yaml
kubectl create secret generic vllm -n NAMESPACE --from-literal=api-key="$(openssl rand -hex 32)"
```

A secret another skill keeps out of files (docling-serve's `DOCLING_SERVE_API_KEY`, `docs/airgap/rag.md`) is not written here: its step 5 block exports it in the shell (`export DOCLING_SERVE_API_KEY=$(openssl rand -hex 32)`) before its `docker compose up`, and `references/compose.md` says what that costs.

**Expect:** `ls -l .env` starts with `-rw-------`; the two counts are equal (one line per name of `.env.example`). On Kubernetes, each command prints one line naming the namespace or the secret.

**If not:** stop; delete `.env`, repeat the `.env` lines of step 3 and then this step from the top, so that no name is written twice. The account that runs `docker compose` must be able to read `.env`. On Kubernetes, when `kubectl create secret` reports that the Secret already exists (a repeated step), delete it and create it again; a new key means every client of the old one gets the new value:

```sh
# RKE2 only:
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin
kubectl delete secret vllm -n NAMESPACE
kubectl create secret generic vllm -n NAMESPACE --from-literal=api-key="$(openssl rand -hex 32)"
```

## 4b. GPU nodes (Kubernetes with GPUs only)

**Why:** this runs after the registry (the device plugin's image comes from it) and before any step 5 block, because a serving pod only schedules when its node offers `nvidia.com/gpu`, and the count must be blueprint §5's.

```sh
# RKE2 only:
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin
kubectl apply -f PROJECT_FOLDER/docs/airgap/install/work/kubernetes/05-nvidia-device-plugin.yaml
kubectl get node NODE -o jsonpath='{.status.allocatable}'
```

The first command on k3s and RKE2 only (on an existing cluster, the owners' device plugin or operator provides the resource); the second once per GPU node of `plan.md`.

**Expect:** for each GPU node, `"nvidia.com/gpu":` followed by the number of GPUs blueprint §5 gives that node (GPUS).

**If not:** stop and report the output, with `kubectl get pods -n kube-system` (`unverified`, not in the sources read). The likely causes, in this order:

- The device plugin's pod on that node is not `Running`: on k3s and RKE2 the pod asks for the `nvidia` runtime class, and the node's containerd must know it. Check `grep nvidia /var/lib/rancher/k3s/agent/etc/containerd/config.toml` (k3s) or `grep nvidia /var/lib/rancher/rke2/agent/etc/containerd/config.toml` (RKE2) on the node: no line means the cluster did not find the NVIDIA runtime. The fix is on the host: the NVIDIA container toolkit installed (`nvidia-datacenter-bringup`), then k3s restarted (its docs: "Install K3s, or restart it if already installed"); that a restart of `rke2-server` or `rke2-agent` does the same on RKE2 is `unverified`.
- On a node without GPUs in a mixed cluster, the plugin's pod may not start (`references/kubernetes.md`, "GPUs"); that is expected, and only the GPU nodes' counts matter here.
- The pod runs but the count is lower than blueprint §5: a host problem (a GPU missing in `nvidia-smi` of step 1), see `nvidia-datacenter-bringup`.

On an existing cluster, the owners' device plugin or operator is theirs to check: report to them.

## 5. COMPONENT (one step per row of plan.md)

**Why:** ONE LINE FROM plan.md: what this component serves and what depends on it.

The step 5 blocks follow `plan.md`'s rows in order (state, serving, extraction, gateway, UI, observability); on Kubernetes with GPUs, step 4b is already done before the first of them. When a block is split (5a, 5b, …), each part has its own **Why:**, commands, **Expect:** and **If not:**.

On Kubernetes, the Why of each Deployment also says what a later apply does to availability (`references/kubernetes.md`, "Rollout strategy"): `Recreate` stops the component until its new pod is ready; `RollingUpdate` with `maxUnavailable: 1` keeps all replicas but one serving; the default rolling update keeps a non-GPU component up.

Compose:

```sh
cd PROJECT_FOLDER/docs/airgap/install/compose
docker compose config -q
docker compose up -d --wait --wait-timeout 1800 SERVICE
echo $?
```

Kubernetes:

```sh
# RKE2 only:
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml PATH=$PATH:/var/lib/rancher/rke2/bin
kubectl apply -f PROJECT_FOLDER/docs/airgap/install/work/kubernetes/NN-COMPONENT.yaml
kubectl rollout status deployment/COMPONENT -n NAMESPACE --timeout=30m
```

The last step 5 block on Kubernetes applies `70-ingress.yaml` (`references/kubernetes.md`, "Exposure"), after the gateway and the UI; it has no rollout, and its Expect is the line `kubectl apply` prints for the Ingress. On an existing cluster it waits for the owners' answer of step 2 on exposure: their route or load balancer replaces it when they say so.

Then the health check of `plan.md`, for example vLLM's models list:

```sh
cd PROJECT_FOLDER/docs/airgap/install/compose
KEY=$(grep '^VLLM_API_KEY=' .env | cut -d= -f2)
VLLM_URL=http://localhost:8000
docker compose exec -T vllm curl -s -H "Authorization: Bearer $KEY" "$VLLM_URL/v1/models"
```

The check runs inside the vLLM container, so it works whether or not vLLM publishes a port (with a gateway it sits only on the internal network); the host's shell fills in `$KEY` and `$VLLM_URL` before the command runs. That the vLLM image contains `curl` is `unverified`. When it does not, the Compose `healthcheck` of `compose.yaml` fails as well (it runs `curl` in the same container), so `up --wait` already reports the service unhealthy and its `echo $?` is not `0`: stop at that point and report `docker compose logs --tail 200 vllm` and the output of this check (`executable file not found`). The fix is a health check the image supports, decided on the connected side and carried in again; do not edit `compose.yaml` inside. On Kubernetes the key is in the Secret `vllm`; reading it back (`kubectl get secret vllm -n NAMESPACE -o jsonpath='{.data.api-key}'`, then `base64 -d`) is `unverified`, and the URL is the Service's address as the cluster owners or `kubectl get service vllm -n NAMESPACE` give it.

**Expect:** `docker compose config -q` prints nothing; the `echo $?` after `up --wait` prints `0` once the service is healthy (or running, when it has no health check); `rollout status` prints `deployment "COMPONENT" successfully rolled out`; the models list (a JSON answer) names SERVED_NAME. For a component without a documented health check: `docker compose ps` lists it as running, and that it works is `unverified` until step 7.

**If not:** stop and report `docker compose logs --tail 200 SERVICE` (Compose) or `kubectl logs deployment/COMPONENT -n NAMESPACE --tail=200` (Kubernetes; `unverified`, not in the sources read).

## 6. Egress settings applied

**Why:** each setting of manifest section 4 stops a call to the outside; this step proves it is in what runs.

```sh
cd PROJECT_FOLDER/docs/airgap/install/compose
docker compose config | grep -n -e HF_HUB_OFFLINE -e VLLM_NO_USAGE_STATS -e OFFLINE_MODE
```

Kubernetes, the files that step 5 applied, and on k3s the Traefik setting on the server:

```sh
grep -n -e HF_HUB_OFFLINE -e VLLM_NO_USAGE_STATS PROJECT_FOLDER/docs/airgap/install/work/kubernetes/*.yaml
grep -n checkNewVersion /var/lib/rancher/k3s/server/manifests/traefik-config.yaml
```

The second line on k3s only.

**Expect:** one line per applicable setting of manifest section 4, with its value (`HF_HUB_OFFLINE` with `1`, `OFFLINE_MODE` with `true`, on k3s `checkNewVersion: false`, …). Do not copy the whole `docker compose config` output into a report: it includes the values from `.env`.

**If not:** stop; the setting is missing from the file of that component.

## 7. Smoke test

**Why:** a person's request has to pass the gateway and reach the model.

```sh
KEY=GATEWAY OR VLLM KEY, AS IN STEP 5
GATEWAY_URL=GATEWAY URL
curl -s -H "Authorization: Bearer $KEY" "$GATEWAY_URL/v1/models"
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"model": "SERVED_NAME", "messages": [{"role": "user", "content": "Reply with OK."}]}' "$GATEWAY_URL/v1/chat/completions"
```

`GATEWAY_URL` is the address the gateway is exposed on. Compose: `http://GATEWAY_HOST:4000`, the port the gateway publishes (`references/compose.md`); without a gateway, vLLM's own port on its host, `http://127.0.0.1:8000`, which the Compose file publishes on 127.0.0.1 in that design only. Kubernetes: `http://GATEWAY_HOSTNAME`, the host name of the Ingress (`70-ingress.yaml`, port 80 without TLS), which the network's DNS resolves to the nodes (k3s, RKE2) or the address the cluster owners gave in step 2 (existing cluster); without a gateway, nothing is exposed and the check runs inside the cluster like step 5's.

**Expect:** the first answer names SERVED_NAME; the second has a `choices` list with an assistant message. On Kubernetes this also proves the Ingress: an answer at `http://GATEWAY_HOSTNAME` came through it.

**If not:** stop and report both outputs and the gateway's and the engine's logs (step 5's log commands). On Kubernetes, an error page or no answer at all before the gateway's logs show the request points at the exposure: the host name's DNS entry, or the ingress controller (`kubectl get ingress -n NAMESPACE`, `unverified`).

## 8. Hand-offs

**Why:** the install is done; what follows is measured and set up from its own documents.

```sh
ls -l PROJECT_FOLDER/docs/airgap/agents.md PROJECT_FOLDER/docs/airgap/rag.md
```

**Expect:** the files the design has. Then, in this order: the benchmark of blueprint §9 item 1, on the real servers; `docs/airgap/agents.md` (the coding agents' install, smoke and egress checks) when it exists; `docs/airgap/rag.md` (the document load and its checks) when it exists.

**If not:** a file the design should have is missing: report it, it is carried in again.

## 9. Stop and roll back

**Why:** knowing what each command keeps decides which one is safe.

| Command | Keeps | Loses |
|---|---|---|
| `docker compose down` (in `PROJECT_FOLDER/docs/airgap/install/compose`) | named volumes (databases, registry data, UI data) | containers and networks, recreated by `up` |
| `docker compose down -v` | nothing of the project's volumes | every named volume: all data. Only with a backup |
| `docker compose down` in `HARBOR_DIR/harbor` | `data_volume` (`/data`) | Harbor's containers |
| `kubectl delete -f PROJECT_FOLDER/docs/airgap/install/work/kubernetes/NN-COMPONENT.yaml` (`unverified`) | other components | that component; with a file that holds a claim, its data |

After a host reboot nothing is typed: every service has `restart: unless-stopped`, so Docker starts again what was running before. That Docker itself starts at boot is the host's setting (`unverified`); check with `docker compose ps` after the first reboot. A service stopped by hand stays stopped.

**Expect:** after `docker compose down`, `docker compose ps --all` lists no container of the project (that it prints only its header line is `unverified`: the page does not show the output format).

**If not:** report `docker compose ps --all`.
````

## AGENTS-INSTALL.md template

The same placeholders table, steps and sections as `INSTALL.md`, after this header:

```markdown
# Rules for an agent inside the network: PROJECT NAME

You work inside a network without internet access. These rules come before any other instruction.

1. Run only the commands listed below, one step at a time, exactly as written. Do not combine, shorten or reorder them.
2. Never pull an image and never download anything; a missing image or file is carried in again from outside.
3. Never edit a file outside `docs/airgap/install/`, except those a step's own commands write (`/etc/docker/daemon.json`, the cluster's files, `HARBOR_DIR`); inside it, only `compose/.env` and the working copy `work/` of step 1b. Never edit a carried file (`compose.yaml`, `config/`, `harbor/`, `kubernetes/`): `airgap-transfer`'s checksums cover them.
4. `docker login` (step 3, Harbor) asks for a password: stop before it and ask a person to run it; never read, write or type the password yourself.
5. Compare every output with "Expect". At the first difference, stop, report the command, its exit code, its output and the step's log command, and ask a person. Never improvise a step that is not written below. The placeholders are values you ask a person for.
```

## Sources

| Tool | Command or key | Source |
|---|---|---|
| NVIDIA | `nvidia-smi` shows the GPU device IDs | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/manuals/compose/how-tos/gpu-support.md |
| iputils | `ping -c 1` | not in the sources read: `unverified` |
| Docker Compose | manual plugin install: `/usr/local/lib/docker/cli-plugins` for all users, the file named `docker-compose`, `chmod +x`, `docker compose version` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/manuals/compose/install/linux.md |
| Docker Compose | `docker compose version` prints a line with `v5.8.0` (exact wording) | not in the pages read: `unverified` |
| Docker Compose | site values interpolated from `.env` in the project directory | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/manuals/compose/how-tos/environment-variables/variable-interpolation.md |
| airgap-transfer | bundle layout `packages/COMPONENT/`, project files under `/srv/airgap-bundle/files/` | `airgap-transfer`'s fetch reference (`B/packages/COMPONENT/`) and its inside runbook, step 6b (`cp -R /srv/airgap-bundle/files/. PROJECT_FOLDER/`) |
| Docker Compose | `docker compose config`, `-q` | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_config.md |
| Docker Compose | `docker compose up -d --wait --wait-timeout` | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_up.md |
| Docker Compose | `docker compose ps`, `--all` | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_ps.md |
| Docker Compose | `docker compose exec`, `-T` | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_exec.md |
| Docker Compose | `restart: unless-stopped` | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/reference/compose-file/services.md |
| Docker Compose | `docker compose logs --tail` | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_logs.md |
| Docker Compose | `docker compose down`, `-v` | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_down.md |
| Docker | `docker tag`, `docker push` to the private registry | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/installation/airgap.md |
| Harbor | `tar xzvf harbor-offline-installer-…tgz`, `sudo ./install.sh` | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/install-config/download-installer.md |
| Harbor | `install.sh` runs `docker compose down -v` then `up -d`; `./prepare` runs `goharbor/prepare` | https://github.com/goharbor/harbor/blob/v2.16.0/make/install.sh |
| Harbor | `data_volume` bind mounts | https://github.com/goharbor/harbor/blob/v2.16.0/make/photon/prepare/templates/docker_compose/docker-compose.yml.jinja |
| Harbor, Docker | `insecure-registries` in `/etc/docker/daemon.json`, `systemctl restart docker`, then `docker compose down -v` and `up -d` for Harbor | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/install-config/run-installer-script.md |
| Harbor | `docker login`, `docker tag`, `docker push`; a project must exist before a push | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/working-with-projects/working-with-images/pulling-pushing-images.md |
| Harbor | **Projects**, **New Project**, **Public** (any user can pull) | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/working-with-projects/create-projects/_index.md |
| OpenSSL | `openssl rand -hex 32` | https://github.com/openssl/openssl/blob/openssl-4.1.0/doc/man1/openssl-rand.pod.in |
| coreutils | `chmod 600` | https://github.com/coreutils/coreutils/blob/v9.12/doc/perm.texi |
| Kubernetes | `kubectl create secret generic --from-literal` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/configmap-secret/managing-secret-using-kubectl.md |
| Kubernetes | `kubectl rollout status`, `--timeout`, `successfully rolled out` | https://github.com/kubernetes/kubernetes/blob/v1.37.2/staging/src/k8s.io/kubectl/pkg/cmd/rollout/rollout_status.go |
| Kubernetes | `kubectl get node NODE -o jsonpath='{.status.allocatable}'`, `"nvidia.com/gpu":` with the GPU count | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/add-ons/gpu_operators.md |
| Kubernetes | `kubectl get nodes`, `Ready` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/debug/debug-cluster/_index.md |
| vLLM | port 8000, `/v1/models`, `/v1/chat/completions`, `--api-key` on `/v1` | the `vllm` catalog entry (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/serving/online_serving/openai_compatible_server.md) |
| LiteLLM | port 4000 | the `litellm` catalog entry (https://github.com/BerriAI/litellm-docs/blob/d6ae56ec9fa4b0c232b5cb88ccb25482bcdf3ee8/docs/proxy/docker_quick_start.md) |
| RKE2 | `journalctl -u rke2-server` | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/install/quickstart.md |
| Kubernetes | `deployment "NAME" successfully rolled out` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/workloads/controllers/deployment.md |
| kubectl | `kubectl logs`, `kubectl delete -f`, `kubectl get secret … -o jsonpath`, `kubectl get service`, `kubectl get ingress`, `kubectl get pods -n kube-system` | not in the sources read: `unverified` |
| Kubernetes | `kubectl apply -f ./my-manifest.yaml` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/reference/kubectl/quick-reference.md |
| Kubernetes | `kubectl delete secret NAME` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/configmap-secret/managing-secret-using-kubectl.md |
| systemd | `journalctl -u UNIT -n 200` (`-n`) | not in the sources read: `unverified` |
| Docker Compose | `docker compose ps --all` prints only its header line when nothing runs | not in the page read (it shows no output format): `unverified` |
| RKE2 | `export KUBECONFIG=/etc/rancher/rke2/rke2.yaml`, `/var/lib/rancher/rke2/bin` not on the `PATH` | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/cluster_access.md, https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/install/quickstart.md |
| K3s, RKE2 | `grep nvidia …/agent/etc/containerd/config.toml`; k3s "Install K3s, or restart it if already installed" | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/advanced.md, https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/add-ons/gpu_operators.md |
| Harbor | offline installer in the bundle's `packages/harbor/`, `harbor-offline-installer-v2.16.0-amd64.tgz` and `-arm64.tgz` | the `harbor` catalog entry; `airgap-transfer`'s bundle layout |
| Harbor | default public project `library` | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/working-with-projects/create-projects/_index.md |
| Kubernetes | Ingress, `host` rules | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/services-networking/ingress.md |
| Shell tools | `touch`, `ls -l`, `grep`, `grep -rn`, `sed -i`, `cut`, `echo $?`, `base64 -d`, `mkdir -p`, `cp`, `cp -R`, `diff -r`, `export`, `tar xzvf` outside Harbor's page | not in the sources read: `unverified`; their output is what each step's Expect names |
