# TEST PLAN -- T-1 Wing Panel Weigh-In, T-2 Static Thrust Stand

Version 1.1, 2026-09-21 (v1.0 written 2026-09-20). Status: NOT YET RUN.
Audience: whoever builds and runs these in the shop. Read section 1, then your test.

Changes in v1.1: airfoil locked to the E423 (T-1 panel and rib table); T-2 rewritten around the
hardware actually bought: SunnySky X2820 800 KV motor, APC 9x4.5E / 9x6E / 12x6E / 12x8E / 12x10E
props, and the Mayatech MT10PRO 10 kg thrust tester. New section 3.4 lists every variable to
measure and why.

These are the two tests named as the immediate priority in PROJECT_MEMORY.md
[2026-09-19 21:49 CDT], under Jordan's standing TESTS FIRST ordering.

---

## 0. Why these two, and what they are worth

Every payload number this project has produced comes from `analysis/sizing/weight.py`, whose
structural weight is scaled by a single fitted constant K_BUILD = 1.066. That constant was fitted
to ONE external data point: NAU "Mach Pine" 2026, 12.2 lb empty, read off a poster
(weight.py:73-84). Nothing else supports it.

What that uncertainty costs, from `analysis/sizing/out/design_card.txt` (6-slot bay, 95 x 26 in wing):

| structure band | empty wt (lb) | payload (lb) | top rung | Flight Score |
|---|---|---|---|---|
| x0.8 (lean build)  | 14.79 | 20.25 | 0E5F | 55 |
| x1.0 (nominal)     | 17.66 | 17.38 | 1E4F | 47 |
| x1.2 (heavy build) | 20.54 | 14.50 | 2E3F | 39 |

That is 16 Flight Score points of pure ignorance, and it works out to about 2.8 FS points per
pound of empty weight. No amount of further analysis narrows it. Only a scale does. -> T-1.

NOTE (v1.1): the table above is the S1223 design point. The airfoil is now locked to the E423.
The only E423 number the model has so far is at the SAME 95 x 26 in wing: trimmed CLmax 1.55 vs
1.66 and payload 16.2 vs 17.4 lb (analysis/sizing/out/sweep_summary.txt line 20). The sizing has
not been re-optimized for the E423 yet, so the wing size and design card will move. The value of
each test (the spread per pound, the ranking T-1 before T-2) does not depend on the airfoil.

Thrust is the second lever. `takeoff.py` applies THRUST_FACTOR = 0.93 to the APC PER3 + Drela
motor model, and that 0.93 is a guess (takeoff.py:33). From
`analysis/sizing/out/takeoff_sensitivity.csv`, at the reference geometry:

    thrust x1.00 -> W_TO_max +1.18 lb
    thrust x0.85 -> W_TO_max -1.41 lb

So the plausible thrust-model range spans about 2.6 lb of takeoff weight, roughly 7 FS points.
Smaller than T-1 but the same kind of problem: unmeasurable by analysis. -> T-2.

Ranking is therefore T-1 first if only one can be done. The two tests are independent and can run
in parallel if two people are available.

---

## 1. Rules that apply to both tests

1. Units: record RAW readings in whatever the instrument shows (grams, volts, amps, rpm), plus the
   unit, in the CSV. Convert in the reduction script, never on paper. The models are in lb, lbf,
   ft, A, V.
2. Every data file is a CSV in `analysis/tests/data/` with the schema given below. One row per
   measured item or sample. Do not reformat, do not average by hand, do not delete outliers.
   An outlier gets a note in the `notes` column and stays in the file.
3. Record the environment at the start and end of every session: date, time, air temperature,
   barometric pressure (station pressure if available, else the altimeter setting from KLAL),
   relative humidity. Wood weight moves with humidity and thrust moves with air density. Density
   altitude comes from `reference/text/nws_density_altitude_formula.txt`.
4. Photograph every test article and rig setup before and after. Files in
   `analysis/tests/data/photos/`.
5. Each instrument gets a calibration check logged before use (sections 2.3 and 3.3). An
   uncalibrated number is not data.
6. When a test is done, append the result to PROJECT_MEMORY.md with the numbers, the file paths,
   and what is still UNVERIFIED. Then update the constants listed in the feedback tables and rerun
   the scripts named there.
7. Nobody changes a model constant without a measurement or a citation. If a measurement is
   ambiguous, widen the uncertainty band instead of picking a number.

---

## 2. TEST T-1: WING PANEL BUILD AND WEIGH-IN

### 2.1 Objective

Replace the lumped, single-point-fitted structural weight model with measured, component-level
coefficients for OUR wood, OUR build technique, and OUR builders.

The current model (weight.py:52) is:

    wing_lb = (A_WING0 + A_WING1 * chord_ft) * S_ft2 + spar(bending) + 0.25    , all x K_BUILD

with A_WING0 = 0.25 lb/ft^2 (sheeting + LE/TE + film), A_WING1 = 0.05 lb/ft^2 per ft of chord
(ribs), and K_BUILD = 1.066 (everything unaccounted for: glue, joints, film overlap, builder
skill). All three are [INFERRED] (weight.py:27-28, 39).

The test is designed to measure the three terms SEPARATELY rather than fit one scalar to one
total. That is the whole point: a single panel total can be matched by infinitely many wrong
combinations of coefficients, and those combinations extrapolate differently to the 95 x 26 in
wing.

### 2.2 Test article

Build one representative panel at the design point geometry:

