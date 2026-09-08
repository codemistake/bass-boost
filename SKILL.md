---
name: bass-boost
description: "Use when a task needs something the coding agent cannot do by itself and an outside model can: generate or replace a raster image, placeholder, icon, or texture; analyze a video or screen recording; transcribe audio or a voice note; research a page or topic the built-in web tools cannot reach; get an independent second opinion on a non-code decision; or move heavy reading onto a cheaper model when the user says their subscription limits are running low. Also use when the user asks which outside model to pick for a task, or what a call would cost."
license: MIT
compatibility: "Needs Python 3.9+, shell access, and an OpenRouter account reached via its MCP server or OPENROUTER_API_KEY. FAL_AI_TOKEN adds the cheap image route; ffmpeg trims oversized media. Economy mode assumes a token-metered host such as Claude Code."
metadata:
  version: "1.1.0"
  author: codemistake
  repository: https://github.com/codemistake/bass-boost
---

# Bass Boost

A coding agent is a tweeter. It is precise, expensive, and it makes the
decisions, but it cannot reach the low end on its own: it does not hear audio,
does not watch video, cannot draw, and pays its own premium rate to read
anything long. This skill wires up a subwoofer for it. Outside models supply the
cheap watts, and every decision stays on the tweeter.

**The main model decides and writes. Every time.** Nothing that comes back from
OpenRouter edits a file, runs a command, or gets believed without a check. A
returned claim is a lead to verify, not a result.

**Every call spends the user's own money.** Always set `max_tokens`. Prefer the
cheapest model that can do the job. Say what a step will cost before an
expensive one.

## Setup

Preferred, no key handling:

```bash
claude mcp add --transport http openrouter https://mcp.openrouter.ai/mcp
claude mcp login openrouter
```

That gives the tools `send-message`, `transcribe-audio`, `list-models`,
`get-model`, and `get-generation`.

**The MCP server alone cannot relieve context.** Its `send-message` takes a
string, so putting a local file in the request means reading that file first.
The saving is gone before the call is made, and no URL trick avoids it: the
`:online` plugin runs a web search, it does not fetch a path or a link you hand
it. Delegating a local file needs `OPENROUTER_API_KEY` and
`scripts/or-send.py`, which reads the file in a shell and returns only the
answer.

Ask the user to create a key at <https://openrouter.ai/keys> and export it.
The draft image route uses a separate one, `FAL_AI_TOKEN`, from
<https://fal.ai/dashboard/keys>. Never ask to see either key, and never write
one into a file.

## Modes

| Mode | Reach for it when | How |
|---|---|---|
| research | built-in fetch is blocked, or the answer needs several pages | `send-message`, a `:online` model |
| video | a screen recording or clip has to be understood | `scripts/or-send.py` |
| audio | speech has to become text | `transcribe-audio`, or `scripts/or-send.py` |
| opinion | a non-code decision needs a dissenting reader | `send-message`, a model from another lab |
| image | a raster image, icon, texture, or placeholder is needed | `scripts/gen-image.py` |
| economy | the user's subscription limits are running out | see below |

Model slugs move. Before pinning one in a new workflow, confirm it with
`get-model`, or find a current one with `list-models` (it sorts by price,
context, coding index, and modality). The `~vendor/family-latest` aliases, such
as `~google/gemini-flash-latest`, always resolve to the newest model in that
family and are the safer default.

### research

`send-message` with a `:online` model, `reasoning_effort: low`,
`max_tokens: 4000`. The `:online` suffix adds web search to any model that
supports it.

Ask for facts with source links, dates, and version numbers, and say no prose.
Then re-read the important links with the local fetch tool. A grounded model
still paraphrases, and the paraphrase is what gets a fact wrong.

`:online` searches. It will not open a URL named in the message, so this mode
answers questions, it does not read a page on request.

### video

```bash
python scripts/or-send.py FILE --ask "what to look for"
```

Name the target in the question: the moment of failure, the exact on-screen
text, the order the user clicked things. Files above about 20 MB are rejected,
and the script prints the `ffmpeg` command that shrinks one.

### audio

A file already on public HTTPS goes through `transcribe-audio` with an
`audio_url`. A local file goes through the script:

```bash
python scripts/or-send.py FILE --lang ru
```

`nvidia/parakeet-tdt-0.6b-v3` is a cheap multilingual default. Never pass
`audio_base64` to the MCP tool; the encoded audio would pass through the main
model's context.

