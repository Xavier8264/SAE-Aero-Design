# TEST PLAN -- T-1 Wing Panel Weigh-In, T-2 Static Thrust Stand

Version 1.0, written 2026-09-20. Status: NOT YET RUN.
Audience: whoever builds and runs these in the shop. Read section 1, then your test.

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
| airfoil | S1223 | design_card.txt |
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

That last number is the specific thing to watch. The S1223 section area coefficient is 0.0649
(computed with aerosandbox), so a 26 in chord rib has a section area of 43.9 in^2. In 1/8 in stock
that gives:

| stock density | solid rib | 30 pct lightened | 40 pct lightened |
|---|---|---|---|
| 6 lb/ft^3 | 8.6 g | 6.0 g | 5.2 g |
| 8 lb/ft^3 | 11.5 g | 8.1 g | 6.9 g |

So a real rib should land somewhere between about 5 and 11 g, while the model implies 23.7 g.
That is a factor of 2 to 4. Either A_WING1 is badly overestimated, or it is silently absorbing
capstrips, shear web and rib doublers that the model does not name anywhere else. The panel
settles which. If A_WING1 really is that high, the wing is lighter than modeled and payload goes
UP. Finding that is worth far more than the panel costs.

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

Measure static thrust, RPM, battery current and pack sag for the two candidate 12 in props on a
real 4S 2200 pack, and use the result to calibrate four separate things the current model guesses:

| what | current value | where |
|---|---|---|
| prop model error | THRUST_FACTOR = 0.93 | takeoff.py:33 |
| motor constants | Rm 0.028 ohm, I0 1.8 A | propulsion.py:43 |
| pack model | V_OC_TO 16.0 V, R_BATT 0.025 ohm | propulsion.py:35-37 |
| propulsion group mass | 1.68 lb | weight.py:38 |

### 3.2 Test articles

- Props: APC 12x6E and APC 12x8E. These are the top two 2-motor candidates in
  `out/takeoff_summary.txt` (W_TO_max 31.5 and 31.1 lb).
- Motors: 800-900 Kv outrunners in the 42xx-50xx class. The design point matched Kv 843 for the
  12x6E and Kv 748 for the 12x8E (design_card.txt, takeoff_summary.txt). Buy what is actually
  available near 843, record the vendor Kv, then MEASURE it, because vendor Kv is routinely off by
  5 to 10 percent [INFERRED].
- Test two motors of the same model, not one. Motor-to-motor scatter matters when both run off one
  pack.
- Battery: the 4S 2200 mAh pack intended for competition, plus a second identical pack so testing
  continues while one charges.
- ESC: the ESC intended for competition, with its actual wiring, connectors and lead lengths. The
  wiring is part of R_BATT.

### 3.3 Equipment

| item | requirement | calibration check |
|---|---|---|
| thrust stand | load cell 10 kg (22 lbf) rated, single-point or S-beam, loaded in line with the thrust axis at 1:1. See 3.3.1 for the sizing. Rigid, thrust line horizontal and perpendicular to the cell axis | hang known masses (0.5, 1, 2, 3 kg) on the thrust axis before and after each session; record the calibration points in the CSV, do not just trust the tare |
| wattmeter or shunt | 0-150 A continuous, logs V and A at 10 Hz or better | cross-check against a DC clamp meter at one operating point |
| tachometer | optical, 2-blade setting, or ESC eRPM telemetry with the pole count | cross-check optical against telemetry at one point; LED shop lighting can alias an optical tach |
| cell voltage readout | per cell, at rest and after load | |
| thermometer, barometer, hygrometer | for air density | |
| IR thermometer | motor can and pack temperature | |
| logging | 10 Hz or better; hand-written point readings are acceptable ONLY for steady part-throttle points, never for the burst test | |

### 3.3.1 Load cell sizing

Worst-case static thrust PER MOTOR across every 2-motor candidate in
`analysis/sizing/out/prop_candidates.csv`, at the high current sensitivity case (110 A peak),
model values at DA 1400 ft:

