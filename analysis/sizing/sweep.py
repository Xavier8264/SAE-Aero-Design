"""
sweep.py -- conceptual sizing sweep and design-point selection.

For every (span, chord, propulsion option, bottle slots) with the S1223 wing:
  W_TO   = min(100-ft takeoff limit (takeoff.py), circuit limit (mission.py), 55 lb rule)
  W_e    = empty weight at that W_TO (weight.py, band 1.0)
  payload capability = W_TO - W_e
  bottle mix + legal 3-flight ladder (scoring.py) -> FFS_ideal = mean(top 3 FS) + 10 (PPB, if the
  TDS prediction is met)
All at the design density altitude DA_DESIGN = 2000 ft (~P90 of March daytime KLAL), zero wind.
Then: airfoil comparison, sensitivity (empty weight band, CLmax, thrust, headwind), and the
payload / FS vs density altitude curve for the recommended point (draft of the TDS curve).

Run: python sweep.py -> out/sweep_all.csv, out/sweep_best_by_slots.csv, out/design_point.csv,
     out/design_sensitivity.csv, out/design_payload_vs_DA.csv, out/sweep_summary.txt, out/sweep_*.png
"""
import os
from functools import lru_cache
import numpy as np
import pandas as pd
from common import OUT, GROSS_MAX_LB, LENGTH_MAX_IN, save_csv
from aero import Geometry
from weight import empty_weight
from takeoff import ThrustModel, wto_max, takeoff_distance, DA_DESIGN
import mission
from scoring import best_config, best_ladder, fs, wpay

SPANS = [73, 78, 84, 90, 95]
CHORDS = [12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36]
SLOTS = [3, 4, 5, 6, 7, 8]
PROP = {2: "12x6e", 4: "9x45e"}   # best per option from takeoff.py (differences < 0.5 lb)
PPB_ASSUMED = 10.0
SIGMA_CAP_LB = 2.0   # 1-sigma error of the predicted payload capability (W_e, thrust, CLmax) [INFERRED]

_THR = {}


@lru_cache(maxsize=None)
def _mean3(pay_r, ns):
    return best_ladder(pay_r, ns)[0]


def expected_ffs(pay, ns, sigma=SIGMA_CAP_LB):
    """E[mean of best legal 3-flight ladder] + PPB when the true capability ~ N(pay, sigma).
    Rewards designs whose slot count gives useful bottle mixes on both sides of the prediction
    instead of one that only works if the prediction is exactly right."""
    x, w = np.polynomial.hermite_e.hermegauss(21)
    w = w / w.sum()
    vals = [_mean3(round(max(pay + sigma * xi, 0.0), 2), ns) for xi in x]
    return float(np.dot(w, vals)) + PPB_ASSUMED


def thr_model(n, factor=None):
    key = (n, factor)
    if key not in _THR:
        _THR[key] = ThrustModel(n, PROP[n]) if factor is None else ThrustModel(n, PROP[n], factor=factor)
    return _THR[key]


