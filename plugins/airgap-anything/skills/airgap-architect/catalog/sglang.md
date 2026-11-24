# SGLang (`sglang`)

Open-source serving framework for language, vision-language and diffusion models with a prefix-caching scheduler (RadixAttention) and OpenAI-, Anthropic- and Ollama-compatible HTTP APIs.

| Field | Value |
|---|---|
| Layer | `llm-serving` |
| Version | `v0.5.23` |
| License | Apache-2.0 |
| Tiers | T1, T2, T3 |
| Requires | none |
| Evidence | docs |
| Last verified | 2026-11-22 |

## Choose when

- Workloads that reuse long shared prefixes or many turns, and agentic and RL-rollout serving: the README says SGLang is 'optimized for agentic workloads, large-scale serving, and RL rollouts', the documentation home page says it is 'designed to deliver low-latency and high-throughput inference across a wide range of setups, from a single GPU to large distributed clusters' with 'RadixAttention, prefix caching, and multi-GPU parallelism', and the session radix cache page says session-aware radix caching 'improves cache hits for long-lived, multi-turn workloads under memory pressure'. (Documentation statements only, no benchmark.)
- Many users are served at the same time on GPUs: the only continuous-batching statement found is in the SGLang Model Gateway section of the RL guide (sglang_for_rl.mdx), about the RL-rollout control plane: its native async server and router architecture 'manages concurrency automatically' with 'effective continuous batching'; no general continuous-batching statement was found in the server documentation. The documented scheduler settings are --max-running-requests (maximum number of running requests), --max-queued-requests (maximum number of queued requests, ignored in disaggregation mode), --max-prefill-tokens (default 16384), --chunked-prefill-size (-1 disables chunked prefill), --schedule-policy (default fcfs; also lpm, random, dfs-weight, lof, priority, routing-key) and --schedule-conservativeness (default 1.0); both request limits default to none.
- Clients speak the OpenAI, Anthropic Messages (/v1/messages, registered automatically on every server) or Ollama APIs: the basic usage pages document all three, plus a native API and an offline engine API.
- A model must be spread over several GPUs: the server arguments list tensor (--tp-size), pipeline (--pp-size), data (--dp-size) and expert parallelism.

## Avoid when

- The only hardware is a CPU that is not an Intel Xeon with AMX: the CPU Servers page says SGLang is 'enabled and optimized on the CPUs equipped with Intel AMX instructions, which are 4th generation or newer Intel Xeon Scalable Processors' (image tag suffix xeon), so it does run without a GPU on those CPUs only, as far as the pages read state; vLLM and Ollama document wider CPU support.

## Alternatives

`vllm`, `ollama`.

## Caveats

