# Clusters

## Contents

- What every path shares
- k3s
- RKE2
- Existing cluster
- Sources

Goal: the cluster part of `INSTALL.md` step 2 and the files under `docs/airgap/install/kubernetes/cluster/` (k3s and RKE2 only). The commands below are the runbook's lines; `references/runbook.md` puts each into the four-part step form. Versions are the catalog's (`v1.37.2+k3s1`, `v1.37.2+rke2r1`): the documentation pages use older example versions in their file names, and the files carried are always those of the manifest.

## What every path shares

- Files come from the bundle, which `INSIDE.md` has already checked; nothing here downloads. The artifacts are the manifest's section 3 rows of the `k3s` or `rke2` catalog entry.
- The registry runs before the cluster pulls anything (`references/plan.md`, start order). Every node gets `registries.yaml`, servers too, because servers are schedulable.
- Each node needs a default route before the cluster starts (both distributions use it to find the node's address; a dummy interface is enough, as their air-gap pages show).
- SELinux: on an SELinux-enabled node (the air-gap pages' condition; `getenforce` printing `Enforcing` is the usual sign, `unverified` here), the policy RPM goes in by hand, before the cluster, and the cluster is started with SELinux enabled. The air-gap installs never install it. The RPM and its operating-system dependencies are not in the catalog's package tables: add them to manifest section 3 marked "(from airgap-install)", with the file for the hosts' distribution (`el8`, `el9`, …). Which file fits a distribution beyond the pages' CentOS examples is not documented: ask the user, and label the choice `unverified`.
- GPUs: the NVIDIA drivers and container toolkit are on the hosts before the cluster (`nvidia-datacenter-bringup`); the device plugin is `05-nvidia-device-plugin.yaml` (`references/kubernetes.md`).
- Done when `kubectl get nodes` lists every node of `plan.md` as `Ready`.

## k3s

Files the skill writes: `kubernetes/cluster/registries.yaml`. Without TLS, the default of `questions.md` question 5 (that an `http` endpoint works is `unverified`: the page's examples use `https`):

```yaml
mirrors:
  REGISTRY_HOST:
    endpoint:
      - "http://REGISTRY_HOST"
```

With the internal CA:

```yaml
mirrors:
  REGISTRY_HOST:
    endpoint:
      - "https://REGISTRY_HOST"
configs:
  REGISTRY_HOST:
    tls:
      ca_file: CERT_DIR/ca.crt
```

When the registry needs a login to pull, add `auth: {username: REGISTRY_USER, password: REGISTRY_PASSWORD}` under `configs` with those placeholders; the runbook fills them on the node, never in the file the skill writes.

Commands, on every node, as root (SELinux nodes first):

```sh
yum install ./k3s-selinux-1.6-1.el8.noarch.rpm
mkdir -p /var/lib/rancher/k3s/agent/images/
cp k3s-airgap-images-amd64.tar.zst /var/lib/rancher/k3s/agent/images/k3s-airgap-images-amd64.tar.zst
cp k3s /usr/local/bin/k3s
chmod +x /usr/local/bin/k3s
mkdir -p /etc/rancher/k3s
cp docs/airgap/install/kubernetes/cluster/registries.yaml /etc/rancher/k3s/registries.yaml
```

The first line only on SELinux nodes, with the RPM for the node's distribution and its dependencies (`container-selinux`, `policycoreutils`, `selinux-policy`) installed from the bundle first. On arm64 the files are `k3s-arm64` and `k3s-airgap-images-arm64.tar.zst`.

The server, then each agent:

```sh
INSTALL_K3S_SKIP_DOWNLOAD=true INSTALL_K3S_EXEC='server --disable-default-registry-endpoint' ./install.sh
INSTALL_K3S_SKIP_DOWNLOAD=true K3S_URL=https://SERVER_IP:6443 K3S_TOKEN=K3S_TOKEN ./install.sh
```

On SELinux nodes add `--selinux` inside `INSTALL_K3S_EXEC` (the agent line takes `INSTALL_K3S_EXEC='agent --selinux'`). `K3S_TOKEN` is the server's join token, typed on the agent and never written into a file the skill ships; where k3s stores it on the server is not on the pages read (`/var/lib/rancher/k3s/server/node-token` by analogy with RKE2, `unverified`). `--disable-default-registry-endpoint` stops containerd from trying the public endpoint "as a last resort", which the k3s docs describe as wanted in a true air-gapped environment. The Traefik version check of manifest section 4 is switched off as its row says (a HelmChartConfig in `/var/lib/rancher/k3s/server/manifests/` or `--disable=traefik`).

Checks:

```sh
grep nvidia /var/lib/rancher/k3s/agent/etc/containerd/config.toml
kubectl get nodes
```

The first on GPU nodes: a line naming the NVIDIA runtime (k3s found it). The second: every node `Ready`. K3s ships `kubectl` with `/etc/rancher/k3s/k3s.yaml` as its default configuration; where it is on the `PATH` is not documented, so when `kubectl` is not found the step's If not names `k3s kubectl get nodes` (`unverified`).

## RKE2

Files the skill writes: `kubernetes/cluster/config.yaml` and `kubernetes/cluster/registries.yaml` (the same layout as k3s above; RKE2's `auth` keys are `username`, `password`, `token`).

```yaml
disable-default-registry-endpoint: true
disable: [rke2-security-responder]
# SELinux-enforcing nodes only, on every server and agent:
selinux: true
```

`disable: [rke2-security-responder]` is the switch of the `rke2` catalog entry for the security responder that RKE2 v1.37 enables by default (servers only); the Traefik version check is placed as manifest section 4 writes it. `system-default-registry` stays unset: the system images come from the image archive, not from the registry. Agents add `server: https://SERVER_IP:9345` and `token: RKE2_TOKEN`; the token is read on the server from `/var/lib/rancher/rke2/server/node-token` and typed into the agent's copy by the runbook, never written into a shipped file.

Commands, as root. SELinux-enforcing nodes first install the policy, before RKE2 (the tarball path "never installs the policy for you"); a reboot is sometimes needed after it, the page does not say when:

```sh
yum -y install /root/rke2-selinux-rpms/*.rpm
```

Then on every node; the artifact folder holds exactly `rke2-images.linux-amd64.tar.zst`, `rke2.linux-amd64.tar.gz`, `sha256sum-amd64.txt` and `install.sh`, because `install.sh` copies every `rke2-images-*` file it finds there:

```sh
mkdir -p /root/rke2-artifacts /etc/rancher/rke2
cp rke2-images.linux-amd64.tar.zst rke2.linux-amd64.tar.gz sha256sum-amd64.txt install.sh /root/rke2-artifacts/
cp docs/airgap/install/kubernetes/cluster/config.yaml /etc/rancher/rke2/config.yaml
cp docs/airgap/install/kubernetes/cluster/registries.yaml /etc/rancher/rke2/registries.yaml
INSTALL_RKE2_ARTIFACT_PATH=/root/rke2-artifacts sh install.sh
systemctl enable rke2-server.service
systemctl start rke2-server.service
```

On agents: `INSTALL_RKE2_TYPE="agent" INSTALL_RKE2_ARTIFACT_PATH=/root/rke2-artifacts sh install.sh`, then `rke2-agent.service`. On arm64 the files carry `arm64` in place of `amd64`. Logs: `journalctl -u rke2-server -f` (or `rke2-agent`).

Checks (`kubectl` is not on the `PATH`):

```sh
export KUBECONFIG=/etc/rancher/rke2/rke2.yaml
/var/lib/rancher/rke2/bin/kubectl get nodes -o wide
```

Every node `Ready`, with the address the plan gives it.

## Existing cluster

No cluster is installed and no file under `kubernetes/cluster/` is written: the cluster belongs to its owners, and their change process is a step of the runbook. `INSTALL.md` step 2 becomes "Ask the cluster owners to", with each item and the answer to record:

1. Create the namespace `NAMESPACE`, or allow the install account to apply `00-namespace.yaml`.
2. Confirm that the GPU nodes expose `nvidia.com/gpu` (their device plugin or operator), how many per node, and on which nodes; the replicas of blueprint §5 must fit.
3. Give the nodes pull access to `REGISTRY_HOST`, or name the cluster's registry the images are pushed to instead (then the manifests name that registry).
4. Name the storage class for the claims of `10-STATE.yaml`, and confirm that `/srv/models` may be mounted from the GPU nodes as `hostPath`, or name the volume the model files go on instead.
5. OpenShift: name the security context constraint the namespace's service account gets. The default ones (`restricted-v2`, `restricted-v3`) drop all capabilities, forbid privilege escalation and assign the user ID from the namespace's range, so the manifests set no fixed `runAsUser`. Whether a plain Deployment with a root image, a `hostPath` volume and a GPU resource runs under them is not documented: ask, and record the answer before step 5 of the runbook.

The manifests stay plain Kubernetes; OpenShift Routes and other cluster objects are the owners' to add. Until every answer is recorded, the install stops after step 1.

## Sources

| Tool | Command or key | Source |
|---|---|---|
| K3s | `/var/lib/rancher/k3s/agent/images/`, `/usr/local/bin/k3s`, `INSTALL_K3S_SKIP_DOWNLOAD=true ./install.sh`, `K3S_URL`, `K3S_TOKEN`, `INSTALL_K3S_EXEC`, default route, `k3s-selinux` before K3s | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/installation/airgap.md |
| K3s | `/etc/rancher/k3s/registries.yaml`, `mirrors`, `endpoint`, `configs`, `auth`, `tls.ca_file`, `--disable-default-registry-endpoint` | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/installation/private-registry.md |
| K3s | `--selinux`, NVIDIA runtime found at start, `grep nvidia /var/lib/rancher/k3s/agent/etc/containerd/config.toml` | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/advanced.md |
| K3s | `kubectl` with `/etc/rancher/k3s/k3s.yaml` | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/cluster-access.md |
| K3s | Traefik version check switch | the `k3s` catalog entry (https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/add-ons/helm.md) |
| RKE2 | `INSTALL_RKE2_ARTIFACT_PATH=/root/rke2-artifacts sh install.sh`, artifact names, default route, `rke2-selinux` before RKE2 | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/install/airgap.md |
| RKE2 | `install.sh` copies every `rke2-images-*` file of the folder | https://github.com/rancher/rke2/blob/v1.37.2%2Brke2r1/install.sh |
| RKE2 | `/etc/rancher/rke2/config.yaml`, `disable-default-registry-endpoint`, `system-default-registry` | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/reference/server_config.md |
| RKE2 | `/etc/rancher/rke2/registries.yaml`, `auth` keys | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/install/private_registry.md |
| RKE2 | `systemctl enable/start rke2-server.service`, `journalctl -u rke2-server -f`, `INSTALL_RKE2_TYPE="agent"`, `server: https://…:9345`, `token`, `/var/lib/rancher/rke2/server/node-token` | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/install/quickstart.md |
| RKE2 | `/var/lib/rancher/rke2/bin/kubectl`, `KUBECONFIG=/etc/rancher/rke2/rke2.yaml` | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/cluster_access.md |
| RKE2 | `selinux: true`, `yum -y install /root/rke2-selinux-rpms/*.rpm`, reboot note | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/security/selinux.md |
| RKE2 | `disable: [rke2-security-responder]` | the `rke2` catalog entry (https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/add-ons/rke2-security-responder.md) |
| Kubernetes | `kubectl get nodes`, `Ready` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/debug/debug-cluster/_index.md |
| OpenShift | `restricted-v2`, `restricted-v3`, pre-allocated UID ranges | https://github.com/openshift/openshift-docs/blob/0d3597abb524d4e19875fa23cb815b47020ccf99/modules/security-context-constraints-about.adoc |
