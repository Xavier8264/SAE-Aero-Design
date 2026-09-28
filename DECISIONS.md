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
| D5 | Motor count (2 vs 4) and X2820s on hand | OPEN | low | [2026-09-26 19:59] | Count from Jordan; D4 |
| D6 | Wheel brake required (free landing roll 393 ft vs 400 ft zone; 114 ft braked) | CURRENT | medium | [2026-09-19 00:28] | Landing analysis with E423 and measured friction |
| D7 | Wood (non-FRP) spar and tail boom | CURRENT | medium | [2026-09-19 00:28] | Structures analysis |
| D8 | Bottle slot envelope 4.7 in dia x 13.0 in (typical bottle 4.33 x 12.4 in, about 0.10 lb) | CURRENT | low | [2026-09-18 20:39] [2026-09-18 21:06] | Measure the bottles we fly |
| D9 | Fill targets 4.05 lb filled, 1.05 lb empty; dry sand or pea gravel; never rice alone; water only if an FAQ allows | CURRENT | medium | [2026-09-18 20:39] [2026-09-18 21:06] | FAQ on filler |
| D10 | Stability start values: wing Cm0 -0.28, x_np about 0.44c (S1223 VLM; not recomputed for E423) | CURRENT | low | [2026-09-19 00:28] | AVL model of the E423 wing |

## Hardware (bought)
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| H1 | Motor SunnySky X2820 800 KV: Rm 41 mOhm, I0 0.9 A at 10 V, 46 A for 30 s, 700 W, 138 g | LOCKED | high | [2026-09-21 22:51] | Stand data (Kv see N3) |
| H2 | ESC SunnySky X60A V2: 60 A, 80 A for 10 s, 61 g; programming/LVC for X60A UNVERIFIED | LOCKED | high | [2026-09-24 10:11] sunnysky_esc_x60 | - |
| H3 | Stand Mayatech MT10PRO 10 kg (display only, no logging) | LOCKED | high | [2026-09-21 22:51] [2026-09-24 03:04] | - |
| H4 | Props on hand: APC 9x4.5E, 9x6E, 12x6E, 12x8E, 12x10E | LOCKED | high | [2026-09-21 22:51] | - |
| H5 | Packs: two identical 4S; capacity, C rating, IR not logged | OPEN | low | [2026-09-26 12:01] | Charger IR readout, label |

## Measured and modeled numbers
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| N1 | THRUST_FACTOR_meas 0.978 +/- 0.007 (12x8E, full throttle, rho 1.1785); `analysis/sizing/takeoff.py` still 0.93 | CURRENT | medium | [2026-09-24 10:11] | More props at calibrated duty (k_t 0.97-1.02 by prop, [2026-09-26 19:59]) |
| N2 | ESC ceiling rpm_max = 776 x (V - 0.075 I), within 0.3 pct over 4 props, reached near stick 80 | CURRENT | medium | [2026-09-26 12:00] | ESC throttle-range calibration |
| N3 | Kv: fit A 809 rpm/V (dmax 0.96); fit B (709) excluded; Kv and dmax not separated | OPEN | low | [2026-09-26 12:00] [2026-09-26 19:59] | No-prop Kv check |
| N4 | Max thrust, calibrated ESC + ideal pack: 2 x 12x8E 10.22 lbf static / 8.07 at V_R; 4 x 9x6E 10.23 / 7.84 (borrowed factors, band 10.16-11.12 static) | CURRENT | low | [2026-09-26 19:59] `analysis/tests/predict_config.py` | 9x6E stand run |
| N5 | BIG FLAG: sizing assumes 12.5 lbf static; best predicted about 10.2 lbf | OPEN | medium | [2026-09-24 10:11] [2026-09-26 19:59] | Sizing rerun with measured propulsion |
| N6 | Design DA 2000 ft; KLAL March DA P50 1410 ft, P90 1975 ft | CURRENT | high | [2026-09-19 00:28] | - |
| N7 | V_R 36.4 ft/s (S1223 card; still used by predict_config.py) | CURRENT | low | [2026-09-19 00:28] [2026-09-26 19:59] | Sizing rerun with E423 |
| N8 | Weight model K_BUILD 1.066 (NAU 2026 only); A_WING1 looks 2-4x too high | OPEN | low | [2026-09-19 00:28] [2026-09-20 21:55] | T-1 wing panel weigh-in |
| N9 | Pack 76-82 A for either leader (35-37C on 2200 mAh); sag 11.5-11.9 V vs 12.0 V default LVC (X60A LVC UNVERIFIED) | OPEN | low | [2026-09-26 19:59] | Pack IR + LVC setting |

## Process
| ID | Decision / number | Status | Conf | Source | Overturned by |
|---|---|---|---|---|---|
| P1 | TESTS FIRST: physical tests (T-1, T-2) before refining models | LOCKED | high | [2026-09-19 21:49] | Jordan |
| P2 | Memory: log is source of truth; STATE.md (imported by CLAUDE.md) + this register are derived; `tools/memcheck.py` at checkpoint | CURRENT | medium | [2026-09-28 15:02] | Jordan |
