"""
takeoff.py -- 100 ft takeoff model -> maximum takeoff weight (lb) for a geometry and propulsion option.

Rule: Regular Class aircraft shall be airborne within 100 ft, full use of the runway before that is
not allowed (100 ft limit) [VERIFIED rules_2027 lines 1010-1015]. Runway paved [INFERRED from
rules_2027 line 1034 "the paved runway"].

Model (point mass, zero wind unless stated):
  ground roll: m dV/dt = T(V) - D - mu_r (W - L),  L = q S CL_g,  D = q S CD(CL_g, in ground effect)
  rotation at V_R = k_R * V_stall (trimmed, clean CLmax), then a rotation segment of t_R seconds at
  V_R before the wheels leave (distance V_R * t_R; conservative: no extra acceleration counted).
  S_TO = S_ground(0 -> V_R) + V_R * t_R  <= 100 ft
Thrust: propulsion.PropSystem full-throttle T(V) at the day's density x THRUST_FACTOR.
Nominal assumptions [INFERRED/UNVERIFIED]: mu_r 0.04 (paved, Raymer 0.03-0.05), CL_g 0.9 (wing
incidence ~2 deg on a tricycle), k_R 1.10, t_R 0.3 s, THRUST_FACTOR 0.93 (APC PER3 data and the
motor model are not yet validated by a thrust stand).

Run: python takeoff.py -> out/takeoff_prop_ranking.csv, out/takeoff_wto_grid.csv,
     out/takeoff_sensitivity.csv, out/takeoff_summary.txt, out/takeoff_wto_vs_S.png
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from common import OUT, G, rho_from_da, save_csv, TO_DIST_FT
from propulsion import PropSystem, PROPS
from aero import Geometry

MU_R = 0.04
CL_G = 0.9
K_R = 1.10
T_R = 0.3
THRUST_FACTOR = 0.93
DA_DESIGN = 2000.0     # ~P90 of March KLAL daytime DA (1975 ft, density_altitude.py)
I_DESIGN = 90.0


class ThrustModel:
    """Full-throttle total thrust T(V) (lbf), tabulated per DA and interpolated."""
    V_GRID = np.arange(0.0, 90.1, 3.0)

    def __init__(self, n_motors, prop, i_design=I_DESIGN, factor=THRUST_FACTOR):
        self.ps = PropSystem(n_motors, prop, i_design=i_design)
        self.n, self.prop, self.factor = n_motors, prop, factor
        self._tab = {}

    def table(self, da):
        key = round(float(da), 1)
        if key not in self._tab:
            T, I = self.ps.thrust_curve(key, self.V_GRID)
            self._tab[key] = (T, I)
        return self._tab[key]

    def T(self, V, da):
        return self.factor * np.interp(V, self.V_GRID, self.table(da)[0])

    def label(self):
        return f"{self.n}x{self.prop}"


def vstall(g, W, rho, clmax=None):
    cl = g.clmax_trimmed() if clmax is None else clmax
    return np.sqrt(2 * W / (rho * g.S * cl))


def takeoff_distance(g, W, thr, da, mu_r=MU_R, CL_g=CL_G, k_R=K_R, t_R=T_R, V_wind=0.0, clmax=None,
                     n_steps=120, detail=False):
    rho = float(rho_from_da(da))
    Vs = vstall(g, W, rho, clmax)
    V_R = k_R * Vs
    Va = np.linspace(V_wind, V_R, n_steps)                     # airspeed
    Vg = Va - V_wind                                           # ground speed
    q = 0.5 * rho * Va ** 2
    # CD in ground effect at CL_g; the profile/CD0 Re-dependence evaluated at 0.7 V_R (weak) [INFERRED]
    CD = g.drag_coeff(CL_g, rho, max(0.7 * V_R, 10.0), in_ground=True)
    L = q * g.S * CL_g
    D = q * g.S * CD
    F = thr.T(Va, da) - D - mu_r * np.maximum(W - L, 0.0)
    if np.any(F <= 0):
        return (np.inf, None) if detail else np.inf
    a = G * F / W
    integrand = Vg / a
    S_G = float(np.sum(0.5 * (integrand[1:] + integrand[:-1]) * np.diff(Vg)))
    t_G = float(np.sum(0.5 * (1 / a[1:] + 1 / a[:-1]) * np.diff(Vg)))
    S = S_G + (V_R - V_wind) * t_R
    if detail:
        return S, dict(S_ground=S_G, t_ground=t_G, V_stall=Vs, V_R=V_R, CD_g=CD, T0=float(thr.T(0.0, da)),
                       T_R=float(thr.T(V_R, da)), rho=rho)
    return S


def wto_max(g, thr, da, s_avail=TO_DIST_FT, **kw):
    f = lambda W: takeoff_distance(g, W, thr, da, **kw) - s_avail
    lo, hi = 3.0, 120.0
    if f(lo) > 0:
        return 0.0
    while np.isinf(f(hi)) or f(hi) < 0:
        hi *= 0.8 if np.isinf(f(hi)) else 1.2
        if hi < lo * 1.01:
            return lo
        if hi > 400:
            return hi
    # f may be inf above some W (thrust < drag + friction): brentq needs finite ends
    while np.isinf(f(hi)):
        hi = 0.5 * (lo + hi)
    return brentq(f, lo, hi, xtol=0.01)


def main():
    lines = []
    ref = dict(span_in=95, chord_in=20, n_slots=5)
    # --- (a) prop ranking on the reference geometry at the design DA
    rows = []
    thr_models = {}
    for n, props in PROPS.items():
        for p in props:
            for idz in (70.0, 90.0, 110.0):
                th = ThrustModel(n, p, i_design=idz)
                g = Geometry(ref["span_in"], ref["chord_in"], ref["n_slots"], n, "s1223")
                W = wto_max(g, th, DA_DESIGN)
                S, d = takeoff_distance(g, W, th, DA_DESIGN, detail=True)
                rows.append(dict(n_motors=n, prop=p, I_design_A=idz, Kv=th.ps.kv, WTO_max_lb=W, V_R_fps=d["V_R"],
                                 T0_lbf=d["T0"], T_VR_lbf=d["T_R"], t_ground_s=d["t_ground"]))
                if idz == I_DESIGN:
                    thr_models[(n, p)] = th
    pr = pd.DataFrame(rows)
    save_csv(pr, "takeoff_prop_ranking.csv")
    p90 = pr[pr.I_design_A == I_DESIGN].sort_values("WTO_max_lb", ascending=False)
    best = {n: p90[p90.n_motors == n].iloc[0].prop for n in (2, 4)}
    lines.append(f"Prop ranking, ref 95x20 in S1223 5 slots, DA {DA_DESIGN:.0f} ft, 90 A peak, thrust x{THRUST_FACTOR}:")
    for _, r in p90.iterrows():
        lines.append(f"  {r.n_motors}x{r.prop:6s} Kv {r.Kv:4.0f}  W_TO_max {r.WTO_max_lb:5.1f} lb  V_R {r.V_R_fps:4.1f} ft/s "
                     f"T0 {r.T0_lbf:5.2f} T(V_R) {r.T_VR_lbf:5.2f}")
    for idz in (70.0, 110.0):
        d = pr[pr.I_design_A == idz].sort_values("WTO_max_lb", ascending=False).iloc[0]
        lines.append(f"  (I_peak {idz:.0f} A: best {d.n_motors}x{d.prop} W_TO_max {d.WTO_max_lb:.1f} lb)")

    # --- (b) W_TO_max vs wing area and CLmax (span 95 in; chord varies), both options
    grid = []
    for n in (2, 4):
        th = thr_models[(n, best[n])]
        for chord in (14, 16, 18, 20, 22, 24, 26):
            g = Geometry(95, chord, 5, n, "s1223")
            cl0 = g.clmax_trimmed()
            for fac in (0.8, 0.9, 1.0, 1.1):
                W = wto_max(g, th, DA_DESIGN, clmax=cl0 * fac)
                grid.append(dict(n_motors=n, prop=best[n], span_in=95, chord_in=chord, S_ft2=g.S, AR=g.AR,
                                 CLmax_trim=cl0 * fac, clmax_factor=fac, WTO_max_lb=W))
    gd = pd.DataFrame(grid)
    save_csv(gd, "takeoff_wto_grid.csv")
    lines.append(f"W_TO_max (lb) vs S at DA {DA_DESIGN:.0f} ft, span 95 in, nominal CLmax (S1223 trimmed):")
    for n in (2, 4):
        d = gd[(gd.n_motors == n) & (gd.clmax_factor == 1.0)]
        lines.append(f"  {n}x{best[n]}: " + ", ".join(f"S {r.S_ft2:4.1f}->{r.WTO_max_lb:4.1f}" for _, r in d.iterrows()))

    # --- (c) sensitivities on the reference geometry, best 2-motor prop
    th = thr_models[(2, best[2])]
    g = Geometry(ref["span_in"], ref["chord_in"], ref["n_slots"], 2, "s1223")
    base = wto_max(g, th, DA_DESIGN)
    cases = [("nominal", {}), ("k_R 1.20", dict(k_R=1.2)), ("t_R 0", dict(t_R=0.0)), ("t_R 0.5 s", dict(t_R=0.5)),
             ("mu_r 0.03", dict(mu_r=0.03)), ("mu_r 0.06", dict(mu_r=0.06)), ("CL_g 0.5", dict(CL_g=0.5)),
             ("CL_g 1.2", dict(CL_g=1.2)), ("headwind 5 kt", dict(V_wind=5 * 1.68781)),
             ("headwind 8 kt", dict(V_wind=8 * 1.68781)), ("s_avail 90 ft", dict(s_avail=90.0)),
             ("CLmax -10%", dict(clmax=0.9 * g.clmax_trimmed()))]
    sens = []
    for name, kw in cases:
        W = wto_max(g, th, DA_DESIGN, **kw)
        sens.append(dict(case=name, WTO_max_lb=W, delta_lb=W - base))
    for name, fac in (("thrust x1.00", 1.0), ("thrust x0.85", 0.85)):
        th2 = ThrustModel(2, best[2], factor=fac)
        W = wto_max(g, th2, DA_DESIGN)
        sens.append(dict(case=name, WTO_max_lb=W, delta_lb=W - base))
    for da in (-1000.0, 0.0, 1000.0, 1400.0, 2500.0, 3000.0):
        W = wto_max(g, th, da)
        sens.append(dict(case=f"DA {da:.0f} ft", WTO_max_lb=W, delta_lb=W - base))
    sd = pd.DataFrame(sens)
    save_csv(sd, "takeoff_sensitivity.csv")
    lines.append(f"Sensitivity, ref 95x20 in, 2x{best[2]}, DA {DA_DESIGN:.0f}: nominal W_TO_max {base:.1f} lb")
    lines.append("  " + "; ".join(f"{r.case} {r.delta_lb:+.1f}" for _, r in sd.iloc[1:].iterrows()))
    with open(os.path.join(OUT, "takeoff_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for n, ls in ((2, "-"), (4, "--")):
        for fac, col in ((0.8, "C3"), (0.9, "C1"), (1.0, "C0"), (1.1, "C2")):
            d = gd[(gd.n_motors == n) & (gd.clmax_factor == fac)]
            ax.plot(d.S_ft2, d.WTO_max_lb, ls, color=col, label=f"{n}x{best[n]}, CLmax x{fac}")
    ax.set_xlabel("Wing area (ft^2), span 95 in")
    ax.set_ylabel("Max takeoff weight in 100 ft (lb)")
    ax.set_title(f"DA {DA_DESIGN:.0f} ft, thrust x{THRUST_FACTOR}, k_R {K_R}, mu {MU_R}")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "takeoff_wto_vs_S.png"), dpi=120)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
