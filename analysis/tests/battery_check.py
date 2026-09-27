#!/usr/bin/env python3
"""
battery_check.py -- was the motor limited at high throttle in a thrust-stand session, and by what?

Written for the 2026-09-25 prop session (SAE Aero Design 2027, T-2 static thrust stand). Jordan's report:
both packs seemed low, and above about 80 pct throttle the RPM sometimes dropped suddenly. This script
tests that against the video-read display (read_mt10pro_video.py), the audio RPM (audio_rpm.py) and the
callout holds (throttle_merge.py). It does not assume a cause; it reports the signatures of each:

  H1 ESC low-voltage cutoff (LVC, "reduce power" mode): a sudden step down in RPM and current at a fixed
     stick, with the voltage jumping UP (less load), and the loaded voltage just before the step near the
     cutoff (--lvc-v, default 12.0 V = 3.0 V/cell x 4, the SunnySky manual default; that manual covers the
     X45/65/85 ESCs, not the X60A V2, so UNVERIFIED for our ESC). After the motor stops, the ESC's
     low-voltage alarm: in that manual three beeps, repeated every 2 s (its only three-beep alarm; the
     protection stays latched until a new battery is connected). The alarm scan below counts these groups.
  H2 throttle endpoint (ESC range not calibrated to the radio): the effective duty stops rising at some
     stick below 100; RPM and current stay the same at higher sticks, voltage well above the cutoff; the
     thrust then only drifts down with time (pack sag, winding heating).
  H3 pack sag only: duty keeps rising with stick, RPM rises less than on a full pack. No steps.
  H4 motor desync / overload: a sudden RPM drop with the current rising or erratic.

Effective duty (fraction of the pack voltage the ESC applies to the motor):
    d = (rpm / Kv + I * R) / V
with two motor fits from the 12x8E run of 2026-09-23 (PROJECT_MEMORY, 12x8E reduction): A = Kv 809 rpm/V,
R 86.6 mOhm; B = Kv 709 rpm/V, R 44 mOhm. BOTH were fitted assuming that 12x8E top point was full
throttle, so d = 1 means "the same output as the 12x8E top point", not a measured 100 pct duty.
The comparison between holds of one run (same pack, same motor) is what matters; A and B bracket it.
The hold RPM is the median of voiced audio hops inside the hold (display clock; needs >= 3 hops).

Sudden-drop detector: voiced audio RPM in 0.1 s median bins; a drop is a >= --drop-pct fall from the median
of the previous 0.8 s to the median of the 0.8 s after a 0.2 s gap. Only counted where every "before" bin
had audio_rpm.py's thrust window (so the before level is not an octave error); off, low-thrust and unread
stretches are skipped. Checked on synthetic data: a 10 pct step injected into a steady hold is found as
9.9 pct within 0.3 s, and the untouched smoke data gives none.
Drop cross-check (v1.2, column "check"): an RPM fall by a fraction f lowers the static thrust by about
1 - (1 - f)^2 (T ~ rpm^2). If the displayed thrust fell by less than half of that, the audio tracker changed
line and the RPM did not really drop ("audio tracking artefact"; on the 2026-09-25 runs these sit in low
holds with thrust and current flat). A load shed (I down, V up) with the voltage before it >= 1 V above
--lvc-v is labelled a throttle cut; one closer to it is checked for an ESC alarm group within 10 s after
(alarm times are on the audio clock, within about 0.5 s of the display clock).

Current from P / V (v1.3): blue states whose current cell alone is unreadable get I = P_W / V_V through
throttle_merge.pv_fallback (rules and evidence in the throttle_merge.py docstring; runs column n_I_from_PV).

CSV precision (v1.4): session CSVs are written with %.6g. v1.3 used %.4g, which wrote rpm >= 10000 as
1.004e+04 and rounded times to 4 significant figures (68.838 s -> 68.84 s).

ESC alarm scan (v1.1): beeps are >= 30 ms stretches where the 2.4-2.8 + 3.3-3.7 kHz bands stand 10 dB over
the 1.5-2.2 + 4.0-4.8 kHz bands (2.5 ms hops); an alarm group is >= 3 beeps of 90-220 ms with onsets
0.30-0.50 s apart. Tuned on the 2026-09-25 videos, where both 12x10E runs end with groups of three ~150 ms
beeps 0.40 s apart every ~2.5 s (tones ~2.65 and ~3.5 kHz); it finds no group in the other three runs
(including 124 s of talking after the 9x4.5E run) or in the 2026-09-23 12x8E video. Times are on the audio
clock (seconds from the start of the audio stream).

Inputs (analysis/tests/data/): the callouts file (run list), and per run RUN_blue_states.csv, RUN_rpm.csv,
RUN_holds.csv, RUN_throttle.csv. Video creation times (ffprobe) order the runs in time.

Usage (repo root):
    python analysis/tests/battery_check.py analysis/tests/data/2026-09-25_throttle_callouts.csv
Outputs (SESSION = callouts file name before _throttle_callouts):
    analysis/tests/data/SESSION_battery_runs.csv    per run: rest voltage before and after, pack line, loaded min,
                                                    ESC alarm groups
    analysis/tests/data/SESSION_battery_holds.csv   per hold: stick, T, I, V, rpm, duty A and B
    analysis/tests/data/SESSION_rpm_drops.csv       sudden RPM drops (>= --drop-pct within about 1 s)
    analysis/tests/out/battery/                     SESSION_battery_vs_stick.png, RUN_zoom.png, log
Requires: Python 3, numpy, pandas, matplotlib; ffprobe for the run times (optional); scipy and ffmpeg for
the alarm scan (optional; --no-alarms skips it).
"""
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from throttle_merge import pv_fallback   # I = P/V where only the current cell is unreadable

