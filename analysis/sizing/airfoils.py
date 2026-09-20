"""
airfoils.py -- NeuralFoil comparison of high-lift airfoils at the Reynolds numbers of this aircraft.

Why these Re: chord 14-18 in, takeoff/landing 35-45 ft/s, cruise 50-65 ft/s at DA ~1400-2000 ft
(rho ~0.00224 slug/ft^3, mu ~3.85e-7 slug/ft s at 80 F) -> Re ~ 250k (liftoff, small chord) to
~450k (cruise, large chord)  [INFERRED from common.reynolds()].

Tool: NeuralFoil 0.3.3 'xlarge' (neural-net surrogate trained on XFoil). n_crit = 9 (standard wind
tunnel / clean air). Near stall NeuralFoil, like XFoil, is optimistic for thick, highly cambered
sections [INFERRED]; its analysis_confidence output is reported so low-confidence points are visible.
Validation point: S1223 measured Cl,max = 2.23, Cm,c/4 = -0.29 at Re 200k
[VERIFIED selig_guglielmo_1997 line 267]; E423 Cl,max 2.00, Cm -0.25 at Re 200k (their note:
based on predictions) [VERIFIED selig_guglielmo_1997 line 260].

Outputs: out/airfoil_polars.csv (full polars, used by wing3d.py / takeoff.py),
         out/airfoil_summary.csv, out/airfoil_summary.txt, out/airfoil_polars.png
"""
import os
import numpy as np
import pandas as pd
import neuralfoil as nf
import aerosandbox as asb
from common import RAW, OUT, save_csv

AIRFOILS = ["s1223", "s1223rtl", "e423", "fx74cl5140", "ch10sm", "s1210", "sd7062"]
RE_LIST = [200e3, 250e3, 350e3, 450e3]
ALPHA = np.arange(-6.0, 22.01, 0.25)
N_CRIT = 9.0
CONF_MIN = 0.5  # points below this NeuralFoil confidence are flagged


def polar(name, Re, n_crit=N_CRIT):
    path = os.path.join(RAW, f"airfoil_{name}.dat")
    r = nf.get_aero_from_dat_file(path, alpha=ALPHA, Re=np.full_like(ALPHA, Re), n_crit=n_crit,
                                  model_size="xlarge")
    return pd.DataFrame(dict(airfoil=name, Re=Re, alpha=ALPHA, CL=np.asarray(r["CL"]), CD=np.asarray(r["CD"]),
                             CM=np.asarray(r["CM"]), conf=np.asarray(r["analysis_confidence"])))


def first_peak(d):
    """Cl,max = first local maximum of CL(alpha) (avoids post-stall surrogate artefacts)."""
    cl = d.CL.values
    for i in range(1, len(cl) - 1):
        if cl[i] >= cl[i - 1] and cl[i] > cl[i + 1] and d.alpha.values[i] > 4.0:
            return i
    return int(np.argmax(cl))


def at_cl(d, cl_target, col):
    """Value of column col at cl_target on the attached branch (alpha < alpha_clmax)."""
    i = first_peak(d)
    a = d.iloc[: i + 1]
    if cl_target > a.CL.max() or cl_target < a.CL.min():
        return np.nan
    order = np.argsort(a.CL.values)
    return float(np.interp(cl_target, a.CL.values[order], a[col].values[order]))


def summarize(d, tc):
    i = first_peak(d)
    att = d.iloc[: i + 1]
    ld = att.CL / att.CD
    j = int(np.argmax(ld.values))
    e15 = (att.CL.clip(lower=0) ** 1.5 / att.CD).values
    k = int(np.argmax(e15))
    return dict(airfoil=d.airfoil.iloc[0], Re=d.Re.iloc[0], t_c=tc,
                clmax=d.CL.iloc[i], alpha_clmax=d.alpha.iloc[i], conf_at_clmax=d.conf.iloc[i],
                cm_at_clmax=d.CM.iloc[i],
                cl0=float(np.interp(0.0, d.alpha, d.CL)), cm0=float(np.interp(0.0, d.alpha, d.CM)),
                ld_max=ld.values[j], cl_at_ldmax=att.CL.values[j],
                cl32_cd_max=e15[k], cl_at_cl32cd_max=att.CL.values[k],
                cd_at_cl10=at_cl(d, 1.0, "CD"), cd_at_cl15=at_cl(d, 1.5, "CD"),
                cm_at_cl10=at_cl(d, 1.0, "CM"), cm_at_cl15=at_cl(d, 1.5, "CM"),
                alpha_at_cl15=at_cl(d, 1.5, "alpha"))


