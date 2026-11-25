# Kubernetes manifests

## Contents

- Rules for every workload
- Manifests
- GPUs: the NVIDIA device plugin
- Sources

Goal: the files under `docs/airgap/install/kubernetes/`, one set for k3s, RKE2 and an existing cluster alike. The cluster-specific part (install, `registries.yaml`, `config.yaml`) is in `references/clusters.md`. Values come from the catalog entries and blueprint §5; anything else is labeled `unverified` with the runbook step that checks it.

## Rules for every workload

- Every image names the local registry: the manifest's Target path (`REGISTRY_HOST/…`) with the manifest's tag, never `latest`.
- Every container sets `imagePullPolicy: IfNotPresent` explicitly. Why: when the field is omitted, Kubernetes sets `Always` for a `:latest` or untagged image and `IfNotPresent` otherwise, and the same docs page also says `IfNotPresent` "by default"; writing it removes the doubt. `IfNotPresent` (not `Never`) because the nodes fetch the image from the local registry on first use; `registries.yaml` with `disable-default-registry-endpoint` keeps them from trying the internet (`references/clusters.md`).
- GPUs only under `resources.limits` as `nvidia.com/gpu: N`, N = GPUs per replica of blueprint §5, and `replicas:` = its replicas. Why: Kubernetes takes the limit as the request, and "If you do not request GPUs when you use the device plugin, the plugin exposes all the GPUs on the machine inside your container". Never set `NVIDIA_VISIBLE_DEVICES=all` as a workaround.
- On k3s, every GPU pod sets `runtimeClassName: nvidia`: k3s finds the NVIDIA runtime but starts pods with `runc` unless they ask for it.
- Secrets are created by a runbook step with `kubectl create secret generic … --from-literal`, never written as YAML values; workloads read them with `secretKeyRef`.
- File names start with a number in the plan's start order. `kubectl apply -f DIR` walks the files in lexical order (read from kubectl's source, not documented) and does not stop at the first error (not documented either), so the runbook applies the files one at a time, Namespace and Secrets first, and checks each rollout before the next.
- A component outside the catalog is written from the user's facts, every line it adds labeled `unverified`.

## Manifests

| File | Holds |
|---|---|
| `00-namespace.yaml` | the Namespace |
| `05-nvidia-device-plugin.yaml` | k3s and RKE2 with GPUs only (below); on an existing cluster the owners provide GPU support |
| `10-STATE.yaml` | databases, cache, vector store: PersistentVolumeClaim, Deployment, Service |
| `20-SERVING.yaml` | vLLM (chat), then its embedding and reranking instances |
| `30-EXTRACTION.yaml` | docling-serve or another extractor |
| `40-GATEWAY.yaml` | the LLM gateway and the identity provider |
| `50-UI.yaml` | the chat UI and a RAG server |
| `60-OBSERVABILITY.yaml` | metrics and dashboards |

The registry has no file here: Harbor (or the Distribution Registry) runs before the cluster pulls anything, with Compose on its host (`references/compose.md`). Replace each capital word by the component's name (`20-vllm.yaml`); one file per component.

`00-namespace.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: NAMESPACE
```

`20-vllm.yaml`, with `R` the replicas and `N` the GPUs per replica of blueprint §5 (18 replicas of 1 GPU: `replicas: 18`, `nvidia.com/gpu: 1`, `--tensor-parallel-size 1`), `MODEL_DIR` and `SERVED_NAME` from manifest section 2 and the blueprint, the `env` lines of manifest section 4:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: vllm
  namespace: NAMESPACE
spec:
  replicas: R
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      # k3s only:
      runtimeClassName: nvidia
      containers:
      - name: vllm
        image: REGISTRY_HOST/vllm/vllm-openai:v0.34.0
        imagePullPolicy: IfNotPresent
        args: ["/srv/models/MODEL_DIR", "--served-model-name", "SERVED_NAME", "--tensor-parallel-size", "N"]
        ports:
        - containerPort: 8000
        env:
        - name: VLLM_API_KEY
          valueFrom:
            secretKeyRef:
              name: vllm
              key: api-key
        - name: VLLM_NO_USAGE_STATS
          value: "1"
        - name: HF_HUB_DISABLE_TELEMETRY
          value: "1"
        - name: HF_HUB_OFFLINE
          value: "1"
        resources:
          limits:
            nvidia.com/gpu: N
        volumeMounts:
        - name: models
          mountPath: /srv/models
        - name: shm
          mountPath: /dev/shm
      volumes:
      - name: models
        hostPath:
          path: /srv/models
          type: Directory
      # vLLM's parallelism page: mount /dev/shm in the pod spec. unverified: emptyDir with medium Memory as the way to do it.
      - name: shm
        emptyDir:
          medium: Memory
---
apiVersion: v1
kind: Service
metadata:
  name: vllm
  namespace: NAMESPACE
spec:
  selector:
    app: vllm
  ports:
  - port: 8000
    targetPort: 8000