- Engine decision table, GPU-free operation: documented for Intel Xeon with AMX (CPU Servers page); the README also lists Apple Silicon through Metal and MLX, a GPU backend, so it is not a GPU-free path. GPU installs: NVIDIA with CUDA 13 (the install page says CUDA 12 images are retired and v0.5.19-cu129 is the last CUDA 12 tag), AMD Instinct, Intel GPU, Ascend NPUs, TPU, Moore Threads.
- Authentication: --api-key sets the API key of the server and the OpenAI-compatible server, and --admin-api-key protects administrative endpoints such as weight updates, cache flush and /server_info; the default is no key, so set one or put a proxy in front of a server that listens beyond 127.0.0.1.
- The images are large and the documentation recommends --ipc=host and --shm-size 32g for the NVIDIA container (install page); the Docker examples map port 30000.
- No paid edition or license check was found in the documentation.
- Radix cache, what is shared and what separates callers when departments share one server: the radix (prefix) cache is on by default (server arguments page: --disable-radix-cache, 'Disable RadixAttention for prefix caching', default False), and without a per-request setting all requests to one server can reuse each other's cached prefixes (source code at the tag, python/sglang/srt/mem_cache/radix_cache.py: a request without extra_key and cache_salt is matched on its tokens alone). The documentation at the tag says nothing about isolation between users or tenants, timing side channels or cache_salt, so the rest of this caveat comes from the source code at the tag, not from documentation. Per-request separation: the completions, chat completions and responses requests of the OpenAI-compatible server take a cache_salt field and an extra_key field ('for caller-defined request classification'; entrypoints/openai/protocol.py); the source calls cache_salt a 'Cache namespace used to isolate otherwise-identical prefixes' (managers/io_struct.py) and says it 'Namespaces the tree, storage and KV events' (RadixKey in radix_cache.py), so only requests with the same salt match each other's cached prefixes. RadixKey does `cache_salt or None` (radix_cache.py), so an empty-string salt means no salt. Turning the cache off instead: --disable-radix-cache (server arguments page); the cost of turning it off is not documented.
- Radix cache, what is not documented (documentation and source at v0.5.23): whether cache_salt is meant as a security boundary, how long a salt may be, and whether any request path drops it. No SGLang source or documentation read mentions a gateway for this, and how a gateway sets or scopes the salt per department is not documented for the gateways of this catalog (the LiteLLM entry's sources document no per-team or per-key request parameters).
- If several departments share one SGLang and org.isolation is not none, the decision's rationale must say which of these applies: a dedicated SGLang instance per department; or the radix cache switched off; or a distinct random secret cache_salt per department on every request, set by whatever sits in front of the engine (the gateway wording comes from the vLLM entry's security page, not from an SGLang source), with the note that this rests on source code, not on documentation. A design that leaves the radix cache on and sets nothing per department is wrong, and keeping the departments apart only in the UI does not isolate their cached prompts.

## Carry in

### Images

| Image | Hardware | Digest |
|---|---|---|
| `lmsysorg/sglang:v0.5.23-runtime` | nvidia | not recorded |
| `lmsysorg/sglang:v0.5.23-xpu` | intel | not recorded |
| `lmsysorg/sglang:v0.5.23-xeon` | cpu | not recorded |

### Packages

None.

### Runtime downloads to stage in advance

