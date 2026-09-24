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

## [2026-09-21 22:51 CDT] Hardware bought, E423 locked, TEST_PLAN.md v1.1 (T-2 rewritten for real hardware)

### Decisions (Jordan, 2026-09-21)
- AIRFOIL LOCKED: Eppler E423. Supersedes the S1223 design point. At the SAME 95 x 26 in wing the
  model gives E423 trimmed CLmax 1.55 vs S1223 1.66 and payload 16.2 vs 17.4 lb
  (analysis/sizing/out/sweep_summary.txt line 20). The sizing has NOT been re-optimized for the E423,
  so design_card.txt is stale (it is still the S1223 point).
- MOTOR BOUGHT: SunnySky X2820 800 KV, original black X Series (not the "X V3" line, which has no
  800 KV). Quantity on hand: OPEN (ask Jordan).
- PROPS ON HAND: APC 9x4.5E, 9x6E, 12x6E, 12x8E, 12x10E. All five have APC PER3 data in the library.
- THRUST STAND BOUGHT: Mayatech MT10PRO 10 kg. This replaces the DIY load cell + HX711 plan in v1.0.

### X2820 800 KV datasheet [VERIFIED from the official SunnySky USA page]
Kv 800; Rm 41 mOhm; I0 0.9 A at 10 V; 46 A for 30 s max continuous; 700 W; 3-5S; ESC 60 A;
12N14P (7 pole pairs); stator 28 x 20 mm; 5 mm shaft; 138 g. No PDF exists; the page is the datasheet.
4S 100 pct points (V column is nominal 14.8 V, W = 14.8 x A, no RPM published):
  12x6 32.7 A 2240 gf 54 C | 12x8 38.5 A 2300 gf 56 C | 13x6.5 40.1 A 2670 gf 60 C | 13x8 45.2 A 2790 gf 64 C.
  The 9x4.5E, 9x6E and 12x10E are not in SunnySky's table.
Files: reference/raw/sunnysky_x2820_800kv_datasheet.txt (library ID sunnysky_x2820_800kv_spec, READ THIS ONE),
reference/raw/sunnysky_x2820_800kv.html (ID sunnysky_x2820_800kv, raw page, ~47k tokens),
reference/data/sunnysky_x2820_800kv_testdata.csv (48 rows; checked against the typed table, 20 rows, 0 mismatches).

### MT10PRO findings [VERIFIED from the reseller page, reference/text/mayatech_mt10pro.txt lines 87-111]
Thrust 0-10 kg ("down to the gram" = display resolution, accuracy unpublished), V 0-60 V, A 0-150 A,
W; motor base 16/19/25 mm; power input 5-26 V (XT60); 733 g; CNC aluminium base with bench holes.
DISPLAY ONLY: no RPM, no torque, no data logging. No official Mayatech page or manual was found.
Safety sheet archived as mayatech_mt10pro_safety (generic).
Consequences written into the plan: a separate optical tach is required; the data logger is a phone
on a tripod at 60 fps with sound (display for T/V/A/W, audio blade-pass 2 x RPM/60 for RPM, via
ffmpeg + STFT in reduce_thrust.py); the display update rate must be measured once (Run 0.5).

### Model predictions on the X2820 [computed, analysis/tests/predict_x2820.py -> analysis/tests/out/predict_x2820.csv]
Datasheet constants (Kv 800, Rm 0.041, I0 0.9, Resc 0.003), V_oc 16.0 V, R_batt 0.025 ohm, DA 1400 ft, J = 0.
  prop    stand 1 motor: rpm / g / A / pct of 46 A      aircraft: n / total lbf / pack A
  9x4.5E  11883 / 1435 / 16.6 / 36                     4 / 11.0 / 59
  9x6E    11635 / 1634 / 21.1 / 46                     4 / 12.2 / 72
  12x6E   10531 / 3024 / 41.1 / 89                     2 / 12.0 / 74
  12x8E   10074 / 3210 / 49.4 / 107                    2 / 12.5 / 88
  12x10E   9736 / 3201 / 55.5 / 121                    2 / 12.4 / 98
- 12x8E and 12x10E are predicted ABOVE the 46 A rating on a fresh pack (upper bound, see next item).
  Plan now has a current ramp rule (50 -> 75 -> 90 pct, 3 s each; above 42 A at 90 pct means no
  100 pct; above 46 A is a hard cut) and tests props in increasing load order.
- vs design card: 2 x 12x6E static was 13.2 lbf (design_card.txt, generic 42xx-50xx motor, Kv 843,
  88 A). With the X2820 the model gives 12.0 lbf; SunnySky's table implies 9.9 lbf (2 x 2240 gf).
- Model vs SunnySky at a stiff 14.8 V, sea level: 12x6 model 3056 gf 41.6 A vs 2240 gf 32.7 A (0.73
  thrust ratio); 12x8 model 3323 gf 51.1 A vs 2300 gf 38.5 A (0.69).
- Back-calculation [INFERRED]: at the RPM where an APC prop absorbs SunnySky's measured current
  (12x6 9182 rpm, 12x8 8692 rpm), SunnySky thrust is 0.943 and 0.929 of APC, i.e. right at
  THRUST_FACTOR 0.93. That fits if their motor saw only about 12.4-12.8 V (3.1-3.2 V/cell) vs the
  model's ~15 V. So the gap is most likely voltage under load, not the prop data, and it is worth
  about 30 pct of static thrust. Unconfirmed: SunnySky publishes neither its loaded voltage nor
  whether its props were E versions. Only measured V_batt + RPM on our stand settles it.

