"""
mission.py -- circuit feasibility checks for a given aircraft weight: climb-out, sustained banked
turn, battery charge used for one competition flight, and landing roll.

Rules: at least one complete 360 deg circuit; no turn before 400 ft from the start; land in the
same direction within a 400 ft zone, touchdown and all rolling inside it; leaving the paved runway
= DQ [VERIFIED rules_2027 lines 956-957, 1015, 1024-1040, 1049]. One 4S 2200 mAh LiPo
[VERIFIED rules_2027 line 1574-1575].

Assumed flight profile [INFERRED, until the field layout is known]:
  takeoff roll (t_ground from takeoff.py) at the full-throttle current;
  climb to 100 ft at full throttle, V = 1.3 V_stall;
  circuit: 3000 ft of level flight at V_c = max(1.4 V_stall, speed for best L/D... capped) of which
  30% in 30 deg banked turns (n = 1.155);
  approach + landing: 30 s at 10 A average.
  Usable charge 80% of 2.2 Ah = 1.76 Ah (LiPo practice) [INFERRED].
Checks:
  climb gradient (T - D)/W >= 0.05 at 1.3 V_stall, out of ground effect;
  sustained 30 deg bank turn at V_c with full throttle (T >= D_turn) and CL_turn <= CLmax/1.2^2;
  charge used <= 1.76 Ah;
  landing roll from V_TD = 1.2 V_stall, idle thrust 0, CL_g 0.9 in ground effect, mu 0.04 (free
  rolling) or 0.30 (wheel brake) [INFERRED], zero wind.
"""
import numpy as np
from common import G, rho_from_da, KG_PER_SLUGFT3, N_PER_LBF, FT_PER_M, BATT_MAH

BANK_DEG = 30.0
CIRCUIT_FT = 3000.0
TURN_FRAC = 0.30
CLIMB_FT = 100.0
USABLE_AH = 0.80 * BATT_MAH / 1000.0
CLIMB_GRAD_MIN = 0.05


def check(g, W, thr, da, t_ground, clmax=None):
    rho = float(rho_from_da(da))
    CLm = g.clmax_trimmed() if clmax is None else clmax
    Vs = np.sqrt(2 * W / (rho * g.S * CLm))
    out = dict(V_stall=Vs)
    # climb
    Vc1 = 1.3 * Vs
    CL1 = W / (0.5 * rho * Vc1 ** 2 * g.S)
    D1 = 0.5 * rho * Vc1 ** 2 * g.S * g.drag_coeff(CL1, rho, Vc1)
    T1 = float(thr.T(Vc1, da))
    grad = (T1 - D1) / W
    out.update(climb_grad=grad, climb_rate_fps=grad * Vc1)
    # turn: choose V_c = 1.4 Vs (low-speed circuit typical of heavy lifters) [INFERRED]
    n = 1.0 / np.cos(np.radians(BANK_DEG))
    Vt = 1.4 * Vs
    CLt = n * W / (0.5 * rho * Vt ** 2 * g.S)
    Dt = 0.5 * rho * Vt ** 2 * g.S * g.drag_coeff(CLt, rho, Vt)
    Tt = float(thr.T(Vt, da))
    CLl = W / (0.5 * rho * Vt ** 2 * g.S)
    Dl = 0.5 * rho * Vt ** 2 * g.S * g.drag_coeff(CLl, rho, Vt)
    out.update(V_cruise=Vt, turn_thrust_margin=(Tt - Dt) / W, CL_turn=CLt, CL_turn_ok=CLt <= CLm / 1.2 ** 2,
               D_level=Dl, D_turn=Dt)
    # charge (A h). Part-throttle current from the prop/motor model; T in N, V in m/s
    rho_si = rho * KG_PER_SLUGFT3
    ps = thr.ps
    f = thr.factor

    def amps(T_lbf, V):
        # the knock-down factor on thrust means the real prop needs T/f of "model thrust"
        return ps.part_throttle_current(T_lbf / f * N_PER_LBF, V / FT_PER_M, rho_si)

    I_full = float(np.interp(0.5 * Vs, thr.V_GRID, thr.table(da)[1]))
    t_climb = CLIMB_FT / max(out["climb_rate_fps"], 0.5)
    I_climb = float(np.interp(Vc1, thr.V_GRID, thr.table(da)[1]))
    I_lvl, I_trn = amps(Dl, Vt), amps(Dt, Vt)
    if np.isnan(I_lvl):
        I_lvl = float(np.interp(Vt, thr.V_GRID, thr.table(da)[1]))
    if np.isnan(I_trn):
        I_trn = float(np.interp(Vt, thr.V_GRID, thr.table(da)[1]))
    t_circ = CIRCUIT_FT / Vt
    Ah = (I_full * t_ground + I_climb * t_climb + t_circ * ((1 - TURN_FRAC) * I_lvl + TURN_FRAC * I_trn)
          + 10.0 * 30.0) / 3600.0
    out.update(I_level_A=I_lvl, I_turn_A=I_trn, t_climb_s=t_climb, t_flight_s=t_ground + t_climb + t_circ + 30,
               charge_Ah=Ah, charge_ok=Ah <= USABLE_AH)
    # landing roll
    for mu, tag in ((0.04, "free"), (0.30, "brake")):
        V = np.linspace(1.2 * Vs, 0.0, 200)
        q = 0.5 * rho * V ** 2
        L = q * g.S * 0.9
        D = q * g.S * g.drag_coeff(0.9, rho, max(Vs, 10.0), in_ground=True)
        a = G * (D + mu * np.maximum(W - L, 0.0)) / W
        integ = V / a
        out[f"land_roll_{tag}_ft"] = float(np.sum(0.5 * (integ[1:] + integ[:-1]) * -np.diff(V)))
    out["feasible"] = bool(grad >= CLIMB_GRAD_MIN and out["turn_thrust_margin"] >= 0 and out["CL_turn_ok"]
                           and out["charge_ok"])
    return out
