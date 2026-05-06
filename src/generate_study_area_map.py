"""Generate a professional study area map using CartoDEM terrain data."""

import numpy as np
import rasterio
from rasterio.merge import merge
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
from matplotlib.colors import LightSource
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE, "figures")
DEM_DIR = os.path.join(BASE, "data", "raw", "cartoDEM")

TILES = [
    os.path.join(DEM_DIR, "P5_PAN_CD_N23_000_E086_000_30m",
                 "P5_PAN_CD_N23_000_E086_000_DEM_30m.tif"),
    os.path.join(DEM_DIR, "P5_PAN_CD_N23_000_E087_000_30m",
                 "P5_PAN_CD_N23_000_E087_000_DEM_30m.tif"),
    os.path.join(DEM_DIR, "P5_PAN_CD_N24_000_E086_000_30m",
                 "P5_PAN_CD_N24_000_E086_000_DEM_30m.tif"),
    os.path.join(DEM_DIR, "P5_PAN_CD_N24_000_E087_000_30m",
                 "P5_PAN_CD_N24_000_E087_000_DEM_30m.tif"),
]

RESERVOIRS = {
    "Maithon Dam":       {"lon": 86.821, "lat": 23.835, "cap": "1.36 BCM",
                          "color": "#2C6FAC", "marker": "D", "size": 120},
    "Panchet Dam":       {"lon": 86.769, "lat": 23.577, "cap": "0.29 BCM",
                          "color": "#D4A034", "marker": "D", "size": 100},
    "Durgapur Barrage":  {"lon": 87.307, "lat": 23.487, "cap": "Run-of-river",
                          "color": "#2D8E6F", "marker": "s", "size": 110},
}

BASIN_BBOX = {"west": 86.40, "east": 87.50, "south": 23.20, "north": 24.20}

RIVER_LONS = [86.30, 86.50, 86.70, 86.82, 87.00, 87.15, 87.31, 87.50, 87.65]
RIVER_LATS = [24.10, 24.05, 23.92, 23.83, 23.70, 23.58, 23.49, 23.42, 23.38]

CITIES = {
    "Dhanbad":  (86.45, 23.80),
    "Bokaro":   (86.15, 23.67),
    "Asansol":  (87.00, 23.68),
    "Durgapur": (87.32, 23.52),
}

VIEW = {"west": 86.05, "east": 87.75, "south": 23.15, "north": 24.25}


def load_and_merge_dem():
    datasets = []
    for path in TILES:
        if os.path.exists(path):
            datasets.append(rasterio.open(path))
    if not datasets:
        raise FileNotFoundError("No CartoDEM tiles found")
    mosaic, transform = merge(datasets)
    profile = datasets[0].profile.copy()
    profile.update(transform=transform, width=mosaic.shape[2],
                   height=mosaic.shape[1])
    for ds in datasets:
        ds.close()
    return mosaic[0], transform, profile


def compute_hillshade(dem, transform):
    ls = LightSource(azdeg=315, altdeg=35)
    dx = abs(transform[0]) * 111320 * np.cos(np.radians(23.7))
    dy = abs(transform[4]) * 111320
    hs = ls.hillshade(dem, dx=dx, dy=dy, fraction=1.3)
    return hs


def pixel_coords(transform, lon, lat):
    col = (lon - transform[2]) / transform[0]
    row = (lat - transform[5]) / transform[4]
    return col, row


