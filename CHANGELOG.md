# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-08

First public release.

### Added

- Five delegation modes: `research`, `video`, `audio`, `opinion`, `economy`.
- `scripts/or-send.py`, standard library only. Sends any local file, text or
  media, to a model and returns only the answer. This is the only route that
  keeps a delegated file out of the calling agent's context, because the MCP
  server's `send-message` takes a string and therefore requires reading the
  file first.
- Cost and privacy section, stating that calls are billed to the user's own
  OpenRouter balance and that delegated content reaches a third-party provider.
- Common mistakes table covering the failure modes seen while building the
  skill: pinning retired model slugs, sending whole files to a frontier model,
  trusting a grounded answer without following its links.

### Notes

- Model slugs are not pinned to dated versions where a `~vendor/family-latest`
  alias exists, because dated slugs are retired without notice.
- No prices appear in `SKILL.md`. They change faster than releases do.

## [1.1.0] - 2026-09-09

### Added

- `image` mode and `scripts/gen-image.py`. Two routes: `draft` on fal.ai
  z-image/turbo, about a second and a fraction of a cent, and `quality` on
  OpenRouter with Nano Banana 2 or GPT Image 2. The script refuses to overwrite
  an existing file and verifies the bytes are PNG or JPEG before writing.

### Changed

- Reframed from "delegate heavy work" to "capabilities the coding agent lacks".
  Hearing, watching, drawing, reach, and an outside view are things it cannot do
  at all; the economy mode is the only one that is purely about cost.
