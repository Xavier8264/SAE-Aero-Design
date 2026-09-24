# Reference library: topic map (read this, not the whole INDEX)

138 documents, about 4.1M tokens in total. NEVER read a document whole: grep `reference/text/<ID>.txt` and read
line ranges. INDEX.md has every ID with its size, flags and source. Written 2026-09-18, extended 2026-09-19;
add new IDs here when you archive something important.

## Design process and systems engineering (added 2026-09-19)
- vt_aoe_a5_initial_sizing, vt_aoe_a7a_config_layout, vt_aoe_a10_prelim_design: Virginia Tech AOE 4065/4066
  course notes (Raj). The phased method: initial sizing -> configuration layout and loft -> preliminary design
  refinement and validation. Heavily figure-based; many pages are flagged img/lowtext, so render when the text thins out.
- mit_1682_flight_vehicle_intro: MIT 16.82 capstone framing of the design process (short, 15 pp).
- nasa_se_handbook: NASA SP-2016-6105 Rev2. Requirements and decision traceability. 262k tokens, GREP ONLY.

## Rules and competition (official = highest authority)
- rules_2027 (OFFICIAL; Regular = printed p.33-36; TDS p.26; flight ops p.17-20). rules_2026 is for comparison only.
- faq_394 (bottle count), faq_393 (TDS breakpoints), faq_395 (prop diameter = sum per motor), faq_382 (ground
  steering), faq_170 (AMA pilot), faq_157 (sae.org affiliation), faq_list (re-fetch to check for new FAQs).
- results_2026_east / _west (placings only). uw_2026_rule_summary (unofficial, has an error).

## Payload
- dimensions_2l_bottle, wiki_two_liter_bottle (4.33 in dia x 12.4 in typical). Filler analysis is in PROJECT_MEMORY.md.

## Sizing, performance, takeoff (start here for conceptual design)
- drela_design_rules: rules of thumb (wing loading, CLmax, tail volumes, static margin). Short; OK to read whole.
- nicolai_rc_model_aero: written for SAE Aero; RC drag polar, Re effects, performance. 13 pp.
- mit_airpower (thrust/power/velocity), mit_prop_appendix (measured small-prop thrust vs speed),
  nasa_grc_propeller_thrust (momentum theory), nasa_ground_effect_propellers (limited relevance).
- scholz_tail_volume: Vh/Vv sizing method and typical ranges.
- GAP: no free takeoff-roll textbook chapter (the Stanford AA241 site is offline; adg.stanford.edu no longer
  resolves, re-confirmed 2026-09-19). Integrate m dV/dt = T(V) - D - mu(W - L) using APC T(V) data.
- nasa_takeoff_flighttest_method: NASA TN D-7603, simplified flight-test method for takeoff performance,
  INCLUDING the effect of pilot technique. Directly relevant: the sizing found rotation technique (k_R) is
  one of the largest levers on payload. Scanned; all pages flagged img, OCR is readable but check numbers.

## Airfoils and aerodynamics
- Coordinates (Selig .dat): airfoil_s1223, airfoil_s1223rtl (lower Cm), airfoil_s1210 (thicker), airfoil_e423,
  airfoil_fx74cl5140, airfoil_ch10sm, airfoil_sd7062, airfoil_naca4412; tails: airfoil_sd8020, airfoil_naca0012.
- selig_guglielmo_1997 (the S1223 paper), selig_lowre_lecture (low-Re design principles).
- Wind-tunnel polars: uiuc_lsat_vol1 (S1223 p.214-217, S1210, CH10, FX74, SD8020), uiuc_lsat_vol2 (E423, S1223RTL),
  uiuc_lsat_vol3 (SD7062). These are PLOTS: text extraction is poor, so RENDER the pages
  (`python tools/doc2text.py render uiuc_lsat_vol1 <PDF page>`; printed page != PDF page, grep the page marker labels).
- Tools: aerosandbox_readme, neuralfoil_readme, avl_doc, xfoil_doc, xflr5_part1_theory / part2_inviscid /
  part3_viscous, vspaero_tutorial, openvsp_user_manual (parametric geometry, feeds VSPAERO).
- CFD (later): openfoam_user_guide, openfoam_airfoil2d_allrun, fluidx3d_readme, su2_quick_start (alternative
  solver), gmsh_reference_manual (meshing; 298k tokens, GREP ONLY), paraview_docs (index page only, browse the site).
- VALIDATION GAP (searched 2026-09-19, nothing found): no published study comparing AVL / XFLR5 / VSPAERO /
  OpenFOAM against wind-tunnel data at Re 100k-500k. We have no external error band for our own predictions.
  Close it ourselves: run our tools against the uiuc_lsat_* polars we already hold (COMPUTE_BACKLOG T1-1).

## Propulsion and electrical
- APC data (PARSE WITH SCRIPTS; ~30-56k tokens each): apc_12x6e, apc_12x8e, apc_12x10e, apc_12x12e, apc_11x7e,
  apc_11x10e, apc_9x6e, apc_9x45e, apc_9x75e, apc_6x4e, apc_6x55e. Format: apc_performance_data_page, apc_engineering.
  RPM limits: apc_rpm_limits (important with no power limiter). The APC site needs a browser UA + Referer to download.
