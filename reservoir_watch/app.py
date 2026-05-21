# Requirements: streamlit plotly folium streamlit-folium pandas numpy
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import pandas as pd

from backend import (
    get_dam_metadata, get_regime_timeseries, get_current_regime,
    get_model_metrics, get_event_annotations, REGIME_COLORS
)

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ReservoirWatch",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Google+Sans:wght@400;500;700&family=Roboto+Mono&display=swap');

/* Base */
html, body, [class*="css"] { font-family: 'Google Sans', sans-serif; }
.stApp { background: #f1f3f4; }

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #1a237e !important;
    color: white;
}
section[data-testid="stSidebar"] * { color: white !important; }
section[data-testid="stSidebar"] .stRadio label { color: white !important; }
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2); }

/* Top bar */
.topbar {
    background: #1a237e;
    padding: 12px 24px;
    display: flex;
    align-items: center;
    gap: 12px;
    border-radius: 0 0 4px 4px;
    margin-bottom: 16px;
}
.topbar-title {
    color: white;
    font-size: 1.25rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}
.topbar-subtitle {
    color: rgba(255,255,255,0.7);
    font-size: 0.85rem;
}

/* Cards */
.card {
    background: white;
    border: 1px solid #dadce0;
    border-radius: 8px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.card-title {
    font-size: 0.72rem;
    font-weight: 500;
    color: #5f6368;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 10px;
}

/* Dam header */
.dam-name { font-size: 1.35rem; font-weight: 600; color: #202124; }
.dam-meta { font-size: 0.82rem; color: #5f6368; margin-top: 2px; }

/* Regime badge */
.regime-wrap { display: flex; align-items: center; gap: 12px; margin: 4px 0 8px; }
.regime-dot {
    width: 14px; height: 14px; border-radius: 50%;
    flex-shrink: 0;
}
.regime-text { font-size: 1.4rem; font-weight: 600; }
.regime-sub { font-size: 0.8rem; color: #5f6368; margin-top: 2px; }

/* Metrics row */
.metrics-row { display: flex; gap: 24px; margin-top: 4px; }
.metric-box { text-align: center; }
.metric-val { font-size: 1.2rem; font-weight: 600; color: #1a237e; }
.metric-lbl { font-size: 0.68rem; color: #80868b; text-transform: uppercase; letter-spacing: 0.8px; }

/* Footer */
.app-footer {
    text-align: center;
    color: #9aa0a6;
    font-size: 0.75rem;
    padding: 16px 0 8px;
    border-top: 1px solid #dadce0;
    margin-top: 12px;
}

/* Plotly iframe border */
iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 💧 ReservoirWatch")
    st.markdown("Passive satellite-based operational regime monitoring")
    st.markdown("---")
    dam_choice = st.radio(
        "Select Reservoir",
        options=["Maithon", "Panchet", "Durgapur"],
        index=0,
    )
    reservoir = dam_choice.lower()
    st.markdown("---")
    st.markdown("**Data sources**")
    st.markdown("Sentinel-1 SAR · CHIRPS · ERA5")
    st.markdown("**Period**")
    st.markdown("2002 – 2026")
    st.markdown("**Update frequency**")
    st.markdown("Monthly (auto)")
    st.markdown("---")
    st.markdown("**Regime legend**")
    for label, color in REGIME_COLORS.items():
        st.markdown(
            f"<span style='display:inline-block;width:10px;height:10px;"
            f"border-radius:50%;background:{color};margin-right:8px'></span>{label}",
            unsafe_allow_html=True,
        )

# ── Load data ─────────────────────────────────────────────────────────────────
meta    = get_dam_metadata(reservoir)
current = get_current_regime(reservoir)
regime_df = get_regime_timeseries(reservoir)
metrics = get_model_metrics()
events  = get_event_annotations(reservoir)

# ── Top bar ───────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="topbar">
        <span style="font-size:1.5rem">💧</span>
        <div>
            <div class="topbar-title">ReservoirWatch</div>
            <div class="topbar-subtitle">Damodar Valley Corporation · Operational Regime Monitor</div>
        </div>
    </div>""",
    unsafe_allow_html=True,
)

# ── Main layout ───────────────────────────────────────────────────────────────
col_map, col_info = st.columns([5, 6], gap="medium")

# ── LEFT: Map ─────────────────────────────────────────────────────────────────
with col_map:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Satellite View</div>', unsafe_allow_html=True)

    m = folium.Map(
        location=[meta["lat"], meta["lon"]],
        zoom_start=11,
        tiles="OpenStreetMap",
        control_scale=True,
    )
    # All three dams as small gray markers
    all_dams = {
        "Maithon":  (23.835, 86.821),
        "Panchet":  (23.577, 86.769),
        "Durgapur": (23.487, 87.307),
    }
    for dname, (dlat, dlon) in all_dams.items():
        is_selected = dname.lower() == reservoir
        folium.CircleMarker(
            location=[dlat, dlon],
            radius=7 if is_selected else 5,
            color="#1a237e" if is_selected else "#757575",
            fill=True,
            fill_color="#1a237e" if is_selected else "#9e9e9e",
            fill_opacity=0.9 if is_selected else 0.5,
            popup=folium.Popup(dname, max_width=120),
            tooltip=dname,
        ).add_to(m)

    # Water extent circle for selected dam
    regime_color_hex = current.get("color", "#1565c0")
    folium.Circle(
        location=[meta["lat"], meta["lon"]],
        radius=2500,
        color=regime_color_hex,
        fill=True,
        fill_color=regime_color_hex,
        fill_opacity=0.18,
        weight=1.5,
        tooltip=f"Approx. water extent — {current['regime']}",
    ).add_to(m)

    st_folium(m, height=370, width=None, returned_objects=[])
    st.markdown("</div>", unsafe_allow_html=True)

# ── RIGHT: Info ───────────────────────────────────────────────────────────────
with col_info:

    # Dam header card
    cap_str = f"{meta['capacity_bcm']} BCM" if meta["capacity_bcm"] else "Run-of-river"
    st.markdown(
        f"""<div class="card">
            <div class="dam-name">{meta['name']}</div>
            <div class="dam-meta">
                {meta['lat']}°N &nbsp;{meta['lon']}°E &nbsp;·&nbsp;
                {meta['river']} River &nbsp;·&nbsp; Capacity: {cap_str}
            </div>
            <div class="dam-meta" style="margin-top:4px">
                {meta['function']} &nbsp;·&nbsp; Est. {meta['commissioned']}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Current regime card
    rcolor = current.get("color", "#1565c0")
    conf_pct = int(current["confidence"] * 100)
    delta_str = (
        f"ΔS = {current['delta_s']:+.3f} BCM"
        if current["delta_s"] is not None and not pd.isna(current["delta_s"])
        else "ΔS = —"
    )
    st.markdown(
        f"""<div class="card">
            <div class="card-title">Current Operational Regime</div>
            <div class="regime-wrap">
                <div class="regime-dot" style="background:{rcolor}"></div>
                <div class="regime-text" style="color:{rcolor}">{current['regime'].upper()}</div>
            </div>
            <div class="regime-sub">
                Confidence: {conf_pct}% &nbsp;·&nbsp; {delta_str} &nbsp;·&nbsp;
                Updated: {current['updated']}
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # Regime history timeline
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Regime History (2014 – 2026)</div>', unsafe_allow_html=True)

    rdf = regime_df[regime_df["date"] >= "2014-01-01"].copy()
    if not rdf.empty:
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Bar(
            x=rdf["date"],
            y=[1] * len(rdf),
            marker_color=rdf["regime_color"].tolist(),
            marker_line_width=0,
            hovertemplate="<b>%{x|%b %Y}</b><br>%{customdata}",
            customdata=rdf["regime_label"].tolist(),
            showlegend=False,
        ))
        # Add one dummy trace per regime for legend
        for label, color in REGIME_COLORS.items():
            fig_timeline.add_trace(go.Bar(
                x=[None], y=[None],
                marker_color=color,
                name=label,
                showlegend=True,
            ))
        fig_timeline.update_layout(
            height=90,
            margin=dict(l=0, r=0, t=0, b=0),
            barmode="stack",
            bargap=0.02,
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(showticklabels=False, showgrid=False, zeroline=False, range=[0, 1]),
            xaxis=dict(showgrid=False, tickformat="%Y"),
            legend=dict(
                orientation="h",
                yanchor="bottom", y=1.02,
                xanchor="right", x=1,
                font=dict(size=10),
                bgcolor="rgba(0,0,0,0)",
            ),
        )
        st.plotly_chart(fig_timeline, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("No regime history available for this reservoir.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Storage anomaly chart
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Storage Anomaly — ΔS (BCM)</div>', unsafe_allow_html=True)

    anom_df = regime_df.dropna(subset=["delta_S_obs_bcm"]).copy()
    if not anom_df.empty:
        fig_anom = go.Figure()
        # Background line
        fig_anom.add_trace(go.Scatter(
            x=anom_df["date"], y=anom_df["delta_S_obs_bcm"],
            mode="lines",
            line=dict(color="#dadce0", width=1.2),
            showlegend=False,
            hoverinfo="skip",
        ))
        # Colored dots by regime
        for label, color in REGIME_COLORS.items():
            mask = anom_df["regime_label"] == label
            sub = anom_df[mask]
            if sub.empty:
                continue
            fig_anom.add_trace(go.Scatter(
                x=sub["date"], y=sub["delta_S_obs_bcm"],
                mode="markers",
                marker=dict(color=color, size=5, opacity=0.85),
                name=label,
                hovertemplate="<b>%{x|%b %Y}</b><br>ΔS = %{y:.3f} BCM<extra>" + label + "</extra>",
                showlegend=False,
            ))
        # Zero line
        fig_anom.add_hline(y=0, line_dash="dot", line_color="#9aa0a6", line_width=1)

        # Event annotations
        y_range = anom_df["delta_S_obs_bcm"].abs().max() * 1.1
        for ev in events:
            try:
                ev_date = pd.to_datetime(ev["date"] + "-01")
            except Exception:
                continue
            if ev_date < anom_df["date"].min() or ev_date > anom_df["date"].max():
                continue
            fig_anom.add_vline(
                x=ev_date, line_dash="dot",
                line_color="#c62828" if ev["severity"] == "high" else "#e65100",
                line_width=1,
            )
            fig_anom.add_annotation(
                x=ev_date, y=y_range * 0.92,
                text=ev["label"],
                showarrow=False,
                font=dict(size=9, color="#5f6368"),
                bgcolor="rgba(255,255,255,0.8)",
                bordercolor="#dadce0",
                borderwidth=1,
            )

        fig_anom.update_layout(
            height=200,
            margin=dict(l=0, r=0, t=4, b=0),
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(
                showgrid=True, gridcolor="#f1f3f4", zeroline=False,
                tickfont=dict(size=10, color="#5f6368"),
                title=dict(text="BCM", font=dict(size=10)),
            ),
            xaxis=dict(showgrid=False, tickfont=dict(size=10, color="#5f6368")),
            hovermode="x unified",
        )
        st.plotly_chart(fig_anom, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("Storage anomaly data not available for this reservoir.")
    st.markdown("</div>", unsafe_allow_html=True)

    # Model metrics + download row
    col_m1, col_m2, col_m3, col_dl = st.columns([1, 1, 1, 2])
    with col_m1:
        st.markdown(
            f'<div class="metric-box"><div class="metric-val">{metrics["NSE"]}</div>'
            f'<div class="metric-lbl">NSE</div></div>',
            unsafe_allow_html=True,
        )
    with col_m2:
        st.markdown(
            f'<div class="metric-box"><div class="metric-val">{metrics["KGE"]}</div>'
            f'<div class="metric-lbl">KGE</div></div>',
            unsafe_allow_html=True,
        )
    with col_m3:
        st.markdown(
            f'<div class="metric-box"><div class="metric-val">{metrics["PBIAS"]:+.1f}%</div>'
            f'<div class="metric-lbl">PBIAS</div></div>',
            unsafe_allow_html=True,
        )
    with col_dl:
        export_df = regime_df[["date", "water_area_km2", "delta_S_obs_bcm", "regime_label", "confidence"]]
        st.download_button(
            label="⬇ Download CSV",
            data=export_df.to_csv(index=False).encode(),
            file_name=f"reservoirwatch_{reservoir}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="app-footer">'
    'Sentinel-1 · CHIRPS · ERA5-Land &nbsp;|&nbsp; '
    'Mandal et al. 2026 — BIT Sindri, Civil Engineering &nbsp;|&nbsp; '
    'Prototype · Not for operational use'
    '</div>',
    unsafe_allow_html=True,
)
