# Kong (`kong`)

Open-source API gateway built on Nginx that routes and secures HTTP traffic through plugins, including a set of AI plugins that proxy requests to LLM providers and self-hosted models.

| Field | Value |
|---|---|
| Layer | `llm-gateway` |
| Version | `3.9.5` |
| License | Apache-2.0 |
| Tiers | T1, T2, T3 |
| Requires | none |
| Evidence | docs |
| Last verified | 2026-11-21 |

## Choose when

- A conventional, plugin-based API gateway is wanted in front of model servers, with OpenAI-compatible routing through the AI Proxy plugin (route types such as llm/v1/chat and llm/v1/embeddings; the plugin translates OpenAI-format requests to the configured provider, introduced in Kong Gateway 3.6), authentication with the Key Auth plugin on Consumers and request-count limits with the Rate Limiting plugin, all in the open-source tree at tag 3.9.5.
- A configuration-as-files deployment without a database is wanted: DB-less mode keeps all entities in memory and loads them from one declarative YAML or JSON file, so there is no database to run; the AI Proxy, Key Auth and Rate Limiting plugin pages list DB-less as a supported topology.

## Avoid when

- Per-team token limits, cost budgets, load balancing across several LLM targets, SSO, RBAC or audit logs are required and no Kong Enterprise license is available: the plugins for the first three are marked as paid in the documentation (see caveats), the open-source 3.9.5 distribution has no cost budgets, and no SSO, RBAC or audit logs are in the open-source distribution (from source at tag 3.9.5, derived, see caveats).
- A newer Kong Gateway line than 3.9 is wanted from open source: open-source Kong is at minor 3.9, with security patches only (3.9.4 and 3.9.5), no newer open-source minor release exists (inferred from the missing releases, see caveats), and a Kong forum reply says Gateway 3.10 and above needs a license installed; the documentation describes Enterprise versions up to 3.16.

## Alternatives

`litellm`.

## Caveats

