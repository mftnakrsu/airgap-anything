# Install questions

Goal: the few facts the blueprint and the transfer manifest do not hold, asked in one message before the install plan. Skip a question the blueprint, the manifest, `docs/airgap/rag.md` or the conversation already answers; record every answer, and every default taken, in the Answers table of `plan.md` (`references/plan.md`).

## How to ask

- One message, in the user's language, with all the questions below whose "When" holds. Each question shows its default and why, so the user can answer "use the defaults" and the skill continues with them.
- Never ask for a password, a token or a key. Secrets are generated inside the network by a runbook step (`references/runbook.md`, step 4), so nobody on the connected side ever knows them.
- A fact nobody on the connected side knows (a mount point, an IP address that is assigned later) stays a placeholder in capitals, listed at the top of `INSTALL.md`. A placeholder is not a guess: the step that uses it says where the value comes from.

## Questions

| # | ID | Ask | Default and why | When |
|---|---|---|---|---|
| 1 | `approved` | Is the blueprint approved as it stands, or is any decision still open? | No default. The architect approves in conversation and leaves the blueprint's `Status:` line at "draft", so the file cannot show it. A yes is recorded in `plan.md` as "Blueprint approved by the user on DATE"; an open decision stops the skill and names `airgap-architect`, and nothing is written | Always, unless the user said in this conversation that it is approved |
| 2 | `hosts` | For each server of blueprint §5: its host name and its address inside the network, and which components run on it | Default: the placeholders `HOST_1`, `HOST_2` …, one per server, with the components placed as blueprint §3 and §5 place them. Why: the address is often assigned only inside; a placeholder in the runbook is filled once, at the top, instead of guessed in every file | Always |
| 3 | `paths.data` | Where does persistent data live on each host (databases, the registry, the vector store)? | Default: named volumes in Compose, PersistentVolumeClaims on the cluster's default storage class in Kubernetes. Why: both are created by the runtime itself and survive `docker compose down` without `-v`; a host path is only needed when the data must sit on a particular disk | Always |
| 4 | `paths.models` | Where are the model files on the serving hosts? | Default: `/srv/models`, the folder `INSIDE.md` (written by `airgap-transfer`) copies the model files into. Why: the install starts where the transfer ends, so the same path needs no second copy | The blueprint serves a model |
| 5 | `tls` | TLS between clients and the services: an internal certificate authority, or none? | Default: none, with a step that names the open item. Why: certificates and keys are secrets that belong to the network's owners and are created inside, so the skill can only leave a slot for them; a TLS proxy the blueprint chose is still deployed, and its certificate step uses the placeholder `CERT_DIR`. Consequence to tell the user: without TLS, Docker needs the registry under `insecure-registries`, and Harbor's documentation calls HTTP acceptable only in air-gapped test or development environments | Always |
| 6 | `inside.operator` | Who runs the install inside: people, a local agent, or people first and then an agent? | Default: `people`. Why: usually the model being installed is the only LLM inside, so nobody can ask one for help during the install; `INSTALL.md` needs neither | The blueprint has no `inside.operator`, or it is `unknown` |
| 7 | `custom.FACTS` | For each component outside the catalog (the user's own service, a custom platform from `rag.md`): its image and tag, port, data path, health endpoint, environment variables and their meaning | No default. Why: the skill writes such a component only from the user's facts, each labeled `unverified`; a missing fact is asked here, never filled in | The blueprint or `rag.md` has a `custom:` component |
| 8 | `exposure` | Kubernetes only: the host names people and the runbook's smoke test use for the UI and the gateway, which the network's DNS resolves to the cluster's nodes (k3s, RKE2) or to the owners' ingress (existing cluster) | Default: the placeholders `UI_HOSTNAME` and `GATEWAY_HOSTNAME`, filled at the top of `INSTALL.md`, and an Ingress in `70-ingress.yaml` (`references/kubernetes.md`, "Exposure"). Why: the Services are `ClusterIP`, reachable only inside the cluster; on k3s the packaged Traefik is the ingress controller. On an existing cluster, how a service is exposed is the owners' choice: the file is a proposal, and the runbook asks them | The orchestration is Kubernetes |

`inside.operator` decides the runbooks: `people` gets `INSTALL.md`, `local_agent` gets `AGENTS-INSTALL.md`, `people_then_agent` gets both (the same table as `airgap-transfer`'s).

## Sources

| Tool | Command or key | Source |
|---|---|---|
| Docker Compose | `docker compose down` keeps named volumes unless `-v` | https://github.com/docker/compose/blob/v5.8.0/docs/reference/compose_down.md |
| Kubernetes | PersistentVolumeClaim | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/storage/persistent-volumes.md |
| Harbor | HTTP acceptable only in air-gapped test or development; `insecure-registries` | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/install-config/configure-yml-file.md |
| Harbor | `insecure-registries` in `/etc/docker/daemon.json` for HTTP | https://github.com/goharbor/website/blob/1ce1ac23f8d4969ce587b7ced8afb7954f76115d/docs/install-config/run-installer-script.md |
| Kubernetes | Ingress rules apply to a `host` and route to a Service | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/services-networking/ingress.md |
| Kubernetes | `ClusterIP` is the default Service `type` | https://github.com/kubernetes/website/blob/adf3bf8ca5ad2caf642cbe4d7dd82e8b0eead607/content/en/docs/concepts/services-networking/service.md |
| K3s | the packaged Traefik is the ingress controller | https://github.com/k3s-io/docs/blob/8b33d6f4106826376a9784bc21d0fbba8dccbc69/docs/networking/networking-services.md |