- drela_motorprop (KEY: motor model Kv/Rm/I0 and matching), qprop_theory, qprop_doc, qmil_doc.
- uiuc_propdb, brandt_selig_2011 (measured low-Re prop data; cross-check for APC).
- Battery: nasa_uav_battery_model (LiPo sag under load), nasa_liion_guidelines (background).
- sjsu_propulsion_sizing (worked Kv/ESC/battery matching example).
- HARDWARE ON HAND (2026-09-21): sunnysky_x2820_800kv_spec (KEY, read this: X2820 800 KV specs + 4S test table
  + reading notes); sunnysky_x2820_800kv (raw product page, ~47k tokens, do not read); test table as CSV in
  reference/data/sunnysky_x2820_800kv_testdata.csv. Thrust stand: mayatech_mt10pro (specs; display only, no RPM,
  no logging), mayatech_mt10pro_safety. ESC: sunnysky_esc_x60 (team ESC, X60A V2: 60 A cont, 80 A 10 s, 61 g);
  sunnysky_esc_manual (throttle calibration + defaults, but written for X45A/X65A/X85A, not the X60A).
  Test-night weather: reference/data/kmkl_asos_2026-09-24.csv.
- Servo sizing (required by the rules): basicairdata_servo_sizing (KEY, RC method), nasa_tm78664_hinge_moment.

## Structures and materials (no FRP allowed)
- wood_handbook_ch5 (KEY: Table 5-3a Sitka spruce, 5-3b balsa and basswood), ch12 (plywood properties),
  ch10 (adhesives), ch8 (fasteners), ch11 (plywood background).
- anc18_wood_aircraft: classic wood aircraft design (spar caps, shear webs, glue joints). OCR text, 119k tokens.
- aerotoolbox_wing_spar (spar cap / shear web method).
- balsa_strength_vs_density (hobbyist; cross-check with Wood Handbook).
- aluminum_6061, aluminum_7075 (joiners, fittings).
- prusament_pla_tds, prusament_petg_tds, colorfabb_lwpla_tds, fdm_infill_orientation (printed parts).
- Loads: nasa_vgh_load_factor_stats (NASA CR-132531, statistical general-aviation VG/VGH gust and maneuver
  load factor data). Use it to justify the V-n design load factor instead of picking one. Scanned, OCR is
  rough on the tables, render pages when a number matters.
- Worked spar examples: uf_wing_spar_optimization (Univ. of Florida, 14 lb / 7 ft span RC aircraft, closest
  scale match we have, 6 pp), syracuse_wing_spar_design (senior design, full bending-moment-to-stress walkthrough).
- fpl_minimum_weight_sandwich (USDA FPL RN-086): minimum-weight sandwich design. Use this for foam-core
  sandwich work. MIL-HDBK-23 was canceled in 1988 and folded into MIL-HDBK-17, which is NOT free: do not go looking.
- FEA: calculix_manual (CalculiX 2.22, the solver behind FreeCAD FEM; 448k tokens, GREP ONLY),
  freecad_fem_workbench (tutorial, from the GitHub docs mirror; wiki.freecad.org is behind bot protection and
  cannot be fetched by script, open it in a browser), gmsh_reference_manual (see the tools list above).

## Competition site and the TDS prediction curve
- klal_airnav (elevation 141.8 ft, runways), noaa_lakeland_normals (March Tmax 80.2 F, Tmin 56.5 F),
  klal_windrose, nws_density_altitude_formula (KEY equations), nws_density_altitude_calc.
- Raw data: reference/data/klal_asos_2021-03_to_2026-04.csv (hourly KLAL weather; see data_readme).

## Flight test and operations (added 2026-09-19)
- nasa_takeoff_flighttest_method (NASA TN D-7603; see the sizing section above).
- ardupilot_airspeed_calibration: pitot / airspeed sensor calibration, for instrumented test flights.
- ama_national_safety_code: AMA doc 105, the official safety code. Short; required reading before first flight.
- GAP: no stall-speed or static-margin flight-test procedure archived yet.

## Manufacturing and build technique (added 2026-09-19)
- modelaviation_sliced_rib_method, modelaviation_diy_laser_cutting: AMA Model Aviation articles on built-up
  wing construction and cutting balsa/ply parts. MAGAZINE GRADE: cite as common practice, never as allowables.
  Allowables come from wood_handbook_ch5 / anc18_wood_aircraft.
- GAP: no covering-film or adhesive-selection source archived yet (wood_handbook_ch10 covers adhesives in general).

## Precedent (other teams)
- Same 2026 bottle mission: nau_2026_report2 (preferred), nau_2026_report1 (earlier draft), nau_2026_poster (render it).
- Older Regular Class (different missions; use for METHODS such as payload prediction and takeoff analysis):
  famu_fsu_2020_report, famu_fsu_2021_report (canard), nau_2018_report (72 in span, 18.6 lb empty), nyu_2018_report,
  nau_2019_report, nau_2021_report, nau_2025_report.
- GAP: no public 2026 reports from the top teams (Warsaw, Concordia, TAMU, Poznan, NUAA).

## Claude Code itself (workflow and settings)
- cc_* docs (costs, prompt_caching, model_config, sub_agents, commands, settings_reference, env_vars, hooks, ...).
  Several are huge (env_vars 124k, settings_reference 111k, hooks 82k tokens): grep only.
