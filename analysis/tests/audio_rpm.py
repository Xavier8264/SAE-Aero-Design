#!/usr/bin/env python3
"""
audio_rpm.py -- prop RPM against time from the sound track of a thrust-stand video (blade-pass method),
and the RPM for each MT10PRO display state, written into the t2 CSV from read_mt10pro_video.py.

Written for the SAE Aero Design 2027 T-2 static thrust stand (TEST_PLAN.md 3.4 and 3.8 item 2).
Developed on 12x8E.MOV (2026-09-24).

Physics: a B-blade prop at shaft rate f_r = RPM / 60 makes a tone family at the blade-pass frequency
F = B * f_r and its harmonics k * F. In 12x8E.MOV (2-blade APC 12x8E on the SunnySky X2820 800 KV) the family
is visible to k = 10 and beyond, and the motor's electromagnetic whine (2 x 7 pole pairs = 14 f_r = 7 F) falls
on the same family. RPM = 60 * F / B.

Method (accuracy first):
  1. Audio: ffmpeg decodes the first audio stream (both channels, native sample rate). The audio start
     time minus the video start time (ffprobe) is added, so t is on the same clock as the video frames.
  2. Spectra: Hann window of 8192 samples (0.171 s at 48 kHz), hop 0.02 s, zero-padded 4x; the powers of
     the two channels are summed.
  3. Level above background L (dB) for every bin: the local floor is the 30th percentile of the bins
     within +/- 1/6 octave (at least +/- 30 Hz). Stationary lines are then removed: the 20th percentile
     over time of each bin's level is subtracted where it is positive (e.g. the 120 Hz hum in 12x8E.MOV,
     present with the motor off).
  4. Harmonic salience of every candidate F on a 1/576-octave grid: the mean over k = 1..K of
     clip(L(k F) - 6, -3, 20) (a missing harmonic costs -3, so F/2 scores below F), minus a sub-harmonic
     penalty for lines at (k - 1/2) F and (k - 1/3) F, which a lower fundamental would explain (so 2F and 3F
     score below F). For a 2-blade prop a half-position line counts only if it is within 6 dB of its
     neighbouring harmonics: prop imbalance puts weak 1/rev lines there, which must not halve the reading.
  4b. Power prior (needs RUN_blue_states.csv and APC PER3 data for the prop): while a display state is on
     screen (+/- 1 s for the unknown display latency), shaft power <= P_elec - P_idle, so
     RPM <= 1.3 * RPM at which APC Cp (x 0.8) absorbs P_elec - P_idle + 1 W. Candidates above that are
     scored as missing. This removes the motor whine (7 F, 14 F) at low throttle. Hops where every covering
     state shows idle current (within 0.05 A of the lowest, which must be < 0.3 A) are motor-off: no F.
  4c. Thrust window (v1.1; needs the same inputs): while a display state is on screen (same lag and +/- 1 s),
     the measured thrust above the motor-off tare, T_min..T_max over the state (>= 100 g), fixes the RPM through
     APC Ct(RPM, J = 0) to within a factor f either way (--tw-factor, default 1.25 since v1.2; 1.4 in v1.1):
     F is limited to [F(T_min) / f, f F(T_max)], the
     union over all covering states (a state below 100 g, without thrust, or motor-off leaves the hop free).
     Inside the window a lower fundamental F/m below the window is ruled out, so the sub-harmonic penalty at
     that m is dropped. An F/2 or 2F reading is a factor 4 in thrust and falls outside. Added because on
     the 2026-09-25 videos the 1/rev lines are as strong as the blade-pass lines, so from sound alone F/2
     scored higher than F at high throttle (12X6E Trial #1 at ~100 s: 130 Hz tracked, display 1701 g needs
     ~260 Hz). v1.2 narrowed f from 1.4 to 1.25 because at low throttle a 2/3 F reading (0.67, inside 1/1.4 =
     0.71) was tracked: 12X10E Trial #2 at 22-37 s (270 g) jumped between ~3050 rpm (measured / APC thrust
     0.83-0.98) and ~2050 rpm (1.4-1.9); with 1.25 the states with measured / APC > 1.3 fell from 25 to 8,
     and 12x8E.MOV was unchanged (0 of 151 states moved by > 50 rpm).
     Tare (v1.3): median thrust of the motor-off states within 10 s of the motor-on span (first to last
     motor-on state). v1.2 used every motor-off state; on 9X4.5E Trial #1 the stand was handled after the
     run (display 77 g at 162-209 s, 0 g before the run and at 106-127 s), which set the tare to 77 g and
     dropped the window from every state below 177 g. Falls back to all motor-off states if none is that close.
  5. Viterbi over time on 1/96-octave cells plus an unvoiced state: cost = -salience; unvoiced cost
     = -voicing threshold; a switch penalty between voiced and unvoiced; a penalty on frequency moves beyond
     a free slew per hop, and no move over 1/8 octave per hop. This stops octave jumps.
  6. Refinement of each voiced hop: each harmonic's peak in the raw spectrum (parabolic interpolation on
     dB), then F = weighted mean of f_k / k with weights k^2 * SNR (SNR capped at 30 dB), one round of
     outlier rejection. The weighted spread of f_k / k is reported as a quality number.
  7. Display states (RUN_blue_states.csv): mean, std, min, max and slope of RPM over each state's time
     window, a plausibility check of the measured thrust against APC PER3 Ct(RPM, J = 0) (catches an
     octave error, which is a factor 4 in thrust), then rpm / rpm_source / notes filled in RUN_t2.csv.
     State flags: motor_off (idle current; no RPM), unsteady (std > 0.5 pct of mean), no_rpm (under half
     of the hops voiced, or under 3), rpm_thrust_mismatch (measured / APC thrust outside 0.5-2.0 while
     the larger of the two is >= 100 g). Only states without motor_off, no_rpm or mismatch are merged.

Usage (from the repo root, Git Bash; run read_mt10pro_video.py on the same video first for the state merge):
    python analysis/tests/audio_rpm.py analysis/tests/video/12x8E.MOV
Options: --run-id (default the video name), --blades, --order, --rpm-min, --rpm-max, --kmax, --win, --hop,
         --voicing, --state-lag, --prop (APC name for the prior and thrust check; default from the t2 file
         or the video name), --rho, --tw-factor (thrust window half-width in RPM, default 1.25),
         --no-prior (sound alone), --no-thrust-window (power prior only, as v1.0),
         --no-merge, --no-plot.

Outputs (RUN = --run-id):
    analysis/tests/data/RUN_rpm.csv          one row per hop: t, voiced, rpm, blade-pass Hz, quality,
                                             F_limit_Hz (power-prior bound; blank = none, 0 = motor off),
                                             F_lo_Hz, F_hi_Hz (thrust window; blank = none)
    analysis/tests/data/RUN_rpm_states.csv   one row per blue display state: RPM statistics + thrust check
    analysis/tests/data/RUN_t2.csv           rpm, rpm_source, notes filled in place (other columns untouched)
    analysis/tests/out/audio/RUN/            log, spectrogram + track plot
  Re-running read_mt10pro_video.py rewrites RUN_t2.csv without RPM; run this script again after it.

Limits and UNVERIFIED items:
  - Display latency: a state's RPM is the mean over the time the state is on screen, shifted by --state-lag
    (default -0.35 s). On 12x8E.MOV the fit of displayed I, P against the audio RPM is best at -0.35 s and
    of the state's mean thrust at -0.40 s (both halves of the run agree within 0.05 s; rms 4.3 -> 2.5 pct
    for I). One video, one MT10PRO; check again on the next video. Steady points are unaffected.
  - Harmonic family per recording: 12x8E.MOV has blade-pass lines to k = 10 and weak 1/rev lines (default
    --blades 2 --kmax 10). The 2026-09-25 videos (phone in another place) show only shaft harmonics 1-4, with
    the 1/rev lines as strong as the blade-pass lines; there --blades 1 --kmax 4 (track the shaft rate) gave
    RPM on 44 of 45 states against 18 of 45 with the defaults (12X6E Trial #2, 30-50 s). Look at the
    spectrum of a new recording before choosing.
  - Needs one dominant prop. Two motors at slightly different RPM (TEST_PLAN D5) give two close families.
  - --order 7 (no-prop run, motor electrical frequency, 7 pole pairs) is untested: the strongest no-prop
    line may be 2 x electrical (14 f_r), which would read as double the RPM. Check against the optical tach.
  - The thrust check uses sea-level-ish density (--rho, default 1.20 kg/m^3) and only flags a ratio
    outside 0.5-2.0; it is not the THRUST_FACTOR calibration (that is reduce_thrust.py's job).
  - The power prior trusts the video-read current and voltage; a misread state widens or narrows the bound
    for about 1 s. The 1.3 and 0.8 margins cover APC Cp error and display latency, not a gross misread.
  - Without the prior (no states, unknown prop, or --no-prior), low-throttle readings can lock on the motor
    whine at 7 F (seen at 5-7 s and 22-25 s in 12x8E.MOV).
  - The thrust window trusts APC Ct at J = 0 to about +/- 25 pct in RPM (a factor 1.56 in thrust; measured / APC
    was 0.87-1.06 on 12x8E.MOV and 0.76-1.05 on 12X10E Trial #2 where tracked correctly) and the tare from
    the motor-off states. Below 100 g there is no lower bound, so an F/2 reading at low throttle is still possible
    there (the rpm_thrust_mismatch check is gated at 100 g as well). Because the window is built from the measured
    thrust, the rpm_thrust_mismatch check can no longer catch an octave error where the window applies; it
    still catches a gross thrust misread. A wrong line just inside the window can still be tracked and then
    sits at the window edge: 12X10E Trial #2 at 17-21 s (158 g) reads ~1760 rpm against ~2450 rpm on the
    neighbouring states (measured / APC 1.5-1.7 against 0.8-0.9). Check T_over_Tapc in RUN_rpm_states.csv.
Requires: Python 3, numpy, scipy, ffmpeg + ffprobe on PATH; matplotlib for the plot; pandas for the thrust check.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
from scipy import fft as sfft
from scipy.ndimage import maximum_filter1d

SCRIPT_VERSION = "1.3"
HERE = Path(__file__).resolve().parent
FINE = 576                       # candidate grid, steps per octave (0.12 pct)
CELL = 6                         # fine steps per Viterbi cell (1/96 octave)
C_THR, C_LO, C_HI = 6.0, -3.0, 20.0   # harmonic score clip(L - C_THR, C_LO, C_HI), L in dB above background
SUB_M, SUB_GAMMA = (2, 3), 1.0   # sub-harmonic penalty: orders checked, weight
SUB_REL = 6.0                    # dB: for a 2-blade prop a half-position line counts only above (neighbour
                                 # harmonics - SUB_REL), so prop imbalance (1/rev) lines do not halve F
REF_THR = 8.0                    # a harmonic enters the refinement if its peak is this many dB above background
SNR_CAP = 30.0                   # dB cap on refinement weights
G0 = 9.80665


# ----------------------------------------------------------------------------------------------
# Audio access
# ----------------------------------------------------------------------------------------------
def probe(path):
    """ffprobe the first audio stream (sample rate, start) and the first video stream (start, frame rate)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=index,codec_type,sample_rate,channels,start_time,avg_frame_rate",
                        "-of", "json", str(path)], capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("ffprobe failed on %s: %s" % (path, r.stderr.strip()[:300]))
    st = json.loads(r.stdout).get("streams", [])
    a = next((s for s in st if s.get("codec_type") == "audio"), None)
    v = next((s for s in st if s.get("codec_type") == "video"), None)
    if a is None:
        sys.exit("no audio stream in %s" % path)

    def num(s, key, default):
        try:
            return float(s.get(key, default))
        except (TypeError, ValueError):
            return default
    fps = None
    if v is not None and "/" in str(v.get("avg_frame_rate", "")):
        n, d = v["avg_frame_rate"].split("/")
        fps = float(n) / float(d) if float(d) else None
    return {"fs": int(num(a, "sample_rate", 48000)), "channels": int(num(a, "channels", 1)),
            "a_start": num(a, "start_time", 0.0), "v_start": num(v, "start_time", 0.0) if v else 0.0, "fps": fps}


