# Tiers and floors

Script, catalog and reference paths in this file are relative to the skill root, the folder that holds `SKILL.md`. Run a script by its full path (the skill root joined with `scripts/NAME.py`) from the project root, so that `docs/airgap/blueprint.json` resolves.

Run:

```bash
python3 scripts/tier.py --blueprint docs/airgap/blueprint.json
```

It writes `tier` into `blueprint.json`. Do not work a tier out by hand.

## What the output means

| Field | Meaning |
|---|---|
| `base` | `T1` single team, `T2` department, `T3` enterprise. It comes from `org.users_total` and `org.departments` only. |
| `floors` | One tier per layer. A floor is the lowest tier you may design that layer for. Most floors equal `base`; some answers raise single layers. |
| `requirements` | Obligations that follow from the answers. See the next table. |
| `reasons` | Why floors were raised. Quote them in the blueprint's tier section. |

| Requirement | When it is true, you must |
|---|---|
| `gateway_non_empty` | Choose a gateway: the `llm-gateway` decision needs a component, an existing gateway or a custom entry. |
| `isolation_design_section` | Add the "Isolation design" subsection to the blueprint, with its marker. |
| `two_engine_replicas` | Nothing by hand: `size.py` already plans at least two replicas per model. |
| `kubernetes_risk_note` | List `org.kubernetes_experience` as a risk in the verification section: the design needs Kubernetes and the team does not run it today. |

## Using a floor

1. For a supporting layer, take the floor's column in `references/layers/supporting-defaults.md`.
2. In a decision table, skip a row when the component's `tiers` list does not include the floor.
3. Designing a layer above its floor needs no permission. Going below it needs an override on that decision: `"override": { "reason": "..." }`. Without it, lint reports error E3. With it, lint lists the override as note N1, and the blueprint's tier section must list it too.

## Tier and hardware are separate

The tier measures how complex the organization is. It says nothing about GPU count. A 40-person team that serves a very large model needs many GPUs at T1; a 2,000-person company that serves a small model needs few at T3. GPU count comes from `size.py`.

## Exit code 2

The script lists the question IDs that are missing or invalid. Go back to the interview for those, then run it again.
