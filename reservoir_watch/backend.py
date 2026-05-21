import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "processed"

DAM_META = {
    "maithon": {
        "name": "Maithon Dam",
        "lat": 23.835, "lon": 86.821,
        "capacity_bcm": 1.360,
        "function": "Flood control + hydropower",
        "catchment_km2": 6294,
        "river": "Barakar",
        "commissioned": 1957,
    },
    "panchet": {
        "name": "Panchet Dam",
        "lat": 23.577, "lon": 86.769,
        "capacity_bcm": 0.290,
        "function": "Tandem flood control + power",
        "catchment_km2": 10966,
        "river": "Damodar",
        "commissioned": 1959,
    },
    "durgapur": {
        "name": "Durgapur Barrage",
        "lat": 23.487, "lon": 87.307,
        "capacity_bcm": None,
        "function": "Irrigation (run-of-river)",
        "catchment_km2": 18920,
        "river": "Damodar",
        "commissioned": 1955,
    },
}

REGIME_COLORS = {
    "Fill":         "#1565c0",
    "Release":      "#c62828",
    "Drawdown":     "#e65100",
    "Conservation": "#6a1b9a",
}

KNOWN_EVENTS = [
    {"date": "2009-09", "label": "2009 Damodar Flood",  "reservoir": "maithon",  "severity": "high"},
    {"date": "2009-09", "label": "2009 Damodar Flood",  "reservoir": "panchet",  "severity": "high"},
    {"date": "2015-07", "label": "El Niño Drought",     "reservoir": "maithon",  "severity": "medium"},
    {"date": "2015-07", "label": "El Niño Drought",     "reservoir": "panchet",  "severity": "medium"},
    {"date": "2015-07", "label": "El Niño Drought",     "reservoir": "durgapur", "severity": "medium"},
]


def load_storage_timeseries(reservoir: str) -> pd.DataFrame:
    fp = DATA_DIR / "DVC_storage_timeseries_2002_2024.csv"
    df = pd.read_csv(fp, parse_dates=["date"])
    df = df[df["reservoir"] == reservoir].copy().reset_index(drop=True)
    df = df.sort_values("date").reset_index(drop=True)
    # Normalise anomaly: use delta_S_obs_p50 if obs is missing
    if "delta_S_obs_bcm" not in df.columns:
        df["delta_S_obs_bcm"] = np.nan
    if df["delta_S_obs_bcm"].isna().all() and "delta_S_obs_p50" in df.columns:
        df["delta_S_obs_bcm"] = df["delta_S_obs_p50"]
    return df


def _classify_regime(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["month"] = df["date"].dt.month

    area_col = "water_area_km2"
    anom_col = "delta_S_obs_bcm"

    # Normalised area anomaly as fallback signal
    area_mean = df[area_col].replace(0, np.nan).mean()
    df["area_norm"] = (df[area_col] - area_mean) / (area_mean + 1e-6)

    # Month-over-month change in water area (negative = rapid drop)
    df["area_chg"] = df[area_col].diff()

    labels, confidences = [], []
    for _, row in df.iterrows():
        m = row["month"]
        anom = row[anom_col] if not pd.isna(row[anom_col]) else row["area_norm"] * 0.1
        chg  = row["area_chg"] if not pd.isna(row["area_chg"]) else 0.0

        if chg < -5 and m in [7, 8, 9, 10]:        # sharp area drop during/after monsoon
            labels.append("Release")
            confidences.append(0.78)
        elif m in [6, 7, 8, 9] and anom > 0.01:    # monsoon + above-average storage
            labels.append("Fill")
            confidences.append(0.82)
        elif m in [10, 11, 12, 1, 2, 3] and anom < -0.01:
            labels.append("Drawdown")
            confidences.append(0.80)
        else:
            labels.append("Conservation")
            confidences.append(0.70)

    df["regime_label"] = labels
    df["confidence"]   = confidences
    df["regime_color"] = df["regime_label"].map(REGIME_COLORS)
    return df


def get_regime_timeseries(reservoir: str) -> pd.DataFrame:
    df = load_storage_timeseries(reservoir)
    df = _classify_regime(df)
    return df[["date", "water_area_km2", "delta_S_obs_bcm",
               "regime_label", "confidence", "regime_color"]].copy()


def get_current_regime(reservoir: str) -> dict:
    df = get_regime_timeseries(reservoir)
    df = df.dropna(subset=["water_area_km2"])
    if df.empty:
        return {"regime": "Unknown", "confidence": 0.0, "updated": "N/A", "delta_s": None}
    row = df.iloc[-1]
    return {
        "regime":     row["regime_label"],
        "confidence": row["confidence"],
        "updated":    row["date"].strftime("%B %Y"),
        "delta_s":    row["delta_S_obs_bcm"],
        "color":      row["regime_color"],
    }


def get_model_metrics() -> dict:
    fp = DATA_DIR / "xgb_cv_results.csv"
    df = pd.read_csv(fp)
    return {
        "NSE":   round(df["NSE"].mean(), 3),
        "KGE":   round(df["KGE"].mean(), 3),
        "PBIAS": round(df["PBIAS"].mean(), 3),
        "n_folds": len(df),
    }


def get_dam_metadata(reservoir: str) -> dict:
    return DAM_META[reservoir]


def get_event_annotations(reservoir: str) -> list:
    return [e for e in KNOWN_EVENTS if e["reservoir"] == reservoir]
