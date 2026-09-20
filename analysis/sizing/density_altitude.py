"""
density_altitude.py -- March density altitude (DA) and wind at KLAL during flying hours.

Data: reference/data/klal_asos_2021-03_to_2026-04.csv (hourly ASOS, UTC)   [VERIFIED data README]
Equations (NWS, nws_density_altitude_formula lines 20-45)                  [VERIFIED]
  e   = 6.11 * 10^(7.5*Td/(237.3+Td))            (mb, Td in C)
  Tv  = T / (1 - (e/P_mb)*(1-0.622))             (K)
  DA  = 145366 * (1 - (17.326*P_inHg / Tv_R)^0.235)   (ft), P = STATION pressure
Station pressure from altimeter setting (standard NWS relation, H in m) [INFERRED standard formula]:
  P_stn = alti * ((288 - 0.0065*H)/288)^5.2561
Flying hours assumed 09:00-17:00 local (America/New_York) [UNVERIFIED: check the event schedule].

Run: python density_altitude.py  -> out/da_march_klal.csv, out/da_summary.txt, out/da_march_hist.png
"""
import numpy as np
import pandas as pd
from common import DATA, OUT, KLAL_ELEV_FT, save_csv

HOUR_START, HOUR_END = 9, 17   # local, inclusive start, exclusive end


def density_altitude(tmpf, dwpf, alti_inhg, elev_ft=KLAL_ELEV_FT):
    H = elev_ft / 3.28084
    p_inhg = alti_inhg * ((288.0 - 0.0065 * H) / 288.0) ** 5.2561
    p_mb = p_inhg * 33.8639
    T_c = (tmpf - 32.0) / 1.8
    Td_c = (dwpf - 32.0) / 1.8
    e = 6.11 * 10.0 ** (7.5 * Td_c / (237.3 + Td_c))
    Tv_k = (T_c + 273.15) / (1.0 - (e / p_mb) * (1.0 - 0.622))
    Tv_r = Tv_k * 1.8
    return 145366.0 * (1.0 - (17.326 * p_inhg / Tv_r) ** 0.235)


def main():
    df = pd.read_csv(f"{DATA}/klal_asos_2021-03_to_2026-04.csv", na_values=["M", "T"])
    df["utc"] = pd.to_datetime(df["valid"], utc=True)
    df["local"] = df["utc"].dt.tz_convert("America/New_York")
    df = df[df["local"].dt.month == 3].copy()
    df = df.dropna(subset=["tmpf", "dwpf", "alti"])
    # sanity filter for bad observations (seen: DA of 14,600 ft) [INFERRED plausibility bounds]
    n0 = len(df)
    df = df[df.alti.between(29.40, 30.80) & df.tmpf.between(30, 100) & (df.dwpf <= df.tmpf + 0.5)]
    n_bad = n0 - len(df)
    # keep one ob per hour (routine METAR near :50-:56) to avoid over-weighting specials
    df["hr"] = df["local"].dt.floor("h")
    df = df.sort_values("local").groupby("hr").tail(1)
    df["DA_ft"] = density_altitude(df.tmpf.values, df.dwpf.values, df.alti.values)
    day = df[(df["local"].dt.hour >= HOUR_START) & (df["local"].dt.hour < HOUR_END)].copy()

    q = [0, 5, 10, 25, 50, 75, 90, 95, 100]
    lines = [f"March KLAL, {day['local'].dt.year.min()}-{day['local'].dt.year.max()}, "
             f"{HOUR_START:02d}-{HOUR_END:02d} local, n={len(day)} hourly obs ({n_bad} bad March obs removed)"]
    pct = np.percentile(day.DA_ft, q)
    lines.append("DA percentiles (ft): " + ", ".join(f"P{a}={b:.0f}" for a, b in zip(q, pct)))
    lines.append(f"Temp F: median {day.tmpf.median():.1f}, P90 {day.tmpf.quantile(.9):.1f}; "
                 f"altimeter inHg median {day.alti.median():.2f}; dewpoint F median {day.dwpf.median():.1f}")
    # per-hour medians (morning vs afternoon)
    byh = day.groupby(day["local"].dt.hour).DA_ft.agg(["median", lambda s: s.quantile(0.9)])
    byh.columns = ["median", "p90"]
    lines.append("Median/P90 DA by local hour: " + "; ".join(
        f"{h}:{r['median']:.0f}/{r['p90']:.0f}" for h, r in byh.iterrows()))
    # by year (climate variability)
    byy = day.groupby(day["local"].dt.year).DA_ft.median()
    lines.append("Median DA by year: " + ", ".join(f"{y}:{v:.0f}" for y, v in byy.items()))
    # wind during flying hours
    w = day.dropna(subset=["sknt", "drct"])
    lines.append(f"Wind kt: median {w.sknt.median():.1f}, P25 {w.sknt.quantile(.25):.1f}, "
                 f"P75 {w.sknt.quantile(.75):.1f}, P90 {w.sknt.quantile(.9):.1f}")
    # headwind on best runway (10/28, 5/23, 8/26 at KLAL per klal_airnav): best of the available headings
    rw = np.array([100, 280, 50, 230, 80, 260], dtype=float)
    ang = np.deg2rad(w.drct.values[:, None] - rw[None, :])
    hw = (w.sknt.values[:, None] * np.cos(ang)).max(axis=1)
    lines.append(f"Headwind on best KLAL runway heading, kt: median {np.median(hw):.1f}, P25 {np.percentile(hw, 25):.1f}"
                 f" (calm obs {100 * np.mean(w.sknt.values == 0):.0f}%) [INFERRED: runway used at the event unknown]")
    design = dict(DA_median=float(np.percentile(day.DA_ft, 50)), DA_p90=float(np.percentile(day.DA_ft, 90)),
                  DA_p10=float(np.percentile(day.DA_ft, 10)), DA_p95=float(np.percentile(day.DA_ft, 95)),
                  DA_min=float(day.DA_ft.min()), DA_max=float(day.DA_ft.max()))
    lines.append("DESIGN: " + ", ".join(f"{k}={v:.0f}" for k, v in design.items()))
    pd.DataFrame([design]).to_csv(f"{OUT}/da_design_points.csv", index=False)
    save_csv(day[["local", "tmpf", "dwpf", "alti", "sknt", "drct", "DA_ft"]].assign(local=day["local"].astype(str)),
             "da_march_klal.csv")
    with open(f"{OUT}/da_summary.txt", "w") as f:
        f.write("\n".join(lines) + "\n")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(day.DA_ft, bins=40, color="C0", alpha=0.8)
    for k, c in (("DA_median", "k"), ("DA_p90", "r"), ("DA_p10", "g")):
        ax.axvline(design[k], color=c, ls="--", label=f"{k} {design[k]:.0f} ft")
    ax.set_xlabel("Density altitude (ft)")
    ax.set_ylabel("Hourly obs")
    ax.set_title(f"KLAL March, {HOUR_START}-{HOUR_END} local")
    ax.legend()
    fig.tight_layout()
    fig.savefig(f"{OUT}/da_march_hist.png", dpi=120)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
