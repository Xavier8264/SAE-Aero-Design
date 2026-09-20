"""
scoring.py -- Regular Class 2027 scoring and payload-ladder model.

Rules used (rules_2027, printed p.35-36):
  FS  = 3*EB + 11*FB                                   [VERIFIED rules_2027 line 1632]
  FFS = (FS1+FS2+FS3)/3 + PPB,  PPB = max(10-(FS-PS)^2, 0), PPB taken from whichever of the
        top-3 flights gives the largest PPB            [VERIFIED rules_2027 line 1629-1647]
  EMPTY bottle: 1.0 < W < 4.0 lb; FILLED: W >= 4.0 lb  [VERIFIED rules_2027 line 1592-1595]
  After a scored flight the next attempt must add >= 1 empty and/or swap >= 1 empty for a
  filled; total bottle count constant or increasing    [VERIFIED rules_2027 line 1597-1599; faq_394 line 38-46]
  -> modelled as: next config (E',F') must have F' >= F, N' >= N, and differ from (E,F).
     (Removing a filled bottle is not a listed option [INFERRED].)
  No fixed number of flight attempts                   [VERIFIED rules_2027 line 915-919]

Run:  python scoring.py   (writes out/scoring_*.csv and out/scoring_fs_vs_payload.png)
"""
import itertools
import numpy as np
import pandas as pd
from common import W_FILLED, W_EMPTY, PTS_EMPTY, PTS_FILLED, OUT, save_csv


def fs(E, F):
    return PTS_EMPTY * E + PTS_FILLED * F


def wpay(E, F):
    return W_EMPTY * E + W_FILLED * F


def feasible_configs(w_cap, n_slots, min_bottles=1):
    """All (E, F) with payload weight <= w_cap and E+F <= n_slots (>= 1 bottle per flight)."""
    out = []
    for F in range(0, n_slots + 1):
        for E in range(0, n_slots - F + 1):
            if E + F < min_bottles:
                continue
            if wpay(E, F) <= w_cap + 1e-9:
                out.append((E, F))
    return out


def best_config(w_cap, n_slots):
    """Max-FS config; ties -> more filled bottles (tie-break rule), then lighter."""
    cfg = feasible_configs(w_cap, n_slots)
    if not cfg:
        return None
    return max(cfg, key=lambda c: (fs(*c), c[1], -wpay(*c)))


def can_follow(a, b):
    """True if config b may follow scored config a."""
    (Ea, Fa), (Eb, Fb) = a, b
    return Fb >= Fa and (Eb + Fb) >= (Ea + Fa) and (Ea, Fa) != (Eb, Fb)


def best_ladder(w_cap, n_slots, n_rungs=3):
    """Best chain of n_rungs scored flights (strictly increasing under the rules) maximising the
    mean FS, all within capability. DP over the partial order. Returns (mean_fs, [configs])."""
    cfg = feasible_configs(w_cap, n_slots)
    if not cfg:
        return 0.0, []
    # prev[c] = (sum of FS, chain) for the best chain of the current length ending at config c.
    # can_follow() implies FS strictly increases along a chain (F'>=F, N'>=N, not equal).
    prev = {c: (fs(*c), [c]) for c in cfg}
    for _ in range(n_rungs - 1):
        cur = {}
        for b in cfg:
            cands = [(prev[a][0] + fs(*b), prev[a][1] + [b]) for a in prev if can_follow(a, b)]
            if cands:
                cur[b] = max(cands, key=lambda t: (t[0], t[1][-1][1]))
        prev = cur
        if not prev:
            return 0.0, []
    s, ch = max(prev.values(), key=lambda t: (t[0], fs(*t[1][-1]), t[1][-1][1]))
    return s / n_rungs, ch


def ladder_table(w_list, slot_list):
    rows = []
    for ns in slot_list:
        for w in w_list:
            bc = best_config(w, ns)
            if bc is None:
                continue
            m3, ch = best_ladder(w, ns)
            rows.append(dict(n_slots=ns, w_cap_lb=w, E=bc[0], F=bc[1], FS_max=fs(*bc),
                             w_used_lb=wpay(*bc), mean3=m3,
                             ladder=" -> ".join(f"{e}E{f}F" for e, f in ch),
                             FFS_ppb10=m3 + 10.0))
    return pd.DataFrame(rows)


def simulate_competition(w_true, n_slots, plan, n_attempts=5, p_other_fail=0.10, rng=None):
    """One competition. plan = ordered list of configs to attempt (climbing). A flight fails if
    payload > w_true or with prob p_other_fail. After a failure the same rung is retried; after a
    payload failure the team drops the rest of the plan and re-flies nothing heavier.
    Returns (top-3 FS list, best achieved FS)."""
    scored = []
    i = 0
    cap_known = np.inf
    for _ in range(n_attempts):
        if i >= len(plan):
            break
        c = plan[i]
        if wpay(*c) >= cap_known:
            break
        fail = (wpay(*c) > w_true) or (rng.random() < p_other_fail)
        if fail:
            if wpay(*c) > w_true:
                cap_known = wpay(*c)  # team learns it is too heavy (failed takeoff)
            continue  # retry the same rung next attempt
        scored.append(fs(*c))
        i += 1
    scored.sort(reverse=True)
    return scored[:3]


