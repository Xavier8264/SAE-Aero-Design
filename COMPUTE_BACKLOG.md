# Dedicated compute backlog (always-on mini PC)

Written 2026-09-19. Brainstorm only: no scripts exist yet for any item below.
Machine: GMKtec NucBox M6 Ultra, AMD Ryzen 5 7640HS (6 cores / 12 threads, Zen 4, 4.3 GHz base,
5.0 GHz boost, 16 MB L3, 35-54 W), 32 GB RAM, 512 GB SSD, Radeon 760M iGPU (8 RDNA3 CUs).
[VERIFIED: AMD product page / TechPowerUp, 2026-09-19]

## Compute budget (order of magnitude, [INFERRED] from the specs above)

| Workload class                          | Cost per run | Runs per 24 h on this box |
|-----------------------------------------|--------------|---------------------------|
| Analytic eval (takeoff integration, weight+aero+score model) | ~1 ms | ~1e9 |
| NeuralFoil airfoil polar point          | ~1 ms        | ~1e9                      |
| AVL run (trim + stability, one config)  | ~0.05-0.5 s  | ~2e6 - 2e7                |
| XFOIL alpha sweep (one airfoil, one Re) | ~5-30 s      | ~3e4 - 2e5                |
| OpenFOAM 2D RANS airfoil (~1e5 cells)   | ~5-15 min    | ~100-300                  |
| OpenFOAM 3D RANS half-aircraft (~5e6 cells) | ~8-20 h  | ~1-2                      |

Implication: anything built on the analytic model or NeuralFoil is effectively free at
sweep scale; XFOIL farms are an overnight job; 3D CFD is one case per day and should be
reserved for questions AVL and 2D polars genuinely cannot answer.

## Tier 1: highest value per compute hour

### T1-1. Model validation harness (RUN THIS FIRST)
Before any long sweep, make the models reproduce known answers. Re-predict the NAU 2026
aircraft (80 in span, 12.2 lb empty, same bottle mission) and the older Regular Class
reports in reference/, and reproduce UIUC LSAT wind-tunnel polars with XFOIL/NeuralFoil at
matching Re and Ncrit. Sweep Ncrit and the transition/roughness settings until the
airfoil model matches the tunnel data, then freeze those settings.
Long-running because: it is a sweep over solver settings x airfoils x Re, with an error
metric per combination. Perhaps 4-12 h.
Why first: hours of optimization on an uncalibrated model produce a confident wrong airplane.

### T1-2. Payload-ladder and TDS strategy optimization (stochastic dynamic program)
The scoring rules make this a decision problem, not an aerodynamics problem:
FS = 3*EB + 11*FB, FFS = mean(top 3 FS) + PPB, PPB = max(10 - (FS - PS)^2, 0), every scored
flight must add payload, and total bottle count can never decrease.
Build an MDP over state (flights remaining, bottles loaded, successes so far, scores banked)
with per-configuration success probability from T1-3, solve for the optimal ladder policy,
and sweep the declared TDS score PS to maximize expected FFS.
Long-running because: solve the DP for every PS, every success-probability model, every
assumed number of available flight rounds, and every candidate airplane from T1-4.
Outputs: the number to write in the TDS, and a printed decision card for the flight line.
Open input [UNVERIFIED]: how many flight attempts a team actually gets at EAST 2027.
Why this is worth real compute: it is pure points, the physics is cheap, and almost no team
does it quantitatively. The quadratic PPB term means guessing PS wrong by two bottles is
worth zero.

### T1-3. Robust takeoff: Monte Carlo over the 100 ft constraint
Integrate m dV/dt = T(V) - D - mu(W - L) to liftoff, then propagate uncertainty:
empty weight (+/- 15%), CLmax at rotation, ground-roll mu, prop thrust vs APC data,
4S 2200 mAh voltage sag, headwind and density altitude drawn from
reference/data/klal_asos_2021-03_to_2026-04.csv filtered to March daytime hours, pilot
rotation technique, tail-lift and rotation dynamics (often the real binding constraint,
not raw thrust).
Output: P(airborne within 100 ft) as a function of payload, for each candidate design.
That probability field is the input to T1-2.
Long-running because: ~1e4 MC samples x ~1e5 candidate designs x ~1 ms = order 1 day.

