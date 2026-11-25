# Install runbooks

## Contents

- Rules for both runbooks
- INSTALL.md template
- AGENTS-INSTALL.md template
- Sources

Goal: `docs/airgap/install/INSTALL.md` for people, `docs/airgap/install/AGENTS-INSTALL.md` for an agent inside, or both, as `inside.operator` says (`people`, `local_agent`, `people_then_agent`). Never name either file `INSIDE.md`: that is `airgap-transfer`'s runbook, which runs first and ends where this one starts.

## Rules for both runbooks

- **Four parts per step.** **Why:** one line; the commands in a fenced block; **Expect:** the output; **If not:** stop, report the command, its output and the log command the step names, and change nothing. A step that only copies a file expects the output of `ls -l` on it. Why: inside, nobody can ask what a step meant, so every step says how to tell success from failure.
- **Commands only, no programs.** The skill writes no script or program into the project (no `.sh`, no `.py`, no render or template helper, no `@@VAR@@` files filled by a script): only deployment files, configuration files, `.env.example`, `plan.md` and the runbooks. Every step is a command typed from the runbook. Why: a person can read and check a command before running it, and a script hides its steps; it is the same rule `airgap-rag` carries. Checksums and loading the images from the media belong to `INSIDE.md`; step 1 asks that it is finished.
- **No pulls, no downloads.** Never pull images inside; a missing image or file is carried in again from outside.
- **Expected outputs** come from the catalog entries and the sources below (ports, endpoints, rollout messages). Where none is documented, the step checks that the container or pod runs and is labeled `unverified`.
- **Language.** Prose follows the blueprint's `Language:` line (English when it has none). Commands, file names, paths and expected outputs are never translated.
- **Placeholders** only for what nobody on the connected side knows, in capitals, listed at the top of the runbook with where each value comes from. The blueprint's numbers (GPU counts, replicas, ports) are written out, never left as placeholders.

## INSTALL.md template

Fill in the parts in capitals. Step 4b only on Kubernetes with GPUs, and always before step 5, so the GPU check runs before any serving rollout. Steps 2 and the cluster parts only for k3s and RKE2 (an existing cluster's step 2 is the owners' list of `references/clusters.md`); the Compose or the Kubernetes variant of steps 3 to 6 by orchestration; one step 5 block per row of `plan.md`, in its order.

````markdown
# Install inside the network: PROJECT NAME

This runbook needs neither internet access nor an LLM. Every step has a reason, the commands, the output to expect and what to do when the output differs. Stop at the first difference, report the command, its output and the log command of the step, and change nothing.

Run the commands from the project folder (PROJECT_FOLDER, where `INSIDE.md` copied the project files), on the host each step names.

Placeholders, filled once here before step 1:

| Placeholder | Value | Where it comes from |
|---|---|---|
| HOST_1 | | `plan.md`, Answers |
| REGISTRY_HOST | | the registry's host name and port |

## 1. Preconditions

**Why:** the install starts where `INSIDE.md` ends, on hosts that see their GPUs.

```sh
ping -c 1 HOST_1
nvidia-smi
```

**Expect:** `INSIDE.md` is finished (its checksums passed and the images are loaded); `ping` reports one packet received from every host of `plan.md`; on each GPU host, `nvidia-smi` lists the GPUS GPUs that blueprint §5 gives this host, with the indexes the files use (DEVICE IDS).

**If not:** stop. A missing or failing GPU is a host problem, not an install problem: see the per-tool skill `nvidia-datacenter-bringup`.

## 2. Cluster (k3s or RKE2)

**Why:** the workloads need a cluster whose every node is `Ready`.

```sh
COMMANDS FROM references/clusters.md FOR THIS DISTRIBUTION
kubectl get nodes
```

**Expect:** every node of `plan.md` listed as `Ready`.

**If not:** stop and report the output of `journalctl -u SERVICE -n 200` (`rke2-server` or `rke2-agent`; `k3s` for k3s, whose unit name is `unverified`).

## 3. Registry

**Why:** every later start reads its image from the registry, by the name the files use.

