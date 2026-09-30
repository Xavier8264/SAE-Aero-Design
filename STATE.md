# STATE -- hot cache (overwritten at every checkpoint; 500 words max)

Derived from PROJECT_MEMORY.md. If they disagree, the log's latest entry wins: fix this file.
[YYYY-MM-DD HH:MM] = a log entry header; grep "## \[2026-09-30 06:59" PROJECT_MEMORY.md, read that range.
Full decision/number register: DECISIONS.md.

Reflects log through: [2026-09-30 09:24]

## Phase
- TESTS FIRST [2026-09-19 21:49]. T-2 2026-09-29 session logged [2026-09-30 06:59]; zipped [2026-09-30 09:21].
  T-1 wing panel weigh-in has no data.
- Sizing done on the S1223 [2026-09-19 00:28]; `analysis/sizing/out/design_card.txt` is STALE since
  the E423 lock [2026-09-21 22:51].
- Stability/trim not started; AVL not installed [2026-09-26 12:01].
- Event East/Florida, March 2027; lottery registered, closed [2026-09-30 09:24]. Report + TDS + 2D
  drawing due 2027-02-01 11:59:59 PM EST [2026-09-18 20:31].

## Hardware on hand
- 4 x motor SunnySky X2820 800 KV (41 mOhm, I0 0.9 A, 46 A for 30 s, 138 g) [2026-09-30 09:24].
- ESC SunnySky X60A V2 (60 A, 80 A for 10 s, 61 g) [2026-09-24 10:11]; count not logged. Throttle range
  calibrated before 2026-09-29 (Jordan) [2026-09-30 09:24].
- Two identical 4S packs; capacity, C rating and IR not logged. Pack A fresh: line 16.75 V,
  85-93 mOhm including leads [2026-09-30 06:59].
- Stand MT10PRO. Props APC 12x6E, 12x8E, 12x10E x 2 each; 9x4.5E, 9x6E x 4 each (9 in count
  INTERPRETED) [2026-09-30 09:24].

## Key numbers
- E423 at the 95 x 26 in wing: CLmax 1.55, payload 16.2 lb (model) [2026-09-21 22:51].
- THRUST_FACTOR_meas 0.978 +/- 0.007 at rho 1.1785; takeoff.py still 0.93 [2026-09-24 10:11].
- Calibrated top end: rpm = 776.5 x (V - 0.081 I), the same K as the 09-25 ceiling. The "calibrated"
  809 case is ruled out [2026-09-30 09:24].
- One motor at stick 100: 9x6E 1320 g, 18.7 A; 12x8E 2198 g, 36.1 A; 9x4.5E 1166 g, 15.75 A. Not a
  layout comparison [2026-09-30 06:59].
- Max thrust, ideal pack: 2 x 12x8E 9.80 lbf static / 7.71 at V_R; 4 x 9x6E 9.75 / 7.43 (borrowed
  factors) [2026-09-30 06:59].
- Aircraft pack 76-82 A (35-37C); sags below the 12.0 V default LVC [2026-09-26 19:59].

## BIG FLAG
Best case about 9.8 lbf static vs 12.5 lbf assumed in the sizing [2026-09-30 09:24]. Pack V0 and IR
are the main lever [2026-09-24 10:11].

## Decisions in force
E423 LOCKED; 2 x 12x8E CURRENT; motor count OPEN but no longer hardware-limited; wheel brake and
wood spar/boom required. See DECISIONS.md.

## Open items for Jordan
1. ESC count on hand [2026-09-30 09:24].
2. Pack capacity, C rating and IR [2026-09-26 19:59].
3. AMA card; sae.org affiliation. Status not logged [2026-09-26 12:01].
4. "4 of the 9 in props": 4 of each? [2026-09-30 09:24].
5. T-1 wing panel weigh-in [2026-09-26 12:01].
6. Commit reader v1.5 (installed, uncommitted) and the 2026-09-29 data [2026-09-30 06:59].

## NEXT TASK
Rerun `analysis/tests/predict_config.py` with the 2026-09-29 data: drop the 809 case; measured 9x6E
factors; top end 776.5 / 81 mOhm; pack 85-93 mOhm [2026-09-30 09:24]. Then rerun the sizing with the E423.