- Model weights, configuration and tokenizer: --model-path takes 'a local folder or a Hugging Face repo ID'; with a repo ID SGLang downloads the model on first use (examples page: 'SGLang downloads the model on first use'), into the Hugging Face cache, which the Docker examples mount from the host (-v $HF_CACHE_DIR:/root/.cache/huggingface); --download-dir sets 'Model download directory for huggingface'. Stage the model on a connected host and either copy the cache or pass the local folder as --model-path (--tokenizer-path takes a tokenizer path). Gated or private models need HF_TOKEN.
- Hugging Face offline switch: HF_HUB_OFFLINE=1 makes huggingface_hub make no HTTP calls to the Hub and use only cached files, raising an error when a file is missing (huggingface_hub documentation); SGLang's source checks the same setting before querying the Hub. The SGLang pages themselves document no offline switch and no air-gap procedure.
- ModelScope instead of Hugging Face: set SGLANG_USE_MODELSCOPE=true (the page notes that ModelScope uses a different cache directory).
- Remote weights: object storage URIs (s3://, gs://, az://) and remote URIs are loaded over the network by the runai_streamer and remote load formats, and --load-format remote_instance pulls weights from another running SGLang instance; none of these is needed for a local folder.

### Telemetry and egress to switch off before the first start

1. Hugging Face library telemetry: the huggingface_hub documentation says some data is collected by default by Hugging Face libraries such as transformers; SGLang depends on transformers and huggingface_hub (python/pyproject.toml). The SGLang documentation does not mention it, and whether SGLang triggers it was not verified.
   Switch off: HF_HUB_DISABLE_TELEMETRY=1 (DO_NOT_TRACK is documented by huggingface_hub as equivalent).

### License server

None: no license check needs connectivity.

### Air-gap notes

Offline behavior is documented only in part and not verified: the entry author did not run SGLang, and the documentation has no air-gap page. Images, one per hardware class named in the documentation (tags checked on Docker Hub on 2026-11-21; the install page says SGLang images ship a CUDA 13 environment and that CUDA 12 images are no longer published): lmsysorg/sglang:v0.5.23-runtime for NVIDIA GPUs, the smaller runtime image of the release (the install page: inference dependencies and fewer development utilities, tag latest-runtime); it is a multi-architecture manifest list (amd64 and arm64), so copy the platform of the target hosts; the full image lmsysorg/sglang:v0.5.23 (the same digest as v0.5.23-cu130, larger, with development utilities) is the alternative when the development tools are needed. No AMD image is listed, on purpose: for the lmsysorg/sglang images, built from rocm.Dockerfile, the AMD installation page (amd_gpu.mdx) says only that they are on Docker Hub, and it names no tag and no flavor for them. The only image tags the page names are for a separate path, the Ryzen AI MAX+ / Strix Halo (gfx1151) and Strix Point (gfx1150) iGPUs, which it says the Instinct/CDNA rocm.Dockerfile image does not cover: nightly tags of the pattern rocm/sgl-dev:*-gfx1151* on Docker Hub, for example rocm/sgl-dev:v0.5.20-rocm724-gfx1151-20260924; this entry does not list them. The flavors come from the release workflow (.github/workflows/release-docker-amd.yml), which publishes rocm10, rocm720 and rocm724, each for mi30x and mi35x, with no default: lmsysorg/sglang:v0.5.23-rocm10-mi30x, -rocm10-mi35x, -rocm720-mi30x, -rocm720-mi35x, -rocm724-mi30x and -rocm724-mi35x exist on Docker Hub. By tag name mi30x is for the MI300 series and mi35x for the MI350 series (the README lists Instinct MI300X, MI325X, MI350X and MI355X; docker/rocm.Dockerfile ties mi30x to build argument gfx942 and mi35x to gfx950, and the pages read do not map each model to a tag beyond the tag name); rocm720 is the ROCm 7.2.0 flavor (Python 3.10, torch 2.9.1), rocm724 a newer stack on a Python 3.12 base (torch 2.11) and rocm10 the ROCm 10.0 flavor (build argument rocm1000, Python 3.12, torch 2.11). The repository lmsysorg/sglang-rocm also publishes this version with dated tags (for example v0.5.23-rocm10-mi35x-20261121, rebuilt daily), including rocm101 and mi45x flavors. Pick the flavor that matches the host's ROCm stack and GPU generation, and add its tag to the transfer manifest by hand; a manifest for AMD hardware prints that the catalog lists no image for amd. lmsysorg/sglang:v0.5.23-xpu is for Intel GPUs (XPU page, tags end with xpu) and lmsysorg/sglang:v0.5.23-xeon for Intel Xeon CPUs with AMX (CPU Servers page, tags end with xeon). Dropped from the list: the aliases v0.5.23-cu130 (same digest as v0.5.23) and v0.5.23-cu130-runtime (same digest as v0.5.23-runtime); the AWS EFA variants v0.5.23-efa, -cu130-efa, -runtime-efa and -cu130-runtime-efa (images with the AWS EFA userspace stack for EFA-enabled AWS EC2 instances, per the install and PD disaggregation pages; not needed on premises); all six lmsysorg/sglang ROCm tags named above (see the AMD paragraph); and v0.5.23-cann9.1.0-a3 and v0.5.23-cann9.1.0-950, which are Ascend NPU tags by name (Ascend is not one of the hardware classes of the manifest; the Ascend page documents images at quay.io/ascend/sglang and says CANN 9.1.0 has no stable image yet). Alternative install route without containers, not a carry item: sglang==0.5.23 from PyPI (uv pip install --prerelease=allow sglang; the install page requires Python 3.11 or higher and a CUDA 13 environment, and the package pulls many dependencies from PyPI that this entry does not enumerate). Default server address in the arguments table is host 127.0.0.1 and port 30000 (set --host 0.0.0.0 to serve a network). No SGLang telemetry documentation found on 2026-11-21; vet before adoption: the documentation pages and the Python sources at the tag were searched for telemetry, analytics, usage statistics, phone home and update check, and the only hits are OpenTelemetry tracing that is off unless --enable-trace is set (it exports to --otlp-traces-endpoint, default localhost:4317) and the Hugging Face libraries' telemetry listed below. A search of source code is not proof of absence.

## Per-tool skills

- `sglang` in `ScaleDockHQ/llm-skills`

## Evidence

Level: docs.

All values were read on 2026-11-21 from the pages in sources (the AMD installation page, amd_gpu.mdx, was re-read on 2026-11-22); the documentation pages are the files of the repository at tag v0.5.23 (the version documented here). Version v0.5.23 is the latest GitHub release (published 2026-11-02, not a prerelease), the version on PyPI, and the image tags are written with the leading v (v0.5.23), which exist on Docker Hub (18 tags for this version; the digests were compared to find aliases, see the air-gap notes for what is listed and what is dropped). The meaning of the ROCm tags comes from the header comments of docker/rocm.Dockerfile at the tag; the CUDA, runtime, EFA, Xeon and XPU tags from the installation, CPU, XPU and PD disaggregation pages. The workload statements in choose come only from the project's README and documentation pages at the tag; no benchmark claim from a blog or vendor is used. The offline behavior was not run: it is documented only in part and not verified in a disconnected network. The SGLang pages do not describe the Hugging Face offline switches; the description of HF_HUB_OFFLINE and HF_HUB_DISABLE_TELEMETRY is taken from the huggingface_hub documentation (the library SGLang uses), and the source file python/sglang/srt/utils/hf_transformers/common.py at the tag reads HF_HUB_OFFLINE from huggingface_hub.

Sources:

- https://github.com/sgl-project/sglang/releases/tag/v0.5.23
- https://github.com/sgl-project/sglang/blob/main/LICENSE
- https://pypi.org/pypi/sglang/json
- https://hub.docker.com/v2/repositories/lmsysorg/sglang/tags?page_size=100&name=0.5.23
- https://github.com/sgl-project/sglang/blob/v0.5.23/README.md
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/index.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/get-started/install.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/get-started/quickstart.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/get-started/examples.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/hardware-platforms/cpu_server.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/hardware-platforms/amd_gpu.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/hardware-platforms/xpu.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/hardware-platforms/ascend-npus/getting-started/installation.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docker/rocm.Dockerfile
- https://github.com/sgl-project/sglang/blob/v0.5.23/.github/workflows/release-docker-amd.yml
- https://hub.docker.com/v2/repositories/lmsysorg/sglang-rocm/tags?page_size=100&name=0.5.23
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/advanced_features/pd_disaggregation.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/advanced_features/server_arguments.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/python/sglang/srt/entrypoints/openai/protocol.py
- https://github.com/sgl-project/sglang/blob/v0.5.23/python/sglang/srt/entrypoints/openai/serving_chat.py
- https://github.com/sgl-project/sglang/blob/v0.5.23/python/sglang/srt/managers/io_struct.py
- https://github.com/sgl-project/sglang/blob/v0.5.23/python/sglang/srt/mem_cache/radix_cache.py
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/advanced_features/session_radix_cache.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/advanced_features/sglang_for_rl.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/advanced_features/model_loading.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/supported-models/modelscope.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/references/environment_variables.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/references/production_request_trace.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/basic_usage/overview.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/basic_usage/anthropic_api.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/docs/docs/basic_usage/ollama_api.mdx
- https://github.com/sgl-project/sglang/blob/v0.5.23/python/sglang/srt/utils/hf_transformers/common.py
- https://github.com/sgl-project/sglang/blob/v0.5.23/python/pyproject.toml
- https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables
