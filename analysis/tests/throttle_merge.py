#!/usr/bin/env python3
"""
throttle_merge.py -- throttle position against time for a thrust-stand video, from the operator's spoken callouts
(logged by hand as discrete throttle / thrust points), and per-hold statistics of thrust, current, voltage, power
and audio rpm.

Written for the SAE Aero Design 2027 T-2 static thrust stand (TEST_PLAN.md 3). Developed on the 2026-09-25
session (analysis/tests/video/2026-09-25/, callouts in analysis/tests/data/2026-09-25_throttle_callouts.csv).

Inputs per run (RUN = run_id), from read_mt10pro_video.py and (optional) audio_rpm.py:
    analysis/tests/data/RUN_frames.csv, RUN_thrust_states.csv, RUN_blue_states.csv, RUN_t2.csv, [RUN_rpm.csv]
    callouts CSV: run_id, video_file, prop, point, throttle_pos, thrust_callout_g, source

Assumptions (check them against the plots):
  A1. The callouts of a run are listed in the order they were spoken, one per throttle setting.
  A2. The called-out thrust was read off the MT10PRO red display during the hold, so that exact value appears on
      the display (as read by read_mt10pro_video.py) at some time during the hold.
  A3. The stick is held still between stick moves, and there is one stick move (possibly made in stages)
      between consecutive callouts, in the direction of the throttle change.
  A4. throttle_pos is the transmitter stick on a -100..+100 scale; throttle_pct = (throttle_pos + 100) / 2.
      This is the ESC's command only if the ESC throttle range was calibrated to the transmitter end points
      (UNVERIFIED for the 2026-09-25 session).
  A5. Times are video (display) times, the clock of the t2 rows. The displays lag the prop by about 0.35-0.4 s
      (audio_rpm.py --state-lag); hold windows for audio rpm are shifted by --state-lag.

Method:
  1. Anchors. Each callout is matched to one red-display thrust state whose value equals the callout. Dynamic
     programming over the callouts of a run picks one state per callout in time order (ANCHOR_GAP_S apart), cost
     |display - callout| / max(1 g, 0.5 pct) plus small penalties for flagged or short states and a small bonus
     for long ones. Candidates are within max(5 g, 3 pct); a callout with none is unmatched (flag no_anchor).
     --anchor RUN:POINT=T forces a callout onto the thrust state on screen at video time T.
  2. Thrust rate. Valid thrust frames (possible_mix frames dropped) on a uniform grid, 7-sample running median,
     0.5 s running mean, d/dt. Fast segments: |rate| > max(RATE_MIN, RATE_REL x T) g/s; same-sign fast segments
     less than MERGE_GAP_S apart are merged (a stick move made in stages).
  3. Stick moves. Between consecutive anchors: the fast segment with the largest thrust change in the direction
     of the throttle change (if none: the move is taken to span the whole time between the two anchor states,
     flag no_move_found), extended over any other same-sign segment between the two anchor states that is
     event-sized and whose blue current moves with it, dI/I >= STAGE_DI_REL x dT/T (a move made in stages more
     than MERGE_GAP_S apart; flags staged_move_after / staged_move_before; v1.2), and over an opposite-sign
     segment after it, before the next callout state, that passes the same current test with the sign reversed
     (an overshoot pulled back; flag overshoot_before; v1.3). Before the first anchor: the
     last rising segment (spool-up); after the last anchor: the largest falling segment (throttle cut); if none,
     the anchor state's own start or end. A rising segment after the last callout that passes the same current
     test is an uncalled stick push: the last hold ends at it, throttle is blank after it, phase "uncalled"
     until the cut (flag uncalled_move_after; v1.2).
  4. Throttle(t) = the callout's position during its hold (end of the stick move before it to start of the stick
     move after it), linear in time across each stick move, blank outside the first and last holds.
  5. Per hold: thrust (valid frames), current, voltage and power (blue states whose middle is in the hold,
     weighted by duration), audio rpm (voiced hops), values in the first and last HOLD_EDGE_S, linear drift per
     second, and events: any other fast thrust segment inside the hold (a thrust change with the stick held),
     with the blue current and voltage just before and after it.

Current from P / V (v1.1, pv_fallback). The meter computes P from its own V and I (|P - V x I| <= 0.32 W on
hand-checked 2026-09-25 states), so where the current cell alone is unreadable I = P_W / V_V is used. It applies
to blue states flagged bad_I_A (bad_aux is dropped with it; the aux value is not used here) whose V_V and P_W
parsed, not flagged P_ne_VxI, unit_glyph, bad_V_V, bad_P_W or short. The readable units.decimals of the current
cell (pattern d.ddA) must agree with P/V within PV_DIGIT_TOL modulo 10 A; a weak_evidence state is used only when
that check parsed and passed (three independent cells agree), and is then marked was_weak. Filled states carry
I_from_PV. Reason: 2026-09-25 12x6E T2 from 56.9 s, glare and blur on the left LCD cells made the reader see
"h 25.61A" / "0 .9.27A" for 25.61 A / 29.27 A (overlays of states 118 and 178); evidence_min, taken over all 32
cells, fell from 10-139 to about 1-3 on every state, so weak_evidence there reflects the blurred left cells
(INFERRED). Check on that run: P/V against the readable digits, median 0.013 A (max 0.022, n 19) on
non-weak states, median 0.015 A on weak ones; 47 states filled, 11 rejected: 79.8-80.2 s (0.78 A off; the current
cell reads .8.86 while thrust and P fall), 66.25 s (0.20 A), and 8 post-run rest states (0.38 A read as 8.38).

Staged stick moves (v1.2). v1.1 took only the largest same-sign fast segment between two callouts as the stick
move, so a second stage more than MERGE_GAP_S later stayed in the next hold as a "thrust_event". Reader v1.4
removed short misread states that had bridged such gaps and exposed it: 12X10E T2 move 50 -> 60 in two stages,
94.94-96.00 s (+107 g) and 97.12-97.55 s (+58 g, I 26.96 -> 27.97 A); v1.1 started hold 11 at 96.00 s (mean
1586 g, callout 1600), v1.2 at 97.55 s (1598 g). The current test keeps real in-hold thrust changes out of the
move: 12X10E T1 hold 4, 62.93-63.36 s +29 g with I 8.14 -> 7.96 A, stays an event. On the 2026-09-25 data v1.2
changed 4 holds (12X10E T1 7, 12X10E T2 9 and 11, 9X4.5E 5); each hold mean moved toward its callout.
Uncalled pushes after the last callout (reader v1.4 data): 12X6E T1 105.37-106.49 s +378 g (I 21.55 -> 29.51 A)
had stayed in hold 10 (stick 58, callout 1701 g, mean 1790 g; now 1700 g) and set stick 58 on the rows after it;
12X10E T1 111.05-111.51 s +80 g (I 31.58 -> 36.69 A) the same in hold 8 (stick 70).

Overshoot pulled back (v1.3). The stick went past its mark and came back before the callout was read. The current
fell with the thrust, as for a stick move: 12X10E T1 move 0 -> 20 reached 1093-1100 g, then 68.67-69.30 s -44 g,
I 14.92 -> 13.66 A, (dI/I)/(dT/T) +2.0; callout 1030 g read at 73.48 s. 12X10E T2 move 40 -> 50 reached 1486-1491 g,
then 88.77-88.97 s -36 g, I 24.03 -> 23.09 A, +1.6; callout 1435 g at 91.00 s. The other in-hold events of
2026-09-25 give -0.53 to +0.22 (thrust changes with the stick held). v1.3 starts those two holds after the
pull-back: hold means 1044.1 -> 1035.1 g and 1452.3 -> 1443.8 g; no other hold changed. Throttle across the
extended move is still linear, so during the overshoot it is below the true (unknown) stick.

Usage (from the repo root, after read_mt10pro_video.py and audio_rpm.py):
    python analysis/tests/throttle_merge.py analysis/tests/data/2026-09-25_throttle_callouts.csv
Options: --run-id (only this run; repeatable), --anchor RUN:POINT=T (repeatable), --state-lag, --no-t2, --no-plot.

Outputs:
    analysis/tests/data/RUN_holds.csv        one row per callout: anchor, hold window, means, drift, events, flags
    analysis/tests/data/RUN_throttle.csv     one row per valid thrust frame: t_s, T_g, throttle_pos, throttle_pct, phase
    analysis/tests/data/RUN_t2.csv           throttle_pct and a " | throttle" notes segment filled in place
    analysis/tests/data/SESSION_holds.csv    all runs of the callouts file (SESSION = its name before _throttle_callouts)
    analysis/tests/out/throttle/             RUN_timeseries.png, SESSION_vs_throttle.png, SESSION_log.txt
  Re-running read_mt10pro_video.py rewrites RUN_t2.csv; run audio_rpm.py and then this script again after it.
Requires: Python 3, numpy, scipy, pandas; matplotlib for the plots.
"""
import argparse
import csv
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import median_filter, uniform_filter1d

SCRIPT_VERSION = "1.3"
HERE = Path(__file__).resolve().parent

ANCHOR_GAP_S = 1.0       # consecutive anchor states at least this far apart
ANCHOR_TOL = (5.0, 0.03) # candidate display values within max(g, fraction x callout)
SKIP_COST = 25.0         # DP cost of leaving a callout unmatched
GRID_DT_MAX = 0.5        # gaps in the valid thrust frames longer than this are not interpolated over
MED_N = 7                # running median, samples
MEAN_S = 0.5             # running mean, s
RATE_MIN, RATE_REL = 20.0, 0.05   # fast-segment threshold: max(RATE_MIN, RATE_REL x T) g/s
MERGE_GAP_S = 1.2        # same-sign fast segments closer than this are one stick move
EVENT_MIN = (15.0, 0.02) # an in-hold fast segment is reported if |dT| >= max(g, fraction x T)
STAGE_DI_REL = 0.75      # a later stage of a stick move: dI/I >= this x dT/T, same sign (v1.2)
HOLD_EDGE_S = 0.5        # window for first / last values of a hold
BLUE_BAD = ("short", "weak_evidence", "P_ne_VxI", "bad_", "unit_glyph")
PV_BLOCK = ("P_ne_VxI", "unit_glyph", "bad_V_V", "bad_P_W")   # no I = P/V fallback for these (pv_fallback)
PV_DIGIT_TOL = 0.1       # A: P/V against the readable units.decimals of the current cell


def fnum(v):
    try:
        x = float(v)
        return x if np.isfinite(x) else None
    except (TypeError, ValueError):
        return None


def pv_fallback(bs):
    """Blue states with I_A = P_W / V_V where only the current cell failed to parse (see docstring, v1.1).
    Returns (new frame, number of states filled, number rejected by the digit check). battery_check.py uses it too."""
    bs = bs.copy()
    fl = bs["flags"].fillna("").astype(str)
    bs["flags"] = fl
    V = pd.to_numeric(bs["V_V"], errors="coerce")
    P = pd.to_numeric(bs["P_W"], errors="coerce")
    elig = (fl.str.contains("bad_I_A") & V.notna() & (V > 0) & P.notna()
            & ~fl.str.contains("|".join(PV_BLOCK)) & ~fl.str.contains("short"))
    n_ok = n_rej = 0
    for i in np.flatnonzero(elig.to_numpy()):
        ipv = P.iat[i] / V.iat[i]
        m = re.search(r"(\d)\.(\d\d)A", str(bs["row0"].iat[i]))
        d = (((ipv - float(m.group(1) + "." + m.group(2)) + 5.0) % 10.0) - 5.0) if m else None
        weak = "weak_evidence" in fl.iat[i]
        if (d is not None and abs(d) > PV_DIGIT_TOL) or (weak and d is None):
            n_rej += 1
            continue
        keep = [f for f in fl.iat[i].split(";") if f and f not in ("bad_I_A", "bad_aux", "weak_evidence")]
        bs.iat[i, bs.columns.get_loc("I_A")] = ipv
        bs.iat[i, bs.columns.get_loc("flags")] = ";".join(keep + ["I_from_PV"] + (["was_weak"] if weak else []))
        n_ok += 1
    return bs, n_ok, n_rej


def runs_of(mask):
    """(start, end_inclusive) index pairs of the True runs of a boolean array."""
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1) - 1))


# ----------------------------------------------------------------------------------------------
# Anchors
# ----------------------------------------------------------------------------------------------
def match_anchors(calls, ts, forced, log):
    """One thrust-state index (or None) per callout, in time order, by dynamic programming."""
    good = ts[~ts["flags"].fillna("").str.contains("possible_mix|bad_digits")].copy()
    cands = []
    for k, c in enumerate(calls):
        cg = float(c["thrust_callout_g"])
        if k in forced:
            tf = forced[k]
            hit = ts[(ts["t_start_s"] <= tf + 1e-6) & (ts["t_end_s"] >= tf - 1e-6)]
            if hit.empty:
                hit = ts.iloc[[int(np.argmin(np.abs(0.5 * (ts["t_start_s"] + ts["t_end_s"]) - tf)))]]
            cands.append([(int(hit.index[0]), 0.0)])
            continue
        tol = max(ANCHOR_TOL[0], ANCHOR_TOL[1] * cg)
        sel = good[(good["T_g"] - cg).abs() <= tol]
        lst = []
        for i, s in sel.iterrows():
            dur = s["t_end_s"] - s["t_start_s"]
            cost = abs(s["T_g"] - cg) / max(1.0, 0.005 * cg)
            fl = str(s["flags"]) if isinstance(s["flags"], str) else ""
            cost += 0.5 * ("weak_evidence" in fl) + 0.5 * (s["n_frames"] < 3) - 0.3 * min(dur, 3.0) / 3.0
            lst.append((int(i), cost))
        cands.append(lst)
    # DP: key = index of the last matched state (-1 = none yet) -> (cost, path)
    best = {-1: (0.0, [])}
    for k in range(len(calls)):
        nxt = {}
        for last, (cst, path) in best.items():
            t_last = ts.at[last, "t_end_s"] if last >= 0 else -np.inf
            if k not in forced:                                             # leave callout k unmatched
                key, val = last, (cst + SKIP_COST, path + [None])
                if key not in nxt or val[0] < nxt[key][0]:
                    nxt[key] = val
            for i, ci in cands[k]:
                if ts.at[i, "t_start_s"] < t_last + ANCHOR_GAP_S:
                    continue
                val = (cst + ci, path + [i])
                if i not in nxt or val[0] < nxt[i][0]:
                    nxt[i] = val
        if not nxt:                                                         # a forced anchor out of order
            log("[!] forced anchor for callout %d is not after the previous anchor; ignoring the order there" % (k + 1))
            nxt = {i: (min(v[0] for v in best.values()) + ci, min(best.values(), key=lambda v: v[0])[1] + [i])
                   for i, ci in cands[k]}
        best = nxt
    cost, path = min(best.values(), key=lambda v: v[0])
    alts = []
    for k, i in enumerate(path):                                            # other exact matches, for the log
        if i is None:
            alts.append(0)
            continue
        cg = float(calls[k]["thrust_callout_g"])
        alts.append(int(sum(1 for j, _ in cands[k] if j != i and ts.at[j, "T_g"] == cg)))
    return path, alts


# ----------------------------------------------------------------------------------------------
# Thrust rate and fast segments
# ----------------------------------------------------------------------------------------------
def thrust_series(fr):
    """Uniform-grid thrust (NaN over gaps), smoothed thrust and rate."""
    v = fr[(fr["thrust_valid"] == 1) & fr["T_g"].notna() & (fr["thrust_possible_mix"] != 1)]
    t, T = v["t_s"].to_numpy(float), v["T_g"].to_numpy(float)
    dt = float(np.median(np.diff(t)))
    tu = np.arange(t[0], t[-1] + 0.5 * dt, dt)
    Tu = np.interp(tu, t, T)
    j = np.clip(np.searchsorted(t, tu), 1, len(t) - 1)
    gap = (t[j] - t[j - 1]) > GRID_DT_MAX
    Tm = median_filter(Tu, size=MED_N, mode="nearest")
    nmean = max(3, int(round(MEAN_S / dt)) | 1)
    Ts = uniform_filter1d(Tm, size=nmean, mode="nearest")
    rate = np.gradient(Ts, tu)
    Ts[gap], rate[gap] = np.nan, np.nan
    return {"t": t, "T": T, "tu": tu, "Ts": Ts, "rate": rate, "dt": dt, "half": nmean // 2}


def fast_segments(S):
    """Merged fast segments: dicts t0, t1, dT, sign, peak_rate."""
    tu, Ts, rate, h = S["tu"], S["Ts"], S["rate"], S["half"]
    thr = np.maximum(RATE_MIN, RATE_REL * np.nan_to_num(Ts, nan=0.0))
    fast = np.nan_to_num(np.abs(rate), nan=0.0) > thr
    segs = []
    for a, b in runs_of(fast):
        ia, ib = max(0, a - h), min(len(tu) - 1, b + h)
        pre, post = Ts[ia], Ts[ib]
        if not (np.isfinite(pre) and np.isfinite(post)):
            pre, post = np.nanmin(Ts[ia:ib + 1]), np.nanmax(Ts[ia:ib + 1])
            if np.nanmean(rate[a:b + 1]) < 0:
                pre, post = post, pre
        dT = float(post - pre)
        segs.append({"t0": float(tu[a]), "t1": float(tu[b]), "dT": dT, "sign": 1 if dT >= 0 else -1,
                     "peak_rate": float(np.nanmax(np.abs(rate[a:b + 1]))), "ia": ia, "ib": ib})
    merged = []
    for s in segs:
        if merged and merged[-1]["sign"] == s["sign"] and s["t0"] - merged[-1]["t1"] < MERGE_GAP_S:
            m = merged[-1]
            m["t1"], m["ib"] = s["t1"], s["ib"]
            m["dT"] = float(Ts[m["ib"]] - Ts[m["ia"]]) if np.isfinite(Ts[m["ib"]]) and np.isfinite(Ts[m["ia"]]) \
                else m["dT"] + s["dT"]
            m["peak_rate"] = max(m["peak_rate"], s["peak_rate"])
        else:
            merged.append(dict(s))
    return merged


# ----------------------------------------------------------------------------------------------
# One run
# ----------------------------------------------------------------------------------------------
def process_run(run_id, calls, data_dir, out_dir, forced, lag, do_t2, do_plot, log):
    p = {k: data_dir / ("%s_%s.csv" % (run_id, k)) for k in ("frames", "thrust_states", "blue_states", "t2", "rpm")}
    missing = [k for k in ("frames", "thrust_states", "blue_states") if not p[k].exists()]
    if missing:
        log("%s: skipped (no %s; run read_mt10pro_video.py first)" % (run_id, ", ".join(missing)), echo=True)
        return None
    fr = pd.read_csv(p["frames"])
    ts = pd.read_csv(p["thrust_states"]).reset_index(drop=True)
    bs, n_pv, n_pv_rej = pv_fallback(pd.read_csv(p["blue_states"]))
    rp = pd.read_csv(p["rpm"]) if p["rpm"].exists() else None
    calls = sorted(calls, key=lambda c: int(c["point"]))
    pos = np.array([float(c["throttle_pos"]) for c in calls])
    cg = np.array([float(c["thrust_callout_g"]) for c in calls])
    K = len(calls)
    log("", echo=True)
    log("=== %s: %d callouts; throttle %s" % (run_id, K, " ".join("%g" % x for x in pos)), echo=True)
    if n_pv or n_pv_rej:
        log("blue states with I = P/V (current cell unreadable): %d; rejected by the digit check: %d" % (n_pv, n_pv_rej),
            echo=True)
    if np.any(np.diff(pos) <= 0):
        log("[!] throttle positions are not increasing in callout order (A1/A3 still assumed)", echo=True)

    # ---- anchors ----
    path, alts = match_anchors(calls, ts, forced, log)
    anchors = []
    for k, i in enumerate(path):
        if i is None:
            anchors.append(None)
            log("  [!] callout %d (%g, %g g): no display state within tolerance -> no_anchor" % (k + 1, pos[k], cg[k]), echo=True)
            continue
        s = ts.loc[i]
        anchors.append({"i": i, "t0": float(s["t_start_s"]), "t1": float(s["t_end_s"]), "T": float(s["T_g"]),
                        "n": int(s["n_frames"]), "flags": s["flags"] if isinstance(s["flags"], str) else ""})
        log("  callout %2d  pos %5g  %5g g  -> display %5g g at %7.2f-%7.2f s (%d frames)%s%s%s" % (
            k + 1, pos[k], cg[k], s["T_g"], s["t_start_s"], s["t_end_s"], s["n_frames"],
            "  forced" if k in forced else "", ("  [%d other exact match(es)]" % alts[k]) if alts[k] else "",
            ("  flags " + anchors[-1]["flags"]) if anchors[-1]["flags"] else ""))

    # ---- rate, fast segments ----
    S = thrust_series(fr)
    segs = fast_segments(S)
    log("  thrust grid dt %.4f s; %d fast segments after merging" % (S["dt"], len(segs)))
    bok = ~bs["flags"].fillna("").apply(lambda f: any(x in f for x in BLUE_BAD))

    def seg_T(s):
        return np.nanmean(S["Ts"][s["ia"]:s["ib"] + 1])

    def stage_ok(s, want):
        """A3 stage test: event-sized, and the blue current moves with the thrust (a stick move, not a thrust
        change with the stick held). For a prop T ~ n^2 and P ~ n^3, so dI/I ~ 1.5 dT/T; half of that is required."""
        Tl = seg_T(s)
        if not abs(s["dT"]) >= max(EVENT_MIN[0], EVENT_MIN[1] * Tl):
            return False
        b0 = bs[bok & (bs["t_end_s"] < s["t0"])].tail(1)
        b1 = bs[bok & (bs["t_start_s"] > s["t1"])].head(1)
        if not (len(b0) and len(b1)):
            return False
        i0, i1 = float(b0["I_A"].iloc[0]), float(b1["I_A"].iloc[0])
        if not (np.isfinite(i0) and np.isfinite(i1) and i0 > 0 and Tl > 0):
            return False
        return want * (i1 - i0) / i0 >= STAGE_DI_REL * abs(s["dT"]) / Tl

    # ---- stick moves ----
    ak = [k for k in range(K) if anchors[k] is not None]
    moves = {}             # (k_from, k_to) -> (t0, t1, seg or None); k_from = -1 spool-up, k_to = K cut
    used = set()
    hold_flags = {k: [] for k in range(K)}
    uncalled = None        # (t0, t1): stick pushed after the last callout, position unknown (v1.2)
    for a, b in zip(ak[:-1], ak[1:]):
        lo, hi = anchors[a]["t1"], anchors[b]["t0"]
        want = np.sign(pos[b] - pos[a]) or 1
        inside = [j for j, s in enumerate(segs) if s["t1"] > lo and s["t0"] < hi]
        good = [j for j in inside if segs[j]["sign"] == want]
        if good:
            j = max(good, key=lambda j: abs(segs[j]["dT"]))
            # A3, a move made in stages more than MERGE_GAP_S apart (v1.2): the other same-sign segments between
            # the two callout states that pass stage_ok are part of the move
            stage = [i for i in good if i == j or stage_ok(segs[i], want)]
            used.update(stage)
            m1 = segs[stage[-1]]["t1"]
            if len(stage) > 1:
                hold_flags[a].append("staged_move_after")
                hold_flags[b].append("staged_move_before")
                log("  move %d-%d in %d stages: %s" % (a + 1, b + 1, len(stage), "; ".join(
                    "%.2f-%.2f s dT %+.0f g" % (segs[i]["t0"], segs[i]["t1"], segs[i]["dT"]) for i in stage)))
            # an overshoot pulled back before the next callout state (v1.3): an opposite-sign segment after the
            # move that passes stage_ok with the sign reversed is still the stick moving; the hold starts after it
            back = [i for i in inside if segs[i]["sign"] == -want and segs[i]["t0"] >= m1 - 1e-6
                    and stage_ok(segs[i], -want)]
            if back:
                used.update(back)
                m1 = segs[back[-1]]["t1"]
                hold_flags[b].append("overshoot_before")
                log("  move %d-%d overshoot pulled back: %s" % (a + 1, b + 1, "; ".join(
                    "%.2f-%.2f s dT %+.0f g" % (segs[i]["t0"], segs[i]["t1"], segs[i]["dT"]) for i in back)), echo=True)
            moves[(a, b)] = (max(segs[stage[0]]["t0"], lo), min(m1, hi), j)
        else:
            moves[(a, b)] = (lo, hi, None)
            hold_flags[a].append("no_move_found_after")
            hold_flags[b].append("no_move_found_before")
    if ak:
        a, b = ak[0], ak[-1]
        pre = [j for j, s in enumerate(segs) if s["t1"] <= anchors[a]["t0"] + 1e-6 and s["sign"] > 0]
        if pre:
            j = pre[-1]
            used.add(j)
            moves[(-1, a)] = (segs[j]["t0"], segs[j]["t1"], j)
        else:
            moves[(-1, a)] = (anchors[a]["t0"], anchors[a]["t0"], None)
            hold_flags[a].append("start_at_anchor")
        post = [j for j, s in enumerate(segs) if s["t0"] >= anchors[b]["t1"] - 1e-6 and s["sign"] < 0]
        if post:
            j = max(post, key=lambda j: abs(segs[j]["dT"]))
            used.add(j)
            moves[(b, K)] = (segs[j]["t0"], segs[j]["t1"], j)
        else:
            moves[(b, K)] = (anchors[b]["t1"], anchors[b]["t1"], None)
            hold_flags[b].append("end_at_anchor")
        # an uncalled stick push after the last callout (v1.2): the first rising segment between the last callout
        # state and the throttle cut that passes stage_ok ends the last hold; the stick after it is unknown
        m0, m1, mj = moves[(b, K)]
        up = [j for j, s in enumerate(segs) if s["t0"] >= anchors[b]["t1"] - 1e-6 and s["t1"] <= m0 + 1e-6
              and s["sign"] > 0 and stage_ok(s, 1)]
        if up:
            j = up[0]
            used.add(j)
            uncalled = (segs[j]["t0"], m0)
            moves[(b, K)] = (segs[j]["t0"], m1, mj)
            hold_flags[b].append("uncalled_move_after")
            log("  after callout %d: uncalled stick push %.2f-%.2f s dT %+.0f g; stick unknown %.2f-%.2f s" % (
                b + 1, segs[j]["t0"], segs[j]["t1"], segs[j]["dT"], uncalled[0], uncalled[1]), echo=True)

    # ---- holds and throttle(t) ----
    holds = {}
    prev = {b: a for (a, b) in moves}
    nxt = {a: b for (a, b) in moves}
    for k in ak:
        hs = moves[(prev[k], k)][1]
        he = moves[(k, nxt[k])][0]
        if prev[k] == -1 and hs < anchors[k]["t0"]:
            # no callout before the first hold: start it no earlier than the last time the smoothed thrust
            # was outside max(10 g, 10 pct) of the anchor value (a missed slow spool-up, an earlier blip)
            m = (S["tu"] >= hs) & (S["tu"] < anchors[k]["t0"])
            out = np.abs(S["Ts"][m] - anchors[k]["T"]) > max(10.0, 0.1 * anchors[k]["T"])
            if out.any():
                hs = float(S["tu"][m][np.flatnonzero(out)[-1]])
                hold_flags[k].append("start_trimmed")
        holds[k] = (hs, he)
    knots_t, knots_p = [], []
    for k in ak:
        hs, he = holds[k]
        knots_t += [hs, he]
        knots_p += [pos[k], pos[k]]
    knots_t, knots_p = np.array(knots_t), np.array(knots_p)

    def throttle_at(t):
        t = np.atleast_1d(np.asarray(t, float))
        out = np.full(t.shape, np.nan)
        if len(knots_t):
            inr = (t >= knots_t[0]) & (t <= knots_t[-1])
            out[inr] = np.interp(t[inr], knots_t, knots_p)
        return out

    def phase_at(t):
        for k in ak:
            if holds[k][0] <= t <= holds[k][1]:
                return "hold %d" % (k + 1)
        for (a, b), (m0, m1, _) in moves.items():
            if 0 <= a and b < K and holds[a][1] < t < holds[b][0]:
                return "move %d-%d" % (a + 1, b + 1)
        if uncalled and uncalled[0] <= t <= uncalled[1]:
            return "uncalled"
        return ""

    # ---- per-hold statistics ----
    bs = bs.copy()
    bs["dur"] = bs["t_end_s"] - bs["t_start_s"] + S["dt"]
    rows = []
    for k in range(K):
        c = calls[k]
        r = {"run_id": run_id, "point": int(c["point"]), "throttle_pos": pos[k], "throttle_pct": (pos[k] + 100.0) / 2.0,
             "thrust_callout_g": cg[k]}
        if anchors[k] is None:
            r["flags"] = "no_anchor"
            rows.append(r)
            continue
        A = anchors[k]
        hs, he = holds[k]
        r.update(anchor_t0_s=A["t0"], anchor_t1_s=A["t1"], anchor_display_g=A["T"], anchor_err_g=A["T"] - cg[k],
                 hold_start_s=hs, hold_end_s=he, hold_dur_s=he - hs)
        fl = list(hold_flags[k]) + (["forced_anchor"] if k in forced else [])
        if he - hs < 1.0:
            fl.append("short_hold")
        m = (S["t"] >= hs) & (S["t"] <= he)
        tt, TT = S["t"][m], S["T"][m]
        if len(TT):
            e0, e1 = tt <= hs + HOLD_EDGE_S, tt >= he - HOLD_EDGE_S
            r.update(n_thrust_frames=int(len(TT)), T_mean_g=TT.mean(), T_min_g=TT.min(), T_max_g=TT.max(),
                     T_first_g=float(np.median(TT[e0])), T_last_g=float(np.median(TT[e1])),
                     T_drift_g_per_s=float(np.polyfit(tt - tt.mean(), TT, 1)[0]) if np.ptp(tt) > 0.3 else None)
        bm = bs[bok & (bs["t_mid_s"] >= hs) & (bs["t_mid_s"] <= he)]
        if len(bm):
            w = bm["dur"].to_numpy()
            for col, key in (("I_A", "I"), ("V_V", "V"), ("P_W", "P")):
                x = bm[col].to_numpy(float)
                ok = np.isfinite(x)
                if ok.any():
                    r[key + "_mean"] = float(np.average(x[ok], weights=w[ok]))
                    r[key + "_first"], r[key + "_last"] = float(x[ok][0]), float(x[ok][-1])
            r["V_min"] = float(np.nanmin(bm["V_V"].to_numpy(float)))
            r["n_blue_states"] = int(len(bm))
        if rp is not None:
            rm = rp[(rp["voiced"] == 1) & rp["rpm"].notna() & (rp["t_s"] >= hs + lag) & (rp["t_s"] <= he + lag)]
            nh = int(((rp["t_s"] >= hs + lag) & (rp["t_s"] <= he + lag)).sum())
            if len(rm) >= 3 and len(rm) >= 0.5 * nh:
                x, tx = rm["rpm"].to_numpy(float), rm["t_s"].to_numpy(float)
                e0, e1 = tx <= hs + lag + HOLD_EDGE_S, tx >= he + lag - HOLD_EDGE_S
                r.update(rpm_mean=x.mean(), rpm_std=x.std(ddof=1), n_rpm_hops=int(len(x)),
                         rpm_first=float(np.median(x[e0])) if e0.any() else None,
                         rpm_last=float(np.median(x[e1])) if e1.any() else None,
                         rpm_drift_per_s=float(np.polyfit(tx - tx.mean(), x, 1)[0]) if np.ptp(tx) > 0.3 else None)
            else:
                fl.append("no_rpm")
        # events: other fast segments inside the hold
        ev = []
        for j, s in enumerate(segs):
            if j in used or s["t0"] < hs or s["t1"] > he:
                continue
            Tl = np.nanmean(S["Ts"][s["ia"]:s["ib"] + 1])
            if abs(s["dT"]) < max(EVENT_MIN[0], EVENT_MIN[1] * Tl):
                continue
            b0 = bs[bok & (bs["t_end_s"] < s["t0"])].tail(1)
            b1 = bs[bok & (bs["t_start_s"] > s["t1"])].head(1)
            ev.append("%.2f-%.2f s dT %+.0f g%s" % (
                s["t0"], s["t1"], s["dT"],
                (" (I %s->%s A, V %s->%s V)" % (b0["I_A"].iloc[0], b1["I_A"].iloc[0], b0["V_V"].iloc[0], b1["V_V"].iloc[0]))
                if len(b0) and len(b1) else ""))
        if ev:
            fl.append("thrust_event")
        r["events"] = "; ".join(ev)
        r["flags"] = ";".join(fl)
        rows.append(r)
        log("  hold %2d  pos %5g  %7.2f-%7.2f s (%4.1f s)  T %6.0f g (%s -> %s)  I %s A  V %s V  rpm %s%s%s" % (
            k + 1, pos[k], hs, he, he - hs, r.get("T_mean_g", np.nan),
            fmt(r.get("T_first_g"), 0), fmt(r.get("T_last_g"), 0), fmt(r.get("I_mean"), 2), fmt(r.get("V_mean"), 2),
            fmt(r.get("rpm_mean"), 0), ("  flags " + r["flags"]) if r["flags"] else "", ("  EVENTS " + r["events"]) if ev else ""),
            echo=True)

    cols = ["run_id", "point", "throttle_pos", "throttle_pct", "thrust_callout_g", "anchor_t0_s", "anchor_t1_s",
            "anchor_display_g", "anchor_err_g", "hold_start_s", "hold_end_s", "hold_dur_s", "n_thrust_frames",
            "T_mean_g", "T_min_g", "T_max_g", "T_first_g", "T_last_g", "T_drift_g_per_s", "n_blue_states",
            "I_mean", "I_first", "I_last", "V_mean", "V_first", "V_last", "V_min", "P_mean", "P_first", "P_last",
            "n_rpm_hops", "rpm_mean", "rpm_std", "rpm_first", "rpm_last", "rpm_drift_per_s", "events", "flags"]
    write_csv(data_dir / (run_id + "_holds.csv"), cols, rows)

    # ---- per-frame throttle ----
    thr = throttle_at(S["t"])
    frows = [{"t_s": t, "T_g": T, "throttle_pos": q, "throttle_pct": (q + 100.0) / 2.0 if np.isfinite(q) else None,
              "phase": phase_at(t)} for t, T, q in zip(S["t"], S["T"], thr)]
    write_csv(data_dir / (run_id + "_throttle.csv"), ["t_s", "T_g", "throttle_pos", "throttle_pct", "phase"], frows,
              {"t_s": 3, "T_g": 0, "throttle_pos": 1, "throttle_pct": 2})

    # ---- t2 file ----
    n_t2 = n_fill = 0
    if do_t2 and p["t2"].exists():
        with open(p["t2"], newline="") as fh:
            rd = csv.DictReader(fh)
            tcols = rd.fieldnames
            t2 = list(rd)
        for r in t2:
            n_t2 += 1
            note = r.get("notes") or ""
            i = note.find(" | rpm audio")
            base, rpm_part = (note[:i], note[i:]) if i >= 0 else (note, "")
            base = base.split(" | throttle")[0]
            t = fnum(r.get("t_s"))
            q = throttle_at(t)[0] if t is not None else np.nan
            if np.isfinite(q):
                r["throttle_pct"] = "%.1f" % ((q + 100.0) / 2.0)
                ph = phase_at(t)
                base += " | throttle v%s: stick %.1f on -100..+100 (%s; from callouts); throttle_pct = (stick + 100) / 2, ESC range UNVERIFIED" % (
                    SCRIPT_VERSION, q, ph if ph.startswith("hold") else ("interpolated, " + ph if ph else "interpolated"))
                n_fill += 1
            else:
                r["throttle_pct"] = ""
            r["notes"] = base + rpm_part
        tmp = p["t2"].with_name(p["t2"].stem + "_tmp.csv")
        with open(tmp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=tcols)
            w.writeheader()
            w.writerows(t2)
        os.replace(tmp, p["t2"])
        log("  t2 file: throttle_pct filled in %d of %d rows" % (n_fill, n_t2), echo=True)

    if do_plot:
        try:
            plot_run(run_id, S, bs[bok], rp, lag, anchors, holds, moves, segs, used, throttle_at, calls, out_dir)
        except Exception as e:
            log("  plot skipped: %s" % e, echo=True)
    return rows


def fmt(v, nd=3):
    if v is None:
        return ""
    if isinstance(v, (float, np.floating)):
        return "" if not np.isfinite(v) else ("%.*f" % (nd, v))
    return str(v)


def write_csv(path, cols, rows, nd=None):
    tmp = path.with_name(path.stem + "_tmp" + path.suffix)
    with open(tmp, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cols)
        for r in rows:
            w.writerow([fmt(r.get(c), (nd or {}).get(c, 3)) for c in cols])
    os.replace(tmp, path)


# ----------------------------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------------------------
def plot_run(run_id, S, bs, rp, lag, anchors, holds, moves, segs, used, throttle_at, calls, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(5, 1, figsize=(16, 15), sharex=True)
    ax[0].plot(S["t"], S["T"], ".", ms=1.5, color="C0", label="display thrust (valid frames)")
    ax[0].plot(S["tu"], S["Ts"], "-", lw=0.8, color="k", label="smoothed")
    for k, A in enumerate(anchors):
        if A is not None:
            ax[0].plot([A["t0"], A["t1"]], [A["T"]] * 2, "r-", lw=3)
            ax[0].annotate("%s\n%s g" % (calls[k]["throttle_pos"], calls[k]["thrust_callout_g"]), (A["t0"], A["T"]),
                           textcoords="offset points", xytext=(0, 8), fontsize=7, color="r")
    for j, s in enumerate(segs):
        if j not in used:
            ax[0].axvspan(s["t0"], s["t1"], color="orange", alpha=0.35, lw=0)
    ax[0].set_ylabel("thrust, g")
    ax[0].set_title("%s: red = callout anchors, grey = holds, orange = fast thrust change not assigned to a stick move" % run_id)
    tq = np.linspace(S["t"][0], S["t"][-1], 4000)
    ax[1].plot(tq, throttle_at(tq), "-", color="C2")
    ax[1].set_ylabel("stick, -100..+100")
    t_b = np.column_stack([bs["t_start_s"], bs["t_end_s"] + S["dt"]]).ravel()
    for i, (col, lab) in enumerate((("I_A", "current, A"), ("V_V", "voltage, V"))):
        y = np.repeat(bs[col].to_numpy(float), 2)
        ax[2 + i].plot(t_b, y, "-", color="C3" if i == 0 else "C4", lw=1)
        ax[2 + i].set_ylabel(lab)
    a2 = ax[2].twinx()
    a2.plot(t_b, np.repeat(bs["P_W"].to_numpy(float), 2), "-", color="C1", lw=0.7, alpha=0.6)
    a2.set_ylabel("power, W (orange)")
    if rp is not None:
        v = rp[(rp["voiced"] == 1) & rp["rpm"].notna()]
        ax[4].plot(v["t_s"] - lag, v["rpm"], ".", ms=1.2, color="C0")
        ax[4].set_ylabel("audio rpm (shifted %+.2f s\nto display time)" % -lag)
    else:
        ax[4].set_ylabel("audio rpm (not run)")
    for a in ax:
        for k, (hs, he) in holds.items():
            a.axvspan(hs, he, color="0.85", lw=0, zorder=-1)
        a.grid(alpha=0.3)
    ax[-1].set_xlabel("video time, s")
    fig.tight_layout()
    fig.savefig(out_dir / (run_id + "_timeseries.png"), dpi=70)
    plt.close(fig)


def plot_session(session, allrows, out_dir):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    df = pd.DataFrame(allrows)
    fig, ax = plt.subplots(2, 3, figsize=(17, 9))
    items = [("T_mean_g", "thrust, g (hold mean)"), ("rpm_mean", "audio rpm (hold mean)"), ("I_mean", "current, A"),
             ("V_mean", "voltage under load, V"), ("P_mean", "electrical power, W"), ("T_drift_g_per_s", "thrust drift in hold, g/s")]
    for a, (col, lab) in zip(ax.ravel(), items):
        for n, (rid, g) in enumerate(df.groupby("run_id", sort=False)):
            if col in g and g[col].notna().any():
                a.plot(g["throttle_pos"], g[col], "o-", ms=4, color="C%d" % n, label=rid.replace(session + "_", ""))
        a.set_xlabel("stick position (-100..+100)")
        a.set_ylabel(lab)
        a.grid(alpha=0.3)
    ax[0, 0].legend(fontsize=8)
    fig.suptitle("%s: per-hold means against throttle (stick) position" % session)
    fig.tight_layout()
    fig.savefig(out_dir / (session + "_vs_throttle.png"), dpi=75)
    plt.close(fig)


# ----------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Throttle position against time from logged callouts; per-hold statistics.")
    ap.add_argument("callouts", help="callouts CSV (run_id, video_file, prop, point, throttle_pos, thrust_callout_g, source)")
    ap.add_argument("--run-id", action="append", default=None, help="only this run (repeatable)")
    ap.add_argument("--anchor", action="append", default=[], help="RUN:POINT=T forces callout POINT of RUN onto the "
                                                                    "thrust state on screen at video time T s")
    ap.add_argument("--data-dir", default=str(HERE / "data"))
    ap.add_argument("--out-dir", default=str(HERE / "out" / "throttle"))
    ap.add_argument("--state-lag", type=float, default=-0.35, help="audio window shift for the hold rpm, s (as audio_rpm.py)")
    ap.add_argument("--no-t2", action="store_true", help="do not write throttle_pct into RUN_t2.csv")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    cpath = Path(args.callouts)
    data_dir, out_dir = Path(args.data_dir), Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    session = re.sub(r"_throttle_callouts$", "", cpath.stem)
    logf = open(out_dir / (session + "_log.txt"), "w")

    def log(msg, echo=False):
        logf.write(msg + "\n")
        logf.flush()
        if echo:
            print(msg, flush=True)

    log("throttle_merge.py v%s  %s  callouts %s" % (SCRIPT_VERSION, time.strftime("%Y-%m-%d %H:%M:%S"), cpath.name), echo=True)
    with open(cpath, newline="") as fh:
        calls = list(csv.DictReader(fh))
    by_run = {}
    for c in calls:
        by_run.setdefault(c["run_id"], []).append(c)
    forced = {}
    for a in args.anchor:
        m = re.match(r"^(.+):(\d+)=([-\d.]+)$", a)
        if not m:
            sys.exit("bad --anchor %r (want RUN:POINT=T)" % a)
        pts = [int(c["point"]) for c in sorted(by_run.get(m.group(1), []), key=lambda c: int(c["point"]))]
        if int(m.group(2)) not in pts:
            sys.exit("--anchor %r: no such run or point" % a)
        forced.setdefault(m.group(1), {})[pts.index(int(m.group(2)))] = float(m.group(3))
    allrows = []
    for rid, cl in by_run.items():
        if args.run_id and rid not in args.run_id:
            continue
        rows = process_run(rid, cl, data_dir, out_dir, forced.get(rid, {}), args.state_lag, not args.no_t2,
                           not args.no_plot, log)
        if rows:
            allrows += rows
    if allrows and not args.run_id:
        cols = list(dict.fromkeys(k for r in allrows for k in r))
        write_csv(data_dir / (session + "_holds.csv"), cols, allrows)
        if not args.no_plot:
            try:
                plot_session(session, allrows, out_dir)
            except Exception as e:
                log("session plot skipped: %s" % e, echo=True)
    log("outputs: %s/RUN_holds.csv, RUN_throttle.csv, RUN_t2.csv (throttle_pct); plots and log in %s" % (data_dir, out_dir), echo=True)
    logf.close()


if __name__ == "__main__":
    main()