def load_audio(path, fs):
    """Decode the first audio stream to float32 at its native rate, as 2 channels (mono is duplicated)."""
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", str(path), "-map", "0:a:0", "-ac", "2",
                        "-ar", str(fs), "-f", "f32le", "-"], capture_output=True)
    if r.returncode != 0 or not r.stdout:
        sys.exit("ffmpeg could not decode the audio of %s: %s" % (path, r.stderr.decode(errors="replace")[:300]))
    return np.frombuffer(r.stdout, np.float32).reshape(-1, 2)


# ----------------------------------------------------------------------------------------------
# Spectra and background
# ----------------------------------------------------------------------------------------------
def stft_power(x, nwin, hop, nfft, nbins, chunk=256):
    """Hann power spectra summed over channels, frames centered on samples 0, hop, 2*hop, ... (T x nbins)."""
    w = np.hanning(nwin + 1)[:-1].astype(np.float32)              # periodic Hann
    n = x.shape[0]
    xp = np.pad(x, ((nwin // 2, nwin // 2), (0, 0)))
    T = 1 + (n - 1) // hop
    P = np.zeros((T, nbins), np.float32)
    ar = np.arange(nwin)
    for a in range(0, T, chunk):
        b = min(T, a + chunk)
        idx = (np.arange(a, b) * hop)[:, None] + ar[None, :]
        for ch in range(x.shape[1]):
            X = sfft.rfft(xp[idx, ch] * w, nfft, axis=1, workers=-1)[:, :nbins]
            P[a:b] += (X.real ** 2 + X.imag ** 2).astype(np.float32)
    return P


def spectral_floor(Pdb, f, q=30.0, half_oct=1.0 / 6.0, min_half_hz=30.0, per_oct=24):
    """Per-hop noise floor (dB): q-th percentile of the bins within +/- half_oct octave (at least
    +/- min_half_hz) of each center of a 1/per_oct-octave grid, interpolated in log f to every bin."""
    fc = 10.0 * 2.0 ** (np.arange(int(np.ceil(np.log2(f[-1] / 10.0) * per_oct)) + 1) / per_oct)
    fl = np.empty((Pdb.shape[0], len(fc)), np.float32)
    for i, c in enumerate(fc):
        ia = max(1, int(np.searchsorted(f, min(c * 2 ** -half_oct, c - min_half_hz))))
        ib = max(ia + 3, int(np.searchsorted(f, max(c * 2 ** half_oct, c + min_half_hz))))
        fl[:, i] = np.percentile(Pdb[:, ia:ib], q, axis=1)
    lfc = np.log(fc)
    lf = np.log(np.maximum(f, 1e-3))
    j = np.clip(np.searchsorted(lfc, lf) - 1, 0, len(fc) - 2)
    w = np.clip((lf - lfc[j]) / (lfc[j + 1] - lfc[j]), 0.0, 1.0).astype(np.float32)
    return fl[:, j] * (1 - w) + fl[:, j + 1] * w


# ----------------------------------------------------------------------------------------------
# Salience, tracking, refinement
# ----------------------------------------------------------------------------------------------
def salience(L, df, Fgrid, K, rel_m=None, F_lo=None, chunk=100):
    """Harmonic salience for every hop and candidate F:
        mean over k = 1..K of clip(L(k F) - C_THR, C_LO, C_HI)                        (harmonics present; a missing
                                                                                        one costs C_LO, so F/2 loses)
      - SUB_GAMMA * max over m in SUB_M of mean over k, j of clip(L((k - j/m) F) - thr, 0, C_HI)
                                                                                       (lines a lower fundamental F/m
                                                                                        would explain, so 2F, 3F lose)
    thr = C_THR, except at m = rel_m = 2 (a 2-blade prop with F the blade-pass frequency), where
    thr = max(C_THR, mean(L((k-1) F), L(k F)) - SUB_REL) (for k = 1: L(F) - SUB_REL). Prop imbalance puts
    1/rev lines at exactly those positions, typically 10-18 dB below the neighbouring blade-pass lines
    (12x8E.MOV); the true harmonics of F/2 are about as strong as their neighbours and are still penalized.
    The penalty does not depend on how strong the fundamental is. L is max-pooled over +/- 2 bins so a harmonic
    between grid points is not lost (the grid step is 0.12 pct). 7F / 14F (motor whine) are not separated here:
    that is the power prior's job. F_lo (per hop, Hz; 0 = none): the thrust window's lower limit; where F / m is
    below it, the lower fundamental is ruled out and the penalty at that m is dropped."""
    Lp = maximum_filter1d(L, size=5, axis=1, mode="nearest")
    kk = np.arange(1, K + 1)
    idx = np.rint(kk[None, :] * Fgrid[:, None] / df).astype(np.int64)
    sub = [(m, np.rint(np.concatenate([kk - j / m for j in range(1, m)])[None, :] * Fgrid[:, None] / df)
            .astype(np.int64)) for m in SUB_M]
    S = np.empty((L.shape[0], len(Fgrid)), np.float32)
    for a in range(0, L.shape[0], chunk):
        Lc = Lp[a:a + chunk]
        H = Lc[:, idx]                                                   # (hops, F, K)
        pens = []
        for m, si in sub:
            thr = C_THR
            if m == rel_m == 2:                            # (k - 1/2) F sits between harmonics k - 1 and k
                thr = np.maximum(C_THR, 0.5 * (np.concatenate([H[..., :1], H[..., :-1]], -1) + H) - SUB_REL)
            pm = np.clip(Lc[:, si] - thr, 0.0, C_HI).mean(-1)
            if F_lo is not None:
                pm[Fgrid[None, :] / m < F_lo[a:a + chunk, None]] = 0.0
            pens.append(pm)
        S[a:a + chunk] = np.clip(H - C_THR, C_LO, C_HI).mean(-1) - SUB_GAMMA * np.max(pens, axis=0)
    return S


def track(Sc, s_uv, pen_v, slew_cells, beta_cell, M):
    """Viterbi over hops x cells plus an unvoiced state (index J). Returns the state per hop (J = unvoiced)."""
    T, J = Sc.shape
    cols = np.arange(2 * M + 1) - M                                  # predecessor offset j' - j
    pen = beta_cell * np.maximum(0.0, np.abs(cols) - slew_cells)
    big = 1e18
    D = np.concatenate([-Sc[0].astype(np.float64), [-s_uv]])
    bp = np.zeros((T, J + 1), np.int32)
    pad = np.full(M, big)
    rows = np.arange(J)
    for t in range(1, T):
        Dv = D[:J]
        C = np.lib.stride_tricks.sliding_window_view(np.concatenate([pad, Dv, pad]), 2 * M + 1) + pen[None, :]
        c = np.argmin(C, axis=1)
        best = C[rows, c]
        from_uv = D[J] + pen_v
        use_uv = from_uv < best
        newD = np.empty(J + 1)
        newD[:J] = np.where(use_uv, from_uv, best) - Sc[t]
        bp[t, :J] = np.where(use_uv, J, rows + c - M)
        jv = int(np.argmin(Dv))
        if Dv[jv] + pen_v < D[J]:
            newD[J], bp[t, J] = Dv[jv] + pen_v - s_uv, jv
        else:
            newD[J], bp[t, J] = D[J] - s_uv, J
        D = newD - newD.min()
    path = np.zeros(T, np.int64)
    path[-1] = int(np.argmin(D))
    for t in range(T - 1, 0, -1):
        path[t - 1] = bp[t, path[t]]
    return path


def refine(Pdb_row, L_row, df, Fc, K):
    """Harmonic peaks near k*Fc -> (F, spread_Hz, harmonics used, max SNR dB) or None."""
    est, wts, ks, snr = [], [], [], []
    n = len(L_row)
    for k in range(1, K + 1):
        f0 = k * Fc
        half = max(2.0 * df, 0.004 * f0)
        a, b = int(np.ceil((f0 - half) / df)), int(np.floor((f0 + half) / df))
        if a < 1 or b >= n - 1:
            continue
        m = a + int(np.argmax(Pdb_row[a:b + 1]))
        if m == a or m == b or L_row[m] < REF_THR:        # not a local maximum inside the window, or too weak
            continue
        y0, y1, y2 = float(Pdb_row[m - 1]), float(Pdb_row[m]), float(Pdb_row[m + 1])
        den = y0 - 2.0 * y1 + y2
        d = 0.5 * (y0 - y2) / den if den < 0 else 0.0
        est.append((m + d) * df / k)
        wts.append(k * k * 10.0 ** (min(float(L_row[m]), SNR_CAP) / 10.0))
        ks.append(k)
        snr.append(float(L_row[m]))
    if not est:
        return None
    est, wts, ks, snr = np.array(est), np.array(wts), np.array(ks), np.array(snr)
    keep = np.ones(len(est), bool)
    for _ in range(2):
        F = float(np.sum(wts[keep] * est[keep]) / np.sum(wts[keep]))
        r = est - F
        mad = 1.4826 * float(np.median(np.abs(r[keep] - np.median(r[keep]))))
        new = np.abs(r) <= max(4.0 * mad, 0.002 * F)
        if not new.any() or np.array_equal(new, keep):
            break
        keep = new
    F = float(np.sum(wts[keep] * est[keep]) / np.sum(wts[keep]))
    spread = float(np.sqrt(np.sum(wts[keep] * (est[keep] - F) ** 2) / np.sum(wts[keep])))
    return F, spread, ks[keep], float(snr[keep].max())


# ----------------------------------------------------------------------------------------------
# APC PER3 static data (reusing analysis/sizing/propulsion.py) and the display-power prior
# ----------------------------------------------------------------------------------------------
PRIOR_PAD = 1.0          # s: a hop is bounded by every display state within this time (display latency + refresh)
PRIOR_N_FACTOR = 1.3     # rpm allowed above the power bound (the bound already assumes 100 pct motor efficiency)
PRIOR_CP_FACTOR = 0.8    # APC Cp may be this much too high
PRIOR_DP_W = 1.0         # W added to the power above idle (display resolution, idle drift)
IDLE_MAX_A = 0.3         # the lowest display current is taken as ESC idle only if it is below this
OFF_DI_A = 0.05          # a state within this of the idle current is 'motor off'
TW_MIN_G = 100.0         # g above tare: a state bounds F from below only if its lowest thrust reaches this
TARE_PAD_S = 10.0        # s: the tare uses motor-off states within this of the motor-on span (not post-run handling)
TW_FACTOR = 1.25         # thrust window half-width in RPM (x / 1.25 .. x 1.25 = a factor 1.56 in thrust); --tw-factor


def apc_model(prop, log):
    """dict(T_g(rpm, rho) in grams at J = 0, Cp_min at J = 0, D_m) for a prop name like 12x8E, or None."""
    if not prop:
        return None
    try:
        sys.path.insert(0, str(HERE.parent / "sizing"))
        from propulsion import parse_apc, coeffs
        p = parse_apc(prop.lower().replace(".", ""))
    except Exception as e:                                    # missing data file or pandas: no check, no bound
        log("APC data for '%s' not loaded (%s): no thrust check, no power bound" % (prop, e), echo=True)
        return None

    def T_g(rpm, rho):
        ct, _ = coeffs(p, rpm, 0.0)
        return float(ct) * rho * (rpm / 60.0) ** 2 * p["D_m"] ** 4 / G0 * 1000.0
    cp_min = min(float(coeffs(p, r, 0.0)[1]) for r in p["rpm"])
    return {"T_g": T_g, "cp_min": cp_min, "D_m": p["D_m"], "name": p["name"]}


def power_prior(states, t, order, apc, rho, lag, fps, log):
    """Per-hop upper limit on the tracked frequency from the MT10PRO electrical power (-inf = motor off).
    Shaft power <= electrical power above ESC idle, and shaft power = Cp rho n^3 D^5 at J = 0, so
        n <= PRIOR_N_FACTOR * ((P - P_idle + PRIOR_DP_W) / (PRIOR_CP_FACTOR * Cp_min * rho * D^5))^(1/3).
    This rules out locking onto the motor whine at 7F and 14F (12N14P: 14 f_r = 7F), which would need
    343 or 2744 times the shaft power; it does not separate F from 2F (the 1/k salience weights do).
    Motor off: the display current is within OFF_DI_A of the idle current (the lowest current in the run, if below
    IDLE_MAX_A). A hop is limited by the most permissive state within PRIOR_PAD s; hops no state covers are free."""
    rec = []
    for s in states:
        I, P = fnum(s.get("I_A")), fnum(s.get("P_W"))
        clean = not re.search(r"weak|P_ne", s.get("flags") or "")
        rec.append((float(s["t_start_s"]), float(s["t_end_s"]), I, P, clean))
    Ic = [r[2] for r in rec if r[2] is not None and r[4]]
    I_idle = min(Ic) if Ic and min(Ic) < IDLE_MAX_A else None
    off = [I_idle is not None and r[2] is not None and r[2] <= I_idle + OFF_DI_A for r in rec]
    Poff = [r[3] for r, o in zip(rec, off) if o and r[3] is not None]
    P_idle = float(np.median(Poff)) if Poff else 0.0
    Flim = np.full(len(t), -np.inf)
    covered = np.zeros(len(t), bool)
    for (ta, tb, I, P, clean), o in zip(rec, off):
        sel = (t >= ta + lag - PRIOR_PAD) & (t < tb + 1.0 / fps + lag + PRIOR_PAD)
        covered |= sel
        if o:
            continue
        if apc is None or P is None:
            Fs = np.inf
        else:
            n = PRIOR_N_FACTOR * ((max(P - P_idle, 0.0) + PRIOR_DP_W)
                                  / (PRIOR_CP_FACTOR * apc["cp_min"] * rho * apc["D_m"] ** 5)) ** (1.0 / 3.0)
            Fs = order * n
        Flim[sel] = np.maximum(Flim[sel], Fs)
    Flim[~covered] = np.inf
    log("power prior: %d display states, %d motor-off (idle %s A, %.2f W); %s; %d hops motor off, %d bounded, %d free"
        % (len(rec), sum(off), "%.2f" % I_idle if I_idle is not None else "unknown", P_idle,
           "bound from APC %s Cp_min %.4f" % (apc["name"], apc["cp_min"]) if apc else "no rpm bound (no APC data)",
           np.isneginf(Flim).sum(), np.isfinite(Flim).sum(), np.isposinf(Flim).sum()), echo=True)
    return Flim, off


def thrust_window(states, t, order, apc, rho, lag, fps, off, log, factor=TW_FACTOR):
    """Per-hop window [F_lo, F_hi] (Hz of the tracked order) from the displayed thrust (0 / inf = no bound).
    Tare T0 = median thrust of the motor-off states within TARE_PAD_S of the motor-on span (all motor-off states
    if none is that close; 0 if there are none). A state with T_min - T0 >= TW_MIN_G gives
    [order * n(T_min - T0) / factor, order * n(T_max - T0) * factor], n(T) from APC Ct(RPM, J = 0) at rho;
    any other covering state (low or no thrust, motor off) gives no bound. A hop takes the union over the states
    within PRIOR_PAD s, so one misread state can only widen the window, never narrow it."""
    rr = np.linspace(100.0, 40000.0, 4000)
    Tt = np.array([apc["T_g"](r, rho) for r in rr])                 # monotonic in rpm (T ~ rpm^2)

    def n_of_T(T):
        return float(np.interp(T, Tt, rr)) / 60.0
    on_t = [(float(s["t_start_s"]), float(s["t_end_s"])) for s, o in zip(states, off) if not o]
    Toff = [(fnum(s.get("T_g_mean")), float(s["t_start_s"]), float(s["t_end_s"])) for s, o in zip(states, off) if o]
    Toff = [v for v in Toff if v[0] is not None]
    near = []
    if on_t:
        a, b = min(x[0] for x in on_t), max(x[1] for x in on_t)
        near = [v for v in Toff if max(a - v[2], v[1] - b, 0.0) <= TARE_PAD_S]
        Toff = near or Toff
    Toff = [v[0] for v in Toff]
    T0 = float(np.median(Toff)) if Toff else 0.0
    F_lo = np.full(len(t), np.inf)
    F_hi = np.full(len(t), -np.inf)
    covered = np.zeros(len(t), bool)
    n_used = 0
    for s, o in zip(states, off):
        ta, tb = float(s["t_start_s"]), float(s["t_end_s"])
        sel = (t >= ta + lag - PRIOR_PAD) & (t < tb + 1.0 / fps + lag + PRIOR_PAD)
        covered |= sel
        tmin, tmax = fnum(s.get("T_g_min")), fnum(s.get("T_g_max"))
        if o or tmin is None or tmax is None or tmin - T0 < TW_MIN_G:
            lo, hi = 0.0, np.inf
        else:
            lo, hi = order * n_of_T(tmin - T0) / factor, order * n_of_T(tmax - T0) * factor
            n_used += 1
        F_lo[sel] = np.minimum(F_lo[sel], lo)
        F_hi[sel] = np.maximum(F_hi[sel], hi)
    F_lo[~covered], F_hi[~covered] = 0.0, np.inf
    act = F_lo > 0
    log("thrust window: tare %.1f g (median of %d motor-off states%s); %d of %d states >= %.0f g above tare bound F; "
        "%d hops bounded (x/%.2f in rpm), %d free"
        % (T0, len(Toff), " within %.0f s of the motor-on span" % TARE_PAD_S if near else "", n_used, len(states), TW_MIN_G, act.sum(), factor, (~act).sum()), echo=True)
    return F_lo, F_hi


# ----------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------
def fnum(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description="Prop RPM from a thrust-stand video's sound (blade-pass tracking).")
    ap.add_argument("video", help="video (or audio) file")
    ap.add_argument("--run-id", default=None, help="default: the video name; must match read_mt10pro_video.py's")
    ap.add_argument("--data-dir", default=str(HERE / "data"))
    ap.add_argument("--debug-dir", default=None, help="default analysis/tests/out/audio/RUN")
    ap.add_argument("--blades", type=int, default=2)
    ap.add_argument("--order", type=float, default=None,
                    help="shaft order of the tracked tone family (default = blades; 7 = motor electrical, no prop, UNTESTED)")
    ap.add_argument("--rpm-min", type=float, default=600.0)
    ap.add_argument("--rpm-max", type=float, default=15000.0, help="X2820 800 KV no-load on a full 4S pack is about 13,400")
    ap.add_argument("--kmax", type=int, default=10, help="harmonics used")
    ap.add_argument("--win", type=int, default=8192, help="window, samples")
    ap.add_argument("--hop", type=float, default=0.02, help="hop, s")
    ap.add_argument("--voicing", type=float, default=1.5, help="salience threshold for 'tone present'")
    ap.add_argument("--state-lag", type=float, default=-0.35,
                    help="shift of each display state's audio window, s; negative = earlier, because the display shows"
                         " values measured about 0.35 s before it changes (fit on 12x8E.MOV)")
    ap.add_argument("--prop", default=None, help="for the thrust check; default from the t2 file or the video name")
    ap.add_argument("--rho", type=float, default=1.20, help="air density for the thrust check and power bound, kg/m^3")
    ap.add_argument("--no-prior", action="store_true", help="track from sound alone (no display power bound, no motor-off gating)")
    ap.add_argument("--tw-factor", type=float, default=TW_FACTOR,
                    help="thrust window half-width in RPM (x / f .. x f; v1.1 used 1.4)")
    ap.add_argument("--no-thrust-window", action="store_true", help="power prior only (v1.0 behaviour)")
    ap.add_argument("--no-merge", action="store_true", help="do not write rpm into RUN_t2.csv")
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()

    video = Path(args.video).resolve()
    if not video.exists():
        sys.exit("file not found: %s" % video)
    run_id = args.run_id or video.stem
    order = float(args.order) if args.order else float(args.blades)
    data_dir = Path(args.data_dir)
    dbg = Path(args.debug_dir) if args.debug_dir else HERE / "out" / "audio" / run_id
    for p in (data_dir, dbg):
        p.mkdir(parents=True, exist_ok=True)
    logf = open(dbg / (run_id + "_rpm_log.txt"), "w")

    def log(msg, echo=False):
        logf.write(msg + "\n")
        logf.flush()
        if echo:
            print(msg, flush=True)

    T0 = time.time()
    log("audio_rpm.py v%s  %s" % (SCRIPT_VERSION, time.strftime("%Y-%m-%d %H:%M:%S")), echo=True)
    info = probe(video)
    fs = info["fs"]
    off = info["a_start"] - info["v_start"]
    fps = info["fps"] or 30.0
    x = load_audio(video, fs)
    log("audio %s: %d Hz, %d channel(s), %.2f s; audio start - video start = %.4f s; video %.3f fps%s"
        % (video.name, fs, info["channels"], len(x) / fs, off, fps, "" if info["fps"] else " (assumed)"), echo=True)
    log("settings: blades %d, order %g, kmax %d, rpm %g-%g, voicing %.2f, state lag %.2f s, rho %.4f, prop '%s'%s%s"
        % (args.blades, order, args.kmax, args.rpm_min, args.rpm_max, args.voicing, args.state_lag, args.rho,
           args.prop or "", ", no prior" if args.no_prior else "", ", no thrust window" if args.no_thrust_window else ""),
        echo=True)

    # ---------------- spectra ----------------
    hop = max(1, int(round(args.hop * fs)))
    nfft = 4 * args.win
    df = fs / nfft
    F_min, F_max = args.rpm_min * order / 60.0, args.rpm_max * order / 60.0
    nbins = min(nfft // 2 + 1, int((args.kmax * F_max * 1.01) / df) + 8)
    P = stft_power(x, args.win, hop, nfft, nbins)
    del x
    T = P.shape[0]
    t = off + np.arange(T) * hop / fs
    f = np.arange(nbins) * df
    Pdb = 10.0 * np.log10(P + 1e-20)
    del P
    L = Pdb - spectral_floor(Pdb, f)
    stat = np.maximum(np.percentile(L, 20, axis=0), 0.0).astype(np.float32)
    L -= stat[None, :]
    lines = []
    for s, e in zip(*[np.flatnonzero(np.diff(np.concatenate([[0], (stat > 6.0).astype(int), [0]])) == v) for v in (1, -1)]):
        if f[s] >= F_min * 0.5:
            lines.append("%.1f Hz (%.0f dB)" % (f[s + int(np.argmax(stat[s:e]))], stat[s:e].max()))
    log("spectra: %d hops of %.3f s (window %.3f s, bin %.3f Hz, up to %.0f Hz); stationary lines removed: %s"
        % (T, hop / fs, args.win / fs, df, f[-1], ", ".join(lines) if lines else "none"), echo=True)

    # ---------------- display states, prop data, power prior ----------------
    p_blue = data_dir / (run_id + "_blue_states.csv")
    p_t2 = data_dir / (run_id + "_t2.csv")
    states = []
    if p_blue.exists():
        with open(p_blue, newline="") as fh:
            states = list(csv.DictReader(fh))
    else:
        log("no %s: run read_mt10pro_video.py first for per-state RPM and the power prior; tracking from sound alone"
            % p_blue.name, echo=True)
    prop = args.prop
    if prop is None and p_t2.exists():
        with open(p_t2, newline="") as fh:
            props = {r.get("prop", "") for r in csv.DictReader(fh)} - {""}
        prop = props.pop() if len(props) == 1 else None
    if prop is None:
        prop = video.stem if re.match(r"^\d+(\.\d+)?x\d+", video.stem) else ""
    apc = apc_model(prop, log) if order == args.blades else None
    Flim = np.full(T, np.inf)
    off_state = [False] * len(states)
    F_lo, F_hi = np.zeros(T), np.full(T, np.inf)
    if states and not args.no_prior:
        Flim, off_state = power_prior(states, t, order, apc, args.rho, args.state_lag, fps, log)
        if apc is not None and not args.no_thrust_window:
            F_lo, F_hi = thrust_window(states, t, order, apc, args.rho, args.state_lag, fps, off_state, log,
                                       factor=args.tw_factor)

    # ---------------- salience + tracking ----------------
    NF = (int(np.floor(FINE * np.log2(F_max / F_min))) + 1) // CELL * CELL
    Fgrid = F_min * 2.0 ** (np.arange(NF) / FINE)
    S = salience(L, df, Fgrid, args.kmax, rel_m=args.blades if order == args.blades else None,
                 F_lo=F_lo if (F_lo > 0).any() else None)
    S[Fgrid[None, :] > Flim[:, None]] = C_LO                       # above the power bound, or motor off
    S[(Fgrid[None, :] < F_lo[:, None]) | (Fgrid[None, :] > F_hi[:, None])] = C_LO   # outside the thrust window
    Sc = S.reshape(T, NF // CELL, CELL).max(-1)
    J = Sc.shape[1]
    slew_cells = 3.0 * (hop / fs) * FINE / CELL                    # 3 octaves/s free
    path = track(Sc, args.voicing, 3.0, slew_cells, 20.0 / (FINE / CELL), M=12)
    voiced = path < J
    # noise check: salience of the best candidate on unvoiced hops (should sit well below --voicing)
    uv_best = Sc[~voiced].max(1) if (~voiced).any() else np.zeros(0)
    log("tracking: %d of %d hops voiced (%.0f%%); best-candidate salience on unvoiced hops: median %.2f, 99th pct %.2f "
        "(voicing threshold %.2f)" % (voiced.sum(), T, 100 * voiced.mean(),
                                      np.median(uv_best) if len(uv_best) else np.nan,
                                      np.percentile(uv_best, 99) if len(uv_best) else np.nan, args.voicing), echo=True)

    # ---------------- refinement ----------------
    rows = []
    for i in range(T):
        r = {"t_s": t[i], "voiced": int(voiced[i]),
             "F_limit_Hz": 0.0 if np.isneginf(Flim[i]) else (float(Flim[i]) if np.isfinite(Flim[i]) else None),
             "F_lo_Hz": float(F_lo[i]) if F_lo[i] > 0 else None, "F_hi_Hz": float(F_hi[i]) if np.isfinite(F_hi[i]) else None}
        if voiced[i]:
            j = int(path[i])
            a, b = max(0, (j - 1) * CELL), min(NF, (j + 2) * CELL)
            fi = a + int(np.argmax(S[i, a:b]))
            Fc = float(Fgrid[fi])
            res = refine(Pdb[i], L[i], df, Fc, args.kmax)
            r.update(salience=float(S[i, fi]), F_coarse_Hz=Fc)
            if res is None:
                r.update(F_Hz=Fc, n_harm=0, harmonics="", spread_rpm=None, snr_max_dB=None, method="coarse")
            else:
                F, spread, ks, snr = res
                r.update(F_Hz=F, n_harm=len(ks), harmonics=" ".join(str(k) for k in ks),
                         spread_rpm=60.0 * spread / order, snr_max_dB=snr, method="harmonic_wls")
            r["rpm"] = 60.0 * r["F_Hz"] / order
        rows.append(r)
    rpm = np.array([r.get("rpm", np.nan) for r in rows])
    ok = np.isfinite(rpm)
    ncoarse = sum(1 for r in rows if r.get("method") == "coarse")
    log("refinement: %d hops with harmonic peaks, %d coarse only; median harmonics used %s; median spread %.1f rpm"
        % (ok.sum() - ncoarse, ncoarse,
           "%.0f" % np.median([r["n_harm"] for r in rows if r.get("n_harm")]) if ok.any() else "-",
           np.nanmedian([r["spread_rpm"] for r in rows if r.get("spread_rpm") is not None]) if ok.any() else np.nan), echo=True)

    def fmt(v, nd=3):
        if v is None:
            return ""
        if isinstance(v, (float, np.floating)):
            return "" if not np.isfinite(v) else ("%.*f" % (nd, v))
        return str(v)

    def write_csv(path, cols, rws, nd=None):
        tmp = path.with_name(path.stem + "_tmp" + path.suffix)
        with open(tmp, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(cols)
            for rw in rws:
                w.writerow([fmt(rw.get(c), (nd or {}).get(c, 3)) for c in cols])
        os.replace(tmp, path)

    p_hops = data_dir / (run_id + "_rpm.csv")
    write_csv(p_hops, ["t_s", "voiced", "rpm", "F_Hz", "F_coarse_Hz", "salience", "n_harm", "harmonics", "spread_rpm",
                       "snr_max_dB", "method", "F_limit_Hz", "F_lo_Hz", "F_hi_Hz"], rows,
              {"rpm": 1, "spread_rpm": 2, "salience": 2, "snr_max_dB": 1, "F_limit_Hz": 1, "F_lo_Hz": 1, "F_hi_Hz": 1})

    # ---------------- display states ----------------
    T_apc = apc["T_g"] if apc else None
    srows = []
    by_id = {}
    for s, s_off in zip(states, off_state):
        ta, tb = float(s["t_start_s"]) + args.state_lag, float(s["t_end_s"]) + 1.0 / fps + args.state_lag
        sel = (t >= ta) & (t < tb)
        rr = rpm[sel & ok]
        tt = t[sel & ok]
        flags = []
        row = {"state_id": s["state_id"], "t_start_s": fnum(s["t_start_s"]), "t_end_s": fnum(s["t_end_s"]),
               "win_start_s": ta, "win_end_s": tb, "n_hops": int(sel.sum()), "n_voiced": len(rr),
               "I_A": s.get("I_A", ""), "V_V": s.get("V_V", ""), "T_g_mean": s.get("T_g_mean", "")}
        if s_off:
            flags.append("motor_off")
        elif len(rr) >= 3 and len(rr) >= 0.5 * sel.sum():
            m = float(rr.mean())
            row.update(rpm_mean=m, rpm_std=float(rr.std(ddof=1)), rpm_min=float(rr.min()), rpm_max=float(rr.max()),
                       rpm_slope_per_s=float(np.polyfit(tt - tt.mean(), rr, 1)[0]) if np.ptp(tt) > 0 else 0.0,
                       spread_rpm_median=float(np.nanmedian([rows[i]["spread_rpm"] for i in np.flatnonzero(sel & ok)
                                                             if rows[i].get("spread_rpm") is not None] or [np.nan])))
            if row["rpm_std"] > 0.005 * m:
                flags.append("unsteady")
            tg = fnum(s.get("T_g_mean"))
            if T_apc is not None and tg is not None:
                ta_g = T_apc(m, args.rho)
                row.update(T_apc_g=ta_g, T_over_Tapc=tg / ta_g if ta_g > 0 else None)
                # an F/2 or 2F error is a factor 4 in thrust; gate on the larger of the two so an F/2 reading
                # (small T_apc, large measured T) is caught too; below 100 g the load cell's zero offset dominates
                if ta_g > 0 and max(ta_g, tg) >= 100.0 and not (0.5 <= tg / ta_g <= 2.0):
                    flags.append("rpm_thrust_mismatch")
        else:
            flags.append("no_rpm")
        row["flags"] = ";".join(flags)
        srows.append(row)
        by_id[str(s["state_id"])] = row
    p_states = data_dir / (run_id + "_rpm_states.csv")
    if srows:
        write_csv(p_states, ["state_id", "t_start_s", "t_end_s", "win_start_s", "win_end_s", "n_hops", "n_voiced",
                             "rpm_mean", "rpm_std", "rpm_min", "rpm_max", "rpm_slope_per_s", "spread_rpm_median",
                             "I_A", "V_V", "T_g_mean", "T_apc_g", "T_over_Tapc", "flags"], srows,
                  {"rpm_mean": 1, "rpm_std": 1, "rpm_min": 1, "rpm_max": 1, "rpm_slope_per_s": 1, "spread_rpm_median": 2,
                   "T_apc_g": 1})

    # ---------------- merge into the t2 file ----------------
    n_t2 = n_t2_rpm = 0
    if srows and p_t2.exists() and not args.no_merge:
        with open(p_t2, newline="") as fh:
            rd = csv.DictReader(fh)
            cols = rd.fieldnames
            t2 = list(rd)
        for r in t2:
            n_t2 += 1
            note = (r.get("notes") or "").split(" | rpm audio")[0]
            m = re.search(r"blue state (\d+) ", note)
            s = by_id.get(m.group(1)) if m else None
            r["rpm"], r["rpm_source"] = "", ""
            if s is not None and s.get("rpm_mean") is not None and not ({"no_rpm", "motor_off", "rpm_thrust_mismatch"} & set(s["flags"].split(";"))):
                r["rpm"], r["rpm_source"] = "%.0f" % s["rpm_mean"], "audio"
                n_t2_rpm += 1
            if s is not None:
                note += " | rpm audio v%s: mean of %d hops, std %s, slope %s rpm/s%s" % (
                    SCRIPT_VERSION, s["n_voiced"], fmt(s.get("rpm_std"), 0), fmt(s.get("rpm_slope_per_s"), 0),
                    ("; flags " + s["flags"]) if s["flags"] else "")
            r["notes"] = note
        tmp = p_t2.with_name(p_t2.stem + "_tmp.csv")
        with open(tmp, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(t2)
        os.replace(tmp, p_t2)

    # ---------------- plot ----------------
    p_png = dbg / (run_id + "_rpm.png")
    if not args.no_plot:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fmax_plot = min(f[-1], max(800.0, 4.5 * float(np.nanmax(np.where(ok, [r.get("F_Hz", np.nan) for r in rows], np.nan)))
                                       if ok.any() else 1500.0))
            nb = int(fmax_plot / df)
            fig, axs = plt.subplots(2, 1, figsize=(16, 10), sharex=True)
            ax = axs[0]
            ax.pcolormesh(t[::2], f[:nb:2], L[::2, :nb:2].T, shading="auto", vmin=0, vmax=35, cmap="viridis")
            Fh = np.where(ok, [r.get("F_Hz", np.nan) for r in rows], np.nan)
            for k in (1, 2, 3, 4):
                ax.plot(t, k * Fh, color="r", lw=0.6, alpha=0.8)
            if (F_lo > 0).any():
                ax.plot(t, np.where(F_lo > 0, F_lo, np.nan), color="w", lw=0.6, ls="--")
                ax.plot(t, np.where(np.isfinite(F_hi) & (F_hi <= fmax_plot), F_hi, np.nan), color="w", lw=0.6, ls="--")
            ax.set_ylabel("Hz (dB above background; red = k x tracked blade-pass; white dashed = thrust window)")
            ax.set_title("%s: audio blade-pass tracking (order %g)" % (video.name, order))
            ax = axs[1]
            ax.plot(t, rpm, ".", ms=1.5, color="C0", label="rpm per hop")
            for s in srows:
                if s.get("rpm_mean") is not None:
                    ax.plot([s["win_start_s"], s["win_end_s"]], [s["rpm_mean"]] * 2, "k-", lw=1.5)
            ax.set_ylabel("rpm (black = display-state mean)")
            ax.set_xlabel("video time, s")
            ax.grid(alpha=0.3)
            tg = [(0.5 * (s["t_start_s"] + s["t_end_s"]), fnum(s["T_g_mean"])) for s in srows if fnum(s["T_g_mean"]) is not None]
            if tg:
                a2 = ax.twinx()
                a2.plot(*zip(*tg), ".", ms=3, color="C1")
                a2.set_ylabel("MT10PRO thrust, g (orange)")
            fig.tight_layout()
            fig.savefig(p_png, dpi=80)
            plt.close(fig)
        except Exception as e:
            log("plot skipped: %s" % e, echo=True)

    # ---------------- summary ----------------
    good = [s for s in srows if s.get("rpm_mean") is not None]
    ratios = [s["T_over_Tapc"] for s in good if s.get("T_over_Tapc") is not None and s.get("T_apc_g", 0) >= 200.0]
    top = max(good, key=lambda s: s["rpm_mean"]) if good else None
    summ = ["done in %.1f min" % ((time.time() - T0) / 60),
            "rpm range %s to %s (hops)" % (fmt(np.nanmin(rpm), 0) if ok.any() else "-", fmt(np.nanmax(rpm), 0) if ok.any() else "-")]
    if srows:
        summ.append("display states: %d; with rpm %d; flagged motor_off %d, unsteady %d, no_rpm %d, rpm_thrust_mismatch %d"
                    % (len(srows), len(good), sum("motor_off" in s["flags"] for s in srows), sum("unsteady" in s["flags"] for s in srows),
                       sum("no_rpm" in s["flags"] for s in srows), sum("rpm_thrust_mismatch" in s["flags"] for s in srows)))
    if top:
        summ.append("highest-rpm state %s: %.0f rpm (std %.0f), I %s A, V %s V, T %s g" % (
            top["state_id"], top["rpm_mean"], top["rpm_std"], top["I_A"], top["V_V"], top["T_g_mean"]))
    if ratios:
        summ.append("measured / APC thrust at the audio rpm (rho %.3f, states with T_apc >= 200 g): median %.3f, range %.3f-%.3f, n %d"
                    % (args.rho, np.median(ratios), min(ratios), max(ratios), len(ratios)))
    if n_t2:
        summ.append("t2 file: rpm filled in %d of %d rows" % (n_t2_rpm, n_t2))
    summ += ["outputs:", "  " + str(p_hops)] + (["  " + str(p_states)] if srows else []) + \
            (["  " + str(p_t2) + " (rpm columns)"] if n_t2 else []) + ["  debug + plot: " + str(dbg)]
    for line in summ:
        log(line, echo=True)
    logf.close()


if __name__ == "__main__":
    main()
