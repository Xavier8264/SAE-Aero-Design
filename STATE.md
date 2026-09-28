# STATE -- hot cache (overwritten at every checkpoint; 500 words max)

Derived from PROJECT_MEMORY.md. If they disagree, the log's latest entry wins: fix this file.
[YYYY-MM-DD HH:MM] = a log entry header; grep "## \[2026-09-26 19:59" PROJECT_MEMORY.md, read that range.
Full decision/number register: DECISIONS.md.

Reflects log through: [2026-09-28 15:02]

## Phase
- TESTS FIRST [2026-09-19 21:49]. T-2 thrust stand in progress; T-1 wing panel weigh-in has no data.
- Sizing done on the S1223 [2026-09-19 00:28]; `analysis/sizing/out/design_card.txt` is STALE since
  the E423 lock [2026-09-21 22:51]. Not rerun.
- Stability/trim not started; AVL not installed [2026-09-26 12:01].
- Event East/Florida, March 2027. Report + TDS + 2D drawing due 2027-02-01 11:59:59 PM EST [2026-09-18 20:31].

## Hardware on hand
- Motor SunnySky X2820 800 KV (41 mOhm, I0 0.9 A, 46 A for 30 s, 138 g); count OPEN [2026-09-21 22:51].
- ESC SunnySky X60A V2 (60 A, 80 A for 10 s, 61 g) [2026-09-24 10:11]; throttle range probably not
  calibrated [2026-09-26 12:00].
- Two identical 4S packs; capacity, C rating and IR not logged [2026-09-26 12:01].
- Stand MT10PRO; props APC 9x4.5E, 9x6E, 12x6E, 12x8E, 12x10E [2026-09-21 22:51].

## Key numbers
- E423 at the 95 x 26 in wing: CLmax 1.55, payload 16.2 lb (model) [2026-09-21 22:51].
- THRUST_FACTOR_meas 0.978 +/- 0.007 at rho 1.1785; takeoff.py still 0.93 [2026-09-24 10:11].
- ESC ceiling rpm_max = 776 x (V - 0.075 I), reached near stick 80 [2026-09-26 12:00].
- Full throttle, calibrated ESC, ideal pack: 2 x 12x8E 10.22 lbf static / 8.07 at V_R;
  4 x 9x6E 10.23 / 7.84 (borrowed factors) [2026-09-26 19:59].
- Pack 76-82 A (35-37C); sags to 11.5-11.9 V, below the 12.0 V default LVC [2026-09-26 19:59].

## BIG FLAG
Best case about 10.2 lbf static vs 12.5 lbf assumed in the sizing [2026-09-26 19:59]. Pack V0 and IR
are the main lever [2026-09-24 10:11].

## Decisions in force
E423 LOCKED; 2 x 12x8E CURRENT; motor count OPEN; wheel brake and wood spar/boom required. See DECISIONS.md.

## Open items for Jordan
1. Lottery interest closes 2026-09-30; AMA card; sae.org affiliation. Status not logged [2026-09-26 12:01].
2. How many X2820s on hand; pack C rating and IR [2026-09-26 19:59].
3. T-1 wing panel weigh-in [2026-09-26 12:01].
4. Commit list from [2026-09-26 12:01]: done (git clean on 2026-09-28).

## NEXT TASK
Next stand session [2026-09-26 19:59]:
1. Full packs; write down which pack is on which run.
2. ESC throttle-range calibration.
3. 12x10E and 12x8E to stick 100, callouts at 60/70/80/90/100.
4. 9x6E to stick 100 (only prop that could beat the 12x8E).
5. Kv check if possible.
Then the 4-step T-2 pipeline in `analysis/tests/`, and rerun the sizing with the E423.
