# LLM gateway (`llm-gateway`)

**Default: `litellm`** whenever the organization needs per-team keys, budgets or audit, or serves more than one model; otherwise no gateway. An existing Kong changes that, as below. Skip any component whose catalog `Tiers` row does not include the `llm-gateway` floor.

| Case | Choose | Evidence | Why |
|---|---|---|---|
| `existing.api_gateway` is `kong`, and 2 or more departments or `org.audit_required` | The existing Kong at the edge, `litellm` behind it | estimate | Kong's AI Proxy, Key Auth and Rate Limiting plugin pages carry no paid tier, but open-source Kong has no documented token or dollar budgets, so per-team budgets come from LiteLLM; the 2-department threshold is the design's (https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-proxy/index.md, https://github.com/BerriAI/litellm-docs/blob/d6ae56ec9fa4b0c232b5cb88ccb25482bcdf3ee8/docs/proxy/team_budgets.md) |
| `existing.api_gateway` is `kong`, one department, no audit | The existing Kong alone | estimate | Key Auth and Rate Limiting identify a consumer and limit request counts with no paid tier; whether the site's Kong has these plugins (AI Proxy exists from Kong Gateway 3.6) is not known (https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/key-auth/index.md, https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/rate-limiting/index.md) |
| Audit required, or isolation other than `none`, or 2 or more departments, or more than one model | `litellm` | estimate | LiteLLM's team budget page describes teams, keys and budgets with no license marker, while its enterprise page lists them among licensed features: the documentation contradicts itself (https://github.com/BerriAI/litellm-docs/blob/d6ae56ec9fa4b0c232b5cb88ccb25482bcdf3ee8/docs/proxy/team_budgets.md, https://github.com/BerriAI/litellm-docs/blob/d6ae56ec9fa4b0c232b5cb88ccb25482bcdf3ee8/docs/enterprise.md) |
| Anything else | No gateway | estimate | The design's starting point |

"No gateway" is not available when the tier requires a gateway (`references/tiers.md`, Floors).

## Writing the decision

1. A gateway that already runs is reused, not deployed: name it under "Existing", for example "Kong, operated by the platform team". Put `kong` under "Components" only when a new Kong instance is deployed for this platform.
2. "No gateway" is a decision too: nothing under Components or Existing, and a rationale that says why none is needed.
3. Open-source Kong stays at minor 3.9 with security patches only (3.9.4 and 3.9.5, derived from the missing releases, not stated by Kong); features from 3.10 on need Kong Enterprise. Weigh a new Kong instance against that, against `litellm`, and against the Kong version the site already runs. Open-source Kong has no documented token or dollar budgets, SSO, RBAC or audit logs.
4. Read the `kong` and `litellm` entries before choosing either: their caveats say which features need a paid license, and "License server" says whether a license check needs connectivity. A paid feature the design relies on goes into the rationale.
5. LiteLLM's documentation contradicts itself on whether teams, keys, budgets and role-based access control need the enterprise license. A design that relies on them says so and lists "confirm with the vendor which team and key features run without a license" under verification. Do not state either answer as a fact.
6. A LiteLLM license key works offline only if it passes the local signature check; otherwise LiteLLM calls `license.litellm.ai` and the paid features switch off when that fails (from the source at tag v1.110.2, not documented). A design with paid features says that a key which passes the offline check must be obtained before installation.
7. `litellm` requires `postgresql`. When LiteLLM runs more than one worker or replica, add `valkey` to the `state` decision: without a shared Redis-protocol store, rate limits, budgets and cache hits are counted per worker. `valkey` is not in LiteLLM's Requires row, so nothing else reminds you.
8. Evidence: the weakest of the case's label and the chosen components' labels.

Components used in this file: `kong`, `litellm`.