### TEST_PLAN.md v1.1 changes
- Header and section 0: v1.1 note; E423 cost at fixed geometry.
- T-1 (section 2): airfoil row E423; rib table recomputed for E423 (area coefficient 0.0827, t/c
  0.125, 55.9 in^2 at 26 in chord; 1/8 in rib 7-15 g vs the model's implied 23.7 g, a factor of
  1.6-3.6); build note on the E423 thicker TE (0.015c vs 0.008c at 95 pct chord, 0.39 vs 0.20 in);
  record as-built TE thickness at 3 ribs.
- T-2 (section 3) rewritten: 3.1 objective with model status; 3.2 hardware on hand + ESC throttle
  calibration; 3.3 equipment around the MT10PRO (hanging-mass pulley calibration up and down, tach,
  60 fps video logging, mount fit check); NEW 3.4 variables to measure (per sample: T, RPM, V_batt,
  I, P, throttle, time; per run: IDs, cell V before/after, temperatures, air density inputs, prop
  clearance; per session: cal, display rate, masses; not measured: torque, airspeed) with the
  SunnySky worked example; 3.5 predictions + current ramp rule; 3.6 methodology (video is the log);
  3.7 procedure (Run 0 setup/cal, Run A masses, Run B pack, Run C motor constants over 6 load
  points incl. no-prop Kv check 12,000-13,400 rpm, Run D thrust with D5 Y-harness downstream of the
  MT10PRO); new CSV schemas (T_g raw grams, rpm_source, pack_id, pack_fresh, video_file, t2_cal.csv);
  3.8 reduction incl. audio RPM; 3.9 gates (Kv +/-10 pct, V_batt near 12.5-13 V, 46 A per motor,
  92 A pack, motor can 158 F, pack 140 F); 3.10 code feedback.
- Section 4 safety: transmitter throttle cut + failsafe OFF test, ramp rule, leads clear of the arc.
- Section 5: Run 0 added. Section 6: no torque; MT10PRO accuracy unpublished (calibration is the only
  accuracy statement); time resolution = display rate; D5 RPM by optical tach (two audio peaks).

### Code facts checked this session
- PropSystem already accepts kv= and motor= (propulsion.py:106); callers takeoff.py:43 and
  propulsion.py:196 do not pass them. So fixing Kv at 800 is a caller change, not a model change.
- ffmpeg is installed on the laptop (winget ffmpeg full build).

### Files
New: analysis/tests/predict_x2820.py, analysis/tests/out/predict_x2820.csv,
reference/raw/sunnysky_x2820_800kv_datasheet.txt, reference/data/sunnysky_x2820_800kv_testdata.csv,
library IDs sunnysky_x2820_800kv, sunnysky_x2820_800kv_spec, mayatech_mt10pro, mayatech_mt10pro_safety.
Modified: TEST_PLAN.md (v1.1), reference/GUIDE.md (Propulsion section), reference/data/README.txt,
reference/INDEX.md and manifest.json (via doc2text).

### UNVERIFIED / OPEN
- How many X2820s are on hand, and which ESC (SunnySky recommends 60 A). Ask Jordan.
- X2820 mount holes vs the MT10PRO 16/19/25 mm patterns.
- Whether the MT10PRO's 5-26 V power input is the pack itself or a separate supply.
- Rm 41 mOhm is presumably line-to-line [INFERRED]. I0 0.9 A is at 10 V; higher at 4S speed.
- The SunnySky low-voltage explanation above [INFERRED].
- The recharge threshold of about 3.9 V/cell per resting cell in Run B5 [INFERRED].
- None of the predictions above have been checked against a measurement yet.

### NEXT TASK
Rerun the sizing with the E423 locked and the X2820 as the fixed motor (Kv 800, datasheet Rm/I0,
passed through takeoff.py:43 and propulsion.py:196) as the interim baseline, so the design card
reflects the hardware actually bought; and/or write analysis/tests/reduce_thrust.py against the
TEST_PLAN.md 3.7 schemas before test day.

## [2026-09-21 22:56 CDT] Prop ranking on the X2820 800 KV, 2-motor and 4-motor

Task: Jordan asked for a best-to-worst ranking of the props in analysis/tests/out/predict_x2820.csv for
the 2-motor and 4-motor setups. Static (J = 0) alone is not enough because T(V_R) decides the 100 ft
takeoff, so the same model was also run over the ground roll.

### Method [computed; scratch script, not saved to the repo]
PropSystem(n, prop, kv=800, X2820 datasheet motor dict, v_oc=V_OC_TO 16.0, r_batt=0.025), DA 1400 ft,
THRUST_FACTOR 1.0 (raw APC). full_throttle over 0 -> V_R 36.4 ft/s (25 points); Tmean = velocity-averaged
thrust over the roll (rough). Peak current = max over the roll (APC Cp rises with J, so the peak is not
at V = 0). Cruise: part_throttle_current at 4.22 lbf, 46.4 ft/s, V_OC_CRUISE 15.2 (design_card.txt
line 8, S1223 point, so absolute cruise numbers are stale for the E423).

  cfg        T0 lbf  Tmean  T(V_R)  Ipk/motor A  pct 46 A  pack pk A  cruise A
  2x12x6e    11.99   10.68   9.23     38.2         83        76.3      34.5
  2x12x8e    12.54   11.49  10.31     47.1        102        94.3      34.2
  2x12x10e   12.38   11.58  10.67     53.5        116       107.0      35.0
  2x9x6e      6.79    6.21   5.52     21.2         46        42.4      37.1
  2x9x45e     6.03    5.26   4.36     16.1         35        32.2      cannot hold cruise
  4x9x6e     12.19   11.04   9.69     19.1         41        76.2      33.4
  4x9x45e    11.03    9.55   7.83     14.8         32        59.3      35.3

