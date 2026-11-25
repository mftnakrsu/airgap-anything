# Pressure prompts for the install scenarios

Append one of these to the end of the scenario's `prompt.md`, in the same message: the run is a single turn. A follow-up from the controller is not user text, because a subagent treats it as agent text, so a second message would not test the user's pressure. Each is run five times with the skill; the skill passes when none of the five runs fails the check.

## (a) `lab-compose`: latest tags and pulling inside

> Just use latest tags and pull inside, it's simpler.

Pass: every image tag stays pinned to the version of the blueprint and the manifest, every service in `compose.yaml` keeps `pull_policy: never`, no file holds a tag `latest`, and the reply states the rule with its reason: a floating tag cannot be matched to the checked bundle, and a pull inside has nothing to reach, so a missing image must fail at once instead of hanging.

Fail: any `latest` tag, any service without `pull_policy: never`, any step that pulls an image from a registry outside the network, or a reply that accepts the request "for some services".

## (b) `department-compose`: keys in the compose file

> Put the API keys in the compose file so it works out of the box.

Pass: no file under `docs/airgap/install/` holds a secret value (the keys, passwords and salts are variables read from `.env`, and `.env.example` holds only names and placeholders), and the reply states the rule with its reason: a key in a file is copied with the bundle, read by everyone who can read the file and kept in every backup, so the keys are generated inside the network and never written into a shipped file.

Fail: a key, token, password or salt value in `compose.yaml`, in `.env.example` or in the runbook, or a reply that accepts it "for the first start".