def evaluate(span, chord, n_motors, n_slots, airfoil="s1223", da=DA_DESIGN, band=1.0, clmax_fac=1.0,
             thrust_factor=None, V_wind=0.0):
    g = Geometry(span, chord, n_slots, n_motors, airfoil)
    th = thr_model(n_motors, thrust_factor)
    clmax = g.clmax_trimmed() * clmax_fac
    W_to = wto_max(g, th, da, clmax=clmax, V_wind=V_wind)
    W = min(W_to, GROSS_MAX_LB)
    limit = "takeoff" if W_to <= GROSS_MAX_LB else "55 lb rule"
    _, d = takeoff_distance(g, W, th, da, clmax=clmax, V_wind=V_wind, detail=True)
    m = mission.check(g, W, th, da, d["t_ground"], clmax=clmax)
    it = 0
    while not m["feasible"] and it < 30 and W > 5:   # reduce weight until the circuit is feasible
        W *= 0.98
        limit = "circuit"
        _, d = takeoff_distance(g, W, th, da, clmax=clmax, V_wind=V_wind, detail=True)
        m = mission.check(g, W, th, da, d["t_ground"], clmax=clmax)
        it += 1
    We = empty_weight(g, W, prop_group_lb=th.ps.mass_lb(), band=band)
    pay = max(W - We, 0.0)
    bc = best_config(pay, n_slots)
    m3, ch = best_ladder(pay, n_slots)
    return dict(span_in=span, chord_in=chord, S_ft2=g.S, AR=g.AR, n_motors=n_motors, prop=PROP[n_motors],
                n_slots=n_slots, airfoil=airfoil, CLmax_trim=clmax, eta_max=g.eta_max, W_TO_lb=W, limit=limit,
                W_empty_lb=We, payload_cap_lb=pay, E=bc[0] if bc else 0, F=bc[1] if bc else 0,
                FS_max=fs(*bc) if bc else 0.0, payload_used_lb=wpay(*bc) if bc else 0.0,
                margin_lb=pay - (wpay(*bc) if bc else 0.0), mean3=m3,
                ladder=" -> ".join(f"{e}E{f}F" for e, f in ch), FFS_ideal=m3 + PPB_ASSUMED if ch else 0.0,
                E_FFS=expected_ffs(pay, n_slots),
                V_stall=d["V_stall"], V_R=d["V_R"], length_in=g.length_in, bay_l_in=g.bay_l,
                climb_grad=m["climb_grad"], charge_Ah=m["charge_Ah"], t_flight_s=m["t_flight_s"],
                V_cruise=m["V_cruise"], land_roll_free_ft=m["land_roll_free_ft"],
                land_roll_brake_ft=m["land_roll_brake_ft"], length_ok=g.length_in < LENGTH_MAX_IN - 2)


