"""
aero.py -- aerodynamic model used by takeoff.py and sweep.py.

Contents
- DESIGN_CLMAX_2D: 2-D clmax used for design (wind-tunnel value where the library has one, else
  NeuralFoil x 0.93). NeuralFoil is optimistic near stall compared with the UIUC tunnel data:
    S1223      NF 2.25 @Re200k  vs  2.11 (LSAT vol2 Table 4.13, uiuc_lsat_vol2 line 2221) and 2.23
               (selig_guglielmo_1997 line 267). Design 2.10.                         [VERIFIED data]
    S1223RTL   NF 2.33-2.35     vs  "near 2.05" (uiuc_lsat_vol2 line 1887). Design 2.05. [VERIFIED]
    E423       NF 2.04          vs  "nearly 2.0" @200k, "slightly less" @300k (uiuc_lsat_vol2 1907-1909). Design 1.95.
    FX74-CL5-140 MOD NF 2.2-2.3 vs  "near 2.0" @200k (uiuc_lsat_vol1 line 2474). Design 2.00.
    CH10sm, S1210, SD7062: NeuralFoil(Re 250k) x 0.93 (the S1223 ratio 2.10/2.25)   [INFERRED]
- lifting_line(): Glauert monoplane-equation solution for a straight untwisted trapezoidal wing:
  span efficiency e_inv and eta_max = max(local cl / CL) (critical-section CLmax method).
- Geometry(): wing, fuselage sized from the bottle bay, tail sized by tail volume coefficients.
- cd0_nonwing(): component build-up (Raymer/Nicolai form: CD = FF*Cf*Swet/S; gear 1.01 on frontal
  area per strut+wheel [VERIFIED nicolai_rc_model_aero line 309-312]).
- drag_coeff(): CD = CD0_nonwing + k_rough*cd_wing(CL, Re) + phi_ge*CL^2/(pi*e*AR).

Units: ft, lbf, slug, s. Angles in degrees unless noted.
"""
import os
import numpy as np
import pandas as pd
from common import OUT, SLOT_DIA_IN, SLOT_LEN_IN, mu_air

# ---------------------------------------------------------------- airfoil data
_POL = None


def polars():
    global _POL
    if _POL is None:
        _POL = pd.read_csv(os.path.join(OUT, "airfoil_polars.csv"))
    return _POL


_NF_RATIO = 2.10 / 2.25   # S1223 tunnel/NeuralFoil ratio used for airfoils without tunnel data
DESIGN_CLMAX_2D = {"s1223": 2.10, "s1223rtl": 2.05, "e423": 1.95, "fx74cl5140": 2.00,
                   "ch10sm": 2.086 * _NF_RATIO, "s1210": 1.927 * _NF_RATIO, "sd7062": 1.586 * _NF_RATIO}
K_ROUGH = 1.10    # built-up film-covered wing profile drag factor on NeuralFoil cd  [UNVERIFIED]


