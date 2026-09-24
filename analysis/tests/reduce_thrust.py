#!/usr/bin/env python3
"""
reduce_thrust.py -- T-2 static thrust-stand data reduction for one run (TEST_PLAN.md 3.8).

Inputs
  analysis/tests/data/RUN_rpm_states.csv  audio_rpm.py output: one row per MT10PRO display state with
                                          rpm (audio), I, V, thrust and quality flags
  analysis/tests/data/t2_conditions.csv   one hand-entered row per run: air temperature, altimeter or
                                          elevation, humidity, the full-throttle time window, hardware.
                                          Every value carries its source in the next column.
Outputs (analysis/tests/out/reduce/)
  RUN_points.csv    per steady state: T_apc and Q_apc at the measured rpm and this run's air density,
                    T / T_apc, per-point Kv estimates on the full-throttle points
  RUN_predict.csv   full-throttle predictions (12 in props, stand and aircraft) with each fitted motor
  RUN_summary.txt   the full report; stdout gets a short version

Steps (numbers follow TEST_PLAN.md 3.8)
  1. Air density. Station pressure from the altimeter setting and elevation, vapour pressure from the
     dewpoint (or RH), rho = P / (Rd * Tv); DA from density_altitude.density_altitude (NWS formula).
  2. RPM comes from audio_rpm.py, already in RUN_rpm_states.csv.
  3. T_apc = Ct(rpm, J=0) rho n^2 D^4 and Q_apc = Cp rho n^2 D^5 / (2 pi), from parse_apc / coeffs in
     analysis/sizing/propulsion.py (reused, not rewritten).
  4. THRUST_FACTOR_meas = mean and std of T / T_apc over the full-throttle points; the median over all
     steady points; and T = a T_apc + b over steady points with T_apc >= 200 g (the zero-offset term).
  5. Motor, on the full-throttle points only (the ESC is a closed switch, so V_motor = V_batt; Drela
     first-order model, drela_motorprop eqs 1-2: rpm = Kv (V - I R), Q = (I - I0) / Kv).
     One prop gives one load point, and one load point cannot separate Kv from R. Three fits are made:
       A  torque side: Kv from the APC Cp torque, (I - I0) / Q_apc; then R_eff from the speed equation.
          Leans on APC Cp being right (a 5 pct Cp error is a 5 pct Kv error).
       B  speed side: R fixed at datasheet Rm + ESC; Kv from the speed equation; then the Cp factor k_Q
          that makes the APC torque match the measured current.
       C  free least squares rpm = Kv V - Kv R I over the hold. Reported with its condition number; with
          one prop the V and I spread is tiny, so it is expected to be ill-conditioned.
     A and B both reproduce the measured point. They differ when the prop or the pack voltage changes.
     The no-prop run (TEST_PLAN Run C1) separates them: it measures Kv almost directly.
  6. Pack: V_batt = V0 - R_pack I over all steady points (includes polarization during the ramp), and
     the instant step at the throttle cut (last full-throttle state to the first state after the cut).
  7. Droop over the full-throttle hold: last / first state, for thrust, rpm and V_batt.
  8. The mean full-throttle point against analysis/tests/out/predict_x2820.csv and SunnySky's 100 pct row.
  9. Full-throttle predictions for the 12 in props with fits A and B, stand (1 motor) and aircraft
     (2 motors on one pack): on this pack, and on a fresh pack bracketed by V0 16.0 V with the ramp
     slope (pessimistic) and V0 16.4 V with the step at the cut (optimistic) [INFERRED bracket].

Run:  python analysis/tests/reduce_thrust.py 12x8E
"""
import argparse
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import brentq

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "sizing"))
from propulsion import parse_apc, coeffs  # noqa: E402
from density_altitude import density_altitude  # noqa: E402
from common import rho_from_da, KG_PER_SLUGFT3  # noqa: E402

