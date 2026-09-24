reference/data/ -- raw datasets kept OUT of reference/text/ so they do not flood grep results.
Parse these with scripts; never read them into the conversation.

klal_asos_2021-03_to_2026-04.csv  (4.5 MB, ~68k rows)
  Hourly ASOS/METAR observations at Lakeland Linder (KLAL, IEM station LAL, network FL_ASOS),
  2021-03-01 to 2026-04-01, ALL months (filter valid month == 3 for March).
  Columns: station,valid(UTC),tmpf(F),dwpf(F),relh(%),drct(deg),sknt(kt),alti(inHg altimeter),mslp(mb),vsby(mi),gust(kt)
  Missing = M, trace = T.
  Source: https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=LAL&data=tmpf,dwpf,relh,drct,sknt,alti,mslp,vsby,gust&year1=2021&month1=3&day1=1&year2=2026&month2=4&day2=1&tz=Etc%2FUTC&format=onlycomma&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=3&report_type=4
  Use: March density-altitude distribution for the TDS prediction curve (with the NWS formula in
  reference/text/nws_density_altitude_formula.txt; field elevation 141.8 ft per klal_airnav),
  and typical March wind (headwind on takeoff).
  Note: alti is the altimeter setting, not station pressure. Station pressure ~= alti adjusted for
  field elevation; check the NWS formula doc for which pressure it expects.

sunnysky_x2820_800kv_testdata.csv  (48 rows)
  SunnySky X2820 800 KV manufacturer test table (all props and voltages published on the official page).
  Columns: kv, prop, V_nominal (V, nominal pack voltage, NOT measured under load), I_A (A), thrust_gf (gf),
  P_W (W, = V_nominal x I_A), eff_g_per_W, temp_C_100pct_prop (deg C at 100 pct throttle, given once per prop).
  The last row of each (prop, V_nominal) group is 100 pct throttle. No RPM is published.
  Source: https://sunnyskyusa.com/products/sunnysky-x2820-brushless-motors (archived as sunnysky_x2820_800kv;
  clean extract and reading notes in sunnysky_x2820_800kv_spec). Extracted 2026-09-21, verified against the
  typed table (20 rows, 0 mismatches).
  Use: cross-check for TEST_PLAN.md T-2 results and analysis/tests/predict_x2820.py.

kmkl_asos_2026-09-24.csv  (4 rows)
  Hourly ASOS/METAR at McKellar-Sipes Regional, Jackson TN (KMKL, IEM station MKL, network TN_ASOS),
  2026-09-24 00:53-03:53 UTC, the night of the first T-2 run (12x8E.MOV, 2026-09-24 01:56 UTC).
  Columns: station,valid(UTC),tmpf(F),dwpf(F),relh(%),alti(inHg altimeter),mslp(mb).
  Source: https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=MKL&data=tmpf,dwpf,relh,alti,mslp&year1=2026&month1=9&day1=24&hour1=0&year2=2026&month2=9&day2=24&hour2=4&tz=Etc%2FUTC&format=onlycomma&latlon=no&elev=no&missing=M&trace=T&direct=no&report_type=3&report_type=4
  KMKL field elevation 434.8 ft (airnav.com/airport/MKL). Test site ground 464.1 ft (USGS EPQS at 35.6750 -88.8635).
  Use: altimeter for air density in analysis/tests/data/t2_conditions.csv (read by reduce_thrust.py).
