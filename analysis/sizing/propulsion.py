"""
propulsion.py -- thrust vs airspeed for the two legal propulsion layouts, from APC PER3 data plus a
first-order motor + battery model.

Rules: 2 motors x 12 in prop or 4 motors x 9 in prop; sum of prop diameters per motor
[VERIFIED rules_2027 line 1577-1578; faq_395 line 36]. One 4S LiPo, <= 2200 mAh, no power limiter
[VERIFIED rules_2027 line 1574-1580]. Disk area: 2 x 12 in -> 226 in^2; 4 x 9 in -> 254 in^2.

Models
- Prop: APC PER3 tables (vortex-theory simulation, sea-level data, Ct/Cp vs J per RPM block)
  [VERIFIED file format reference/raw/apc_12x8e.dat lines 1-25]. Ct, Cp interpolated in (RPM, J);
  thrust/torque scale with density rho (Ct, Cp definitions).
- Motor (Drela first-order model, drela_motorprop): I = (V_motor - Omega/Kv)/Rm, Q = (I - I0)/Kv.
- Battery: linear sag, V_batt = V_oc - I_batt*R_batt. All motors identical, one pack.
- Kv is chosen per prop so the PEAK full-throttle battery current over 0-50 ft/s equals I_DESIGN.
  (A design choice: the team picks the motor Kv for the prop; exact products are not chosen here.)

Assumptions (all [UNVERIFIED] until thrust-stand tests):
  V_oc = 16.0 V at takeoff (fresh pack under load ~ 4.0 V/cell effective)
  R_batt = 0.025 ohm (pack ~0.020 + wiring/connectors 0.005)
  I_DESIGN = 90 A total peak (41C on 2.2 Ah; short bursts); sensitivity 70 and 110 A
  2-motor class: Rm 0.028 ohm, I0 1.8 A, ESC 0.003 ohm (e.g. 42xx-50xx outrunner, ~600 W)
  4-motor class: Rm 0.055 ohm, I0 1.0 A, ESC 0.005 ohm (e.g. 28xx-35xx outrunner, ~300 W)
  APC thin-electric RPM limit 150000/D(in)  [VERIFIED apc_rpm_limits line 28-30]

Run: python propulsion.py -> out/prop_candidates.csv, out/prop_thrust_curves.csv, out/prop_thrust_vs_V.png
"""
import os
import re
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from common import RAW, OUT, FPS_PER_MPH, N_PER_LBF, FT_PER_M, KG_PER_SLUGFT3, rho_from_da, save_csv

V_OC_TO = 16.0
V_OC_CRUISE = 15.2   # mid-flight effective open-circuit voltage (3.8 V/cell) [UNVERIFIED]
R_BATT = 0.025
I_DESIGN = 90.0
ETA_ESC_PART = 0.95  # ESC efficiency at part throttle [UNVERIFIED]
DA_DESIGN_KV = 1400.0  # DA at which Kv is matched (site median, see density_altitude.py)

MOTOR_CLASS = {
    2: dict(Rm=0.028, I0=1.8, Resc=0.003, m_motor_lb=0.42, m_esc_lb=0.14, m_prop_lb=0.08, m_mount_lb=0.10),
    4: dict(Rm=0.055, I0=1.0, Resc=0.005, m_motor_lb=0.24, m_esc_lb=0.07, m_prop_lb=0.04, m_mount_lb=0.08),
}

PROPS = {2: ["12x6e", "12x8e", "12x10e", "12x12e", "11x7e", "11x10e"],
         4: ["9x45e", "9x6e", "9x75e"]}


def parse_apc(name):
    """Return dict(D_m, rpm[], J[list], Ct[list], Cp[list]) from reference/raw/apc_<name>.dat."""
    path = os.path.join(RAW, f"apc_{name}.dat")
    txt = open(path, encoding="latin-1").read().splitlines()
    m = re.match(r"\s*([\d.]+)x", txt[0])
    D_in = float(m.group(1))
    blocks, cur, rpm = [], None, None
    for line in txt:
        if "PROP RPM" in line:
            if cur:
                blocks.append((rpm, np.array(cur)))
            rpm = float(line.split("=")[1])
            cur = []
            continue
        if cur is None:
            continue
        parts = line.split()
        if len(parts) == 15:
            try:
                cur.append([float(p) for p in parts])
            except ValueError:
                pass
    if cur:
        blocks.append((rpm, np.array(cur)))
    rpms = np.array([b[0] for b in blocks])
    J = [b[1][:, 1] for b in blocks]
    Ct = [b[1][:, 3] for b in blocks]
    Cp = [b[1][:, 4] for b in blocks]
    return dict(name=name, D_in=D_in, D_m=D_in * 0.0254, rpm=rpms, J=J, Ct=Ct, Cp=Cp,
                rpm_limit=150000.0 / D_in)