| item | spec | source |
|---|---|---|
| airfoil | E423 (LOCKED by Jordan 2026-09-21; supersedes S1223) | reference/raw/airfoil_e423.dat |
| chord | 26.0 in (full design chord, do not scale) | design_card.txt |
| span | 24.0 in | one representative bay group |
| planform area | 4.33 ft^2 | 26 x 24 / 144 |
| rib pitch | 3.0 in -> 9 ribs | [INFERRED] typical practice; see note below |
| rib stock | 1/8 in balsa, lightened | modelaviation_sliced_rib_method (practice only) |
| spar caps | spruce, sized by weight.py:wing_spar_lb at this panel's span station | weight.py:42-45 |
| shear web | balsa, grain vertical | anc18_wood_aircraft |
| sheeting | D-box leading edge sheeting, thickness per build spec | |
| covering | the film actually intended for the aircraft | GAP: no film source archived |

IMPORTANT: build it the way the real wing will be built, by the people who will build the real
wing, with the glue that will be used on the real wing. A carefully built showpiece panel measures
a K_BUILD we will not reproduce at 95 in span at 2 am in February.

Rib pitch note: rib pitch has never been fixed in this project. Fix it before building. Because
the test weighs ribs individually, any other pitch can be scaled from the result, so this choice
does not invalidate the test.

Model prediction to compare against [computed from the current weight.py]:

- Area terms, before K_BUILD: (0.25 + 0.05 * 2.167) * 4.33 = 1.55 lb
- Area terms, with K_BUILD 1.066: 1.66 lb (751 g)
- Implied rib weight: 0.05 * 2.167 * 4.33 = 0.469 lb over 9 ribs = 23.7 g per rib

That last number is the specific thing to watch. The E423 section area coefficient is 0.0827
(computed with aerosandbox from reference/raw/airfoil_e423.dat, t/c 0.125), so a 26 in chord rib
has a section area of 55.9 in^2. In 1/8 in stock that gives:

| stock density | solid rib | 30 pct lightened | 40 pct lightened |
|---|---|---|---|
| 6 lb/ft^3 | 11.0 g | 7.7 g | 6.6 g |
| 8 lb/ft^3 | 14.7 g | 10.3 g | 8.8 g |

(For the record, the same calculation for the S1223 this table used before v1.1: area coefficient
0.0649, 43.9 in^2, 5.2 to 11.5 g. The E423 rib is about 27 percent heavier for the same chord.)

So a real E423 rib should land somewhere between about 7 and 15 g, while the model implies 23.7 g.
That is a factor of 1.6 to 3.6. Either A_WING1 is overestimated, or it is silently absorbing
capstrips, shear web and rib doublers that the model does not name anywhere else. The panel
settles which. If A_WING1 really is that high, the wing is lighter than modeled and payload goes
UP. Finding that is worth far more than the panel costs.

Build note for the E423: its trailing edge is about twice as thick as the S1223's (0.015c vs 0.008c
at 95 percent chord, i.e. 0.39 in vs 0.20 in at 26 in chord). That makes the aft rib, TE stock and
film line much easier to build to profile. Record the as-built TE thickness at 3 ribs (calipers) in
t1_parts.csv notes, because a TE that ends up thicker than the profile costs drag and a thinner one
costs strength.

### 2.3 Equipment

| item | requirement | calibration check |
|---|---|---|
| precision scale | 0-2000 g, 0.1 g resolution | check against a known mass (calibration weight, or a new US nickel at 5.000 g nominal) before and after each session |
| second scale | 0-10 kg, 1 g resolution, for the finished panel | same check with a heavier known mass |
| calipers | 0.001 in | check on a gauge block or a drill shank |
| steel rule / tape | for stock dimensions | |
| thermometer + hygrometer | shop conditions | |

### 2.4 Procedure

Phase A -- raw stock characterization (BEFORE cutting anything)

- A1. For every sheet, stick, and ply panel bought for this build: measure length, width and
  thickness with calipers (3 places each, record all 3) and weigh it. Record the vendor's claimed
  grade.
- A2. Compute density per piece. This gives the mean AND the scatter of our actual balsa supply,
  which is the input to the Monte Carlo in COMPUTE_BACKLOG T1-5, and which no published table can
  give us (balsa_strength_vs_density is hobbyist grade and is about strength, not about our stock).
- A3. Sample size: every piece of stock, minimum 15 pieces. If the order is smaller than 15 pieces,
  weigh every piece and say so in the log.
- A4. Sort by density and record which piece goes into which part. Heavy stock into spars and
  high-load parts, light stock into ribs, is a real weight-saving decision that needs this data to
  execute.

  -> `analysis/tests/data/t1_stock.csv`
  columns: piece_id, material, nominal_size, L_in, W_in, t1_in, t2_in, t3_in, mass_g,
  density_lb_ft3, intended_part, notes

Phase B -- component weighing (DURING the build, before assembly)

- B1. Weigh every rib individually, after cutting and lightening, before any glue. n = 9.
- B2. Weigh the spar caps (each), the shear web stock, the leading edge, the trailing edge, the
  sheeting, the capstrips, the tip rib, and any fittings, each as a separate line.
- B3. Record the total of all dry parts. This is the theoretical zero-glue panel weight.

  -> `analysis/tests/data/t1_parts.csv`
  columns: part_id, part_type, count, mass_g_each, mass_g_total, material, piece_id, notes

Phase C -- assembly weighing

- C1. Weigh the assembled, uncovered structure. Glue weight = C1 minus the sum of Phase B. Record
  ambient conditions and how long it has been since the last glue joint. Wood glue keeps losing
  water for days: wait at least 48 h after the last joint before C1, and record the elapsed time.
- C2. Weigh the covering film as cut, before application (off the roll, the exact pieces used).
- C3. Weigh the finished covered panel.
- C4. Film applied = C3 minus C1. Compare against C2 to capture trim waste and shrink loss.
- C5. Re-weigh the finished panel 7 days later in the same conditions, to catch moisture drift.

  -> `analysis/tests/data/t1_panel.csv`
  columns: stage, mass_g, temp_F, rh_pct, hours_since_last_joint, notes

