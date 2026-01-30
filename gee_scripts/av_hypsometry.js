/**
 * av_hypsometry.js
 * DVC Reservoir Attribution Project — Stage 1 (Day 3)
 *
 * Purpose: Derive Area-Volume (A-V) hypsometric curves for Maithon, Panchet,
 *          and Durgapur from ALOS AW3D30 DEM (30m, GEE).
 *          CartoDEM unavailable on Bhuvan — ALOS AW3D30 is the listed backup
 *          (CLAUDE.md §3.1 dataset #4, JAXA/ALOS/AW3D30/V2_2).
 *
 * Method:
 *   For each reservoir:
 *     1. Clip DEM to reservoir bbox + JRC max_extent mask
 *     2. Find min elevation (dead storage level proxy)
 *     3. Sweep elevation from min to max in 0.5m steps
 *     4. At each elevation h: count pixels below h → water area at that level
 *     5. Integrate area-elevation curve → volume at each level (trapezoidal rule)
 *     6. Export full elevation-area-volume table
 *
 * Output: av_hypsometry.csv
 * Columns: reservoir, elevation_m, area_km2, volume_bcm
 *
 * Run: Paste into new GEE tab → Run → Submit export task
 *      Download → data/raw/av_hypsometry.csv
 *      Then run: uv run python src/fit_av_params.py
 */

// ═══════════════════════════════════════════════════════
// SECTION 1: Reservoir geometries (updated Panchet bbox)
// ═══════════════════════════════════════════════════════

var RESERVOIRS = {
  maithon:  ee.Geometry.Rectangle([86.75, 23.78, 86.90, 23.90]),
  // Tightened to 86.95°E (v3): prior bbox captured Damodar river floodplain
  panchet:  ee.Geometry.Rectangle([86.72, 23.52, 86.95, 23.68]),
  durgapur: ee.Geometry.Rectangle([87.25, 23.44, 87.38, 23.54])
};
var RESERVOIR_NAMES = ['maithon', 'panchet', 'durgapur'];

// Elevation sweep step (metres) — finer = more accurate curve, slower export
var ELEV_STEP = 0.5;

// ═══════════════════════════════════════════════════════
// SECTION 2: Load DEM and JRC mask
// ═══════════════════════════════════════════════════════

// ALOS AW3D30 v2.2 — AVE_DSM band, 30m, vertical accuracy ±5m RMSE globally
// Better than SRTM for vegetated terrain in Jharkhand
var dem = ee.Image('JAXA/ALOS/AW3D30/V2_2').select('AVE_DSM');

// JRC max_extent: pixels that have ever been water — defines reservoir footprint
var jrcMask = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('max_extent')
  .eq(1)
  .focal_max(100, 'circle', 'meters');  // 100m buffer (conservative for DEM work)

// ═══════════════════════════════════════════════════════
// SECTION 3: Hypsometry computation per reservoir
// ═══════════════════════════════════════════════════════

/**
 * Compute elevation-area-volume table for one reservoir.
 *
 * @param {string} name - reservoir name
 * @returns {ee.FeatureCollection} rows of {reservoir, elevation_m, area_km2, volume_bcm}
 */
function computeHypsometry(name) {
  var geom    = RESERVOIRS[name];
  var demClip = dem.clip(geom).updateMask(jrcMask.clip(geom));

  // Get min and max elevation within reservoir footprint
  var stats = demClip.reduceRegion({
    reducer:   ee.Reducer.minMax(),
    geometry:  geom,
    scale:     30,
    maxPixels: 1e9,
    bestEffort: true
  });

  var elevMin = ee.Number(stats.get('AVE_DSM_min')).subtract(1);
  var elevMax = ee.Number(stats.get('AVE_DSM_max')).add(1);

  // Number of elevation steps
  var nSteps  = elevMax.subtract(elevMin).divide(ELEV_STEP).ceil().toInt();
  var indices = ee.List.sequence(0, nSteps);

  // For each elevation step, compute cumulative area below that level
  var rows = indices.map(function(i) {
    i = ee.Number(i);
    var h = elevMin.add(i.multiply(ELEV_STEP));

    // Pixels at or below elevation h = potential water surface at level h
    var belowH = demClip.lte(h);

    // Area in km²: count pixels × (30m)² / 1e6
    var pixCount = ee.Number(
      belowH.reduceRegion({
        reducer:   ee.Reducer.sum(),
        geometry:  geom,
        scale:     30,
        maxPixels: 1e9,
        bestEffort: true
      }).get('AVE_DSM')
    );

    var area_km2 = pixCount.multiply(30 * 30).divide(1e6);

    return ee.Feature(null, {
      'reservoir':   name,
      'elevation_m': h,
      'area_km2':    area_km2,
      // Volume placeholder (BCM) — computed properly in Python with trapezoidal rule
      // GEE doesn't support cumulative integration elegantly; do it in Python
      'volume_bcm':  -9999
    });
  });

  return ee.FeatureCollection(rows);
}

// ═══════════════════════════════════════════════════════
// SECTION 4: Run for all reservoirs
// ═══════════════════════════════════════════════════════

var maithonHyps  = computeHypsometry('maithon');
var panchetHyps  = computeHypsometry('panchet');
var durgapurHyps = computeHypsometry('durgapur');

var allHyps = maithonHyps.merge(panchetHyps).merge(durgapurHyps);

print('Maithon rows:',  maithonHyps.size());
print('Panchet rows:',  panchetHyps.size());
print('Durgapur rows:', durgapurHyps.size());
print('Total rows:',    allHyps.size());

// ═══════════════════════════════════════════════════════
// SECTION 5: Export
// ═══════════════════════════════════════════════════════

Export.table.toDrive({
  collection:     allHyps,
  description:    'av_hypsometry',
  folder:         'dvc_research',
  fileNamePrefix: 'av_hypsometry',
  fileFormat:     'CSV',
  selectors:      ['reservoir', 'elevation_m', 'area_km2', 'volume_bcm']
});

// ─── AFTER EXPORT ────────────────────────────────────────────────────────────
// 1. Download av_hypsometry.csv → data/raw/av_hypsometry.csv
// 2. Run: uv run python src/fit_av_params.py
//    → fits V = a × A^b power law per reservoir
//    → prints new AV_PARAMS dict to copy into 01_storage_reconstruction.py
//    → saves figures/FigS1_AV_curves.png (supplementary figure for paper)
// ─────────────────────────────────────────────────────────────────────────────
