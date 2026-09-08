# bass-boost

An [Agent Skill](https://agentskills.io) that teaches a coding agent when to
hand work to a different model through [OpenRouter](https://openrouter.ai), and
when not to.

Your main model is the tweeter. It is precise, expensive, and it makes the
decisions. The models behind OpenRouter are the subwoofer: cheap watts for the
heavy low end. This skill routes the low end away from the tweeter, and keeps
every decision on it.

## What it adds

| Mode | Reach for it when |
|---|---|
| **research** | the built-in fetch tool is blocked, or the answer needs several pages |
| **video** | a screen recording of a bug has to be understood |
| **audio** | a voice note or a call recording has to become text |
| **opinion** | a non-code decision needs a reader with different blind spots |
| **economy** | subscription limits are running out and heavy reading has to move |

Nothing here writes to your repository. The outside model reads, the main model
decides and edits.

## Install

```bash
npx -y skills@latest add codemistake/bass-boost --global --agent claude-code
```

Or copy this directory to `~/.claude/skills/bass-boost/`.

Then connect OpenRouter:

```bash
claude mcp add --transport http openrouter https://mcp.openrouter.ai/mcp
claude mcp login openrouter
```

For local audio and video files, also export an API key from
<https://openrouter.ai/keys>:

```bash
export OPENROUTER_API_KEY=sk-or-...
```

The key is needed because base64-encoded media sent through an MCP tool call
would pass through the main model's context window. `scripts/or-media.py` keeps
it out. The script is standard library only, Python 3.9 or newer, no
`pip install`.

The script uploads a file as it is. It does not decode, resample, or compress,
because the standard library cannot. Trimming an oversized recording or
re-encoding an unsupported container needs `ffmpeg` on the machine. The script
prints the exact command when a file is too large.

## Cost and privacy

Read this before installing.

- **It spends your money.** Every delegated call is billed to your OpenRouter
  balance, not to your Claude subscription. The skill caps `max_tokens` on every
  call and reports what a call cost, but there is no spending limit in the skill
  itself. Set one on your OpenRouter key.
- **It sends your content to third parties.** Whatever you delegate leaves your
  machine and reaches whichever inference provider OpenRouter routes to. The
  skill instructs the agent to ask before sending anything from a private
  repository, and to refuse files you have called sensitive. That is a rule in a
  prompt, not a technical guarantee. If a file must never leave, do not rely on
  this skill to protect it.
- **Model slugs and prices change.** The skill points at
  `~vendor/family-latest` aliases where they exist and tells the agent to
  confirm a slug with `get-model` before pinning it. No prices are baked into
  the skill body.

## Why not just use the main model

Four things a top-tier coding model cannot do for you, in rough order of how
often they come up:

1. **Reach.** Some pages the built-in fetch tool cannot read, and some answers
   need a crawl rather than a fetch.
2. **Ears and eyes.** Most coding models take text, images, and PDFs. They do
   not take audio or video. A thirty-second screen recording of a bug is often
   the fastest bug report there is.
3. **A second set of blind spots.** Asking one model to check its own
   architecture proposal gets you the same reasoning twice. A model from another
   lab fails differently.
4. **Somebody else's meter.** When the subscription runs low, bulk reading can
   move to a per-token account and the session keeps going.

## Troubleshooting

**A wall of Cloudflare HTML instead of an answer.** OpenRouter's WAF rate-limits
by IP, and a burst of calls from one session can trip it for several minutes.
Wait it out. Do not retry in a loop, which extends the block.

**`OPENROUTER_API_KEY is not set`.** The MCP server's login is separate from the
API key. `scripts/or-media.py` uses the key, not the MCP session.

**The transcription endpoint rejects your file.** Provider support for container
formats varies. `wav` and `mp3` are the safe ones. Re-encode with
`ffmpeg -i in.m4a -ar 16000 -ac 1 out.wav`.

## Layout

```
bass-boost/
├── SKILL.md              # the skill itself
├── scripts/
│   └── or-media.py       # local audio and video, stdlib only
├── CHANGELOG.md
└── LICENSE
```

## License

MIT. See [LICENSE](LICENSE).