The endpoint returns one flat string. There are no timestamps and no speaker
labels, so a recording with several speakers comes back as a single run of text.
Reading the task out of it is the main model's job.

### opinion

`send-message` with a frontier model from a **different lab** than the main
model, `max_tokens: 3000`. The value is a different training run with different
blind spots, not a higher benchmark score, so picking the cheapest capable
outsider beats picking the most expensive one.

Send a brief, not a repository: context in five to fifteen lines, the options,
and the question. Ask it to argue against the plan and to name what would have
to be true for the plan to fail.

An outside model is not independent evidence. Two models trained on overlapping
data repeat each other's mistakes, so agreement proves nothing. What comes back
is a list of things to check, and the checking still happens locally.

Use it for architecture, product, and wording calls. For code review, the host's
own review tooling sees the actual diff and does better.

### image

```bash
python scripts/gen-image.py "prompt" --out assets/icons/sword.png
python scripts/gen-image.py "prompt" --route quality --out assets/hero.png
```

Two routes, and the default is the cheap one on purpose.

`draft` runs fal.ai z-image/turbo, needs `FAL_AI_TOKEN`, and returns in about a
second for a small fraction of a cent. Placeholders, layout stand-ins, and
figuring out what the prompt should say all belong here. Iterate on the draft
route until the wording is right.

`quality` runs OpenRouter and needs `OPENROUTER_API_KEY`. The default is
`google/gemini-3.1-flash-image`, and `openai/gpt-image-2` is the alternative
when text inside the image has to render correctly. Ask the user which one, or
say which you picked and why. Use it once, at the end, on the prompt the draft
route settled.

Wire the result into the code and show it to the user. Never invent a filename
that something already references, and never overwrite an existing asset without
being asked: the script refuses to write over a file that exists.

An image is not a decision. Getting a logo, a brand asset, or anything a person
will read as authentic is the user's call, not a step to complete quietly.

### economy

Turn on when the user says they are low on limits, or asks for economy mode.
Confirm in one line, then hold it until they say stop or the session ends.

While it is on, take the cheapest step that answers the question, in this order:

1. **Narrow locally.** `grep`, `sed`, `wc`, `head`. This costs nothing, leaks
   nothing, and ends the job on anything with a searchable signature. A failed
   deploy has an `ERROR` line in the log. One regex beats any delegation.
2. **Delegate what narrowing cannot reach.** Send material out only when the
   question is about meaning rather than a string: what a long document argues,
   whether a report contradicts itself, what an unfamiliar module does. Send a
   local file with `scripts/or-send.py FILE --ask "..."`, which is the only
   route that keeps the file out of this context. Without the key, this step
   is unavailable; say so and go to step 3 instead of pretending to save.
3. **Read directly** whatever survives both steps. It should be small.

Also while it is on:

- Long first drafts, such as a README or a report, are drafted outside and
  edited by the main model.
- Subagents stay off. They bill the same subscription that is running out.
- The main model keeps edits, commands, short reads, decisions, and the final
  check.

What does not change in economy mode: verify before acting, ask before anything
destructive, and never let an outside model write to the repository.

This trades one bill for another, and it only helps where the host meters
tokens. On a host that meters turns or requests, delegating adds a round trip
and saves nothing. Say so rather than promising a saving you cannot measure.

## Cost and privacy

Whatever gets sent leaves the machine. Source code, logs, and recordings all
reach a third-party inference provider that the router picks. Before sending
anything from a private repository, say so and get agreement. For a file the
user has called sensitive, do not send it at all.

Spending is metered per call against the user's balance. After a large or
unfamiliar call, `get-generation` with the returned id reports what it actually
cost.

## Common mistakes

| Mistake | What to do instead |
|---|---|
| Delegating a task the main model would finish faster | Delegate for reach, context relief, or an outside view. Nothing else. |
| Delegating a file that one `grep` would narrow | Search locally first. A regex costs nothing and keeps the file on the machine. Delegation does neither. |
| Pasting a whole file into an opinion call | Send a brief. Frontier models are billed per token in both directions. |
| Treating a grounded answer as verified | Follow the links. Grounding narrows hallucination, it does not remove it. |
| Pinning a model slug found in a blog post | Confirm it with `get-model` first. Slugs are retired without notice. |
| Sending base64 media through a tool call | Use the script. The tool result would land in the main model's context. |
| Leaving `max_tokens` unset on a reasoning model | A stuck reasoning loop bills to the user until it stops. |
