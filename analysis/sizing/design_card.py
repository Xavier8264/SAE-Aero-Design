"""
design_card.py -- one-page numeric description of the RECOMMENDED design point chosen by sweep.py
(read from out/design_point.csv): geometry, tail, bay, weight breakdown, aero, takeoff, circuit,
propulsion operating points. Run sweep.py first.

Run: python design_card.py -> out/design_card.txt, out/design_weight_breakdown.csv
"""
import os
import numpy as np
import pandas as pd
from common import OUT, save_csv, rho_from_da, KG_PER_SLUGFT3, N_PER_LBF
from aero import Geometry
from weight import components, empty_weight
from takeoff import ThrustModel, takeoff_distance, DA_DESIGN
import mission
from scoring import wpay

AR_H, AR_V = 4.0, 1.5     # same assumptions as wing3d_check.py [INFERRED]


def main():
    dp = pd.read_csv(os.path.join(OUT, "design_point.csv")).iloc[0]
    span, chord, ns, nm, prop = int(dp.span_in), int(dp.chord_in), int(dp.n_slots), int(dp.n_motors), dp.prop
    g = Geometry(span, chord, ns, nm, dp.airfoil)
    th = ThrustModel(nm, prop)
    W = float(dp.W_TO_lb)
    L = []
    L.append(f"DESIGN CARD: {nm} x APC {prop}, wing {span} x {chord} in rectangular {dp.airfoil.upper()}, {ns} bottle slots")
    L.append(f"Wing: S {g.S:.2f} ft2, AR {g.AR:.2f}, MAC {chord} in, W/S {W / g.S:.2f} lb/ft2 at W_TO {W:.1f} lb")
    bh = np.sqrt(AR_H * g.Sh)
    hv = np.sqrt(AR_V * g.Sv)
    L.append(f"Tail (V_H {g.V_H}, V_V {g.V_V}, l_t {g.lt_in:.0f} in): H-tail {g.Sh:.2f} ft2 ({bh * 12:.0f} x {g.Sh / bh * 12:.1f} in, AR 4); "
             f"V-tail {g.Sv:.2f} ft2 ({hv * 12:.0f} in tall x {g.Sv / hv * 12:.1f} in, AR 1.5)")
    L.append(f"Bay: {g.layers} layer(s), {g.bay_l:.1f} in long x {g.bay_w:.1f} in wide x {g.bay_h:.1f} in tall (bottles "
             f"transverse); fuselage pod ~{g.fus_l_in:.0f} in + boom; overall length ~{g.length_in:.0f} in (< 120 rule)")

    # weights
    We, parts = components(g, W, th.ps.mass_lb())
    lo, hi = empty_weight(g, W, th.ps.mass_lb(), band=0.8), empty_weight(g, W, th.ps.mass_lb(), band=1.2)
    L.append(f"Empty weight {We:.2f} lb (structure band x0.8 {lo:.2f} / x1.2 {hi:.2f}): " +
             ", ".join(f"{k} {v:.2f}" for k, v in parts.items()))
    L.append(f"Payload capability {W - We:.2f} lb (band: {W - hi:.2f} .. {W - lo:.2f}); 1E4F needs {wpay(1, 4):.2f} lb, "
             f"0E4F {wpay(0, 4):.2f}, 2E4F {wpay(2, 4):.2f}, 0E5F {wpay(0, 5):.2f}")
    save_csv(pd.DataFrame([dict(component=k, lb=v) for k, v in parts.items()] + [dict(component="TOTAL_EMPTY", lb=We)]),
             "design_weight_breakdown.csv")

    # aero
    rho = float(rho_from_da(DA_DESIGN))
    m = mission.check(g, W, th, DA_DESIGN, 4.0)
    Vc = m["V_cruise"]
    cd0, br = g.cd0_nonwing(rho, Vc)
    CLc = W / (0.5 * rho * Vc ** 2 * g.S)
    CDc = g.drag_coeff(CLc, rho, Vc)
    L.append(f"Aero: clmax_2D {g.section.clmax_design:.2f}, eta_max {g.eta_max:.3f}, CLmax wing {g.clmax_wing():.3f}, "
             f"trimmed {g.clmax_trimmed():.3f}; e {g.e_total():.3f}; CD0 non-wing {cd0:.4f} (" +
             ", ".join(f"{k} {v:.4f}" for k, v in br.items()) + ")")
    L.append(f"  Cruise/circuit V {Vc:.1f} ft/s ({Vc / 1.4667:.0f} mph), CL {CLc:.2f}, CD {CDc:.3f}, L/D {CLc / CDc:.1f}, "
             f"drag {m['D_level']:.2f} lbf")

    # takeoff at design DA and at the median DA
    for da in (DA_DESIGN, 1400.0):
        S, d = takeoff_distance(g, W, th, da, detail=True)
        L.append(f"Takeoff W {W:.1f} lb, DA {da:.0f} ft: distance {S:.1f} ft (ground {d['S_ground']:.1f} ft, {d['t_ground']:.1f} s), "
                 f"V_stall {d['V_stall']:.1f} ft/s, V_R {d['V_R']:.1f} ft/s, T0 {d['T0']:.2f} lbf, T(V_R) {d['T_R']:.2f} lbf")
    S, d = takeoff_distance(g, W, th, DA_DESIGN, detail=True)
    m = mission.check(g, W, th, DA_DESIGN, d["t_ground"])
    L.append(f"Circuit (DA {DA_DESIGN:.0f}): climb gradient {m['climb_grad']:.3f} ({m['climb_rate_fps']:.1f} ft/s at 1.3 V_s), "
             f"30 deg turn thrust margin {m['turn_thrust_margin']:.3f} W, CL_turn {m['CL_turn']:.2f}")
    L.append(f"  current level {m['I_level_A']:.0f} A / turn {m['I_turn_A']:.0f} A, flight {m['t_flight_s']:.0f} s, "
             f"charge {m['charge_Ah']:.2f} Ah of 1.76 usable; landing roll from 1.2 V_s: {m['land_roll_free_ft']:.0f} ft free, "
             f"{m['land_roll_brake_ft']:.0f} ft braked (400 ft zone incl. touchdown)")

    # propulsion operating points
    for da in (DA_DESIGN, 1400.0, 0.0):
        r = th.ps.full_throttle(0.0, float(rho_from_da(da)) * KG_PER_SLUGFT3)
        L.append(f"Prop static DA {da:5.0f}: Kv {th.ps.kv:.0f} rpm/V, {r['rpm']:.0f} rpm (APC limit {150000 / 12 if nm == 2 else 150000 / 9:.0f}), "
                 f"thrust {r['T_N'] / N_PER_LBF / nm:.2f} lbf/motor (model, x{th.factor} applied in takeoff), "
                 f"battery {r['I_A']:.0f} A total, shaft {r['P_shaft_W'] / nm:.0f} W/motor, V_batt {r['V_batt']:.1f} V")
    # bay alternative (6-slot single layer vs 8-slot two-layer 2x4) across the empty-weight band, and an
    # aluminum-tube boom instead of a wood box boom (0.13 vs 0.05 lb/ft) [INFERRED masses]
    from sweep import evaluate
    for s_ in (ns, 8):
        txt = []
        for band in (0.8, 1.0, 1.2):
            r = evaluate(span, chord, nm, s_, band=band)
            txt.append(f"band {band}: pay {r['payload_cap_lb']:.1f} -> {r['E']}E{r['F']}F FS {r['FS_max']:.0f}, "
                       f"E_FFS {r['E_FFS']:.1f}")
        L.append(f"Bay option {s_} slots: " + "; ".join(txt))
    g_b = Geometry(span, chord, ns, nm, dp.airfoil)
    lb_boom = max(g_b.lt - 0.5 * g_b.fus_l_in / 12, 0.5)
    from weight import K_BUILD
    d_al = (0.13 - 0.05) * lb_boom * K_BUILD * 1.08
    L.append(f"Aluminum-tube boom ({lb_boom:.1f} ft): +{d_al:.2f} lb empty -> payload {W - We - d_al:.2f} lb")
    with open(os.path.join(OUT, "design_card.txt"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
