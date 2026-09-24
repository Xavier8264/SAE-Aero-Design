"""
predict_x2820.py -- model predictions for the T-2 thrust stand with the motor actually bought.

Runs the existing propulsion model (analysis/sizing/propulsion.py, APC PER3 + Drela first-order motor
+ linear pack sag) at J = 0 with the SunnySky X2820 800 KV constants instead of the generic motor class.
These are the numbers the stand measurements get compared against, and the current column is the
safety pre-check: any prop predicted above the motor's rated current gets a throttle ramp, not a
straight 100 percent burst.

Motor constants come from the manufacturer datasheet (reference/text/sunnysky_x2820_800kv_spec.txt) and are
[UNVERIFIED] until TEST_PLAN.md Run C measures Kv, Rm and I0 on our own motor.

Run: python analysis/tests/predict_x2820.py -> analysis/tests/out/predict_x2820.csv + short summary
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "sizing"))

import pandas as pd
from common import N_PER_LBF, KG_PER_SLUGFT3, rho_from_da
from propulsion import PropSystem, V_OC_TO, R_BATT

KV = 800.0
RM = 0.041      # ohm, datasheet "Motor resistance 41 mOhm"
I0 = 0.9        # A, datasheet "No-load current 0.9A/10V" (I0 rises with rpm; at 4S it is higher)
I_MAX = 46.0    # A, datasheet "Max continuous current 46A/30s"
RESC = 0.003    # ohm, ESC on-resistance, same assumption as propulsion.py MOTOR_CLASS[2]
DA_FT = 1400.0  # same DA as the prop_candidates.csv tables, so the numbers are comparable

PROPS = ["12x6e", "12x8e", "12x10e", "9x6e", "9x45e"]
AIRCRAFT_N = {"12": 2, "9": 4}  # rules: 2 x 12 in or 4 x 9 in


def main():
    rho = rho_from_da(DA_FT) * KG_PER_SLUGFT3
    motor = dict(Rm=RM, I0=I0, Resc=RESC, m_motor_lb=0.0, m_esc_lb=0.0, m_prop_lb=0.0, m_mount_lb=0.0)
    rows = []
    for pn in PROPS:
        n_ac = AIRCRAFT_N[pn.split("x")[0]]
        for n_live, case in ((1, "stand, 1 motor"), (n_ac, f"aircraft, {n_ac} motors")):
            ps = PropSystem(n_live, pn, kv=KV, motor=motor, v_oc=V_OC_TO, r_batt=R_BATT)
            r = ps.full_throttle(0.0, rho)
            I_m = r["I_A"] / n_live
            T1 = r["T_N"] / n_live / N_PER_LBF
            rows.append(dict(prop=pn, case=case, n_live=n_live, rpm=round(r["rpm"]),
                             rpm_limit=round(ps.p["rpm_limit"]), T_per_motor_lbf=round(T1, 2),
                             T_per_motor_g=round(T1 * 453.592), T_total_lbf=round(T1 * n_live, 2),
                             I_per_motor_A=round(I_m, 1), I_batt_A=round(r["I_A"], 1),
                             V_batt_V=round(r["V_batt"], 2), P_elec_per_motor_W=round(r["V_batt"] * I_m),
                             P_shaft_per_motor_W=round(r["P_shaft_W"] / n_live),
                             pct_of_I_max=round(100 * I_m / I_MAX), g_per_W=round(T1 * 453.592 / (r["V_batt"] * I_m), 2)))
    df = pd.DataFrame(rows)
    out = os.path.join(HERE, "out")
    os.makedirs(out, exist_ok=True)
    df.to_csv(os.path.join(out, "predict_x2820.csv"), index=False)
    print(f"X2820 Kv {KV:.0f}, Rm {RM} ohm, I0 {I0} A, I_max {I_MAX} A; V_oc {V_OC_TO} V, R_batt {R_BATT} ohm, DA {DA_FT:.0f} ft")
    print(df[["prop", "case", "rpm", "T_per_motor_g", "T_total_lbf", "I_per_motor_A", "I_batt_A", "V_batt_V",
              "P_elec_per_motor_W", "pct_of_I_max"]].to_string(index=False))

    # Cross-check against the SunnySky 100 percent rows (reference/data/sunnysky_x2820_800kv_testdata.csv).
    # Their test conditions are not published; assume a stiff 14.8 V source (r_batt = 0) at sea level.
    rho_sl = rho_from_da(0.0) * KG_PER_SLUGFT3
    mfr = {"12x6e": (32.7, 2240.0), "12x8e": (38.5, 2300.0)}
    print("Model vs SunnySky 100 pct rows (14.8 V stiff source, sea level; mfr conditions unpublished):")
    for pn, (I_mfr, T_mfr) in mfr.items():
        r = PropSystem(1, pn, kv=KV, motor=motor, v_oc=14.8, r_batt=0.0).full_throttle(0.0, rho_sl)
        T_g = r["T_N"] / N_PER_LBF * 453.592
        print(f"  {pn}: model {T_g:.0f} gf {r['I_A']:.1f} A {r['rpm']:.0f} rpm | mfr {T_mfr:.0f} gf {I_mfr:.1f} A"
              f" | thrust ratio mfr/model {T_mfr / T_g:.3f}, current ratio {I_mfr / r['I_A']:.3f}")


if __name__ == "__main__":
    main()
