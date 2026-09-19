# Reference library: topic map (read this, not the whole INDEX)

118 documents, about 2.9M tokens in total. NEVER read a document whole: grep `reference/text/<ID>.txt` and read
line ranges. INDEX.md has every ID with its size, flags and source. Written 2026-09-18; add new IDs here when you
archive something important.

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
- GAP: no free takeoff-roll textbook chapter (the Stanford AA241 site is offline). Integrate
  m dV/dt = T(V) - D - mu(W - L) using APC T(V) data.

## Airfoils and aerodynamics
- Coordinates (Selig .dat): airfoil_s1223, airfoil_s1223rtl (lower Cm), airfoil_s1210 (thicker), airfoil_e423,
  airfoil_fx74cl5140, airfoil_ch10sm, airfoil_sd7062, airfoil_naca4412; tails: airfoil_sd8020, airfoil_naca0012.
- selig_guglielmo_1997 (the S1223 paper), selig_lowre_lecture (low-Re design principles).
- Wind-tunnel polars: uiuc_lsat_vol1 (S1223 p.214-217, S1210, CH10, FX74, SD8020), uiuc_lsat_vol2 (E423, S1223RTL),
  uiuc_lsat_vol3 (SD7062). These are PLOTS: text extraction is poor, so RENDER the pages
  (`python tools/doc2text.py render uiuc_lsat_vol1 <PDF page>`; printed page != PDF page, grep the page marker labels).
- Tools: aerosandbox_readme, neuralfoil_readme, avl_doc, xfoil_doc, xflr5_part1_theory / part2_inviscid /
  part3_viscous, vspaero_tutorial.
- CFD (later): openfoam_user_guide, openfoam_airfoil2d_allrun, fluidx3d_readme.

## Propulsion and electrical
- APC data (PARSE WITH SCRIPTS; ~30-56k tokens each): apc_12x6e, apc_12x8e, apc_12x10e, apc_12x12e, apc_11x7e,
  apc_11x10e, apc_9x6e, apc_9x45e, apc_9x75e, apc_6x4e, apc_6x55e. Format: apc_performance_data_page, apc_engineering.
  RPM limits: apc_rpm_limits (important with no power limiter). The APC site needs a browser UA + Referer to download.
- drela_motorprop (KEY: motor model Kv/Rm/I0 and matching), qprop_theory, qprop_doc, qmil_doc.
- uiuc_propdb, brandt_selig_2011 (measured low-Re prop data; cross-check for APC).
- Battery: nasa_uav_battery_model (LiPo sag under load), nasa_liion_guidelines (background).
- sjsu_propulsion_sizing (worked Kv/ESC/battery matching example).
- Servo sizing (required by the rules): basicairdata_servo_sizing (KEY, RC method), nasa_tm78664_hinge_moment.

## Structures and materials (no FRP allowed)
- wood_handbook_ch5 (KEY: Table 5-3a Sitka spruce, 5-3b balsa and basswood), ch12 (plywood properties),
  ch10 (adhesives), ch8 (fasteners), ch11 (plywood background).
- anc18_wood_aircraft: classic wood aircraft design (spar caps, shear webs, glue joints). OCR text, 119k tokens.
- aerotoolbox_wing_spar (spar cap / shear web method).
- balsa_strength_vs_density (hobbyist; cross-check with Wood Handbook).
- aluminum_6061, aluminum_7075 (joiners, fittings).
- prusament_pla_tds, prusament_petg_tds, colorfabb_lwpla_tds, fdm_infill_orientation (printed parts).

## Competition site and the TDS prediction curve
- klal_airnav (elevation 141.8 ft, runways), noaa_lakeland_normals (March Tmax 80.2 F, Tmin 56.5 F),
  klal_windrose, nws_density_altitude_formula (KEY equations), nws_density_altitude_calc.
- Raw data: reference/data/klal_asos_2021-03_to_2026-04.csv (hourly KLAL weather; see data_readme).

## Precedent (other teams)
- Same 2026 bottle mission: nau_2026_report2 (preferred), nau_2026_report1 (earlier draft), nau_2026_poster (render it).
- Older Regular Class (different missions; use for METHODS such as payload prediction and takeoff analysis):
  famu_fsu_2020_report, famu_fsu_2021_report (canard), nau_2018_report (72 in span, 18.6 lb empty), nyu_2018_report,
  nau_2019_report, nau_2021_report, nau_2025_report.
- GAP: no public 2026 reports from the top teams (Warsaw, Concordia, TAMU, Poznan, NUAA).

## Claude Code itself (workflow and settings)
- cc_* docs (costs, prompt_caching, model_config, sub_agents, commands, settings_reference, env_vars, hooks, ...).
  Several are huge (env_vars 124k, settings_reference 111k, hooks 82k tokens): grep only.
