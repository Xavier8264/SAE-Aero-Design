"""
weight.py -- empty-weight model for a built-up wood (balsa/ply/spruce) aircraft with film covering,
calibrated to NAU "Mach Pine" 2026 (first-time team, same class and mission):
  80 in span x 19 in chord (10.56 ft^2), S1223, 60 in long fuselage, 39 x 8 in stab, 2 bottle slots,
  2 x 4250-class motors, 12.2 lb empty, 20 lb loaded  [VERIFIED PROJECT_MEMORY lines 211-214 (poster/slides)]
Sanity point (older, larger rules): NAU 2018, 120 in span, 13.6 ft^2, 18.6 lb empty
  [VERIFIED nau_2018_report line 220 for the weight; span/area from PROJECT_MEMORY].

Model (lb). Every coefficient is [INFERRED] engineering judgement for this build style; the global
structure factor K_BUILD is fitted so the model reproduces NAU 2026 exactly.
  wing      = (A_WING0 + A_WING1*chord)*S + spar caps sized for n*W bending (spruce, 3700 psi allowable, x1.6 for webs,
              joiner) + 0.25 fittings
  fuselage  = A_FUS*Swet_fus + 0.08 per bottle slot (floor, restraints) + 0.30 (wing saddle, gear mounts)
  tail      = A_TAIL*(Sh+Sv) + 0.05 lb/ft boom (wood box; an FRP/carbon boom is illegal, rules_2027
              lines 1557-1560; a 1 in x 0.035 in 6061 tube is ~0.13 lb/ft) + 0.10 fittings
  gear      = 0.045*W_TO + 0.20 (tricycle, steerable nose wheel)
  misc      = 8% of structure (glue, hardware, film overlaps)
  purchased = propulsion group (propulsion.py mass_lb) + battery 0.55 + 5 servos x 0.13 + 0.40 (Rx, arming plug, wiring)
Uncertainty band: 0.8 / 1.0 / 1.2 x structure (a skilled lean build vs a NAU-like first build vs overweight).
"""
import os
import numpy as np
import pandas as pd
from common import OUT, save_csv
from aero import Geometry

A_WING0 = 0.25      # lb/ft^2 sheeting + LE/TE + film  [INFERRED]
A_WING1 = 0.05      # lb/ft^2 per ft of chord: rib weight per unit area grows ~ chord (0.33 at 19 in) [INFERRED]
A_FUS = 0.20        # lb/ft^2 of fuselage wetted area (ply/balsa box, lightening holes) [INFERRED]
A_TAIL = 0.16       # lb/ft^2 of tail planform (built-up or sheet balsa) [INFERRED]
N_DESIGN = 3.0      # limit load factor used to size the spar [INFERRED; confirm with the structures plan]
SPRUCE_DENS = 0.0145  # lb/in^3 (SG ~0.40)        [INFERRED; wood_handbook_ch5 lists SG by species]
SPRUCE_ALLOW = 3700.0  # psi, ~5600 psi compression parallel / 1.5  [INFERRED]
BATTERY_LB = 0.55   # 4S 2200 mAh pack [UNVERIFIED: weigh the chosen pack]
SERVOS = 5
SERVO_LB = 0.13
RX_WIRING_LB = 0.40
PROP_GROUP_DEFAULT = {2: 1.68, 4: 2.07}   # from propulsion.py mass_lb() [INFERRED masses]
K_BUILD = None      # set by calibrate()


def wing_spar_lb(span_in, S_in2, tc, W_TO, n=N_DESIGN):
    """Two spruce caps sized by root bending moment M = n*W*b/8 (uniform lift, conservative),
    cap depth 0.85*t, caps taper to 60% average, x1.6 for shear webs and joiner."""
    return 1.6 * 2 * SPRUCE_DENS * 0.6 * n * W_TO * span_in ** 3 / (8 * SPRUCE_ALLOW * 0.85 * tc * S_in2)