SCRIPT_VERSION = "1.4"
HERE = Path(__file__).resolve().parent
FITS = {"A": (809.0, 0.0866), "B": (709.0, 0.044)}    # Kv rpm/V, R ohm (12x8E, 2026-09-23; see docstring)
BLUE_BAD = ("short", "weak_evidence", "P_ne_VxI", "bad_", "unit_glyph")   # same as throttle_merge.py
REST_I = 0.3        # A: a state below this is at rest (ESC idle)
LOAD_I = 1.0        # A: a state at or above this is loaded (pack line fit)
BIN_S = 0.1         # s: RPM median bins for the step detector
STEP_PRE, STEP_GAP, STEP_POST = 0.8, 0.2, 0.8   # s: before window, gap, after window
ALARM_BAND = ((2400, 2800), (3300, 3700))       # Hz: alarm tones (heard 2026-09-25: ~2.65 and ~3.5 kHz)
ALARM_REF = ((1500, 2200), (4000, 4800))        # Hz: neighbouring bands (motor noise, voices)
ALARM_DB = 10.0                                 # dB the alarm bands must stand over the neighbours
ALARM_LEN = (0.09, 0.22)                        # s: length of one alarm beep
ALARM_GAP = (0.30, 0.50)                        # s: onset spacing inside a group


def fnum(v):
    try:
        x = float(v)
        return x if np.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def creation_time(path):
    """'YYYY-MM-DDTHH:MM:SS-0500' from the QuickTime creation date (start of recording, UNVERIFIED), or ''."""
    try:
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                              "format_tags=com.apple.quicktime.creationdate,creation_time", "-of", "json", str(path)],
                             capture_output=True, text=True, timeout=60).stdout
        tags = json.loads(out).get("format", {}).get("tags", {})
        return tags.get("com.apple.quicktime.creationdate") or tags.get("creation_time") or ""
    except Exception:
        return ""