| prop | 70 A | 90 A | 110 A |
|---|---|---|---|
| 12x6e  | 5.75 | 6.62 | 7.30 |
| 12x8e  | 5.37 | 6.20 | 6.88 |
| 11x7e  | 5.18 | 5.98 | 6.62 |
| 12x10e | 4.87 | 5.67 | 6.33 |
| 11x10e | 4.45 | 5.19 | 5.80 |
| 12x12e | 4.41 | 5.16 | 5.78 |

(4-motor candidates are lower, about 3.2 lbf per motor, and would be tested one at a time.)

- Maximum expected, one motor: **7.3 lbf (3.3 kg)**, the 12x6E at 110 A.
- Design the rig to **10 lbf (4.5 kg)** to cover model error. THRUST_FACTOR could come out above
  1.0, denser air than DA 1400 adds a few percent, and spin-up is a transient.
- **Buy a 10 kg (22 lbf) cell.** Peak load then sits near 33 percent of rating, which leaves room
  for a mishandled rig or a prop strike. A 5 kg cell would put 7.3 lbf at 66 percent of rating,
  which is fine on resolution but leaves little overload margin.
- If both motors are ever mounted on ONE stand (not required by this plan, Run D5 measures thrust
  on one motor at a time), that doubles to about 14.6 lbf and needs a 20 kg cell.

Resolution is not the binding constraint. The measurement needs to resolve about 1 percent of
6.5 lbf, which is 0.065 lbf or 30 g, and a 10 kg cell on a 24-bit HX711 resolves far better than
that even with realistic noise. Rigidity, alignment and overload survival are what actually limit
the measurement, so spend the effort there.

SAMPLE RATE, check before buying: the HX711 runs at 10 or 80 samples/s depending on its RATE pin,
and many cheap breakout boards tie that pin to ground for 10 SPS [INFERRED from the HX711
datasheet; verify on the specific board]. 10 SPS is exactly the minimum this plan asks for and
leaves no margin for the D3 droop test. Either pick a board that exposes RATE, cut the trace to
select 80 SPS, or use an ADC that samples faster. Confirm the actual achieved rate by logging a
known step before trusting a run.

A bare digital scale (kitchen or luggage type) will NOT do the whole job. It cannot log at 10 Hz,
so it cannot measure the thrust droop in D3 or give the V-versus-I trace that R_BATT is fitted
from. It is usable only for steady full-throttle point readings. The load cell plus HX711 plus a
microcontroller route is both cheaper and the only one that meets the requirement.

### 3.4 Methodology, read this before running anything

Two rules make this test worth doing.

1. MEASURE THRUST AND RPM TOGETHER, ALWAYS. The APC data is Ct and Cp versus (RPM, J)
   (propulsion.py:53-79). Comparing measured thrust against the APC table AT THE SAME MEASURED RPM
   isolates propeller model error. Comparing at the same throttle setting confounds prop error with
   motor error, battery error and ESC error, and yields a THRUST_FACTOR that means nothing.

2. TAKE THE MODEL-CRITICAL POINTS AT 100 PERCENT THROTTLE. At full throttle the ESC is effectively
   a closed switch, so V_motor = V_batt and the Drela first-order model applies directly
   (drela_motorprop eqs 1-2: Qm = (i - i0)/Kv, Omega = (v - i*R)*Kv). At part throttle the ESC is
   chopping and the effective motor voltage becomes an extra unmeasured quantity. Vary the LOAD by
   changing props, not by changing throttle. Part-throttle points are still recorded, because the
   mission energy model needs them, but they are tagged lower confidence.

This test is static only (J = 0). It cannot measure thrust lapse with airspeed, which is what
actually sets the takeoff distance at V_R. Section 6 says what to do about that.

### 3.5 Procedure

Run A -- component weights (10 minutes, do it first, it is free)

