#!/usr/bin/env python3
"""
predict_config.py -- which legal layout gives the most thrust on the X2820 800 KV: 2 x 12 in or 4 x 9 in,
and with which prop. Calibrated to the T-2 stand data, not the datasheet.

Model (per motor, all motors identical, one shared 4S pack):
  top end  rpm = K (V_batt - R' I)          measured ESC-ceiling line, K 776.1 rpm/V, R' 75.0 mOhm
                                            (PROJECT_MEMORY 2026-09-26 12:00; refit below as a check)
  current  I = c0 + K_si k_q Q_apc(rpm, J)  battery-side. Under PWM at duty d the motor sees I/d, so
                                            I = d I0 + (Kv d) Q; at the ceiling Kv d = K, so K sets it.
  thrust   T = k_t T_apc(rpm, J)
  pack     V_batt = V0 - n I R_pack
k_t per prop = median T / T_apc over the stand holds in the upper half of that prop's thrust range (audio rpm;
k_t rises with rpm, so the low holds would bias it low). k_q per prop = mean of
(I - c0) / (K_si Q_apc) over the ESC-ceiling points. Untested props (9x6E and the APC-only ones) borrow the
factors of the nearest tested prop and get a band from the min / max factors over all tested props.

Scenarios [INFERRED brackets]:
  ESC  "as set"      K 776.1, R' 75.0 mOhm (the ceiling measured on 2026-09-23/25, stick ~80)
       "calibrated"  K 809, R' 69 mOhm (fit A Kv 809 -> dmax 0.96 -> R = 75.0 x 0.96^2; UNVERIFIED)
  pack "fresh ideal" V0 16.4 V, 39 mOhm (step at the 12x8E cut); "fresh real" V0 16.0 V, 68 mOhm (ramp slope)
Air: DA 1400 ft (design DA, same basis as predict_x2820 and the sizing). Airspeeds: static and V_R 36.4 ft/s
(V_R from the stale S1223 design card; representative only).

Run:  python analysis/tests/predict_config.py
Out:  analysis/tests/out/predict_config/{calibration.csv, predict.csv, summary.txt}
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sizing"))
sys.path.insert(0, str(HERE))
from propulsion import parse_apc, coeffs  # noqa: E402
from common import rho_from_da, KG_PER_SLUGFT3, FT_PER_M, N_PER_LBF  # noqa: E402
from reduce_thrust import air  # noqa: E402

TWO_PI = 2.0 * math.pi
G_PER_N = 1000.0 / 9.80665
K_CEIL, R_CEIL = 776.1, 0.0750   # measured ceiling line (log 2026-09-26 12:00)
C0 = 0.9                         # A, I0 term (datasheet 0.9 A at 10 V; same as reduce_thrust fit A)
I_MAX, I_ESC = 46.0, 60.0        # A per motor: X2820 46 A / 30 s, X60A 60 A continuous
V_LVC = 12.0                     # V, ESC default LVC 3.0 V/cell (X45/65/85 manual; UNVERIFIED for X60A)
DA_FT, V_R_FPS = 1400.0, 36.4
ESC = {"as set": (776.1, 0.0750), "calibrated": (809.0, 0.0690)}
PACK = {"fresh ideal": (16.4, 0.039), "fresh real": (16.0, 0.068)}
ON_HAND = {"12x6e", "12x8e", "12x10e", "9x45e", "9x6e"}
CONFIGS = [(2, "12x6e"), (2, "12x8e"), (2, "12x10e"), (4, "9x45e"), (4, "9x6e"),
           (2, "12x12e"), (2, "11x7e"), (2, "11x10e"), (4, "9x75e")]
BORROW = {"9x6e": "9x45e", "9x75e": "9x45e", "12x12e": "12x10e", "11x7e": "12x8e", "11x10e": "12x10e"}
APC_NAME = {"12x6E": "12x6e", "12x8E": "12x8e", "12x10E": "12x10e", "9x4.5E": "9x45e"}
# Ceiling points not in the holds file (uncalled stick pushes), from the log 2026-09-26 12:00 "top of the run":
EXTRA_CEIL = [("2026-09-25_12x6E_T1", "12x6E", 2028.0, 8585.0, 29.5, 13.28),
              ("2026-09-25_12x10E_T1", "12x10E", 1823.0, 7337.0, 36.6, 12.22)]
OUT = HERE / "out" / "predict_config"


def loads(p, rpm, rho, V_ms=0.0):
    """APC thrust (N) and torque (N m) at rpm and airspeed."""
    n = rpm / 60.0
    ct, cp = coeffs(p, rpm, V_ms / (n * p["D_m"]))
    D = p["D_m"]
    return ct * rho * n ** 2 * D ** 4, cp * rho * n ** 2 * D ** 5 / TWO_PI


def solve(p, K, Rm, k_q, k_t, v0, r_b, n_mot, rho, V_ms=0.0, c0=C0):
    """Per-motor full-throttle point for n_mot motors on one pack."""
    K_si = K * TWO_PI / 60.0

    def f(om):
        I = (v0 - om / K_si) / (Rm + n_mot * r_b)
        return I - c0 - K_si * k_q * loads(p, om * 60.0 / TWO_PI, rho, V_ms)[1]

    om = brentq(f, 50.0, K_si * v0 * 0.999, xtol=1e-4)
    rpm = om * 60.0 / TWO_PI
    I = (v0 - om / K_si) / (Rm + n_mot * r_b)
    return dict(rpm=rpm, I=I, T_N=k_t * loads(p, rpm, rho, V_ms)[0], V=v0 - n_mot * I * r_b)


def calibrate(rep, c0=C0):
    cond = pd.read_csv(HERE / "data" / "t2_conditions.csv").set_index("run_id")
    rho_run = {r: air(cond.loc[r])["rho"] for r in cond.index}
    h = pd.read_csv(HERE / "data" / "2026-09-25_battery_holds.csv")
    h = h[~h["flags"].fillna("").str.contains("no_rpm|thrust_event")].copy()
    kt_pts, ceil = [], []
    for _, r in h.iterrows():
        p = parse_apc(APC_NAME[r.prop])
        T_apc = loads(p, r.rpm_median, rho_run[r.run_id])[0] * G_PER_N
        if T_apc >= 200.0:
            kt_pts.append((r.prop, T_apc, r.T_mean_g / T_apc))
    # 12x8E (2026-09-23): steady points already reduced by reduce_thrust.py at that run's rho
    pts = pd.read_csv(HERE / "out" / "reduce" / "12x8E_points.csv")
    pts = pts[pts["flags"].isna() & (pts.T_apc_g >= 200.0)]
    kt_pts += [("12x8E", t, v) for t, v in zip(pts.T_apc_g, pts.T_ratio)]
    ft = pts[pts.full_throttle]
    ceil.append(("12x8E", "12x8E", ft.T_g_mean.mean(), ft.rpm_mean.mean(), ft.I_A.mean(), ft.V_V.mean()))
    # ceiling holds: stick >= 80 on the 2026-09-25 runs (thrust_event holds kept here, rpm and I are steady)
    hc = pd.read_csv(HERE / "data" / "2026-09-25_battery_holds.csv")
    hc = hc[hc.throttle_pos >= 80]
    ceil += [(r.run_id, r.prop, r.T_mean_g, r.rpm_median, r.I_mean, r.V_mean) for _, r in hc.iterrows()]
    ceil += EXTRA_CEIL
    cdf = pd.DataFrame(ceil, columns=["run_id", "prop", "T_g", "rpm", "I", "V"])
    # refit the ceiling line as a check: rpm = a V - b I
    A = np.c_[cdf.V, -cdf.I]
    a, b = np.linalg.lstsq(A, cdf.rpm, rcond=None)[0]
    cdf["line_err_pct"] = 100.0 * (cdf.rpm / (K_CEIL * (cdf.V - R_CEIL * cdf.I)) - 1.0)
    rep(f"Ceiling line check over {len(cdf)} points: refit K {a:.1f} rpm/V, R' {1000 * b / a:.1f} mOhm "
        f"(log: {K_CEIL} / {1000 * R_CEIL:.1f}); max |err| vs log line {cdf.line_err_pct.abs().max():.2f} pct")
    K_si = K_CEIL * TWO_PI / 60.0
    kq = []
    for _, r in cdf.iterrows():
        rho = rho_run.get(r.run_id, rho_run["12x8E"])
        Q = loads(parse_apc(APC_NAME[r.prop]), r.rpm, rho)[1]
        kq.append((r.I - c0) / (K_si * Q))
    cdf["k_q"] = kq
    # k_t rises with rpm and flattens near the top (12 in: ~0.92 below 4500 rpm, 0.98-1.04 above 6000), so it is
    # taken over the upper half of each prop's measured thrust range, where the predictions sit
    kt = pd.DataFrame(kt_pts, columns=["prop", "T_apc", "k_t"])
    kt_top = kt[kt.T_apc >= 0.5 * kt.groupby("prop").T_apc.transform("max")]
    cal = kt_top.groupby("prop").k_t.agg(["median", "std", "count"]).rename(
        columns={"median": "k_t", "std": "k_t_sd", "count": "n_kt"})
    cal["k_t_all"] = kt.groupby("prop").k_t.median()
    g = cdf.groupby("prop").k_q
    cal["k_q"], cal["k_q_sd"], cal["n_kq"] = g.mean(), g.std(), g.count()
    cal.index = [APC_NAME[i] for i in cal.index]
    return cal, cdf


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = []

    def rep(s=""):
        lines.append(s)

    cal, cdf = calibrate(rep)
    rep("Per-prop calibration against APC PER3 (k_t thrust, k_q torque/current):")
    rep(cal.round(3).to_string())
    rep("Ceiling points: " + "; ".join(f"{r.prop} {r.rpm:.0f} rpm {r.I:.1f} A {r.V:.2f} V k_q {r.k_q:.3f}"
                                         for _, r in cdf.iterrows()))
    rho = float(rho_from_da(DA_FT)) * KG_PER_SLUGFT3
    V_R = V_R_FPS / FT_PER_M
    kt_rng = (cal.k_t.min(), cal.k_t.max())
    kq_rng = (cal.k_q.min(), cal.k_q.max())
    rows = []
    for n_mot, pn in CONFIGS:
        p = parse_apc(pn)
        src = pn if pn in cal.index else BORROW[pn]
        variants = [("nominal", cal.loc[src, "k_t"], cal.loc[src, "k_q"])]
        if pn not in cal.index:  # band: worst and best factor pairs seen on any tested prop
            variants += [("band low", kt_rng[0], kq_rng[1]), ("band high", kt_rng[1], kq_rng[0])]
        for esc, (K, Rm) in ESC.items():
            for pack, (v0, rb) in PACK.items():
                for var, k_t, k_q in variants:
                    s0 = solve(p, K, Rm, k_q, k_t, v0, rb, n_mot, rho)
                    sR = solve(p, K, Rm, k_q, k_t, v0, rb, n_mot, rho, V_R)
                    I_pk = max(s0["I"], sR["I"])
                    rows.append(dict(
                        layout=f"{n_mot} x {pn}", n=n_mot, prop=pn, on_hand=pn in ON_HAND,
                        factors=("measured" if src == pn else f"from {src}"), variant=var, esc=esc, pack=pack,
                        rpm0=round(s0["rpm"]), rpm_limit=round(p["rpm_limit"]),
                        T0_lbf=round(n_mot * s0["T_N"] / N_PER_LBF, 2), TVR_lbf=round(n_mot * sR["T_N"] / N_PER_LBF, 2),
                        I_motor_pk_A=round(I_pk, 1), pct_46A=round(100 * I_pk / I_MAX),
                        I_pack_pk_A=round(n_mot * I_pk, 1), V_batt_min=round(min(s0["V"], sR["V"]), 2),
                        below_LVC=min(s0["V"], sR["V"]) < V_LVC,
                        W_pack=round(n_mot * max(s0["I"] * s0["V"], sR["I"] * sR["V"]))))
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "predict.csv", index=False)
    cal.to_csv(OUT / "calibration.csv")

    rep()
    rep(f"Predictions, full throttle, DA {DA_FT:.0f} ft (rho {rho:.4f}), T0 static, TVR at {V_R_FPS} ft/s; totals per aircraft")
    cols = ["layout", "factors", "variant", "rpm0", "T0_lbf", "TVR_lbf", "I_motor_pk_A", "pct_46A",
            "I_pack_pk_A", "V_batt_min", "below_LVC"]
    for esc in ESC:
        for pack in PACK:
            d = df[(df.esc == esc) & (df.pack == pack)].sort_values("T0_lbf", ascending=False)
            rep(f"-- ESC {esc} {ESC[esc]}, pack {pack} {PACK[pack]}")
            rep(d[cols].to_string(index=False))
    # Sensitivity of the on-hand ranking (nominal factors, calibrated ESC, static / V_R):
    # c0 (I0 term) 0.5 and 1.5 A with k_q recalibrated to it; and a stiff 16.8 V, 0 ohm pack (upper bound)
    rep()
    rep("Sensitivity, calibrated ESC, on-hand props, nominal factors: T0/TVR lbf, peak A per motor")
    K, Rm = ESC["calibrated"]
    for name, c0, (v0, rb) in (("c0 0.5 A, fresh ideal", 0.5, PACK["fresh ideal"]),
                               ("c0 1.5 A, fresh ideal", 1.5, PACK["fresh ideal"]),
                               ("stiff 16.8 V, 0 ohm pack", C0, (16.8, 0.0))):
        cal_c = calibrate(lambda s: None, c0)[0]
        res = []
        for n_mot, pn in [c for c in CONFIGS if c[1] in ON_HAND]:
            src = pn if pn in cal_c.index else BORROW[pn]
            k_t, k_q = cal_c.loc[src, "k_t"], cal_c.loc[src, "k_q"]
            s0 = solve(parse_apc(pn), K, Rm, k_q, k_t, v0, rb, n_mot, rho, 0.0, c0)
            sR = solve(parse_apc(pn), K, Rm, k_q, k_t, v0, rb, n_mot, rho, V_R, c0)
            T0, TR = n_mot * s0["T_N"] / N_PER_LBF, n_mot * sR["T_N"] / N_PER_LBF
            res.append((T0, f"{n_mot}x{pn} {T0:.2f}/{TR:.2f} {max(s0['I'], sR['I']):.0f}A"))
        rep(f"  {name}: " + " | ".join(t for _, t in sorted(res, reverse=True)))
    (OUT / "summary.txt").write_text("\n".join(lines) + "\n", encoding="ascii")

    # short stdout: nominal rows, props on hand, ideal case and realistic case
    print("\n".join(lines[:2 + len(cal) + 1]))
    for esc, pack in (("calibrated", "fresh ideal"), ("as set", "fresh real")):
        d = df[(df.esc == esc) & (df.pack == pack) & df.on_hand & (df.variant == "nominal")]
        print(f"-- {esc} ESC, {pack} pack (on-hand props, nominal factors)")
        print(d.sort_values("T0_lbf", ascending=False)[["layout", "T0_lbf", "TVR_lbf", "I_motor_pk_A",
                                                       "I_pack_pk_A", "V_batt_min"]].to_string(index=False))
    print(f"Full tables: {OUT / 'summary.txt'}")


if __name__ == "__main__":
    main()