def esc_alarms(path):
    """Groups of >= 3 ESC alarm beeps in a video's audio (see docstring). -> list of (t_s, n_beeps), or None
    if the audio cannot be decoded."""
    from scipy.signal import spectrogram
    fs = 22050
    try:
        raw = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-vn", "-ac", "1", "-ar", str(fs),
                              "-f", "s16le", "-"], capture_output=True, timeout=600).stdout
    except Exception:
        return None
    x = np.frombuffer(raw, np.int16).astype(np.float32)
    if len(x) < fs:
        return None
    f, t, S = spectrogram(x, fs, nperseg=512, noverlap=512 - 55)

    def level(bands):
        return 10 * np.log10(S[np.any([(f > a) & (f < b) for a, b in bands], axis=0)].mean(0) + 1e-9)
    on = np.r_[False, level(ALARM_BAND) - level(ALARM_REF) > ALARM_DB, False]
    d = np.diff(on.astype(int))
    beeps = [(t[a], t[b - 1] - t[a]) for a, b in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1))]
    groups = []
    for t0, ln in beeps:
        if not ALARM_LEN[0] <= ln <= ALARM_LEN[1]:
            continue
        if groups and ALARM_GAP[0] <= t0 - groups[-1][-1] <= ALARM_GAP[1]:
            groups[-1].append(t0)
        else:
            groups.append([t0])
    return [(float(g[0]), len(g)) for g in groups if len(g) >= 3]


def rpm_bins(rp, lag):
    """Voiced audio RPM on the display clock (t_s - lag), as BIN_S medians (bins with >= 2 hops), and whether
    the bin had audio_rpm.py's thrust window (octave pinned by the displayed thrust; all True for a v1.0 file)."""
    v = rp[(rp["voiced"] == 1) & rp["rpm"].notna()]
    td = v["t_s"].to_numpy(float) - lag
    b = np.floor(td / BIN_S).astype(int)
    win = v["F_lo_Hz"].notna().to_numpy() if "F_lo_Hz" in v else np.ones(len(v), bool)
    df = pd.DataFrame({"b": b, "rpm": v["rpm"].to_numpy(float), "win": win}).groupby("b").agg(
        median=("rpm", "median"), size=("rpm", "size"), win=("win", "all"))
    df = df[df["size"] >= 2]
    return (df.index.to_numpy() + 0.5) * BIN_S, df["median"].to_numpy(), df["win"].to_numpy(bool)


def find_drops(tb, rb, wb, min_pct, min_rpm):
    """Times where median RPM over the next STEP_POST s (after a STEP_GAP s gap) is at least min_pct below the
    median over the previous STEP_PRE s, with every 'before' bin inside the thrust window (so the before level
    is not an octave error). Non-maximum suppression within 1.5 s. -> list of (t, before, after, fraction)."""
    cand = []
    for i, t in enumerate(tb):
        mp = (tb >= t - STEP_PRE) & (tb < t)
        pre = rb[mp]
        post = rb[(tb >= t + STEP_GAP) & (tb < t + STEP_GAP + STEP_POST)]
        if len(pre) < 4 or len(post) < 4 or not wb[mp].all():
            continue
        a, b = float(np.median(pre)), float(np.median(post))
        if a >= min_rpm and (b - a) / a <= -min_pct / 100.0:
            cand.append((t, a, b, (b - a) / a))
    cand.sort(key=lambda c: c[3])
    out = []
    for c in cand:
        if all(abs(c[0] - o[0]) > 1.5 for o in out):
            out.append(c)
    return sorted(out)


