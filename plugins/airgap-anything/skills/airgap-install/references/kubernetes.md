# Kubernetes manifests

## Contents

- Rules for every workload
- Manifests
- GPUs: the NVIDIA device plugin
- Exposure: the Ingress
- Sources

Goal: the files under `docs/airgap/install/kubernetes/`, one set for k3s, RKE2 and an existing cluster alike. The cluster-specific part (install, `registries.yaml`, `config.yaml`) is in `references/clusters.md`. Values come from the catalog entries and blueprint §5; anything else is labeled `unverified` with the runbook step that checks it.

## Rules for every workload

- Every image names the local registry: the manifest's Target path (`REGISTRY_HOST/…`) with the manifest's tag, never `latest`. With Harbor, a Target path without a project segment gets Harbor's default public project `library` (`REGISTRY_HOST/library/postgres:18.7`), as `references/compose.md` says and `plan.md` records.
- Every container sets `imagePullPolicy: IfNotPresent` explicitly. Why: when the field is omitted, Kubernetes sets `Always` for a `:latest` or untagged image and `IfNotPresent` otherwise, and the same docs page also says `IfNotPresent` "by default"; writing it removes the doubt. `IfNotPresent` (not `Never`) because the nodes fetch the image from the local registry on first use; `registries.yaml` with `disable-default-registry-endpoint` keeps them from trying the internet (`references/clusters.md`).
- GPUs only under `resources.limits` as `nvidia.com/gpu: N`, N = GPUs per replica of blueprint §5, and `replicas:` = its replicas. Why: Kubernetes takes the limit as the request, and "If you do not request GPUs when you use the device plugin, the plugin exposes all the GPUs on the machine inside your container". Never set `NVIDIA_VISIBLE_DEVICES=all` as a workaround.
- On k3s and RKE2, every GPU pod sets `runtimeClassName: nvidia`. k3s finds the NVIDIA runtime but starts pods with `runc` unless they ask for it. RKE2's documentation does not say that a host-installed NVIDIA runtime becomes containerd's default (its GPU page covers only the GPU Operator), so RKE2 gets the same runtime class; that RKE2 registers the `nvidia` handler is `unverified` and checked by `INSTALL.md` step 4b.
- Every Deployment that reserves GPUs sets `strategy: type: Recreate`. Why: with the default rolling update a new pod starts before the old one stops, and when the old pods hold the GPUs the new one stays pending, so a re-apply never finishes its rollout; with `Recreate`, "All existing Pods are killed before new ones are created".
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
| `70-ingress.yaml` | the Ingress for the gateway and the UI (below, "Exposure: the Ingress") |

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
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: vllm
  template:
    metadata:
      labels:
        app: vllm
    spec:
      # k3s and RKE2 (RKE2: unverified, INSTALL.md step 4b checks it); an existing cluster: as its owners say.
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
          # Directory: "A directory must exist at the given path."
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

`05-nvidia-device-plugin.yaml`: the static manifest of the plugin at tag v0.20.2, with the image on the local registry, the pull policy set and, on k3s and RKE2, the runtime class:

```yaml
# k3s and RKE2: the RuntimeClass of the plugin's README.
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
      # k3s and RKE2:
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

Keep both runtime-class parts on RKE2 too. The plugin's README requires the NVIDIA runtime as the default low-level runtime or a RuntimeClass, and RKE2's documentation does not say that the hosts' runtime becomes the default, so the RuntimeClass is the documented way (whether RKE2's containerd lists a `nvidia` handler for a host-installed toolkit is `unverified`; step 4b checks it). `INSTALL.md` step 4b (`references/runbook.md`) checks the result: `kubectl get node NODE -o jsonpath='{.status.allocatable}'` shows `"nvidia.com/gpu":` with blueprint §5's GPU count for every GPU node, after the registry and before any step 5 rollout.

Mixed clusters (GPU and CPU nodes): the static DaemonSet has no `nodeSelector`, so it runs on every node. The plugin's README describes GPU node labels through gpu-feature-discovery, which this skill does not deploy, and gives no selector for the static manifest, so none is written; on a node without GPUs the plugin's pod may fail to start under the `nvidia` runtime class (`unverified`), which does not change the count on the GPU nodes. Step 4b's If not tells these apart.

## Exposure: the Ingress

The Services above are `ClusterIP`, the default type, which is reachable only inside the cluster, so people and the runbook's smoke test (step 7) reach the gateway and the UI through an Ingress. On k3s, the packaged Traefik is the ingress controller and its LoadBalancer Service listens on ports 80 and 443 of the nodes. On RKE2, the `ingress-controller` key of `config.yaml` decides ("the first value will be set as the default ingress class"); which one RKE2 deploys when the key is unset is not on the page read (`unverified`). On an existing cluster, exposure is the owners' choice: `70-ingress.yaml` is written as a proposal, and `INSTALL.md` step 2 asks them (`references/clusters.md`).

`70-ingress.yaml`, with the host names of `questions.md` question 8 and the Service names and ports of `40-GATEWAY.yaml` and `50-UI.yaml` (LiteLLM's 4000, Open WebUI's 8080):

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: PROJECT
  namespace: NAMESPACE
spec:
  # No ingressClassName: the cluster's default class. unverified on k3s that Traefik is the default class;
  # an existing cluster: ingressClassName: the class its owners name.
  rules:
  - host: GATEWAY_HOSTNAME
    http:
      paths:
      - pathType: Prefix
        path: "/"
        backend:
          service:
            name: GATEWAY_SERVICE
            port:
              number: 4000
  - host: UI_HOSTNAME
    http:
      paths:
      - pathType: Prefix
        path: "/"
        backend:
          service:
            name: UI_SERVICE
            port:
              number: 8080
```