def ffs_from(scored, ps):
    if not scored:
        return 0.0
    top = scored[:3] + [0.0] * (3 - len(scored[:3]))
    ppb = max(max(10.0 - (s - ps) ** 2 for s in scored[:3]), 0.0)
    return float(np.mean(top)) + ppb


def monte_carlo(w_pred, n_slots, sigma_frac=0.05, n_attempts=5, n_mc=20000, seed=1):
    """Compare flight plans for an aircraft whose predicted capability is w_pred (lb payload).
    Capability truth ~ N(w_pred, sigma_frac*w_pred) [UNVERIFIED prediction error]."""
    rng = np.random.default_rng(seed)
    rows = []
    for frac in (1.00, 0.95, 0.90):
        top = best_config(frac * w_pred, n_slots)
        m3, ch = best_ladder(frac * w_pred, n_slots)
        # climbing plan: one safe opener (the lowest rung of a 4-rung ladder), then the best 3-ladder
        m4, ch4 = best_ladder(frac * w_pred, n_slots, n_rungs=4)
        plan = ch4 if ch4 else ch
        # stretch rung after the plan: best config at 105% of predicted capability
        stretch = best_config(1.05 * w_pred, n_slots)
        if stretch is not None and can_follow(plan[-1], stretch):
            plan = plan + [stretch]
        ps = fs(*top)  # TDS prediction = planned top rung
        res = [ffs_from(simulate_competition(rng.normal(w_pred, sigma_frac * w_pred), n_slots, plan,
                                             n_attempts, rng=rng), ps) for _ in range(n_mc)]
        res = np.array(res)
        rows.append(dict(plan_top_frac=frac, PS=ps, plan=" -> ".join(f"{e}E{f}F" for e, f in plan),
                         ideal_FFS=m3 + 10, mean_FFS=res.mean(), p10_FFS=np.percentile(res, 10),
                         p50_FFS=np.percentile(res, 50)))
    return pd.DataFrame(rows)


def main():
    w_list = np.round(np.arange(1.0, 45.01, 0.25), 2)
    slots = [2, 3, 4, 5, 6, 7, 8, 10, 12, 40]
    df = ladder_table(w_list, slots)
    save_csv(df, "scoring_ladders.csv")

    # Marginal value per lb and per slot [INFERRED from FS formula]
    per_lb_f, per_lb_e = PTS_FILLED / W_FILLED, PTS_EMPTY / W_EMPTY
    lines = []
    lines.append(f"Points per lb: filled {per_lb_f:.3f}, empty {per_lb_e:.3f} (at {W_FILLED}/{W_EMPTY} lb)")
    lines.append(f"Points per slot: filled {PTS_FILLED:.0f}, empty {PTS_EMPTY:.0f}")

    # Examples: capability 8..24 lb with unlimited slots vs tight bays
    for w in (8, 12, 14, 16, 18, 20, 24):
        for ns in (4, 5, 6, 40):
            r = df[(df.n_slots == ns) & (df.w_cap_lb == w)].iloc[0]
            lines.append(f"W_cap {w:>4.1f} lb slots {ns:>2d}: best {int(r.E)}E+{int(r.F)}F FS={r.FS_max:>4.0f} "
                         f"mean3={r.mean3:5.1f} ladder {r.ladder}")

    # Plot FS_max and mean3 vs payload capability
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for ns, col in ((3, "C0"), (4, "C1"), (5, "C2"), (6, "C3"), (40, "k")):
        d = df[df.n_slots == ns]
        lab = "unlimited slots" if ns == 40 else f"{ns} slots"
        ax[0].step(d.w_cap_lb, d.FS_max, where="post", color=col, label=lab)
        ax[1].step(d.w_cap_lb, d.mean3, where="post", color=col, label=lab)
    for a, t in zip(ax, ("Max single-flight FS", "Mean of best legal 3-flight ladder")):
        a.set_xlabel("Payload capability (lb)")
        a.set_title(t)
        a.grid(alpha=0.3)
        a.set_xlim(0, 32)
        a.set_ylim(0, 90)
    ax[0].plot([0, 32], [0, 32 * per_lb_f], "k:", lw=0.8, label="11/4.05 pts/lb")
    ax[0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{OUT}/scoring_fs_vs_payload.png", dpi=120)

    # Monte Carlo of flight plans for representative capabilities
    mcs = []
    for w_pred in (12.0, 16.0, 20.0):
        for ns in (4, 5, 6):
            d = monte_carlo(w_pred, ns)
            d.insert(0, "n_slots", ns)
            d.insert(0, "w_pred_lb", w_pred)
            mcs.append(d)
    mc = pd.concat(mcs, ignore_index=True)
    save_csv(mc, "scoring_mc.csv")
    for w_pred in (16.0,):
        for _, r in mc[mc.w_pred_lb == w_pred].iterrows():
            lines.append(f"MC w_pred {r.w_pred_lb:.0f} lb slots {int(r.n_slots)} top@{r.plan_top_frac:.2f}: "
                         f"PS={r.PS:.0f} ideal {r.ideal_FFS:.1f} mean {r.mean_FFS:.1f} p10 {r.p10_FFS:.1f}")
    with open(f"{OUT}/scoring_summary.txt", "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:2] + lines[2:30:1][:22]))


if __name__ == "__main__":
    main()