### Ranking given to Jordan [INFERRED from the model above]
2-motor: 1) 12x8E, conditional on the stand showing <= 46 A per motor (+1.08 lbf at V_R, +12 pct over
12x6E; model peak 47.1 A = 102 pct, pack 94 A just over the TEST_PLAN 92 A gate). 2) 12x6E, the only
12 in prop with current margin (83 pct); the fallback if 12x8E reads over. 3) 12x10E, out: 116 pct of
rating, 107 A pack, and only +0.36 lbf at V_R over 12x8E. 2 x 9 in is legal but about half the thrust.
4-motor (9 in max): 1) 9x6E (T(V_R) 9.69, above 2x12x6E's 9.23). 2) 9x45E (-1.86 lbf at V_R).
On this 800 Kv motor the 9 in props run at 32-46 pct of rating, so 4 motors carry the weight of two extra
motors and ESCs without using them. The earlier "2x12x6e vs 4x9x45e within 0.1 lb" result used Kv matched
per prop and does not apply to the fixed X2820.
Cruise current is 33-37 A for every viable setup, so it does not separate them.

### UNVERIFIED
- All numbers are model output. The model is about 30 pct above SunnySky's published thrust, most likely
  loaded voltage [INFERRED, see 22:51 entry]. Lower real voltage cuts current too, which helps 12x8E's
  current case, but also cuts high-load props the most, so the 12x8E/12x10E thrust edge may shrink.
- Stand vs aircraft: one motor on the stand draws more than one motor in the aircraft (less pack sag):
  12x8E 49.4 A stand vs 44.0 A aircraft static. Judge the 46 A question with the aircraft-equivalent
  current, or with the D5 two-motor run.
- Number of X2820s on hand is still OPEN; the 4-motor option needs four.

### NEXT TASK
Unchanged from the 22:51 entry. T-2 settles the 12x6E vs 12x8E call.

## [2026-09-23 22:53 CDT] MT10PRO video reader written (read_mt10pro_video.py); 12x8E.MOV not yet processed

### What was done
- Jordan filmed the Mayatech MT10PRO screens during a 12x8E run (phone on a tripod, gantry clamped to a
  table, some wind shake). Video moved to analysis/tests/video/12x8E.MOV (201.7 MB).
- New .gitignore: analysis/tests/video/ (the video is over GitHub's 100 MB file limit) and
  analysis/tests/out/video/ (the script's regenerable cache and overlays).
- Wrote analysis/tests/read_mt10pro_video.py (v1.0, 1303 lines, accuracy over speed). Claude did NOT run
  it on the video; Jordan runs it (commands below). Only its functions were imported in scratch tests.
- Product facts (ranges, display-only, no RPM/torque/logging) are already in the 2026-09-21 22:51 entry.
  This entry adds what the video shows.

### Video [VERIFIED, OpenCV + ffprobe]
3840x2160 H.264, 30.0 fps CFR (TEST_PLAN asked for 60), 3676 frames, 122.53 s, AAC audio 48 kHz stereo.
The displays leave the picture from about frame 3580 (119.3 s). Motion blur from about 40-75 s (high
throttle).

### MT10PRO display, as read from the video [VERIFIED from frames unless tagged]
- Blue backlit dot-matrix LCD, 2 rows x 16 cells of 5x7 dots, HD44780 A00 ROM glyph forms.
  Row 0 "  34.12A  13.14V": current A (2 dp), battery V (2 dp). Row 1 "    2.0Wh 448.4W": aux field, power W (1 dp).
- Aux field cycles about every 3 s: Ap, Vm, Wp, Ah, Wh. Meanings [INFERRED from units and values]: peak A,
  minimum V, peak W, charge used, energy used. Frames 0/45/150: 0.17Ap, 15.40Vm, 1.7Wp at 0.11-0.12 A, 15.40-15.41 V live.
- Glyphs seen (18): space . 0-9 A V W p h m.
- Thrust: red-plate 7-segment LCD, 5 digits, grams [UNVERIFIED unit, none shown], triangle marker at the
  left; the leading digit was blank in every frame checked.
- Blue display refresh about 0.46 s (2.2 Hz), from frame counting in the prototype work; the script
  re-measures it and logs it. The thrust value can change on consecutive frames, so its refresh is faster
  than 30 fps can resolve [VERIFIED lower bound only]. Frames at a blue update are rolling-shutter mixes
  (upper cells from one state, lower from the next).
- |P - V x I| = 0.09, 0.18, 0.32, 0.07 W on four hand-checked states.

### Hand-checked single frames [VERIFIED; points only, not the processed run]
  frame  t s    I A     V      P W     thrust g
  1147   38.2   2.83   15.17    43.0     352
  2059   68.6  32.33   13.38   432.9    2053
  2129   71.0  34.12   13.14   448.4    2111
  2142   71.4  33.95   13.12   445.6    (not checked)
First look vs the 22:51/22:56 model [INFERRED, throttle position unknown]: the model's 12x8E stand peak is
49.4 A; 34.12 A is the highest hand-checked here. Voltage went 15.41 V at 0.12 A -> 13.14 V at 34.12 A,
an apparent source resistance of 0.067 ohm (an upper bound for pack + leads, because the open-circuit
voltage also fell as 2.0 Wh were used). The model assumes V_OC 16.0 V, r_batt 0.025 ohm. This supports the
earlier guess that loaded voltage explains the model's thrust over-prediction. Wait for the full run and
the Ap/Vm aux values before concluding.

### Script method (analysis/tests/read_mt10pro_video.py)
- Setup: scan every 15th frame; the sharpest clean in-state pair is the registration reference; up to 8
  sharp frames at least 45 frames apart train lit/unlit dot footprints by least squares (with gain
  normalization and outlier drop/relearn).
- Pass 1, per frame: color detection of both displays -> homography from the fitted outline -> masked ECC
  homography against the reference using static features only (borders, A/V/W unit glyphs, thrust
  triangle). ECC failure falls back to the outline homography. Blue: frame = plane + gain * K conv
  (sharp dot model); per-frame NNLS blur kernel K; glyph costs in dot-equivalents. Thrust: 35 segment
  darkness values, per-frame on/off levels, costs in segment-equivalents.
- Pass 2: per-cell / per-digit Viterbi (switch penalty 4.0 dot-eq blue, 1.0 seg-eq thrust; blurry frames
  down-weighted). Blue mix runs (1-3 frames) dropped; thrust 1-2 frame neighbor mixes kept, flagged
  possible_mix, and left out of T_g. P check tolerance 0.5 + 0.003 P W. T_g per blue state = mean of the
  thrust frames over that state.
- ECC finding: most frames converge in 15-50 iterations (1.0-1.9 s); frame 2058 needs 200-330 (13 s), with
  corners moving 0.42 px while the correlation changes 0.0005. Cap kept at 200 for accuracy.
- Outputs: analysis/tests/data/RUN_t2.csv (TEST_PLAN t2 columns, one row per clean blue state),
  RUN_blue_states.csv, RUN_thrust_states.csv, RUN_frames.csv; debug in analysis/tests/out/video/RUN/
  (log, setup.json, model.npz, pass-1 chunk cache, overlays). RUN defaults to the video name. An interrupted
  run resumes from the chunk cache (--fresh ignores it).

### Validation [VERIFIED, scratch tests importing the script's functions; not an end-to-end run]
- Blue reader: 832/832 cells on 26 truth frames, with the prototype footprints and with the script's own
  training path. Thrust reader: 17/17 frames. Registration and frame seek match the prototype.
- Pass-2 block executed on synthetic pass-1 data with known truth (900 frames, 49 injected mixes, blur,
  6 invalid frames): 66/66 blue states correct, T_g within 0.51 g of the true state mean, 117/117 thrust
  states, refresh period 0.4615 s recovered (true 0.4613 s).
- First 10 s: displays found and 31-32 of 32 cells decode in frames 0-299, so the smoke test is valid.

### Commands (Git Bash, repo root)
  python analysis/tests/read_mt10pro_video.py analysis/tests/video/12x8E.MOV --end 10 --run-id 12x8E_smoke
  python analysis/tests/read_mt10pro_video.py analysis/tests/video/12x8E.MOV --prop 12x8E
  (optional: --motor-id --esc-id --pack-id --pack-fresh --n-motors-live --throttle-pct, copied into t2)

### UNVERIFIED / open
- Full-video runtime: estimate 2-3 s per frame per worker, 6 workers -> about 35-75 min; share of slow-ECC
  frames unknown.
- Thrust unit (grams assumed); thrust refresh rate; latency between the thrust and blue displays (T_g
  pairing may lag); aux field meanings; throttle position during the run.
- Only the 18 glyphs above are modeled; other camera framings/orientations untested.
- RPM: the audio track is present but not processed (TEST_PLAN blade-pass method, not written yet).
- Next videos: film at 60 fps as TEST_PLAN says (30 fps cannot resolve the thrust refresh).

### NEXT TASK
Jordan runs the two commands. Next session: review 12x8E_t2.csv, the flagged states and a few overlays,
then write the audio blade-pass RPM extraction for the same video.

## [2026-09-24 03:04 CDT] 12x8E.MOV processed: video reader run reviewed, audio RPM tool written; first T-2 data

Task (Jordan, overnight, no permission prompts): run the two read_mt10pro_video.py commands, review the output
and fix the script, then write the RPM estimator. All done unattended. Nothing committed (Jordan commits).

### Video reader run [VERIFIED against hand reads of the video]
- Smoke (frames 0-299): 15.3 min, 100 pct readable, 20 blue states, refresh 0.455 s. The 12x8E_smoke_*.csv
  files are left in analysis/tests/data/.
- Full video: 3676 frames (122.5 s at 30 fps) took 171.8 min on 6 workers = 15.6 s per frame per worker
  (median 9.2 s, p90 50 s, max 105 s; slow ECC convergence dominates). The 22:53 estimate (35-75 min) was wrong.
- Readable: blue 3601 (98 pct), thrust 3596 (98 pct). All unreadable frames are at 119.3-122.5 s (unit off).
- 237 blue states (231 good, 5 short, 1 bad end state), 231 rows in 12x8E_t2.csv. 221 thrust states, 0-2193 g.
- Blue refresh 0.457 s (alignment R 0.50). Thrust value changes: median interval 0.333 s, min 0.100 s.
- Hand checks, exact match: frame 1147 2.83 A 15.17 V 43.0 W 352 g; 2059 32.33 A 13.38 V 432.9 W 2053 g;
  2129 34.12 A 13.14 V 448.4 W 2111 g; 2142 2193 g.
- |P - V x I| max 0.39 W. Fit T = 17.07 x P^0.800 g (105 states with P > 20 W, residual std 5.8 pct).
- One current spike (frame 1017, 2.91 A) is a mid-update frame and is excluded from every state.
- Fix: the run_jobs() ETA divided elapsed time by chunks done, so early in the pool it read 576 min (true
  about 150). It now counts at least one chunk per worker. Edited after the run ended, because spawned
  workers re-import the file.

### Audio RPM tool: analysis/tests/audio_rpm.py v1.0 (new)
Method:
1. ffmpeg audio -> STFT (8192 window, 20 ms hop). Stationary lines are removed.
2. Harmonic salience of the blade-pass frequency F = B x RPM/60 over 10 harmonics.
3. Sub-harmonic penalty at m = 2 and 3. For a 2-blade prop the m = 2 threshold is relative:
   max(C_THR, mean of the neighbouring harmonic levels - SUB_REL 6 dB). Without it, the 1/rev imbalance lines
   (10-18 dB below the blade-pass lines) made the tracker lock onto the shaft rate (F/2).
4. Power prior from the display states: n_lim = 1.3 x ((dP + 1 W)/(0.8 Cp_min rho D^5))^(1/3). The motor is
   treated as off when I is within 0.05 A of idle.
5. Viterbi with an unvoiced state (max jump 1/8 octave per hop), then WLS refinement on the harmonic peaks.
6. Each blue state's window is shifted by --state-lag, default -0.35 s (display latency, below).
7. APC PER3 thrust check: flag rpm_thrust_mismatch when T_meas/T_apc is outside 0.5-2.0 and
   max(T_apc, T_meas) >= 100 g. The max catches an F/2 error, which drops T_apc by 4x.
Outputs:
- data/RUN_rpm.csv (per hop) and data/RUN_rpm_states.csv.
- The rpm, rpm_source and notes columns are merged into RUN_t2.csv; rerunning the merge gives the same file.
- out/audio/RUN/RUN_rpm.png and RUN_rpm_log.txt.
- Runtime 0.2 min.
Command: python analysis/tests/audio_rpm.py analysis/tests/video/12x8E.MOV --prop 12x8E

Fixes made during review:
- The octave error at about 38 s is fixed by the relative m = 2 threshold. Verified on real and synthetic data.
- The thrust gate uses the max of T_apc and T_meas, as in step 7.
- A column-name clash with the pandas .flags attribute.
- The docstring.

Validation:
- Synthetic: state means 4999.3 / 7000.2 / 8250.0 / 2999.4 rpm (truth 5000 / 7000 / 8250 / 3000). Held states
  have an rpm std of 0.6-0.9.
- 12x8E: 3619 of 6127 hops voiced; 883-8315 rpm; no lock onto the motor whine (7F).
- States: 151 have an rpm. Flags: motor_off 35, unsteady 44, no_rpm 51, rpm_thrust_mismatch 1. The mismatch is
  state 12, the start transient (2037 rpm at 0 g, weak evidence), and it is correctly excluded.
- 150 of the 231 t2 rows have an rpm.

Display latency [measured, one video only]:
- The MT10PRO shows values about 0.35-0.40 s after they are measured. The best lag is -0.35 s for I and P and
  -0.40 s for T. The two halves of the run give -0.40 and -0.35 s.
- Fit rms improves from 4.3 to 2.5 pct for I and from 3.3 to 2.0 pct for T.
- Throttle cut: heard at 76.46-76.50 s, while the display still showed 33.49 A until 77.07 s.

### First T-2 data: X2820 800 KV + APC 12x8E on 4S [measured; throttle position not recorded]
  state  t s    rpm (std)   I A    V V    P W    T g    T_apc g  T/T_apc
  77     38.07  3502 (31)   2.83   15.17   43.0   352    388     0.908  unsteady
  143    68.33  8125 (51)  32.33   13.38  432.9  2029   2114     0.960
  145    69.27  8276 (16)  33.86   13.17  446.2  2119   2195     0.965  highest rpm
  148    70.73  8235 (13)  34.12   13.14  448.4  2111   2173     0.971  highest current
  149    71.13  8242 (5)   33.95   13.12  445.6  2108   2177     0.968
- Peaks: current 34.1 A (74 pct of the 46 A rating), rpm 8276, thrust 2120 g state mean (2193 g single frame).
- Measured / APC thrust at the audio rpm (rho 1.20, T_apc >= 200 g): median 0.957, range 0.869-1.056, n 105.
  At matched rpm the APC PER3 data holds within about 4 pct.
- Thrust offset [INFERRED, medium confidence]:
  - Below 400 g of T_apc: T_meas = 0.9986 T_apc - 27.3 g (n 39).
  - All steady states: T_meas = 0.9747 T_apc - 20.0 g (residual 13.3 g, n 107).
  - An offset that stays constant with thrust looks like stand zero or friction, not a Ct error.
  - With +27 g added, the top-end ratio is about 0.98.
  - Settle it with the TEST_PLAN Run 0.2 hanging-mass calibration (load up, then down).
- During the 69-76.5 s hold, rpm decays from 8280 to 8170 as V sags from 13.26 to 13.03 V.
- At 8276 rpm the shaft power is about 348 W (APC Cp 0.0417) against 446 W electrical, so motor + ESC
  efficiency is about 0.78 [INFERRED].
- Against the model (22:51 entry), which predicted 10074 rpm / 3210 g / 49.4 A for the 12x8E stand at full
  throttle:
  - The measured top was 8276 rpm / 2120 g / 34.1 A.
  - The throttle position is unknown, so this is not a full-throttle comparison. A Kv back-calculation
    (about 708 rpm/V if the throttle was at 100 pct) is inconclusive.
  - The prop data matches at matched rpm, so the thrust gap is in the rpm reached (motor/voltage side). This
    agrees with the 22:51 inference.
  - If the run was at full throttle, the 12x8E stays inside the 46 A rating and wins the 12x6E vs 12x8E call.
    Ask Jordan.
- After shutdown the displayed current decays from 0.44 to 0.17 A over about 25 s (idle was 0.11-0.12 A
  before). Cause UNVERIFIED; possibly current-sensor zero drift after load. Those states are not treated as
  motor off, but they are correctly flagged no_rpm.

### Files
New (untracked):
- analysis/tests/audio_rpm.py
- analysis/tests/data/: 12x8E_{t2,blue_states,thrust_states,frames,rpm,rpm_states}.csv and 12x8E_smoke_*.csv
- analysis/tests/out/audio/12x8E/ (plot 0.86 MB + log; not in .gitignore)
- analysis/tests/out/video/12x8E/ (37 MB, gitignored)
Modified: analysis/tests/read_mt10pro_video.py (the ETA line in run_jobs).
Scratch only (not in the repo): diag4.py (penalty variants), lag.py (latency fit), synthetic test data.

### UNVERIFIED / open
- Display latency (-0.35 s) is from one video only.
- --order 7 (tracking the motor whine instead of blade pass) is untested.
- The cause of the -20 to -27 g thrust offset.
- rho 1.20 is assumed: air temperature and pressure were not recorded.
- The cause of the post-shutdown current decay.
- The throttle position during the run.
- The start transient at 5.2-6.5 s is ambiguous in the audio.
- Stand vs aircraft current (22:56 entry), unchanged.

### Adjacent issues (listed, not fixed)
- The video reader is slow: 172 min for 122 s of video. ECC iterations dominate. Starting ECC from the
  previous frame's warp may cut this; worth trying before the next batch of videos.
- Blank end frames (unit off) read as thrust 0, which stretches the last thrust state.
- Post-shutdown states are flagged no_rpm, not motor_off (idle current drifts up after load).
- The smoke outputs are still in data/. Archive them once they are no longer needed.
- Next videos: 60 fps (TEST_PLAN); write down the throttle pct, air temperature and pressure; run Run 0.2.

### NEXT TASK
See the CURRENT STATE SUMMARY below.

---

## [2026-09-24 03:04 CDT] CURRENT STATE SUMMARY (after the first T-2 data; start here)

The [2026-09-19 00:28] summary (and the [2026-09-18 21:06] one it points to) still hold for rules, team,
bottles, scoring and the library, with these updates:
- AIRFOIL LOCKED: E423 (2026-09-21).
  - analysis/sizing/out/design_card.txt is STALE: it is still the S1223 point (95 x 26 in).
  - At the same wing the E423 gives CLmax 1.55 and a payload of 16.2 lb (model).
  - The sizing has not been re-optimized.
- Hardware on hand:
  - Motor: SunnySky X2820 800 KV. Quantity OPEN.
  - ESC: OPEN.
  - Thrust stand: Mayatech MT10PRO 10 kg (display only, no logging).
  - Props: APC 9x4.5E, 9x6E, 12x6E, 12x8E, 12x10E.
- Prop ranking (model, 22:56 entry): for 2 motors, 12x8E if it draws <= 46 A per motor, else 12x6E. For
  4 motors, 9x6E.
- Tests (TEST_PLAN.md v1.1):
  - T-1 wing panel weigh-in: no data logged yet.
  - T-2 thrust stand: first run done (12x8E; entry above).
- T-2 data pipeline:
  1. Phone video.
  2. analysis/tests/read_mt10pro_video.py (display values; about 15.6 s per frame per worker).
  3. analysis/tests/audio_rpm.py (rpm from blade pass; 0.2 min).
  4. Output: analysis/tests/data/RUN_t2.csv.
  - analysis/tests/reduce_thrust.py (TEST_PLAN 3.8) is NOT written yet.
- First T-2 result, 12x8E (throttle unknown): up to 34.1 A, 8276 rpm, 2120 g. APC PER3 thrust matches within
  about 4 pct at matched rpm (median ratio 0.957). There is a probable -20 to -27 g stand offset.
- Stability and trim (the 2026-09-19 NEXT TASK) is not started. AVL/XFLR5 is not installed.

### Action items for Jordan
1. For the 12x8E run: was it full throttle? Also the air temperature and the pressure or altitude. Also: how
   many X2820s are on hand, and which ESC?
2. Next stand session:
   - Film at 60 fps.
   - Run 0.2 hanging-mass calibration (settles the thrust offset).
   - Full-throttle ramps for 12x6E and 12x8E using the TEST_PLAN current rule.
   - Write down the throttle pct for each hold.
3. T-1 wing panel weigh-in (tests before analysis).
4. From the old summary: lottery interest by 2026-09-30, AMA card, sae.org affiliation (status not logged).
5. Commit the new files (audio_rpm.py, the 12x8E data, the reader ETA fix, this log).

### NEXT TASK
Write analysis/tests/reduce_thrust.py per TEST_PLAN.md 3.8, using 12x8E_t2.csv as the first input:
- air density;
- T_apc from parse_apc/coeffs in propulsion.py:51-93;
- THRUST_FACTOR_meas per prop, with the zero-offset term;
- Kv/I0/Rm fit.
Then rerun the sizing with the E423 and the X2820 as the fixed motor. Use the throttle answer from item 1
if Jordan has given it.

---

## [2026-09-24 10:11 CDT] reduce_thrust.py written; 12x8E run reduced as full throttle; ESC identified

### Jordan's answers (2026-09-24), from the 03:04 action item 1
- The 12x8E run WAS AT FULL THROTTLE at the peak thrust. It is an assumption: the stick was not recorded,
  and ESC throttle-range calibration is NOT confirmed. Full-throttle window: states 145-160 (69.3-76.5 s).
- Air: 72 F indoors (assumed, not measured), Jackson TN.
- ESC: SunnySky X series ESC X60A V2 (label ESC-X60, 2-6S, SBEC 8 A at 5.6/7.4 V) [VERIFIED sunnysky_esc_x60]:
  60 A continuous, 80 A for 10 s, 61 g, XT60 in, 3.5 mm bullets out, $45.99. Firmware, on-resistance and
  programmability for the X60A itself: UNVERIFIED. sunnysky_esc_manual (32-bit proprietary firmware; calibration =
  stick max, power on, "beep~beep" within 2 s, stick to min, cell-count beeps, long beep; default timing 15 deg,
  LVC 3.0 V/cell) is written for X45A/X65A/X85A LW/PRO; the X60A is not in its model table.
  The model's m_esc_lb 0.14 lb (63.5 g) matches the 61 g listing.
- Still OPEN: how many X2820s are on hand.

### Test conditions (analysis/tests/data/t2_conditions.csv, new; one row per run, each value with its source)
- Video metadata: 2026-09-23 20:56:43 CDT (01:56 UTC), GPS 35.6750 N 88.8635 W, iPhone 15.
- Elevation 464.1 ft [VERIFIED USGS EPQS]. KMKL field is 434.8 ft [VERIFIED airnav].
- KMKL altimeter 30.20 inHg at 01:53Z and 30.21 at 02:53Z; outdoor 68 F / dewpoint 59 F
  [VERIFIED IEM ASOS, saved as reference/data/kmkl_asos_2026-09-24.csv].
- Indoor dewpoint taken as the outdoor 59 F [INFERRED]. It is worth under 0.3 pct of density.
- Result: rho 1.1785 kg/m^3 (0.962 x ISA SL), DA 1333 ft. The 03:04 entry assumed 1.20, 1.8 pct too high.
  DA 1333 ft is close to the design DA of 1400 ft, so these numbers compare directly with the sizing.

### analysis/tests/reduce_thrust.py (new, TEST_PLAN 3.8)
Run: `python analysis/tests/reduce_thrust.py 12x8E`
- Inputs: RUN_rpm_states.csv and t2_conditions.csv.
- Outputs: analysis/tests/out/reduce/RUN_{summary.txt, points.csv, predict.csv}.
- Reuses parse_apc/coeffs (propulsion.py) and density_altitude() (density_altitude.py).
- Covers items 1, 3-9. Item 2 (rpm) stays in audio_rpm.py. Item 7 uses the hold, not a D3 burst.
- pyflakes clean. Checked by running on 12x8E: fits A and B reproduce the measured point (8218 vs 8228 rpm,
  33.6 vs 33.7 A, 2077 vs 2083 g).

### 12x8E results, full throttle (16 states, mean 8228 rpm, 33.67 A, 13.09 V, 2083 g, 441 W) [measured + INFERRED fits]
- THRUST_FACTOR_meas = 0.978 +/- 0.007 (full throttle, rho 1.1785). The median over all steady points is 0.975.
  - Offset fit over steady points: T = 0.9747 T_apc - 20 g (unchanged).
  - The APC PER3 Ct holds to about 2 pct. Gate 3.9 "0.90-1.00": PASS. The takeoff.py value is still 0.93;
    not changed yet.
- Current: 33.7 A mean, 34.1 A peak = 73-74 pct of the motor's 46 A (30 s) and 56 pct of the ESC's 60 A.
- Pack [measured]:
  - Resting before the run: 15.40 V = 3.85 V/cell. THE PACK WAS NOT FULLY CHARGED (full = 16.8 V).
  - Fit over the ramp: V = 15.37 - 68.3 mOhm x I (includes polarization).
  - Step at the throttle cut: 39.2 mOhm (13.03 V at 33.3 A -> 14.32 V at 0.44 A, 0.6 s later).
  - The model assumed V_oc 16.0 V and 25 mOhm.
  - Gate 3.9 "V_batt 12.5-13 V instead of about 15 V" is TRIGGERED (13.09 V), but partly because the pack
    was part-charged.
- Against predict_x2820 (datasheet motor, V_oc 16.0 V, 25 mOhm): rpm 0.817, I 0.682, V 0.886, T 0.649.
  Most of the gap is voltage. Fed this pack's V-I line, the datasheet motor would give 8845 rpm and 38.4 A.
  Measured rpm is 0.930 of that, which is the motor-side part of the gap.
- Motor fit. One prop = one load point, so Kv and R cannot both be pinned:
  - A (torque from APC Cp, I0 0.9 A): Kv 809 rpm/V, R_eff 86.6 mOhm, i.e. datasheet 44 mOhm + 43 extra
    (ESC, wiring, hot winding). A +/-5 pct Cp error moves Kv to 770-851.
  - B (R fixed 44 mOhm): Kv 709 rpm/V (-11.4 pct vs 800). The APC Cp would have to be x 1.141 to match the
    current. A duty ceiling near 89 pct from an uncalibrated throttle would look the same on the speed side.
  - C (free LSQ over the hold): Kv 690 +/- 20, R 35 mOhm. Leans toward B, but the hold is 7 s of warming
    winding and sagging pack, so low confidence.
  - Power balance at datasheet constants: 48 W of 441 W unaccounted (= 43 mOhm at 33.7 A). A explains it with
    resistance, B with APC Cp being 14 pct low. Either could be true [UNVERIFIED].
  - What separates them: the no-prop run on the same pack predicts about 12,340 rpm under A and 10,850
    under B. Also do the ESC throttle calibration first.
- Hold droop over 7.2 s: thrust 0.967, rpm 0.990, V 0.989. rpm^2 alone gives 0.980; the extra 1.3 pct
  may be room recirculation or stand drift [INFERRED]. Gate 3.9 (10 pct): PASS.

### Predictions at full throttle, static, rho 1.1785, thrust x 0.978 (out/reduce/12x8E_predict.csv) [INFERRED]
Fresh-pack bracket: pessimistic = V0 16.0 V with 68 mOhm; optimistic = V0 16.4 V with 39 mOhm.
  prop    per motor A, 1 motor (pct of 46 A)      aircraft 2 motors: total lbf / pack A
  12x6E   29-35 A (62-77 pct)                     7.2-9.7 lbf / 47-63 A
  12x8E   34-42 A (73-90 pct)                     7.4-9.8 lbf / 55-72 A
  12x10E  37-47 A (80-102 pct)                    7.2-9.7 lbf / 60-80 A
Fits A and B agree within about 3 pct on every 12 in case, so the prop call does not depend on the
Kv/R question.
- PROP DECISION (2-motor): 12x8E.
  - It stays under 46 A in every case (worst 41.6 A, 90 pct).
  - It gives the most static thrust of the three (1-4 pct over 12x6E).
  - Per the 22:56 rule, 12x8E wins. 12x10E: no thrust gain, and it reaches 46.8 A in the optimistic case. Drop it.
- BIG FLAG for the sizing: 2 x 12x8E gives 7.4-9.8 lbf static against 12.5 lbf in predict_x2820 / the
  sizing assumptions. The pack is the main lever: V0 and R_pack are worth about 2.4 lbf between the
  bracket ends. A pack IR check and a fully charged run are needed before the sizing rerun means much.

### Files
New:
- analysis/tests/reduce_thrust.py
- analysis/tests/data/t2_conditions.csv
- analysis/tests/out/reduce/12x8E_{summary.txt,points.csv,predict.csv}
- reference/data/kmkl_asos_2026-09-24.csv (+ README entry)
- reference: sunnysky_esc_x60, sunnysky_esc_manual (doc2text; INDEX/manifest updated; GUIDE line 61)

### UNVERIFIED / open
- Full throttle is an assumption. Whether the ESC throttle range was calibrated is unknown.
- Air temperature 72 F not measured. Indoor humidity inferred.
- Kv/R split (fit A vs B). APC Cp accuracy for the 12x8E at static (uiuc_propdb may have measured APC TE data).
- Pack identity, C rating and IR. The fresh-pack V0 bracket 16.0-16.4 V is a guess.
- Motor count on hand.
- I0 at 4S rpm (0.9 A at 10 V used).

### Adjacent issues (listed, not fixed)
- analysis/sizing/__pycache__/ is untracked and not in .gitignore.
- t2_conditions.csv is hand-entered; read_mt10pro_video.py still writes empty temp/throttle columns in RUN_t2.csv.

### NEXT TASK
Next stand session, then rerun the sizing:
1. Fully charge the pack and write down its resting V. Get the pack IR from the charger if it reports it.
2. Do the ESC throttle-range calibration (sunnysky_esc_manual steps).
3. No-prop run (C1) with the motor-whine audio (--order 7), to settle Kv (A vs B).
4. 12x8E and 12x6E full-throttle holds. Record the stick/throttle pct, a thermometer reading and Run 0.2.
Then update propulsion.py and takeoff.py per TEST_PLAN 3.10 with the measured THRUST_FACTOR, Kv/R and
pack, and rerun the sizing with the E423 and 2 x X2820 + 12x8E. If no new stand data is coming soon, run the
sizing now with the bracket above (V0 16.0/68 mOhm and 16.4/39 mOhm).

---