Without a gateway in the blueprint, leave the gateway rule out: the engine's `--api-key` does not protect every path, so vLLM is never exposed; step 7 then runs inside the cluster as step 5's check does. Without TLS (`questions.md` question 5), the Ingress serves HTTP on port 80; TLS is the open item of the plan. Each path needs a `pathType` ("Paths that do not include an explicit `pathType` will fail validation").

## Sources

| Tool | Command or key | Source |
|---|---|---|
| Kubernetes | `imagePullPolicy` values and defaults | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/containers/images.md |
| Kubernetes | `resources.limits` `nvidia.com/gpu` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/manage-gpus/scheduling-gpus.md |
| Kubernetes | `kubectl create secret generic --from-literal` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/configmap-secret/managing-secret-using-kubectl.md |
| Kubernetes | `valueFrom.secretKeyRef` (`name`, `key`) | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/examples/pods/inject/pod-single-secret-env-variable.yaml |
| Kubernetes | allocatable check `kubectl get node NODE -o jsonpath='{.status.allocatable}'` | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/add-ons/gpu_operators.md |
| Kubernetes | `kubectl apply -f DIR` lexical order, `-R` | https://github.com/kubernetes/kubernetes/blob/v1.37.2/staging/src/k8s.io/cli-runtime/pkg/resource/visitor.go |
| Kubernetes | Deployment (`replicas`, `selector`, `template`) | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/workloads/controllers/deployment.md |
| Kubernetes | Service (`port`, `targetPort`) | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/services-networking/service.md |
| Kubernetes | PersistentVolumeClaim, `ReadWriteOnce`, `claimName` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/storage/persistent-volumes.md |
| Kubernetes | Ingress (`rules`, `host`, `pathType: Prefix`, `backend.service.name`, `port.number`), default class when `ingressClassName` is omitted, `pathType` required | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/services-networking/ingress.md, https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/examples/service/networking/name-virtual-host-ingress.yaml |
| Kubernetes | `ClusterIP` is the default Service `type` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/services-networking/service.md |
| Kubernetes | `hostPath` `type: Directory` ("A directory must exist at the given path") | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/reference/storage/volume-types.md |
| Kubernetes | `strategy: type: Recreate` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/workloads/controllers/deployment.md |
| K3s | Traefik is the packaged ingress controller, LoadBalancer Service on ports 80 and 443 | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/networking/networking-services.md |
| RKE2 | `ingress-controller`: "the first value will be set as the default ingress class" | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/reference/server_config.md |
| RKE2 | no statement that a host NVIDIA runtime becomes containerd's default (advanced options, GPU page) | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/advanced.md, https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/add-ons/gpu_operators.md |
| Harbor | default public project `library` | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/working-with-projects/create-projects/_index.md |
| Kubernetes | Namespace | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/tasks/administer-cluster/namespaces.md |
| NVIDIA device plugin | static DaemonSet, image `nvcr.io/nvidia/k8s-device-plugin:v0.20.2`, namespace `kube-system` | https://github.com/NVIDIA/k8s-device-plugin/blob/v0.20.2/deployments/static/nvidia-device-plugin.yml |
| NVIDIA device plugin | RuntimeClass `nvidia`, default-runtime prerequisite, exposes all GPUs without a request, no air-gap install documented, node labels through gpu-feature-discovery | https://github.com/NVIDIA/k8s-device-plugin/blob/v0.20.2/README.md |
| K3s | `runtimeClassName: nvidia` | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/advanced.md |
| GPU Operator | installs images and restarts containerd (why the plugin is used instead) | https://github.com/rancher/rke2-docs/blob/3931bc85192e5d74abdfc43a499b0c6fae2274d2/docs/add-ons/gpu_operators.md |
| vLLM | mount `/dev/shm` in the pod spec; `--tensor-parallel-size` | https://github.com/vllm-project/vllm/blob/v0.34.0/docs/serving/parallelism_scaling.md |
| vLLM | image, port 8000, `VLLM_API_KEY`, egress variables | the `vllm` catalog entry (https://github.com/vllm-project/vllm/blob/v0.34.0/docs/deployment/docker.md) |