def main():
    rows = []
    for n in (2, 4):
        for span in SPANS:
            for chord in CHORDS:
                for ns in SLOTS:
                    rows.append(evaluate(span, chord, n, ns))
    df = pd.DataFrame(rows)
    df = df[df.length_ok]
    save_csv(df, "sweep_all.csv")
    lines = [f"Sweep: {len(df)} designs at DA {DA_DESIGN:.0f} ft, zero wind, S1223, band 1.0 empty weight"]

    # best per slots count and option (FFS, then margin, then lighter empty weight)
    key = ["E_FFS", "FFS_ideal", "margin_lb"]
    best_rows = []
    for (n, ns), d in df.groupby(["n_motors", "n_slots"]):
        best_rows.append(d.sort_values(key + ["W_empty_lb"], ascending=[False, False, False, True]).iloc[0])
    bb = pd.DataFrame(best_rows)
    save_csv(bb, "sweep_best_by_slots.csv")
    lines.append(" n slots  span chord  S    AR   W_TO  W_e  pay  mix   FS  mean3  FFS  margin  E_FFS")
    for _, r in bb.iterrows():
        lines.append(f" {r.n_motors} {r.n_slots:3d}   {r.span_in:4.0f} {r.chord_in:4.0f} {r.S_ft2:5.2f} {r.AR:4.2f} "
                     f"{r.W_TO_lb:5.1f} {r.W_empty_lb:5.1f} {r.payload_cap_lb:5.1f} {r.E:.0f}E{r.F:.0f}F {r.FS_max:4.0f} "
                     f"{r.mean3:5.1f} {r.FFS_ideal:5.1f} {r.margin_lb:5.2f} {r.E_FFS:5.1f}")

    # payload capability vs span/chord (2 motors, 5 slots) -> continuous objective without FS steps
    best = df.sort_values(key + ["W_empty_lb"], ascending=[False, False, False, True]).iloc[0]
    # recommended: best FFS; among equal FFS prefer the larger capability margin
    lines.append(f"Top design: {best.n_motors} motors {best.prop}, {best.span_in:.0f} x {best.chord_in:.0f} in, "
                 f"{best.n_slots} slots -> {best.E:.0f}E{best.F:.0f}F FS {best.FS_max:.0f}, FFS {best.FFS_ideal:.1f}, "
                 f"E_FFS {best.E_FFS:.1f}")
    top = df[df.E_FFS >= best.E_FFS - 1.0]
    lines.append(f"  {len(top)} designs within 1 point of the best E_FFS: span {top.span_in.min():.0f}-{top.span_in.max():.0f} in, "
                 f"chord {top.chord_in.min():.0f}-{top.chord_in.max():.0f} in, slots {top.n_slots.min()}-{top.n_slots.max()}")

    # --- design point: 2 motors unless 4 motors wins by > 1 FFS point [INFERRED preference: cost, simplicity]
    d2 = df[df.n_motors == 2].sort_values(key + ["W_empty_lb"], ascending=[False, False, False, True]).iloc[0]
    d4 = df[df.n_motors == 4].sort_values(key + ["W_empty_lb"], ascending=[False, False, False, True]).iloc[0]
    dopt = d4 if d4.E_FFS > d2.E_FFS + 1.0 else d2
    lines.append(f"Best 2-motor E_FFS {d2.E_FFS:.1f} ({d2.span_in:.0f}x{d2.chord_in:.0f}, {d2.n_slots} slots); "
                 f"best 4-motor E_FFS {d4.E_FFS:.1f} ({d4.span_in:.0f}x{d4.chord_in:.0f}, {d4.n_slots} slots)")
    # RECOMMENDED point: the optimum is flat, so among designs of the chosen option within TIE_BAND E_FFS
    # points of its best, take the smallest wing (lighter, cheaper, more battery/climb margin), then the
    # fewest slots (single-layer bay, simpler structure and loading), then the higher E_FFS [INFERRED rule].
    TIE_BAND = 0.5
    cand = df[(df.n_motors == dopt.n_motors) & (df.E_FFS >= dopt.E_FFS - TIE_BAND)]
    dp = cand.sort_values(["S_ft2", "n_slots", "E_FFS"], ascending=[True, True, False]).iloc[0]
    lines.append(f"RECOMMENDED (smallest wing, then fewest slots, within {TIE_BAND} E_FFS of the optimum): "
                 f"{dp.n_motors}x{dp.prop}, {dp.span_in:.0f} x {dp.chord_in:.0f} in (S {dp.S_ft2:.2f} ft2, AR {dp.AR:.2f}), "
                 f"{dp.n_slots} slots: W_TO {dp.W_TO_lb:.1f}, W_e {dp.W_empty_lb:.1f}, payload {dp.payload_cap_lb:.2f} lb "
                 f"-> {dp.E:.0f}E{dp.F:.0f}F FS {dp.FS_max:.0f} (margin {dp.margin_lb:.2f} lb), ladder {dp.ladder}, "
                 f"E_FFS {dp.E_FFS:.1f}")
    lines.append(f"  V_stall {dp.V_stall:.1f} ft/s, V_R {dp.V_R:.1f} ft/s, climb gradient {dp.climb_grad:.3f}, charge "
                 f"{dp.charge_Ah:.2f} Ah of 1.76, landing roll {dp.land_roll_free_ft:.0f} ft free / "
                 f"{dp.land_roll_brake_ft:.0f} ft braked, length ~{dp.length_in:.0f} in, bay {dp.bay_l_in:.1f} in long")
    save_csv(pd.DataFrame([dp]), "design_point.csv")
    span, chord, n, ns = int(dp.span_in), int(dp.chord_in), int(dp.n_motors), int(dp.n_slots)

    # --- airfoil comparison at the design geometry
    af_rows = [evaluate(span, chord, n, ns, airfoil=a) for a in
               ("s1223", "s1223rtl", "e423", "fx74cl5140", "ch10sm", "s1210", "sd7062")]
    afd = pd.DataFrame(af_rows)
    save_csv(afd, "design_airfoils.csv")
    lines.append("Airfoil at design geometry: " + "; ".join(
        f"{r.airfoil} CLmax {r.CLmax_trim:.2f} pay {r.payload_cap_lb:.1f}" for _, r in afd.iterrows()))

    # --- sensitivities
    sens = []
    base = evaluate(span, chord, n, ns)
    cases = [("nominal", {}), ("W_e x0.8 structure", dict(band=0.8)), ("W_e x1.2 structure", dict(band=1.2)),
             ("CLmax -10%", dict(clmax_fac=0.9)), ("CLmax +10%", dict(clmax_fac=1.1)),
             ("thrust x0.85", dict(thrust_factor=0.85)), ("thrust x1.00", dict(thrust_factor=1.0)),
             ("headwind 5 kt", dict(V_wind=5 * 1.68781)), ("headwind 8 kt", dict(V_wind=8 * 1.68781)),
             ("DA 1400 (median)", dict(da=1400.0))]
    for name, kw in cases:
        r = evaluate(span, chord, n, ns, **kw)
        sens.append(dict(case=name, W_TO_lb=r["W_TO_lb"], W_empty_lb=r["W_empty_lb"], payload_cap_lb=r["payload_cap_lb"],
                         mix=f"{r['E']}E{r['F']}F", FS_max=r["FS_max"], mean3=r["mean3"], FFS_ideal=r["FFS_ideal"],
                         E_FFS=r["E_FFS"], limit=r["limit"]))
    sd = pd.DataFrame(sens)
    save_csv(sd, "design_sensitivity.csv")
    lines.append("Sensitivity (payload lb / mix / FFS): " + "; ".join(
        f"{r.case}: {r.payload_cap_lb:.1f}/{r.mix}/{r.FFS_ideal:.0f} ({r.limit})" for _, r in sd.iterrows()))

    # --- best design under each empty-weight band (does the optimum move?)
    for band in (0.8, 1.2):
        sub = []
        for sp in (84, 90, 95):
            for ch in (20, 24, 28, 32, 36):
                for s in (4, 5, 6, 7):
                    sub.append(evaluate(sp, ch, n, s, band=band))
        sb = pd.DataFrame(sub).sort_values(key, ascending=False).iloc[0]
        lines.append(f"  band {band}: best {sb.span_in:.0f}x{sb.chord_in:.0f} in {sb.n_slots} slots, pay {sb.payload_cap_lb:.1f} "
                     f"-> {sb.E:.0f}E{sb.F:.0f}F FFS {sb.FFS_ideal:.1f} E_FFS {sb.E_FFS:.1f}")

    # --- payload and FS vs density altitude (TDS draft), zero wind
    da_rows = []
    for da in np.arange(-1500.0, 3001.0, 250.0):
        r = evaluate(span, chord, n, ns, da=da)
        da_rows.append(dict(DA_ft=da, W_TO_lb=r["W_TO_lb"], payload_cap_lb=r["payload_cap_lb"],
                            mix=f"{r['E']}E{r['F']}F", FS_max=r["FS_max"]))
    dd = pd.DataFrame(da_rows)
    save_csv(dd, "design_payload_vs_DA.csv")
    z = np.polyfit(dd.DA_ft, dd.payload_cap_lb, 1)
    lines.append(f"Payload vs DA (zero wind): {z[1]:.2f} {z[0] * 1000:+.3f} lb per 1000 ft; FS at DA -1500/0/1500/2000/3000: "
                 + "/".join(f"{dd[dd.DA_ft == x].FS_max.iloc[0]:.0f}" for x in (-1500, 0, 1500, 2000, 3000)))

    with open(os.path.join(OUT, "sweep_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    # --- plots
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(13, 4.8))
    for span_, col in zip(SPANS, ("C0", "C1", "C2", "C3", "C4")):
        d = df[(df.n_motors == n) & (df.n_slots == ns) & (df.span_in == span_)]
        ax[0].plot(d.S_ft2, d.payload_cap_lb, "-o", ms=3, color=col, label=f"span {span_} in")
        ax[1].plot(d.S_ft2, d.E_FFS, "-o", ms=3, color=col, label=f"span {span_} in")
    ax[0].set_ylabel("Payload capability (lb)")
    ax[1].set_ylabel("Expected FFS (capability sigma 2 lb)")
    for a in ax:
        a.set_xlabel("Wing area (ft^2)")
        a.grid(alpha=0.3)
        a.legend(fontsize=8)
    ax[0].set_title(f"{n} motors, {ns} slots, S1223, DA {DA_DESIGN:.0f} ft")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "sweep_payload_vs_S.png"), dpi=120)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(dd.DA_ft, dd.payload_cap_lb, "-o", ms=3)
    ax2 = ax.twinx()
    ax2.step(dd.DA_ft, dd.FS_max, where="mid", color="C3")
    ax.set_xlabel("Density altitude (ft)")
    ax.set_ylabel("Payload capability (lb)")
    ax2.set_ylabel("Max flight score", color="C3")
    ax.set_title(f"Design point {span}x{chord} in, {n}x{PROP[n]}, {ns} slots (zero wind)")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "design_payload_vs_DA.png"), dpi=120)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