def drop_check(d, fr, alarms, lvc_v):
    """Cross-check of one audio RPM drop against the display (see docstring, v1.2). fr < 0 is the RPM change."""
    notes = []
    Tb, Ta = fnum(d.get("T_before_g")), fnum(d.get("T_after_g"))
    if Tb is None or Ta is None or Tb <= 0:
        notes.append("no display thrust to compare")
    elif Ta > Tb * (1.0 - 0.5 * (1.0 - (1.0 + fr) ** 2)):
        notes.append("display thrust did not fall with it: audio tracking artefact")
    else:
        notes.append("display thrust fell with it")
    if "load shed" in (d.get("signature") or ""):
        if d["V_before"] - lvc_v >= 1.0:
            notes.append("V %.1f V above the LVC reference: throttle cut, not LVC" % (d["V_before"] - lvc_v))
        elif alarms is None:
            notes.append("V within 1 V of the LVC reference; alarm scan not run")
        else:
            late = [a[0] - d["t_display_s"] for a in alarms if 0.0 <= a[0] - d["t_display_s"] <= 10.0]
            notes.append("V within 1 V of the LVC reference; " + ("ESC alarm group %.1f s later" % late[0] if late
                                                                  else "no ESC alarm group within 10 s"))
    return "; ".join(notes)


