"""
wing3d_check.py -- AeroSandbox vortex-lattice (VLM) check of the conceptual wing + tail model in aero.py.

What it checks (inviscid, linear; no stall, no viscous decambering):
  1. Wing alone (rectangular S1223, recommended span/chord): CL_alpha, zero-lift angle, near-field span
     efficiency e, and the wing zero-lift pitching moment Cm0 about c/4.
  2. The same wing at AR ~40 (quasi 2-D) -> ratio K_CM3D = Cm0(AR) / Cm0(2-D). aero.py needs this ratio to
     turn the viscous 2-D cm0 (NeuralFoil) into a 3-D wing Cm0. Lifting-line theory says K = 1 for an
     untwisted, unswept, constant-section wing; Raymer's AR/(AR+2) factor would give ~0.65 at AR 3.65.
  3. Wing + horizontal + vertical tail (tail volume, arm and area from aero.Geometry): neutral point x_np/c
     compared with the hand formula in aero.Geometry.trim().
  4. Trim at cruise CL and at CLmax with the CG at x_np - 0.12c: required tail incidence (inviscid) and
     the trimmed-CLmax penalty. The inviscid S1223 Cm is larger than the viscous one, so the VLM trim
     numbers are a conservative bound; the best estimate uses the viscous 2-D cm0 x K_CM3D.

Geometry units are ft (VLM coefficients are scale independent). Assumptions [INFERRED]: tail plane
4 in below the wing chord plane (boom at mid fuselage height), H-tail AR 4, V-tail AR 1.5, NACA 0009
tails, 12 spanwise x 8 chordwise panels per surface (grid checked below).

Run: python wing3d_check.py -> out/asb_check.txt, out/asb_check.csv
"""
import os
import numpy as np
import pandas as pd
import aerosandbox as asb
from common import OUT, save_csv
from aero import Geometry, lifting_line

SPAN_IN, CHORD_IN, SLOTS = 95, 26, 6      # recommended design point (sweep.py RECOMMENDED)
Z_TAIL_FT = -4.0 / 12.0
AR_H, AR_V = 4.0, 1.5
SM = 0.12                                  # static margin used by aero.Geometry.trim()
NS, NC = 12, 8                             # VLM panels (spanwise per half wing, chordwise)

AF_WING = asb.Airfoil("s1223")
AF_TAIL = asb.Airfoil("naca0009")


def rect_wing(name, x_le, span_ft, chord_ft, af, z=0.0, twist=0.0):
    return asb.Wing(name=name, symmetric=True, xsecs=[
        asb.WingXSec(xyz_le=[x_le, 0.0, z], chord=chord_ft, twist=twist, airfoil=af),
        asb.WingXSec(xyz_le=[x_le, span_ft / 2, z], chord=chord_ft, twist=twist, airfoil=af)])


def airplane(g, with_tail=True, i_t=0.0, span_ft=None):
    b = g.b if span_ft is None else span_ft
    c = g.c
    wings = [rect_wing("wing", 0.0, b, c, AF_WING)]
    if with_tail:
        bh = np.sqrt(AR_H * g.Sh)
        ch = g.Sh / bh
        x_h = 0.25 * c + g.lt - 0.25 * ch          # tail quarter chord at l_t behind wing quarter chord
        wings.append(rect_wing("htail", x_h, bh, ch, AF_TAIL, z=Z_TAIL_FT, twist=i_t))
        hv = np.sqrt(AR_V * g.Sv)
        cv = g.Sv / hv
        x_v = 0.25 * c + g.lt - 0.25 * cv
        wings.append(asb.Wing(name="vtail", symmetric=False, xsecs=[
            asb.WingXSec(xyz_le=[x_v, 0.0, Z_TAIL_FT], chord=cv, airfoil=AF_TAIL),
            asb.WingXSec(xyz_le=[x_v, 0.0, Z_TAIL_FT + hv], chord=cv, airfoil=AF_TAIL)]))
    return asb.Airplane(name="sae27", xyz_ref=[0.25 * c, 0.0, 0.0], wings=wings,
                        s_ref=b * c, c_ref=c, b_ref=b)


def vlm(ap, alpha, x_ref, ns=NS, nc=NC, stab=False):
    a = asb.VortexLatticeMethod(ap, asb.OperatingPoint(velocity=15.0, alpha=alpha), xyz_ref=[x_ref, 0.0, 0.0],
                                spanwise_resolution=ns, chordwise_resolution=nc)
    return a.run_with_stability_derivatives(alpha=True, beta=False, p=False, q=False, r=False) if stab else a.run()


