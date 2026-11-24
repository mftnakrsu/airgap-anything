# Serving requirements

Goal: for each chosen tool and model, state in `docs/airgap/agents.md` the API the tool speaks, the parsers the engine needs, the context window, the served model name and, behind a gateway, the LiteLLM route. Values were read on 2026-11-24 for vLLM v0.34.0, SGLang v0.5.23 and LiteLLM v1.110.2. Where a family has no documented parser the table says "not documented": say so to the user and never guess a parser.

## Contents

- The API per tool
- vLLM parsers per model family
- SGLang parsers per model family
- Served model name and context window
- LiteLLM in front of the engine
- Who the agent users are

## The API per tool

| Tool | API | Endpoint the server must offer | Catalog |
|---|---|---|---|
| Qwen Code | Chat Completions (Responses optional, `"wireApi": "responses"`) | `/v1/chat/completions` | `catalog/qwen-code.md` |
| opencode | Chat Completions | `/chat/completions` under the base URL | `catalog/opencode.md` |
| Codex CLI | Responses only | `/v1/responses`, streamed, with `response.completed` | `catalog/codex-cli.md` |
| Claude Code (private Claude route only) | Anthropic Messages | `/v1/messages`, optional `/v1/messages/count_tokens` | `catalog/claude-code.md` |

