"""
FIX B3 — De-leaked XGBoost attribution CV (v2)
===============================================
Defects fixed (RECOVERY_ROADMAP.md §1.1 B3 + §2 D3/D10, verified 2026-07-11):
  L1  v1 tune_xgboost() evaluated trials on the LAST 25% of the full series,
      which overlaps the expanding-window CV test folds (2019–2023).
      -> v2 tunes ONLY inside the first MIN_TRAIN_SIZE months; every tuning
         validation index ends strictly BEFORE the first outer test index.
  L2  v1 fitted every CV fold with eval_set=[(X_test, y_test)] and early
      stopping — the test fold steered training in all 4 folds.
      -> v2 early-stops on the tail 20% OF THE TRAINING WINDOW, then refits
         on the full training window at the selected n_estimators.
  L3  v1 imputed AET_mm with seasonal means computed over the FULL series
      (including future test months) before splitting.
      -> v2 imputes in-fold: month-of-year climatology from TRAIN rows only.
  L4  v1 computed SHAP on an in-sample final model.
      -> v2 computes SHAP per fold on that fold's own test rows (OOS-SHAP).
  L5  v1 pbias() returned normalised MAE (% of obs std) labelled "PBIAS".
      -> v2 reports true PBIAS = 100*sum(pred-obs)/sum(obs); the old metric is
         kept under its honest name nMAE_std.

Outputs (v1 files are NEVER overwritten):
    data/processed/xgb_cv_results_v2.csv
    data/processed/delta_S_anthro_v2.csv          (+ fold column)
    data/processed/delta_S_anthro_nolags_v2.csv
    data/processed/shap_values_oos_v2.csv
    data/processed/baseline_comparison_v2.csv
    figures/diag_deleak_pred_vs_obs.png

Run: uv run python src/03b_xgboost_deleak.py
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import xgboost as xgb
import shap
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
FIGURES_DIR   = PROJECT_ROOT / 'figures'

RANDOM_STATE       = 42
N_OPTUNA           = 150
MIN_TRAIN_SIZE     = 24     # must match v1 so folds are directly comparable
CV_STEP            = 12
DEAD_STORAGE_FLOOR_BCM = -0.183
TARGET_COL = 'delta_S_maithon_bcm'
FEATURE_ORDER = ['API6', 'PET_mm', 'AET_mm', 'DMI',
                 'dS_lag1', 'dS_lag3', 'Q_inflow_bcm', 'MO_anom']


# ═══════════════════════════════════════════════════════════════════
# METRICS (audited definitions)
# ═══════════════════════════════════════════════════════════════════

def nse(obs, pred):
    """Nash–Sutcliffe efficiency."""
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    if len(o) < 3:
        return np.nan
    denom = np.sum((o - o.mean()) ** 2)
    if denom < 1e-12:
        return np.nan
    return float(1.0 - np.sum((o - p) ** 2) / denom)


def kge(obs, pred):
    """
    Kling–Gupta efficiency. Variability term = coefficient-of-variation ratio
    (Kling et al. 2012 revised form) — IDENTICAL to v1 src/03 implementation so
    that v1-vs-v2 metric deltas reflect de-leaking only, never a redefinition.
    """
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    if len(o) < 3 or o.std() < 1e-12 or p.std() < 1e-12:
        return np.nan
    r = np.corrcoef(o, p)[0, 1]
    beta = p.mean() / o.mean() \
        if abs(o.mean()) > 1e-12 else np.nan
    gamma = (p.std() / p.mean()) / (o.std() / o.mean()) \
        if (abs(p.mean()) > 1e-12 and abs(o.mean()) > 1e-12) else np.nan
    if np.isnan(beta) or np.isnan(gamma):
        return np.nan
    return float(1 - np.sqrt((r - 1) ** 2 + (gamma - 1) ** 2 + (beta - 1) ** 2))


def pbias_true(obs, pred):
    """
    TRUE percent bias: 100 * sum(pred - obs) / sum(obs).
    Undefined when sum(obs) ~ 0 — storage ANOMALY sums can legitimately be
    near zero, so NaN is returned rather than an explosive number.
    """
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    denom = o.sum()
    if abs(denom) < 1e-6 or len(o) < 3:
        return np.nan
    return float(100.0 * (p - o).sum() / denom)


def nmae_std(obs, pred):
    """Mean absolute error normalised by obs std (the v1 'pbias', renamed)."""
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    sd = o.std()
    return float(100.0 * np.mean(np.abs(o - p)) / sd) if sd > 1e-12 else np.nan


def all_metrics(obs, pred):
    return {'NSE': nse(obs, pred), 'KGE': kge(obs, pred),
            'PBIAS': pbias_true(obs, pred), 'nMAE_std': nmae_std(obs, pred)}


# ═══════════════════════════════════════════════════════════════════
# DATA (same loading as v1 minus the global pre-split imputation)
# ═══════════════════════════════════════════════════════════════════

def load_data(feature_order=FEATURE_ORDER) -> tuple[pd.DataFrame, pd.Series]:
    x_path = PROCESSED_DIR / 'X_climate_final.csv'
    X_full = pd.read_csv(x_path, index_col=0, parse_dates=True)
    X_full.index = pd.to_datetime(X_full.index)
    X_full = X_full.sort_index()

    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
                     parse_dates=['date'])
    ts = ts[ts['reservoir'] == 'maithon'][['date', 'delta_S_obs_bcm']].copy()
    ts = ts.set_index('date').sort_index()
    ts.columns = [TARGET_COL]

    df = X_full.join(ts, how='left').loc['2017-01-01':]
    df = df.dropna(subset=[TARGET_COL])

    feats = [f for f in feature_order if f in df.columns]
    missing = [f for f in feature_order if f not in df.columns]
    if missing:
        print(f"  WARNING features absent from matrix: {missing}")
    X = df[feats].copy()
    y = df[TARGET_COL]

    # NOTE: NO imputation here. AET imputation happens in-fold (leak fix L3).
    print(f"  Loaded {len(X)} S1-era rows | features: {list(X.columns)}")
    for col in X.columns:
        n_nan = X[col].isna().sum()
        if n_nan:
            print(f"    {col}: {n_nan} NaN ({100*n_nan/len(X):.0f}%) left to in-fold handling")
    return X, y


# ═══════════════════════════════════════════════════════════════════
# IN-FOLD IMPUTATION (fixes leak L3)
# ═══════════════════════════════════════════════════════════════════

def impute_infold(X_train: pd.DataFrame, X_test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Month-of-year climatology fitted on TRAIN rows only; global train mean fallback."""
    tr, te = X_train.copy(), X_test.copy()
    stats = {}
    for col in tr.columns:
        if tr[col].isna().any() or te[col].isna().any():
            mo = tr.groupby(tr.index.month)[col].mean()
            gm = tr[col].mean()
            stats[col] = {'months_imputed_from_train_clim': True}
            for frame in (tr, te):
                month_of_row = pd.Series(frame.index.month, index=frame.index)
                filled = frame[col].fillna(month_of_row.map(mo))
                frame[col] = filled.fillna(gm)
    return tr, te