### T1-4. Full-factorial design-space map, not a single optimum
Grid or space-fill over span, area/AR, taper, airfoil choice, empty weight fraction,
2 vs 4 motors, prop/Kv, tail volume, CG, bottle count and layout. Score every point with
the calibrated model plus the T1-3 robustness metric and the T1-2 expected FFS.
Eight variables at ten levels is 1e8 evaluations, about 2-3 h at 1 ms/eval on 12 threads.
Deliverable is a map, not an answer: where the score plateau is wide (insensitive to build
error) matters more for a first-year team than where the sharp peak is. Follow with
NSGA-II or CMA-ES multi-start in the promising regions and check the optimizer lands
inside the plateau the grid found.

### T1-5. Weight-driven structural optimization with material scatter
Empty weight is the whole game: every pound saved is roughly a third of a bottle.
Optimize spar cap area distribution, web thickness, rib spacing and D-tube geometry for
minimum weight at limit load, with buckling, glue-joint and deflection margins, using
Wood Handbook properties (no FRP allowed). Layer a Monte Carlo over balsa density scatter
(a 4x range in the literature) and spruce grain variability, so the answer is a design that
survives the wood you actually get rather than the wood in the table.
Long-running because: MC x a few hundred structural layouts x load cases; optionally
CalculiX FEA on the shortlist overnight.

## Tier 2: strong value, clear compute use

### T2-1. Airfoil polar farm and airfoil shape optimization
Farm: XFOIL over the 10 archived airfoils x Re 150k-600k x Reynolds-consistent Ncrit x
roughness x flap deflections, with convergence retries, cached into interpolated tables
that every other tool reads. One overnight run, used for the rest of the project.
Optimization: CST or Bezier parameterization searched with NeuralFoil (fast, differentiable)
for max CL at Re ~300k, constrained on Cm (tail load and trim drag), thickness (spar depth),
trailing-edge thickness (buildable in balsa) and stall gentleness, then verified in XFOIL.
Multi-start over hundreds of initial shapes = hours. Treat the result with suspicion:
a shape that beats S1223 on paper and cannot be built or flown is worth nothing.

### T2-2. Propulsion combinatorics
Every combination of (prop from the 11 archived APC datasets and the wider catalog) x
(motor Kv, Rm, I0) x (2 vs 4 motors, respecting the sum-of-diameters limit per FAQ 395) x
(battery sag model, no power limiter, APC RPM limits as a hard constraint), scored on the
100 ft takeoff and on whether a 2200 mAh 4S pack completes the full mission with reserve.
Long-running because: combinatorics x the T1-3 Monte Carlo. Output is a shortlist to buy
and then verify on the thrust stand, which closes the loop into T3-2.

### T2-3. AVL sweeps: trim, stability, control authority, gust response
Thousands of configurations: tail volumes, tail arm, dihedral, washout, CG range across
every loading state. Check static margin, elevator authority at rotation speed with a very
high CL wing, spiral and dutch-roll modes, and crosswind response weighted by the KLAL wind
rose. Produces a feasible box for the tail rather than a single point design.

### T2-4. Bottle packing and CG across the whole ladder
Enumerate bay layouts (upright, lying, staggered, rows) against bottle dimensions,
fuselage cross-section, the 120 in length limit, and the 60 s two-person unload rule.
The hard constraint is that CG must stay acceptable for every loading state you will fly,
including mixed empty/filled configurations as the ladder grows. Combinatorial search over
layouts x loading sequences, scored on frontal area, structure weight and CG travel.

### T2-5. Mission energy and trajectory simulation
3-DOF simulation of the actual pattern: airborne within 100 ft, one 360 degree circuit,
land within 400 ft, same direction. Verify the energy budget from 2200 mAh at 4S with sag
and reserve, and optimize the climb and turn profile. Monte Carlo over wind and pilot
variance. Confirms or kills designs that pass takeoff but cannot fly the pattern.