def coeffs(p, rpm, J):
    """Ct, Cp at (rpm, J): linear in J within each block, linear in rpm between blocks."""
    r = np.clip(rpm, p["rpm"][0], p["rpm"][-1])
    i = int(np.clip(np.searchsorted(p["rpm"], r) - 1, 0, len(p["rpm"]) - 2))
    w = (r - p["rpm"][i]) / (p["rpm"][i + 1] - p["rpm"][i])
    out = []
    for k in (i, i + 1):
        out.append((np.interp(J, p["J"][k], p["Ct"][k]), np.interp(J, p["J"][k], p["Cp"][k])))
    ct = (1 - w) * out[0][0] + w * out[1][0]
    cp = (1 - w) * out[0][1] + w * out[1][1]
    return ct, cp


class PropSystem:
    """n_motors identical motor+prop units on one 4S pack."""

    def __init__(self, n_motors, prop_name, i_design=I_DESIGN, kv=None, motor=None,
                 v_oc=V_OC_TO, r_batt=R_BATT, da_match=DA_DESIGN_KV):
        self.n = n_motors
        self.p = parse_apc(prop_name)
        self.m = dict(MOTOR_CLASS[n_motors]) if motor is None else motor
        self.v_oc, self.r_b = v_oc, r_batt
        self.i_design = i_design
        self.kv = kv if kv is not None else self.match_kv(i_design, rho_from_da(da_match) * KG_PER_SLUGFT3)

    # --- core solve (SI inside) ---
    def _q_prop(self, omega, V, rho):
        n = omega / (2 * np.pi)
        J = V / (n * self.p["D_m"]) if n > 0 else 0.0
        ct, cp = coeffs(self.p, n * 60.0, J)
        D = self.p["D_m"]
        T = ct * rho * n ** 2 * D ** 4
        P = cp * rho * n ** 3 * D ** 5
        return P / omega, T, P, J

    def full_throttle(self, V_ms, rho_si, kv=None, v_oc=None):
        """Per-aircraft totals at full throttle: thrust N, battery current A, rpm, V_batt, shaft W."""
        kv = self.kv if kv is None else kv
        v_oc = self.v_oc if v_oc is None else v_oc
        kv_si = kv * 2 * np.pi / 60.0
        Rtot = self.m["Rm"] + self.m["Resc"] + self.n * self.r_b

        def f(om):
            I = (v_oc - om / kv_si) / Rtot
            return (I - self.m["I0"]) / kv_si - self._q_prop(om, V_ms, rho_si)[0]

        om_max = kv_si * v_oc * 0.999
        om = brentq(f, 50.0, om_max, xtol=1e-3)
        I = (v_oc - om / kv_si) / Rtot
        _, T, P, J = self._q_prop(om, V_ms, rho_si)
        return dict(T_N=self.n * T, I_A=self.n * I, rpm=om * 60 / (2 * np.pi),
                    V_batt=v_oc - self.n * I * self.r_b, P_shaft_W=self.n * P, J=J)

    def match_kv(self, i_total, rho_si):
        """Kv such that the PEAK full-throttle battery current over the takeoff speed range
        (0-50 ft/s) equals i_total. APC Cp rises with J at low J, so the peak is not at V=0."""
        vs = np.array([0.0, 10.0, 20.0, 30.0, 40.0, 50.0]) / FT_PER_M
        g = lambda kv: max(self.full_throttle(v, rho_si, kv=kv)["I_A"] for v in vs) - i_total
        return brentq(g, 150.0, 5000.0, xtol=0.5)

    def part_throttle_current(self, T_total_N, V_ms, rho_si, v_oc=V_OC_CRUISE):
        """Battery current (A) to produce total thrust T at speed V. NaN if above full throttle."""
        D = self.p["D_m"]
        T1 = T_total_N / self.n
        kv_si = self.kv * 2 * np.pi / 60.0

        def thr(rpm):
            n = rpm / 60.0
            ct, _ = coeffs(self.p, rpm, V_ms / (n * D))
            return ct * rho_si * n ** 2 * D ** 4 - T1

        lo, hi = 800.0, min(self.kv * v_oc, self.p["rpm"][-1])
        if thr(hi) < 0:
            return np.nan
        if thr(lo) > 0:
            lo = 300.0
        rpm = brentq(thr, lo, hi, xtol=0.5)
        om = rpm * 2 * np.pi / 60.0
        Q, _, P, _ = self._q_prop(om, V_ms, rho_si)
        I_m = Q * kv_si + self.m["I0"]
        V_m = om / kv_si + I_m * (self.m["Rm"] + self.m["Resc"])
        P_in = self.n * V_m * I_m / ETA_ESC_PART
        disc = v_oc ** 2 - 4 * self.r_b * P_in
        if disc < 0:
            return np.nan
        I_b = (v_oc - np.sqrt(disc)) / (2 * self.r_b)
        V_b = v_oc - I_b * self.r_b
        if V_m > V_b:  # would need more than 100% duty
            return np.nan
        return I_b

    # --- US-unit helpers used by takeoff/sweep ---
    def thrust_curve(self, da_ft, V_fps):
        rho = rho_from_da(da_ft) * KG_PER_SLUGFT3
        T, I = [], []
        for v in np.atleast_1d(V_fps):
            r = self.full_throttle(v / FT_PER_M, rho)
            T.append(r["T_N"] / N_PER_LBF)
            I.append(r["I_A"])
        return np.array(T), np.array(I)

    def mass_lb(self):
        m = self.m
        wiring = 0.20 if self.n == 2 else 0.35  # [UNVERIFIED]
        return self.n * (m["m_motor_lb"] + m["m_esc_lb"] + m["m_prop_lb"] + m["m_mount_lb"]) + wiring


