# DECISIONS -- register of current decisions and numbers

Derived from PROJECT_MEMORY.md (the source of truth; its latest entry wins). Updated at every checkpoint.
To change a row: append the log entry first, then mark the old row SUPERSEDED and add a new row that
names it. Never delete rows. Lookup: grep this file for the topic, then read the cited log entry.

Status: LOCKED (rule, bought, or Jordan's call) | CURRENT (best estimate, may move) | OPEN | SUPERSEDED.
Conf: high / medium / low. Source: [YYYY-MM-DD HH:MM] = log entry header; plus library ID or file.

## Rules (rules_2027; FAQ numbers from the 2026 FAQ)
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| R1 | Span > 72 and < 96 in; chord > 4 in; length < 120 in; GTOW <= 55 lb | LOCKED | high | [2026-09-18 21:06] rules_2027 | 2027 rules revision |
| R2 | No FRP except bought motor mounts, props, gear, linkages | LOCKED | high | [2026-09-18 21:06] rules_2027 | 2027 rules revision |
| R3 | 2 motors x 12 in props or 4 x 9 in (sum per motor, FAQ 395); one 4S LiPo <= 2200 mAh, no limiter; Rx pack >= 1000 mAh | LOCKED | high | [2026-09-18 21:06] rules_2027 | 2027 FAQ |
| R4 | Airborne within 100 ft, single try; one 360 deg circuit; land within 400 ft same direction; steerable gear (FAQ 382) | LOCKED | high | [2026-09-18 21:06] rules_2027 | 2027 FAQ |
| R5 | Bottles internal, no shifting; EMPTY > 1.0 and < 4.0 lb; FILLED >= 4.0 lb; bottle count never decreases (FAQ 394) | LOCKED | high | [2026-09-18 21:06] rules_2027 | 2027 FAQ |
| R6 | FS = 3 EB + 11 FB; FFS = mean top-3 FS + PPB; PPB = max(10 - (FS - PS)^2, 0) | LOCKED | high | [2026-09-18 21:06] rules_2027 | 2027 rules revision |
| R7 | Pilots need a current AMA card (FAQ 170); team + advisor affiliated on sae.org (FAQ 157) | LOCKED | high | [2026-09-18 21:06] | 2027 FAQ |
| R8 | Event East/Florida, March 2027; report + TDS + 2D drawing due 2027-02-01 11:59:59 PM EST | LOCKED | high | [2026-09-18 20:31] | Lottery result |

## Design
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| D1 | Airfoil E423 (supersedes the S1223 point, D2) | LOCKED | high | [2026-09-21 22:51] | Jordan |
| D2 | S1223 point: 95 x 26 in wing, W_TO 35 lb, W_e 17.7 lb, payload 17.4 lb, 1E4F FS 47 at DA 2000 ft (`analysis/sizing/out/design_card.txt`, STALE) | SUPERSEDED | medium | [2026-09-19 00:28] | Replaced by D1; sizing rerun pending |
| D3 | E423 at the same 95 x 26 in wing: trimmed CLmax 1.55, payload 16.2 lb | CURRENT | medium | [2026-09-21 22:51] `analysis/sizing/out/sweep_summary.txt` | Sizing rerun with E423 + measured propulsion |
| D4 | Propulsion layout: 2 x APC 12x8E | CURRENT | medium | [2026-09-24 10:11] [2026-09-26 19:59] | 9x6E stand run beating 12x8E at V_R; 12x8E > 46 A per motor at full duty |
| D5 | Motor count (2 vs 4) and X2820s on hand | SUPERSEDED | low | [2026-09-26 19:59] | Replaced by D11 and H6 [2026-09-30 09:24] |
| D6 | Wheel brake required (free landing roll 393 ft vs 400 ft zone; 114 ft braked) | CURRENT | medium | [2026-09-19 00:28] | Landing analysis with E423 and measured friction |
| D7 | Wood (non-FRP) spar and tail boom | CURRENT | medium | [2026-09-19 00:28] | Structures analysis |
| D8 | Bottle slot envelope 4.7 in dia x 13.0 in (typical bottle 4.33 x 12.4 in, about 0.10 lb) | CURRENT | low | [2026-09-18 20:39] [2026-09-18 21:06] | Measure the bottles we fly |
| D9 | Fill targets 4.05 lb filled, 1.05 lb empty; dry sand or pea gravel; never rice alone; water only if an FAQ allows | CURRENT | medium | [2026-09-18 20:39] [2026-09-18 21:06] | FAQ on filler |
| D10 | Stability start values: wing Cm0 -0.28, x_np about 0.44c (S1223 VLM; not recomputed for E423) | CURRENT | low | [2026-09-19 00:28] | AVL model of the E423 wing |
| D11 | Motor count (2 vs 4): hardware no longer limits it (H6, H7); the choice follows D4 and the predict_config rerun. ESC count not logged (4-motor layout needs 4) | OPEN | medium | [2026-09-30 09:24] | predict_config rerun with the 09-29 data; ESC count |

## Hardware (bought)
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| H1 | Motor SunnySky X2820 800 KV: Rm 41 mOhm, I0 0.9 A at 10 V, 46 A for 30 s, 700 W, 138 g | LOCKED | high | [2026-09-21 22:51] | Stand data (Kv see N3) |
| H2 | ESC SunnySky X60A V2: 60 A, 80 A for 10 s, 61 g; programming/LVC for X60A UNVERIFIED | LOCKED | high | [2026-09-24 10:11] sunnysky_esc_x60 | - |
| H3 | Stand Mayatech MT10PRO 10 kg (display only, no logging) | LOCKED | high | [2026-09-21 22:51] [2026-09-24 03:04] | - |
| H4 | Props on hand: APC 9x4.5E, 9x6E, 12x6E, 12x8E, 12x10E | SUPERSEDED | high | [2026-09-21 22:51] | Replaced by H7 [2026-09-30 09:24] |
| H5 | Packs: two identical 4S; capacity, C rating, IR not logged | OPEN | low | [2026-09-26 12:01] | Charger IR readout, label |
| H6 | Motors on hand: 4 x SunnySky X2820 800 KV (Jordan) | LOCKED | high | [2026-09-30 09:24] | - |
| H7 | Props on hand: APC 12x6E x 2, 12x8E x 2, 12x10E x 2; 9x4.5E and 9x6E x 4 each (Jordan: "4 of the 9 in props", read as 4 each [INTERPRETED]) | LOCKED | medium | [2026-09-30 09:24] | Jordan on the 9 in count |

## Measured and modeled numbers
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| N1 | THRUST_FACTOR_meas 0.978 +/- 0.007 (12x8E, full throttle, rho 1.1785); `analysis/sizing/takeoff.py` still 0.93 | CURRENT | medium | [2026-09-24 10:11] | More props at calibrated duty (k_t 0.97-1.02 by prop, [2026-09-26 19:59]) |
| N2 | ESC ceiling rpm_max = 776 x (V - 0.075 I), within 0.3 pct over 4 props, reached near stick 80 | SUPERSEDED | medium | [2026-09-26 12:00] | Replaced by N10 [2026-09-30 06:59] |
| N3 | Kv: fit A 809 rpm/V (dmax 0.96); fit B (709) excluded; Kv and dmax not separated | SUPERSEDED | low | [2026-09-26 12:00] [2026-09-26 19:59] | Replaced by N11 [2026-09-30 06:59] |
| N4 | Max thrust, calibrated ESC + ideal pack: 2 x 12x8E 10.22 lbf static / 8.07 at V_R; 4 x 9x6E 10.23 / 7.84 (borrowed factors, band 10.16-11.12 static) | SUPERSEDED | low | [2026-09-26 19:59] `analysis/tests/predict_config.py` | Replaced by N12 [2026-09-30 06:59] |
| N5 | BIG FLAG: sizing assumes 12.5 lbf static; best predicted about 10.2 lbf | SUPERSEDED | medium | [2026-09-24 10:11] [2026-09-26 19:59] | Replaced by N13 [2026-09-30 06:59] |
| N6 | Design DA 2000 ft; KLAL March DA P50 1410 ft, P90 1975 ft | CURRENT | high | [2026-09-19 00:28] | - |
| N7 | V_R 36.4 ft/s (S1223 card; still used by predict_config.py) | CURRENT | low | [2026-09-19 00:28] [2026-09-26 19:59] | Sizing rerun with E423 |
| N8 | Weight model K_BUILD 1.066 (NAU 2026 only); A_WING1 looks 2-4x too high | OPEN | low | [2026-09-19 00:28] [2026-09-20 21:55] | T-1 wing panel weigh-in |
| N9 | Pack 76-82 A for either leader (35-37C on 2200 mAh); sag 11.5-11.9 V vs 12.0 V default LVC (X60A LVC UNVERIFIED) | OPEN | low | [2026-09-26 19:59] | Pack IR + LVC setting |
| N10 | Top end (2026-09-29, pack A, 3 props): stick-100 holds fit rpm = 776.5 x (V - 0.081 I), residual < 0.05 pct; same K as N2. Duty now rises about linearly to stick 100 (no flat top at stick 80); rpm NOT above the 776 line (0.980-0.994 of it) | SUPERSEDED | high | [2026-09-30 06:59] | Replaced by N16 [2026-09-30 09:24] |
| N11 | Kv x dmax = 776 at the top end on both 09-25 and 09-29; fit A's 809 not reached (stick-100 rpm 5.3-7.8 pct below it); Kv and dmax not separated; if the ESC top is 100 pct duty [UNVERIFIED], Kv about 776 | SUPERSEDED | low | [2026-09-26 12:00] [2026-09-30 06:59] | Replaced by N17 [2026-09-30 09:24] |
| N12 | Max thrust: the "calibrated" case of N4 is not reached, so use the "as set" case: 2 x 12x8E 9.80 lbf static / 7.71 at V_R (ideal pack), 7.91 / 5.97 (real); 4 x 9x6E 9.75 / 7.43, 7.83 / 5.68 (borrowed factors). predict_config not rerun | CURRENT | low | [2026-09-26 19:59] [2026-09-30 06:59] `analysis/tests/predict_config.py` | predict_config rerun with the 09-29 data |
| N13 | BIG FLAG: sizing assumes 12.5 lbf static; best predicted about 9.8 lbf | OPEN | medium | [2026-09-26 19:59] [2026-09-30 06:59] | Sizing rerun with measured propulsion |
| N14 | Pack A fresh (09-29): rest 16.73-16.74 V; line V0 16.74-16.76 V, R 85-93 mOhm incl. leads (single motor, up to 36 A); V min 13.63 V at 35.7 A; no ESC alarm | CURRENT | medium | [2026-09-30 06:59] | Pack IR readout; aircraft-level current |
| N15 | One motor at stick 100 (09-29, pack A): 9x6E 1320 g, 18.7 A, 14.99 V; 12x8E 2198 g, 36.1 A, 13.70 V; 9x4.5E 1166 g, 15.75 A, 15.26 V. Measured / APC median 0.984 / 0.996 / 0.964. Not a layout comparison | CURRENT | high | [2026-09-30 06:59] | Repeat runs |
| N16 | Top end with the ESC throttle range calibrated (Jordan confirmed): stick-100 holds (09-29, pack A, 3 props) fit rpm = 776.5 x (V - 0.081 I), residual < 0.05 pct; same K as N2. Calibration moved the ceiling from about stick 80 to stick 100; it did not raise the maximum | CURRENT | high | [2026-09-30 06:59] [2026-09-30 09:24] | A stick-100 run above the line |
| N17 | Kv x dmax = 776 with the calibrated ESC; fit A's 809 (the N4 "calibrated" case) ruled out. Kv and dmax not separated; if the X60A's calibrated top is 100 pct duty [UNVERIFIED], Kv about 776 | OPEN | medium | [2026-09-30 06:59] [2026-09-30 09:24] | Kv measured without the ESC (back-EMF spin test) |

## Process
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| P1 | TESTS FIRST: physical tests (T-1, T-2) before refining models | LOCKED | high | [2026-09-19 21:49] | Jordan |
| P2 | Memory: log is source of truth; STATE.md (imported by CLAUDE.md) + this register are derived; `tools/memcheck.py` at checkpoint | CURRENT | medium | [2026-09-28 15:02] | Jordan |
| P3 | T-2 video pipeline: `analysis/tests/read_mt10pro_video.py` v1.5 with --thrust-refine 24 (12x8E truth frames 18/18 vs 10/18 on v1.4); audio_rpm defaults blades 2, kmax 10 (not the 09-25 --blades 1 --kmax 4). v1.5 installed, not committed | CURRENT | medium | [2026-09-30 06:59] | Rerun of the 09-25 runs with v1.5 |
| P4 | Competition lottery: registered (Jordan), closed. Result not logged; R8 unchanged | LOCKED | high | [2026-09-30 09:24] | - |
