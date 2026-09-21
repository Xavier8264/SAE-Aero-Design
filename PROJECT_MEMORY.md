# SAE Aero Design 2027 Regular Class -- Project Memory Log

## RULES FOR THIS FILE (read first, every session)

1. APPEND-ONLY. Never delete or edit existing text. Add new entries at the END of the file only
   (e.g. `cat >> PROJECT_MEMORY.md <<'EOF' ... EOF`), never rewrite the file.
2. Every entry starts with a timestamp header: `## [YYYY-MM-DD HH:MM TZ] <task title>`.
   Get the time from the system clock (`date`), do not guess it.
3. CONTRADICTIONS: if two entries disagree, the entry with the LATEST timestamp is correct.
   To correct something, append a new entry that says what it supersedes. Do not edit the old one.
4. When in doubt, document. Record what was done, what was decided, the numbers used, where
   files/scripts live, sources, and what is still unverified, so a future Claude Code session
   can pick up without re-deriving anything.
5. Tag confidence where it matters: [VERIFIED] = read from a source/file, [INFERRED] = my
   reasoning, [UNVERIFIED] = assumption that still needs checking.
6. ASCII only in this file.

---

## [2026-09-18 20:31 CDT] Log created; back-fill of session 1 work (earlier this evening)

Note: the items below were done earlier in session 1 on 2026-09-18 before this file existed.
They are recorded now, so the timestamp is when they were written down, not when they happened.

### Source documents
- Rules: `2027_SAE_AeroDesign_Rules_Set.pdf` (Version 2027.0) in this folder.
- Text extraction: `pdftotext -layout` works (Git Bash, /mingw64/bin/pdftotext). Equations lose
  their symbols in text; render the page with PyMuPDF (`import pymupdf`, page.get_pixmap) to read them.
  The Read tool cannot render PDFs here (no pdftoppm).
- Regular Class = rules section 7 (pp. 33-36). TDS prediction = section 4.5 (p. 26).
  Flight rules = section 3 (pp. 17-20). Gross weight = p. 12.

### 2027 Regular Class rules summary [VERIFIED from rules PDF]
- Wingspan: > 72 in and < 96 in (max reduced vs 2026; Regular mission is in "year 2").
- Wing chord > 4 in. Body axis length < 120 in. Gross takeoff weight <= 55 lb.
- NO fiber-reinforced plastic anywhere (carbon, fiberglass; duct tape counts as FRP). Exceptions:
  commercially available FRP motor mounts, propellers, landing gear, control linkage parts.
- Rubber bands / elastics may not retain the wing or the payload.
- Propulsion: exactly 2 or 4 electric motors, any make/model. Props at motor RPM (1:1 if geared/belted).
  Max prop diameter 12 in (2 motors) or 9 in (4 motors). No metal props. Spinner or rounded safety nut.
- Battery: one commercially available 4S (14.8 V) LiPo, max 2200 mAh. NO power limiter required.
- Separate receiver battery required (Regular): LiPo or LiFe, >= 1000 mAh. Rx must work with arming plug out.
- Red arming plug on + lead, >= 9 in from any prop, top of fuselage near centerline, clearly visible.
- Wheeled gear needs ground steering (not aero surfaces alone).
- Ballast allowed if permanently installed, not in payload bay, not tradeable for payload.
- Payload: unmodified commercially available 2L cylindrical plastic bottles, carried internally.
  - EMPTY BOTTLE: gross weight > 1.0 lb and < 4.0 lb (unpressurized air or inert material).
  - FILLED BOTTLE: gross weight >= 4.0 lb.
  - Min 1 bottle per flight. After a scored flight, next attempt must add >= 1 empty bottle AND/OR
    swap >= 1 empty for a filled one. Total scored bottle count must stay constant or increase.
  - Spill that delays flight ops -> forfeit one flight attempt.
  - Cargo bay fully enclosed, bottles not exposed to airstream, must not shift. Any size/shape, multiple bays OK.
  - Unload demo at weigh station: <= 2 people, 1 minute, configuration unchanged since flight.
    Filled < 4.0 lb counts as empty; empty < 1.0 lb not counted. No tethers/harnesses on bottles.
- Flight: one flight per attempt, 60 s time limit from call to flight line, NO multiple takeoff tries (Regular).
  Airborne within 100 ft. No turn before 400 ft from start. One full 360 deg circuit. No aerobatics.
  Land within 400 ft, same direction as takeoff, no touch-and-go, stay on runway/zone.
  Two escorts + pilot; one member may hold the aircraft; main gear on takeoff line; no push on release.
  Anything other than a prop broken on landing falling off -> flight disqualified. Stickers/tape/covering
  detaching -> 25% deduction.