def components(g, W_TO, prop_group_lb=None, k_build=None, fus_swet=None, tail_area=None, boom_ft=None):
    k = K_BUILD if k_build is None else k_build
    tc = {"s1223": 0.121, "s1223rtl": 0.135, "e423": 0.125, "fx74cl5140": 0.140, "ch10sm": 0.128,
          "s1210": 0.120, "sd7062": 0.140}[g.af]    # from airfoil_summary.csv (asb max_thickness)
    wing = (A_WING0 + A_WING1 * g.c) * g.S + wing_spar_lb(g.b_in, g.S * 144, tc, W_TO) + 0.25
    sw = g.swet_fus() if fus_swet is None else fus_swet
    fus = A_FUS * sw + 0.08 * g.ns + 0.30
    ta = (g.Sh + g.Sv) if tail_area is None else tail_area
    lb = max(g.lt - 0.5 * g.fus_l_in / 12, 0.5) if boom_ft is None else boom_ft
    tail = A_TAIL * ta + 0.05 * lb + 0.10
    gear = 0.045 * W_TO + 0.20
    struct = wing + fus + tail + gear
    misc = 0.08 * struct
    pg = PROP_GROUP_DEFAULT[g.nm] if prop_group_lb is None else prop_group_lb
    purchased = pg + BATTERY_LB + SERVOS * SERVO_LB + RX_WIRING_LB
    parts = dict(wing=k * wing, fuselage=k * fus, tail=k * tail, gear=k * gear, misc=k * misc,
                 propulsion=pg, battery=BATTERY_LB, avionics=SERVOS * SERVO_LB + RX_WIRING_LB)
    return sum(parts.values()), parts


def empty_weight(g, W_TO, prop_group_lb=None, band=1.0):
    """Empty weight (lb) incl. battery; band scales the structural part (0.8 / 1.0 / 1.2)."""
    return components(g, W_TO, prop_group_lb, k_build=K_BUILD * band)[0]


def calibrate():
    """Fit K_BUILD to NAU 2026. Their fuselage was a 60 in full-length fuselage (no boom); assumed
    6 x 6 in mean section -> Swet ~ 2*(0.5+0.5)*5*0.85 = 8.5 ft^2 [INFERRED]; stab 39 x 8 in = 2.17 ft^2
    [VERIFIED memory line 212], fin assumed 0.8 ft^2 [INFERRED]."""
    global K_BUILD
    g = Geometry(80, 19, 2, 2, "s1223")
    f = lambda k: components(g, 20.0, 1.68, k_build=k, fus_swet=8.5, tail_area=2.17 + 0.8, boom_ft=0.0)[0]
    # linear in k: W = k*A + B
    B = f(0.0)
    A = f(1.0) - B
    K_BUILD = (12.2 - B) / A
    return K_BUILD, g


if K_BUILD is None:
    calibrate()


def main():
    k, gN = calibrate()
    lines = [f"K_BUILD fitted to NAU 2026 (12.2 lb): {k:.3f}"]
    W, parts = components(gN, 20.0, 1.68, fus_swet=8.5, tail_area=2.97, boom_ft=0.0)
    lines.append("  NAU 2026 breakdown: " + ", ".join(f"{a} {b:.2f}" for a, b in parts.items()) + f" -> {W:.2f} lb")
    # sanity: NAU 2018 (120 in, 13.6 ft^2 -> chord 16.3 in), assume 3 slots-equivalent bay, W_TO 40 lb
    g18 = Geometry(120, 16.3, 3, 2, "s1223")
    W18 = empty_weight(g18, 40.0)
    lines.append(f"  Sanity NAU 2018 (120 in, 13.6 ft2, assumed W_TO 40 lb): model {W18:.1f} lb vs 18.6 lb actual "
                 f"(older rules, different payload/fuselage; order-of-magnitude check only)")
    rows = []
    for span in (73, 80, 86, 90, 95):
        for chord in (14, 16, 18, 20, 22, 24):
            for ns in (4, 5, 6):
                g = Geometry(span, chord, ns, 2, "s1223")
                for W_TO in (30.0, 35.0):
                    We, p = components(g, W_TO, 1.68)
                    rows.append(dict(span_in=span, chord_in=chord, S_ft2=g.S, n_slots=ns, W_TO=W_TO, W_empty=We,
                                     W_empty_lo=empty_weight(g, W_TO, band=0.8),
                                     W_empty_hi=empty_weight(g, W_TO, band=1.2), **{f"w_{a}": b for a, b in p.items()}))
    df = pd.DataFrame(rows)
    save_csv(df, "weight_table.csv")
    lines.append("Empty weight (lb, band 0.8/1.0/1.2 on structure), 2 motors, S1223, W_TO 35 lb:")
    for span, chord, ns in ((80, 19, 2), (90, 18, 5), (95, 20, 5), (95, 22, 5), (95, 24, 6)):
        g = Geometry(span, chord, ns, 2, "s1223")
        We, p = components(g, 35.0, 1.68)
        lines.append(f"  {span} x {chord} in ({g.S:5.2f} ft2), {ns} slots: {empty_weight(g, 35, band=0.8):5.2f} / "
                     f"{We:5.2f} / {empty_weight(g, 35, band=1.2):5.2f}   wing {p['wing']:.2f} fus {p['fuselage']:.2f} "
                     f"tail {p['tail']:.2f} gear {p['gear']:.2f}")
    with open(os.path.join(OUT, "weight_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
