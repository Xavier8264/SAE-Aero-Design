#!/usr/bin/env python3
"""
read_mt10pro_video.py -- read the Mayatech MT10PRO thrust tester displays from a phone video and log
thrust (g), current (A), battery voltage (V), power (W) and the auxiliary field to CSV files.

Written for the SAE Aero Design 2027 T-2 static thrust stand (TEST_PLAN.md section 3).
Optimized for accuracy, not speed. Developed and checked on 12x8E.MOV (2026-09-23).

Displays (as seen in 12x8E.MOV):
  - Blue backlit dot-matrix LCD, 2 rows x 16 cells of 5x7 dots:
        row 0: "  34.12A  13.14V"   current (A), battery voltage (V)
        row 1: "    2.0Wh 448.4W"   auxiliary field (cycles about every 3 s), power (W)
    Auxiliary units seen: Ap, Vm, Wp, Ah, Wh. Meanings are INFERRED from the units (peak current,
    minimum voltage, peak power, charge used, energy used); no manual was found to confirm them.
  - Red-plate 7-segment LCD, 5 digits, thrust in grams (unit assumed, the display shows no unit).

Method (every decision is a model fit with a measurable residual, not a hard threshold):
  Setup   Scan the video. Pairs of frames 4 apart whose blue text decodes cleanly and identically are
          "in-state" candidates. The sharpest is the registration reference. Up to 8 of the sharpest
          (spread out in time) train the lit-dot and unlit-dot footprints of the blue LCD by exact
          least squares.
  Pass 1  Every frame: find both displays by color, rectify each with a homography from its fitted
          outline, then refine with masked ECC (homography) against the reference using only static
          features (display borders, the A/V/W unit glyphs, the thrust display triangle marker).
          Blue LCD: frame = plane + gain * K conv (sharp dot model of the text). K is a per-frame
          nonnegative blur kernel fitted by NNLS, so motion-blurred frames still read. Every glyph in
          every cell gets a cost in "dot-equivalents" (1.0 = one sharp dot wrong).
          Thrust LCD: darkness of all 35 segments, per-frame on/off levels, cost per digit state in
          "segment-equivalents" (1.0 = one segment wrong).
  Pass 2  Per-cell (blue) and per-digit (thrust) Viterbi smoothing over time with a switch penalty.
          Frames are grouped into display states. Blue runs of 1-3 frames made only of cells from the
          two neighboring states are rolling-shutter mixes and are dropped. Thrust runs of 1-2 frames
          made only of neighbor digits are kept but flagged possible_mix (a real thrust state can last
          one frame at 30 fps) and left out of T_g. Fields are parsed; P is checked against V x I.

Usage (from the repo root, Git Bash):
    python analysis/tests/read_mt10pro_video.py analysis/tests/video/12x8E.MOV
    python analysis/tests/read_mt10pro_video.py VIDEO --end 10          # quick smoke test, first 10 s
Options: --run-id, --prop, --motor-id, --esc-id, --pack-id, --pack-fresh, --n-motors-live,
         --throttle-pct (copied into the t2 CSV), --start/--end (s), --step (frames), --workers,
         --lambda-blue, --lambda-thrust, --ref-frame, --no-overlays, --fresh.

Outputs (RUN = --run-id, default the video file name without extension):
    analysis/tests/data/RUN_t2.csv            one row per blue display state, TEST_PLAN.md t2_thrust columns
    analysis/tests/data/RUN_blue_states.csv   every blue display state with parse flags and evidence
    analysis/tests/data/RUN_thrust_states.csv every thrust display state
    analysis/tests/data/RUN_frames.csv        per-frame raw and smoothed readings and quality metrics
    analysis/tests/out/video/RUN/             log, setup json, pass-1 chunk cache, overlay images

Limits and UNVERIFIED items:
  - T_g for a blue state is the mean of the per-frame thrust readings over that state. The relative
    latency of the two displays is unknown.
  - Only the 18 glyphs seen in 12x8E.MOV are modeled (space . 0-9 A V W p h m). Any other glyph is read
    as the nearest one, and the state is then usually flagged by the field parser.
  - Assumes the camera orientation of 12x8E.MOV (the thrust display is below the blue LCD in the
    picture). The script stops with a message if the unit glyphs are not found in the reference frame.
Requires: Python 3, numpy, scipy, opencv-python (cv2.findTransformECCWithMask, present in OpenCV 4.13).
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

import numpy as np
import cv2

SCRIPT_VERSION = "1.0"
HERE = Path(__file__).resolve().parent

# ----------------------------------------------------------------------------------------------
# Display geometry, measured on 12x8E.MOV (canonical pixel units)
# ----------------------------------------------------------------------------------------------
BW, BH = 1600, 360            # blue LCD canonical size: the backlit rectangle mapped to 1600 x 360
TW, TH = 1200, 500            # thrust LCD canonical size: the pocket in the red plate mapped to 1200 x 500
MARGIN = 40                   # canonical margin kept around each display for ECC (px)
GRID = (127.638, 86.1487, 14.0046, 50.4365, 147.2971, 16.1425)   # x0, cell pitch, dot pitch x, y0, row pitch, dot pitch y
UNIT_CELLS = {(0, 7): "A", (0, 15): "V", (1, 15): "W"}           # static glyphs used for registration and sanity checks
TRI_BOX = (1117, 82, 1148, 113)                                   # static triangle marker on the thrust display
FR, KR = 12, 28               # dot footprint radius, blur kernel radius (px)
ECC_CRIT = (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 200, 1e-7)
ECC_MIN = 0.5                 # ECC correlation below this: display not found or occluded
FIELD_UNITS_AUX = ("Ap", "Vm", "Wp", "Ah", "Wh")

GLYPHS = {   # 5x7, rows top to bottom, '#' = lit. Observed in 12x8E.MOV; match the HD44780 A00 ROM forms.
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".##..", ".##.."],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."],
    "4": ["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."],
    "5": ["#####", "#....", "####.", "....#", "....#", "#...#", ".###."],
    "6": ["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."],
    "A": [".###.", "#...#", "#...#", "#...#", "#####", "#...#", "#...#"],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."],
    "p": [".....", ".....", "####.", "#...#", "####.", "#....", "#...."],
    "h": ["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "#...#"],
    "m": [".....", ".....", "##.#.", "#.#.#", "#.#.#", "#...#", "#...#"],
}
KEYS = list(GLYPHS)
NG = len(KEYS)
GB = np.array([[1.0 if ch == "#" else 0.0 for ch in "".join(GLYPHS[k])] for k in KEYS])   # NG x 35

SEG7 = {" ": "", "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg", "5": "acdfg",
        "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g"}
DKEYS = list(SEG7)
ND = len(DKEYS)
SB = np.array([[1.0 if s in SEG7[k] else 0.0 for s in "abcdefg"] for k in DKEYS])          # ND x 7
# segment centers relative to each digit's x anchor: (dx, y, orientation)
SEG = {"a": (-29.9, 84.7, "h"), "b": (17.3, 162.9, "v"), "c": (0.0, 330.7, "v"), "d": (-63.0, 404.6, "h"),
       "e": (-111.4, 327.6, "v"), "f": (-94.4, 158.7, "v"), "g": (-46.6, 243.3, "h")}
DCX = [201.0, 412.6, 622.8, 833.9, 1047.4]
SLANT = np.array([-17.0, 168.0]) / np.hypot(-17.0, 168.0)   # direction of the vertical segments (italic digits)


# ----------------------------------------------------------------------------------------------
# Display detection: outline -> sub-pixel quad
# ----------------------------------------------------------------------------------------------
def order_tl_tr_br_bl(q):
    q = np.asarray(q, np.float64)
    c = q.mean(0)
    q = q[np.argsort(np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0]))]
    return np.roll(q, -int(np.argmin(q.sum(1))), axis=0)


def fit_quad_from_contour(c, side_frac=0.7, tol=25.0):
    """Split the contour into 4 sides using minAreaRect, fit a robust line per side, intersect."""
    pts = c.reshape(-1, 2).astype(np.float64)
    box = order_tl_tr_br_bl(cv2.boxPoints(cv2.minAreaRect(c)))
    lines = []
    for i in range(4):
        a, b = box[i], box[(i + 1) % 4]
        L = np.linalg.norm(b - a)
        u = (b - a) / L
        nrm = np.array([-u[1], u[0]])
        rel = pts - a
        t = rel @ u
        lo = (1 - side_frac) / 2
        sel = (t > lo * L) & (t < (1 - lo) * L) & (np.abs(rel @ nrm) < tol)
        if sel.sum() < 10:
            raise ValueError("too few outline points on one side")
        vx, vy, x0, y0 = cv2.fitLine(pts[sel].astype(np.float32), cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        lines.append((np.array([x0, y0], float), np.array([vx, vy], float)))
    out = []
    for i in range(4):
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        t = np.linalg.solve(np.array([d1, -d2]).T, p2 - p1)
        out.append(p1 + t[0] * d1)
    return np.array(out, np.float32)


def blue_contour(hsv):
    m = ((hsv[..., 0] > 95) & (hsv[..., 0] < 130) & (hsv[..., 1] > 120) & (hsv[..., 2] > 100)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m)
    if n < 2:
        return None
    k = 1 + int(np.argmax(st[1:, 4]))
    cs = cv2.findContours((lab == k).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
    return max(cs, key=cv2.contourArea) if cs else None


def thr_quad(hsv, bq):
    """Thrust display: the largest non-red hole in the red plate below the blue LCD."""
    Wb = np.linalg.norm(bq[1] - bq[0])
    Hb = np.linalg.norm(bq[3] - bq[0])
    xa = int(max(0, bq[3, 0] - 0.15 * Wb))
    xb = int(min(hsv.shape[1], bq[2, 0] + 0.05 * Wb))
    ya = int(max(bq[2, 1], bq[3, 1]) + 0.2 * Hb)
    yb = int(min(hsv.shape[0], max(bq[2, 1], bq[3, 1]) + 4 * Hb))
    if xb - xa < 50 or yb - ya < 50:
        return None
    sub = hsv[ya:yb, xa:xb]
    red = (((sub[..., 0] < 12) | (sub[..., 0] > 168)) & (sub[..., 1] > 90) & (sub[..., 2] > 50)).astype(np.uint8)
    hole = cv2.morphologyEx(1 - red, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(hole)
    best = None
    for k in range(1, n):
        x, y, w, h, a = st[k]
        if x == 0 or y == 0 or x + w == hole.shape[1] or y + h == hole.shape[0] or a < 0.05 * Wb * Hb:
            continue
        if best is None or a > st[best][4]:
            best = k
    if best is None:
        return None
    blob = cv2.morphologyEx((lab == best).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((31, 31), np.uint8))
    c = max(cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0], key=cv2.contourArea)
    return fit_quad_from_contour(c + np.array([xa, ya]), tol=20)


def quad_area(q):
    return float(abs(cv2.contourArea(np.float32(q))))


def find_quads(im):
    """Returns (blue quad or None, thrust quad or None)."""
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    try:
        c = blue_contour(hsv)
        bq = fit_quad_from_contour(c) if c is not None and cv2.contourArea(c) > 5000 else None
    except (ValueError, np.linalg.LinAlgError, cv2.error):
        bq = None
    if bq is None:
        return None, None
    try:
        tq = thr_quad(hsv, bq)
    except (ValueError, np.linalg.LinAlgError, cv2.error):
        tq = None
    return bq, tq


def canon_H(q, W, H):
    m = MARGIN
    return cv2.getPerspectiveTransform(np.float32(q), np.float32([[m, m], [W + m, m], [W + m, H + m], [m, H + m]]))


SHIFT = np.array([[1, 0, -MARGIN], [0, 1, -MARGIN], [0, 0, 1]], np.float64)


# ----------------------------------------------------------------------------------------------
# Blue LCD dot model
# ----------------------------------------------------------------------------------------------
_r, _c, _j, _k = np.meshgrid(np.arange(2), np.arange(16), np.arange(8), np.arange(5), indexing="ij")
GX = GRID[0] + _c * GRID[1] + _k * GRID[2]          # dot centers, shape (2, 16, 8, 5); row j = 7 is the cursor row
GY = GRID[3] + _r * GRID[4] + _j * GRID[5]


def splat(xs, ys):
    img = np.zeros((BH, BW), np.float64)
    xs, ys = np.ravel(xs), np.ravel(ys)
    ix, iy = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = xs - ix, ys - iy
    for dy, dx, w in ((0, 0, (1 - fx) * (1 - fy)), (0, 1, fx * (1 - fy)), (1, 0, (1 - fx) * fy), (1, 1, fx * fy)):
        np.add.at(img, (iy + dy, ix + dx), w)
    return img


def impulse_maps(assign):
    """Bilinear impulse maps of lit dots and unlit dots (the cursor row counts as unlit)."""
    L = np.zeros((2, 16, 8, 5), bool)
    L[:, :, :7, :] = GB[assign].reshape(2, 16, 7, 5) > 0
    return splat(GX[L], GY[L]), splat(GX[~L], GY[~L])


def xcorr(A, B, lag):
    """C(t) = sum_y A(y) B(y+t) for t in [-lag, lag]^2, indexed [ty+lag, tx+lag] (zero padded, no wrap)."""
    sh = (A.shape[0] + 2 * lag + 1, A.shape[1] + 2 * lag + 1)
    C = np.fft.irfft2(np.conj(np.fft.rfft2(A, sh)) * np.fft.rfft2(B, sh), sh)
    return np.roll(np.roll(C, lag, 0), lag, 1)[:2 * lag + 1, :2 * lag + 1]


_yy, _xx = np.mgrid[0:BH, 0:BW].astype(np.float64)
PB = [np.ones((BH, BW)), (_xx - BW / 2) / BW, (_yy - BH / 2) / BH]   # plane basis


def normal_eqs(maps, R, lag):
    """Exact LS normal equations for R ~ sum_m F_m conv maps[m] + plane with F_m on [-lag, lag]^2.
    Exact when every map is zero within lag of the image border (true here: dots are >= 38 px inside)."""
    n = (2 * lag + 1) ** 2
    nm = len(maps)
    N = nm * n + 3
    uy, ux = np.divmod(np.arange(n), 2 * lag + 1)
    uy, ux = uy - lag, ux - lag
    dy = (uy[:, None] - uy[None, :]) + 2 * lag
    dx = (ux[:, None] - ux[None, :]) + 2 * lag
    AtA = np.zeros((N, N))
    Atb = np.zeros(N)
    for a in range(nm):
        for b in range(a, nm):
            blk = xcorr(maps[a], maps[b], 2 * lag)[dy, dx]
            AtA[a * n:(a + 1) * n, b * n:(b + 1) * n] = blk
            AtA[b * n:(b + 1) * n, a * n:(a + 1) * n] = blk.T
        for p, P in enumerate(PB):
            v = xcorr(maps[a], P, lag).ravel()
            AtA[a * n:(a + 1) * n, nm * n + p] = v
            AtA[nm * n + p, a * n:(a + 1) * n] = v
        Atb[a * n:(a + 1) * n] = xcorr(maps[a], R, lag).ravel()
    for p, P in enumerate(PB):
        for q, Q in enumerate(PB):
            AtA[nm * n + p, nm * n + q] = (P * Q).sum()
        Atb[nm * n + p] = (P * R).sum()
    return AtA, Atb


def learn_footprints(frames, ridge=1e-7):
    """Lit and unlit dot footprints (2FR+1 square) by exact LS over frames [(R, assign)], one plane per frame."""
    n = (2 * FR + 1) ** 2
    k = 2 * n
    H = np.zeros((k, k))
    g = np.zeros(k)
    for R, assign in frames:
        A, b = normal_eqs(list(impulse_maps(assign)), R, FR)
        X = np.linalg.solve(A[k:, k:], np.column_stack([A[k:, :k], b[k:]]))
        H += A[:k, :k] - A[:k, k:] @ X[:, :k]
        g += b[:k] - A[:k, k:] @ X[:, k]
    th = np.linalg.solve(H + ridge * np.trace(H) / k * np.eye(k), g)
    return th[:n].reshape(2 * FR + 1, -1), th[n:].reshape(2 * FR + 1, -1)


def conv_same(img, ker):
    """sum_u ker(u) img(x - u), kernel centered, zero outside."""
    return cv2.filter2D(img, -1, ker[::-1, ::-1].astype(np.float64), borderType=cv2.BORDER_CONSTANT)


def sharp_model(assign, FL, FU):
    SL, SU = impulse_maps(assign)
    return conv_same(SL, FL) + conv_same(SU, FU)


TENT = np.outer([0.5, 1.0, 0.5], [0.5, 1.0, 0.5])


def estimate_K(R, Q, kc=13, step=2, ridge=1e-3):
    """Nonnegative blur kernel on a tent basis (nodes every `step` px out to kc*step), plane unconstrained.
    NNLS, not clipped LS: unconstrained LS overfits unmodeled structure with large edge spikes (seen on
    frame 2058 of 12x8E.MOV)."""
    from scipy.optimize import nnls
    from scipy.linalg import cholesky, solve_triangular
    Qt = conv_same(Q, TENT)
    lag = kc * step
    m = np.arange(-kc, kc + 1)
    my, mx = [v.ravel() for v in np.meshgrid(m, m, indexing="ij")]
    n = len(my)
    C = xcorr(Qt, Qt, 2 * lag)
    Hkk = C[step * (my[:, None] - my[None, :]) + 2 * lag, step * (mx[:, None] - mx[None, :]) + 2 * lag]
    Hkp = np.stack([xcorr(Qt, P, lag)[step * my + lag, step * mx + lag] for P in PB], 1)
    bk = xcorr(Qt, R, lag)[step * my + lag, step * mx + lag]
    App = np.array([[(P * P2).sum() for P2 in PB] for P in PB])
    bp = np.array([(P * R).sum() for P in PB])
    X = np.linalg.solve(App, np.column_stack([Hkp.T, bp]))
    H = Hkk - Hkp @ X[:, :n]
    f = bk - Hkp @ X[:, n]
    H = 0.5 * (H + H.T) + ridge * np.trace(H) / n * np.eye(n)
    L = cholesky(H, lower=True)
    c = nnls(L.T, solve_triangular(L, f, lower=True))[0]
    K = np.zeros((2 * KR + 1, 2 * KR + 1))
    K[KR + step * my, KR + step * mx] = c
    K = conv_same(K, TENT)
    if K.sum() <= 0:
        K = np.zeros_like(K)
        K[KR, KR] = 1.0
        return K
    return K / K.sum()


def fit_gain(R, KQ):
    X = np.stack(PB + [KQ], -1).reshape(-1, 4)
    cf = np.linalg.lstsq(X, R.reshape(-1), rcond=None)[0]
    return cf, (X @ cf).reshape(R.shape)


def place(G, x, y, xa, ya, w, h):
    cx, cy = (G.shape[1] - 1) / 2, (G.shape[0] - 1) / 2
    M = np.float64([[1, 0, x - xa - cx], [0, 1, y - ya - cy]])
    return cv2.warpAffine(G, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)


_ys_fit = slice(int(GY.min()) - 6, int(GY[:, :, :7].max()) + 7)
_xs_fit = slice(int(GX.min()) - 6, int(GX.max()) + 7)


def glyph_costs(R, assign, FL, FU, K, sweeps=2):
    """SSE of every glyph in every cell with the other cells held (coordinate descent).
    Returns SSE (2,16,NG), updated assign, gain d, residual variance over the text area."""
    GL = conv_same(np.pad(FL, KR), K)
    GU = conv_same(np.pad(FU, KR), K)
    SL, SU = impulse_maps(assign)
    cf, Mod = fit_gain(R, conv_same(SL, GL) + conv_same(SU, GU))
    d = cf[3]
    E = R - Mod
    DG = GL - GU
    hs = DG.shape[0] // 2
    SSE = np.zeros((2, 16, NG))
    assign = assign.copy()
    wins = {}
    for r in range(2):
        for c in range(16):
            xa = max(int(np.floor(GX[r, c].min())) - hs - 1, 0)
            ya = max(int(np.floor(GY[r, c, :7].min())) - hs - 1, 0)
            xb = min(int(np.ceil(GX[r, c].max())) + hs + 2, BW)
            yb = min(int(np.ceil(GY[r, c, :7].max())) + hs + 2, BH)
            w, h = xb - xa, yb - ya
            D = np.stack([place(DG, GX[r, c, j, k], GY[r, c, j, k], xa, ya, w, h).ravel()
                          for j in range(7) for k in range(5)])
            wins[r, c] = (xa, ya, w, h, D, D @ D.T)
    for _ in range(sweeps):
        for r in range(2):
            for c in range(16):
                xa, ya, w, h, D, Gm = wins[r, c]
                g0 = assign[r, c]
                e = E[ya:ya + h, xa:xa + w].ravel() + d * (GB[g0] @ D)
                s = e @ e - 2 * d * (GB @ (D @ e)) + d * d * np.einsum("gi,ij,gj->g", GB, Gm, GB)
                SSE[r, c] = s
                g1 = int(np.argmin(s))
                assign[r, c] = g1
                E[ya:ya + h, xa:xa + w] = (e - d * (GB[g1] @ D)).reshape(h, w)
    return SSE, assign, d, float(np.mean(E[_ys_fit, _xs_fit] ** 2))


def threshold_decode(R):
    """Quick decode for sharp frames: dot brightness vs a global threshold. ok[r, c] = within 1 dot of a glyph."""
    b = cv2.blur(R.astype(np.float64), (7, 7))
    V = b[np.round(GY[:, :, :7]).astype(int), np.round(GX[:, :, :7]).astype(int)].reshape(2, 16, 35)
    th = 0.5 * (np.percentile(V, 10) + np.percentile(V, 97))
    ham = np.abs(GB[None, None] - (V[..., None, :] > th)).sum(-1)
    return ham.argmin(-1), ham.min(-1) <= 1


def units_ok(assign):
    return all(KEYS[assign[rc]] == ch for rc, ch in UNIT_CELLS.items())


def text_of(assign):
    return ["".join(KEYS[v] for v in row) for row in assign]


_kyy, _kxx = np.mgrid[-KR:KR + 1, -KR:KR + 1]


def read_blue(R, init, FL, FU, U, max_iter=4):
    """Alternate K fit and glyph costs until the text stops changing (K then matches the final text).
    Returns normalized costs (2,16,NG) in dot-equivalents, assign, gain, rms, blur sx, sy, iters, stable."""
    a = init.copy()
    stable = False
    for it in range(1, max_iter + 1):
        K = estimate_K(R, sharp_model(a, FL, FU))
        SSE, a2, d, s2 = glyph_costs(R, a, FL, FU, K)
        if np.array_equal(a2, a):
            stable = True
            break
        a = a2
    dd = max(abs(d), 1e-3) ** 2
    ct = (SSE - SSE.min(-1, keepdims=True)) / (dd * U)
    mx, my = (K * _kxx).sum(), (K * _kyy).sum()
    sx = float(np.sqrt(max((K * _kxx ** 2).sum() - mx ** 2, 0)))
    sy = float(np.sqrt(max((K * _kyy ** 2).sum() - my ** 2, 0)))
    return ct.astype(np.float32), a2, float(d), float(np.sqrt(s2)), sx, sy, it, stable


# ----------------------------------------------------------------------------------------------
# Thrust 7-segment reader
# ----------------------------------------------------------------------------------------------
def seg_pts(cx, name):
    dx, y, o = SEG[name]
    c = np.array([cx + dx, y])
    if o == "v":
        ax, ac, L, Wd = SLANT, np.array([SLANT[1], -SLANT[0]]), 50, 8
    else:
        ax, ac, L, Wd = np.array([1.0, 0.0]), np.array([0.0, 1.0]), 32, 6
    t = np.arange(-L, L + 1, 4.0)
    s = np.arange(-Wd, Wd + 1, 4.0)
    return (c[None, None, :] + t[:, None, None] * ax + s[None, :, None] * ac).reshape(-1, 2)


def thrust_sampler(ox=0.0, oy=0.0):
    """All sample points for 5 digits x (background + 7 segments), as one remap row."""
    groups = []
    for cx in DCX:
        bg = [[cx - 38 + dx, 163 + dy] for dx in (-8, 0, 8) for dy in (-15, 0, 15)] + \
             [[cx - 55 + dx, 328 + dy] for dx in (-8, 0, 8) for dy in (-15, 0, 15)]
        groups.append(np.array(bg, np.float64))
        for s in "abcdefg":
            groups.append(seg_pts(cx, s))
    sizes = np.array([len(g) for g in groups])
    P = (np.concatenate(groups) + np.array([ox, oy])).astype(np.float32)
    return P[:, 0].reshape(1, -1).copy(), P[:, 1].reshape(1, -1).copy(), np.r_[0, np.cumsum(sizes)[:-1]], sizes


def thrust_dark(T, smp):
    """Darkness (bg - seg) / bg of every segment, shape (5, 7)."""
    mxp, myp, starts, sizes = smp
    v = cv2.remap(T, mxp, myp, cv2.INTER_LINEAR)[0].astype(np.float64)
    m = (np.add.reduceat(v, starts) / sizes).reshape(5, 8)
    bg = np.maximum(m[:, :1], 1.0)
    return (bg - m[:, 1:]) / bg


def thrust_costs(v):
    """Per-frame on/off levels by 2-means, then cost of every digit state in segment-equivalents.
    Returns costs (5, ND), contrast (hi - lo), residual sigma (normalized)."""
    f = np.sort(v.ravel())
    lo, hi = np.percentile(f, 20), np.percentile(f, 95)
    for _ in range(30):
        on = f > 0.5 * (lo + hi)
        if on.all() or not on.any():
            break
        lo2, hi2 = f[~on].mean(), f[on].mean()
        if abs(lo2 - lo) < 1e-9 and abs(hi2 - hi) < 1e-9:
            break
        lo, hi = lo2, hi2
    con = hi - lo
    if con < 0.05:
        return np.zeros((5, ND), np.float32), float(con), float("inf")
    pred = lo + con * SB[None]                                   # 1, ND, 7
    cost = (((v[:, None, :] - pred) / con) ** 2).sum(-1)         # 5, ND
    best = cost.argmin(1)
    sig = float(np.sqrt(np.mean(cost[np.arange(5), best]) / 7.0))
    return (cost - cost.min(1, keepdims=True)).astype(np.float32), float(con), sig


def sep_score(v):
    """Otsu separability of the 35 segment darkness values (1 = perfectly two-level)."""
    f = np.sort(v.ravel())
    best = 0.0
    var = f.var() + 1e-12
    for k in range(3, len(f) - 2):
        a, b = f[:k], f[k:]
        best = max(best, len(a) * len(b) / len(f) ** 2 * (b.mean() - a.mean()) ** 2 / var)
    return best


# ----------------------------------------------------------------------------------------------
# Video access
# ----------------------------------------------------------------------------------------------
def frame_index(cap, fps):
    return int(round(cap.get(cv2.CAP_PROP_POS_MSEC) * fps / 1000.0))


def iter_frames(path, a, b, fps, step=1):
    """Yield (idx, t_s, cap) for frames a <= idx < b with (idx - a) % step == 0; the frame is grabbed,
    call cap.retrieve() to decode it. Frame indices come from the frame timestamps, and a seek that lands
    past frame a is retried from further back, so frame numbering is exact for constant-frame-rate video."""
    cap = None
    idx = None
    for back in (0, 60, 300, 1800, None):
        if cap is not None:
            cap.release()
        cap = cv2.VideoCapture(str(path))
        s = 0 if back is None else max(0, a - back)
        if s > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, s)
        if not cap.grab():
            cap.release()
            return
        idx = frame_index(cap, fps)
        if idx <= a:
            break
    try:
        while idx < b:
            if idx >= a and (idx - a) % step == 0:
                yield idx, cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0, cap
            if not cap.grab():
                break
            idx = frame_index(cap, fps)
    finally:
        cap.release()


def read_one(path, idx, fps):
    for i, t, cap in iter_frames(path, idx, idx + 1, fps):
        ok, im = cap.retrieve()
        return im if ok else None
    return None


# ----------------------------------------------------------------------------------------------
# Workers (module level so they can run in spawned processes on Windows)
# ----------------------------------------------------------------------------------------------
_G = {}


def _worker_init(ctx):
    _G.clear()
    _G.update(ctx)
    cv2.setNumThreads(int(ctx.get("cv_threads", 1)))
    if "thr_off" in ctx:
        _G["smp"] = thrust_sampler(*ctx["thr_off"])
    if "Tb" in ctx:
        _G["in_b"] = np.full(ctx["Tb"].shape, 255, np.uint8)
        _G["in_t"] = np.full(ctx["Tt"].shape, 255, np.uint8)


def _scan_chunk(job):
    """Setup scan: at every stride-th frame and the frame `gap` later, rectify the blue LCD by its outline,
    measure sharpness and threshold-decode it."""
    a, b = job
    stride, gap, fps = _G["stride"], _G["gap"], _G["fps"]
    out = []
    for idx, t, cap in iter_frames(_G["video"], a, b, fps):
        k = (idx - _G["f0"]) % stride
        if k != 0 and k != gap:
            continue
        ok, im = cap.retrieve()
        if not ok:
            continue
        bq, tq = find_quads(im)
        if bq is None or tq is None:
            continue
        R = cv2.warpPerspective(im, canon_H(bq, BW, BH), (BW + 2 * MARGIN, BH + 2 * MARGIN),
                                flags=cv2.INTER_CUBIC)[MARGIN:MARGIN + BH, MARGIN:MARGIN + BW, 1].astype(np.float64)
        assign, okc = threshold_decode(R)
        sharp = float(cv2.Laplacian(R[_ys_fit, _xs_fit], cv2.CV_64F).var())
        out.append((idx, sharp, "|".join(text_of(assign)), bool(okc.all() and units_ok(assign)),
                    quad_area(bq), quad_area(tq)))
    return out


def register(im, prev):
    """Quad + masked ECC registration of both displays. prev = last usable quad homographies.
    reg_b / reg_t: 2 = ECC refined, 1 = outline quad only (ECC failed; the reader's fit residual then
    sets the frame weight), 0 = display not found. Returns (Mb or None, Mt or None, info dict, new prev)."""
    G = _G
    info = {"quad_b": 0, "quad_t": 0, "ecc_b": float("nan"), "ecc_t": float("nan"), "reg_b": 0, "reg_t": 0}
    bq, tq = find_quads(im)
    Hb = Ht = None
    if bq is not None and 0.6 < quad_area(bq) / G["area_b"] < 1.6:
        Hb = canon_H(bq, BW, BH)
        info["quad_b"] = 1
    elif prev is not None:
        Hb = prev[0]
    if tq is not None and 0.6 < quad_area(tq) / G["area_t"] < 1.6:
        Ht = canon_H(tq, TW, TH)
        info["quad_t"] = 1
    elif prev is not None:
        Ht = prev[1]
    out = {}
    for key, H, T, mask, inm, (W_, H_) in (("b", Hb, G["Tb"], G["mb"], G["in_b"], (BW, BH)),
                                          ("t", Ht, G["Tt"], G["mt"], G["in_t"], (TW, TH))):
        out[key] = None
        if H is None:
            continue
        J = cv2.warpPerspective(im, H, (W_ + 2 * MARGIN, H_ + 2 * MARGIN), flags=cv2.INTER_CUBIC)[..., 1].astype(np.float32)
        try:
            cc, W = cv2.findTransformECCWithMask(T, J, mask, inm, np.eye(3, dtype=np.float32),
                                                 cv2.MOTION_HOMOGRAPHY, ECC_CRIT, 5)
            info["ecc_" + key] = float(cc)
            if cc >= ECC_MIN:
                out[key] = SHIFT @ np.linalg.solve(W.astype(np.float64), H)
                info["reg_" + key] = 2
        except cv2.error:
            pass
        if out[key] is None and info["quad_" + key]:
            out[key] = SHIFT @ H
            info["reg_" + key] = 1
    new_prev = (Hb if Hb is not None else (prev[0] if prev else None),
                Ht if Ht is not None else (prev[1] if prev else None))
    return out["b"], out["t"], info, new_prev


def _frame_record(im, prev, prev_assign):
    G = _G
    rec = {}
    Mb, Mt, info, new_prev = register(im, prev)
    rec.update(info)
    rec["Mb"] = Mb if Mb is not None else np.full((3, 3), np.nan)
    rec["Mt"] = Mt if Mt is not None else np.full((3, 3), np.nan)
    # blue LCD
    rec["blue_valid"] = int(Mb is not None)
    rec["ct"] = np.zeros((2, 16, NG), np.float32)
    rec["assign"] = np.zeros((2, 16), np.int16)
    rec["gain"] = rec["rms"] = rec["sx"] = rec["sy"] = float("nan")
    rec["iters"] = 0
    rec["stable"] = 0
    new_assign = prev_assign
    if Mb is not None:
        R = cv2.warpPerspective(im, Mb, (BW, BH), flags=cv2.INTER_CUBIC)[..., 1].astype(np.float64)
        a0, ok0 = threshold_decode(R)
        if prev_assign is not None:
            a0 = np.where(ok0, a0, prev_assign)
        res = read_blue(R, a0, G["FL"], G["FU"], G["U"])
        bad = (not res[7]) or res[2] < 0.6
        if bad and prev_assign is not None and not np.array_equal(prev_assign, a0):
            res2 = read_blue(R, prev_assign.copy(), G["FL"], G["FU"], G["U"])
            if res2[3] < res[3]:
                res = res2
        ct, a, d, rms, sx, sy, it, stable = res
        rec.update(ct=ct, assign=a.astype(np.int16), gain=d, rms=rms, sx=sx, sy=sy, iters=it, stable=int(stable))
        new_assign = a
    # thrust LCD
    rec["thrust_valid"] = int(Mt is not None)
    rec["tc"] = np.zeros((5, ND), np.float32)
    rec["tcon"] = rec["tsig"] = float("nan")
    if Mt is not None:
        T = cv2.warpPerspective(im, Mt, (TW, TH), flags=cv2.INTER_CUBIC)[..., 1].astype(np.float32)
        tc, con, sig = thrust_costs(thrust_dark(T, G["smp"]))
        rec.update(tc=tc, tcon=con, tsig=sig)
        if not np.isfinite(sig):
            rec["thrust_valid"] = 0
    return rec, new_prev, new_assign


REC_KEYS = ["idx", "t", "quad_b", "quad_t", "ecc_b", "ecc_t", "reg_b", "reg_t", "Mb", "Mt", "blue_valid", "ct", "assign",
            "gain", "rms", "sx", "sy", "iters", "stable", "thrust_valid", "tc", "tcon", "tsig", "tproc"]


def _process_chunk(job):
    a, b = job
    G = _G
    cache = Path(G["cache_dir"]) / ("chunk_%07d_%07d.npz" % (a, b))
    if cache.exists() and not G.get("fresh"):
        try:
            with np.load(cache, allow_pickle=False) as z:
                if str(z["sig"]) == G["sig"]:
                    return {k: z[k] for k in REC_KEYS}
        except Exception:
            pass
    recs = {k: [] for k in REC_KEYS}
    prev = None
    prev_assign = None
    for idx, t, cap in iter_frames(G["video"], a, b, G["fps"], G["step"]):
        t0 = time.time()
        ok, im = cap.retrieve()
        if not ok:
            continue
        rec, prev, prev_assign = _frame_record(im, prev, prev_assign)
        rec["idx"], rec["t"], rec["tproc"] = idx, t, time.time() - t0
        for k in REC_KEYS:
            recs[k].append(rec[k])
    out = {k: np.array(v) for k, v in recs.items()}
    if len(out["idx"]) == 0:
        out = empty_records()
    tmp = cache.with_name(cache.stem + "_tmp.npz")
    np.savez(tmp, sig=np.array(G["sig"]), **out)
    os.replace(tmp, cache)
    return out


def empty_records():
    shapes = {"Mb": (0, 3, 3), "Mt": (0, 3, 3), "ct": (0, 2, 16, NG), "assign": (0, 2, 16), "tc": (0, 5, ND)}
    return {k: np.zeros(shapes.get(k, (0,))) for k in REC_KEYS}


def run_jobs(func, jobs, ctx, workers, log, label):
    """Run jobs in-process (workers == 1) or in a spawned process pool; yields results as they finish."""
    t0 = time.time()
    done = 0
    if workers <= 1:
        _worker_init(ctx)
        it = map(func, jobs)
        pool = None
    else:
        import multiprocessing as mp
        pool = mp.get_context("spawn").Pool(workers, initializer=_worker_init, initargs=(ctx,))
        it = pool.imap_unordered(func, jobs)
    last = 0.0
    try:
        for res in it:
            done += 1
            el = time.time() - t0
            if el - last > 60 or done == len(jobs):
                last = el
                # the first chunks finish together after one chunk time, so count at least one per worker
                eta = el / max(done, min(max(workers, 1), len(jobs))) * (len(jobs) - done)
                log("  %s: %d/%d chunks, %.1f min elapsed, about %.1f min left" % (label, done, len(jobs), el / 60, eta / 60), echo=True)
            yield res
    except BaseException:
        if pool is not None:
            pool.terminate()
            pool.join()
            pool = None
        raise
    finally:
        if pool is not None:
            pool.close()
            pool.join()


# ----------------------------------------------------------------------------------------------
# Pass 2: temporal smoothing and state assembly
# ----------------------------------------------------------------------------------------------
def viterbi(E, lam):
    """Min-cost path through states with per-frame costs E (F x S) and a flat switch penalty lam."""
    F, S = E.shape
    if F == 0:
        return np.zeros(0, int)
    D = E[0].astype(np.float64).copy()
    bp = np.zeros((F, S), np.int16)
    ar = np.arange(S)
    for f in range(1, F):
        j = int(np.argmin(D))
        sw = D[j] + lam
        use = sw < D
        bp[f] = np.where(use, j, ar)
        D = np.where(use, sw, D) + E[f]
    path = np.zeros(F, int)
    path[-1] = int(np.argmin(D))
    for f in range(F - 1, 0, -1):
        path[f - 1] = bp[f, path[f]]
    return path


def runs_of(keys):
    """[(start, end_exclusive, key)] for consecutive equal keys."""
    out = []
    s = 0
    for i in range(1, len(keys) + 1):
        if i == len(keys) or keys[i] != keys[s]:
            out.append((s, i, keys[s]))
            s = i
    return out


NUM_RE = re.compile(r"^ *\d+(\.\d+)?$")


def parse_num(s):
    """Right-aligned decimal with leading blanks and no leading zero (e.g. '  34.12', '  0.119')."""
    return float(s) if NUM_RE.match(s) and not re.match(r"^ *0\d", s) else None


# P ~ V x I tolerance. Observed |P - V*I| on four hand-checked states of 12x8E.MOV: 0.09, 0.18, 0.32, 0.07 W
# (the meter rounds its own internal V and I). The flag catches wrong tens/hundreds digits, not last digits.
def p_tol(P):
    return 0.5 + 0.003 * abs(P)


def parse_blue(r0, r1):
    """Fixed-column parse. Returns (numbers dict, display text dict, flags list)."""
    flags = []
    txt = {"I_A": r0[0:7], "V_V": r0[8:15], "aux_value": r1[0:7], "P_W": r1[9:15]}
    f = {k: parse_num(v) for k, v in txt.items()}
    f["aux_unit"] = r1[7:9]
    if r0[7] != "A" or r0[15] != "V" or r1[15] != "W":
        flags.append("unit_glyph")
    for k in ("I_A", "V_V", "P_W"):
        if f[k] is None:
            flags.append("bad_" + k)
    if f["aux_unit"] not in FIELD_UNITS_AUX or f["aux_value"] is None:
        flags.append("bad_aux")
    return f, {k: (v.strip() if f[k] is not None else "") for k, v in txt.items()}, flags


def parse_thrust(s):
    """Right-aligned integer: leading blanks only, no leading zero, optional minus sign."""
    s2 = s.strip()
    if s != s.rstrip() or " " in s2:
        return None
    if re.match(r"^-?\d+$", s2) and not re.match(r"^-?0\d", s2):
        return int(s2)
    return None


def refresh_period(tt, lo=0.2, hi=2.0):
    """Refresh period P that best puts the display change times tt on one grid t0 + k*P
    (maximum circular resultant R; R = 1 means every change falls exactly on the grid)."""
    tt = np.asarray(tt, np.float64)
    if len(tt) < 8:
        return float("nan"), float("nan")
    P = np.arange(lo, hi, 0.0005)
    Rv = np.empty(len(P))
    for i0 in range(0, len(P), 500):
        Pc = P[i0:i0 + 500]
        Rv[i0:i0 + 500] = np.abs(np.exp(2j * np.pi * tt[None, :] / Pc[:, None]).mean(1))
    k = int(np.argmax(Rv))
    return float(P[k]), float(Rv[k])


def evidence(E_rows, chosen):
    """Min over units of (second-best summed cost - chosen summed cost) over a state's frames."""
    Ssum = E_rows.sum(0)                      # units x S
    ch = Ssum[np.arange(len(chosen)), chosen]
    other = Ssum.copy()
    other[np.arange(len(chosen)), chosen] = np.inf
    return float((other.min(1) - ch).min())