# ═══════════════════════════════════════════════════════════════════
# MODEL FITTING WITH TRAIN-TAIL EARLY STOPPING (fixes leak L2)
# ═══════════════════════════════════════════════════════════════════

def fit_with_train_tail_es(X_tr: pd.DataFrame, y_tr: np.ndarray,
                           params: dict, es_frac: float = 0.2):
    """
    Early-stop on the tail es_frac of the TRAINING window, then refit on the
    FULL training window at the selected number of boosting rounds.
    The test fold is never touched.
    Returns (final_model, best_iteration).
    """
    n = len(y_tr)
    n_es = max(3, int(round(n * es_frac)))
    fit_idx = list(range(n - n_es))
    es_idx  = list(range(n - n_es, n))

    es_params = dict(params)
    es_params['early_stopping_rounds'] = 20
    probe = xgb.XGBRegressor(**es_params)
    probe.fit(X_tr.iloc[fit_idx], y_tr[fit_idx],
              eval_set=[(X_tr.iloc[es_idx], y_tr[es_idx])],
              verbose=False)
    best_iter = int(getattr(probe, 'best_iteration', params.get('n_estimators', 100)))

    final_params = dict(params)
    final_params['n_estimators'] = max(best_iter + 1, 20)
    model = xgb.XGBRegressor(**final_params)
    model.fit(X_tr, y_tr, verbose=False)
    return model, best_iter


