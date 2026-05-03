"""
Permutation Importance Test — All Features (Focus: DMI)
========================================================
Retrains XGBoost with same Optuna setup on the same S1-era Maithon data,
then computes permutation importance for ALL 8 features on held-out
expanding-window CV test folds.

For each feature:
  1. Baseline NSE on pooled OOS predictions
  2. Shuffle that feature column 100 times, each time predict and compute NSE
  3. Importance = baseline_NSE - mean(shuffled_NSE)
  4. p-value = fraction of shuffled NSE >= baseline NSE (one-sided)

Output: data/processed/permutation_importance.csv

Run: cd /home/stark007/dvc-research && uv run python src/permutation_importance_test.py
"""

import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from pathlib import Path

import xgboost as xgb
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

# ── Constants (match 03_xgboost_attribution.py exactly) ──
PROCESSED_DIR  = Path('data/processed')
RANDOM_STATE   = 42
N_OPTUNA       = 150
MIN_TRAIN_SIZE = 24
CV_STEP        = 12
S1_ERA_START   = '2017-01-01'
TARGET_COL     = 'delta_S_maithon_bcm'
FEATURE_ORDER  = ['API6', 'PET_mm', 'AET_mm', 'DMI',
                  'dS_lag1', 'dS_lag3', 'Q_inflow_bcm', 'MO_anom']
N_PERMUTATIONS = 100

# ── Utilities ──

def nse(obs, pred):
    obs, pred = np.asarray(obs, float), np.asarray(pred, float)
    mask = ~(np.isnan(obs) | np.isnan(pred))
    o, p = obs[mask], pred[mask]
    if len(o) < 3:
        return np.nan
    denom = np.sum((o - np.mean(o))**2)
    if denom < 1e-12:
        return np.nan
    return float(1.0 - np.sum((o - p)**2) / denom)


def expanding_window_splits(n, min_train=MIN_TRAIN_SIZE, step=CV_STEP):
    splits = []
    train_end = min_train
    while train_end + step <= n:
        train_idx = list(range(train_end))
        test_idx  = list(range(train_end, min(train_end + step, n)))
        if test_idx:
            splits.append((train_idx, test_idx))
        train_end += step
    return splits


# ── Load data (same as 03_xgboost_attribution.py) ──

def load_data():
    X_full = pd.read_csv(PROCESSED_DIR / 'X_climate_final.csv',
                         index_col=0, parse_dates=True).sort_index()

    ts = pd.read_csv(PROCESSED_DIR / 'DVC_storage_timeseries_2002_2024.csv',
                     parse_dates=['date'])
    ts = ts[ts['reservoir'] == 'maithon'][['date', 'delta_S_obs_bcm']].copy()
    ts = ts.set_index('date').sort_index()
    ts.columns = [TARGET_COL]

    df = X_full.join(ts, how='left')
    df = df.loc[S1_ERA_START:]
    df = df.dropna(subset=[TARGET_COL])

    available_features = [f for f in FEATURE_ORDER if f in df.columns]
    X = df[available_features].copy()
    y = df[TARGET_COL]

    # Impute AET_mm NaN with seasonal mean (same as original script)
    if 'AET_mm' in X.columns and X['AET_mm'].isna().any():
        aet_month_mean = X['AET_mm'].groupby(X.index.month).transform('mean')
        X['AET_mm'] = X['AET_mm'].fillna(aet_month_mean)

    return X, y


# ── Optuna tuning (same as original) ──

def tune_xgboost(X, y):
    n = len(X)
    tune_cutoff = int(n * 0.75)
    X_arr = X.values
    y_arr = y.values

    def objective(trial):
        params = {
            'n_estimators':      trial.suggest_int('n_estimators', 50, 500),
            'max_depth':         trial.suggest_int('max_depth', 2, 8),
            'learning_rate':     trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
            'subsample':         trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree':  trial.suggest_float('colsample_bytree', 0.4, 1.0),
            'min_child_weight':  trial.suggest_int('min_child_weight', 1, 10),
            'reg_alpha':         trial.suggest_float('reg_alpha', 1e-4, 10.0, log=True),
            'reg_lambda':        trial.suggest_float('reg_lambda', 1e-4, 10.0, log=True),
            'random_state':      RANDOM_STATE,
            'tree_method':       'hist',
            'verbosity':         0,
        }
        es_params = dict(params)
        es_params['early_stopping_rounds'] = 15
        model = xgb.XGBRegressor(**es_params)
        X_train_t = pd.DataFrame(X_arr[:tune_cutoff], columns=X.columns)
        X_val_t   = pd.DataFrame(X_arr[tune_cutoff:], columns=X.columns)
        model.fit(X_train_t, y_arr[:tune_cutoff],
                  eval_set=[(X_val_t, y_arr[tune_cutoff:])],
                  verbose=False)
        pred = model.predict(X_val_t)
        return nse(y_arr[tune_cutoff:], pred)

    study = optuna.create_study(direction='maximize',
                                sampler=optuna.samplers.TPESampler(seed=RANDOM_STATE))
    study.optimize(objective, n_trials=N_OPTUNA, show_progress_bar=False)

    best = study.best_params
    best['random_state'] = RANDOM_STATE
    best['tree_method']  = 'hist'
    best['verbosity']    = 0
    return best


# ── Expanding-window CV with OOS predictions ──