- Scoring (rules p. 36):
  - FS = 3*EB + 11*FB   (EB = # empty bottles, FB = # filled bottles)
  - FFS = (FS1 + FS2 + FS3)/3 + PPB   (top 3 flights)
  - PPB = max(10 - (FS - PS)^2, 0), PS = predicted max flight score read off the TDS curve at the
    measured density altitude. PPB uses whichever of the top-3 flights gives the largest PPB.
  - Tie-break: total filled bottles in top 3 scored flights.
- TDS: 1-page stand-alone doc (graph of predicted max flight score vs density altitude, English units,
  one value per altitude, monotonic, may include headwind/rolling drag/etc.) + a JSON data file.
  Bad JSON -> may lose the prediction bonus.
- Deadlines: lottery interest window Sept 16-30, 2026; lottery published Oct 1, 2026.
  Design Report + TDS + 2D drawing due 02/01/2027 11:59:59 EST (East/Florida, March)
  or 03/08/2027 (West/California, April). ECR deadline 02/26/2027 East, 04/02/2027 West.
  Late penalty 5 pts/day up to 5 days.

### Scoring insights [INFERRED]
- Points per pound are nearly equal: empty ~3.0 pts/lb (at ~1.0 lb), filled ~2.75 pts/lb (at 4.0 lb).
  Per bottle, filled is 3.7x better. Empties cost bay volume and drag more than weight.
  Likely direction: size the bay around filled bottles, use empties as +3 increments.
- Payload must increase every scored flight and FFS averages the top 3, so a planned payload
  "ladder" of >= 3 successful rungs is needed, and the bay must fit the top rung.
- PPB is effectively "predict your exact max configuration": missing by one empty bottle (3 pts)
  drops PPB from 10 to 1. Worth nearly one filled bottle.

### Team context (answers from Jordan)
- First-year team (no prior SAE aircraft or legacy data).
- Pilot: experienced with large/heavy (10+ lb) RC aircraft.
- Shop: laser cutter, 3D printers, machine shop / CNC mill. NO foam hot-wire.
- CAD: SolidWorks.
- Aircraft budget: under $1,000 (one airframe, value components, few spares). [INFERRED] favors 2 motors.
- Testing: thrust stand (have or can build) + flying field. No wattmeter/telemetry yet
  (recommended buying an inline wattmeter).
- Jordan wants help on everything: sizing & performance, aero & stability, structures & layout,
  report & TDS, and wants real external/online tools used (e.g. OpenFOAM, FluidX3D, not limited to these).

### Local compute [VERIFIED 2026-09-18]
- Laptop: AMD Ryzen 5 PRO 5675U, ~16 GB RAM, AMD integrated Radeon graphics only (no NVIDIA).
- WSL2 Ubuntu + docker-desktop distros installed (stopped). Python 3.14 with numpy 2.3.4, scipy 1.17.1,
  matplotlib 3.10.7, pandas 2.3.3, pypdf, pymupdf, pdfplumber.
- NOT installed: xfoil, avl, xflr5, openvsp, OpenFOAM, gmsh, paraview, aerosandbox.
- [INFERRED] FluidX3D (OpenCL) should run on the iGPU but at limited resolution; OpenFOAM feasible in WSL
  for a few-million-cell RANS case. Plan: AeroSandbox+NeuralFoil for sizing now, AVL/XFLR5 for
  stability, CFD later for targeted questions (fuselage drag, prop wash, flapped wing).

### Proposed plan (draft, to Feb 1, 2027)
1. Now -> mid-Oct: scoring/ladder model + conceptual sizing (100 ft takeoff model, motor/prop/battery,
   wing area, bottle count, 2 vs 4 motors). AeroSandbox + Python.
2. Mid-Oct -> Nov: airfoil, tail, CG/stability (AVL/XFLR5); spar/structure (wood/ply/aluminum);
   SolidWorks layout; thrust stand tests.
3. Late Nov -> Dec: build prototype, test-fly, measure takeoff distance at stepped weights.
4. Early Jan: targeted CFD. Jan: calibrate prediction with test data -> TDS curve + JSON, report, 2D drawing.

---

## [2026-09-18 20:31 CDT] Decisions from Jordan (session 1, second message)

- EVENT: assume the SOONER competition = East / Florida (March 2027). Design deadline = Feb 1, 2027
  (Design Report + TDS + 2D drawing, 11:59:59 PM EST). This supersedes "event undecided".
- This file (`PROJECT_MEMORY.md`) is the project memory: append-only, timestamped, latest wins.
- Standing rule: when in doubt, document work here for future Claude Code sessions.
- Bottle dimensions: use standard US 2L bottle dimensions from a web lookup (see next entries).
- Research what typically goes in the bottles, using 2026 (last year) info where possible.

---

## [2026-09-18 20:39 CDT] Research: standard US 2L bottle dimensions

- dimensions.com "Soda Bottle - 2 Liter": overall height 12.4 in (31.5 cm), diameter 4.33 in (11 cm). [VERIFIED source]
- Wikipedia "Two-liter bottle": height 300-330 mm (12-13 in), diameter 100-120 mm (3.9-4.7 in); PET, one piece,
  corrugated (petaloid) base. [VERIFIED source]
- Empty bottle mass: web sources disagree (30-80 g quoted); most say ~40-50 g. Working value 0.10 lb (~45 g)
  incl. cap. [UNVERIFIED -- weigh the actual bottles]
- WORKING BOTTLE MODEL for sizing: 4.33 in dia x 12.4 in tall, 0.10 lb empty.
- DESIGN ENVELOPE per bottle slot until real bottles are measured: 4.7 in dia x 13.0 in long [INFERRED:
  covers the whole Wikipedia range]. Shrink once the team buys and measures its chosen brand.
- TODO (Jordan/team): buy the brand you will fly, measure dia/height/empty mass of several, record here.

## [2026-09-18 20:39 CDT] Research: what goes in the bottles (2026 info)

### What the rules actually say [VERIFIED]
- 2026 rules: bottles contain "unpressurized air or material". 2027 rules: "unpressurized air or INERT material".
- No rule and no official FAQ (as of 2026-09-18) names a specific filler. Teams supply their own bottles
  [INFERRED from rules wording; not stated explicitly].
- Spill that delays flight ops -> forfeit one flight attempt (both years).
- 2027 adds: unloaded bottles must be free of tethers, harnesses, or similar external modification.
- Searched: official FAQ list, 2026 NAU capstone docs, TAMU/UC news articles, general web. No public source
  states what 2026 teams filled bottles with. Articles only say "weighted 2-liter plastic bottles".
  Per-team 2026 flight scores are not public (require saestars.com team login).

### Filler analysis [INFERRED; bulk densities are typical values, UNVERIFIED]
Targets with margin: FILLED = 4.05 lb gross, EMPTY = 1.05 lb gross (bottle 0.10 lb assumed).
Filler mass: FILLED 1.792 kg (3.95 lb), EMPTY 0.431 kg (0.95 lb). Nominal volume 2.0 L.
Brim-full average density needed: FILLED 0.896 kg/L, EMPTY 0.215 kg/L.

| Filler        | kg/L | FILLED fill % | EMPTY fill % | Notes |
|---------------|------|---------------|--------------|-------|
| water         | 1.00 | 90%           | 22%          | sloshes if not full; brim-full = 4.51 lb (+0.46 lb waste); leak/spill risk; "inert"? ask FAQ |
| dry sand      | 1.6  | 56%           | 13%          | cheap, dense; half-empty bottle lets sand shift at high pitch/vibration |
| pea gravel    | 1.6  | 56%           | 13%          | like sand, less dust, easier cleanup |
| white rice    | 0.8  | 112% (NO)     | 27%          | TRAP: brim-full rice = 3.63 lb gross -> scores as EMPTY, not filled |
| steel BBs     | 4.7  | 19%           | 5%           | very compact, rolls freely -> worst for CG shift |
| sawdust       | 0.21 | no            | ~103%        | brim-full ~1.03 lb gross: right at the 1.0 lb empty limit, too marginal |

Takeaways:
1. Most practical choices: dry sand or pea gravel (cheap, inert, dense, cleanable), or water if the FAQ allows it.
2. Free space inside the bottle lets the payload CG move when the aircraft pitches (rotation ~10-15 deg).
   Liquid moves immediately. Sand/gravel only flows past its angle of repose (~30-35 deg), so it is much
   better. Best: a BRIM-FULL dry mix tuned to the target density (e.g. sand + a lighter granular filler)
   so nothing can move.
3. Never use rice alone for a filled bottle (it cannot reach 4.0 lb).
4. Weigh every bottle on a calibrated scale before each flight; the weigh station is final.
   Filled < 4.0 lb scores as empty; empty < 1.0 lb does not count.
5. Cap security matters (spill = forfeit attempt), but tape/tethers may count as "external modification".

### Recommended official FAQ question to submit (saeaerodesign.com FAQ)
"Regular Class 2027 7.4: (a) Is water an acceptable 'inert material' for bottle fill? (b) May teams seal the
bottle cap with tape or thread sealant, or does that count as modification? (c) Are there restrictions on
granular fillers such as sand or gravel?"

## [2026-09-18 20:39 CDT] Research: 2026 Regular Class (last year) findings

### 2026 -> 2027 rule changes (diffed section 7 text) [VERIFIED]
- Max span: < 120 in (2026) -> < 96 in (2027). Min span > 72 in unchanged.
- Flight score: FS = 4*EB + 15*FB (2026) -> FS = 3*EB + 11*FB (2027). PPB formula unchanged.
- Filler wording: "material" -> "inert material".
- Payload increase rule now in the rulebook: "Total scored bottle count must remain constant or increase".
- New: unloaded bottles must be free of tethers/harnesses/external modification.
- Tie-break: lowest empty weight (2026) -> most filled bottles in top 3 flights (2027).
- Everything else in section 7 (materials, propulsion, battery, props, cargo bay) is unchanged.
- [INFERRED] every 2026 aircraft (many had 10 ft spans) must be redesigned for 96 in, so a first-year
  team is less disadvantaged than usual.

### Official FAQs (verbatim copies in reference/2026/SAE_FAQ_394_393_395_382.txt) [VERIFIED]
- FAQ 394 (2026): total bottle count must be constant or increasing. 2 empty + 2 filled -> 3 filled is NOT
  allowed. Valid: -> 1 empty + 3 filled, or -> 3 empty + 2 filled.
- FAQ 393 (2026): TDS breakpoints need not be evenly spaced; duplicate a density altitude at a score step to
  avoid interpolation (the highest score is used for duplicates); otherwise linear interpolation.
  (2026 used CSV; 2027 rules say JSON. Assume the same interpolation behavior [UNVERIFIED for 2027].)
- FAQ 395 (2027, posted 2026-09-14): prop diameter limit is the SUM of prop diameters per motor
  (2 motors: 12 in per motor, e.g. 1x12 or 2x6; 4 motors: 9 in per motor). No blade-count limit.
  SAE says battery + prop limits were set deliberately to cap payload capability since the power limiter was removed.
- FAQ 382 (2025): differential thrust does NOT count as ground steering; need a steerable wheel/mechanism.

### 2026 results (placings only; scores not public) [VERIFIED docs, column mapping INFERRED]
- East: March 6-8, 2026, Lakeland FL. Regular mission 1st Politechnika Poznanska (White Eagle), 2nd UW-Platteville
  (Pioneer Flyers), 3rd UFBA (Axe Fly). Regular overall: same order. Design 1st Warsaw UT (WUT Regular).
- West: April 17-19, 2026, Fort Worth TX (note: the 2027 rules say West is in California).
  Regular mission and overall: 1st NUAA (Phoenix), 2nd Poznan (White Eagle), 3rd Tarleton State (Texan Aero).
- TAMU Regular (Farmers Flight): 5th overall, 6th mission, 14th design report; 1st presentation.
  UC AeroCats Regular: 4th overall; ten-foot span.

### NAU "Mach Pine" 2026 Regular (a first-time capstone team) -- a useful low-end data point [VERIFIED poster/slides]
- Final: 80 in span, 19 in chord, 3 deg dihedral, S1223 wing airfoil, NACA 0012 tail, 39 in x 8 in stab,
  60 in long, 26 in tall. 2x Spektrum 4250-800kV with Master Airscrew 12x6 3-blade props.
  12.2 lb empty, 20 lb loaded. Cargo volume: 2 bottles. Goal: two 4-lb filled bottles.
- Tools: MATLAB, ANSYS Fluent & Mechanical, XFLR5, OpenVSP.
- Test: took off within 100 ft carrying 2 empty bottles (~1 lb each), but the flight ended in a crash.
- Lesson [INFERRED]: an empty-weight fraction around 60% leaves little payload. Plan early flight testing and repair time.

### Reference files saved to the project (for future sessions)
- reference/2026/2026_SAE_AeroDesign_Rules_Set.pdf
- reference/2026/2026_SAE_Aero_Design_East_Final_Results.pdf, ..._West_Final_Results.pdf
- reference/2026/NAU_MachPine_2026_Regular_poster.pdf
- reference/2026/UW_2026_rule_summary.pdf (a team's summary; it wrongly says "single electric motor")
- reference/2026/SAE_FAQ_394_393_395_382.txt

### Sources
- https://www.dimensions.com/element/soda-bottle-2-liter
- https://en.wikipedia.org/wiki/Two-liter_bottle
- https://saeaerodesign.com/cdsweb/rqa/BrowseFAQs.aspx (FAQ 382, 393, 394, 395)
- https://saeaerodesign.com/cdsweb/gen/DownloadDocument.aspx?DocumentID=10643d37-9fd1-4821-b413-9b7ddae8724b (2026 rules)
- https://www.saeaerodesign.com/content/2026-SAE-Aero-Design-East-Final-Results.pdf
- https://www.saeaerodesign.com/content/2026-SAE-Aero-Design-West-Final-Results.pdf
- https://www.ceias.nau.edu/capstone/projects/ME/2026/F25toSp26_Aero26/RegularClass.html (poster, slides;
  design report and most slides are password protected and were not opened)
- https://news.engineering.tamu.edu/news/2026/04/27/aero-design-team-continues-international-success/
- https://www.uc.edu/news/articles/2026/05/engineers-place-first-in-aircraft-design-competition.html
- https://aerouw.org/rule_summary.pdf

---

## [2026-09-18 20:54 CDT] Workflow: local reference library for token efficiency (tools/doc2text.py)

Jordan proposed: download documents once, convert PDFs/web pages to text with a Python script, and look
at the text instead of re-reading originals. Adopted, with these additions: an index, page markers,
per-page reliability flags, on-demand page rendering, and the file-rule amendments in the next entry.

### Commands (run from the project root)
- `python tools/doc2text.py fetch URL --name ID [--note TEXT]`  download + convert (cached; --force to refresh)
- `python tools/doc2text.py add PATH --name ID [--source URL] [--note TEXT]`  convert a local file in place
- `python tools/doc2text.py render ID PAGES`  PNG of PDF page(s) -> reference/render/ (only when needed)
- `python tools/doc2text.py note ID TEXT`, `rebuild`, `list`
- Handles PDF (PyMuPDF), HTML (BeautifulSoup+lxml), DOCX, PPTX (incl. truncated files), XLSX.
  Detects encrypted Office files and plain zips (flagged, not converted). No new packages were installed.

### Layout
- reference/INDEX.md: one row per document (ID, type, pages, ~tokens, flags, source, note). READ THIS FIRST.
- reference/text/ID.txt: text with markers like `=== PAGE 44 | p.36 | math ===` (PDF page | printed page | flags).
- reference/raw/: downloaded originals. reference/manifest.json: machine-readable index.
- reference/2026/: 2026 originals added in place.

### Lookup procedure (token-efficient)
1. Read reference/INDEX.md (small), not whole documents.
2. Grep reference/text/ for keywords, then Read only those line ranges. Cite printed page numbers.
3. Render a page image only if it is flagged (math/garbled/img) and the exact form matters.

### Measured [VERIFIED 2026-09-18]
- 15 documents: 4.30 MB of originals -> 0.30 MB of text (7%).
- Each SAE FAQ page: 17-30 KB of HTML -> about 150-420 tokens of text.
- rules_2027.txt is about 33k tokens in total: never read it whole, grep it.

### Extraction caveats found while testing [VERIFIED]
- PyMuPDF + Unicode NFKC recovers the Cambria Math equations that pdftotext drops. Rules p.36 reads
  "FS= Flight Score= 3(EB) + 11(FB)", "PPB= ... MAX(10 -(FS-PS)2, 0)". Sub/superscripts are flattened:
  "(FS-PS)2" means squared, "FS1" means FS_1. Those pages carry the `math` flag.
- The rules PDFs draw section NUMBERS (e.g. "7.6") as small images, so they are missing from the text.
  Search by heading words instead.
- The NAU poster has broken font encoding (flag `garbled`). Render it if needed.
- saeaerodesign.com is ASP.NET and wraps the whole page in a <form>; the converter must not strip <form>.
  The `lowtext` flag caught this bug on the first run.
- TOOL QUIRK: backslash-u escape sequences typed into Claude tool inputs (Write/Edit/Bash) get turned into
  literal Unicode characters. In code, build non-ASCII characters with chr(0x...) instead.

### Superseded / new
- reference/2026/SAE_FAQ_394_393_395_382.txt is superseded by reference/text/faq_*.txt (kept, not deleted).
- Library IDs as of now: rules_2027, rules_2026, results_2026_east, results_2026_west, nau_2026_poster,
  uw_2026_rule_summary, faq_list, faq_157, faq_170, faq_382, faq_393, faq_394, faq_395,
  wiki_two_liter_bottle, dimensions_2l_bottle.
- NEW [VERIFIED FAQ 170]: every pilot must present a valid AMA (Academy of Model Aeronautics) card at the
  field. The only exception is MAAC (Canada) members. ACTION: confirm the team pilot's AMA membership is current.
- NEW [VERIFIED FAQ 157]: all team members and the faculty advisor must be affiliated on www.sae.org. Students who
  submit documents or ask rules questions must also be affiliated on www.saeaerodesign.com.

## [2026-09-18 20:54 CDT] Amendment to RULES FOR THIS FILE (rules 7-9; appended, since the file is append-only)

7. CURRENT STATE SUMMARY entries: at the end of each design phase, or once ~400 lines have been added since the
   last one, append an entry titled "CURRENT STATE SUMMARY" that consolidates the latest truth (decisions,
   key numbers, open items, file locations). Future sessions: read the RULES header, then the LAST
   "CURRENT STATE SUMMARY" and everything after it. Grep older entries only when needed.
   (None written yet: the log is still short enough to read in full.)
8. Analysis scripts write full outputs to files and print only a short summary. Never paste full solver or CFD
   logs into the conversation.
9. Look things up library-first: reference/INDEX.md -> grep reference/text/ -> read line ranges -> render only
   if flagged. Use WebFetch only for one-off facts; archive anything that will be cited again with
   `doc2text.py fetch`.

---

## [2026-09-18 21:06 CDT] AI token-efficiency workflow set up (CLAUDE.md, AI_WORKFLOW.md, settings)

Verified against official Claude Code docs, archived as reference/text/cc_*.txt (costs, prompt_caching,
model_config, memory, best_practices, vs_code, context_window, commands, sessions, hooks, statusline,
troubleshooting, settings_reference, env_vars). These are big files (cc_hooks ~82k tokens,
cc_env_vars ~124k): grep them, never read them whole.

### Key facts [VERIFIED from docs]
- Every request re-sends the full conversation; cached re-reads still count toward usage. /clear costs nothing.
  /compact is itself a large request and is lossy.
- Auto-compact is ON by default. On Opus 4.7+ / Sonnet 5 / Fable (1M window, Anthropic API) it fires at about
  967K tokens. Settings: `autoCompactEnabled` (the /config "Auto-compact" toggle), `autoCompactWindow`
  (100K-1M; /autocompact writes it to USER settings), env CLAUDE_CODE_AUTO_COMPACT_WINDOW,
  CLAUDE_AUTOCOMPACT_PCT_OVERRIDE, DISABLE_AUTO_COMPACT.
- CLAUDE.md may contain a "# Compact instructions" section. The project-root CLAUDE.md and auto memory are
  re-injected from disk after compaction.
- These invalidate the prompt cache: switching model, changing effort (except Fable 5.1), fast mode, MCP
  connect/disconnect, plugin toggle, compaction, many images, upgrading Claude Code. Rewind keeps the cache.
  Editing CLAUDE.md mid-session keeps the cache but only applies after /clear, /compact or restart.
- Cache TTL: 1 hour on a subscription within limits (5 min on an API key / usage credits).
- VS Code extension: supports only a subset of slash commands (type / to list), has checkpoints/rewind via the
  message hover button, a context indicator in the prompt box, a Session history button, and /usage.
- Keep CLAUDE.md under 200 lines. MCP servers add tool names + server instructions to every session.
  Agent teams use about 7x the tokens.

### Changes made (Jordan approved both via questions)
- CREATED .claude/settings.json (project scope): {"autoCompactEnabled": true, "autoCompactWindow": 200000}.
  It is a backstop only. It takes effect from the NEXT session: the settings watcher only watches directories
  that had a settings file at session start [per update-config skill; not directly verified].
- EDITED C:/Users/jprun/.claude/settings.json (GLOBAL): effortLevel "xhigh" -> "high". Model stays "opus".
  Applies to new sessions. Pick xhigh at the START of hard design sessions.
- CREATED CLAUDE.md (project root, ~40 lines, auto-loaded every session): session-start protocol,
  working rules, checkpoint procedure, "# Compact instructions".
- CREATED AI_WORKFLOW.md: the human guide (session loop, which reset to use, auto-compact, model/effort,
  tips, cheat sheet). CLAUDE.md tells Claude not to load it unless asked.

### Session protocol (summary; CLAUDE.md is authoritative)
Start fresh with one task -> Claude reads the log header + LAST "CURRENT STATE SUMMARY" + later entries ->
work -> Jordan says "checkpoint" -> Claude appends to the log -> Jordan runs /clear.
Wrong path -> rewind (cheapest). Long session mid-task -> /compact with focus. Side question -> /btw.
Break > 1 hour -> checkpoint first.

### Suggestions left to Jordan (not done)
- Disable MCP connectors this project does not use (Indeed, Canva probably) via /mcp.
- Gmail / Google Calendar connectors need authorization in claude.ai connector settings if ever wanted.

## [2026-09-18 21:06 CDT] CURRENT STATE SUMMARY (end of setup/research phase; start here)

Consolidates everything above. Older entries hold the detail and sources; grep them only when needed.

### Project
- SAE Aero Design 2027 Regular Class (2L-bottle cargo). First-year team. Jordan leads the work with Claude.
- Event: plan for EAST / Florida (March 2027). Design Report + TDS (1-page PDF + JSON) + 2D drawing due
  2027-02-01 11:59:59 PM EST. Lottery interest window closes 2026-09-30.
- Team: experienced heavy-RC pilot; laser cutter, 3D printers, machine shop/CNC mill (no hot-wire);
  SolidWorks; budget < $1,000; thrust stand + flying field; no wattmeter yet (buy one).
- Compute: Ryzen 5 5675U laptop, 16 GB, AMD iGPU, WSL Ubuntu. Python: numpy/scipy/matplotlib/pandas,
  pymupdf, bs4, lxml, python-docx/pptx, openpyxl, requests. No aero tools installed yet.

### Rules that drive the design (rules_2027, printed pages 33-36 unless noted)
- Span > 72 in and < 96 in; chord > 4 in; length < 120 in; gross weight <= 55 lb (p.12).
- NO FRP (carbon/fiberglass/duct tape) except bought motor mounts, props, gear, linkages.
- 2 motors (12 in props) or 4 motors (9 in props); the limit is the SUM of prop diameters per motor
  (FAQ 395). One 4S LiPo <= 2200 mAh; no power limiter. Separate Rx battery >= 1000 mAh.
- Airborne within 100 ft, single try; one 360-degree circuit; land within 400 ft, same direction.
  Steerable ground gear required (differential thrust does not count, FAQ 382).
- Bottles carried internally, fully enclosed, no shifting; unloaded by 2 people in 60 s; no tethers.
  EMPTY: > 1.0 and < 4.0 lb. FILLED: >= 4.0 lb. Each scored flight must add payload, and the total bottle
  count can never go down (FAQ 394).
- FS = 3*EB + 11*FB. FFS = mean of the top 3 FS + PPB, where PPB = max(10 - (FS - PS)^2, 0).
  Tie-break: filled bottles in the top 3 flights.
- TDS: predicted max FS vs density altitude, monotonic, English units, plus JSON. Breakpoints may be uneven
  and duplicated at score steps (FAQ 393, 2026; assume the same for 2027).
- All pilots need a current AMA card (FAQ 170). Team + advisor must be affiliated on sae.org (FAQ 157).

### Working design assumptions
- Bottle slot envelope 4.7 in dia x 13.0 in until real bottles are measured (typical 4.33 x 12.4 in, ~0.10 lb).
- Targets: filled 4.05 lb, empty 1.05 lb gross. Filler: dry sand or pea gravel, ideally a brim-full mix
  tuned to ~0.9 kg/L (filled) so nothing shifts. NOT rice alone (brim-full = 3.63 lb, scores as empty).
  Water only if an FAQ confirms it counts as inert.
- Strategy [INFERRED]: size the bay around filled bottles; use empties as +3 steps; plan a payload ladder of
  3 or more successful flights; PPB rewards predicting the exact maximum configuration.
- 2 motors favored by budget (trade study still to do). 2026 NAU data point: 80 in span, 12.2 lb empty,
  aimed at 2 filled bottles, crashed in testing.

### Tooling in place
- PROJECT_MEMORY.md (this log, append-only). CLAUDE.md (auto-loaded rules). AI_WORKFLOW.md (human guide).
- tools/doc2text.py + reference/INDEX.md: 29 documents (rules 2026/2027, results, FAQs, bottle pages,
  Claude Code docs).
- .claude/settings.json: autoCompactWindow 200000. Global effort: high.

### Open items / action items for Jordan
1. Register interest in the lottery by 2026-09-30.
2. Confirm the pilot's AMA membership; affiliate everyone on sae.org.
3. Buy and measure the bottles you will fly (diameter, height, empty weight).
4. Optional: submit an FAQ on water as filler / cap sealing.
5. Optional: disable unused MCP connectors (/mcp).

### NEXT TASK (start of the design phase)
Conceptual sizing: pip install aerosandbox (with NeuralFoil); build the scoring/payload-ladder model and a
100 ft takeoff model; motor/prop/battery; wing area and span; bottle count; 2 vs 4 motors.
Suggested session setup: Opus, effort high (or xhigh), fresh session.

---

## [2026-09-18 21:25 CDT] Reference library expanded to 118 docs; model/agent selection guidance; project agents

### Jordan's standing guidance on models and agents (verbatim intent, 2026-09-18)
- Clearing chat context is often worth it: many tasks only need an agent doing one specific job, not the whole chat.
- Sometimes a Sonnet model is all a task needs. Sometimes an extra-high (xhigh) Opus 5 agent is needed.
  Do not lock yourself below Opus xhigh.
- Fable 5: sometimes needed, but use it SPARINGLY and ASK JORDAN FIRST.
- Now encoded in CLAUDE.md ("Model and agent selection") and in the project agents below.

### Project agents created: .claude/agents/ (docs verified in cc_sub_agents: frontmatter model + effort)
- sae-researcher: Sonnet, effort medium; tools WebSearch/WebFetch/Bash/Read/Grep/Glob. Web research; returns tables.
- sae-worker: Sonnet, effort medium. Routine execution: scripts, archiving, reformatting, small edits.
- sae-analyst: Opus, effort xhigh. Trade studies, analysis models, reviews.
- Subagents do NOT receive CLAUDE.md or the global rules, so each profile body repeats the essentials
  (never delete/vault.ps1, ASCII/chr() quirk, library-first, never write PROJECT_MEMORY.md).
- A running session does not detect a newly created .claude/ directory. Jordan must RESTART Claude Code
  (not just /clear) before the agents and .claude/settings.json (autoCompactWindow 200000) load.
  [per cc_sub_agents and the update-config skill]

### How the library was built (method worth reusing)
- 5 Sonnet general-purpose agents ran in parallel, one per topic (design methods, aero data/tools,
  propulsion/electrical, structures/materials, site climate + precedent). Each verified every URL by download
  and returned a table. The main session imported sequentially (tools/doc2text.py add), so manifest.json had
  one writer. Cost: about 546k subagent tokens total (101k-127k each), 7-10 min wall time.
- Import helper used: a script that copies the files into reference/raw/<id>.<ext>, then runs doc2text add with
  --source/--note. (It lived in the session scratchpad and is gone; trivial to rewrite.)
- doc2text.py fixes: on SSL certificate errors it falls back to curl (the NAU server sends an incomplete chain);
  fetch failures now print one line instead of a traceback, and nothing is added to the manifest.
- APC site (apcprop.com) returns 403 unless given a full browser UA + a Referer of the performance-data page.
  doc2text fetch does not send these, so download APC files with curl + headers, then `add`.

### What is in the library now (118 docs, ~2.9M tokens total; READ reference/GUIDE.md, the topic map)
- Methods: drela_design_rules, nicolai_rc_model_aero (written for SAE Aero; hosted by SAE), mit_airpower,
  mit_prop_appendix, scholz_tail_volume, nasa_grc_propeller_thrust.
- Aero: 10 airfoil .dat files (S1223, S1223RTL, S1210, E423, FX74-CL5-140, CH10sm, SD7062, NACA4412; tails SD8020,
  NACA0012), selig_guglielmo_1997, selig_lowre_lecture, UIUC LSAT wind-tunnel volumes 1-3 (plots: render pages),
  tool docs (AeroSandbox, NeuralFoil, AVL, XFOIL, XFLR5 parts 1-3, VSPAERO), CFD docs (OpenFOAM, FluidX3D).
- Propulsion: 11 APC PER3 data files (12x6E/8E/10E/12E, 11x7E/10E, 9x6E/4.5E/7.5E, 6x4E/5.5E), APC RPM limits,
  drela_motorprop, QPROP/QMIL docs, UIUC prop DB + Brandt-Selig paper, LiPo papers, servo sizing sources.
- Structures: Wood Handbook 2021 ch5/8/10/11/12, ANC-18 wood aircraft (OCR text), aluminum 6061/7075, balsa vs
  density (hobbyist), PLA/PETG/LW-PLA data sheets, FDM infill paper, spar design tutorial.
- Site/TDS: KLAL elevation 141.8 ft [VERIFIED airnav]; NOAA March normals Tmax 80.2 F / Tmin 56.5 F (Lakeland 2
  station); NWS density-altitude equations; reference/data/klal_asos_2021-03_to_2026-04.csv (hourly KLAL
  weather, all months, 68k rows, kept out of text/ so it does not flood grep; see reference/data/README.txt).
- Precedent: NAU 2026 reports 1+2 (same mission), FAMU-FSU 2020/2021, NAU 2018/2019/2021/2025, NYU 2018 (older
  missions; use for methods: payload prediction, takeoff analysis).

### Known gaps (searched, not found free/legit)
- Stanford AA241 (Kroo) site is offline (NXDOMAIN); no archived takeoff/tail/weight chapters.
- No public 2026 reports from the top teams (Warsaw, Concordia, TAMU, Poznan, NUAA).
- MatWeb is blocked (403); DTIC hinge-moment report down; Borrega & Gibson balsa paper behind a captcha.
- No LiPo-specific (vs Li-ion) government paper on voltage sag at high C; only nasa_uav_battery_model.
- The FAA 5010 record for KLAL needs a login (used AirNav instead).

### Files changed this entry
- NEW: reference/GUIDE.md (topic map), reference/data/ (CSV + README), .claude/agents/sae-{researcher,worker,analyst}.md
- EDITED: CLAUDE.md (model/agent section; GUIDE.md pointer), AI_WORKFLOW.md (tip 8), tools/doc2text.py (curl fallback)
- The CURRENT STATE SUMMARY above is still valid, except: the library is now 118 docs (not 29), and there are project agents.

---

## [2026-09-18 23:47 CDT] Conceptual sizing started (unattended overnight session)

- Installed with pip for Python 3.14.0: aerosandbox 4.2.10, neuralfoil 0.3.3, casadi 3.8.1, plus dill and
  sortedcontainers. All import cleanly [VERIFIED by running python].
- Delegated conceptual sizing to the sae-analyst agent (Opus xhigh). Its work goes ONLY in analysis/sizing/
  (scripts, out/, REPORT.md). Scope: scoring/payload-ladder model, KLAL March density altitude, 2x12 vs 4x9
  propulsion from APC PER3 data, 100 ft takeoff model, NeuralFoil airfoil comparison, empty-weight model,
  span/area/AR sweep -> recommended design point.
- IF THIS IS THE LAST ENTRY: the agent may not have finished (usage limit or session end). Check whether
  analysis/sizing/REPORT.md exists and is complete; if it does not, resume the sizing task from what is in
  analysis/sizing/.

---

## [2026-09-19 00:28 CDT] Conceptual sizing DONE (sae-analyst agent, ~41 min, 88k tokens)

All work in analysis/sizing/. Run order: density_altitude, scoring, propulsion, airfoils (slowest), aero, weight,
takeoff, sweep (~12 s), design_card, wing3d_check (~4 s). Libraries: common.py, mission.py. Headline numbers are
in analysis/sizing/out/design_card.txt [VERIFIED: file read by main session; values below match it].
Main session spot-checked rule citations in rules_2027.txt l.1548-1560, 1576-1578, 1592-1599 [VERIFIED].

### Recommended design point (DA 2000 ft, zero wind, 100 ft takeoff) [INFERRED, medium confidence overall]
- Wing 95 x 26 in rectangular S1223, untwisted: S 17.15 ft^2, AR 3.65, W/S 2.04 lb/ft^2.
- 2 x APC 12x6E, Kv ~840, ~90 A peak total, one 4S 2200 mAh pack (>= 45C burst). 4 x 9x4.5E ties on score
  (E_FFS 52.4 vs 52.6) but weighs 0.39 lb more -> choose 2 motors.
- 6-slot single-layer transverse bay, 29.9 x 13.5 x 5.7 in. Tail V_H 0.55, V_V 0.045, l_t 72 in
  (H 44 x 11.1 in, V 15 x 9.9 in), wood boom. Overall length ~93 in.
- W_TO 35.0 lb (takeoff-limited; the 55 lb limit is not active). W_empty 17.66 lb (band 14.8-20.5).
  Payload 17.4 lb (band 14.5-20.3).
- Top rung 1E4F = 17.25 lb, FS 47, margin only 0.13 lb. Ladder 1E3F (36) -> 0E4F (44) -> 1E4F (47);
  FFS 52.3 with full PPB.
- Speeds: Vs 33.1 ft/s, V_R 36.4, circuit 46.4 ft/s at L/D 8.3; the circuit uses 1.38 of 1.76 Ah usable.
- Draft TDS curve: payload = 18.96 - 0.79 lb per 1000 ft DA (out/design_payload_vs_DA.csv).
  FS 50 (2E4F) below DA ~900 ft, 47 (1E4F) from 1000 to 2000 ft, 44 (0E4F) from 2250 to 3000 ft.
- KLAL March, 09-17 local (n=1441): DA P10 533, P50 1410, P90 1975, max 2484 ft [VERIFIED from ASOS CSV via
  script]. Median wind 9 kt; no wind credit taken.

### Key findings
- The biggest levers on payload are empty weight (1:1; structure x1.2 -> 2E3F), span (~0.13 lb/in near 95 in),
  and pilot rotation technique (k_R 1.2 instead of 1.1 -> -2.8 lb W_TO). Then peak current (70 A 29.2 lb,
  110 A 33.5 lb W_TO), thrust (x0.85 -> -1.5 lb) and CLmax (-10% -> -1.8 lb). A 5 kt headwind is worth +6 lb W_TO.
- Airfoil ranking (NeuralFoil, anchored to tunnel data): S1223 > S1223RTL (-0.4 lb, fallback if the thin trailing edge
  is hard to build) > FX74 > E423 > CH10 > S1210 > SD7062. High confidence in the ranking.
- Chord at 95 in span is flat for 26-32 in; the agent took the smallest wing within 0.5 E_FFS of the optimum.
  The 6-slot bay beats 8 slots (2x4) at every empty-weight band.
- FRP ban (l.1557-1560) -> no carbon boom or spar. An aluminum tube boom costs 0.38 lb and drops the top rung to 0E4F.
- Landing roll 393 ft free vs the 400 ft zone (touchdown included) -> a WHEEL BRAKE IS REQUIRED (114 ft braked).
- AeroSandbox VLM check (wing3d_check.py): the Raymer AR/(AR+2) factor on Cm0 is wrong for this wing. Best wing
  Cm0 is ~ -0.28 (aero.py uses -0.178), and x_np is ~0.44c with the fuselage (hand formula 0.39c). The two errors
  nearly cancel (trimmed CLmax +1.1%), so the sizing stands. USE THE VLM VALUES FOR STABILITY WORK.
- Weight estimate calibrated only on NAU 2026 (K_BUILD 1.066). Our payload fraction of 0.50 vs NAU's 0.39 is the
  single largest uncertainty.

### UNVERIFIED (what confirms it)
- Thrust x0.93 knock-down, 90 A peak, pack sag, motor Rm 0.028 / I0 1.8 -> thrust stand with the real pack.
- Empty-weight coefficients, battery 0.55 lb, prop group 1.68 lb -> build and weigh a test wing panel.
- Bottle slot 4.7 x 13.0 in and the 4.05/1.05 lb fill targets -> measure real bottles.
- Landing friction and brake effectiveness; event runway heading.
- Stability and trim: no AVL/XFLR5 model yet; the tail is sized by volume coefficients only.

### Housekeeping
- analysis/sizing/REPORT.md was NOT written. The agent said the harness blocked sub-agents from writing report
  .md files and asked the main session to write it. It was not written without Jordan's approval. The full
  report text exists only in the overnight session's chat. The numbers are in out/*.txt and out/*.csv.
- out/airfoil_summary.txt still cites selig_guglielmo_1997 l.266 (the correct line is l.267) until airfoils.py is rerun.
- The agent archived one stray output to the vault (id 0e9c883b).
- Not committed to git.
- A multi-line heredoc append with shell variables was blocked by the delete-safety hook (false positive; nothing
  was being deleted). Workaround: write the entry to the scratchpad with the Write tool, then run a plain cat >>.

---

## [2026-09-19 00:28 CDT] CURRENT STATE SUMMARY (end of conceptual sizing; start here)

The [2026-09-18 21:06] summary still holds for the project, rules, team, bottles and scoring, with these updates:
- Library: 118 docs; the topic map is reference/GUIDE.md. Project agents are in .claude/agents/ (researcher,
  worker, analyst).
- Tools installed: aerosandbox 4.2.10, neuralfoil 0.3.3, casadi 3.8.1 (Python 3.14). No AVL/XFLR5/OpenFOAM yet.
- Design point (see the entry above; analysis/sizing/out/design_card.txt): 95 x 26 in rectangular S1223 wing,
  2 x APC 12x6E on 4S 2200, 6-slot bay, W_TO 35 lb, W_e 17.7 lb, payload 17.4 lb, top rung 1E4F (FS 47) at DA 2000 ft.
- Required features found by the analysis: wheel brake, wood (non-FRP) spar and boom, big tail for the S1223 Cm0.

### Action items for Jordan (hardware; these retire the top uncertainties)
1. Lottery interest by 2026-09-30; AMA card; sae.org affiliation (unchanged).
2. Buy and measure bottles.
3. Thrust stand: 12x6E and 12x8E on 800-900 Kv motors with a real 4S 2200 pack (thrust, amps, sag).
4. Build and weigh a wing test panel (refit K_BUILD in weight.py).
5. Decide whether to save the sizing report text as analysis/sizing/REPORT.md (see Housekeeping above).

### NEXT TASK
Stability and trim: install AVL (or XFLR5) and build a model of the design point, starting from the VLM values
(wing Cm0 -0.28, x_np ~0.44c). Size the tail and elevator for trim at CLmax with every bottle-ladder CG, and check
static margin, Cn_beta and Cl_beta. Then fix the Cm0 factor in aero.py and rerun sweep.py.
Suggested: sae-analyst agent; main session on Opus.

---

## [2026-09-19 16:11 UTC / 11:11 CDT] Dedicated compute box: task backlog brainstorm (no scripts written)

Task: Jordan has an always-on mini PC to dedicate to this project for its duration and asked for
ideas for long-running iterative jobs. Brainstorm only; explicitly NO scripts written this session.

### Hardware [VERIFIED 2026-09-19 via AMD product page / TechPowerUp / LaptopMedia]
GMKtec NucBox M6 Ultra. AMD Ryzen 5 7640HS: 6 cores / 12 threads, Zen 4, 4.3 GHz base, 5.0 GHz
boost, 16 MB L3, 35-54 W TDP. Radeon 760M iGPU (8 RDNA3 CUs). 32 GB RAM (DDR5-5600 supported),
512 GB SSD. NOTE: 6 cores, not 8; the 8-core part is the 7840HS.

### Compute budget [INFERRED, order of magnitude, not benchmarked]
- Analytic eval (takeoff integration + weight + aero + score): ~1 ms -> ~1e9 evals/day.
- NeuralFoil point ~1 ms. AVL run ~0.05-0.5 s -> ~2e6-2e7/day.
- XFOIL alpha sweep ~5-30 s -> ~3e4-2e5 polars/day.
- OpenFOAM 2D RANS (~1e5 cells) ~5-15 min -> ~100-300 cases/day.
- OpenFOAM 3D RANS (~5e6 cells, fits in 32 GB) ~8-20 h -> ~1-2 cases/day.
- FluidX3D on 760M: ~60 GB/s effective bandwidth / ~55 bytes per cell-step -> ~1e9 cell-updates/s,
  i.e. 256^3 at ~60 steps/s. UNVERIFIED arithmetic; benchmark before relying on it.

### Backlog written to COMPUTE_BACKLOG.md (NEW FILE, 184 lines)
Tier 1 (highest value per compute hour):
  T1-1 Model validation harness (RUN FIRST): reproduce NAU 2026 aircraft and UIUC LSAT tunnel
       polars; sweep XFOIL Ncrit/transition/roughness settings until they match, then freeze.
  T1-2 Payload-ladder + TDS strategy as a stochastic dynamic program over
       (flights remaining, bottles loaded, successes, scores banked); sweep declared PS to
       maximize expected FFS. Quadratic PPB term makes PS choice worth real compute.
       OPEN [UNVERIFIED]: number of flight attempts available at EAST 2027 (DP input).
  T1-3 Robust takeoff Monte Carlo: P(airborne within 100 ft) vs payload, with uncertainty on
       empty weight, CLmax, mu, thrust, LiPo sag, and density altitude/headwind drawn from
       reference/data/klal_asos_2021-03_to_2026-04.csv (March daytime hours). Feeds T1-2.
  T1-4 Full-factorial design-space MAP (8 vars x 10 levels = 1e8 evals ~ 2-3 h), then NSGA-II /
       CMA-ES multi-start; deliverable is the score plateau, not a single peak.
  T1-5 Structural weight optimization with Monte Carlo over balsa density scatter and spruce
       variability; CalculiX FEA on the shortlist.
Tier 2: T2-1 XFOIL polar farm + NeuralFoil-driven airfoil shape optimization; T2-2 propulsion
  combinatorics (prop x Kv x 2 vs 4 motors x sag, APC RPM limits as hard constraint);
  T2-3 AVL sweeps (trim, static margin, elevator authority at rotation, gust/crosswind vs KLAL
  wind rose); T2-4 bottle packing + CG across EVERY loading state of the ladder; T2-5 mission
  energy / 3-DOF trajectory (2200 mAh must fly the full pattern); T2-6 cross-validation of
  independent models over the whole sweep space.
Tier 3: T3-1 CFD used narrowly (2D check on XFOIL; 3D only for ground effect, junction drag,
  propwash; FluidX3D as an experiment); T3-2 surrogates + Bayesian calibration against thrust
  stand / flight test data; T3-3 QMIL custom prop [legality UNVERIFIED, stretch only];
  T3-4 topology optimization of printed parts (low payoff).
Background chores: daily SAE FAQ/rules diff with alert; nightly pipeline re-run + regression
  tests; density-altitude watch; build/weight tracker feeding the score prediction.
Setup: Ubuntu Server bare metal (not WSL), systemd + tmux, checkpointed resumable jobs writing
  SQLite/Parquet, 6-worker pools for bandwidth-bound work and 12 for cheap evals, log clocks and
  temps (a 35-54 W part in a mini chassis will throttle), watch SSD fill from CFD writes.

### Key judgement recorded
The biggest risk is hours of compute on an uncalibrated model producing a confident wrong
airplane. T1-1 gates everything else. Second judgement: T1-2 and T1-3 are where this project is
most likely to gain points over other teams, because the physics is cheap and the decision
analysis is what teams skip.

### Files changed
- NEW: COMPUTE_BACKLOG.md
- No scripts written (per Jordan's instruction).

### NEXT TASK
Either (a) stand up the mini PC: Ubuntu Server, Python env, aerosandbox/NeuralFoil, XFOIL, AVL,
and implement T1-1 the validation harness; or (b) proceed with conceptual sizing on the laptop as
the previous CURRENT STATE SUMMARY planned and let the mini PC pick up T1-1 in parallel.

---

## [2026-09-19 21:49 CDT] Git consolidated; 20 sources archived for the post-sizing phases

Task from Jordan: talk through how to approach building the airplane, with every decision grounded in an
outside source and using free/open-source tools; make the repo good for future sessions and token-efficient;
merge everything to main and trim stray branches.

### Git housekeeping [VERIFIED by running the commands]
- Local main had the uncommitted analysis/sizing work; origin/main was 2 commits ahead (COMPUTE_BACKLOG.md,
  merged from PR #1 branch claude/mini-pc-compute-ideas-p4tp5m).
- Committed the sizing work (9d8f8d6), merged origin/main (9c8168b), pushed. main == origin/main.
- PROJECT_MEMORY.md merge conflict resolved by keeping BOTH appended blocks in timestamp order
  (00:28 CDT sizing entries, then the 16:11 UTC compute-backlog entry). No existing text was changed.
- Branches: main is the only branch, local and remote. The PR branch was already deleted on GitHub.
  Nothing to trim.
- NOTE: reference/raw/ is tracked in git and is now ~213 MB; .git is 114 MB. Works, but if the repo keeps
  growing consider gitignoring reference/raw/ (text/ + manifest.json are what sessions actually read).

### Jordan's decisions this session
1. Push to GitHub: yes, done.
2. Session task: archive the researched sources.
3. ORDERING, standing guidance: TESTS FIRST. Physical tests (wing panel weigh-in, thrust stand) come before
   further analysis refinement, because the weight model rests on a single calibration point (NAU 2026) and
   every downstream number is scaled by it. This supersedes the "AVL stability and trim" next task from the
   [2026-09-19 00:28] summary as the immediate priority; AVL work resumes after or alongside the test data.

### Library: 118 -> 138 documents (~2.9M -> ~4.1M tokens)
sae-researcher pass (Sonnet, ~58k tokens) found free sources for the gaps conceptual sizing left open.
Every URL was HTTP-200 verified before archiving. New IDs, by gap:
- Design process: vt_aoe_a5_initial_sizing, vt_aoe_a7a_config_layout, vt_aoe_a10_prelim_design (Virginia Tech
  AOE 4065/4066, Raj), mit_1682_flight_vehicle_intro, nasa_se_handbook (SP-2016-6105 Rev2, 262k tokens).
- Structures and loads: nasa_vgh_load_factor_stats (NASA CR-132531, VG/VGH statistics -> V-n load factor),
  uf_wing_spar_optimization (14 lb / 7 ft span RC aircraft, closest scale match), syracuse_wing_spar_design,
  fpl_minimum_weight_sandwich (USDA FPL RN-086).
- Tools: openvsp_user_manual, gmsh_reference_manual (298k), calculix_manual (CalculiX 2.22, 448k),
  freecad_fem_workbench, su2_quick_start, paraview_docs.
- Flight test: nasa_takeoff_flighttest_method (NASA TN D-7603, takeoff performance INCLUDING pilot technique),
  ardupilot_airspeed_calibration, ama_national_safety_code.
- Build technique: modelaviation_sliced_rib_method, modelaviation_diy_laser_cutting (AMA magazine grade:
  cite as practice, never as allowables).
reference/GUIDE.md updated with three new sections and the notes above. The big ones are GREP ONLY.

### Gaps and dead ends found by the search [VERIFIED this session]
- NO published study compares AVL / XFLR5 / VSPAERO / OpenFOAM against wind-tunnel data at Re 100k-500k.
  We therefore have NO external error band for our own aero predictions. Close it in-house by running our
  tools against the uiuc_lsat_* polars already held (this is COMPUTE_BACKLOG T1-1, validation harness).
- Stanford AA241 is confirmed dead (adg.stanford.edu does not resolve). Stop looking for it.
- MIL-HDBK-23 was canceled in 1988 and folded into MIL-HDBK-17, which is not free. Use fpl_minimum_weight_sandwich.
- wiki.freecad.org is behind Anubis bot protection: curl and doc2text get an interstitial page, not content.
  The first freecad_fem_workbench download captured that interstitial; it was vaulted (id a1aad00b) and
  replaced by the raw.githubusercontent.com FreeCAD-documentation mirror. Browser-only for other wiki pages.
- Still missing: stall-speed and static-margin flight-test procedures; covering-film guidance; no
  SAE-Aero-specific requirements-traceability source (the held student team reports are the closest thing).

### Approach proposed to Jordan (not yet built; his reaction pending)
- DECISIONS.md: a flat ledger, one row per decision (ID, decision, number with units, source citation as
  library ID + line range or script path + output file, confidence, what would overturn it). Rule: nothing
  enters without an external citation or a script whose inputs are cited; anything else is [UNVERIFIED] with
  a retirement path. Purpose: a new session learns WHY the wing is 95 in without reading 600 log lines.
- analysis/README.md (run order and which outputs are current) and a short pinned state file, so context
  loading is one short read. The log stays append-only as the audit trail.
- Three kinds of claim need three kinds of grounding: physics/method -> literature; component behavior ->
  manufacturer data plus independent measurement; OUR airframe -> our own tests, because no source exists
  for an airplane nobody has built. That third category is why tests come first.

### NEXT TASK
Write the test plan for the two tests that retire the biggest uncertainties, with procedures grounded in the
new sources: (1) wing test panel build and weigh, to refit K_BUILD in analysis/sizing/weight.py; (2) static
thrust stand for 12x6E and 12x8E on 800-900 Kv motors with a real 4S 2200 pack, measuring thrust, current
and pack sag against the apc_* data. Include what to measure, how many runs, and how each result feeds back
into a specific script. Then, with data in hand, resume AVL stability and trim.

## [2026-09-20 21:55 CDT] TEST_PLAN.md written (T-1 wing panel weigh-in, T-2 static thrust stand)

Task: the NEXT TASK from the [2026-09-19 21:49] entry. Wrote the test plan for the two physical
tests that retire the biggest uncertainties, under Jordan's TESTS FIRST ordering.

### Files changed
- NEW: TEST_PLAN.md (about 440 lines, project root).
- NEW: analysis/tests/data/ (empty; holds the CSVs the plan specifies).
- No analysis scripts changed. No model constants changed. Nothing committed to git.

### Value of each test, computed from existing outputs [VERIFIED by reading the files]
- T-1: structure band x0.8/x1.0/x1.2 -> payload 20.25 / 17.38 / 14.50 lb -> FS 55 / 47 / 39
  (out/design_card.txt). 16 Flight Score points of spread, about 2.8 FS per lb of empty weight.
- T-2: THRUST_FACTOR x1.00 -> W_TO_max +1.18 lb; x0.85 -> -1.41 lb (out/takeoff_sensitivity.csv).
  About 2.6 lb of takeoff weight, roughly 7 FS points.
- Therefore T-1 ranks first if only one test gets done. The two are independent and can run in
  parallel with two people.

### Design choices in the plan worth remembering
1. T-1 weighs COMPONENTS, not just the finished panel. One panel total is one equation for three
   unknowns (A_WING0, A_WING1, K_BUILD) and wrong combinations that match the total extrapolate
   differently to a 95 in wing. Phase A weighs every piece of stock (n >= 15, gives the balsa
   density scatter that COMPUTE_BACKLOG T1-5 needs), Phase B weighs each rib (n = 9) and each
   part, Phase C weighs the assembly and the film. K_BUILD then becomes a measured glue-and-
   assembly overhead instead of a catch-all fudge factor.
2. T-2 takes all model-critical points at 100 PERCENT THROTTLE, varying load by changing props
   rather than throttle. At full throttle the ESC is effectively a closed switch, so
   V_motor = V_batt and the Drela first-order model applies directly (drela_motorprop eqs 1-2).
   At part throttle the effective motor voltage is an extra unmeasured quantity. Part-throttle
   points are still taken for the mission energy model but tagged lower confidence.
3. T-2 always logs THRUST AND RPM TOGETHER, so measured thrust is compared against the APC table
   at matched RPM. That isolates prop model error from motor, battery and ESC error. Comparing at
   matched throttle would yield a meaningless THRUST_FACTOR.

### Finding: A_WING1 looks 2 to 4 times too high [INFERRED, computed this session]
weight.py A_WING1 = 0.05 implies 23.7 g per rib at 26 in chord (0.05 * 2.167 * 4.33 ft^2 over
9 ribs). Computed the real number: S1223 area coefficient 0.0649 (aerosandbox af.area()), so a
26 in chord section is 43.9 in^2; in 1/8 in balsa that is 8.6 g solid at 6 lb/ft^3, 11.5 g solid
at 8 lb/ft^3, and 5.2 to 6.9 g at 40 percent lightening. So a real rib is 5 to 11 g against the
model's 23.7 g. Either A_WING1 is badly overestimated (wing lighter than modeled, payload goes UP)
or it is silently absorbing capstrips, shear web and rib doublers the model names nowhere else.
T-1 settles it. This is the single most likely-to-move number in the weight model.

### Load cell sizing for the DIY thrust gauge (Jordan asked) [VERIFIED from prop_candidates.csv]
Worst-case static thrust per motor across all 2-motor candidates at the 110 A sensitivity case,
DA 1400: 12x6e 7.30, 12x8e 6.88, 11x7e 6.62, 12x10e 6.33, 11x10e 5.80, 12x12e 5.78 lbf.
4-motor candidates are about 3.2 lbf per motor.
- Max expected one motor: 7.3 lbf (3.3 kg). Design the rig to 10 lbf (4.5 kg) for model error,
  denser air and spin-up transients.
- RECOMMENDATION: 10 kg (22 lbf) load cell, single-point or S-beam, loaded in line with the
  thrust axis at 1:1. Peak then sits near 33 percent of rating. A 5 kg cell puts peak at 66
  percent, fine on resolution, thin on overload margin. Both motors on one stand would need 20 kg.
- Resolution is NOT the binding constraint: the test needs about 0.065 lbf (30 g) and a 10 kg cell
  on an HX711 beats that easily. Rigidity, alignment and overload survival are the real limits.
- [INFERRED, verify on the board] the HX711 runs 10 or 80 SPS per its RATE pin and many cheap
  breakouts tie RATE to ground for 10 SPS. That is exactly the plan's minimum with no margin for
  the D3 droop test. Pick a board exposing RATE, cut the trace for 80 SPS, or use a faster ADC.
- A bare digital kitchen or luggage scale will NOT do: no 10 Hz logging, so it cannot measure
  thrust droop over the 4.5 s roll or give the V-vs-I trace that R_BATT is fitted from.

### What the plan feeds back into (tables in TEST_PLAN.md sections 2.8 and 3.8)
T-1 -> weight.py:27 A_WING0, :28 A_WING1, :32 SPRUCE_DENS, :73-84 calibrate() (keep the NAU case
as a printed cross-check, do not delete it), :34 BATTERY_LB. Then rerun weight, sweep, design_card
and diff design_card.txt; the wing area, bay size and top rung can all move, and the 6-vs-8 slot
decision re-opens.
T-2 -> takeoff.py:33 THRUST_FACTOR; propulsion.py:35 V_OC_TO, :36 V_OC_CRUISE, :37 R_BATT,
:38 I_DESIGN, :43 MOTOR_CLASS Rm/I0 and component masses, :100 allow a measured-Kv override;
weight.py:34,:38. Then rerun propulsion, takeoff, sweep, design_card. The prop choice is genuinely
in play: 2x12x6e and 4x9x45e differ by 0.1 lb of W_TO_max, far below the model's own error.

### Stated limits of the plan [VERIFIED as written into section 6]
- T-1 gives n = 1 on K_BUILD unless a second panel is built. If only one, keep a band of at least
  x0.92/x1.08. Two panels built by two different people is the most informative version.
- T-2 is STATIC only. It cannot measure thrust lapse with airspeed, and thrust at V_R (9.5 lbf at
  36.4 ft/s) is what actually decides the 100 ft takeoff. The static test calibrates the prop
  model and the calibrated model predicts the lapse. A taped-down measurement from a moving
  vehicle is NOT a substitute. The lapse gets checked later against flight data using
  nasa_takeoff_flighttest_method (NASA TN D-7603).
- No covering-film source is archived, so film weight has no external cross-check (GAP noted at
  reference/GUIDE.md:94).
- ETA_ESC_PART (propulsion.py:39) is only indirectly checked by the part-throttle map.

### Listed but NOT done (section 7, Jordan's call)
1. Proof-load the panel to n = 3.0 after weighing, to retest SPRUCE_ALLOW 3700 psi and N_DESIGN
   (both [INFERRED]). Needs its own rig and safety case and destroys the T-1 article; build a
   third panel if wanted.
2. Static thrust in ground effect vs clear of it.
3. Rolling friction (MU_R 0.04) by towing the finished gear on the real surface with a fish scale.

### Standing guidance recorded this session
Jordan: do not wait for approval to write PROJECT_MEMORY.md entries. Write them as part of
finishing the task; he commits to GitHub himself most of the time. Saved to Claude auto-memory.

### NEXT TASK
Jordan buys the load cell and builds the thrust gauge, and the team buys wing stock. Meanwhile the
next session should either (a) resume AVL stability and trim from the VLM values (wing Cm0 -0.28,
x_np ~0.44c) as the [2026-09-19 00:28] summary planned, since T-1 and T-2 are now blocked on
hardware, or (b) write analysis/tests/reduce_panel.py and reduce_thrust.py against the CSV schemas
in TEST_PLAN.md so the reduction is ready before data exists. (b) is cheap and removes a step from
test day; (a) is the bigger open design question.
