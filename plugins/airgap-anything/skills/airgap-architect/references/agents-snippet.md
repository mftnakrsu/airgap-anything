# Agent instruction block

Add the block below to `AGENTS.md` in the project root. Create the file if it does not exist. If the block is already there, replace everything from the start marker to the end marker. Replace `BLUEPRINT_PATH` with the value of `blueprint_path`.

When `inside.operator` in `blueprint.json` is `local_agent` or `people_then_agent`, also put the section from "Rules for an agent inside the network" below into the block, directly before the end marker. Lint reports W4 while it is missing. For `people`, leave it out.

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

## Rules for an agent inside the network

```markdown
<!-- airgap-architect:inside-agent -->
### Rules for an agent inside the network

The installation inside follows the bundle that `airgap-transfer` builds: its runbook, `AGENTS-INSIDE.md`, `verify.sh` and `load.sh`.

- Run one command per step, exactly as the runbook gives it.
- Check the exit code of every command. 0 means go on.
- Stop at the first non-zero exit code and report the command, its exit code and its output; when `verify.sh` stops, report the contents of `MISSING.txt`.
- Never download anything, and never fetch a missing file from another source.
- Never edit the generated scripts or the files they check.
- Never improvise a step the runbook does not name. Ask a person instead.
```