def main():
    print("Loading CartoDEM tiles...")
    dem, transform, profile = load_and_merge_dem()

    dem = np.where(dem < -100, np.nan, dem)

    print("Computing hillshade...")
    dem_filled = np.nan_to_num(dem, nan=np.nanmean(dem))
    hs = compute_hillshade(dem_filled, transform)

    cols_w, rows_s = pixel_coords(transform, VIEW["west"], VIEW["south"])
    cols_e, rows_n = pixel_coords(transform, VIEW["east"], VIEW["north"])
    r0, r1 = int(min(rows_n, rows_s)), int(max(rows_n, rows_s))
    c0, c1 = int(min(cols_w, cols_e)), int(max(cols_w, cols_e))

    r0, r1 = max(0, r0), min(dem.shape[0], r1)
    c0, c1 = max(0, c0), min(dem.shape[1], c1)

    dem_crop = dem[r0:r1, c0:c1]
    hs_crop = hs[r0:r1, c0:c1]

    extent = [
        transform[2] + c0 * transform[0],
        transform[2] + c1 * transform[0],
        transform[5] + r1 * transform[4],
        transform[5] + r0 * transform[4],
    ]

    fig, ax = plt.subplots(1, 1, figsize=(8, 6.5), dpi=200)

    ax.imshow(hs_crop, cmap="gray", extent=extent, aspect="auto",
              alpha=0.55, vmin=0.1, vmax=0.95)
    im = ax.imshow(dem_crop, cmap="terrain", extent=extent, aspect="auto",
                   alpha=0.55, vmin=50, vmax=650)

    basin_rect = mpatches.FancyBboxPatch(
        (BASIN_BBOX["west"], BASIN_BBOX["south"]),
        BASIN_BBOX["east"] - BASIN_BBOX["west"],
        BASIN_BBOX["north"] - BASIN_BBOX["south"],
        boxstyle="round,pad=0.02",
        linewidth=1.8, edgecolor="#2C3E50", facecolor="none",
        linestyle="--", zorder=5,
    )
    ax.add_patch(basin_rect)

    ax.plot(RIVER_LONS, RIVER_LATS, color="#3498DB", linewidth=2.2,
            alpha=0.8, zorder=6, label="Damodar River (approx.)")

    for name, info in RESERVOIRS.items():
        ax.scatter(info["lon"], info["lat"], marker=info["marker"],
                   s=info["size"], c=info["color"], edgecolors="white",
                   linewidths=1.2, zorder=10)
        offset_x, offset_y = 0.04, 0.04
        if "Durgapur" in name:
            offset_x, offset_y = -0.35, 0.05
        elif "Panchet" in name:
            offset_x, offset_y = -0.30, -0.06
        ax.annotate(
            f"{name}\n({info['cap']})",
            xy=(info["lon"], info["lat"]),
            xytext=(info["lon"] + offset_x, info["lat"] + offset_y),
            fontsize=7, fontweight="bold", color="#2C3E50",
            ha="left", va="bottom",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#BDC3C7",
                      alpha=0.85),
            arrowprops=dict(arrowstyle="-|>", color="#7F8C8D", lw=0.8),
            zorder=11,
        )

    for city, (lon, lat) in CITIES.items():
        ax.plot(lon, lat, "o", color="#555555", markersize=4, zorder=8)
        ax.annotate(city, (lon, lat), fontsize=6, color="#555555",
                    xytext=(4, 4), textcoords="offset points",
                    fontstyle="italic", zorder=8)

    ax.set_xlim(VIEW["west"], VIEW["east"])
    ax.set_ylim(VIEW["south"], VIEW["north"])
    ax.set_xlabel("Longitude ($^\circ$E)", fontsize=9)
    ax.set_ylabel("Latitude ($^\circ$N)", fontsize=9)
    ax.tick_params(labelsize=8)

    ax.set_title("Study Area — Damodar Valley Corporation Reservoir System",
                 fontsize=11, fontweight="bold", color="#2C3E50", pad=10)

    jh_x = (BASIN_BBOX["west"] + BASIN_BBOX["east"]) / 2 - 0.25
    wb_x = BASIN_BBOX["east"] - 0.08
    ax.text(jh_x, BASIN_BBOX["north"] - 0.04, "Jharkhand", fontsize=7,
            color="#2C3E50", alpha=0.5, fontstyle="italic", zorder=4)
    ax.text(wb_x, BASIN_BBOX["north"] - 0.04, "West Bengal", fontsize=7,
            color="#2C3E50", alpha=0.5, fontstyle="italic", zorder=4)

    ax_inset = inset_axes(ax, width="22%", height="28%", loc="upper left",
                          borderpad=1.5)
    india_lons = [68, 97, 97, 68, 68]
    india_lats = [8, 8, 37, 37, 8]
    ax_inset.fill(india_lons, india_lats, color="#ECF0F1", zorder=1)
    ax_inset.plot(india_lons, india_lats, color="#BDC3C7", linewidth=0.5,
                  zorder=2)

    basin_cx = (BASIN_BBOX["west"] + BASIN_BBOX["east"]) / 2
    basin_cy = (BASIN_BBOX["south"] + BASIN_BBOX["north"]) / 2
    ax_inset.plot(basin_cx, basin_cy, "o", color="#E74C3C", markersize=6,
                  zorder=5)
    ax_inset.annotate("Study\nArea", (basin_cx, basin_cy),
                      xytext=(basin_cx + 6, basin_cy + 3),
                      fontsize=5, color="#E74C3C", fontweight="bold",
                      arrowprops=dict(arrowstyle="-", color="#E74C3C",
                                      lw=0.6),
                      zorder=5)
    ax_inset.text(82, 28, "India", fontsize=8, ha="center", color="#7F8C8D",
                  fontweight="bold", zorder=3)
    ax_inset.set_xlim(65, 100)
    ax_inset.set_ylim(5, 40)
    ax_inset.set_xticks([])
    ax_inset.set_yticks([])
    for spine in ax_inset.spines.values():
        spine.set_color("#BDC3C7")

    cbar = fig.colorbar(im, ax=ax, shrink=0.55, pad=0.02, aspect=20)
    cbar.set_label("Elevation (m)", fontsize=8)
    cbar.ax.tick_params(labelsize=7)

    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], color="#3498DB", linewidth=2, label="Damodar River"),
        mpatches.Patch(edgecolor="#2C3E50", facecolor="none", linestyle="--",
                       linewidth=1.2,
                       label=f"Upper catchment (~19,600 km$^2$)"),
    ]
    for name, info in RESERVOIRS.items():
        legend_elements.append(
            Line2D([0], [0], marker=info["marker"], color="w",
                   markerfacecolor=info["color"], markeredgecolor="white",
                   markersize=8, label=name)
        )
    ax.legend(handles=legend_elements, loc="lower left", fontsize=6.5,
              framealpha=0.9, edgecolor="#BDC3C7", fancybox=True)

    plt.tight_layout()

    for fmt in ("png", "pdf"):
        out = os.path.join(FIG_DIR, f"Fig1_study_area.{fmt}")
        fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
        print(f"Saved: {out}")

    plt.close()
    print("Done.")


if __name__ == "__main__":
    main()