# ═══════════════════════════════════════════════════════════════════
# TUNING CONFINED TO PRE-CV REGION (fixes leak L1)
# ═══════════════════════════════════════════════════════════════════

TUNE_SPLITS = [((0, 14), (14, 19)),   # inner expanding splits INSIDE first 24 months
               ((0, 17), (17, 24))]   # all indices < MIN_TRAIN_SIZE by construction


def tune_deleak(X: pd.DataFrame, y: pd.Series, n_trials: int = N_OPTUNA) -> dict:
    print(f"\n[TUNE] Optuna confined to months [0, {MIN_TRAIN_SIZE}) "
          f"— ends BEFORE first outer test index ({MIN_TRAIN_SIZE})")
    assert max(e for _, (_, e) in TUNE_SPLITS) <= MIN_TRAIN_SIZE

    def objective(trial):
        params = sample_params(trial)
        scores = []
        for (a, b), (c, d) in TUNE_SPLITS:
            X_tr, X_val = X.iloc[a:b], X.iloc[c:d]
            y_tr, y_val = y.values[a:b], y.values[c:d]
            X_tr_i, X_val_i = impute_infold(X_tr, X_val)
            try:
                model, _ = fit_with_train_tail_es(X_tr_i, y_tr, params)
                scores.append(nse(y_val, model.predict(X_val_i)))
            except Exception:
                scores.append(np.nan)
        s = np.array(scores, dtype=float)
        return float(np.nanmean(s)) if np.isfinite(s).any() else -999.0

    study = optuna.create_study(direction='maximize',
                                sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=True)
    best = study.best_params
    best.update({'random_state': RANDOM_STATE, 'tree_method': 'hist', 'verbosity': 0})
    print(f"  Best inner-CV NSE: {study.best_value:.4f}")
    print(f"  Params: n_est={best['n_estimators']} depth={best['max_depth']} "
          f"lr={best['learning_rate']:.4f}")
    return best


def sample_params(trial) -> dict:
    return {
        'n_estimators':     trial.suggest_int('n_estimators', 50, 500),
        'max_depth':        trial.suggest_int('max_depth', 2, 8),
        'learning_rate':    trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample':        trial.suggest_float('subsample', 0.5, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.4, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'reg_alpha':        trial.suggest_float('reg_alpha', 1e-4, 10.0, log=True),
        'reg_lambda':       trial.suggest_float('reg_lambda', 1e-4, 10.0, log=True),
        'random_state': RANDOM_STATE, 'tree_method': 'hist', 'verbosity': 0,
    }


# ═══════════════════════════════════════════════════════════════════
# EXPANDING-WINDOW CV (de-leaked)
# ═══════════════════════════════════════════════════════════════════

def expanding_window_splits(n: int, min_train: int = MIN_TRAIN_SIZE,
                            step: int = CV_STEP):
    splits, train_end = [], min_train
    while train_end + step <= n:
        splits.append((list(range(train_end)),
                       list(range(train_end, min(train_end + step, n)))))
        train_end += step
    return splits


