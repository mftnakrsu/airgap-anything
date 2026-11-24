<p align="center">
  <img src="assets/brand/icon-tile-animated.svg" width="96" height="96" alt="">
</p>

<h1 align="center">airgap-anything</h1>

<p align="center">Design any system for air-gapped environments.</p>

<p align="center">
  <a href="https://github.com/mftnakrsu/airgap-anything/actions/workflows/ci.yml"><img src="https://github.com/mftnakrsu/airgap-anything/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/Agent%20Skills-markdown%20only-blue" alt="Agent Skills, markdown only">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"></a>
</p>

<p align="center">
  <a href="#install"><b>Install</b></a> ·
  <a href="#use">Use</a> ·
  <a href="examples/department/blueprint.md">Example</a> ·
  <a href="https://airgap-anything.mefby.com">Docs</a> ·
  <a href="CONTRIBUTING.md">Contributing</a> ·
  <a href="#türkçe">Türkçe</a>
</p>

`airgap-anything` is a plugin of agent skills for networks without internet access. You describe your organization; your agent designs the whole system, sizes the GPUs, lists everything that has to be carried in, and packs it into a bundle that checks itself on the other side.

The skills are plain markdown: no scripts, no dependencies, nothing to install but the folder. They work in Claude Code, Codex, Cursor and every agent that reads [Agent Skills](https://agentskills.io), and they work inside the air gap too, on a local model.

<p align="center">
  <img src="assets/brand/how-it-works.svg" alt="Eight steps on a connected workstation, done by the agent and you. The files cross the air gap, and the people or the agent inside build the system without internet." width="880">
</p>

## Skills

| Skill | What it does | Where it runs |
|---|---|---|
| [`airgap-architect`](plugins/airgap-anything/skills/airgap-architect/SKILL.md) | Interviews you, then writes the blueprint: one decision per layer with its reasons and alternatives, GPU sizing with every step shown, and the transfer manifest of what to carry in | A connected workstation |
| [`airgap-transfer`](plugins/airgap-anything/skills/airgap-transfer/SKILL.md) | Turns the transfer manifest into a bundle that checks itself: fetch commands you approve first, a SHA-256 list, a split across media, an inventory, and a runbook or agent rules for the inside | A connected workstation; its runbook runs inside |

Coming next: [`airgap-rag`](https://github.com/mftnakrsu/airgap-anything/issues/11) for document search inside the network and [`airgap-agent`](https://github.com/mftnakrsu/airgap-anything/issues/10) for coding agents on the local model. Ideas for more are in [#12](https://github.com/mftnakrsu/airgap-anything/issues/12).

## Why

Architecture skills usually assume internet access and hosted services. Skills for air-gapped work usually explain one tool at a time. `airgap-anything` is the layer above: one interview, one blueprint for the whole stack, written for a network where nothing can be looked up or downloaded.

From memory, an agent writes versions, image names and GPU counts that look right and are not sourced; inside the network a wrong one costs another trip. Here every component, version and image comes from a [catalog](plugins/airgap-anything/skills/airgap-architect/catalog) where each value carries its source, and every number comes from a sizing procedure the agent writes out step by step.

The skills decide; they do not operate. For the details of running each tool, catalog entries point to existing per-tool skills.

## Install

Install it once; after that you only ask (see [Use](#use)).

### Claude Code

In a Claude Code session:

```
/plugin install airgap-anything --marketplace mftnakrsu/airgap-anything
```

Claude Code asks you to confirm the new marketplace, then lets you choose where to install. The plugin carries both skills. This form needs Claude Code 2.1.275 or newer; from your shell, `claude plugin install airgap-anything --marketplace mftnakrsu/airgap-anything` does the same with 2.1.292 or newer. On older versions, add the marketplace first:

```
/plugin marketplace add mftnakrsu/airgap-anything
/plugin install airgap-anything@airgap-anything-marketplace
```

### Codex

```bash
codex plugin marketplace add mftnakrsu/airgap-anything
```

Then install airgap-anything from the plugin directory in Codex or the ChatGPT desktop app.

### Cursor and other agents that support Agent Skills

```bash
npx skills add mftnakrsu/airgap-anything -g
```

This installs both skills. To install one, add `--skill`, for example `npx skills add mftnakrsu/airgap-anything -g --skill airgap-transfer`.

`-g` installs them for your user, so every project has them; without `-g` they go into the current project only. Add `-a` and an agent ID to choose the agent, for example `-a cursor`, `-a codex`, `-a opencode` or `-a antigravity`. The [skills CLI](https://github.com/vercel-labs/skills) supports Claude Code, Codex, Cursor, OpenCode and 75 more agents; its [agent list](https://github.com/vercel-labs/skills/blob/main/docs/agents.md) has the IDs. This route needs Node.js 22.20 or newer.

### Without internet

On a connected machine, in a clone of this repository:

```bash
for skill in airgap-architect airgap-transfer; do
  git archive --format=tar.gz --prefix=$skill/ -o $skill.tar.gz HEAD:plugins/airgap-anything/skills/$skill
  sha256sum $skill.tar.gz > $skill.tar.gz.sha256
done
```

Carry the four files in, then:

```bash
for skill in airgap-architect airgap-transfer; do
  sha256sum -c $skill.tar.gz.sha256 && mkdir -p ~/.claude/skills && tar -xzf $skill.tar.gz -C ~/.claude/skills/
done
```

`~/.claude/skills/` is where Claude Code keeps personal skills; Codex reads `~/.agents/skills/`. Use your agent's own skills folder if it differs. Nothing else is needed: the skills are markdown.

## Use

Ask your agent, in your own words, on a machine with internet access:

> Design an air-gapped LLM platform for my organization.

You do not need to name the skill. Claude Code picks it when a request is about designing, planning or sizing a system for an air-gapped, offline or on-premises network, and leaves other requests alone; [a test](evals/results/2026-11-23-triggering.md) checks this in English and Turkish. In Claude Code you can also start it directly: with `/airgap-anything:airgap-architect` after the plugin install, or with `/airgap-architect` when it is installed as a personal or project skill.

The agent then works through these steps and ticks them off as it goes:

| # | Step | Who |
|---|---|---|
| 1 | Interview: people, departments, privacy, hardware, operations | the agent, one question at a time |
| 2 | Tier and per-layer floors | the agent, from the tier table |
| 3 | GPU, server and power sizing, every step written out | the agent, from the sizing procedure |
| 4 | One decision per layer, from the layer guides and the catalog | the agent |
| 5 | Transfer manifest | the agent, from the catalog entries |
| 6 | Blueprint, and the agent block in `AGENTS.md` | the agent |
| 7 | Self-review against a checklist, until every item holds | the agent |
| 8 | Your approval, then hand-off to an implementation plan | you |

### Carrying it in

Once the blueprint is approved, ask in your own words, for example "prepare everything in the transfer manifest for our USB disks". `airgap-transfer` then works through these steps:

| # | Step | Who |
|---|---|---|
| 1 | A few questions: where to build the bundle, where each model comes from, the medium or the channel's file limit | the agent |
| 2 | The plan: every item, the tools, the known sizes | the agent |
| 3 | Your approval, then the download | you, or the agent after you approve |
| 4 | Manual items: add files or mark them not needed | you |
| 5 | Checksums, split, volumes, inventory, runbook or agent rules | the agent |
| 6 | Self-check, then one medium at a time, read back | the agent |

Inside, on any Linux host, the runbook checks every file with `sha256sum -c` before anything is loaded. When a file is missing or damaged, it names the file and the volume it came on.

## What you get

```
your-project/
├── docs/airgap/blueprint.md            the blueprint (under docs/superpowers/specs/ with superpowers)
├── docs/airgap/transfer-manifest.md    images, models, packages and settings to carry in
├── docs/airgap/transfer-plan.md        the transfer's answers, items and volumes
└── AGENTS.md                           instructions for the agent that builds it inside the network
```

The bundle itself lives outside the repository, with `SHA256SUMS`, `INVENTORY.md` and `INSIDE.md` (or `AGENTS-INSIDE.md`) on every volume. Inside, people follow the runbook, an agent follows its rules, and nobody needs internet access.

The [department example](examples/department/blueprint.md) is a complete blueprint for 180 people in four departments, one 671-billion-parameter model on eight 141 GB GPUs:

| Layer | Decision |
|---|---|
| `llm-serving` | `vllm`, one replica on all eight GPUs, prefix caching off so departments share no cached prompts |
| `llm-gateway` | `litellm`, for per-department keys, budgets and audit |
| `ui` | `open-webui`, one instance per department |
| `identity` | `keycloak` federated to Active Directory |
| `observability` | `prometheus` and `grafana` |
| `orchestration` | `docker-compose` |
| `state` | `postgresql` and `valkey` |
| `registry` | `harbor` |

Tier T2. Peak concurrency 9 to 18 requests in flight. 8 GPUs in 1 server, about 10.1 kW. Every number has its arithmetic in the blueprint, and every decision lists the alternatives it beat.

## Tiers and sizing are separate

A tier (T1 single team, T2 department, T3 enterprise) measures how complex the organization is: how many people and departments, and whether audit, isolation or zero downtime is required. It selects patterns such as "gateway or not" and "Compose or Kubernetes".

GPU count is a different question. It comes from the size of the model, the kind of usage and the headcount. A small team that serves a very large model needs many GPUs at T1.

Sizing covers memory, not speed. Every blueprint carries a "benchmark before production" step.

## Evidence labels

Every catalog entry, threshold and default carries one label.

| Label | Meaning |
|---|---|
| `field` | Verified in a real deployment by a named person |
| `docs` | Taken from official project or vendor documentation, or, where the documentation is silent, from the project's source code at the release tag; the URL is recorded |
| `estimate` | Reasoned or community-sourced; verify before relying on it |

A decision inherits the weakest label among its inputs. Every decision that rests on an estimate is listed in the blueprint's verification section.

## Scope

In version 0.3:

- Layer guides for the inference engine and the LLM gateway, and per-tier defaults for UI, identity, observability, orchestration, state stores and artifact registry.
- Sizing from organization answers, a transfer manifest, and a self-review.
- `airgap-transfer`: a plan and fetch commands from the transfer manifest, a checked bundle split across media, and a runbook or agent rules for the inside.

Not in version 0.3:

- Deployment files such as Docker Compose or Helm.
- A recommendation of which model to run.
- Guides for data, CI/CD and security layers.
- Compliance mappings.

## Works with superpowers

When [superpowers](https://github.com/obra/superpowers) is installed, the blueprint is written where its specs live and handed to `superpowers:writing-plans` after you approve it. Without superpowers the skills work on their own.

## Contributing

The catalog is the part that ages, and it is markdown: adding or re-verifying a component is a small pull request. [CONTRIBUTING.md](CONTRIBUTING.md) explains how. One rule above all: nothing is written from memory.

Logo files and their usage rules are in the [brand guide](assets/brand/BRAND.md).

## License

MIT. See [LICENSE](LICENSE).

## Türkçe

`airgap-anything`, internete kapalı (air-gapped) ağlar için agent skill'lerinden oluşan bir plugin'dir. Kurumunuzu anlatırsınız; agent'ınız tüm sistemi tasarlar, GPU'ları hesaplar, ağın içine taşınması gereken her şeyi listeler ve bunu öbür tarafta kendini denetleyen bir pakete dönüştürür.

Skill'ler düz markdown'dır: betik yok, bağımlılık yok, klasörden başka kurulacak bir şey yok. Claude Code, Codex, Cursor ve [Agent Skills](https://agentskills.io) okuyan her agent'ta çalışır; internete kapalı ağın içinde, yerel bir modelle de çalışır.

`airgap-architect` kurumunuzla kısa bir görüşme yapar ve bir blueprint yazar: her katman için gerekçesi ve alternatifleriyle bir karar, her adımı yazılmış GPU, sunucu ve güç hesabı, ağa taşınacak her şeyin listesi. `airgap-transfer` bu listeyi kendini denetleyen bir pakete çevirir: önce sizin onayladığınız indirme komutları, SHA-256 listesi, disklere bölme, envanter ve içeride insanlar için bir çalıştırma kılavuzu ya da içerideki agent için kurallar. İçeride hiçbir adım internet ya da LLM gerektirmez.

**Kurulum.** Bir kez kurarsınız; sonrasında yalnızca sorarsınız. Claude Code oturumunda:

```
/plugin install airgap-anything --marketplace mftnakrsu/airgap-anything
```

Bu biçim Claude Code 2.1.275 veya üstünü ister. Daha eski sürümlerde önce marketplace'i ekleyin:

```
/plugin marketplace add mftnakrsu/airgap-anything
/plugin install airgap-anything@airgap-anything-marketplace
```

Codex'te `codex plugin marketplace add mftnakrsu/airgap-anything`, ardından plugin dizininden kurun. Cursor ve Agent Skills standardını destekleyen diğer agent'larda (agent seçmek için `-a`, örneğin `-a cursor`):

```bash
npx skills add mftnakrsu/airgap-anything -g
```

İnternetsiz kurulum için yukarıdaki [Without internet](#without-internet) bölümüne bakın.

**Kullanım.** İnternete bağlı bir makinede agent'ınıza kendi cümlenizle sorun, örneğin:

> Kurumum için internete kapalı bir LLM platformu tasarla.

Skill'in adını söylemeniz gerekmez: Claude Code, internete kapalı, çevrimdışı ya da kurum içi bir ağ için sistem tasarlama, planlama veya boyutlandırma isteklerinde skill'i kendisi seçer, başka isteklerde seçmez. Bunu Türkçe ve İngilizce isteklerle ölçen bir test vardır. Claude Code'da skill'i doğrudan da başlatabilirsiniz: plugin olarak kurduysanız `/airgap-anything:airgap-architect`, kişisel ya da proje skill'i olarak kurduysanız `/airgap-architect` yazın.