### 2.5 Runs and sample size

One panel is one sample of K_BUILD, and that is the weakness of this test. Mitigations, in order
of preference:

1. Component-level weighing (Phase B) gives n = 9 on ribs and n >= 15 on stock density, so the
   area coefficients get real statistics even from one panel.
2. Build the second panel too. The wing needs at least two anyway, and two panels built by two
   different people is the single most informative version of this test, because
   builder-to-builder scatter IS K_BUILD. Do this if the schedule allows.
3. If only one panel is built, do NOT collapse the uncertainty band to zero. Keep a band of at
   least x0.92 / x1.08 on structure until a second article confirms it.

### 2.6 Data reduction

Write `analysis/tests/reduce_panel.py` (to be written once the CSVs exist). It computes:

    S_panel      = chord_in * span_in / 144                    [ft^2]
    m_ribs       = sum of rib masses                           [lb]
    m_skin       = sheeting + LE + TE + capstrips + film       [lb]
    m_spar       = spar caps + shear web + joiner              [lb]
    m_glue       = assembled_uncovered - sum(dry parts)        [lb]

    A_WING1_meas = m_ribs / (S_panel * chord_ft)               [lb/ft^2 per ft]
    A_WING0_meas = m_skin / S_panel                            [lb/ft^2]
    K_BUILD_meas = (m_ribs + m_skin + m_spar + m_glue) / (m_ribs + m_skin + m_spar)

Note what this does to K_BUILD: it stops being a catch-all fudge factor and becomes a measured
glue-and-assembly overhead, typically a few percent, with the real structural mass carried by the
measured A_WING0 and A_WING1. That is a strictly better model even if the total comes out the same.

Also compare m_spar against `wing_spar_lb()` evaluated for this panel's span station, and compare
the measured spruce density against SPRUCE_DENS = 0.0145 lb/in^3 (weight.py:32).

### 2.7 Acceptance and decision gates

| outcome | reading | action |
|---|---|---|
| panel within 0.1 lb of the 1.66 lb prediction | model is good | keep K_BUILD, narrow the band to x0.9 / x1.1 |
| panel lighter by more than 0.15 lb | ribs or film overestimated | refit; expect payload to rise; rerun the sweep, because the optimum wing area may grow |
| panel heavier by more than 0.15 lb | build overhead underestimated | refit; if empty weight goes above about 19 lb, the 6-slot bay and the 35 lb design point both need revisiting |
| rib mass far below 23.7 g each (expect 5 to 11 g) | A_WING1 too high, as suspected | this is the expected result; refit and rerun everything |
| stock density scatter worse than +/- 20 percent | supply is inconsistent | weigh-and-sort becomes a build requirement, not an option |

### 2.8 Feedback into the code (do this in order)

| # | file | constant | replace with |
|---|---|---|---|
| 1 | analysis/sizing/weight.py:27 | A_WING0 = 0.25 | A_WING0_meas |
| 2 | analysis/sizing/weight.py:28 | A_WING1 = 0.05 | A_WING1_meas |
| 3 | analysis/sizing/weight.py:32 | SPRUCE_DENS = 0.0145 | measured spruce density |
| 4 | analysis/sizing/weight.py:73-84 | calibrate() fits K_BUILD to NAU 2026 | replace the fit with the measured K_BUILD; KEEP the NAU case as a printed cross-check, do not delete it |
| 5 | analysis/sizing/weight.py docstring | "calibrated to NAU 2026" | "calibrated to our own panel, NAU 2026 retained as cross-check"; retag the constants [VERIFIED] with the data file path |
| 6 | analysis/sizing/weight.py:34 | BATTERY_LB = 0.55 | weigh the actual pack (T-2 Run A does this) |

Then rerun, in this order:

    python analysis/sizing/weight.py
    python analysis/sizing/sweep.py
    python analysis/sizing/design_card.py

and diff the new design_card.txt against the current one. The wing area, the bay size and the top
scoring rung can all move. Expect to re-open the "how many bottle slots" decision.

---

## 3. TEST T-2: STATIC THRUST STAND

### 3.1 Objective

Measure static thrust, RPM, battery current and battery voltage for every prop the team owns, on
the SunnySky X2820 800 KV motor and a real 4S 2200 pack. Use the result to calibrate what the
propulsion model currently guesses or takes from a catalog:

| what | model value now | where | status |
|---|---|---|---|
| prop model error | THRUST_FACTOR = 0.93 | takeoff.py:33 | guess |
| motor Kv | matched per prop (843 for the 12x6E) | propulsion.py:106 match_kv() | now FIXED at 800 by the purchase; unmeasured |
| motor Rm, I0 | 0.028 ohm, 1.8 A (generic 42xx-50xx class) | propulsion.py:43 | datasheet says 0.041 ohm, 0.9 A at 10 V; unmeasured |
| pack model | V_OC_TO 16.0 V, R_BATT 0.025 ohm | propulsion.py:35-37 | guess |
| propulsion group mass | 1.68 lb | weight.py:38 | guess; datasheet motor is 138 g |

Note: the X2820 has a 28 mm stator. That is the size class the model assumed for the 4-MOTOR
layout (propulsion.py:23), not the 42xx-50xx class it assumed for 2 motors. The model's static
thrust for 2 x 12x6E drops from 13.2 lbf (design_card.txt: 6.62 lbf per motor at DA 1400, Kv 843,
88 A) to 12.0 lbf with this motor, and SunnySky's own table implies about 9.9 lbf (2 x 2240 gf,
section 3.5). This test decides which is true.

### 3.2 Test articles (hardware on hand, 2026-09-21)