- A1. Weigh each of: motor, ESC, prop, spinner or safety nut, motor mount, motor wiring run,
  battery pack, arming plug and its leads, receiver, each servo.

  -> `analysis/tests/data/t2_masses.csv`   columns: item, mass_g, notes

Run B -- battery characterization

- B1. Charge the pack to full, rest 30 minutes, measure per-cell resting voltage. This is V_oc.
- B2. During the Run D bursts, capture V_batt and I_batt at 10 Hz or better. R_BATT is fitted as
  the slope of V_batt versus I_batt.
- B3. Immediately after each burst, measure pack temperature and per-cell voltage.
- B4. Repeat B1 on a pack at about 50 percent charge, for the mid-mission voltage (V_OC_CRUISE,
  currently the guess 15.2 V, propulsion.py:36).

Run C -- motor constants

- C1. No prop, 100 percent throttle: record RPM, current, voltage. This gives I0 at high RPM and a
  first estimate of Kv = RPM / V_motor.
- C2. Small load (a 9x6 or similar, if one is on hand), 100 percent throttle: RPM, current, voltage.
- C3. The two test props at 100 percent throttle (that is Run D) are the high-load points.
- C4. Rm is fitted across all of C1 to C3 from Omega = (v - i*Rm)*Kv. Do NOT do a locked-rotor
  test; it dumps full current into a stalled motor and cooks the windings.
- C5. Repeat for BOTH motors separately.

  -> `analysis/tests/data/t2_motor.csv`
  columns: run_id, motor_id, prop, throttle_pct, rpm, I_A, V_batt_V, T_lbf, temp_F, notes

Run D -- static thrust, the main event

For each prop (12x6E, 12x8E) and each motor:

- D1. Fresh pack. Spin up to 100 percent throttle, hold 6 seconds, log at 10 Hz or better. Cut
  throttle.
- D2. Cool down 2 minutes. Repeat. 3 runs per (prop, motor) combination, so 2 props x 2 motors x 3
  runs = 12 full-throttle runs.
- D3. Takeoff duplicate: one run per prop at 100 percent throttle held for 5.0 seconds (the model
  predicts a 4.5 s ground roll, design_card.txt), logged at 10 Hz or better, from a fresh pack.
  What matters here is the DROOP: thrust at t = 0.5 s versus t = 4.5 s. The takeoff model assumes
  constant open-circuit voltage through the roll, and that is optimistic.
- D4. Part-throttle map, lower confidence: 50, 60, 70, 80, 90 percent throttle, 1 run each, 5 s
  hold, both props, one motor. Used for the circuit-energy model, which predicts 38 A level,
  48 A in turns, 1.38 Ah of 1.76 usable (design_card.txt).
- D5. Both motors on one pack, 100 percent throttle, 5 s, one run per prop. This is the real
  aircraft configuration and the only way to see true pack sag at about 90 A total. Thrust is only
  measurable for one motor at a time on a single-cell stand, so measure RPM on both and thrust on
  one.

  -> `analysis/tests/data/t2_thrust.csv`
  columns: run_id, timestamp_s, prop, motor_id, n_motors_live, throttle_pct, T_lbf, rpm, I_A,
  V_batt_V, temp_F, temp_air_F, press_inHg, rh_pct, notes

Total: about 25 runs, one afternoon with two people, plus charging time between packs.

### 3.6 Data reduction

Write `analysis/tests/reduce_thrust.py`. It computes:

1. Air density from temperature, pressure and humidity (nws_density_altitude_formula).
2. For each steady full-throttle point: T_apc = Ct(rpm, J=0) * rho * n^2 * D^4, using the same
   `parse_apc` and `coeffs` functions already in propulsion.py:53-90. Reuse them, do not rewrite
   them.
3. THRUST_FACTOR_meas = mean(T_measured / T_apc) over all full-throttle points, with the standard
   deviation reported. Report it per prop. If the two props disagree by more than a few percent,
   say so rather than averaging it away.