# X2820 800 KV datasheet (reference/text/sunnysky_x2820_800kv_spec.txt) and model assumptions
KV_DS = 800.0
RM_DS = 0.041     # ohm, datasheet "Motor resistance 41 mOhm"
I0_DS = 0.9       # A, datasheet "No-load current 0.9A/10V"
RESC = 0.003      # ohm, same assumption as predict_x2820.py
I_MAX = 46.0      # A, datasheet "Max continuous current 46A/30s"
RD, RV = 287.05, 461.5   # J/(kg K), dry air and water vapour
TWO_PI = 2.0 * math.pi
G_PER_N = 1000.0 / 9.80665
PREDICT_PROPS = ["12x6e", "12x8e", "12x10e"]
FRESH_V0 = (16.0, 16.4)  # V, fresh-pack intercept under load [INFERRED bracket; 16.0 = propulsion.V_OC_TO]
MFR_100 = {"12x6e": (32.7, 2240.0), "12x8e": (38.5, 2300.0)}  # SunnySky 100 pct rows: A, gf at "14.8 V"


def air(c):
    """rho (kg/m^3), station pressure (hPa), vapour pressure (hPa), DA (ft) from one conditions row."""
    elev_ft = float(c["elev_ft"])
    alti = float(c["alti_inHg"]) if pd.notna(c["alti_inHg"]) else 29.92
    T_f = float(c["temp_air_F"])
    T_c = (T_f - 32.0) / 1.8
    es = 6.11 * 10.0 ** (7.5 * T_c / (237.3 + T_c))  # hPa, same Magnus form as density_altitude.py
    if pd.notna(c["dwpf_F"]):
        Td_c = (float(c["dwpf_F"]) - 32.0) / 1.8
        e = 6.11 * 10.0 ** (7.5 * Td_c / (237.3 + Td_c))
    else:
        e = es * float(c["rh_pct"]) / 100.0
    x = math.log10(e / 6.11)
    Td_c = 237.3 * x / (7.5 - x)
    H = elev_ft / 3.28084
    p_hpa = alti * ((288.0 - 0.0065 * H) / 288.0) ** 5.2561 * 33.8639
    T_k = T_c + 273.15
    rho = (p_hpa - e) * 100.0 / (RD * T_k) + e * 100.0 / (RV * T_k)
    da = float(density_altitude(T_f, Td_c * 1.8 + 32.0, alti, elev_ft=elev_ft))
    return dict(rho=rho, p_hpa=p_hpa, e_hpa=e, rh=100.0 * e / es, da_ft=da, alti=alti)


def prop_loads(p, rpm, rho):
    """Thrust (g) and torque (N m) from APC PER3 at J = 0."""
    n = rpm / 60.0
    ct, cp = coeffs(p, rpm, 0.0)
    D = p["D_m"]
    return ct * rho * n ** 2 * D ** 4 * G_PER_N, cp * rho * n ** 2 * D ** 5 / TWO_PI


def solve_ft(p, kv, R_m, I0, k_q, k_t, v0, r_b, n_mot, rho):
    """Full throttle, static: per-motor rpm, I, thrust g and V_batt. R_m is everything between the
    pack terminals and the back-EMF (ESC, wiring, winding); r_b is the pack, shared by n_mot motors."""
    kv_si = kv * TWO_PI / 60.0

    def f(om):
        I = (v0 - om / kv_si) / (R_m + n_mot * r_b)
        return (I - I0) / kv_si - k_q * prop_loads(p, om * 60.0 / TWO_PI, rho)[1]

    om = brentq(f, 50.0, kv_si * v0 * 0.999, xtol=1e-4)
    rpm = om * 60.0 / TWO_PI
    I = (v0 - om / kv_si) / (R_m + n_mot * r_b)
    return dict(rpm=rpm, I=I, T_g=k_t * prop_loads(p, rpm, rho)[0], V=v0 - n_mot * I * r_b)