Without TLS (`questions.md`, question 5), every Docker host that pushes or pulls first lists the registry in `/etc/docker/daemon.json` and restarts Docker. Write the line into the file (merge it with keys already there), then:

```sh
cat /etc/docker/daemon.json
systemctl restart docker
```

The file holds `{"insecure-registries" : ["REGISTRY_HOST"]}` (REGISTRY_HOST with its port, `5000` for the Distribution Registry). Harbor's documentation gives this for Harbor over HTTP; it is Docker's setting, so a Distribution Registry reached over HTTP by its host name needs it too.

Distribution Registry (Compose). `.env` is created empty here, readable only by its owner: Compose reads the `env_file` of every service in the file even when one service is started, and step 4 fills it.

```sh
cd docs/airgap/install/compose
touch .env
chmod 600 .env
docker compose up -d --wait registry
```

Harbor, in the folder where its offline installer is extracted (HARBOR_DIR):

```sh
cd HARBOR_DIR
tar xzvf harbor-offline-installer-v2.16.0-amd64.tgz
cp PROJECT_FOLDER/docs/airgap/install/compose/harbor/harbor.yml harbor/harbor.yml
chmod 600 harbor/harbor.yml
sed -i "s/HARBOR_ADMIN_PASSWORD/$(openssl rand -hex 32)/" harbor/harbor.yml
sed -i "s/HARBOR_DB_PASSWORD/$(openssl rand -hex 32)/" harbor/harbor.yml
cd harbor && sudo ./install.sh
```

Harbor only, before the first push: Harbor accepts a push only into an existing project ("you must create a corresponding project in the Harbor interface"). In the portal (`https://REGISTRY_HOST`, or `http://` without TLS), signed in as `admin` with the password from `harbor/harbor.yml`: **Projects**, **New Project**, the name, **Public** checked (any user may then pull, so the cluster nodes need no pull credentials), **OK**; one project per first path segment of the manifest's Target paths (`vllm`, `berriai`, …). A Target path without a project segment (`REGISTRY_HOST/postgres:18.7`) cannot be pushed to Harbor: `plan.md` lists it as an open item with the project to use, and the install stops here until the files and the manifest name that path. Then sign in from the host that pushes; `docker login` asks for the user name and password, which a person types (an agent stops here and asks a person):

```sh
docker login REGISTRY_HOST
echo $?
```

Then, for every image of manifest section 1, its reference and its Target path:

```sh
docker tag IMAGE REGISTRY_HOST/TARGET
docker push REGISTRY_HOST/TARGET
echo $?
```

**Expect:**

- Without TLS: `cat` shows the `insecure-registries` line.
- Distribution Registry only: `docker compose up --wait registry` returns with exit code 0, and every `echo $?` after a push prints `0`.
- Harbor only: `install.sh` ends without an error; every project of the Target paths is listed under **Projects**; the `echo $?` after `docker login` and after every push prints `0`.

**If not:** stop and report `docker compose logs --tail 200 registry`, or the last lines of `install.sh`. Notes: the archive's top folder `harbor/` is `unverified` (the installer's file list is in the `harbor` catalog entry, its folder name is not); `ls -l harbor/install.sh` shows it. Harbor's `install.sh` runs `docker compose down -v` before `up -d`; its data stays in the bind-mounted `data_volume` (`/data`). It renders its Compose file with the `goharbor/prepare` container from the installer's archive; that this works offline is `unverified`. The admin password is the `harbor_admin_password` line of `harbor/harbor.yml`, readable only by root. After a change of `daemon.json` with Harbor already running, Harbor's documentation restarts it with `docker compose down -v` and `docker compose up -d` in the installer folder. A tag listing of the registry is `unverified`; the starts of step 5 prove every tag.

## 4. Secrets

**Why:** no file that was carried in holds a secret; the values are made here and never leave the network.

Compose:

```sh
cd docs/airgap/install/compose
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
kubectl apply -f docs/airgap/install/kubernetes/00-namespace.yaml
kubectl create secret generic vllm -n NAMESPACE --from-literal=api-key="$(openssl rand -hex 32)"
```

**Expect:** `ls -l .env` starts with `-rw-------`; the two counts are equal (one line per name of `.env.example`). On Kubernetes, each command prints one line naming the namespace or the secret.