Every tool sends tool definitions with its requests, so the engine must parse tool calls. A working Chat Completions endpoint "doesn't establish Responses compatibility" (Codex CLI's gateway page): run the `/v1/responses` smoke test (`references/verification.md`) before choosing Codex CLI.

- vLLM serves `/v1/responses` (also `/{id}` and `/{id}/cancel`). It ignores `store` unless `VLLM_ENABLE_RESPONSES_API_STORE=1`, which keeps responses in memory and never frees them. For gpt-oss the recipe lists basic streaming, zero usage counts and function calling only with `tool_choice="auto"` (https://docs.vllm.ai/en/v0.34.0/serving/online_serving/, https://recipes.vllm.ai/openai/gpt-oss-120b).
- vLLM serves `/v1/messages` and `/v1/messages/count_tokens` since v0.11.1. Requests with server tools, such as WebSearch, get a 400 (https://docs.vllm.ai/en/v0.34.0/serving/integrations/claude_code/).
- SGLang serves `/v1/messages` and `/v1/messages/count_tokens` since v0.5.9; without `--tool-call-parser` tool calls come back as raw text (https://docs.sglang.io/docs/basic_usage/anthropic_api). SGLang `/v1/responses`: not documented in the research.
- LiteLLM serves `/v1/responses` since v1.63.8 (below).

## vLLM parsers per model family

Tool calling needs `--enable-auto-tool-choice` (the parser loads only with it) and `--tool-call-parser <name>`. Reasoning uses `--reasoning-parser <name>`. `--tool-parser-plugin` adds a custom parser. Sources: https://docs.vllm.ai/en/latest/features/tool_calling.html and https://docs.vllm.ai/en/latest/features/reasoning_outputs.html. All names below are registered in v0.34.0.

| Family | Tool parser | Reasoning parser | Source |
|---|---|---|---|
| Qwen3-Coder | `qwen3_xml` (docs) or `qwen3_coder` (recipe); same module | none | https://recipes.vllm.ai/Qwen/Qwen3-Coder-480B-A35B-Instruct |
| Qwen3 (2507) | `hermes` | `qwen3` | https://recipes.vllm.ai/Qwen/Qwen3-235B-A22B-Instruct-2507 |
| Qwen3.6, Qwen3.8 | `qwen3_coder` | `qwen3` | https://recipes.vllm.ai/Qwen/Qwen3.6-27B |
| GLM-4.5, GLM-4.6 | `glm45` | `glm45` | https://recipes.vllm.ai/zai-org/GLM-4.5 |
| GLM-4.7 | `glm47` | not documented | https://docs.vllm.ai/en/v0.34.0/features/tool_calling/ |
| GLM-5, GLM-5.3 | `glm47` | `glm47` (5.3 also `--tokenizer-mode glm5_next`) | https://recipes.vllm.ai/zai-org/GLM-5.3 |
| gpt-oss | `openai` | undocumented in the docs; registry key `openai_gptoss` | https://recipes.vllm.ai/openai/gpt-oss-120b |
| DeepSeek-V3.1 | `deepseek_v31` with a chat template | `deepseek_v3` (tools only in non-thinking mode) | https://docs.vllm.ai/en/v0.34.0/features/tool_calling/ |
| DeepSeek-V3.2 | `deepseek_v32` | `deepseek_v3`; `--tokenizer-mode deepseek_v32` | https://recipes.vllm.ai/deepseek-ai/DeepSeek-V3.2 |
| DeepSeek-V4, V4.1-Flash | `deepseek_v4`, `deepseek_v41` | same names, plus a tokenizer mode of the same name | https://recipes.vllm.ai/deepseek-ai/DeepSeek-V4.1-Flash |
| Kimi-K2, K2.7-Code, K3 | `kimi_k2`, `kimi_k3` | same names | https://recipes.vllm.ai/moonshotai/Kimi-K3 |
| MiniMax-M2, M2.7, M3.x | `minimax_m2`, `minimax_m3` | same names (the docs also list `minimax_m2_append_think`) | https://recipes.vllm.ai/MiniMaxAI/MiniMax-M2.7 |
| Mistral Small 4 (merges Devstral and Magistral) | `mistral` | `mistral` | https://recipes.vllm.ai/mistralai/Mistral-Small-4-119B-2603 |
| Devstral Small 2 | `mistral` | none | https://huggingface.co/mistralai/Devstral-Small-2-24B-Instruct-2512 |

The registry has no `devstral` and no `glm5` key. The tool-calling page has no MiniMax, GLM-5 or DeepSeek-V3.2 and later sections, so those rows come from recipes.

## SGLang parsers per model family

`--tool-call-parser` and `--reasoning-parser` both accept `auto`, which detects the parser from the model's chat template. There is no auto-tool-choice flag. Sources: https://docs.sglang.io/advanced_features/tool_parser.html, https://docs.sglang.io/advanced_features/separate_reasoning.html and https://docs.sglang.io/advanced_features/server_arguments.html.

| Family | Tool parser | Reasoning parser |
|---|---|---|
| Qwen3-Coder | `qwen3_coder` | not documented |
| Qwen3 (2507) | `qwen` ("Qwen series except Qwen3-Coder") | `qwen3`, `qwen3-thinking` |
| Qwen3.5 and later | not documented | not documented |
| GLM-4.5, GLM-4.6 | `glm` for GLM-4.6; `glm45` appears only in the v0.5.23 source | `glm45` |
| GLM-4.7, GLM-5 | not documented | not documented |
| GLM-5.3 | `glm47` | `glm45` |
| gpt-oss | `gpt-oss` | `gpt-oss` |
| DeepSeek-V3.1 | `deepseekv31` | not documented |
| DeepSeek-V3.2 | `deepseekv32` | `deepseek-v3` |
| DeepSeek-V4 | `deepseekv4` | `deepseek-v4` |
| DeepSeek-V4.1-Flash | `deepseekv41` (v0.5.23 source only) | not documented |
| Kimi-K2, K3 | `kimi_k2`, `kimi_k3` | `kimi_k2`, `kimi_k3` |
| MiniMax-M2, M2.7 | `minimax-m2` | `minimax`, `minimax-append-think` (M2.7) |
| MiniMax-M3 | `minimax-m3` | `minimax-m3` |
| Mistral | `mistral` | `mistral` |
| Devstral | not documented | not documented |

SGLang limits for images, `cache_control` and server tools on `/v1/messages`: not documented in the research.

## Served model name and context window

- Set `--served-model-name` to a name without `/`. Claude Code fails on model names that contain `/` (vLLM's Claude Code page). Use the same name for every tool, so one name works everywhere and the configuration files differ only in format.
- The context window set in the tool must be equal to or below the engine's `--max-model-len`. Where each tool takes it:

| Tool | Setting |
|---|---|
| Qwen Code | `generationConfig.contextWindowSize` in the `modelProviders` entry |
| Claude Code | `CLAUDE_CODE_MAX_CONTEXT_TOKENS` (unrecognized model IDs get an assumed 1M context) |
| Codex CLI | not documented in the research; see the catalog entry's sources |
| opencode | not documented in the research; see the catalog entry's sources |

## LiteLLM in front of the engine

When the blueprint has a gateway, `agents.md` states the route per tool. Sources: https://docs.litellm.ai/docs/anthropic_unified/native_passthrough, https://docs.litellm.ai/docs/anthropic_unified/messages_to_responses_mapping and https://docs.litellm.ai/docs/response_api.

- Chat Completions (Qwen Code, opencode) needs nothing special.
- `/v1/messages` is translated by default. `openai/<model>` goes through the Responses API; `custom_openai/` and other OpenAI-compatible providers go through `/v1/chat/completions`. `litellm_settings.use_chat_completions_url_for_anthropic_messages: true` forces Chat Completions, and requests with `stop_sequences` take that route anyway.
- Native passthrough (since v1.92.0): `model_info.supported_endpoints: ["/v1/chat/completions", "/v1/messages"]` sends the body to `{api_base}/v1/messages`, with a trailing `/v1` stripped. `cache_control` is reduced to `ephemeral` unless `model_info.cache_control_ttl: true`. The `hosted_vllm/` prefix is not mentioned on that page.
- `/v1/responses` (since v1.63.8): `custom_openai/`, `openai_like/` and most other OpenAI-compatible providers are bridged through `/v1/chat/completions`. `openai/` with a custom `api_base` calls the backend's `/responses` and fails if it is missing. `hosted_vllm/` sends `/v1/responses` natively. Force the bridge with `litellm_params.use_chat_completions_api: true` or `model: openai/chat_completions/<m>`.
- Bridged sessions need `general_settings.store_prompts_in_spend_logs: true` plus a cold-storage logger.
- The opt-in `model_info.supported_endpoints: ["/v1/responses"]` (since v1.101.0) forwards `previous_response_id`, which servers that do not store responses reject with a 400 (https://docs.litellm.ai/docs/response_api_native_passthrough).

## Who the agent users are

Agent users are the architect's `code_assistant` group. When the number of people differs from the blueprint, rerun the architect's sizing: this skill does not recompute it.