def run_cv(X, y, best_params, collect_shap=True):
    splits = expanding_window_splits(len(X))
    dates = y.index
    records, shap_frames = [], []
    oos = np.full(len(y), np.nan)
    oos_fold = np.full(len(y), np.nan)

    print(f"\n[CV] {len(splits)} folds | min_train={MIN_TRAIN_SIZE} step={CV_STEP} "
          f"| ES on train tail only")
    for fi, (tr_idx, te_idx) in enumerate(splits, start=1):
        X_tr_raw, X_te_raw = X.iloc[tr_idx], X.iloc[te_idx]
        y_tr, y_te = y.values[tr_idx], y.values[te_idx]

        # L3 fix: imputation statistics from THIS training window only
        X_tr, X_te = impute_infold(X_tr_raw, X_te_raw)

        # L2 fix: early stopping on train tail, refit, predict test
        model, best_iter = fit_with_train_tail_es(X_tr, y_tr, best_params)
        pred = model.predict(X_te)

        m_all = all_metrics(y_te, pred)
        clip_mask = y_te > DEAD_STORAGE_FLOOR_BCM
        m_uc = (all_metrics(y_te[clip_mask], pred[clip_mask])
                if clip_mask.sum() >= 3 else
                {'k': np.nan for k in ('NSE', 'KGE', 'PBIAS', 'nMAE_std')})

        records.append({
            'fold': fi, 'train_months': len(tr_idx), 'test_months': len(te_idx),
            'train_start': dates[tr_idx[0]].date(), 'train_end': dates[tr_idx[-1]].date(),
            'test_start': dates[te_idx[0]].date(), 'test_end': dates[te_idx[-1]].date(),
            'best_iteration': best_iter,
            **{f'{k}': v for k, v in m_all.items()},
            'n_unclipped': int(clip_mask.sum()),
            **{f'{k}_unclipped': v for k, v in m_uc.items()},
        })
        for j, idx in enumerate(te_idx):
            oos[idx] = pred[j]
            oos_fold[idx] = fi

        if collect_shap:
            sv = shap.TreeExplainer(model).shap_values(X_te)
            shap_frames.append(pd.DataFrame(sv, index=X_te.index, columns=X_te.columns))
            print(f"  fold {fi}: train={len(tr_idx)} test={len(te_idx)} | "
                  f"NSE={m_all['NSE']:+.3f} NSE_unc={m_uc['NSE']:+.3f} "
                  f"PBIAS={m_all['PBIAS']} best_iter={best_iter}")

    cv = pd.DataFrame(records)
    y_pred_oos = pd.Series(oos, index=y.index, name='pred')
    fold_of = pd.Series(oos_fold, index=y.index, name='fold')
    shap_oos = (pd.concat(shap_frames).sort_index()
                if shap_frames else pd.DataFrame(index=y.index))
    return cv, y_pred_oos, fold_of, shap_oos


# ═══════════════════════════════════════════════════════════════════
# LEAKAGE-FREE BASELINES
# ═══════════════════════════════════════════════════════════════════

def baseline_predictions(X, y):
    """Persistence / climatology / zero under the identical OOS framework."""
    splits = expanding_window_splits(len(X))
    preds = {name: np.full(len(y), np.nan)
             for name in ('persistence', 'climatology', 'zero')}
    for tr_idx, te_idx in splits:
        y_tr = y.values[tr_idx]
        mo_means = (y.iloc[tr_idx].groupby(y.iloc[tr_idx].index.month).mean())
        gmean = y_tr.mean()
        for i in te_idx:
            preds['zero'][i] = 0.0
            preds['climatology'][i] = mo_means.get(y.index[i].month, gmean)
            if i > 0 and np.isfinite(y.values[i - 1]):
                preds['persistence'][i] = y.values[i - 1]
    out = {}
    for name, arr in preds.items():
        mask = np.isfinite(arr)
        m = all_metrics(y.values[mask], arr[mask])
        out[name] = {'n': int(mask.sum()), **{k: v for k, v in m.items()}}
    return out


# ═══════════════════════════════════════════════════════════════════
# BOOTSTRAP CI (v2: reuses de-leak CV structure; seeds vary stochasticity)
# ═══════════════════════════════════════════════════════════════════

def bootstrap_anthro_ci(X, y, best_params, n_boot=50):
    resid_frames = []
    for seed in range(n_boot):
        params_seed = {**best_params, 'random_state': seed}
        _, y_pred, _, _ = run_cv(X, y, params_seed, collect_shap=False)
        resid_frames.append((y - y_pred).rename(seed))
    boot = pd.concat(resid_frames, axis=1).dropna()
    ci = pd.DataFrame({
        'delta_S_anthro_mean':  boot.mean(axis=1),
        'delta_S_anthro_ci_lo': boot.quantile(0.025, axis=1),
        'delta_S_anthro_ci_hi': boot.quantile(0.975, axis=1),
        'delta_S_anthro_std':   boot.std(axis=1),
    })
    lo, hi = ci['delta_S_anthro_mean'].min(), ci['delta_S_anthro_mean'].max()
    width = (ci['delta_S_anthro_ci_hi'] - ci['delta_S_anthro_ci_lo']).mean()
    print(f"  Bootstrap mean range [{lo:.4f}, {hi:.4f}] BCM | mean CI width ±{width/2:.4f}")
    return ci