- Paid license, from the plugin pages (the front matter field tier, defined in the documentation's front matter reference as the subscription tier requirement): the plugins AI Proxy Advanced (the page says it proxies to multiple providers and models at the same time and sets up load balancing between targets), AI Rate Limiting Advanced (token-based limits), AI Semantic Cache and AI Sanitizer carry tier ai_gateway_enterprise (the banner says only available as part of the Kong AI Gateway Enterprise offering); Rate Limiting Advanced, OpenID Connect, LDAP Authentication Advanced, SAML and JWT Signer carry tier enterprise. The plugins AI Proxy, AI Prompt Decorator, AI Prompt Guard, AI Prompt Template, AI Request Transformer and AI Response Transformer, Key Auth and Rate Limiting carry no tier and are in the open-source source tree at tag 3.9.5 (kong/plugins).
- Single sign-on (the OpenID Connect plugin and the other SSO plugins above are tier enterprise), role-based access control, audit logs and Consumer Groups: the documentation pages for RBAC and the license entity are written for Kong Gateway Enterprise (the RBAC page's example assumes a valid license in KONG_LICENSE_DATA; the License entity page covers Enterprise licenses), and the audit logs page does not state a tier. The kong.conf reference for 3.9 has the settings enforce_rbac, audit_log and admin_gui_auth, but the open-source 3.9.5 kong.conf.default has none of them, the open-source 3.9 Admin API specification has no RBAC, license, Consumer Group or audit endpoint, and the open-source database entities (kong/db/schema/entities) have no RBAC or Consumer Group entity. Treat all four as not part of the open-source distribution; that is derived from those files, not stated in one sentence, and was not verified by running Kong.
- The open-source line: Kong open source is at minor 3.9. 3.9.x still gets patches (3.9.4 on 2026-10-12 and 3.9.5 on 2026-11-19; the 3.9.4 and 3.9.5 entries of the changelog list only security fixes, which is not a statement that 3.9 is unmaintained). Inferred, not stated by Kong in a cited page: no newer open-source minor exists, because kong/meta.lua on the master branch of Kong/kong is 3.10.0 while the repository has no 3.10 or later tag or release and Docker Hub has no 3.10 image of the official kong image (Kong/kong discussion 14405, April 2025 to September 2025, has users reporting the missing 3.10 image and no official answer; none of the developer.konghq.com pages read say that open-source releases ended). A reply in a Kong forum thread (written as a Kong response; the page does not label the author as staff) says: For Gateway 3.10 and above, you will need to make sure you have a license installed if you do not already. A design that needs features of 3.10 or later (for example the AI Sanitizer plugin, introduced in 3.10) needs Kong Enterprise.
- Per-team keys with limits: Consumers (open-source entity) with Key Auth credentials and the Rate Limiting plugin (limits HTTP request counts per second, minute, hour, day, month or year, identified by Consumer, credential, IP address or other supported identifiers) are open source. Token-based limits are the AI Rate Limiting Advanced plugin (paid). Dollar budgets per team: the AI cost management budgets page is for Konnect (works on konnect, AI Gateway 2.3 and later), a SaaS control plane that is not reachable from an air-gapped network, so there is no documented budget feature for the open-source distribution.
- License validation does not need network access: the License entity page says each node checks its license at startup and that network connectivity is not required for license validation (self-managed Kong Gateway Enterprise; the license comes from KONG_LICENSE_DATA, /etc/kong/license.json, KONG_LICENSE_PATH or the /licenses Admin API endpoint, and in hybrid mode each data plane node must start with it). For renewals in an air-gapped network: the breaking changes page says that from Enterprise 3.15.0.0 an expired license makes the Admin API and all interfaces read-only (no configuration changes) until a valid license is uploaded, while proxy traffic continues with the existing configuration; /licenses stays available to upload a new license. It describes 3.15 and later, not 3.9. The open-source distribution has no license check documented. license_server is false.
- DB-less mode needs no database: all entities are held in memory (the LMDB cache, sized by lmdb_map_size, default 2048m, and the whole configuration must fit) and are loaded from a declarative file with declarative_config or declarative_config_string, or through the /config Admin API endpoint. Limits stated on the page: no coordination or propagation between nodes (load the file on every node), the Admin API is read-only for entities (writes return HTTP 405), decK cannot be used, Kong Manager cannot create, update or delete entities, and some plugins need a database; the Rate Limiting plugin's cluster policy is not supported in DB-less mode (use redis or local).
- Database mode needs PostgreSQL (kong.conf.default: postgres or off, PostgreSQL 9.5 and above; the docker-kong compose template runs kong migrations bootstrap before the first start): all nodes of one cluster connect to the same database and share configuration, with a load balancer in front. It is not in Requires because DB-less mode works; list postgresql for any design that uses the Admin API for changes, a cluster sharing one configuration, or the Rate Limiting cluster policy.
- Redis is needed only for the Rate Limiting plugin's redis policy (the three policies are local, in memory on the node and less accurate across nodes; cluster, in the Kong data store; redis, shared counters). The documentation names Redis; Valkey compatibility not confirmed. The plugins' Redis pages mention Amazon ElastiCache for Valkey 7.2 or later and Memorystore for Valkey only for cloud IAM authentication, which does not state compatibility of a self-hosted Valkey.
- State of telemetry: the only phone-home found is anonymous_reports, on by default (see telemetry). No telemetry, analytics, usage statistics or update-check feature other than that was found in kong.conf.default at tag 3.9.5, in the 3.9 kong.conf reference and in the pages read when searching them for telemetry, phone home, update check, usage statistics and analytics on 2026-11-21; the hits were data plane to control plane telemetry connections in hybrid mode and analytics flush settings of the kong.conf reference, which the pages do not describe as calls to Kong servers. A search is not proof of absence; vet before adoption.

## Carry in

### Images

| Image | Hardware | Digest |
|---|---|---|
| `kong:3.9.5` | any | not recorded |

### Packages

None.

### Runtime downloads to stage in advance

None.

### Telemetry and egress to switch off before the first start

1. Anonymous usage reports (the kong.conf description: anonymous usage data such as error stack traces) sent by the gateway to kong-hf.konghq.com on port 61833 (constants.lua and reports.lua at tag 3.9.5, which is source code, not a documentation page); on by default (anonymous_reports = on).
   Switch off: anonymous_reports = off in kong.conf, or KONG_ANONYMOUS_REPORTS=off.

### License server

None: no license check needs connectivity.

### Air-gap notes

No runtime download is documented in the pages and source files read: the plugins in the image are bundled, and the AI plugins call the LLM provider or model server you configure. Offline behavior is documented but not verified; there is no air-gap or offline page in the documentation (a search for air-gap, airgap, offline and disconnected found only the hybrid mode pages on data planes that lose their control plane, and an unrelated certificate remark). The one image row is the official Docker Hub image kong:3.9.5 (listed on the Docker Hub page as supported tag 3.9.5; amd64 and arm64); the installation page that the Docker Hub page points to is the Kong Gateway installation documentation. Not listed: the aliases 3.9, 3 and latest of the same tag, and the 3.9.5-ubuntu tag. The compose template of the docker-kong repository at tag 3.9.5 runs the image with the tag from KONG_DOCKER_TAG (default kong:latest) and, for database mode, postgres:9.5 (take PostgreSQL from the postgresql entry; Kong itself documents PostgreSQL 9.5 and above in kong.conf.default). Native package installs (deb, rpm, apk archives) exist in the docker-kong repository and on the project's installation page, but this entry does not enumerate them; the documentation names no artifact for installing without internet access other than the image. The image listens on 8000 (proxy), 8443 (proxy TLS), 8001 (Admin API) and 8444 (Admin API TLS) in the compose template. Settings: kong.conf or KONG_* environment variables. Database-less mode: KONG_DATABASE=off with KONG_DECLARATIVE_CONFIG pointing to the declarative file (the compose template mounts it at /opt/kong/kong.yaml); database mode: KONG_DATABASE=postgres and the pg_* settings, and the compose template runs kong migrations bootstrap before the first start and kong migrations up with kong migrations finish on upgrades. Kong Enterprise images (kong/kong-gateway) and the Kong AI Gateway 2.x entities, policies and budgets are not covered: the documentation lists the 2.x budgets as available on Konnect only, and its on-prem 2.x page states that self-hosted Kong Gateway 3.x does not have the 2.x entities and expresses them with AI plugins on Services and Routes.

## Per-tool skills

- `kong-ai-gateway` in `ScaleDockHQ/llm-skills`

## Evidence

Level: docs.

All values were read on 2026-11-21 from the pages in sources. The entry is for the open-source Kong Gateway in the repository Kong/kong (Apache-2.0): open-source Kong is at minor 3.9 (see the caveat on the open-source line); version 3.9.5 is the latest GitHub release (published 2026-11-19, not a prerelease), the latest tag on the official Docker Hub image kong (3.9.5, 3.9, 3 and latest are the same tag list), and its tag shape has no leading v. The project's documentation moved to the repository Kong/developer.konghq.com, which has no release tags and documents Kong Gateway Enterprise up to version 3.16 (the old documentation repository Kong/docs.konghq.com is marked archived on GitHub, last push 2026-10-15); its pages are cited at the commit read (a6c38e73, 2026-11-21). Facts about 3.9.5 itself come from the repository at tag 3.9.5 (kong.conf.default, the plugin directory, the database entities) and from the 3.9 versions of the kong.conf reference and of the open-source Admin API specification in the documentation repository. Where the licensing answers below say a feature is absent from the open-source distribution, that rests on those sources (the documentation marks paid plugins with a tier field, and the open-source 3.9 Admin API specification and the 3.9.5 source tree contain no such endpoint, setting or plugin); a page that says 'Enterprise only' in words exists only for the plugins marked with tier. The offline behavior is documented but not verified: the entry author did not run Kong, and the documentation has no air-gap page.

Sources:

- https://github.com/Kong/kong/releases/tag/3.9.5
- https://github.com/Kong/kong/blob/3.9.5/LICENSE
- https://github.com/Kong/kong/blob/3.9.5/README.md
- https://github.com/Kong/kong/blob/3.9.5/CHANGELOG.md
- https://github.com/Kong/kong/blob/66288d2723bd3825e6385a21be27e2ec2199def8/kong/meta.lua
- https://github.com/Kong/kong/discussions/14405
- https://discuss.konghq.com/t/kic-helm-charts-dont-upgrade-gateway-above-version-3-9/13895
- https://github.com/Kong/docs.konghq.com
- https://github.com/Kong/kong/blob/3.9.5/kong.conf.default
- https://github.com/Kong/kong/tree/3.9.5/kong/plugins
- https://github.com/Kong/kong/tree/3.9.5/kong/db/schema/entities
- https://github.com/Kong/kong/blob/3.9.5/kong/constants.lua
- https://github.com/Kong/kong/blob/3.9.5/kong/reports.lua
- https://github.com/Kong/docker-kong/blob/3.9.5/README.md
- https://github.com/Kong/docker-kong/blob/3.9.5/compose/README.md
- https://github.com/Kong/docker-kong/blob/3.9.5/compose/docker-compose.yml
- https://hub.docker.com/_/kong
- https://hub.docker.com/v2/repositories/library/kong/tags/3.9.5
- https://github.com/docker-library/docs/blob/master/kong/content.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/gateway/db-less-mode.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/gateway/traditional-mode.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/gateway/audit-logs.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/gateway/version-support-policy.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong-conf/gateway/3.9.json
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/api-specs/gateway/admin-oss/3.9/openapi.yaml
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/docs/front-matter-reference.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_gateway_entities/license.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_gateway_entities/rbac.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-proxy/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-proxy-advanced/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-rate-limiting-advanced/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-semantic-cache/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/key-auth/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/rate-limiting/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/rate-limiting-advanced/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/openid-connect/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ldap-auth-advanced/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_includes/plugins/rate-limiting/strategies.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_includes/plugins/redis/oss.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/ai-cost-management/budgets.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/ai-gateway/configure-on-prem.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-sanitizer/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/saml/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/jwt-signer/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-prompt-decorator/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-prompt-guard/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-prompt-template/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-request-transformer/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/_kong_plugins/ai-response-transformer/index.md
- https://github.com/Kong/developer.konghq.com/blob/a6c38e732cd9e2048b22eab35cc51394240c18e5/app/gateway/breaking-changes.md
