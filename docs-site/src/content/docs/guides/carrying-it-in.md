---
title: Carrying it in
description: From the transfer manifest to a running system inside the air-gapped network.
---

## Before the transfer

Work through `docs/airgap/transfer-manifest.md` on the connected side:

1. **Pull every image** in the manifest and fill in the digest and size columns as you pull. The manifest lists only the images for your hardware class.
2. **Download the model files** named under model artifacts.
3. **Stage runtime downloads.** Each tool's [catalog page](/reference/catalog/) lists what it would try to fetch while running, such as model weights, tokenizers or price tables, and how to provide it offline.
4. **Note the settings to switch off.** Telemetry and other outbound calls are listed with the setting that disables each one. Apply them before first start, not after.
5. **Write checksums** and check signatures where the project publishes them.

Then carry the artifacts, the manifest, the blueprint, `blueprint.json` and `AGENTS.md` across, by whatever channel the interview recorded.

## Inside

An agent inside the network follows `AGENTS.md` and the blueprint without internet access. The skill itself can be carried in too; see [Install without internet](/start/install/#without-internet).

## When something changes

A new decision, model or GPU makes the manifest stale: lint reports it, and `manifest.py` writes a fresh one. Plan updates at the cadence the interview recorded.
