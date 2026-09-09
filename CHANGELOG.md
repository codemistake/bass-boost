# Changelog

All notable changes to this skill are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-09-09

### Added

- `scripts/save-key.py` and `references/setup.md`, so the skill owns the
  question of where a credential lives instead of saying "export it" and
  leaving the user to guess. The Agent Skills specification has no field for
  secrets, but Claude Code settings files take an `env` block, and the per-user
  file is the right home for one.
- The script reads a key from a file or stdin, never from the command line,
  because a command line lands in shell history and in the transcript of
  whichever agent ran it. It merges into existing settings, backs the old file
  up, refuses a file it cannot parse, and never prints the value.
- A refusal to write into a project's `.claude/settings.json`, which exists to
  be committed and is the usual way a key reaches a git history.

## [1.2.0] - 2026-09-09

### Changed

- The image mode is one model in three price tiers, `openai/gpt-image-2.5` on
  fal.ai, replacing the two-route split across two providers. The z-image draft
  route and the OpenRouter image route are gone; `FAL_AI_TOKEN` is now the only
  key images need. GPT Image 2.5 is not sold through OpenRouter at all, and fal
  is the only host that exposes the quality parameter, without which a route
  called "quality" silently returns the cheapest tier.
- Default quality is `low`. It measured good enough for icons and UI art at
  $0.006 per 1024x1024 image, against $0.211 for the same prompt at high.

### Added

- A hard spending stop. A call priced above `--max-cost` (default $0.01) is not
  sent: the script prints the price, names the tiers that do fit, and exits with
  status 2. Overriding it takes `--yes` on the command line, so an agent cannot
  reason its way past the limit the way it can past a sentence in a prompt.
- `--model sunburst` for the precision-tuned variant at the same price, and
  `--background transparent` for icons, which returns a real alpha channel.

### Removed

- `google/gemini-3.1-flash-image`. It measured about ten times the price of
  GPT Image 2.5 at a comparable tier with no evidence of better output.

## [1.1.0] - 2026-09-09

### Added

- `image` mode and `scripts/gen-image.py`. Two routes: `draft` on fal.ai
  z-image/turbo, about a second and a fraction of a cent, and `quality` on
  OpenRouter with Nano Banana 2 or GPT Image 2. The script refuses to overwrite
  an existing file and verifies the bytes are PNG or JPEG before writing.

- `scripts/fetch-url.py`, a Firecrawl fallback for reading a named page the
  host's own fetch tool cannot get: Cloudflare blocks, IP rate-limits, and
  JavaScript-rendered content. Free tier covers 1000 pages a month, so an
  occasional fallback costs nothing. Optional; the skill states a page is
  unreachable rather than guessing when the key is absent.

### Fixed

- The quality image route posted to `/chat/completions` with a `modalities`
  field. Dedicated image models reject that endpoint outright, and models whose
  only output is an image reject the `["image","text"]` pair. Both now go
  through `/api/v1/images`, which returns `data[0].b64_json`. The three-place
  response search this required is deleted.
- The quality default is now `openai/gpt-image-2`. It renders text inside an
  image correctly and measured about ten times cheaper per image than
  `google/gemini-3.1-flash-image`, which was the previous default.

### Changed

- Reframed from "delegate heavy work" to "capabilities the coding agent lacks".
  Hearing, watching, drawing, reach, and an outside view are things it cannot do
  at all; the economy mode is the only one that is purely about cost.

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