class WingSection:
    """Profile drag cd(cl, Re) and cm0 from the NeuralFoil polars (attached branch only)."""

    def __init__(self, name):
        self.name = name
        P = polars()
        self.res = sorted(P[P.airfoil == name].Re.unique())
        self.branch = {}
        for Re in self.res:
            d = P[(P.airfoil == name) & (P.Re == Re)].sort_values("alpha")
            cl = d.CL.values
            i = int(np.argmax(cl))
            # first local maximum (same rule as airfoils.py)
            for k in range(1, len(cl) - 1):
                if cl[k] >= cl[k - 1] and cl[k] > cl[k + 1] and d.alpha.values[k] > 4.0:
                    i = k
                    break
            a = d.iloc[: i + 1]
            a = a[a.CL > -0.2]
            self.branch[Re] = (a.CL.values, a.CD.values, a.alpha.values, float(np.interp(0.0, d.alpha, d.CM)))
        self.clmax_design = DESIGN_CLMAX_2D[name]

    def _at(self, Re, cl):
        c, d, al, _ = self.branch[Re]
        cl = np.clip(cl, c.min(), c.max())
        return np.interp(cl, c, d)

    def cd(self, cl, Re):
        Re = float(np.clip(Re, self.res[0], self.res[-1]))
        j = int(np.clip(np.searchsorted(self.res, Re) - 1, 0, len(self.res) - 2))
        w = (Re - self.res[j]) / (self.res[j + 1] - self.res[j])
        return (1 - w) * self._at(self.res[j], cl) + w * self._at(self.res[j + 1], cl)

    def cm0(self):
        return self.branch[self.res[len(self.res) // 2]][3]


# ---------------------------------------------------------------- lifting line
def lifting_line(AR, taper=1.0, a0=2 * np.pi * 0.95, n_terms=31):
    """Straight, untwisted trapezoidal wing. Returns (e_inv, eta_max, CL_alpha per rad).
    Monoplane equation with odd sine terms, collocation on 0 < theta <= pi/2."""
    N = n_terms
    th = np.arange(1, N + 1) * (np.pi / 2) / N   # theta in (0, pi/2]; y = cos(theta)
    n = 2 * np.arange(N) + 1
    y = np.cos(th)                      # y / (b/2), 0 at root
    c_rel = (1 - (1 - taper) * np.abs(y))  # chord / root chord
    b_over_cr = AR * (1 + taper) / 2.0    # b / c_root for a trapezoid
    mu = c_rel * a0 / (4.0 * b_over_cr)
    M = np.sin(np.outer(th, n)) * (mu[:, None] * n[None, :] + np.sin(th)[:, None])
    rhs = mu * np.sin(th) * 1.0          # alpha = 1 rad (all linear, geometric twist 0)
    A = np.linalg.solve(M, rhs)
    CL = np.pi * AR * A[0]
    delta = np.sum(n[1:] * (A[1:] / A[0]) ** 2)
    e_inv = 1.0 / (1.0 + delta)
    cl_loc = 4.0 * b_over_cr * (np.sin(np.outer(th, n)) @ A) / c_rel
    eta = cl_loc / CL
    return e_inv, float(eta.max()), CL


# ---------------------------------------------------------------- geometry
class Geometry:
    """Conceptual layout. Wing: rectangular (taper 1) unless given. Fuselage: box around a
    bottle bay; bottles lie across the fuselage (axis spanwise) in one fore-aft row when
    n_slots <= 6 (smallest wetted area of the layouts tried), otherwise two stacked layers.
    [INFERRED layouts]
    Tail: conventional, V_H and V_V constant, tail arm l_t = 3.0*c limited to 36-72 in."""

    V_H, V_V = 0.55, 0.045        # higher V_H than usual because of the S1223's large -Cm [INFERRED]
    H_WING_FT = 1.0               # wing height above ground for ground effect [INFERRED]

    def __init__(self, span_in, chord_in, n_slots, n_motors=2, airfoil="s1223", taper=1.0):
        self.b_in, self.c_in, self.ns, self.nm, self.af, self.taper = span_in, chord_in, n_slots, n_motors, airfoil, taper
        self.b = span_in / 12.0
        self.c = chord_in / 12.0                      # mean chord (= MAC for rectangular)
        self.S = self.b * self.c
        self.AR = self.b ** 2 / self.S
        # bottle bay [INFERRED layout; slot envelope from common.py, UNVERIFIED until bottles measured]
        wall = 0.5
        self.layers = 1 if n_slots <= 6 else 2
        self.bay_w = SLOT_LEN_IN + wall
        self.bay_l = int(np.ceil(n_slots / self.layers)) * (SLOT_DIA_IN + 0.2) + wall
        self.bay_h = self.layers * SLOT_DIA_IN + 1.0
        self.fus_l_in = self.bay_l + 16.0             # 6 in nose fairing + 10 in aft taper
        # tail
        self.lt_in = float(np.clip(3.0 * chord_in, 36.0, 72.0))
        self.lt = self.lt_in / 12.0
        self.Sh = self.V_H * self.S * self.c / self.lt
        self.Sv = self.V_V * self.S * self.b / self.lt
        self.length_in = self.lt_in + 0.25 * chord_in + 6.0 + 0.75 * np.sqrt(self.Sh * 144 / 4.0)  # rough overall length
        self.e_inv, self.eta_max, self.CLa_rad = lifting_line(self.AR, taper)
        self.section = WingSection(airfoil)

    # wetted areas (ft^2)
    def swet_fus(self):
        w, h, L = self.bay_w / 12, self.bay_h / 12, self.fus_l_in / 12
        return 2 * (w + h) * L * 0.85 + w * h         # tapered ends -> 0.85 factor [INFERRED]

    def cd0_nonwing(self, rho, V):
        mu = mu_air()
        S = self.S
        cf_t = lambda Re: 0.455 / np.log10(max(Re, 1e4)) ** 2.58          # turbulent flat plate
        cf_l = lambda Re: 1.328 / np.sqrt(max(Re, 1e4))                     # laminar flat plate
        # fuselage (turbulent, boxy -> Q 1.2) [INFERRED]
        L = self.fus_l_in / 12
        d_eq = np.sqrt(4 * (self.bay_w / 12) * (self.bay_h / 12) / np.pi)
        f = L / d_eq
        FF = 1 + 60 / f ** 3 + f / 400
        cd_f = 1.2 * FF * cf_t(rho * V * L / mu) * self.swet_fus() / S
        # tail boom: ~1 in wood box or aluminum tube, fuselage end to tail. NOT carbon: FRP is banned except
        # commercial motor mounts, props, gear, linkages [VERIFIED rules_2027 lines 1557-1560]
        l_boom = max(self.lt - 0.5 * L, 0.5)
        cd_boom = 1.05 * cf_t(rho * V * (L + l_boom) / mu) * (np.pi * (1 / 12) * l_boom) / S
        # tails: t/c 0.09, FF 1.2, mixed laminar/turbulent Cf = mean(lam, turb) [INFERRED]
        ct = np.sqrt(self.Sh / 4.0)                                          # tail chord, AR 4
        cf_tail = 0.5 * (cf_l(rho * V * ct / mu) + cf_t(rho * V * ct / mu))
        cd_tail = 1.2 * 1.05 * cf_tail * 2.04 * (self.Sh + self.Sv) / S
        # landing gear: tricycle, 3 struts+wheels, 1.01 on ~4 in^2 frontal each [nicolai line 309-312 / INFERRED area]
        cd_gear = 3 * 1.01 * (4.0 / 144) / S
        # motor nacelles: CD 0.34 on frontal area [nicolai line 314-316]; 2.5 in dia (2-motor), 2.0 in (4-motor)
        dn = 2.5 if self.nm == 2 else 2.0
        cd_nac = self.nm * 0.34 * (np.pi * dn ** 2 / 4 / 144) / S
        tot = cd_f + cd_boom + cd_tail + cd_gear + cd_nac
        return 1.10 * tot, dict(fus=cd_f, boom=cd_boom, tail=cd_tail, gear=cd_gear, nac=cd_nac)  # +10% misc

    def reynolds(self, rho, V):
        return rho * V * self.c / mu_air()

    def e_total(self):
        return 0.95 * self.e_inv       # fuselage / nacelle interference [INFERRED]

    def phi_ground(self):
        r = (16 * self.H_WING_FT / self.b) ** 2
        return r / (1 + r)             # McCormick ground-effect factor on induced drag [INFERRED standard]

    def drag_coeff(self, CL, rho, V, in_ground=False):
        cd0, _ = self.cd0_nonwing(rho, V)
        cdp = K_ROUGH * self.section.cd(CL, self.reynolds(rho, V))
        k = (self.phi_ground() if in_ground else 1.0) / (np.pi * self.e_total() * self.AR)
        return cd0 + cdp + k * CL ** 2

    # ------------------------------------------------ CLmax
    def clmax_wing(self):
        """Critical-section method: CLmax_wing = clmax_2D / eta_max; fuselage centre-section loss
        (1 - 0.3*w_fus/b) for a wing mounted on top of the fuselage [INFERRED]."""
        return self.section.clmax_design / self.eta_max * (1 - 0.3 * (self.bay_w / 12) / self.b)

    def trim(self, CL_w, sm=0.12):
        """Tail lift (as dCL on wing area) to trim at CL_w. Wing Cm0 3-D = cm0_2D*AR/(AR+2)
        (Raymer, straight wing) [INFERRED]; neutral point from x_np = 0.25 + 0.9*V_H*(a_t/a_w)*(1-deps)
        - 0.05 (fuselage) [INFERRED]; CG at x_np - sm."""
        cm0 = self.section.cm0() * self.AR / (self.AR + 2)
        a_w = self.CLa_rad
        a_t = 2 * np.pi * 4 / (4 + 2)  # tail AR 4
        deps = 2 * a_w / (np.pi * self.AR)
        x_np = 0.25 + 0.9 * self.V_H * (a_t / a_w) * (1 - deps) - 0.05
        x_cg = x_np - sm
        dCL_t = (CL_w * (x_cg - 0.25) + cm0) / (self.lt / self.c)
        return dCL_t, x_np, x_cg, cm0

    def clmax_trimmed(self):
        clw = self.clmax_wing()
        dcl, *_ = self.trim(clw)
        return clw + dcl


def main():
    """Print a small table of lifting-line results and one example drag breakdown."""
    lines = ["Lifting line (straight, untwisted), a0 = 0.95*2pi:"]
    lines.append("  AR  taper  e_inv  eta_max  CLa/rad")
    rows = []
    for AR in (4, 5, 6, 7, 8):
        for tp in (1.0, 0.7, 0.5):
            e, eta, cla = lifting_line(AR, tp)
            rows.append(dict(AR=AR, taper=tp, e_inv=e, eta_max=eta, CLa_rad=cla))
            if tp in (1.0, 0.5):
                lines.append(f"  {AR:2d}  {tp:4.1f}  {e:5.3f}  {eta:6.3f}  {cla:6.3f}")
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "lifting_line_table.csv"), index=False, float_format="%.4g")
    g = Geometry(94, 20, 5, 2, "s1223")
    rho, V = 0.00224, 55.0
    cd0, parts = g.cd0_nonwing(rho, V)
    lines.append(f"Example 94 x 20 in, 5 slots, S {g.S:.2f} ft2, AR {g.AR:.2f}: CD0 non-wing {cd0:.4f} "
                 + ", ".join(f"{k} {v:.4f}" for k, v in parts.items()))
    lines.append(f"  Sh {g.Sh:.2f} ft2, Sv {g.Sv:.2f} ft2, l_t {g.lt_in:.0f} in, bay {g.bay_l:.1f} x {g.bay_w:.1f} in, "
                 f"fus {g.fus_l_in:.0f} in, overall ~{g.length_in:.0f} in")
    clw = g.clmax_wing()
    dcl, xnp, xcg, cm0 = g.trim(clw)
    lines.append(f"  CLmax wing {clw:.3f}, trim dCL {dcl:+.3f} (x_np {xnp:.2f}c, x_cg {xcg:.2f}c, Cm0_3D {cm0:.3f}) "
                 f"-> CLmax trimmed {g.clmax_trimmed():.3f}")
    for CL in (0.6, 1.0, 1.4):
        lines.append(f"  CL {CL:.1f}: CD {g.drag_coeff(CL, rho, V):.4f} (free air), "
                     f"{g.drag_coeff(CL, rho, 40.0, True):.4f} (ground, 40 ft/s)")
    with open(os.path.join(OUT, "aero_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
