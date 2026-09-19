# ID: data_readme
# SOURCE: (local file)
# ORIGINAL: reference/data/README.txt
# CONVERTED: 2026-09-18 21:23 UTC-0500 | type txt | 1 pages | ~308 tokens
# NOTE: Index of raw datasets in reference/data (KLAL hourly weather 2021-2026). Read this, then parse the CSV with a script

=== PAGE 1 ===
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