def main():
    ap = argparse.ArgumentParser(description="Pack / ESC limiting check for a thrust-stand session.")
    ap.add_argument("callouts", help="SESSION_throttle_callouts.csv")
    ap.add_argument("--data-dir", default=str(HERE / "data"))
    ap.add_argument("--out-dir", default=str(HERE / "out" / "battery"))
    ap.add_argument("--video-dir", default=None, help="default analysis/tests/video/<date from the session name>")
    ap.add_argument("--state-lag", type=float, default=-0.35, help="audio t = display t + lag (audio_rpm.py default)")
    ap.add_argument("--lvc-v", type=float, default=12.0, help="ESC cutoff voltage to compare against (UNVERIFIED)")
    ap.add_argument("--cells", type=int, default=4)
    ap.add_argument("--drop-pct", type=float, default=3.0, help="RPM drop reported, pct")
    ap.add_argument("--no-plot", action="store_true")
    ap.add_argument("--no-alarms", action="store_true", help="skip the ESC alarm scan of the audio")
    args = ap.parse_args()

    cpath = Path(args.callouts)
    session = cpath.stem.replace("_throttle_callouts", "")
    data, out = Path(args.data_dir), Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    vdir = Path(args.video_dir) if args.video_dir else HERE / "video" / session[:10]
    logf = open(out / (session + "_battery_log.txt"), "w")

    def log(msg, echo=False):
        logf.write(msg + "\n")
        if echo:
            print(msg, flush=True)

    log("battery_check.py v%s  session %s  lag %.2f s  LVC reference %.2f V (%.2f V/cell, UNVERIFIED)"
        % (SCRIPT_VERSION, session, args.state_lag, args.lvc_v, args.lvc_v / args.cells), echo=True)
    calls = pd.read_csv(cpath)
    runs = []
    for rid, g in calls.groupby("run_id", sort=False):
        runs.append({"run_id": rid, "video": g["video_file"].iloc[0], "prop": g["prop"].iloc[0],
                     "created": creation_time(vdir / g["video_file"].iloc[0])})
    runs.sort(key=lambda r: (r["created"] or "~", r["run_id"]))

    run_rows, hold_rows, drop_rows, zoom = [], [], [], {}
    for R in runs:
        rid = R["run_id"]
        p = {k: data / ("%s_%s.csv" % (rid, k)) for k in ("blue_states", "rpm", "holds", "throttle")}
        if not p["blue_states"].exists():
            log("%s: no blue states, skipped" % rid, echo=True)
            continue
        bs, n_pv, _ = pv_fallback(pd.read_csv(p["blue_states"]))
        bs["I"] = pd.to_numeric(bs["I_A"], errors="coerce")
        bs["V"] = pd.to_numeric(bs["V_V"], errors="coerce")
        clean = ~bs["flags"].fillna("").apply(lambda f: any(x in f for x in BLUE_BAD)) & bs["I"].notna() & bs["V"].notna()
        b = bs[clean]
        load = b[b["I"] >= LOAD_I]
        rest = b[b["I"] < REST_I]
        row = dict(run_id=rid, prop=R["prop"], created=R["created"], n_clean_states=len(b), n_I_from_PV=n_pv)
        if len(load):
            t0, t1 = float(load["t_start_s"].min()), float(load["t_end_s"].max())
            r0 = rest[rest["t_end_s"] < t0]
            r1 = rest[rest["t_start_s"] > t1]
            if len(r0):
                row.update(V_rest_start=float(r0["V"].median()), n_rest_start=len(r0))
            if len(r1):
                row.update(V_rest_end=float(r1["V"].tail(3).median()), n_rest_end=len(r1),
                           rest_end_after_load_s=float(r1["t_mid_s"].iloc[-1]) - t1)
            c = np.polyfit(load["I"], load["V"], 1)
            res = load["V"] - np.polyval(c, load["I"])
            imin = load["V"].idxmin()
            row.update(line_V0=float(c[1]), line_R_mohm=-1000.0 * float(c[0]), line_rms_V=float(res.std()),
                       n_load_states=len(load), I_max=float(load["I"].max()), P_max=float(pd.to_numeric(load["P_W"], errors="coerce").max()),
                       V_min_loaded=float(load.loc[imin, "V"]), I_at_V_min=float(load.loc[imin, "I"]),
                       t_V_min=float(load.loc[imin, "t_mid_s"]),
                       V_min_per_cell=float(load.loc[imin, "V"]) / args.cells,
                       lvc_margin_V=float(load.loc[imin, "V"]) - args.lvc_v)
        al = None if args.no_alarms else esc_alarms(vdir / R["video"])
        if al is not None:
            row.update(esc_alarm_groups=len(al), esc_alarm_t_s=" ".join("%.1f" % a[0] for a in al))
        run_rows.append(row)

        # ---- holds + duty (rpm = median of the voiced hops in the hold: robust to voice-callout glitches) ----
        rp = pd.read_csv(p["rpm"]) if p["rpm"].exists() else None
        hd = pd.read_csv(p["holds"]) if p["holds"].exists() else None
        if hd is not None:
            for _, h in hd.iterrows():
                r = {"run_id": rid, "prop": R["prop"]}
                for c in ("point", "throttle_pos", "throttle_pct", "thrust_callout_g", "hold_start_s", "hold_end_s",
                          "T_mean_g", "T_first_g", "T_last_g", "I_mean", "V_mean", "V_min", "P_mean", "rpm_mean",
                          "rpm_std", "rpm_first", "rpm_last", "events", "flags"):
                    r[c] = h.get(c)
                a0, a1 = fnum(h.get("hold_start_s")), fnum(h.get("hold_end_s"))
                if rp is not None and a0 is not None and a1 is not None:
                    x = rp[(rp["voiced"] == 1) & rp["rpm"].notna() & (rp["t_s"] >= a0 + args.state_lag)
                           & (rp["t_s"] <= a1 + args.state_lag)]["rpm"]
                    if len(x) >= 3:
                        r["rpm_median"] = float(x.median())
                I, V, n = fnum(h.get("I_mean")), fnum(h.get("V_mean")), fnum(r.get("rpm_median"))
                if I is not None and V is not None and n is not None and V > 0:
                    for k, (kv, rr) in FITS.items():
                        r["duty_" + k] = (n / kv + I * rr) / V
                if I is not None and "line_V0" in row:
                    r["V_line"] = row["line_V0"] - row["line_R_mohm"] / 1000.0 * I
                hold_rows.append(r)

        # ---- sudden RPM drops ----
        if rp is not None:
            tb, rb, wb = rpm_bins(rp, args.state_lag)
            th = pd.read_csv(p["throttle"]) if p["throttle"].exists() else None
            drops = find_drops(tb, rb, wb, args.drop_pct, 1500.0)
            for (t, a, bb, fr) in drops:
                d = {"run_id": rid, "t_display_s": t, "rpm_before": a, "rpm_after": bb, "drop_pct": 100.0 * fr}
                if th is not None and len(th):
                    j = int(np.argmin(np.abs(th["t_s"].to_numpy(float) - t)))
                    near = abs(float(th["t_s"].iloc[j]) - t) <= 0.5
                    d["phase"] = th["phase"].iloc[j] if near and isinstance(th["phase"].iloc[j], str) else ""
                    d["throttle_pos"] = th["throttle_pos"].iloc[j] if near else None
                    pre = th[(th["t_s"] >= t - 1.0) & (th["t_s"] < t)]["T_g"]
                    post = th[(th["t_s"] >= t + 0.4) & (th["t_s"] < t + 1.4)]["T_g"]
                    d["T_before_g"] = float(pre.median()) if len(pre) else None
                    d["T_after_g"] = float(post.median()) if len(post) else None
                pre = b[(b["t_end_s"] >= t - 1.5) & (b["t_end_s"] < t - 0.1)]
                post = b[(b["t_start_s"] > t + 0.3) & (b["t_start_s"] <= t + 1.8)]
                if len(pre) and len(post):
                    d.update(I_before=float(pre["I"].iloc[-1]), I_after=float(post["I"].iloc[0]),
                             V_before=float(pre["V"].iloc[-1]), V_after=float(post["V"].iloc[0]))
                    dI, dV = d["I_after"] - d["I_before"], d["V_after"] - d["V_before"]
                    d["signature"] = ("I down, V up (load shed: LVC or throttle cut)" if dI < -0.5 and dV > 0.05 else
                                      "I up (overload / desync?)" if dI > 0.5 else "I and V ~unchanged")
                d["check"] = drop_check(d, fr, al, args.lvc_v)
                drop_rows.append(d)
            zoom[rid] = (bs, clean, rp, th, hd, drops)

    # ---- write ----
    def wcsv(name, rows, cols):
        df = pd.DataFrame(rows)
        for c in cols:
            if c not in df.columns:
                df[c] = None
        df[cols].to_csv(data / name, index=False, float_format="%.6g")
        return data / name
    f_runs = wcsv(session + "_battery_runs.csv", run_rows,
                  ["run_id", "prop", "created", "n_clean_states", "n_I_from_PV", "V_rest_start", "n_rest_start", "V_rest_end", "n_rest_end",
                   "rest_end_after_load_s", "line_V0", "line_R_mohm", "line_rms_V", "n_load_states", "I_max", "P_max",
                   "V_min_loaded", "I_at_V_min", "t_V_min", "V_min_per_cell", "lvc_margin_V", "esc_alarm_groups",
                   "esc_alarm_t_s"])
    f_holds = wcsv(session + "_battery_holds.csv", hold_rows,
                   ["run_id", "prop", "point", "throttle_pos", "throttle_pct", "thrust_callout_g", "hold_start_s", "hold_end_s",
                    "T_mean_g", "T_first_g", "T_last_g", "I_mean", "V_mean", "V_min", "V_line", "P_mean", "rpm_median", "rpm_mean", "rpm_std",
                    "rpm_first", "rpm_last", "duty_A", "duty_B", "events", "flags"])
    f_drops = wcsv(session + "_rpm_drops.csv", drop_rows,
                   ["run_id", "t_display_s", "phase", "throttle_pos", "rpm_before", "rpm_after", "drop_pct", "T_before_g",
                    "T_after_g", "I_before", "I_after", "V_before", "V_after", "signature", "check"])

    # ---- summary ----
    log("", echo=True)
    log("run (time order)        created     Vrest start/end   pack line V0 / R        V min loaded (I)    margin to %.1f V"
        "   ESC alarm groups (first, s)" % args.lvc_v, echo=True)
    for r in run_rows:
        log("%-22s  %-10s  %6s / %6s      %6s V / %5s mOhm   %6s V (%5s A)     %s V   %s" % (
            r["run_id"], (r.get("created") or "")[11:19], "%.2f" % r["V_rest_start"] if "V_rest_start" in r else "-",
            "%.2f" % r["V_rest_end"] if "V_rest_end" in r else "-", "%.2f" % r["line_V0"] if "line_V0" in r else "-",
            "%.0f" % r["line_R_mohm"] if "line_R_mohm" in r else "-", "%.2f" % r["V_min_loaded"] if "V_min_loaded" in r else "-",
            "%.1f" % r["I_at_V_min"] if "I_at_V_min" in r else "-", "%+.2f" % r["lvc_margin_V"] if "lvc_margin_V" in r else "-",
            "%d (%s)" % (r["esc_alarm_groups"], r["esc_alarm_t_s"].split(" ")[0] if r["esc_alarm_groups"] else "-")
            if "esc_alarm_groups" in r else "-"), echo=True)
    hi = [h for h in hold_rows if fnum(h.get("throttle_pos")) is not None and h["throttle_pos"] >= 50]
    if hi:
        log("holds at stick >= 50:  run / stick: T g, rpm, I A, V V, duty A (B)", echo=True)
        for h in hi:
            log("  %-22s %4.0f: %5s g  %5s rpm  %5s A  %5s V  d %s (%s)" % (
                h["run_id"], h["throttle_pos"], "%.0f" % fnum(h["T_mean_g"]) if fnum(h["T_mean_g"]) else "-",
                "%.0f" % fnum(h.get("rpm_median")) if fnum(h.get("rpm_median")) else "-", "%.2f" % fnum(h["I_mean"]) if fnum(h["I_mean"]) else "-",
                "%.2f" % fnum(h["V_mean"]) if fnum(h["V_mean"]) else "-", "%.3f" % h["duty_A"] if "duty_A" in h else "-",
                "%.3f" % h["duty_B"] if "duty_B" in h else "-"), echo=True)
    n_art = sum("artefact" in d.get("check", "") for d in drop_rows)
    log("sudden RPM drops >= %.0f pct: %d, of which %d audio tracking artefacts (details in %s)"
        % (args.drop_pct, len(drop_rows), n_art, f_drops.name), echo=True)
    for d in drop_rows:
        log("  %-22s %7.2f s  %-10s stick %5s  %5.0f -> %5.0f rpm (%+.1f%%)  %s; %s" % (
            d["run_id"], d["t_display_s"], d.get("phase", ""), "%.0f" % d["throttle_pos"] if fnum(d.get("throttle_pos")) is not None else "-",
            d["rpm_before"], d["rpm_after"], d["drop_pct"], d.get("signature", ""), d.get("check", "")))
        if "artefact" not in d.get("check", ""):
            log("    [real] %s %.2f s: %s" % (d["run_id"], d["t_display_s"], d.get("check", "")), echo=True)
    log("outputs: %s, %s, %s; plots and log in %s" % (f_runs.name, f_holds.name, f_drops.name, out), echo=True)

    # ---- plots ----
    if not args.no_plot and hold_rows:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        H = pd.DataFrame(hold_rows)
        fig, axs = plt.subplots(2, 3, figsize=(17, 9))
        items = [("duty_A", "effective duty, fit A (1 = 12x8E top point)"), ("rpm_median", "audio rpm (hold median)"),
                 ("T_mean_g", "thrust, g (hold mean)"), ("I_mean", "current, A"), ("V_mean", "voltage, V (mean; x = min)"),
                 ("P_mean", "electrical power, W")]
        for ax, (col, lab) in zip(axs.flat, items):
            for i, (rid, g) in enumerate(H.groupby("run_id", sort=False)):
                g = g.sort_values("throttle_pos")
                y = pd.to_numeric(g[col], errors="coerce") if col in g else None
                if y is None or y.notna().sum() == 0:
                    continue
                ax.plot(g["throttle_pos"], y, "o-", ms=4, color="C%d" % i, label=rid.replace(session + "_", ""))
                if col == "duty_A" and "duty_B" in g:
                    ax.plot(g["throttle_pos"], pd.to_numeric(g["duty_B"], errors="coerce"), "--", lw=0.8, color="C%d" % i)
                if col == "V_mean":
                    ax.plot(g["throttle_pos"], pd.to_numeric(g["V_min"], errors="coerce"), "x", ms=5, color="C%d" % i)
            if col == "V_mean":
                ax.axhline(args.lvc_v, color="r", lw=0.8, ls=":")
                ax.text(0.02, args.lvc_v + 0.05, "LVC reference %.1f V (UNVERIFIED)" % args.lvc_v, color="r", fontsize=8,
                        transform=ax.get_yaxis_transform())
            ax.set_xlabel("stick, -100..+100")
            ax.set_ylabel(lab)
            ax.grid(alpha=0.3)
        axs[0, 0].legend(fontsize=8, title="dashed = fit B")
        fig.suptitle("%s: hold means against stick (battery_check.py v%s)" % (session, SCRIPT_VERSION))
        fig.tight_layout()
        fig.savefig(out / (session + "_battery_vs_stick.png"), dpi=80)
        plt.close(fig)

        for rid, (bs, clean, rp, th, hd, drops) in zoom.items():
            if hd is None or not len(hd):
                continue
            hh = hd[pd.to_numeric(hd["throttle_pos"], errors="coerce") >= 40]
            hs_col = pd.to_numeric(hh["hold_start_s"], errors="coerce").dropna()
            if not len(hs_col):
                continue
            ta = float(hs_col.min()) - 5.0
            he_all = pd.to_numeric(hd["hold_end_s"], errors="coerce").dropna()
            tb_ = float(he_all.max()) + 5.0 if len(he_all) else float(bs["t_end_s"].max())
            fig, axs = plt.subplots(4, 1, figsize=(15, 11), sharex=True)
            if th is not None:
                m = (th["t_s"] >= ta) & (th["t_s"] <= tb_)
                axs[0].plot(th["t_s"][m], th["T_g"][m], ".", ms=1.5, color="C1")
            v = rp[(rp["voiced"] == 1) & rp["rpm"].notna()]
            td = v["t_s"] - args.state_lag
            m = (td >= ta) & (td <= tb_)
            axs[1].plot(td[m], v["rpm"][m], ".", ms=1.2, color="C0")
            b = bs[clean & (bs["t_mid_s"] >= ta) & (bs["t_mid_s"] <= tb_)]
            for ax, col, lab in ((axs[2], "I", "current, A"), (axs[3], "V", "voltage, V")):
                ax.step(b["t_start_s"], b[col], where="post", color="k", lw=0.8)
                ax.set_ylabel(lab)
            axs[3].axhline(args.lvc_v, color="r", lw=0.8, ls=":")
            axs[0].set_ylabel("thrust, g")
            axs[1].set_ylabel("audio rpm (display clock)")
            for _, h in hd.iterrows():
                a0, a1 = fnum(h.get("hold_start_s")), fnum(h.get("hold_end_s"))
                if a0 is None or a1 is None or a1 < ta:
                    continue
                for ax in axs:
                    ax.axvspan(a0, a1, color="0.9", zorder=0)
                axs[0].text(0.5 * (a0 + a1), axs[0].get_ylim()[1], "%g" % h["throttle_pos"], ha="center", va="top", fontsize=9)
            for (t, a, bb, fr) in drops:
                if ta <= t <= tb_:
                    for ax in axs:
                        ax.axvline(t, color="r", lw=0.8, ls="--")
            for ax in axs:
                ax.grid(alpha=0.3)
            axs[3].set_xlabel("video time, s (grey = callout holds, label = stick; red dashed = RPM drop >= %.0f pct)" % args.drop_pct)
            fig.suptitle("%s: high-stick part" % rid)
            fig.tight_layout()
            fig.savefig(out / (rid + "_zoom.png"), dpi=80)
            plt.close(fig)
    logf.close()


if __name__ == "__main__":
    main()