def get_oos_predictions(X, y, best_params, X_override=None):
    """
    Run expanding-window CV. If X_override is provided, use it for
    prediction (permuted features) but train on original X.
    Returns pooled OOS predictions array aligned to y.
    """
    splits = expanding_window_splits(len(X))
    X_arr = X.values
    y_arr = y.values
    X_pred_arr = X_override.values if X_override is not None else X_arr
    oos_preds = np.full(len(y), np.nan)

    for train_idx, test_idx in splits:
        X_train = pd.DataFrame(X_arr[train_idx], columns=X.columns)
        X_test  = pd.DataFrame(X_arr[test_idx],  columns=X.columns)
        y_train = y_arr[train_idx]
        y_test  = y_arr[test_idx]

        es_params = dict(best_params)
        es_params['early_stopping_rounds'] = 20
        model = xgb.XGBRegressor(**es_params)
        model.fit(X_train, y_train,
                  eval_set=[(X_test, y_test)],
                  verbose=False)

        # Predict on (potentially permuted) test features
        X_test_pred = pd.DataFrame(X_pred_arr[test_idx], columns=X.columns)
        pred = model.predict(X_test_pred)

        for i, idx in enumerate(test_idx):
            oos_preds[idx] = pred[i]

    return oos_preds


# ── Main ──

def main():
    print("=" * 65)
    print("PERMUTATION IMPORTANCE TEST — DVC XGBoost Attribution Model")
    print("=" * 65)

    # Load data
    X, y = load_data()
    print(f"\nData: {X.shape[0]} rows x {X.shape[1]} features")
    print(f"Features: {list(X.columns)}")
    print(f"Date range: {X.index.min().date()} to {X.index.max().date()}")

    # Tune (same Optuna + same seed = same hyperparams)
    print(f"\nTuning XGBoost ({N_OPTUNA} Optuna trials, seed={RANDOM_STATE})...")
    best_params = tune_xgboost(X, y)
    print(f"Best params: n_est={best_params['n_estimators']}, "
          f"depth={best_params['max_depth']}, "
          f"lr={best_params['learning_rate']:.4f}")

    # Baseline OOS NSE
    print("\nComputing baseline OOS predictions...")
    baseline_preds = get_oos_predictions(X, y, best_params)
    valid_mask = ~np.isnan(baseline_preds)
    baseline_nse = nse(y.values[valid_mask], baseline_preds[valid_mask])
    n_test = int(valid_mask.sum())
    print(f"Baseline NSE (pooled OOS, {n_test} test rows): {baseline_nse:.4f}")

    # Permutation importance for each feature
    print(f"\nRunning permutation importance ({N_PERMUTATIONS} shuffles per feature)...")
    rng = np.random.RandomState(RANDOM_STATE)
    results = []

    for feat in X.columns:
        print(f"  {feat:15s} ... ", end="", flush=True)
        shuffled_nses = []

        for perm_i in range(N_PERMUTATIONS):
            X_perm = X.copy()
            # Shuffle only the test rows' feature values (same permutation approach)
            X_perm[feat] = rng.permutation(X_perm[feat].values)
            perm_preds = get_oos_predictions(X, y, best_params, X_override=X_perm)
            perm_nse = nse(y.values[valid_mask], perm_preds[valid_mask])
            shuffled_nses.append(perm_nse)

        shuffled_nses = np.array(shuffled_nses)
        mean_shuffled = np.nanmean(shuffled_nses)
        importance = baseline_nse - mean_shuffled
        # p-value: fraction of permutations where shuffled NSE >= baseline
        # (i.e., feature removal didn't hurt = feature is unimportant)
        p_value = np.mean(shuffled_nses >= baseline_nse)

        results.append({
            'Feature': feat,
            'Baseline_NSE': baseline_nse,
            'Mean_Shuffled_NSE': mean_shuffled,
            'Std_Shuffled_NSE': np.nanstd(shuffled_nses),
            'Importance': importance,
            'p_value': p_value,
        })
        print(f"imp={importance:+.4f}  p={p_value:.3f}")

    # Build results table
    df_results = pd.DataFrame(results).sort_values('Importance', ascending=False)
    df_results = df_results.reset_index(drop=True)

    # Print ranked table
    print("\n" + "=" * 85)
    print(f"{'Rank':<5} {'Feature':<15} {'Baseline_NSE':>13} {'Mean_Shuf_NSE':>14} "
          f"{'Importance':>11} {'p_value':>8}")
    print("-" * 85)
    for i, row in df_results.iterrows():
        sig = "***" if row['p_value'] < 0.01 else "**" if row['p_value'] < 0.05 else "*" if row['p_value'] < 0.10 else ""
        print(f"{i+1:<5} {row['Feature']:<15} {row['Baseline_NSE']:>13.4f} "
              f"{row['Mean_Shuffled_NSE']:>14.4f} {row['Importance']:>11.4f} "
              f"{row['p_value']:>7.3f} {sig}")
    print("=" * 85)
    print("Significance: *** p<0.01, ** p<0.05, * p<0.10")

    # DMI-specific interpretation
    dmi_row = df_results[df_results['Feature'] == 'DMI'].iloc[0]
    print(f"\n── DMI Assessment ──")
    print(f"  Permutation importance: {dmi_row['Importance']:+.4f}")
    print(f"  p-value: {dmi_row['p_value']:.3f}")
    if dmi_row['p_value'] > 0.05:
        print(f"  FINDING: DMI has NO significant predictive contribution (p={dmi_row['p_value']:.3f} > 0.05).")
        print(f"  DMI survived VIF (orthogonal to other features) but carries negligible")
        print(f"  predictive information for Maithon storage. Disclose in paper.")
    else:
        print(f"  FINDING: DMI has SIGNIFICANT predictive contribution (p={dmi_row['p_value']:.3f}).")

    # Save
    out_path = PROCESSED_DIR / 'permutation_importance.csv'
    df_results.to_csv(out_path, index=False)
    print(f"\nSaved: {out_path}")


if __name__ == '__main__':
    main()