Motor: SunnySky X2820 800 KV, original black X Series (NOT the "X V3" line, which has no 800 KV).
- Datasheet: reference/text/sunnysky_x2820_800kv_spec.txt; manufacturer test table:
  reference/data/sunnysky_x2820_800kv_testdata.csv. Ratings: 46 A for 30 s max continuous, 700 W,
  3-5S, 60 A ESC recommended, 12N14P (14 poles, 7 pole pairs), 5 mm shaft, 138 g.
- How many are on hand: 4 (Jordan, 2026-09-30). The 2-motor layout needs 2, the 4-motor layout
  needs 4. Test at least 2 of them if available; motor-to-motor scatter matters when all motors
  share one pack.
- Confirm it really is the 800 KV version with the no-prop run (C1). The 800, 920 and 1100 KV
  versions are 15 to 40 percent apart in speed, which is easy to see. Do not try to identify it by
  its 41 mOhm winding resistance: a hobby multimeter's own leads read 100-300 mOhm.

Props (APC thin electric; all five have APC performance data in the library):

| prop | layout | library data | rules check (2 x 12 in max, or 4 x 9 in max) |
|---|---|---|---|
| 9x4.5E | 4 motors | apc_9x45e | OK |
| 9x6E | 4 motors | apc_9x6e | OK |
| 12x6E | 2 motors (current design point prop) | apc_12x6e | OK |
| 12x8E | 2 motors | apc_12x8e | OK |
| 12x10E | 2 motors | apc_12x10e | OK, but see the current warning in 3.5 |

Check that each label says "E". Balance each prop before its first run. Weigh each one (Run A).

Battery: the 4S 2200 mAh pack intended for competition, plus a second identical pack so testing
continues while one charges. Give each pack an ID.

ESC: the ESC intended for competition (SunnySky recommends 60 A for this motor), with its actual
wiring, connectors and lead lengths. The wiring is part of R_BATT. OPEN: which ESC.

Throttle source: the MT10PRO has no throttle output that any listing mentions [INFERRED]. Use the
competition transmitter and receiver, or a servo tester. BEFORE the first run, do the ESC's
throttle-range calibration with that same transmitter, so full stick really is 100 percent duty.
Skip this and "100 percent" may be 90-something percent, and the full-throttle model (3.6 rule 2) no
longer applies.

### 3.3 Equipment

| item | what it gives / requirement | calibration check |
|---|---|---|
| Mayatech MT10PRO (bought) | thrust 0-10 kg, 1 g resolution; battery voltage 0-60 V; current 0-150 A; power (V x I). Listed "power input 5-26 V (XT60)", so a 4S pack (16.8 V max) is in range [INFERRED: the listing does not say whether that input is the pack or a separate supply]. Motor base 16/19/25 mm. DISPLAY ONLY: no RPM, no torque, no data logging, no PC link. Source: reference/text/mayatech_mt10pro.txt (reseller page; no official Mayatech page or manual was found) and mayatech_mt10pro_safety | thrust: hang known masses on a string over a pulley, pulling along the thrust axis, 0.5 / 1 / 2 / 3 kg, loading up and then down (the sled rides on linear bearings, so look for hysteresis). Before and after every session -> t2_cal.csv. Zero it with the prop mounted before every run. Voltage: against a multimeter at the pack. Current: against a DC clamp meter at one point, if one is available |
| tachometer, MUST BE ADDED (the MT10PRO has none) | optical prop tach with a 2-blade setting | cross-check against the audio method at one steady point. LED and fluorescent lights flicker and can alias an optical tach: use daylight or a flashlight |
| phone on a tripod, video at 60 fps with sound | THIS IS THE DATA LOGGER. Frame both MT10PRO screens and the throttle (transmitter screen or a card) in one shot. The picture gives thrust, V, A, W against time; the sound gives RPM against time (blade-pass frequency = 2 x RPM / 60 for a 2-blade prop, e.g. 333 Hz at 10,000 rpm) | measure the MT10PRO display update rate once: film a throttle step and count frames between display changes. Log the rate |
| cell checker | per-cell resting voltage before and after each run | against the multimeter |
| IR thermometer | motor can, ESC and pack temperature right after each run | |
| thermometer, barometer, hygrometer | air density | barometer: station pressure, or the local altimeter setting plus the field elevation |
| scale, 0.1 g | Run A component masses | nickel check (2.3) |

Stand capacity: the model's largest single-motor static thrust with this motor is 3.2 kg (12x8E and
12x10E, 3.5), 32 percent of the MT10PRO's 10 kg range, the same margin v1.0 asked for. The largest
current is 98 A (2 motors on 12x10E, D5 wiring), under the 150 A rating. The DIY load cell and HX711
design in v1.0 is no longer needed and has been dropped.

Mounting check before test day [UNVERIFIED]: confirm the X2820's mounting holes (its X-mount or back
plate) match one of the MT10PRO's 16 / 19 / 25 mm patterns. If not, make an adapter plate; do not
drill the stand.

### 3.4 What to measure, and why each variable matters

The propulsion model is a chain of four links. Each measured variable pins down one link. A link
that is not measured hides its error inside the others, and then the calibration means nothing.

    PACK              ESC + WIRING        MOTOR                PROP
    V_oc, R_batt  ->  V_batt, I      ->   Kv, Rm, I0      ->   Ct(RPM)       ->  THRUST
                      (measured)          (fit from V, I, RPM) (fit from T, RPM)

A. Every sample (from the video of the MT10PRO, plus audio or tach)