# ----------------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Read Mayatech MT10PRO displays from a video into CSV (accuracy first).")
    ap.add_argument("video")
    ap.add_argument("--out-dir", default=str(HERE / "data"))
    ap.add_argument("--debug-dir", default=None, help="default analysis/tests/out/video/RUN")
    ap.add_argument("--run-id", default=None)
    ap.add_argument("--prop", default=None, help="default: the video name if it looks like a prop (e.g. 12x8E)")
    for k in ("motor-id", "esc-id", "pack-id", "pack-fresh", "n-motors-live", "throttle-pct"):
        ap.add_argument("--" + k, default="")
    ap.add_argument("--start", type=float, default=0.0, help="start time (s)")
    ap.add_argument("--end", type=float, default=None, help="end time (s)")
    ap.add_argument("--step", type=int, default=1, help="process every Nth frame (1 = all, most accurate)")
    ap.add_argument("--workers", type=int, default=max(1, min(6, (os.cpu_count() or 2) // 2)))
    ap.add_argument("--lambda-blue", type=float, default=4.0, help="blue switch penalty, dot-equivalents")
    ap.add_argument("--lambda-thrust", type=float, default=1.0, help="thrust switch penalty, segment-equivalents")
    ap.add_argument("--ref-frame", type=int, default=None, help="force the registration reference frame")
    ap.add_argument("--no-overlays", action="store_true")
    ap.add_argument("--fresh", action="store_true", help="ignore cached pass-1 chunks")
    args = ap.parse_args()

    if not hasattr(cv2, "findTransformECCWithMask"):
        sys.exit("This OpenCV (%s) has no cv2.findTransformECCWithMask; install a newer opencv-python." % cv2.__version__)
    video = Path(args.video).resolve()
    if not video.exists():
        sys.exit("video not found: %s" % video)
    run_id = args.run_id or video.stem
    prop = args.prop if args.prop is not None else (video.stem if re.match(r"^\d+x\d+", video.stem) else "")
    out_dir = Path(args.out_dir)
    dbg = Path(args.debug_dir) if args.debug_dir else HERE / "out" / "video" / run_id
    cache_dir = dbg / "chunks"
    for p in (out_dir, dbg, cache_dir):
        p.mkdir(parents=True, exist_ok=True)
    logf = open(dbg / (run_id + "_log.txt"), "w")

    def log(msg, echo=False):
        logf.write(msg + "\n")
        logf.flush()
        if echo:
            print(msg, flush=True)

    T0 = time.time()
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS)
    nfr = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fw, fh = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    if not fps or fps <= 0 or nfr <= 0:
        sys.exit("cannot read frame rate / frame count from %s" % video)
    f0 = max(0, int(round(args.start * fps)))
    f1 = nfr if args.end is None else min(nfr, int(round(args.end * fps)))
    if f1 - f0 < 10:
        sys.exit("time range too short")
    workers = max(1, args.workers)
    cv_threads = max(1, (os.cpu_count() or 2) // workers)
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("MKL_NUM_THREADS", "1")
    log("read_mt10pro_video.py v%s  %s" % (SCRIPT_VERSION, time.strftime("%Y-%m-%d %H:%M:%S")), echo=True)
    log("video %s: %dx%d, %.3f fps, %d frames (%.2f s); range frames %d-%d, step %d, workers %d"
        % (video.name, fw, fh, fps, nfr, nfr / fps, f0, f1 - 1, args.step, workers), echo=True)

    # ---------------- setup: candidate scan ----------------
    stride, gap = 15, 4
    base = {"video": str(video), "fps": fps, "stride": stride, "gap": gap, "f0": f0, "cv_threads": cv_threads}
    span = max(stride * 8, (f1 - f0) // (workers * 3) // stride * stride)
    scan_jobs = [(a, min(a + span + gap + 1, f1)) for a in range(f0, f1, span)]
    scan = {}
    for res in run_jobs(_scan_chunk, scan_jobs, base, workers, log, "setup scan"):
        for row in res:
            scan[row[0]] = row
    pairs = []
    for idx, row in scan.items():
        if (idx - f0) % stride == 0 and idx + gap in scan:
            r2 = scan[idx + gap]
            if row[3] and r2[3] and row[2] == r2[2]:
                pairs.append((min(row[1], r2[1]), idx, row[2]))
    pairs.sort(reverse=True)
    log("setup: %d scanned frames, %d clean in-state pairs" % (len(scan), len(pairs)), echo=True)
    if not pairs and args.ref_frame is None:
        sys.exit("no frame in range where the blue LCD decodes cleanly; check the video framing (see log %s)" % logf.name)
    ref_idx = args.ref_frame if args.ref_frame is not None else pairs[0][1]
    train = []
    for sh, idx, txt in pairs:
        if all(abs(idx - j) >= 45 for j, _ in train):
            train.append((idx, txt))
        if len(train) >= 8:
            break

    ref = read_one(video, ref_idx, fps)
    if ref is None:
        sys.exit("cannot read reference frame %d" % ref_idx)
    bq, tq = find_quads(ref)
    if bq is None or tq is None:
        sys.exit("displays not found in reference frame %d" % ref_idx)
    Hb0, Ht0 = canon_H(bq, BW, BH), canon_H(tq, TW, TH)
    Tb = cv2.warpPerspective(ref, Hb0, (BW + 2 * MARGIN, BH + 2 * MARGIN), flags=cv2.INTER_CUBIC)[..., 1].astype(np.float32)
    Tt = cv2.warpPerspective(ref, Ht0, (TW + 2 * MARGIN, TH + 2 * MARGIN), flags=cv2.INTER_CUBIC)[..., 1].astype(np.float32)
    a_ref, ok_ref = threshold_decode(Tb[MARGIN:MARGIN + BH, MARGIN:MARGIN + BW])
    if not units_ok(a_ref):
        sys.exit("unit glyphs A/V/W not found in reference frame %d (decoded %s). The script assumes the camera "
                 "orientation of 12x8E.MOV." % (ref_idx, "|".join(text_of(a_ref))))

    def band(W, H, w=24):
        k = np.zeros((H + 2 * MARGIN, W + 2 * MARGIN), np.uint8)
        cv2.rectangle(k, (MARGIN - w, MARGIN - w), (W + MARGIN + w, H + MARGIN + w), 1, -1)
        cv2.rectangle(k, (MARGIN + w, MARGIN + w), (W + MARGIN - w, H + MARGIN - w), 0, -1)
        return k
    mb, mt = band(BW, BH), band(TW, TH)
    for (r, c) in UNIT_CELLS:
        xa, ya = int(GX[r, c].min()) - 12, int(GY[r, c, :7].min()) - 12
        xb, yb = int(GX[r, c].max()) + 13, int(GY[r, c, :7].max()) + 13
        mb[ya + MARGIN:yb + MARGIN, xa + MARGIN:xb + MARGIN] = 1
    mt[TRI_BOX[1] + MARGIN:TRI_BOX[3] + MARGIN, TRI_BOX[0] + MARGIN:TRI_BOX[2] + MARGIN] = 1
    ctx = dict(base, Tb=Tb, Tt=Tt, mb=mb, mt=mt, area_b=quad_area(bq), area_t=quad_area(tq), thr_off=(0.0, 0.0))
    _worker_init(ctx)

    # ---------------- setup: learn dot footprints on the training frames ----------------
    tr = []
    for idx, txt in train:
        im = read_one(video, idx, fps)
        if im is None:
            continue
        Mb, Mt, info, _ = register(im, None)
        if Mb is None or Mt is None:
            continue
        R = cv2.warpPerspective(im, Mb, (BW, BH), flags=cv2.INTER_CUBIC)[..., 1].astype(np.float64)
        a, okc = threshold_decode(R)
        if not okc.all() or "|".join(text_of(a)) != txt:
            log("  training frame %d dropped: registered decode differs from scan decode" % idx)
            continue
        T = cv2.warpPerspective(im, Mt, (TW, TH), flags=cv2.INTER_CUBIC)[..., 1].astype(np.float32)
        tr.append({"idx": idx, "R": R, "a": a, "T": T, "ecc_b": info["ecc_b"], "ecc_t": info["ecc_t"]})
    if len(tr) < 2:
        sys.exit("fewer than 2 usable training frames; cannot learn the dot model")
    # first fit, then scale each frame to the joint model (exposure differs between frames): after this
    # every training frame has gain 1, so its rms is in the same units as rms/gain in pass 1
    FL, FU = learn_footprints([(f["R"], f["a"]) for f in tr])
    for f in tr:
        cf, _ = fit_gain(f["R"], sharp_model(f["a"], FL, FU))
        plane = cf[0] * PB[0] + cf[1] * PB[1] + cf[2] * PB[2]
        f["R"] = plane + (f["R"] - plane) / max(cf[3], 0.2)
    for rnd in range(4):
        FL, FU = learn_footprints([(f["R"], f["a"]) for f in tr])
        U = float(((FL - FU) ** 2).sum())
        bad = []
        for f in tr:
            res = read_blue(f["R"], f["a"], FL, FU, U)
            f["rms"], f["read_ok"] = res[3] / max(abs(res[2]), 1e-3), bool(np.array_equal(res[1], f["a"]))
            if not f["read_ok"]:
                bad.append(f["idx"])
        if bad:
            log("  training frames %s: model read disagrees with threshold read" % bad, echo=True)
        if not bad or len(tr) - len(bad) < 2 or rnd == 3:
            break
        log("  dropping them and relearning", echo=True)
        tr = [f for f in tr if f["read_ok"]]
    rms_ref = float(np.median([f["rms"] for f in tr]))
    # thrust: check the segment geometry offset on the training frames, and the reference noise level
    best_off, best_sc = (0.0, 0.0), -1.0
    sc0 = None
    for oy in range(-6, 7, 2):
        for ox in range(-6, 7, 2):
            smp = thrust_sampler(ox, oy)
            sc = float(np.mean([sep_score(thrust_dark(f["T"], smp)) for f in tr]))
            if (ox, oy) == (0, 0):
                sc0 = sc
            if sc > best_sc:
                best_off, best_sc = (float(ox), float(oy)), sc
    thr_off = best_off if best_sc > sc0 + 0.02 else (0.0, 0.0)
    smp = thrust_sampler(*thr_off)
    tsig_ref = float(np.median([thrust_costs(thrust_dark(f["T"], smp))[2] for f in tr]))
    log("setup: reference frame %d; training frames %s; dot model rms %.1f; thrust offset %s (sep %.3f vs %.3f at 0,0); thrust sigma %.3f"
        % (ref_idx, [f["idx"] for f in tr], rms_ref, thr_off, best_sc, sc0, tsig_ref), echo=True)
    sig_src = "%s|%d|%d|%d|%d|%d|%s|%.6e|%.6e|%s" % (SCRIPT_VERSION, video.stat().st_size, f0, f1, args.step, ref_idx,
                                                   [f["idx"] for f in tr], float(FL.sum()), float(FU.sum()), thr_off)
    sig = hashlib.sha1(sig_src.encode()).hexdigest()
    with open(dbg / (run_id + "_setup.json"), "w") as fh_:
        json.dump({"video": str(video), "fps": fps, "frames": nfr, "range": [f0, f1], "step": args.step,
                   "ref_frame": ref_idx, "train_frames": [f["idx"] for f in tr],
                   "train_text": ["|".join(text_of(f["a"])) for f in tr], "train_rms": [f["rms"] for f in tr],
                   "rms_ref": rms_ref, "U": U, "thrust_offset": thr_off, "tsig_ref": tsig_ref, "signature": sig}, fh_, indent=1)
    np.savez(dbg / (run_id + "_model.npz"), FL=FL, FU=FU, Tb=Tb, Tt=Tt)

    # ---------------- pass 1 ----------------
    ctx.update(FL=FL, FU=FU, U=U, thr_off=thr_off, step=args.step, sig=sig, cache_dir=str(cache_dir), fresh=args.fresh)
    clen = max(1, 90 // args.step) * args.step
    jobs = [(a, min(a + clen, f1)) for a in range(f0, f1, clen)]
    log("pass 1: %d chunks of %d frames (finished chunks are cached, so an interrupted run resumes)" % (len(jobs), clen), echo=True)
    parts = [p for p in run_jobs(_process_chunk, jobs, ctx, workers, log, "pass 1") if len(p["idx"])]
    if not parts:
        sys.exit("pass 1 produced no frames")
    D = {k: np.concatenate([p[k] for p in parts]) for k in REC_KEYS}
    o = np.argsort(D["idx"], kind="stable")
    D = {k: v[o] for k, v in D.items()}
    _, uniq = np.unique(D["idx"], return_index=True)
    D = {k: v[uniq] for k, v in D.items()}
    F = len(D["idx"])
    if F == 0:
        sys.exit("pass 1 produced no frames")
    t = D["t"].astype(np.float64)
    np.savez_compressed(dbg / (run_id + "_pass1.npz"), **D)
    log("pass 1: %d frames, mean %.2f s per frame per worker" % (F, float(np.mean(D["tproc"]))), echo=True)

    # ---------------- pass 2: smoothing ----------------
    # Frame weights. Glyph-cost noise in dot-equivalents scales with (fit rms / gain), so the log-likelihood
    # weight is (rms_ref / rel_rms)^2, capped at 1 so no frame counts more than a clean training frame.
    # A blue fit worse than 3x the training frames (occlusion, display leaving the picture) gets weight 0.
    gain = D["gain"].astype(np.float64)
    rel = D["rms"] / np.maximum(np.abs(gain), 1e-6)
    bval = D["blue_valid"].astype(bool) & np.isfinite(rel) & (gain > 0.3) & (rel < 3.0 * rms_ref)
    wb = np.where(bval, np.minimum((rms_ref / np.maximum(rel, 1e-6)) ** 2, 1.0), 0.0)
    wb = np.where(D["stable"].astype(bool), wb, 0.5 * wb)
    Eb = D["ct"].astype(np.float64) * wb[:, None, None, None]              # F, 2, 16, NG
    path_b = np.zeros((F, 2, 16), int)
    for r in range(2):
        for c in range(16):
            path_b[:, r, c] = viterbi(Eb[:, r, c, :], args.lambda_blue)
    tval = D["thrust_valid"].astype(bool) & np.isfinite(D["tsig"])
    wt = np.where(tval, np.minimum((tsig_ref / np.maximum(D["tsig"], 1e-6)) ** 2, 1.0), 0.0)
    Et = D["tc"].astype(np.float64) * wt[:, None, None]                    # F, 5, ND
    path_t = np.zeros((F, 5), int)
    for k in range(5):
        path_t[:, k] = viterbi(Et[:, k, :], args.lambda_thrust)

    raw_b = D["ct"].argmin(-1)
    raw_t = D["tc"].argmin(-1)
    btxt = ["|".join(text_of(p)) for p in path_b]
    ttxt = ["".join(DKEYS[v] for v in p) for p in path_t]
    raw_btxt = ["|".join(text_of(p)) for p in raw_b]
    raw_ttxt = ["".join(DKEYS[v] for v in p) for p in raw_t]
    tval_num = [parse_thrust(s) if tval[i] else None for i, s in enumerate(ttxt)]

    def min_margin(C):
        s = np.sort(C, -1)
        return (s[..., 1] - s[..., 0]).reshape(len(C), -1).min(1)
    raw_b_marg = min_margin(D["ct"])
    raw_t_marg = min_margin(D["tc"])

    def mixed(k, a, b):
        return all(ci == ai or ci == bi for ci, ai, bi in zip(k, a, b))

    # thrust states. Genuine thrust states can last 1 frame, so short runs made only of digits from the
    # neighboring states are flagged possible_mix (kept in the states file, left out of T_g statistics).
    vt = np.where(tval)[0]
    truns = runs_of([ttxt[i] for i in vt])
    tmix = np.zeros(F, bool)
    tstates = []
    for n, (s, e, k) in enumerate(truns):
        fr = vt[s:e]
        flags = []
        if e - s <= 2 and 0 < n < len(truns) - 1 and mixed(k, truns[n - 1][2], truns[n + 1][2]):
            flags.append("possible_mix")
            tmix[fr] = True
        val = parse_thrust(k)
        if val is None:
            flags.append("bad_digits")
        ev = evidence(Et[fr], np.array([DKEYS.index(ch) for ch in k]))
        if ev < 1.0:
            flags.append("weak_evidence")
        tstates.append({"t_start_s": t[fr[0]], "t_end_s": t[fr[-1]], "n_frames": len(fr), "display": "[" + k + "]",
                        "T_g": val, "evidence_min": ev, "raw_agree_frac": float(np.mean([raw_ttxt[i] == k for i in fr])),
                        "flags": ";".join(flags)})

    # blue states. The blue LCD refreshes about every 0.46 s, so a run of 3 frames or fewer made only of
    # cells from its neighbors is a refresh caught mid-change (rolling shutter / LCD response) and is dropped.
    vb = np.where(bval)[0]
    bruns_all = runs_of([btxt[i] for i in vb])
    bruns = [(s, e, k) for n, (s, e, k) in enumerate(bruns_all)
             if not (e - s <= 3 and 0 < n < len(bruns_all) - 1 and mixed(k, bruns_all[n - 1][2], bruns_all[n + 1][2]))]
    bstates = []
    frame_state = np.full(F, -1)
    for sid, (s, e, k) in enumerate(bruns):
        fr = vb[s:e]
        frame_state[fr] = sid
        r0, r1 = k.split("|")
        num, txt, flags = parse_blue(r0, r1)
        ev = evidence(Eb[fr].reshape(len(fr), 32, NG), np.array([KEYS.index(ch) for ch in r0 + r1]))
        if (t[fr[-1]] - t[fr[0]]) < 0.2:
            flags.append("short")
        if ev < 1.0:
            flags.append("weak_evidence")
        pchk = None
        if num["I_A"] is not None and num["V_V"] is not None and num["P_W"] is not None:
            pchk = num["P_W"] - num["I_A"] * num["V_V"]
            if abs(pchk) > p_tol(num["P_W"]):
                flags.append("P_ne_VxI")
        tv = [tval_num[i] for i in fr if tval_num[i] is not None and not tmix[i]]
        bstates.append({"state_id": sid, "t_start_s": t[fr[0]], "t_end_s": t[fr[-1]], "t_mid_s": 0.5 * (t[fr[0]] + t[fr[-1]]),
                        "n_frames": len(fr), "row0": "[" + r0 + "]", "row1": "[" + r1 + "]",
                        "I_A": txt["I_A"], "V_V": txt["V_V"], "aux_value": txt["aux_value"], "aux_unit": num["aux_unit"],
                        "P_W": txt["P_W"], "P_minus_VxI_W": pchk,
                        "T_g_mean": "%.1f" % np.mean(tv) if tv else None, "T_g_median": "%.1f" % np.median(tv) if tv else None,
                        "T_g_min": min(tv) if tv else None, "T_g_max": max(tv) if tv else None, "n_thrust_frames": len(tv),
                        "evidence_min": ev, "raw_agree_frac": float(np.mean([raw_btxt[i] == k for i in fr])),
                        "flags": ";".join(flags), "_frames": fr})
    soft = ("short", "weak_evidence", "P_ne_VxI")

    # ---------------- outputs ----------------
    def fmt(v, nd=3):
        if v is None:
            return ""
        if isinstance(v, (float, np.floating)):
            return "" if not np.isfinite(v) else ("%.*f" % (nd, v))
        return str(v)

    def write_csv(path, cols, rows):
        with open(path, "w", newline="") as fh_:
            w = csv.writer(fh_)
            w.writerow(cols)
            for row in rows:
                w.writerow([fmt(row.get(c)) for c in cols])

    fcols = ["frame", "t_s", "blue_valid", "thrust_valid", "reg_blue", "reg_thrust", "ecc_blue", "ecc_thrust",
             "blue_gain", "blue_rms", "blue_rel_rms", "blue_weight", "blur_sx_px", "blur_sy_px", "blue_iters", "blue_stable",
             "blue_raw_row0", "blue_raw_row1", "blue_raw_min_margin", "blue_row0", "blue_row1", "blue_state_id",
             "thrust_raw", "thrust_raw_min_margin", "thrust_sigma", "thrust_weight", "thrust_display", "T_g",
             "thrust_possible_mix", "t_proc_s"]
    frows = []
    for i in range(F):
        rr0, rr1 = raw_btxt[i].split("|")
        s0, s1 = btxt[i].split("|")
        hb = bool(D["blue_valid"][i])
        frows.append({"frame": int(D["idx"][i]), "t_s": t[i], "blue_valid": int(bval[i]), "thrust_valid": int(tval[i]),
                      "reg_blue": int(D["reg_b"][i]), "reg_thrust": int(D["reg_t"][i]), "ecc_blue": D["ecc_b"][i],
                      "ecc_thrust": D["ecc_t"][i], "blue_gain": D["gain"][i], "blue_rms": D["rms"][i], "blue_rel_rms": rel[i],
                      "blue_weight": wb[i], "blur_sx_px": D["sx"][i], "blur_sy_px": D["sy"][i],
                      "blue_iters": int(D["iters"][i]), "blue_stable": int(D["stable"][i]),
                      "blue_raw_row0": ("[" + rr0 + "]") if hb else "", "blue_raw_row1": ("[" + rr1 + "]") if hb else "",
                      "blue_raw_min_margin": raw_b_marg[i] if hb else None,
                      "blue_row0": ("[" + s0 + "]") if bval[i] else "", "blue_row1": ("[" + s1 + "]") if bval[i] else "",
                      "blue_state_id": int(frame_state[i]) if frame_state[i] >= 0 else None,
                      "thrust_raw": ("[" + raw_ttxt[i] + "]") if tval[i] else "",
                      "thrust_raw_min_margin": raw_t_marg[i] if tval[i] else None, "thrust_sigma": D["tsig"][i],
                      "thrust_weight": wt[i], "thrust_display": ("[" + ttxt[i] + "]") if tval[i] else "", "T_g": tval_num[i],
                      "thrust_possible_mix": int(tmix[i]), "t_proc_s": D["tproc"][i]})
    p_frames = out_dir / (run_id + "_frames.csv")
    write_csv(p_frames, fcols, frows)
    bcols = ["state_id", "t_start_s", "t_end_s", "t_mid_s", "n_frames", "row0", "row1", "I_A", "V_V", "aux_value", "aux_unit",
             "P_W", "P_minus_VxI_W", "T_g_mean", "T_g_median", "T_g_min", "T_g_max", "n_thrust_frames", "evidence_min",
             "raw_agree_frac", "flags"]
    p_blue = out_dir / (run_id + "_blue_states.csv")
    write_csv(p_blue, bcols, bstates)
    tcols = ["t_start_s", "t_end_s", "n_frames", "display", "T_g", "evidence_min", "raw_agree_frac", "flags"]
    p_thr = out_dir / (run_id + "_thrust_states.csv")
    write_csv(p_thr, tcols, tstates)
    t2cols = ["run_id", "video_file", "t_s", "prop", "motor_id", "esc_id", "pack_id", "pack_fresh", "n_motors_live",
              "throttle_pct", "T_g", "rpm", "rpm_source", "I_A", "V_batt_V", "P_W", "temp_motor_F", "temp_air_F",
              "press_inHg", "rh_pct", "notes"]
    t2rows = []
    for s in bstates:
        fl = [f for f in s["flags"].split(";") if f]
        if [f for f in fl if f not in soft] or "short" in fl:
            continue
        note = "auto v%s: blue state %d %.2f-%.2f s (%d frames); aux %s %s; T_g = mean of %d thrust frames (median %s, min %s, max %s)" % (
            SCRIPT_VERSION, s["state_id"], s["t_start_s"], s["t_end_s"], s["n_frames"], s["aux_value"], s["aux_unit"],
            s["n_thrust_frames"], fmt(s["T_g_median"]), fmt(s["T_g_min"]), fmt(s["T_g_max"]))
        if fl:
            note += "; flags " + ";".join(fl)
        t2rows.append({"run_id": run_id, "video_file": video.name, "t_s": s["t_mid_s"], "prop": prop,
                       "motor_id": args.motor_id, "esc_id": args.esc_id, "pack_id": args.pack_id, "pack_fresh": args.pack_fresh,
                       "n_motors_live": args.n_motors_live, "throttle_pct": args.throttle_pct, "T_g": s["T_g_mean"],
                       "I_A": s["I_A"], "V_batt_V": s["V_V"], "P_W": s["P_W"], "notes": note})
    p_t2 = out_dir / (run_id + "_t2.csv")
    write_csv(p_t2, t2cols, t2rows)

    # ---------------- display refresh rate (TEST_PLAN asks for it) ----------------
    tt = []
    for (s1, e1, _), (s2, e2, _) in zip(bruns[:-1], bruns[1:]):
        ta, tb = t[vb[e1 - 1]], t[vb[s2]]
        if tb - ta <= 5.0 / fps:
            tt.append(0.5 * (ta + tb))
    P_blue, R_blue = refresh_period(tt)
    dth = np.diff([s["t_start_s"] for s in tstates if "possible_mix" not in s["flags"]])
    log("blue refresh: period %.4f s (%.3f Hz), grid alignment R %.3f from %d changes" % (P_blue, 1 / P_blue if P_blue else 0, R_blue, len(tt)))
    if len(dth):
        log("thrust value changes: %d, interval min %.3f s, 5th pct %.3f s, median %.3f s (30 fps video cannot resolve a faster refresh)"
            % (len(dth) + 1, dth.min(), np.percentile(dth, 5), np.median(dth)))

    # ---------------- overlays ----------------
    if not args.no_overlays and bstates:
        ov = dbg / "overlays"
        ov.mkdir(exist_ok=True)
        want = {}
        for s in bstates:
            fr = s["_frames"]
            best = fr[int(np.argmax(raw_b_marg[fr]))]
            want[int(D["idx"][best])] = (s, best)
        for idx in sorted(want):
            s, i = want[idx]
            if not np.isfinite(D["Mb"][i]).all():
                continue
            im = read_one(video, idx, fps)
            if im is None:
                continue
            Rb = cv2.warpPerspective(im, D["Mb"][i], (BW, BH), flags=cv2.INTER_CUBIC)
            tw = int(TW * BH / TH)
            if np.isfinite(D["Mt"][i]).all():
                Tt_ = cv2.resize(cv2.warpPerspective(im, D["Mt"][i], (TW, TH), flags=cv2.INTER_CUBIC), (tw, BH))
            else:
                Tt_ = np.zeros((BH, tw, 3), np.uint8)
            canvas = np.zeros((BH + 120, BW + tw, 3), np.uint8)
            canvas[:BH, :BW] = Rb
            canvas[:BH, BW:] = Tt_
            txt1 = "state %d  t %.2f-%.2f s  frame %d   %s %s   thrust [%s]" % (
                s["state_id"], s["t_start_s"], s["t_end_s"], idx, s["row0"], s["row1"], ttxt[i])
            txt2 = "I %s A  V %s V  P %s W  T_g mean %s g  evidence %.1f  flags %s" % (
                s["I_A"], s["V_V"], s["P_W"], fmt(s["T_g_mean"]), s["evidence_min"], s["flags"] or "-")
            cv2.putText(canvas, txt1, (10, BH + 45), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
            cv2.putText(canvas, txt2, (10, BH + 100), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (255, 255, 255), 2)
            canvas = cv2.resize(canvas, (canvas.shape[1] // 2, canvas.shape[0] // 2), interpolation=cv2.INTER_AREA)
            cv2.imwrite(str(ov / ("state_%04d_t%07.2f.jpg" % (s["state_id"], s["t_mid_s"]))), canvas, [cv2.IMWRITE_JPEG_QUALITY, 88])

    # ---------------- summary ----------------
    nflag = sum(1 for s in bstates if s["flags"])
    npv = sum(1 for s in bstates if "P_ne_VxI" in s["flags"])
    nweak = sum(1 for s in bstates if "weak_evidence" in s["flags"])
    tvals = [s["T_g"] for s in tstates if s["T_g"] is not None]
    summ = [
        "done in %.1f min" % ((time.time() - T0) / 60),
        "frames: %d processed; blue readable %d (%.0f%%), thrust readable %d (%.0f%%)" % (
            F, bval.sum(), 100 * bval.mean(), tval.sum(), 100 * tval.mean()),
        "blue states: %d; %d with a flag (%d weak evidence, %d fail P ~ V x I); %d rows in the t2 file" % (
            len(bstates), nflag, nweak, npv, len(t2rows)),
        "thrust states: %d, %s to %s g" % (len(tstates), min(tvals) if tvals else "-", max(tvals) if tvals else "-"),
        "blue display refresh period %.3f s (alignment R %.2f, 1 = perfect)" % (P_blue, R_blue),
        "outputs:", "  " + str(p_t2), "  " + str(p_blue), "  " + str(p_thr), "  " + str(p_frames),
        "  debug + overlays: " + str(dbg),
        "check a few overlays; states flagged weak_evidence or P_ne_VxI deserve a look.",
    ]
    for line in summ:
        log(line, echo=True)
    logf.close()


if __name__ == "__main__":
    main()