# ═══════════════════════════════════════════════════════════════════
# DIAGNOSTIC FIGURE
# ═══════════════════════════════════════════════════════════════════

def plot_diag(y, y_pred, anthro_df, out_path):
    fig, axes = plt.subplots(2, 1, figsize=(13, 8), sharex=True,
                             gridspec_kw={'height_ratios': [2, 1]})
    ax = axes[0]
    ax.plot(y.index, y.values, color='#1f77b4', lw=1.5, label='ΔS_obs')
    ax.plot(y_pred.index, y_pred.values, color='#ff7f0e', lw=1.5, ls='--',
            label='ΔS_climate (de-leaked XGBoost OOS)')
    ax.axhline(0, color='gray', lw=0.6, ls=':')
    ax.set_ylabel('Storage anomaly (BCM)')
    ax.set_title('De-leaked expanding-window CV (B3 fix)\n'
                 'tuning < first test date · ES on train tails · in-fold imputation')
    ax.legend(fontsize=9)
    ax2 = axes[1]
    anthro = anthro_df['delta_S_anthro_bcm'].dropna()
    ax2.fill_between(anthro.index, anthro.values, 0, where=(anthro.values >= 0),
                     alpha=0.6, color='#2ca02c', label='ΔS_anthro ≥ 0')
    ax2.fill_between(anthro.index, anthro.values, 0, where=(anthro.values < 0),
                     alpha=0.6, color='#d62728', label='ΔS_anthro < 0')
    ax2.axhline(0, color='gray', lw=0.8)
    ax2.set_ylabel('ΔS_anthro (BCM)')
    ax2.legend(fontsize=8, loc='lower left')
    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