### T2-6. Cross-validation of independent models
Run two independent implementations (own integration vs AeroSandbox, XFOIL vs NeuralFoil
vs UIUC tunnel data, own weight buildup vs statistical regressions from the precedent
reports) across the whole sweep space and flag every region where they disagree by more
than a threshold. Cheap per point, exhaustive over the space, and it catches modelling
errors before they cost an airplane.

## Tier 3: speculative or lower priority

### T3-1. CFD, used narrowly
- 2D OpenFOAM RANS with a transition model, as an independent check on XFOIL at Re 200-500k.
  ~100-300 cases/day, so a batch of settings studies runs overnight.
- 3D RANS for what AVL cannot do: ground effect during the roll, wing-fuselage junction
  drag, propwash over the wing. About one case per day at ~5e6 cells in 32 GB, so pick
  the two or three questions that are actually worth a day each.
- FluidX3D on the 760M iGPU (OpenCL LBM). Rough bandwidth estimate: DDR5-5600 dual channel
  is ~90 GB/s theoretical, call it ~60 GB/s effective; FluidX3D moves roughly 55 bytes per
  cell per step in its memory-efficient mode, so ~1e9 cell-updates/s, i.e. a 256^3 domain at
  ~60 steps/s. [INFERRED, not measured: benchmark it before trusting it.] Usable for coarse
  transient studies, not for resolving a Re 3e5 boundary layer. Experiment, not a tool the
  design depends on.

### T3-2. Surrogate models and Bayesian calibration against test data
Train surrogates (GP or gradient boosting) on the T1-4 sweep so later design changes are
instant instead of hours. As thrust stand, weight and flight test data arrive, re-calibrate
the model parameters (CLmax, mu, thrust scale factor, sag coefficients) by MCMC overnight
and re-run the downstream decisions automatically. A good use of an always-on box: the
design answer stays current with the latest measurement without anyone asking.

### T3-3. Custom propeller design (QMIL)
The FRP exception list covers commercially available props; a non-FRP custom prop appears
legal on a plain reading [UNVERIFIED, would need an FAQ]. QMIL could design one matched to
the takeoff case. High manufacturing risk for a first-year team, so treat as a stretch item
and do not let it into the baseline.

### T3-4. 3D printed part optimization
Topology or lattice optimization for bottle cradles, motor mounts and gear blocks, with
FDM print constraints and the PLA/PETG/LW-PLA data already archived. Compute is cheap;
the binding constraints are printability and layer-direction strength, so the payoff over
careful hand design is modest.

## Always-on background chores (near-zero compute, high value)

- Daily poll of the SAE FAQ list and the rules page, diffed against the archived copy, with
  an alert on any change. Rules and FAQ changes have direct design consequences.
- Nightly re-run of the whole pipeline on the current baseline design, producing a dated
  report and plots, plus regression tests so a model edit that breaks a result is caught.
- Weather/density-altitude watch: re-derive the March KLAL density altitude distribution as
  new ASOS data lands, and flag any drift in the TDS inputs.
- Build/weight tracker: every part weighed goes into a database; the empty weight estimate
  and the whole downstream score prediction update automatically.

## Setup notes

- Ubuntu Server bare metal, not WSL. tmux plus systemd units for jobs that must survive a
  reboot.
- Every job checkpoints and is resumable: write results to SQLite or Parquet incrementally,
  never hold a day of results in RAM.
- Size worker pools to 6 physical cores, not 12 threads, for memory-bandwidth-bound work
  (CFD, FEA); use all 12 for independent cheap evals.
- Thermals: a 35-54 W part in a mini PC chassis will throttle under sustained all-core load.
  Log clocks and temperatures alongside results so a slow run is not mistaken for a hard one.
- 512 GB fills fast with CFD. Write intervals matter; delete intermediate time directories.
- Results sync back into this repo (summaries and plots, not raw fields) so sessions can read
  them without re-running anything.