| variable | unit | from | why it is needed | calibrates |
|---|---|---|---|---|
| thrust T | g, as displayed | MT10PRO | the output the takeoff model needs | THRUST_FACTOR |
| RPM | rev/min | audio blade-pass; optical tach check | the most important variable, and the one the MT10PRO does NOT give. It cuts the chain in half: thrust against RPM tests the prop alone; RPM against voltage and current tests the motor alone. Without RPM a thrust shortfall cannot be pinned on the prop, the motor or the pack | THRUST_FACTOR at matched RPM, Kv, Rm |
| battery voltage V_batt | V | MT10PRO | at full throttle the motor sees this voltage (less a small ESC drop), so it sets RPM. See the SunnySky example below | V_OC_TO, R_BATT, Kv fit |
| battery current I | A | MT10PRO | current is motor torque, Q = (I - I0) / Kv. It is also the safety limit (46 A per motor) and the energy used | Rm, I0, R_BATT, I_DESIGN |
| electrical power P | W | MT10PRO (V x I) | a consistency check on V and I only | none |
| throttle setting | percent | transmitter channel monitor or servo tester | tags which points are true full throttle (model grade) and which are part throttle (lower confidence) | point tagging |
| time from throttle-up | s | video time stamp | thrust and voltage droop over a takeoff-length burst | droop factor |

B. Once per run

| variable | unit | from | why |
|---|---|---|---|
| prop, motor, ESC, pack IDs | | labels | unit-to-unit scatter; a run that cannot be tied to its hardware is not data |
| pack resting voltage per cell, before and after | V | cell checker | state of charge and V_oc; decides which runs count as fresh-pack runs |
| motor can, ESC, pack temperature after the run | F | IR thermometer | thermal limits, and a hot winding has a higher Rm (copper +0.39 percent per deg C), so the fit needs it |
| air temperature, station pressure, humidity | F, inHg, pct | weather instruments | air density. At a given RPM thrust is proportional to density: a 90 F day is about 6 percent thinner than a 59 F standard day, as big as the error being measured |
| prop clearance to walls, bench and floor | in | tape | blockage and ground effect change static thrust; recorded so runs can be compared |

C. Once per session: MT10PRO calibration and zero (Run 0); display update rate (once ever);
component masses (Run A).

D. Not measured, and what that costs
- Torque. The MT10PRO has no torque cell, so the prop power coefficient Cp is not measured
  directly. Shaft power comes through the motor model, P_shaft = (V_m - I*Rm) * (I - I0), which is
  sound at full throttle where V_m is known. One more reason to take the model points at 100 percent.
- Anything with airspeed (static test only, section 6).

WHY RPM AND VOLTAGE MATTER SO MUCH, a worked example from the datasheet.
SunnySky lists the APC 12x6 at 100 percent throttle on "14.8 V" as 2240 gf at 32.7 A, with no RPM.
Our model, given the same motor constants and a stiff 14.8 V supply, predicts 3056 gf at 41.6 A.
That looks like a 27 percent miss. Now work backwards: an APC 12x6E absorbs 32.7 A worth of torque
at 9,180 rpm, where the APC table gives 2376 gf. SunnySky's 2240 gf is 0.94 of that (the 12x8 gives
0.93), right at the THRUST_FACTOR of 0.93 already assumed. So the prop data probably holds up. The
real difference is that SunnySky's motor was only seeing about 12.4 to 12.8 V, roughly 3.1 to 3.2 V
per cell, while our model assumes about 15 V from a fresh pack [INFERRED: SunnySky publishes neither
its voltage under load nor whether its prop is the E version; its Watts column is simply
14.8 V x A]. Whichever is true for OUR pack, wiring and ESC is worth about 30 percent of static
thrust. Only V_batt and RPM, measured together during the run, settle it. Thrust alone cannot.

### 3.5 Model predictions and the current limit (read before the first run)

From analysis/tests/predict_x2820.py (full output analysis/tests/out/predict_x2820.csv). Datasheet
motor constants (Kv 800, Rm 0.041 ohm, I0 0.9 A), fresh pack (V_oc 16.0 V, R_batt 0.025 ohm),
DA 1400 ft, 100 percent throttle, static. The worked example above suggests these are an UPPER
bound on both thrust and current.

| prop | stand, one motor: RPM / thrust g / current A / V_batt | pct of 46 A rating | aircraft: motors / total thrust lbf / pack current A |
|---|---|---|---|
| 9x4.5E | 11,880 / 1435 / 16.6 / 15.6 | 36 | 4 / 11.0 / 59 |
| 9x6E | 11,640 / 1634 / 21.1 / 15.5 | 46 | 4 / 12.2 / 72 |
| 12x6E | 10,530 / 3024 / 41.1 / 15.0 | 89 | 2 / 12.0 / 74 |
| 12x8E | 10,070 / 3210 / 49.4 / 14.8 | 107 | 2 / 12.5 / 88 |
| 12x10E | 9,740 / 3201 / 55.5 / 14.6 | 121 | 2 / 12.4 / 98 |

SunnySky's own 100 percent points, where they exist: 12x6 2240 gf at 32.7 A; 12x8 2300 gf at 38.5 A.
The 9x4.5E, 9x6E and 12x10E are not in SunnySky's table.

What this means for test day:
1. Every prop stays under APC's RPM limit (150,000 / D: 12,500 rpm at 12 in, 16,700 rpm at 9 in).
   The no-prop run reaches about 13,400 rpm on a full pack; that is motor only, no prop limit.
2. The 12x8E and 12x10E are predicted ABOVE the motor's 46 A rating on a fresh pack, and the 12x6E
   is close. CURRENT RAMP RULE for each 12 in prop the first time it runs: step the throttle
   50 -> 75 -> 90 percent, 3 s each, watching the ammeter. If the current at 90 percent is already
   above 42 A, do NOT go to 100 percent. Record that this prop overloads the X2820 on 4S. That is a
   design result, not a failed test. Any reading above 46 A: throttle cut immediately.