def main():
    polars, rows = [], []
    for name in AIRFOILS:
        af = asb.Airfoil(name=name, coordinates=os.path.join(RAW, f"airfoil_{name}.dat"))
        tc = float(af.max_thickness())
        for Re in RE_LIST:
            d = polar(name, Re)
            polars.append(d)
            rows.append(summarize(d, tc))
    P = pd.concat(polars, ignore_index=True)
    S = pd.DataFrame(rows)
    # sensitivity: n_crit 5 (turbulent-ish, prop wash / rough balsa+film) at Re 350k
    rough = []
    for name in AIRFOILS:
        d = polar(name, 350e3, n_crit=5.0)
        s = summarize(d, np.nan)
        rough.append(dict(airfoil=name, clmax_ncrit5_Re350k=s["clmax"], ld_max_ncrit5_Re350k=s["ld_max"]))
    S = S.merge(pd.DataFrame(rough), on="airfoil", how="left")
    save_csv(P, "airfoil_polars.csv")
    save_csv(S, "airfoil_summary.csv")

    lines = [f"NeuralFoil xlarge, n_crit {N_CRIT:.0f}. Validation: S1223 exp Cl,max 2.23 / Cm -0.29 @Re200k "
             f"[selig_guglielmo_1997 l.267]"]
    v = S[(S.airfoil == "s1223") & (S.Re == 200e3)].iloc[0]
    lines.append(f"  NeuralFoil S1223 @Re200k: clmax {v.clmax:.2f} at {v.alpha_clmax:.1f} deg, "
                 f"cm_at_clmax {v.cm_at_clmax:.3f}, conf {v.conf_at_clmax:.2f}")
    lines.append("Re 350k summary (see airfoil_summary.csv for 200k/250k/450k):")
    lines.append("  airfoil      t/c  clmax a_clmax conf  cm0    L/Dmax @cl  cd@1.5  cm@1.5 clmax(ncrit5)")
    for _, r in S[S.Re == 350e3].iterrows():
        lines.append(f"  {r.airfoil:11s} {r.t_c:5.3f} {r.clmax:5.2f} {r.alpha_clmax:5.1f} {r.conf_at_clmax:5.2f} "
                     f"{r.cm0:6.3f} {r.ld_max:6.1f} {r.cl_at_ldmax:4.2f} {r.cd_at_cl15:7.4f} {r.cm_at_cl15:6.3f} "
                     f"{r.clmax_ncrit5_Re350k:5.2f}")
    lines.append("clmax vs Re: " + "; ".join(
        f"{a}: " + "/".join(f"{x:.2f}" for x in S[S.airfoil == a].clmax) for a in AIRFOILS))
    with open(os.path.join(OUT, "airfoil_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.5))
    for name in AIRFOILS:
        d = P[(P.airfoil == name) & (P.Re == 350e3)]
        ax[0].plot(d.alpha, d.CL, label=name)
        ax[1].plot(d.CD, d.CL, label=name)
        ax[2].plot(d.alpha, d.CM, label=name)
    ax[0].set_xlabel("alpha (deg)"); ax[0].set_ylabel("cl")
    ax[1].set_xlabel("cd"); ax[1].set_ylabel("cl"); ax[1].set_xlim(0, 0.06)
    ax[2].set_xlabel("alpha (deg)"); ax[2].set_ylabel("cm c/4")
    for a in ax:
        a.grid(alpha=0.3)
    ax[0].legend(fontsize=8)
    ax[0].set_title("NeuralFoil, Re 350k, n_crit 9")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "airfoil_polars.png"), dpi=120)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