def main():
    t0 = datetime.now()
    print("=" * 68)
    print("FIX B3 — de-leaked XGBoost attribution (v2)")
    print(f"Started: {t0:%Y-%m-%d %H:%M:%S}")
    print("=" * 68)

    X, y = load_data()

    # ── leakage audit before anything runs ────────────────────────────
    tune_max = max(e for _, (_, e) in TUNE_SPLITS)
    first_test = MIN_TRAIN_SIZE
    print("\n[LEAKAGE AUDIT]")
    print(f"  L1 tuning region: indices [0,{tune_max}) | first outer test index: {first_test}"
          f"  -> overlap = {max(0, tune_max - first_test)} rows "
          f"{'OK ✓' if tune_max <= first_test else 'LEAK ✗'}")

    best = tune_deleak(X, y)
    cv, y_pred_oos, fold_of, shap_oos = run_cv(X, y, best)

    anthro = pd.DataFrame({
        'delta_S_obs_bcm': y,
        'delta_S_climate_bcm': y_pred_oos,
        'fold': fold_of,
    })
    anthro['delta_S_anthro_bcm'] = anthro['delta_S_obs_bcm'] - anthro['delta_S_climate_bcm']
    anthro['reservoir'] = 'maithon'

    valid = anthro.dropna(subset=['delta_S_anthro_bcm'])
    print(f"\n[RESIDUAL] ΔS_anthro rows={len(valid)} "
          f"range=[{valid.delta_S_anthro_bcm.min():+.4f}, {valid.delta_S_anthro_bcm.max():+.4f}] "
          f"mean={valid.delta_S_anthro_bcm.mean():+.4f} BCM")

    # pooled OOS metrics
    mask = y_pred_oos.notna().values
    pooled = all_metrics(y.values[mask], y_pred_oos.values[mask])
    uc = y.values[mask] > DEAD_STORAGE_FLOOR_BCM
    pooled_uc = all_metrics(y.values[mask][uc], y_pred_oos.values[mask][uc])
    print("\n[POOLED OOS — all rows]    " +
          " ".join(f"{k}={v:.4f}" if v == v else f"{k}=nan" for k, v in pooled.items()))
    print(f"[POOLED OOS — unclipped n={uc.sum()}] " +
          " ".join(f"{k}={v:.4f}" if v == v else f"{k}=nan" for k, v in pooled_uc.items()))

    baselines = baseline_predictions(X, y)
    base_rows = []
    for name, m in baselines.items():
        print(f"[BASELINE {name:<13}] n={m['n']} " +
              " ".join(f"{k}={v:.4f}" if v == v else f"{k}=nan" for k, v in m.items()))
        base_rows.append({'model': name, **m})
    base_rows.append({'model': 'xgboost_deleak_pooled',
                      'n': int(mask.sum()),
                      **{k: v for k, v in pooled.items()}})
    pd.DataFrame(base_rows).to_csv(PROCESSED_DIR / 'baseline_comparison_v2.csv', index=False)

    # no-lag sensitivity (same de-leak protocol, lag features removed)
    lag_cols = [c for c in X.columns if 'lag' in c.lower()]
    if lag_cols:
        X_nl = X.drop(columns=lag_cols)
        best_nl = tune_deleak(X_nl, y, n_trials=N_OPTUNA)
        cv_nl, y_pred_nl, fold_nl, shap_nl = run_cv(X_nl, y, best_nl)
        anthro_nl = pd.DataFrame({
            'delta_S_obs_bcm': y, 'delta_S_climate_bcm': y_pred_nl, 'fold': fold_nl,
            'reservoir': 'maithon'})
        anthro_nl['delta_S_anthro_bcm'] = anthro_nl.delta_S_obs_bcm - anthro_nl.delta_S_climate_bcm
        m_nl = y_pred_nl.notna().values
        pooled_nl = all_metrics(y.values[m_nl], y_pred_nl.values[m_nl])
        print(f"\n[NO-LAG POOLED] NSE={pooled_nl['NSE']:.4f} "
              f"(full-model {pooled['NSE']:.4f}; lag boost {pooled['NSE']-pooled_nl['NSE']:+.4f})")

    # bootstrap CI (full-feature model, de-leak structure, 50 seeds)
    boot = bootstrap_anthro_ci(X, y, best, n_boot=50)

    # ── save v2 outputs (never overwrite v1) ──────────────────────────
    cv.to_csv(PROCESSED_DIR / 'xgb_cv_results_v2.csv', index=False)
    anthro.to_csv(PROCESSED_DIR / 'delta_S_anthro_v2.csv')
    shap_oos.to_csv(PROCESSED_DIR / 'shap_values_oos_v2.csv')
    boot.to_csv(PROCESSED_DIR / 'delta_S_anthro_bootstrap_ci_v2.csv')
    if lag_cols:
        anthro_nl.to_csv(PROCESSED_DIR / 'delta_S_anthro_nolags_v2.csv')

    imp = shap_oos.abs().mean().sort_values(ascending=False)
    print("\n[OOS-SHAP importance — mean |SHAP| across 48 OOS rows]")
    total = imp.sum()
    for feat, val in imp.items():
        print(f"  {feat:<16} {val:.4f} BCM  ({100*val/total if total else 0:.1f}%)")

    plot_diag(y, y_pred_oos, anthro, FIGURES_DIR / 'diag_deleak_pred_vs_obs.png')

    # ── v1 vs v2 comparison ───────────────────────────────────────────
    print("\n[V1 → V2 COMPARISON]")
    try:
        v1 = pd.read_csv(PROCESSED_DIR / 'baseline_comparison.csv')
        pers_v1 = v1[v1['model'].str.contains('ersist')].iloc[0]
        print(f"  v1 persistence NSE_all={pers_v1['NSE_all']} | "
              f"v2 persistence NSE={baselines['persistence']['NSE']:.4f}")
        v1cv = pd.read_csv(PROCESSED_DIR / 'xgb_cv_results.csv')
        print(f"  v1 XGB fold-mean NSE={v1cv['NSE'].dropna().mean():.4f} "
              f"NSE_unclipped={v1cv['NSE_unclipped'].dropna().mean():.4f}")
    except Exception as e:
        print(f"  (v1 files not readable here: {e})")
    print(f"  v2 XGB pooled NSE_all={pooled['NSE']:.4f} "
          f"NSE_unclipped={pooled_uc['NSE']:.4f} (n_unclipped={int(uc.sum())})")

    print(f"\nFinished: {datetime.now():%Y-%m-%d %H:%M:%S}  (elapsed {(datetime.now()-t0).seconds}s)")
    print("NOTE: v2 metrics replace v1 as paper-reportable once geometry rebuild lands.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