4. Kv, I0 and Rm fitted from the Run C points by least squares on the Drela relations.
5. R_BATT from the slope of V_batt versus I_batt in Run D.
6. Thrust droop ratio from D3: T(4.5 s) / T(0.5 s).

### 3.7 Acceptance and decision gates

| outcome | reading | action |
|---|---|---|
| THRUST_FACTOR in 0.90 to 1.00 | the APC data holds up | set the measured value, narrow the takeoff band |
| THRUST_FACTOR below 0.85 | prop or stand is underperforming | check the stand first (rigidity, alignment, bench blockage). If it is real, W_TO_max drops about 1.4 lb and the design point needs revisiting |
| measured Kv off the vendor figure by more than 10 percent | normal, but it moves the operating point | use the measured Kv in propulsion.py and rerun the prop ranking; the ordering of props can change |
| peak total current above 100 A | above the 90 A design assumption | reduce I_DESIGN, re-match Kv, accept less static thrust. Do not fly a pack past its rating for a 2 lb payload gain |
| V_batt under load below 12.8 V (3.2 V/cell) | pack sag worse than modeled | same action; also revisit V_OC_TO = 16.0 V, which is optimistic |
| thrust droop over 4.5 s worse than 10 percent | takeoff model is optimistic | add the droop to takeoff.py as a time-dependent thrust factor, not a constant |
| pack or motor above about 140 F after a burst | thermal limit reached | stop, reduce current, record it as a hard constraint on I_DESIGN |

### 3.8 Feedback into the code

| # | file | constant | replace with |
|---|---|---|---|
| 1 | analysis/sizing/takeoff.py:33 | THRUST_FACTOR = 0.93 | measured, per prop |
| 2 | analysis/sizing/propulsion.py:43 | MOTOR_CLASS[2] Rm, I0 | measured |
| 3 | analysis/sizing/propulsion.py:43 | m_motor_lb, m_esc_lb, m_prop_lb, m_mount_lb | Run A weights |
| 4 | analysis/sizing/propulsion.py:35 | V_OC_TO = 16.0 | measured loaded-fresh value |
| 5 | analysis/sizing/propulsion.py:36 | V_OC_CRUISE = 15.2 | measured at 50 percent charge |
| 6 | analysis/sizing/propulsion.py:37 | R_BATT = 0.025 | fitted slope |
| 7 | analysis/sizing/propulsion.py:38 | I_DESIGN = 90.0 | confirmed or reduced per the gates above |
| 8 | analysis/sizing/propulsion.py:100 | Kv from match_kv() | allow an override with the measured Kv of the motor actually bought; keep match_kv for trade studies |
| 9 | analysis/sizing/weight.py:34, 38 | BATTERY_LB 0.55, PROP_GROUP_DEFAULT 1.68 | Run A weights |
| 10 | analysis/sizing/propulsion.py docstring lines 18-24 | "all [UNVERIFIED] until thrust-stand tests" | retag [VERIFIED] with the data file path and date |

Then rerun:

    python analysis/sizing/propulsion.py
    python analysis/sizing/takeoff.py
    python analysis/sizing/sweep.py
    python analysis/sizing/design_card.py

and diff design_card.txt. The prop choice itself is in play: 2x12x6e and 4x9x45e are separated by
0.1 lb of W_TO_max in the current model, which is far below the model's own error.

---

## 4. Safety

- LiPo: charge and store in a fire-safe container, never unattended. Inspect for puffing before
  every run. A 4S 2200 at 90 A is a 40C discharge. Reference: nasa_liion_guidelines.
- Props: nobody in the plane of rotation, ever, including the person holding the throttle. Use a
  physical barrier. Eye protection for everyone in the room.
- The motor and stand are bolted down before the pack is connected. The pack is connected last and
  disconnected first.
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
3. T-1 Phases B and C (build and weigh) and T-2 Runs B through D, in parallel if two people.
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
