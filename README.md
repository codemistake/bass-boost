# bass-boost

An [Agent Skill](https://agentskills.io) that gives a coding agent the senses it
does not have, and teaches it when to use them.

Your coding agent is a tweeter. It is precise, expensive, and it makes the
decisions, but it cannot reach the low end on its own: it does not hear audio,
does not watch video, cannot draw, and pays its own premium rate to read
anything long. This skill wires up a subwoofer. Outside models supply the cheap
watts, and every decision stays on the tweeter.

## What it adds

| Mode | Reach for it when |
|---|---|
| **research** | the built-in fetch tool is blocked, or the answer needs several pages |
| **video** | a screen recording of a bug has to be understood |
| **audio** | a voice note or a call recording has to become text |
| **opinion** | a non-code decision needs a reader with different blind spots |
| **image** | a placeholder, icon, texture, or shipped asset has to be drawn |
| **economy** | subscription limits are running out and heavy reading has to move |

Nothing here writes to your repository. The outside model reads, the main model
decides and edits.

Built and tested on Claude Code, and not affiliated with or endorsed by
Anthropic. The four scripts are plain Python with no dependencies and no
knowledge of the host, so the skill works anywhere the Agent Skills format is
read. Two things are Claude Code shaped and documented with alternatives: where
keys are stored, and the command that connects an MCP server.

## Install

```bash
npx -y skills@latest add codemistake/bass-boost --global --agent claude-code
```

Or copy this directory to `~/.claude/skills/bass-boost/`, or to
`~/.agents/skills/bass-boost/` on a runtime that reads that path.

Then connect OpenRouter:

```bash
claude mcp add --transport http openrouter https://mcp.openrouter.ai/mcp
claude mcp login openrouter
```

To delegate anything held in a local file, also add an API key from
<https://openrouter.ai/keys>:

You do not have to run anything. Save the key to a file, tell your agent the
path, and it stores the key for you with the bundled script:

```bash
python scripts/save-key.py OPENROUTER_API_KEY --from-file ~/key.txt
```

`save-key.py` writes into the `env` block of `~/.claude/settings.json`, merging
rather than replacing and backing the old file up first. It reads the value from
a file or from stdin, never from the command line, because a command line lands
in shell history and in the transcript of whichever agent ran it. It never
prints the value back, and it will not write to a project's
`.claude/settings.json`, which is meant to be committed. Delete the file you
pasted the key from afterwards. The full procedure is in
[references/setup.md](references/setup.md).

The key is not optional if you want the economy mode to do anything. The MCP
server's `send-message` takes a string, so handing it a local file means reading
that file into the agent's context first, which is the cost you were trying to
avoid. No URL trick gets around it either: the `:online` suffix runs a web
search, it does not fetch a link you hand it.

`scripts/or-send.py` is the way out. It reads the file in a shell, sends it, and
prints only the answer. Standard library only, Python 3.9 or newer, no
`pip install`. It routes by extension:

```bash
python scripts/or-send.py deploy.log  --ask "what failed and why"
python scripts/or-send.py bug.mp4     --ask "where does the UI break"
python scripts/or-send.py voicenote.m4a --lang ru
```

The script sends a file as it is. It does not decode, resample, or compress,
because the standard library cannot. Trimming an oversized recording or
re-encoding an unsupported container needs `ffmpeg` on the machine. The script
prints the exact command when a file is too large.

Images need a fal.ai key from <https://fal.ai/dashboard/keys>:

```bash
python scripts/save-key.py FAL_AI_TOKEN --from-file ~/key.txt
python scripts/gen-image.py "a pixel-art treasure chest icon" --out chest.png
```

One model, GPT Image 2.5, in three price tiers. Quality is the entire cost
story: at 1024x1024 the same prompt costs $0.006 at low and $0.211 at high.
The default is low, because low is good enough for placeholders, icons, and
most shipped UI art.

**A call over one cent refuses to run.** It prints the price, exits with status
2, and sends nothing. That is a hard stop in the script, not a rule in a prompt,
so an agent cannot talk itself past it:

```
$ python scripts/gen-image.py "hero art" --quality high --out hero.png
This call costs $0.211 at 1024x1024 quality=high, over the $0.010 limit. It was NOT sent.
Ask the person paying, then re-run with --yes.
Within the limit at this size: low $0.006.
```

Raise the ceiling with `--max-cost` or confirm one call with `--yes`. Only the
six resolutions fal publishes prices for are offered, because a call that cannot
be priced cannot be guarded.

For pages your agent's own fetch tool cannot read, a Firecrawl key is the third
optional extra. The free plan is 1000 pages a month with no card, and one page
costs one credit, so an occasional fallback never leaves it:

```bash
python scripts/save-key.py FIRECRAWL_API_KEY --from-file ~/key.txt
python scripts/fetch-url.py https://example.com/docs --out docs.md
```

Firecrawl requests from its own infrastructure and renders JavaScript, so a
Cloudflare block or an IP rate-limit on your machine does not apply to it. Try
the built-in tool first; this is the fallback, not the default.

## What a call actually costs

Measured on this skill's own routes, not quoted from a price list. Your figures
will differ with size and length, but the ratios hold.

| Route | Model | Input | Cost |
|---|---|---|---|
| image, low | gpt-image-2.5 | prompt, 1024x1024 | $0.006 |
| image, medium | gpt-image-2.5 | prompt, 1024x1024 | $0.053 |
| image, high | gpt-image-2.5 | prompt, 1024x1024 | $0.211 |
| audio | parakeet-tdt-0.6b-v3 | 34 s of speech | $0.0008 |
| video | gemini flash | 5 s clip, 2.8 MB | $0.0009 |
| text | gemini flash | 92 KB log, 48,607 tokens | $0.038 |

Two things to read off that table. The top image tier costs thirty-five times
the bottom one, which is why the script stops before spending rather than
trusting a prompt. And a 92 KB log costs four cents to delegate, which is why
the skill tells the agent to narrow with `grep` before sending anything.

## What has been verified

Every mode below was run against the live API while the skill was written, not
reasoned about. Two of them changed the skill when they failed.

| Mode | Evidence |
|---|---|
| research | facts returned with source URLs; `:online` confirmed to search, not fetch |
| image | all three tiers priced and the cheap one generated; the cost stop refused a $0.211 call |
| audio | a 34 s speech sample transcribed verbatim for $0.0008 |
| video | a 5 s clip described correctly for $0.0009 |
| opinion | a frontier model from another lab returned three usable objections, two of which are now rules in this skill |
| economy | two subagent runs; the first one refused to delegate and was right, which rewrote the rule |
| fetch-url | retrieved a page that the host's own fetch tool answered with HTTP 403 |

The economy run is worth repeating. Given a 1400-line log and told to save
money, the agent ran one `grep` instead of delegating, and explained that a
regex costs nothing while the delegation would have cost four cents and shipped
the log to a third party. It was right, so the rule now says to narrow locally
first.

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

Five things a top-tier coding model cannot do for you, in rough order of how
often they come up:

1. **Reach.** Some pages the built-in fetch tool cannot read, and some answers
   need a crawl rather than a fetch.
2. **Ears and eyes.** Most coding models take text, images, and PDFs. They do
   not take audio or video. A thirty-second screen recording of a bug is often
   the fastest bug report there is.
3. **Hands for drawing.** A coding model writes the markup for a card and then
   leaves a grey box where the picture goes. An icon costs about half a cent, so
   the placeholder can be the real thing from the first commit.
4. **A second set of blind spots.** Asking one model to check its own
   architecture proposal gets you the same reasoning twice. A model from another
   lab fails differently.
5. **Somebody else's meter.** When the subscription runs low, bulk reading can
   move to a per-token account and the session keeps going.

## Troubleshooting

**A wall of Cloudflare HTML instead of an answer.** OpenRouter's WAF rate-limits
by IP, and a burst of calls from one session can trip it for several minutes.
Wait it out. Do not retry in a loop, which extends the block.

**`OPENROUTER_API_KEY is not set`.** The MCP server's login is separate from the
API key. `scripts/or-send.py` uses the key, not the MCP session.

**A 404 from a provider that clearly exists.** OpenRouter's account privacy
settings gate which providers may serve your requests, and a model whose only
provider is disallowed fails as a 404 rather than as a permission error. Check
the provider list in your OpenRouter settings before assuming the slug is wrong.

**The model says it cannot open your link.** Expected. `:online` searches the
web; it does not fetch a URL from the message. Send the content instead.

**The transcription endpoint rejects your file.** Provider support for container
formats varies. `wav` and `mp3` are the safe ones. Re-encode with
`ffmpeg -i in.m4a -ar 16000 -ac 1 out.wav`.

## Layout

```
bass-boost/
├── SKILL.md              # the skill itself
├── references/
│   └── setup.md          # which key unlocks what, and where keys must not go
├── scripts/
│   ├── or-send.py        # any local file to a cheap model, stdlib only
│   ├── gen-image.py      # raster images, three price tiers, hard cost stop
│   ├── fetch-url.py      # one page as markdown, via Firecrawl
│   └── save-key.py       # store a key in ~/.claude/settings.json safely
├── CHANGELOG.md
└── LICENSE
```

## License

MIT. See [LICENSE](LICENSE).