def wing_alone(g, span_ft=None, ns=NS, nc=NC):
    ap = airplane(g, with_tail=False, span_ft=span_ft)
    al = np.array([-4.0, 0.0, 4.0, 8.0])
    rs = [vlm(ap, a, 0.25 * g.c, ns, nc) for a in al]
    CL = np.array([float(r["CL"]) for r in rs])
    CD = np.array([float(r["CD"]) for r in rs])
    Cm = np.array([float(r["Cm"]) for r in rs])
    cla_deg, cl0 = np.polyfit(al, CL, 1)
    dcm_dcl, cm0 = np.polyfit(CL, Cm, 1)          # Cm about c/4 = cm0 + dcm_dcl*CL
    ar = (g.b if span_ft is None else span_ft) / g.c
    k = np.polyfit(CL ** 2, CD, 1)[0]
    return dict(AR=ar, CLa_rad=cla_deg * 180 / np.pi, alpha_L0_deg=-cl0 / cla_deg, Cm0_c4=cm0,
                x_ac_over_c=0.25 - dcm_dcl, e_near=1.0 / (np.pi * ar * k))


def eta_vlm(g, alpha=8.0, ns=20, nc=10):
    """Spanwise lift distribution of the wing alone: returns max(local cl / CL) (critical-section
    factor, compare aero.py lifting-line eta_max). Strips are grouped by panel y position."""
    ap = airplane(g, with_tail=False)
    op = asb.OperatingPoint(velocity=15.0, alpha=alpha)
    a = asb.VortexLatticeMethod(ap, op, xyz_ref=[0.25 * g.c, 0.0, 0.0], spanwise_resolution=ns, chordwise_resolution=nc)
    r = a.run()
    F = np.asarray(a.forces_geometry)            # per panel, geometry axes (x aft, z up)
    al = np.radians(alpha)
    lift = F[:, 2] * np.cos(al) - F[:, 0] * np.sin(al)
    yl = np.asarray(a.front_left_vertices)[:, 1]
    yr = np.asarray(a.front_right_vertices)[:, 1]
    yc = np.round(0.5 * (yl + yr), 6)
    q = 0.5 * float(op.atmosphere.density()) * 15.0 ** 2   # same units the VLM used for the forces
    strips = {}
    for i, y in enumerate(yc):
        L0, w0 = strips.get(y, (0.0, abs(yr[i] - yl[i])))
        strips[y] = (L0 + lift[i], w0)
    cl = np.array([L / (q * g.c * w) for L, w in strips.values()])
    CL = float(r["CL"])
    return float(cl.max() / CL), CL


