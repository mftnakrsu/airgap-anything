# Security policy

## Supported versions

The latest release (currently 0.4.x) and `main`.

## What counts as a security issue

airgap-anything ships Markdown, JSON and an icon; it runs no code of its own. A security issue is anything in the skills or the catalog that could lead an agent or a person to do something unsafe, for example:

- an instruction or command that could make an agent download or run something the user did not approve;
- a catalog entry that points to a wrong, compromised or tampered image, package or URL;
- a checksum or verification step that would let a damaged or altered file pass as good;
- a step that could expose a token, password or key.

## Reporting a vulnerability

Report it privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability** (https://github.com/mftnakrsu/airgap-anything/security/advisories/new). Please do not open a public issue for a security problem.

This is a volunteer project. Reports are handled on a best-effort basis; you will get an answer in the advisory, and a fix is published as a new release with credit to the reporter unless you ask otherwise.