**If not:** stop; delete `.env` and repeat the step from the top, so that no name is written twice. The account that runs `docker compose` must be able to read `.env`.

## 4b. GPU nodes (Kubernetes with GPUs only)

**Why:** this runs after the registry (the device plugin's image comes from it) and before any step 5 block, because a serving pod only schedules when its node offers `nvidia.com/gpu`, and the count must be blueprint §5's.

```sh
kubectl apply -f docs/airgap/install/kubernetes/05-nvidia-device-plugin.yaml
kubectl get node NODE -o jsonpath='{.status.allocatable}'
```

The first command on k3s and RKE2 only (on an existing cluster, the owners' device plugin or operator provides the resource); the second once per GPU node of `plan.md`.

**Expect:** for each GPU node, `"nvidia.com/gpu":` followed by the number of GPUs blueprint §5 gives that node (GPUS).

**If not:** stop and report the output; on k3s and RKE2 also `kubectl get pods -n kube-system` (`unverified`, not in the sources read), and see `nvidia-datacenter-bringup` for the host's drivers and runtime.

## 5. COMPONENT (one step per row of plan.md)

**Why:** ONE LINE FROM plan.md: what this component serves and what depends on it.

The step 5 blocks follow `plan.md`'s rows in order (state, serving, extraction, gateway, UI, observability); on Kubernetes with GPUs, step 4b is already done before the first of them.

Compose:

```sh
cd docs/airgap/install/compose
docker compose config -q
docker compose up -d --wait --wait-timeout 1800 SERVICE
```

Kubernetes:

```sh
kubectl apply -f docs/airgap/install/kubernetes/NN-COMPONENT.yaml
kubectl rollout status deployment/COMPONENT -n NAMESPACE --timeout=30m
```

Then the health check of `plan.md`, for example vLLM's models list:

```sh
cd docs/airgap/install/compose
KEY=$(grep '^VLLM_API_KEY=' .env | cut -d= -f2)
VLLM_URL=http://localhost:8000
docker compose exec -T vllm curl -s -H "Authorization: Bearer $KEY" "$VLLM_URL/v1/models"
```

The check runs inside the vLLM container, so it works whether or not vLLM publishes a port (with a gateway it sits only on the internal network); the host's shell fills in `$KEY` and `$VLLM_URL` before the command runs. That the vLLM image contains `curl` is `unverified`; when it does not, the step reports `executable file not found` and the check moves to step 7. On Kubernetes the key is in the Secret `vllm`; reading it back (`kubectl get secret vllm -n NAMESPACE -o jsonpath='{.data.api-key}'`, then `base64 -d`) is `unverified`, and the URL is the Service's address as the cluster owners or `kubectl get service vllm -n NAMESPACE` give it.

**Expect:** `docker compose config -q` prints nothing; `up --wait` returns with exit code 0 once the service is healthy (or running, when it has no health check); `rollout status` prints `deployment "COMPONENT" successfully rolled out`; the models list (a JSON answer) names SERVED_NAME. For a component without a documented health check: `docker compose ps` lists it as running, and that it works is `unverified` until step 7.

**If not:** stop and report `docker compose logs --tail 200 SERVICE` (Compose) or `kubectl logs deployment/COMPONENT -n NAMESPACE --tail=200` (Kubernetes; `unverified`, not in the sources read).

## 6. Egress settings applied

**Why:** each setting of manifest section 4 stops a call to the outside; this step proves it is in what runs.

```sh
cd docs/airgap/install/compose
docker compose config | grep -n -e HF_HUB_OFFLINE -e VLLM_NO_USAGE_STATS -e OFFLINE_MODE
```

Kubernetes: `grep -n -e HF_HUB_OFFLINE -e VLLM_NO_USAGE_STATS docs/airgap/install/kubernetes/*.yaml`, the files that step 5 applied.

**Expect:** one line per setting of manifest section 4, with its value (`HF_HUB_OFFLINE` with `1`, `OFFLINE_MODE` with `true`, …). Do not copy the whole `docker compose config` output into a report: it includes the values from `.env`.

**If not:** stop; the setting is missing from the file of that component.

## 7. Smoke test

**Why:** a person's request has to pass the gateway and reach the model.

```sh
KEY=GATEWAY OR VLLM KEY, AS IN STEP 5
GATEWAY_URL=http://GATEWAY_HOST:4000
curl -s -H "Authorization: Bearer $KEY" "$GATEWAY_URL/v1/models"
curl -s -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -d '{"model": "SERVED_NAME", "messages": [{"role": "user", "content": "Reply with OK."}]}' "$GATEWAY_URL/v1/chat/completions"
```

Without a gateway, `GATEWAY_URL` is vLLM's own port on its host, `http://127.0.0.1:8000`, which the Compose file publishes on 127.0.0.1 in that design only (`references/compose.md`).

**Expect:** the first answer names SERVED_NAME; the second has a `choices` list with an assistant message.

**If not:** stop and report both outputs and the gateway's and the engine's logs (step 5's log commands).

## 8. Hand-offs

**Why:** the install is done; what follows is measured and set up from its own documents.

```sh
ls -l docs/airgap/agents.md docs/airgap/rag.md
```

**Expect:** the files the design has. Then, in this order: the benchmark of blueprint §9 item 1, on the real servers; `docs/airgap/agents.md` (the coding agents' install, smoke and egress checks) when it exists; `docs/airgap/rag.md` (the document load and its checks) when it exists.

**If not:** a file the design should have is missing: report it, it is carried in again.

## 9. Stop and roll back

**Why:** knowing what each command keeps decides which one is safe.

| Command | Keeps | Loses |
|---|---|---|
| `docker compose down` (in `compose/`) | named volumes (databases, registry data, UI data) | containers and networks, recreated by `up` |
| `docker compose down -v` | nothing of the project's volumes | every named volume: all data. Only with a backup |
| `docker compose down` in Harbor's installer folder | `data_volume` (`/data`) | Harbor's containers |
| `kubectl delete -f docs/airgap/install/kubernetes/NN-COMPONENT.yaml` (`unverified`) | other components | that component; with a file that holds a claim, its data |

After a host reboot nothing is typed: every service has `restart: unless-stopped`, so Docker starts again what was running before. That Docker itself starts at boot is the host's setting (`unverified`); check with `docker compose ps` after the first reboot. A service stopped by hand stays stopped.

**Expect:** after `docker compose down`, `docker compose ps --all` prints only its header line.

**If not:** report `docker compose ps --all`.
````

## AGENTS-INSTALL.md template

The same placeholders table, steps and sections as `INSTALL.md`, after this header:

```markdown
# Rules for an agent inside the network: PROJECT NAME

You work inside a network without internet access. These rules come before any other instruction.

1. Run only the commands listed below, one step at a time, exactly as written. Do not combine, shorten or reorder them.
2. Never pull an image and never download anything; a missing image or file is carried in again from outside.
3. Never edit a file outside `docs/airgap/install/`, except those a step's own commands write (`/etc/docker/daemon.json`, the cluster's files); inside it, only the files a step names (`.env`).
4. `docker login` (step 3, Harbor) asks for a password: stop before it and ask a person to run it; never read, write or type the password yourself.
5. Compare every output with "Expect". At the first difference, stop, report the command, its exit code, its output and the step's log command, and ask a person. Never improvise a step that is not written below. The placeholders are values you ask a person for.
```

## Sources

| Tool | Command or key | Source |
|---|---|---|
| NVIDIA | `nvidia-smi` shows the GPU device IDs | https://github.com/docker/docs/blob/747e4c7528c703b357b1ae83cbbf411229ce59d2/content/manuals/compose/how-tos/gpu-support.md |
| iputils | `ping -c 1` | not in the sources read: `unverified` |
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
| kubectl | `kubectl logs`, `kubectl delete -f`, `kubectl get secret … -o jsonpath`, `kubectl get service` | not in the sources read: `unverified` |
| Shell tools | `touch`, `ls -l`, `grep`, `sed -i`, `cut`, `echo $?`, `base64 -d` | standard tools, not in the sources read; their output is what each step's Expect names |