3. Run the props in increasing load: no prop, 9x4.5E, 9x6E, 12x6E, 12x8E, 12x10E. Each step shows
   the current trend before the next, heavier one.
4. Full-throttle holds are 6 s at most (the rating is 30 s), then 2 minutes of cooling.

### 3.6 Methodology, read this before running anything

Three rules make this test worth doing.

1. MEASURE THRUST AND RPM TOGETHER, ALWAYS. The APC data is Ct and Cp against (RPM, J)
   (propulsion.py:51-93). Comparing measured thrust with the APC table AT THE SAME MEASURED RPM
   isolates prop model error. Comparing at the same throttle setting mixes prop error with motor,
   battery and ESC error, and gives a THRUST_FACTOR that means nothing.

2. TAKE THE MODEL-CRITICAL POINTS AT 100 PERCENT THROTTLE. At full throttle the ESC is effectively
   a closed switch, so V_motor = V_batt and the Drela first-order model applies directly
   (drela_motorprop eqs 1-2: Qm = (i - i0)/Kv, Omega = (v - i*R)*Kv). At part throttle the ESC is
   chopping and the effective motor voltage is one more unmeasured quantity. Vary the LOAD by
   changing props, not by changing throttle. Having five props now helps: they give five load
   points on the motor curve. Part-throttle points are still taken for the mission energy model,
   tagged lower confidence. This rule depends on the ESC throttle calibration in 3.2.

3. THE VIDEO IS THE LOG. Start recording before arming, speak the run ID into it, and keep it
   running until the throttle is back at zero and the prop has stopped. Transcribe the numbers
   from the frames afterwards: every display update for the bursts, the average of the last 3 s for
   steady points. Do not try to write numbers down during a run.

This test is static only (J = 0). It cannot measure thrust lapse with airspeed, which is what
actually sets the takeoff distance at V_R. Section 6 says what to do about that.

### 3.7 Procedure

Run A -- component weights (10 minutes, do it first, it is free)

- A1. Weigh each of: motor (datasheet 138 g), ESC, each of the 5 props, spinner or safety nut,
  motor mount, motor wiring run, battery pack, arming plug and its leads, receiver, each servo.

  -> `analysis/tests/data/t2_masses.csv`   columns: item, mass_g, notes

Run 0 -- stand setup and calibration (every session)

- 0.1 Bolt the MT10PRO to the bench through the holes in its base. Mount the motor and check the
  thrust line is level.
- 0.2 Calibrate with hanging masses over a pulley (3.3), loading up and then down.
- 0.3 Record the environment (section 1, rule 3).
- 0.4 ESC throttle-range calibration with the transmitter (first session, and any time the ESC or
  radio changes).
- 0.5 First session only: display update rate check.

  -> `analysis/tests/data/t2_cal.csv`   columns: session_id, applied_g, reading_g, direction, notes

Run B -- battery characterization

- B1. Charge the pack to full, rest 30 minutes, measure per-cell resting voltage. This is V_oc.
- B2. During the Run D bursts, capture V_batt and I_batt from the video. R_BATT is fitted as the
  slope of V_batt against I_batt.
- B3. Immediately after each burst, measure pack temperature and per-cell voltage.
- B4. Repeat B1 on a pack at about 50 percent charge, for the mid-mission voltage (V_OC_CRUISE,
  currently the guess 15.2 V, propulsion.py:36).
- B5. Record the resting voltage before every run. Only the first 2 runs after a full charge count
  as fresh-pack runs (they set V_OC_TO). Recharge when resting voltage falls below about 3.9 V per
  cell [INFERRED threshold], roughly 10-12 six-second bursts.

Run C -- motor constants

- C1. No prop, 100 percent throttle: RPM, current, voltage. RPM from the optical tach reading one
  strip of white or reflective tape on the bell, or from the audio motor whine at 7 x RPM / 60
  (7 pole pairs). Gives Kv = RPM / (V_motor - I*Rm) and I0 at operating speed. Also confirms the
  motor version: expect roughly 12,000 to 13,400 rpm on a full pack; a 920 KV would run about 15
  percent faster.
- C2. Light loads: 9x4.5E and 9x6E at 100 percent (taken in Run D).
- C3. Heavy loads: the 12 in props at 100 percent (taken in Run D).
- C4. Fit Kv, Rm and I0 across C1 to C3, six load points (no prop plus five props), from
  Omega = (v - i*Rm)*Kv. Do NOT do a locked-rotor test; it dumps full current into a stalled motor
  and cooks the windings.
- C5. Repeat for each motor.

  -> `analysis/tests/data/t2_motor.csv`
  columns: run_id, motor_id, prop, throttle_pct, rpm, rpm_source, I_A, V_batt_V, T_g, temp_motor_F,
  notes

Run D -- static thrust, the main event

- D1. Each prop in the order of 3.5 (12 in props only after passing the ramp rule): 100 percent
  throttle, hold 6 s, video running. Cut throttle.
- D2. Cool down 2 minutes. Repeat. 3 runs per (prop, motor). With 2 motors that is
  5 props x 2 motors x 3 = 30 runs; with one motor, 15. If time runs short, the priority is
  12x6E, 12x8E, 9x6E, 9x4.5E, then 12x10E.
- D3. Takeoff duplicate: one run per 12 in prop that passed the ramp rule, 100 percent held for
  5.0 s (the model predicts a 4.5 s ground roll, design_card.txt), from a fresh pack. What matters
  is the DROOP: thrust, RPM and V_batt at t = 0.5 s against t = 4.5 s. The takeoff model assumes
  constant open-circuit voltage through the roll, and that is optimistic. Add the 9x6E if the
  4-motor layout is still in play.
