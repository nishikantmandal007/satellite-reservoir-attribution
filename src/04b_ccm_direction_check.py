"""
FIX B4a — CCM direction validation + corrected significance protocol (v2)
==========================================================================
Defect (RECOVERY_ROADMAP.md §1.1 B4, verified 2026-07-11):
    src/04_causal_inference.py:525-531 called pyEDM.CCM(columns='cause',
    target='effect'), read ONLY out['cause:effect'], and interpreted the
    direction by assumption. Additionally the surrogate null was computed at
    ONE library size while significance used max-rho across ALL sizes
    (selection/test mismatch).

Fixes implemented here:
  1. CONVENTION PINNING: pyEDM's cross-map direction semantics are validated
     EMPIRICALLY on a synthetic unidirectionally-coupled system (logistic
     maps, x -> y known). Whichever output column carries convergent skill on
     ground truth defines the reading applied to real data. No doc-trusting.
  2. BOTH directions reported for every pair.
  3. MATCHED NULL: phase-randomised surrogates get their OWN rho-vs-L curve;
     per-library-size 95th-percentile envelope; significance requires
     consistent exceedance across library sizes AND positive convergence
     slope of the REAL curve.

Data note: residual inputs come from delta_S_anthro_v2.csv (de-leaked, B3)
so Stage-4 v2 numbers sit downstream of the corrected Stage-3 pipeline.

Outputs (v1 never overwritten):
    data/processed/ccm_results_v2.csv
    data/processed/ccm_summary_v2.txt

Run: uv run python src/04b_ccm_direction_check.py [--surr N]
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import pyEDM
    PYEDM_OK = True
except ImportError:
    PYEDM_OK = False

from statsmodels.tsa.seasonal import STL

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'

RANDOM_STATE = 42


# ────────────────────────────────────────────────────────────────────────
# Part 1: pin the pyEDM direction convention on synthetic ground truth
# ────────────────────────────────────────────────────────────────────────

def coupled_logistic(n=600, burn=200, rx=3.8, ry=3.66, c=0.32, seed=7):
    """Unidirectional coupling: x drives y; y does NOT feed back to x."""
    rng = np.random.default_rng(seed)
    x, y = 0.4, 0.2
    for _ in range(burn):
        xn = rx * x * (1 - x)
        yn = ry * ((c * x + (1 - c) * y)) * (1 - (c * x + (1 - c) * y))
        x, y = xn, yn
    xs, ys = [], []
    for _ in range(n):
        xs.append(x); ys.append(y)
        xn = rx * x * (1 - x)
        yn = ry * ((c * x + (1 - c) * y)) * (1 - (c * x + (1 - c) * y))
        x, y = xn, yn
    return np.array(xs), np.array(ys)


def best_E(series: np.ndarray, name: str, max_E: int = 6) -> int:
    n = len(series)
    df = pd.DataFrame({'time': range(1, n + 1), 'x': series})
    try:
        out = pyEDM.EmbedDimension(dataFrame=df, columns='x', target='x',
                                   maxE=max_E, Tp=1,
                                   lib=f'1 {n//2}', pred=f'{n//2+1} {n}',
                                   showPlot=False)
        e = int(out.loc[out['rho'].idxmax(), 'E'])
        print(f"    Simplex E [{name}] = {e} (rho={out['rho'].max():.3f})")
        return max(e, 2)
    except Exception as exc:
        print(f"    Simplex E [{name}] failed ({exc}) — default 2")
        return 2


def ccm_curve(cause: np.ndarray, effect: np.ndarray, E: int,
              sample: int = 200, n_lib: int | None = None):
    """Full rho-vs-L sweep in one pyEDM call."""
    n = min(len(cause), len(effect))
    df = pd.DataFrame({'time': range(1, n + 1),
                       'cause': cause[:n], 'effect': effect[:n]})
    step = n_lib or 4
    lo, hi = max(E + 2, 8), n - 2
    if hi <= lo:
        hi = lo + 1
    out = pyEDM.CCM(dataFrame=df, E=E, tau=-1,
                    columns='cause', target='effect',
                    libSizes=f'{lo} {hi} {step}',
                    sample=sample, seed=RANDOM_STATE, showPlot=False)
    col = 'cause:effect'
    Ls = out['LibSize'].values.astype(float)
    rhos = out[col].values.astype(float)
    return Ls, rhos


def pin_convention() -> str:
    """
    Ground truth: x causes y (unidirectional coupling).
    Sugihara logic: if X->Y then estimating X FROM Y's manifold has
    convergent skill. We test which output column lights up.
    Returns a verdict string used to label all real-data results.
    """
    print("\n" + "=" * 70)
    print("PART 1 — SYNTHETIC CONVENTION VALIDATION (ground truth: x causes y)")
    print("=" * 70)
    x, y = coupled_logistic()
    Ex = best_E(x, 'x-driver')
    Ey = best_E(y, 'y-respondent')

    _, rho_xy = ccm_curve(x, y, Ex)          # output column 'x:y'
    _, rho_yx = ccm_curve(y, x, Ey)          # output column 'y:x'
    conv = lambda r: float(np.polyfit(range(len(r)), r, 1)[0])

    print(f"\n  column 'x:y' : rho_final={rho_xy[-1]:+.3f}  conv_slope={conv(rho_xy):+.5f}")
    print(f"  column 'y:x' : rho_final={rho_yx[-1]:+.3f}  conv_slope={conv(rho_yx):+.5f}")

    if rho_xy[-1] > rho_yx[-1]:
        verdict = ("out[col:tgt] measures estimating COL from TGT's manifold "
                   "-> significant col:tgt is evidence that COL CAUSES TGT")
        mapping = "'A:B' significant => A causes B"
    else:
        verdict = ("out[col:tgt] measures estimating TGT from COL's manifold "
                   "-> significant col:tgt is evidence that TGT CAUSES COL")
        mapping = "'A:B' significant => B causes A"
    print(f"\n  VERDICT (empirical): {verdict}")
    print(f"  Reading rule for real data: {mapping}")
    return verdict


# ────────────────────────────────────────────────────────────────────────
# Part 2: corrected CCM on project series
# ────────────────────────────────────────────────────────────────────────

def phase_randomise(series: np.ndarray, n_surr: int, rng) -> np.ndarray:
    ft = np.fft.rfft(series)
    mags = np.abs(ft)
    surr = np.empty((n_surr, len(series)))
    for i in range(n_surr):
        phases = rng.uniform(0, 2 * np.pi, len(ft))
        surr[i] = np.fft.irfft(mags * np.exp(1j * phases), n=len(series))
    return surr


def stl_resid(s: pd.Series, period: int = 12) -> pd.Series:
    s = s.dropna()
    res = STL(s, period=period, robust=True).fit()
    return pd.Series(res.resid, index=s.index, name=s.name)


def load_remainders() -> dict[str, pd.Series]:
    anthro_v2 = pd.read_csv(PROCESSED_DIR / 'delta_S_anthro_v2.csv',
                            index_col=0, parse_dates=True)
    idx = anthro_v2.dropna(subset=['delta_S_anthro_bcm']).index

    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
                     parse_dates=['date']).set_index('date').sort_index()

    frame = pd.DataFrame(index=idx)
    frame['maithon']  = ts[ts['reservoir'] == 'maithon']['delta_S_obs_bcm']
    frame['durgapur'] = ts[ts['reservoir'] == 'durgapur']['delta_S_obs_bcm']
    frame['anthro']   = anthro_v2['delta_S_anthro_bcm']
    frame['climate']  = anthro_v2['delta_S_climate_bcm']
    frame = frame.loc[:, ~frame.columns.duplicated()]

    rems = {}
    for col in ['maithon', 'durgapur', 'anthro', 'climate']:
        rems[col] = stl_resid(frame[col].dropna())
    n_common = len(set.intersection(*[set(r.index) for r in rems.values()]))
    print(f"  Remainder overlap after STL alignment: {n_common} months")
    return {k: v.sort_index() for k, v in rems.items()}


def run_pair(name_a: str, name_b: str, rems: dict, n_surr: int,
             rows: list, lines: list):
    a = rems[name_a].dropna().values
    b = rems[name_b].dropna().values
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    rng = np.random.default_rng(RANDOM_STATE)

    for cols_name, cause, tgt_name, effect in [
            (name_a, a, name_b, b),      # direction A:B
            (name_b, b, name_a, a)]:     # direction B:A
        if not PYEDM_OK:
            break
        E = best_E(cause, f'{cols_name}(as columns)')
        Ls, rho_real = ccm_curve(cause, effect, E, sample=200)

        # matched null: each surrogate gets its own full curve
        surr_series = phase_randomise(cause, n_surr, rng)
        surr_rho = np.empty((n_surr, len(Ls)))
        for i in range(n_surr):
            try:
                _, rr = ccm_curve(surr_series[i].astype(float), effect, E,
                                  sample=20)
                surr_rho[i] = rr
            except Exception:
                surr_rho[i] = np.nan
        p95 = np.nanpercentile(surr_rho, 95, axis=0)

        exceeded = rho_real > p95
        frac = float(np.mean(exceeded))
        slope = float(np.polyfit(Ls, rho_real, 1)[0])
        sig = bool(frac >= 0.7 and slope > 0 and exceeded[-1])
        margin_L = float(rho_real[-1] - p95[-1])

        rows.extend({'pair': f'{name_a}->{name_b}', 'L': int(L), 
                     'rho_real': r, 'surr_p95': p, 'exceeded': bool(e)}
                    for L, r, p, e in zip(Ls, rho_real, p95, exceeded))
        lines.append(
            f"{name_a}->{name_b} (columns={cols_name}, E={E}): "
            f"rho[Lmax]={rho_real[-1]:+.3f} surr95[Lmax]={p95[-1]:+.3f} "
            f"margin={margin_L:+.3f} exceed_frac={frac:.2f} slope={slope:+.5f} "
            f"=> {'SIGNIFICANT ✓' if sig else 'ns'}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--surr', type=int, default=299,
                    help='number of phase-randomised surrogates (999 = protocol full)')
    args = ap.parse_args()

    print("=" * 70)
    print("FIX B4a — CCM direction check + corrected protocol (v2)")
    print("=" * 70)
    if not PYEDM_OK:
        print("pyEDM unavailable — cannot run.")
        return 1

    verdict = pin_convention()
    print("\n" + "=" * 70)
    print("PART 2 — REAL DATA (STL remainders, de-leaked residuals, "
          f"{args.surr} surrogates)")
    print("=" * 70)
    rems = load_remainders()

    rows, lines = [], []
    run_pair('maithon', 'durgapur', rems, args.surr, rows, lines)
    run_pair('anthro', 'climate', rems, args.surr, rows, lines)

    print()
    for ln in lines:
        print("  " + ln)

    df = pd.DataFrame(rows)
    out_csv = PROCESSED_DIR / 'ccm_results_v2.csv'
    df.to_csv(out_csv, index=False)

    txt = ["CCM v2 — corrected direction reading + matched-per-L surrogate nulls",
           f"Surrogates: {args.surr}; convention pinned empirically:",
           f"  {verdict}", "", "RESULTS:"] + ["  " + l for l in lines]
    (PROCESSED_DIR / 'ccm_summary_v2.txt').write_text("\n".join(txt) + "\n")

    print(f"\nSaved: {out_csv}")
    print("Saved: data/processed/ccm_summary_v2.txt")

    print("\n[V1 → V2 comparison notes]")
    print("  F-015 claimed Maithon→Durgapur SIGNIFICANT via max-rho vs single-size null;")
    print("  v2 requires consistent per-L exceedance + convergence under BOTH-direction audit.")
    print("  Interpret the printed direction labels using the empirical rule above.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
