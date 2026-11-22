# Agent instruction block

Add the block below to `AGENTS.md` in the project root. Create the file if it does not exist. If the block is already there, replace everything from the start marker to the end marker. Replace `BLUEPRINT_PATH` with the value of `blueprint_path`.

If the project has a `CLAUDE.md` that does not import `AGENTS.md`, ask the user before adding the line `@AGENTS.md` to it.

```markdown
<!-- airgap-architect:start -->
## Air-gapped blueprint

This project follows the blueprint at `BLUEPRINT_PATH`. Its machine-readable state is `docs/airgap/blueprint.json`. The artifacts to carry into the network are listed in `docs/airgap/transfer-manifest.md`.

- The target network has no internet access. Do not run a command that downloads anything; use the internal registry and mirrors.
- Use exactly the component versions pinned in the blueprint.
- Do not add a component, image, package or model that the blueprint does not list. Propose it as a blueprint change instead; the design is updated outside the network and carried in again.
- Decisions listed in the blueprint's verification section rest on estimates. Measure before relying on them.
<!-- airgap-architect:end -->
```
