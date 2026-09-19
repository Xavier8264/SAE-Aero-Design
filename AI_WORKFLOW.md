# AI Workflow: getting the most out of Claude Code per token

For Jordan (and any teammate using Claude Code on this project). Written 2026-09-18.
Everything marked (docs) is from the official Claude Code docs, archived in `reference/text/cc_*.txt`.

## 1. The one idea behind every tip

Every message you send re-sends the WHOLE conversation so far, and so does every tool call Claude makes
inside a turn (docs). Caching makes re-reads cheaper, but they still count toward your usage.
A 1-line question at the end of a long session costs far more than the same question in a fresh one.

So the goal is simple: **keep conversations short and focused, and keep long-term memory in files, not in chat.**
That is why this project has:

| File | Role | Loaded automatically? |
|---|---|---|
| `CLAUDE.md` | Short rules for Claude (session start, checkpoints, compaction) | Yes, every session |
| `PROJECT_MEMORY.md` | Append-only project log; "CURRENT STATE SUMMARY" entries | No; Claude reads the header + latest summary |
| `reference/INDEX.md` + `reference/text/` | Every source, converted to searchable text | No; Claude greps it |
| `.claude/settings.json` | Project settings (auto-compact at 200K) | Yes |

## 2. The session loop

1. **Start** a fresh conversation (VS Code: new conversation / new tab, or `/clear`).
   State ONE task in one specific sentence, e.g. "Build the takeoff model for the sizing study."
   Claude reads the log summary on its own (CLAUDE.md tells it to).
2. **Pick the model and effort before the first message.** Changing either mid-session forces a full,
   uncached re-read of the conversation (docs).
3. **Work.**
4. **Checkpoint**: type `checkpoint`. Claude appends what was done, decided, and still open to the log.
5. **`/clear`**. It costs nothing (docs), and nothing is lost because it is all in the log.
   Next task -> back to step 1.

## 3. Which reset to use

| Situation | Do this | Why |
|---|---|---|
| Task finished, moving to a different task | `checkpoint`, then `/clear` | Free; the log carries the memory |
| Went down a wrong path | Rewind (VS Code: hover a message -> rewind button; CLI: `/rewind` or Esc Esc) | Truncates to an already-cached point: cheapest reset (docs) |
| Mid-task, conversation getting long, need continuity | `/compact keep the current task, numbers, file paths` | Summary request costs something and loses detail, but keeps you going (docs) |
| Quick side question ("what does FAQ 395 say?") | `/btw <question>` | Answer never enters the history (docs). VS Code shows only a subset of commands; type `/` to check it is there |
| Stepping away more than 1 hour | `checkpoint` first; start a fresh session when you return | The cache expires after 1 hour on a subscription; the first message back re-reads everything at full cost (docs) |
| Want an old conversation back | VS Code: Session history button; CLI: `/resume` | Name important sessions with `/rename` before clearing (docs) |
| Check usage | `/usage` (VS Code opens the Account & usage dialog) | Plan limits, plus flags for whatever drives 10%+ of usage (docs) |
| See what fills the context | Context indicator in the VS Code prompt box; `/context` where available | (docs) |

## 4. Auto-compact: what we set and why

- Auto-compact was already ON. But on Opus 5 (1M-token window) it only fires at about 967K tokens (docs),
  so a session could grow huge, with every turn re-reading all of it.
- Set for this project: `autoCompactWindow = 200000` in `.claude/settings.json` (range 100K-1M, docs).
  It takes effect in the next session.
- Treat it as a **backstop, not the plan**. Auto-compaction fires wherever it lands, often mid-task,
  and the summary is lossy. Checkpoint + `/clear` at task boundaries should mean it rarely fires.
- CLAUDE.md contains `# Compact instructions` telling the summarizer what to keep (docs feature).
- To change it: edit `.claude/settings.json`, or `/autocompact 300k` (that writes to your GLOBAL settings).

## 5. Model and effort

- Global default is now **Opus, effort high** (was xhigh). Thinking tokens are billed as output tokens,
  and the default budget can be tens of thousands per request (docs).
- Choose at the START of a session:
  - Hard design reasoning (trade studies, stability, structures decisions): Opus, high or xhigh.
  - Routine execution (running scripts, reformatting, small edits, report layout): Sonnet, or a lower effort.
    Docs: "Sonnet handles most coding tasks well and costs less than Opus."
- Never switch model or effort in the middle of a big conversation. `/clear` first, then switch.

## 6. Other habits that save tokens

1. **Be specific.** "Size the horizontal tail for 0.5 volume coefficient" beats "work on the tail"; vague
   prompts trigger broad file scanning (docs).
2. **Give Claude a way to check itself**: expected numbers, test cases, a rule to satisfy (docs).
3. **Plan mode for big multi-step work** (VS Code mode indicator, CLI Shift+Tab). A wrong direction
   caught at the plan stage is far cheaper than rework (docs).
4. **Stop early.** If Claude heads the wrong way, press Esc and redirect, rather than letting it finish.
5. **Turn off connectors this project doesn't use.** Each connected MCP server adds its tool names and
   instructions to every session (docs). This machine has Canva, Slack, Google Drive, Indeed, and
   Claude Docs connected. Indeed and Canva are unlikely to help an aircraft design. Manage them with `/mcp`.
6. **Don't paste screenshots unless needed.** Images are expensive, and piling them up invalidates the cache (docs).
7. **Editing CLAUDE.md mid-session does nothing** until the next `/clear`, `/compact`, or restart (docs).
8. **Right model for the job (project agents in `.claude/agents/`).** Agents start from zero, so they never
   carry a long chat's history, and each one can run a cheaper or stronger model:
   - `sae-researcher` (Sonnet): web searches, finding sources, price and spec lookups.
   - `sae-worker` (Sonnet): running scripts, archiving docs, reformatting, small edits.
   - `sae-analyst` (Opus, extra-high effort): trade studies, analysis models, reviewing results.
   - Fable 5: hardest problems only; Claude asks you first every time.
   You can name one directly: "use sae-researcher to find ...". Agent teams use about 7x the tokens (docs); avoid them.
9. **Avoid recurring loops on big sessions.** Scheduled tasks re-send the full context every time they fire (docs).

## 7. How Claude keeps its side (from CLAUDE.md)

- Reads the log header + latest summary, not the whole log. Greps the document library, never whole PDFs.
- Scripts print short summaries; full output goes to files.
- Renders images only when text extraction is flagged unreliable.
- Checkpoints to the append-only log, so `/clear` never loses anything important.

## 8. One-screen cheat sheet

```
NEW TASK        -> fresh session, one specific sentence, model/effort chosen first
DONE            -> "checkpoint"  then  /clear
WRONG TURN      -> rewind (hover message -> rewind)      [cheapest]
LONG + MID-TASK -> /compact keep <what matters>
SIDE QUESTION   -> /btw <question>
BREAK > 1 HOUR  -> "checkpoint" before leaving, fresh session after
USAGE CHECK     -> /usage
```