def main():
    rows, curves = [], []
    V_fps = np.arange(0.0, 90.1, 2.0)
    for n, props in PROPS.items():
        for pn in props:
            for idz in (70.0, 90.0, 110.0):
                ps = PropSystem(n, pn, i_design=idz)
                T, I = ps.thrust_curve(DA_DESIGN_KV, V_fps)
                rho = rho_from_da(DA_DESIGN_KV) * KG_PER_SLUGFT3
                st = ps.full_throttle(0.0, rho)
                rows.append(dict(n_motors=n, prop=pn, I_design_A=idz, Kv=ps.kv, rpm_static=st["rpm"],
                                 rpm_limit=ps.p["rpm_limit"], V_batt_static=st["V_batt"],
                                 P_shaft_static_W=st["P_shaft_W"], P_elec_static_W=st["V_batt"] * st["I_A"],
                                 T0_lbf=T[0], T20_lbf=np.interp(20, V_fps, T), T30_lbf=np.interp(30, V_fps, T),
                                 T40_lbf=np.interp(40, V_fps, T), T50_lbf=np.interp(50, V_fps, T),
                                 T60_lbf=np.interp(60, V_fps, T), I40_A=np.interp(40, V_fps, I),
                                 prop_mass_group_lb=ps.mass_lb()))
                if idz == 90.0:
                    for v, t, i in zip(V_fps, T, I):
                        curves.append(dict(n_motors=n, prop=pn, V_fps=v, T_lbf=t, I_A=i))
    df = pd.DataFrame(rows)
    save_csv(df, "prop_candidates.csv")
    save_csv(pd.DataFrame(curves), "prop_thrust_curves.csv")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    cv = pd.DataFrame(curves)
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for (n, pn), d in cv.groupby(["n_motors", "prop"]):
        ls = "-" if n == 2 else "--"
        ax[0].plot(d.V_fps, d.T_lbf, ls, label=f"{n}x {pn}")
        ax[1].plot(d.V_fps, d.I_A, ls, label=f"{n}x {pn}")
    ax[0].set_ylabel("Total thrust, full throttle (lbf)")
    ax[1].set_ylabel("Battery current (A)")
    for a in ax:
        a.set_xlabel("Airspeed (ft/s)")
        a.grid(alpha=0.3)
        a.legend(fontsize=7)
    ax[0].set_title(f"DA {DA_DESIGN_KV:.0f} ft, Kv matched to {I_DESIGN:.0f} A peak")
    fig.tight_layout()
    fig.savefig(f"{OUT}/prop_thrust_vs_V.png", dpi=120)

    d90 = df[df.I_design_A == 90.0]
    print(f"Full-throttle totals at DA {DA_DESIGN_KV:.0f} ft, Kv matched to 90 A peak over 0-50 ft/s (see prop_candidates.csv)")
    print(" n prop     Kv   rpm0  rpmLim  Pshaft0   T0    T30   T40   T50   T60  I40  massgrp")
    for _, r in d90.iterrows():
        print(f" {r.n_motors:d} {r.prop:7s} {r.Kv:5.0f} {r.rpm_static:6.0f} {r.rpm_limit:6.0f} {r.P_shaft_static_W:7.0f} "
              f"{r.T0_lbf:5.2f} {r.T30_lbf:5.2f} {r.T40_lbf:5.2f} {r.T50_lbf:5.2f} {r.T60_lbf:5.2f} {r.I40_A:4.0f} "
              f"{r.prop_mass_group_lb:5.2f}")


if __name__ == "__main__":
    main()
