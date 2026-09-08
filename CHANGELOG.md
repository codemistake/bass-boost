# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-09-08

First public release.

### Added

- Five delegation modes: `research`, `video`, `audio`, `opinion`, `economy`.
- `scripts/or-media.py`, standard library only, for local audio and video.
  Keeps base64 payloads out of the main model's context window.
- Cost and privacy section, stating that calls are billed to the user's own
  OpenRouter balance and that delegated content reaches a third-party provider.
- Common mistakes table covering the failure modes seen while building the
  skill: pinning retired model slugs, sending whole files to a frontier model,
  trusting a grounded answer without following its links.

### Notes

- Model slugs are not pinned to dated versions where a `~vendor/family-latest`
  alias exists, because dated slugs are retired without notice.
- No prices appear in `SKILL.md`. They change faster than releases do.