def main():
    ap = argparse.ArgumentParser(description="T-2 thrust-stand data reduction (TEST_PLAN.md 3.8).")
    ap.add_argument("run_id")
    ap.add_argument("--data-dir", default=str(HERE / "data"))
    ap.add_argument("--out-dir", default=str(HERE / "out" / "reduce"))
    ap.add_argument("--conditions", default=None, help="default DATA_DIR/t2_conditions.csv")
    ap.add_argument("--prop", default=None, help="APC name as in reference/raw/apc_<name>.dat; default from the run")
    ap.add_argument("--i0", type=float, default=I0_DS, help="motor no-load current used in fits A and B, A")
    args = ap.parse_args()

    data, out = Path(args.data_dir), Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cond = pd.read_csv(args.conditions or data / "t2_conditions.csv", dtype={"run_id": str})
    cond = cond[cond.run_id == args.run_id]
    if cond.empty:
        sys.exit(f"[X] no row for run {args.run_id} in t2_conditions.csv")
    c = cond.iloc[0]
    prop = (args.prop or str(c["prop"]).replace("APC", "").strip()).lower()
    p = parse_apc(prop)
    st = pd.read_csv(data / f"{args.run_id}_rpm_states.csv")

    lines = []

    def rep(s=""):
        lines.append(s)

    # 1. air
    a = air(c)
    rho = a["rho"]
    rep(f"reduce_thrust.py  run {args.run_id}  prop {prop}  ({c['date_local']} {c['time_local']}, {c['site']})")
    rep(f"[1] Air: {c['temp_air_F']} F ({c['temp_source']}); elev {c['elev_ft']} ft ({c['elev_source']});"
        f" altimeter {a['alti']:.2f} inHg ({c['alti_source']})")
    rep(f"    station P {a['p_hpa']:.1f} hPa, e {a['e_hpa']:.1f} hPa (RH {a['rh']:.0f} pct; {c['rh_source']}"
        f" / dewpoint {c['dwpf_source']})")
    rep(f"    rho {rho:.4f} kg/m^3 = {rho / 1.225:.4f} x ISA SL; DA {a['da_ft']:.0f} ft (NWS);"
        f" ISA rho at that DA {float(rho_from_da(a['da_ft'])) * KG_PER_SLUGFT3:.4f}")

    # steady and full-throttle states
    flags = st["flags"].fillna("")
    steady = st[(flags == "") & st.rpm_mean.notna() & (st.I_A > 1.0)].copy()
    ft_mask = (steady.t_start_s >= float(c["ft_t_start_s"])) & (steady.t_end_s <= float(c["ft_t_end_s"]))
    steady["full_throttle"] = ft_mask
    ft = steady[ft_mask].copy()
    if ft.empty:
        sys.exit("[X] no clean states inside the full-throttle window")

    # 3. APC thrust and torque at the measured rpm
    loads = np.array([prop_loads(p, r, rho) for r in steady.rpm_mean])
    steady["T_apc_g"] = loads[:, 0]
    steady["Q_apc_Nm"] = loads[:, 1]
    steady["T_ratio"] = steady.T_g_mean / steady.T_apc_g
    steady["P_shaft_apc_W"] = steady.Q_apc_Nm * steady.rpm_mean * TWO_PI / 60.0
    steady["P_elec_W"] = steady.V_V * steady.I_A
    ft = steady[steady.full_throttle].copy()

    # 4. thrust factor
    tf_m, tf_s = ft.T_ratio.mean(), ft.T_ratio.std(ddof=1)
    big = steady[steady.T_apc_g >= 200.0]
    slope, icpt = np.polyfit(big.T_apc_g, big.T_g_mean, 1)
    res = big.T_g_mean - (slope * big.T_apc_g + icpt)
    rep(f"[4] THRUST_FACTOR_meas (full throttle, n {len(ft)}): {tf_m:.3f} +/- {tf_s:.3f} (1 sd);"
        f" all steady points (T_apc >= 200 g, n {len(big)}): median {big.T_ratio.median():.3f}")
    rep(f"    offset fit, steady points: T = {slope:.4f} T_apc {icpt:+.1f} g (rms {res.std(ddof=2):.1f} g);"
        f" with the offset removed the full-throttle ratio is {((ft.T_g_mean - icpt) / ft.T_apc_g).mean():.3f}")

    # 5. motor fits on the full-throttle points
    I, V, rpm, Q = ft.I_A.values, ft.V_V.values, ft.rpm_mean.values, ft.Q_apc_Nm.values
    i0 = args.i0
    kvA_pts = (I - i0) / Q * 60.0 / TWO_PI
    kvA = kvA_pts.mean()
    RA_pts = (V - rpm / kvA) / I
    RA = RA_pts.mean()
    RB = RM_DS + RESC
    kvB_pts = rpm / (V - I * RB)
    kvB = kvB_pts.mean()
    kqB_pts = (I - i0) / (kvB * TWO_PI / 60.0 * Q)
    kqB = kqB_pts.mean()
    X = np.column_stack([V, I])
    coef, *_ = np.linalg.lstsq(X, rpm, rcond=None)
    resid = rpm - X @ coef
    dof = max(len(rpm) - 2, 1)
    cov = np.linalg.inv(X.T @ X) * (resid @ resid) / dof
    kvC, RC = coef[0], -coef[1] / coef[0]
    kvC_se = math.sqrt(cov[0, 0])
    Xc = X - X.mean(axis=0)
    condC = np.linalg.cond(Xc / Xc.std(axis=0)) if len(rpm) > 2 else float("nan")
    ft["Kv_A_pt"], ft["R_A_pt"], ft["Kv_B_pt"], ft["kQ_B_pt"] = kvA_pts, RA_pts, kvB_pts, kqB_pts
    steady = steady.join(ft[["Kv_A_pt", "R_A_pt", "Kv_B_pt", "kQ_B_pt"]])
    mt = ft.mean(numeric_only=True)
    rep(f"[5] Full-throttle mean (n {len(ft)}, {ft.t_start_s.min():.1f}-{ft.t_end_s.max():.1f} s): {mt.rpm_mean:.0f} rpm,"
        f" {mt.I_A:.2f} A, {mt.V_V:.2f} V, {mt.T_g_mean:.0f} g; P_elec {mt.P_elec_W:.0f} W,"
        f" APC shaft {mt.P_shaft_apc_W:.0f} W (ratio {mt.P_shaft_apc_W / mt.P_elec_W:.3f})")
    rep(f"    A torque side (I0 {i0} A, k_Q 1): Kv {kvA:.0f} rpm/V (sd {kvA_pts.std(ddof=1):.0f});"
        f" R_eff {RA * 1000:.1f} mOhm = datasheet {RB * 1000:.0f} + {(RA - RB) * 1000:.1f} extra."
        f" Kv at k_Q 0.95 / 1.05: {kvA / 0.95:.0f} / {kvA / 1.05:.0f}")
    rep(f"    B speed side (R fixed {RB * 1000:.0f} mOhm): Kv {kvB:.0f} rpm/V (sd {kvB_pts.std(ddof=1):.0f},"
        f" {100 * (kvB / KV_DS - 1):+.1f} pct vs 800); APC Cp must be x {kqB:.3f} to match the current")
    rep(f"    C free LSQ over the hold: Kv {kvC:.0f} +/- {kvC_se:.0f} rpm/V, R {RC * 1000:.0f} mOhm,"
        f" condition no. {condC:.1f}, V span {np.ptp(V):.2f} V, I span {np.ptp(I):.2f} A -> not usable alone"
        if abs(kvC_se / kvC) > 0.05 else
        f"    C free LSQ over the hold: Kv {kvC:.0f} +/- {kvC_se:.0f} rpm/V, R {RC * 1000:.0f} mOhm,"
        f" condition no. {condC:.1f}")
    loss_extra = mt.P_elec_W - mt.P_shaft_apc_W - mt.I_A ** 2 * RB - i0 * mt.rpm_mean / KV_DS
    rep(f"    Power balance at datasheet constants: P_elec - P_shaft(APC) - I^2 R - I0 V_emf = {loss_extra:.0f} W"
        f" unaccounted (= {loss_extra / mt.I_A ** 2 * 1000:.0f} mOhm at {mt.I_A:.1f} A)")

    # 6. pack
    pre = st[(st.t_end_s < steady.t_start_s.min()) & (st.I_A < 0.3)]
    pk = pd.concat([pre[["I_A", "V_V"]], steady[["I_A", "V_V"]]])
    rpk, v0 = np.polyfit(pk.I_A, pk.V_V, 1)
    rpk = -rpk
    pk_res = pk.V_V - (v0 - rpk * pk.I_A)
    last = ft.iloc[-1]
    post = st[(st.t_start_s > float(c["ft_t_end_s"])) & (st.I_A < 1.0)]
    r_step = float("nan")
    rep(f"[6] Pack: resting before the run {pre.V_V.median():.2f} V at {pre.I_A.median():.2f} A"
        f" ({pre.V_V.median() / 4:.3f} V/cell) [fresh = 16.8 V]")
    rep(f"    V = {v0:.2f} - {rpk * 1000:.1f} mOhm x I over {len(pk)} steady points (rms {pk_res.std(ddof=2) * 1000:.0f} mV;"
        f" includes polarization during the ramp)")
    if not post.empty:
        p1 = post.iloc[0]
        r_step = (p1.V_V - last.V_V) / (last.I_A - p1.I_A)
        rep(f"    step at the throttle cut: {last.V_V:.2f} V @ {last.I_A:.2f} A -> {p1.V_V:.2f} V @ {p1.I_A:.2f} A"
            f" ({p1.t_start_s - last.t_end_s:.2f} s later) -> {r_step * 1000:.1f} mOhm; recovered to"
            f" {post.V_V.max():.2f} V by {post.t_end_s.max():.0f} s")

    # 7. droop over the hold
    f0, f1 = ft.iloc[0], ft.iloc[-1]
    rep(f"[7] Hold droop over {f1.t_end_s - f0.t_start_s:.1f} s: thrust {f1.T_g_mean / f0.T_g_mean:.3f},"
        f" rpm {f1.rpm_mean / f0.rpm_mean:.4f}, V {f1.V_V / f0.V_V:.4f}; rpm^2 alone predicts thrust"
        f" {(f1.rpm_mean / f0.rpm_mean) ** 2:.3f}")

    # 8. comparison with the model and SunnySky
    pred = HERE / "out" / "predict_x2820.csv"
    if pred.exists():
        pr = pd.read_csv(pred)
        row = pr[(pr.prop == prop) & (pr.n_live == 1)]
        if not row.empty:
            r0 = row.iloc[0]
            rep(f"[8] vs predict_x2820 (DA 1400 ft, V_oc 16.0, datasheet motor): {r0.rpm:.0f} rpm, {r0.I_per_motor_A} A,"
                f" {r0.V_batt_V} V, {r0.T_per_motor_g:.0f} g -> measured / model: rpm {mt.rpm_mean / r0.rpm:.3f},"
                f" I {mt.I_A / r0.I_per_motor_A:.3f}, V {mt.V_V / r0.V_batt_V:.3f}, T {mt.T_g_mean / r0.T_per_motor_g:.3f}")
    if prop in MFR_100:
        Im, Tm = MFR_100[prop]
        rep(f"    vs SunnySky 100 pct row ({Tm:.0f} gf at {Im} A, '14.8 V' nominal): measured / mfr T"
            f" {mt.T_g_mean / Tm:.3f}, I {mt.I_A / Im:.3f}; g/A measured {mt.T_g_mean / mt.I_A:.1f}, mfr {Tm / Im:.1f}")
    same_model = solve_ft(p, KV_DS, RB, I0_DS, 1.0, tf_m, v0, rpk, 1, rho)
    rep(f"    datasheet motor fed THIS pack fit (V0 {v0:.2f}, {rpk * 1000:.0f} mOhm) and this rho: {same_model['rpm']:.0f} rpm,"
        f" {same_model['I']:.1f} A, {same_model['V']:.2f} V -> measured rpm is {mt.rpm_mean / same_model['rpm']:.3f} of it")

    # 9. predictions
    fits = {"A": dict(kv=kvA, R=RA, kq=1.0), "B": dict(kv=kvB, R=RB, kq=kqB)}
    rows = []
    # fresh-pack bracket: pessimistic = low V0 with the ramp slope; optimistic = high V0 with the cut step
    packs = [("this pack", v0, rpk), (f"fresh {FRESH_V0[0]:.1f}/R ramp", FRESH_V0[0], rpk)]
    if np.isfinite(r_step):
        packs.append((f"fresh {FRESH_V0[1]:.1f}/R step", FRESH_V0[1], r_step))
    for fn, fp in fits.items():
        for pn in PREDICT_PROPS:
            pp = parse_apc(pn)
            for pack_name, pv0, prb in packs:
                for n_mot in (1, 2):
                    r = solve_ft(pp, fp["kv"], fp["R"], i0, fp["kq"], tf_m, pv0, prb, n_mot, rho)
                    rows.append(dict(fit=fn, prop=pn, pack=pack_name, V0=pv0, R_pack_mOhm=round(prb * 1000, 1),
                                     n_motors=n_mot, rpm=round(r["rpm"]), I_motor_A=round(r["I"], 1),
                                     I_pack_A=round(r["I"] * n_mot, 1), V_batt=round(r["V"], 2),
                                     T_motor_g=round(r["T_g"]), T_total_lbf=round(r["T_g"] * n_mot / 453.592, 2),
                                     pct_of_46A=round(100 * r["I"] / I_MAX)))
    pdf = pd.DataFrame(rows)
    pdf.to_csv(out / f"{args.run_id}_predict.csv", index=False)
    chk = pdf[(pdf.prop == prop) & (pdf.pack == "this pack") & (pdf.n_motors == 1)]
    rep("[9] Reproduction of this run (1 motor, this pack): " + "; ".join(
        f"fit {r.fit} {r.rpm} rpm {r.I_motor_A} A {r.T_motor_g} g" for r in chk.itertuples()) +
        f"  | measured {mt.rpm_mean:.0f} rpm {mt.I_A:.1f} A {mt.T_g_mean:.0f} g")
    rep("    Per-motor current and total thrust at full throttle, static, this rho (thrust x THRUST_FACTOR_meas):")
    rep("    fit prop    pack                   1 motor: rpm   A   pct46   g   | 2 motors: A/motor  pack A  V_batt  lbf total")
    for (fn, pn, pack_name), g in pdf.groupby(["fit", "prop", "pack"], sort=False):
        s1, s2 = g[g.n_motors == 1].iloc[0], g[g.n_motors == 2].iloc[0]
        rep(f"    {fn}   {pn:7s} {pack_name:21s}  {s1.rpm:6d} {s1.I_motor_A:5.1f} {s1.pct_of_46A:4d} {s1.T_motor_g:5d}"
            f"   |  {s2.I_motor_A:5.1f}  {s2.I_pack_A:6.1f}  {s2.V_batt:5.2f}  {s2.T_total_lbf:5.2f}")
    rep("    Separating A from B: no-prop rpm on this pack, fit A "
        f"{kvA * (v0 - RA * 1.2):.0f}, fit B {kvB * (v0 - RB * 1.2):.0f} (I0 about 1.2 A assumed) [INFERRED]")

    steady.to_csv(out / f"{args.run_id}_points.csv", index=False, float_format="%.5g")
    (out / f"{args.run_id}_summary.txt").write_text("\n".join(lines) + "\n", encoding="ascii")
    short = [ln for ln in lines if not ln.startswith("    ") or ln.startswith("    A ") or ln.startswith("    B ")
             or ln.startswith("    rho") or ln.startswith("    V =") or ln.startswith("    step")]
    print("\n".join(short))
    print(f"[OK] full report: {out / (args.run_id + '_summary.txt')}")


if __name__ == "__main__":
    main()
