# SAE Aero Design 2027 Regular Class -- project instructions for Claude

Kept short on purpose: this file loads into every session. Details live in the files it points to.
Human-readable version of the workflow: AI_WORKFLOW.md (do not load it unless asked).

## Session start (cheap context loading)
1. Read PROJECT_MEMORY.md: the RULES header (first ~45 lines), then the LAST entry titled
   "CURRENT STATE SUMMARY" and every entry after it. Grep older entries only when needed.
2. Never read whole reference documents. Use reference/GUIDE.md (topic map; INDEX.md is the full list)
   -> grep reference/text/<ID>.txt -> read line ranges. Raw datasets live in reference/data/ (parse with scripts).

## While working
- PROJECT_MEMORY.md is append-only and timestamped from `date`; the latest entry wins. Write each entry
  to a scratch file first, then append it with `cat >>`. ASCII only.
- Archive any source we will cite again: `python tools/doc2text.py fetch URL --name ID`.
- Analysis scripts write full output to files and print a short summary (about 20 lines max).
- Render PDF pages or view images only when the text is flagged (math/garbled/img) and the exact form matters.
- Never paste large outputs, whole files, or solver/CFD logs into the conversation.
- In code, build non-ASCII characters with chr(0x...); backslash-u escapes typed into tool inputs get converted.
- One task per session. When a task is done, run the checkpoint below and tell Jordan it is safe to /clear.

## Model and agent selection (Jordan's standing guidance, 2026-09-18)
Match the model to the task. Do not default everything to one tier, and do not cap yourself below Opus xhigh.
- A task that doesn't need this chat's history -> delegate it to an agent with a self-contained prompt
  (agents start cold and do not see CLAUDE.md, so put the essentials in the prompt).
- `sae-researcher` (Sonnet): web searches, source finding, fact and price lookups.
- `sae-worker` (Sonnet): running scripts and sweeps, archiving docs, reformatting, small edits from a clear spec.
- `sae-analyst` (Opus, xhigh): hard reasoning such as trade studies, analysis models, reviewing results.
- Fable 5: only for the hardest problems, used sparingly, and ASK JORDAN FIRST every time.
- Agents never write PROJECT_MEMORY.md or run doc2text.py in parallel. The main session integrates and logs.

## Checkpoint (when Jordan says "checkpoint", before a long break, or when a task is done)
1. Append a timestamped entry to PROJECT_MEMORY.md: what was done, decisions, key numbers with units,
   file paths, open items, and what is UNVERIFIED.
2. At the end of a design phase, or ~400 log lines after the last one, also append a "CURRENT STATE SUMMARY".
3. Finish with one line: the task the next session should start with.

# Compact instructions
When compacting, preserve: the current task and its next step; decisions and key numbers with units;
paths of files created or modified; open questions and anything marked UNVERIFIED; any result not yet
written to PROJECT_MEMORY.md. Drop: tool output, file dumps, search results, and web page text
(they are saved under reference/ and can be grepped again).