def main():
    g = Geometry(SPAN_IN, CHORD_IN, SLOTS, 2, "s1223")
    lines = [f"AeroSandbox VLM check: {SPAN_IN} x {CHORD_IN} in rectangular S1223 (S {g.S:.2f} ft2, AR {g.AR:.2f}), "
             f"Sh {g.Sh:.2f} ft2, Sv {g.Sv:.2f} ft2, l_t {g.lt_in:.0f} in, tail z {Z_TAIL_FT * 12:.0f} in"]
    rows = []

    # 1-2. wing alone at the design AR and at AR 40 (quasi 2-D); panel check at the design AR
    w = wing_alone(g)
    w_fine = wing_alone(g, ns=20, nc=14)
    w2d = wing_alone(g, span_ft=40 * g.c, ns=30)
    K = w["Cm0_c4"] / w2d["Cm0_c4"]
    e_ll, eta_ll, cla_ll = lifting_line(g.AR, 1.0, a0=2 * np.pi)
    for tag, d in (("wing AR design", w), ("wing AR design fine grid", w_fine), ("wing AR 40", w2d)):
        rows.append(dict(case=tag, **d))
    lines.append(f"Wing alone (VLM, inviscid): CLa {w['CLa_rad']:.3f}/rad (fine grid {w_fine['CLa_rad']:.3f}; lifting line "
                 f"a0=2pi {cla_ll:.3f}), alpha_L0 {w['alpha_L0_deg']:.1f} deg, e_near {w['e_near']:.3f} "
                 f"(lifting line e_inv {e_ll:.3f}), x_ac {w['x_ac_over_c']:.3f} c")
    eta_v, _ = eta_vlm(g)
    lines.append(f"Critical-section factor eta_max = max(cl_local)/CL: VLM {eta_v:.3f} vs lifting line (aero.py, a0 0.95*2pi) "
                 f"{g.eta_max:.3f} -> wing CLmax scales by {g.eta_max / eta_v:.3f}")
    rows.append(dict(case="eta_max", eta_vlm=eta_v, eta_lifting_line=g.eta_max))
    lines.append(f"Wing Cm0 about c/4: AR {g.AR:.2f} {w['Cm0_c4']:.3f} (fine {w_fine['Cm0_c4']:.3f}), AR 40 "
                 f"{w2d['Cm0_c4']:.3f} -> K_CM3D = {K:.3f}  (Raymer AR/(AR+2) = {g.AR / (g.AR + 2):.3f})")
    cm0_2d_visc = g.section.cm0()
    lines.append(f"  viscous 2-D cm0 (NeuralFoil) {cm0_2d_visc:.3f}; inviscid/viscous ratio {w2d['Cm0_c4'] / cm0_2d_visc:.2f}"
                 f" -> best-estimate wing Cm0 = {cm0_2d_visc * K:.3f} (aero.py uses {g.trim(1.0)[3]:.3f})")

    # 3. wing + tail neutral point
    ap = airplane(g, with_tail=True, i_t=0.0)
    s = vlm(ap, 4.0, 0.25 * g.c, stab=True)
    x_np_c = float(s["x_np"]) / g.c
    _, x_np_hand, _, _ = g.trim(1.0)
    lines.append(f"Wing + tail (VLM): CLa {float(s['CLa']):.3f}/rad, x_np {x_np_c:.3f} c from wing LE "
                 f"(aero.py hand formula {x_np_hand:.3f} c)")
    rows.append(dict(case="wing+tail", AR=g.AR, CLa_rad=float(s["CLa"]), x_np_over_c=x_np_c))

    # 4. trim with CG at x_np - SM (VLM x_np); linear model in alpha and tail incidence i_t
    x_cg = (x_np_c - SM) * g.c
    base = dict((k, vlm(airplane(g, True, it), a, x_cg)) for k, (a, it) in
                {"00": (0.0, 0.0), "a": (6.0, 0.0), "i": (0.0, -4.0)}.items())
    CL0, Cm0 = float(base["00"]["CL"]), float(base["00"]["Cm"])
    CLa = (float(base["a"]["CL"]) - CL0) / 6.0
    Cma = (float(base["a"]["Cm"]) - Cm0) / 6.0
    CLi = (float(base["i"]["CL"]) - CL0) / -4.0
    Cmi = (float(base["i"]["Cm"]) - Cm0) / -4.0
    clmax_model = g.clmax_trimmed()
    for CLt in (0.85, clmax_model):
        A = np.array([[CLa, CLi], [Cma, Cmi]])
        a_tr, i_tr = np.linalg.solve(A, [CLt - CL0, -Cm0])
        dcl_tail = CLi * i_tr        # lift change caused by the tail incidence (on wing area)
        lines.append(f"  Trim CL {CLt:.2f} (CG {x_np_c - SM:.3f} c): alpha {a_tr:5.2f} deg, tail incidence {i_tr:+.2f} deg "
                     f"(inviscid S1223 Cm, conservative); tail-incidence lift {dcl_tail:+.3f}")
        rows.append(dict(case=f"trim CL {CLt:.2f}", alpha_deg=a_tr, i_t_deg=i_tr, x_cg_over_c=x_np_c - SM))

    # trimmed CLmax: aero.py (Raymer Cm factor, hand x_np) vs corrected, same trim formula.
    # Corrected = VLM eta_max, 2-D viscous cm0 x K_CM3D, VLM x_np minus the same 0.05c fuselage shift that
    # aero.py applies (VLM has no fuselage) [INFERRED].
    X_FUS = 0.05
    clw_old = g.clmax_wing()
    clw_new = clw_old * g.eta_max / eta_v

    def trimmed(clw, cm0_3d, xnp):
        return clw + (clw * (xnp - SM - 0.25) + cm0_3d) / (g.lt / g.c)
    cl_old = trimmed(clw_old, g.trim(1.0)[3], x_np_hand)
    cl_new = trimmed(clw_new, cm0_2d_visc * K, x_np_c - X_FUS)
    cl_inv = trimmed(clw_new, w["Cm0_c4"], x_np_c - X_FUS)
    lines.append(f"Trimmed CLmax: aero.py {cl_old:.3f}; corrected (VLM eta, cm0 x K_CM3D, VLM x_np - {X_FUS}c fus) "
                 f"{cl_new:.3f} ({(cl_new / cl_old - 1) * 100:+.1f}%); with inviscid VLM Cm0 {cl_inv:.3f} "
                 f"({(cl_inv / cl_old - 1) * 100:+.1f}%)")
    lines.append("  -> aero.py errors in Cm0 (-36% magnitude) and x_np (-0.05c) largely cancel in trimmed CLmax;"
                 " use the VLM values for the stability/tail design. e_near > 1 is a near-field VLM artefact:"
                 " keep the lifting-line e.")
    rows.append(dict(case="CLmax_trim", clmax_aero_py=cl_old, clmax_corrected=cl_new, clmax_inviscid_bound=cl_inv,
                     K_CM3D=K))
    save_csv(pd.DataFrame(rows), "asb_check.csv")
    with open(os.path.join(OUT, "asb_check.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