- D4. Part-throttle map, lower confidence: 50, 60, 70, 80, 90 percent, 5 s each, 12x6E and 12x8E,
  one motor. For the circuit energy model, which predicts 38 A level and 48 A in turns
  (design_card.txt).
- D5. Aircraft pack load, optional, needs a second rigidly bolted motor mount: two motors on one
  pack through a Y-harness wired DOWNSTREAM of the MT10PRO, so the MT10PRO reads total pack current
  and voltage. Thrust on the stand motor only; RPM of the second motor by optical tach. 100 percent,
  5 s, 12x6E. This is the only way to see real pack sag at about 75 A. Four motors on 9 in props
  are not practical on one stand; the fit from Runs B to D predicts that case.

  -> `analysis/tests/data/t2_thrust.csv`
  columns: run_id, video_file, t_s, prop, motor_id, esc_id, pack_id, pack_fresh, n_motors_live,
  throttle_pct, T_g, rpm, rpm_source, I_A, V_batt_V, P_W, temp_motor_F, temp_air_F, press_inHg,
  rh_pct, notes

Total: about 35 to 45 runs with two motors. One long afternoon with two people, plus charging.

### 3.8 Data reduction

Write `analysis/tests/reduce_thrust.py`. It computes:

1. Air density from temperature, pressure and humidity (nws_density_altitude_formula).
2. RPM against time from each video's sound track: pull the audio with ffmpeg (installed on the
   laptop, verified 2026-09-21), take a short-time FFT, and track the blade-pass peak near
   2 x RPM / 60. Check it against the optical tach points.
3. For each steady full-throttle point: T_apc = Ct(rpm, J=0) * rho * n^2 * D^4, using the same
   `parse_apc` and `coeffs` functions already in propulsion.py:51-93. Reuse them, do not rewrite them.
4. THRUST_FACTOR_meas = mean(T_measured / T_apc) over all full-throttle points, with the standard
   deviation, per prop. If the props disagree by more than a few percent, say so rather than
   averaging it away.
5. Kv, I0 and Rm by least squares on the Drela relations over the Run C and D full-throttle
   points, with V_motor = V_batt - I * R_esc.
6. R_BATT from the slope of V_batt against I_batt; V_OC_TO from the fresh-pack runs.
7. Droop ratios from D3: T(4.5 s) / T(0.5 s), and the same for RPM and V_batt.
8. Each full-throttle point against analysis/tests/out/predict_x2820.csv and against SunnySky's
   table, so the log records which of the two the real hardware looks like.

### 3.9 Acceptance and decision gates

| outcome | reading | action |
|---|---|---|
| THRUST_FACTOR in 0.90 to 1.00 | the APC data holds up | set the measured value, narrow the takeoff band |
| THRUST_FACTOR below 0.85 | prop or stand is underperforming | check the stand first (calibration, alignment, blockage). If it is real, W_TO_max drops about 1.4 lb and the design point needs revisiting |
| V_batt at full throttle near 12.5 to 13 V (SunnySky-like) instead of about 15 V | pack, wiring or ESC losses much worse than modeled | revisit V_OC_TO and R_BATT first; 2 x 12x6E static thrust falls toward 10 lbf; rerun takeoff and sweep before anything else |
| measured Kv more than 10 percent off 800 | wrong version (920 / 1100) or normal scatter | check against the datasheet versions; use the measured Kv in every model run |
| one motor above 46 A at 100 percent | that prop overloads the X2820 on 4S | drop the prop for this motor; do not fly it |
| aircraft pack current above 92 A (D5, or predicted by the fit) | 2 x 46 A motor limit, and 42C on a 2200 pack | pick the lighter prop; check the pack's C rating |
| V_batt under load below 12.8 V (3.2 V per cell) | pack sag worse than modeled | same action as the 12.5-13 V row |
| thrust droop over 4.5 s worse than 10 percent | takeoff model is optimistic | add the droop to takeoff.py as a time-dependent thrust factor, not a constant |
| motor can above about 158 F (70 C) after a burst | beyond SunnySky's own highest 100 percent figure (64 C, 13x8 on 4S) | stop, cool, and treat that load as a limit |
| pack above about 140 F (60 C) after a burst | LiPo thermal limit | stop, reduce current, record it as a hard constraint on I_DESIGN |

### 3.10 Feedback into the code

| # | file | constant | replace with |
|---|---|---|---|
| 1 | analysis/sizing/takeoff.py:33 | THRUST_FACTOR = 0.93 | measured, per prop |
| 2 | analysis/sizing/propulsion.py:43 | MOTOR_CLASS[2] Rm 0.028, I0 1.8 | interim: datasheet 0.041 ohm / 0.9 A (cited); final: measured |
| 3 | analysis/sizing/propulsion.py:43 | m_motor_lb, m_esc_lb, m_prop_lb, m_mount_lb | Run A weights |
| 4 | analysis/sizing/propulsion.py:35 | V_OC_TO = 16.0 | measured fresh-pack value under load |
| 5 | analysis/sizing/propulsion.py:36 | V_OC_CRUISE = 15.2 | measured at 50 percent charge |
| 6 | analysis/sizing/propulsion.py:37 | R_BATT = 0.025 | fitted slope |
| 7 | analysis/sizing/propulsion.py:38 | I_DESIGN = 90.0 | now capped by the motor, 2 x 46 A = 92 A; set from the prop result |
| 8 | analysis/sizing/propulsion.py:106 and takeoff.py:43 | Kv from match_kv() | Kv is now fixed by the hardware. PropSystem already takes kv= and motor=; takeoff.py:43 must pass them (measured Kv 800-ish and the X2820 constants). Keep match_kv for trade studies only |
| 9 | analysis/sizing/weight.py:34, 38 | BATTERY_LB 0.55, PROP_GROUP_DEFAULT 1.68 | Run A weights |
| 10 | analysis/sizing/propulsion.py docstring lines 18-24 | "all [UNVERIFIED] until thrust-stand tests" | retag [VERIFIED] with the data file path and date |