```

The model folder is a `hostPath` on each GPU node, where `INSIDE.md` copied the model files (`/srv/models`); every node that may run a replica needs the same folder. No readiness probe is written: the catalog documents no health endpoint for Kubernetes probes, so readiness is `unverified` and the runbook checks `/v1/models` after the rollout.

`10-STATE.yaml` keeps its data in a claim on the cluster's default storage class (or the class the owners name):

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: COMPONENT-data
  namespace: NAMESPACE
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: SIZE
```

`SIZE` comes from the blueprint's `state` decision or `rag.md`'s sizing; when neither gives one, it is an open item in `plan.md`. The Deployment mounts it with `persistentVolumeClaim: claimName: COMPONENT-data` and runs `replicas: 1`.

## GPUs: the NVIDIA device plugin

On k3s and RKE2 with GPUs, the cluster exposes `nvidia.com/gpu` only once the device plugin runs. The skill uses the plugin, not the GPU Operator: the operator installs drivers, the toolkit and a dozen images and restarts containerd, while the drivers and toolkit are already on the hosts (`nvidia-datacenter-bringup`). The plugin's README documents no air-gapped install, so its offline behavior is `unverified`. Add its image to manifest section 1 as `nvcr.io/nvidia/k8s-device-plugin:v0.20.2` with Target path `REGISTRY_HOST/nvidia/k8s-device-plugin:v0.20.2`, marked "(from airgap-install)".

`05-nvidia-device-plugin.yaml`: the static manifest of the plugin at tag v0.20.2, with the image on the local registry, the pull policy set and, on k3s, the runtime class:

```yaml
# k3s only: the RuntimeClass of the plugin's README.
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: nvidia
handler: nvidia
---
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: nvidia-device-plugin-daemonset
  namespace: kube-system
spec:
  selector:
    matchLabels:
      name: nvidia-device-plugin-ds
  updateStrategy:
    type: RollingUpdate
  template:
    metadata:
      labels:
        name: nvidia-device-plugin-ds
    spec:
      # k3s only:
      runtimeClassName: nvidia
      tolerations:
      - key: nvidia.com/gpu
        operator: Exists
        effect: NoSchedule
      priorityClassName: "system-node-critical"
      containers:
      - image: REGISTRY_HOST/nvidia/k8s-device-plugin:v0.20.2
        imagePullPolicy: IfNotPresent
        name: nvidia-device-plugin-ctr
        env: []
        securityContext:
          allowPrivilegeEscalation: false
          capabilities:
            drop: ["ALL"]
        volumeMounts:
        - name: kubelet-device-plugins-dir
          mountPath: /var/lib/kubelet/device-plugins
      volumes:
      - name: kubelet-device-plugins-dir
        hostPath:
          path: /var/lib/kubelet/device-plugins
          type: Directory
```

On RKE2, drop the two `k3s only` parts unless the hosts' NVIDIA runtime is not the default; the plugin's README requires the NVIDIA runtime as the default low-level runtime or a RuntimeClass. Whether the RKE2 hosts have it as the default is `unverified` and checked by the runbook: each GPU node reports `nvidia.com/gpu` allocatable.

## Sources

| Tool | Command or key | Source |
|---|---|---|
| Kubernetes | `imagePullPolicy` values and defaults | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/containers/images.md |
| Kubernetes | `resources.limits` `nvidia.com/gpu` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/manage-gpus/scheduling-gpus.md |
| Kubernetes | `kubectl create secret generic --from-literal` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/configmap-secret/managing-secret-using-kubectl.md |
| Kubernetes | `valueFrom.secretKeyRef` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/inject-data-application/distribute-credentials-secure.md |
| Kubernetes | `kubectl apply -f DIR` lexical order, `-R` | https://github.com/kubernetes/kubernetes/blob/v1.37.2/staging/src/k8s.io/cli-runtime/pkg/resource/visitor.go |
| Kubernetes | Deployment (`replicas`, `selector`, `template`) | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/workloads/controllers/deployment.md |
| Kubernetes | Service (`port`, `targetPort`) | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/services-networking/service.md |
| Kubernetes | PersistentVolumeClaim, `ReadWriteOnce`, `claimName` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/storage/persistent-volumes.md |
| Kubernetes | Namespace | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/administer-cluster/namespaces.md |
| NVIDIA device plugin | static DaemonSet, image `nvcr.io/nvidia/k8s-device-plugin:v0.20.2`, namespace `kube-system` | https://github.com/NVIDIA/k8s-device-plugin/blob/v0.20.2/deployments/static/nvidia-device-plugin.yml |
| NVIDIA device plugin | RuntimeClass `nvidia`, default-runtime prerequisite, exposes all GPUs without a request, no air-gap install documented | https://github.com/NVIDIA/k8s-device-plugin/blob/v0.20.2/README.md |
| K3s | `runtimeClassName: nvidia` | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/advanced.md |
| GPU Operator | installs images and restarts containerd (why the plugin is used instead) | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/add-ons/gpu_operators.md |
| vLLM | mount `/dev/shm` in the pod spec; `--tensor-parallel-size` | https://github.com/vllm-project/vllm/blob/v0.34.0/docs/serving/parallelism_scaling.md |
| vLLM | image, port 8000, `VLLM_API_KEY`, egress variables | the `vllm` catalog entry (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/deployment/docker.md) |