Then rerun:

    python analysis/sizing/propulsion.py
    python analysis/sizing/takeoff.py
    python analysis/sizing/sweep.py
    python analysis/sizing/design_card.py

and diff design_card.txt. The prop choice is genuinely open: on this motor the 12x8E and 12x10E may
be ruled out by current, and the 4-motor 9 in layout (lower current per motor) may come back into
play.

---

## 4. Safety

- LiPo: charge and store in a fire-safe container, never unattended. Inspect for puffing before
  every run. A 4S 2200 at 90 A is a 40C discharge. Reference: nasa_liion_guidelines.
- Props: nobody in the plane of rotation, ever, including the person holding the throttle. Use a
  physical barrier. Eye protection for everyone in the room.
- The motor and stand are bolted down before the pack is connected. The pack is connected last and
  disconnected first.
- Throttle cut: before the first run, set up and test the transmitter's throttle cut (kill switch)
  and set the receiver failsafe to throttle OFF, then check it by switching the transmitter off
  with the motor at low throttle. The throttle operator's thumb stays on the cut for every run.
  Throttle at zero before the pack is connected.
- Current: follow the ramp rule in 3.5 for every 12 in prop. Any reading above 46 A is an
  immediate throttle cut. Hold full throttle 6 s at most, then cool 2 minutes.
- Secure every power lead and the MT10PRO cables away from the prop arc (mayatech_mt10pro_safety).
- Use an arming plug on the stand the same way the rules require it on the aircraft (red arming
  plug on the positive lead, rules_2027). Practice the ritual now.
- A 12 in prop at 10,500 rpm has released blades before. Treat a damaged or previously overspeed
  prop as scrap.
- The AMA National Safety Code applies once this moves to the field: ama_national_safety_code.
- T-1 has no hazards beyond knives and CA glue. Ventilate for the covering iron and for CA.

---

## 5. Order of work

1. T-2 Run A (component weights). 10 minutes, no rig needed, feeds both tests.
2. T-1 Phase A (stock characterization). Must happen before anything is cut.
3. T-1 Phases B and C (build and weigh) and T-2 Run 0 (stand setup, calibration, ESC throttle
   calibration) then Runs B through D, in parallel if two people.
4. Reduce, update constants, rerun the scripts, diff the design card.
5. Log to PROJECT_MEMORY.md.
6. Resume AVL stability and trim (the task deferred by the TESTS FIRST ordering), now on a weight
   and thrust model that has been measured rather than assumed.

---

## 6. Known limits of this plan

- T-1 gives n = 1 on K_BUILD unless a second panel is built. Section 2.5 covers it. Do not report a
  tight uncertainty band off one panel.
- T-2 is static only. It cannot measure thrust lapse with airspeed, and thrust at V_R (9.5 lbf at
  36.4 ft/s, design_card.txt) is what actually determines whether we are airborne within 100 ft.
  The static measurement calibrates the PROP MODEL, and the calibrated model then predicts the
  lapse. That is the best available route without a wind tunnel or an instrumented flight test. A
  taped-down measurement from a moving vehicle is NOT a substitute and introduces more error than
  it removes. The lapse gets checked later against flight data using nasa_takeoff_flighttest_method
  (NASA TN D-7603), which includes pilot technique effects.
- No covering-film source is archived, so film weight has no external cross-check. The measurement
  is the only source. Flagged as a library GAP in reference/GUIDE.md:94.
- Humidity effects on balsa weight are caught by the 7-day re-weigh (C5) but not modeled. If the
  drift exceeds about 2 percent, it needs to be added to the weight budget as a margin.
- ESC part-throttle efficiency (ETA_ESC_PART = 0.95, propulsion.py:39) is not well measured by this
  plan. The part-throttle map (D4) gives an indirect check only.
- No torque measurement. The MT10PRO has no torque cell, so the prop power coefficient Cp is never
  measured directly; shaft power is inferred through the fitted motor model (3.4 D).
- MT10PRO accuracy is unpublished. "Down to the gram" is display resolution, not accuracy, and no
  V or A accuracy is listed at all. The Run 0 hanging-mass calibration (and the multimeter and clamp
  meter checks) are the only accuracy statement this test has. Report them with the results.
- Time resolution is set by the MT10PRO display update rate (measured in Run 0.5), not by the
  60 fps video. If the display updates only a few times per second, the D3 droop curve is coarse.
  Transcribing numbers from video frames can also introduce reading errors, so spot-check a sample.
- Audio RPM needs one dominant prop. In D5 two motors run at slightly different RPM and give two
  close blade-pass peaks, so D5 RPM comes from the optical tach on each motor, not from audio.

---

## 7. Adjacent items, NOT included in this plan

Listed for Jordan to decide on, not done unprompted:

1. Proof-load the panel after weighing. Once the panel exists, a sandbag or water-jug load to the
   n = 3.0 design limit (weight.py:31) would retest SPRUCE_ALLOW = 3700 psi and N_DESIGN, both
   [INFERRED], for the cost of an afternoon and one destroyed panel. High value, but it is a
   separate test with its own rig and its own safety case, and it destroys the article T-1 just
   measured. Build a third panel if this is wanted.
2. Static thrust in ground effect versus clear of it. The aircraft takes off in ground effect and
   the stand will have some. Cheap to bracket by raising the stand.
3. Rolling-friction measurement (MU_R = 0.04, takeoff.py:29) by towing the finished gear on the
   actual runway surface with a fish scale. Small effect, about +/- 0.6 lb of W_TO_max, but nearly
   free once the gear exists.
