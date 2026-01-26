/**
 * modis_water_area.js
 * DVC Reservoir Attribution Project — Stage 1
 *
 * Purpose: Extract monthly water area (km²) from MODIS MOD09GA for
 *          Maithon, Panchet, and Durgapur reservoirs, 2002–2013.
 *
 * Output:  water_area_modis.csv (432 rows: 144 months × 3 reservoirs)
 * Columns: date, reservoir, water_area_km2, n_images, gap_flag, sensor
 *
 * v2 fix: allFeatures flatten — double-flatten list BEFORE wrapping in
 *         FeatureCollection. The v1 bug called .flatten() on a FC of Features
 *         instead of a FC of FCs → error 3.
 */

// ═══════════════════════════════════════════════════════
// SECTION 1: Reservoir geometries (identical to s1_water_area.js)
// ═══════════════════════════════════════════════════════

var RESERVOIRS = {
  maithon:  ee.Geometry.Rectangle([86.75, 23.78, 86.90, 23.90]),
  // Tightened to 86.95°E (v3): bbox [87.05] captured Damodar river valley +
  // DVC canal network → bimodal contamination. Actual lake within 86.95°E.
  panchet:  ee.Geometry.Rectangle([86.72, 23.52, 86.95, 23.68]),
  durgapur: ee.Geometry.Rectangle([87.25, 23.44, 87.38, 23.54])
};
var RESERVOIR_NAMES = ['maithon', 'panchet', 'durgapur'];
var STUDY_BBOX      = ee.Geometry.Rectangle([86.70, 23.40, 87.45, 23.95]);

var NDWI_THRESHOLD  = 0.2;
var MIN_IMAGES_FLAG = 5;

// ═══════════════════════════════════════════════════════
// SECTION 2: JRC permanent water mask (500m scale for MODIS)
// ═══════════════════════════════════════════════════════

var jrcMask = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('max_extent')
  .eq(1)
  .focal_max(500, 'circle', 'meters');

// ═══════════════════════════════════════════════════════
// SECTION 3: QA filter — mask cloudy pixels
// ═══════════════════════════════════════════════════════

/**
 * Mask cloudy pixels using MOD09GA state_1km QA band.
 * Bits 0–1: 00 = clear, 01 = unobstructed. Keep both (value ≤ 1).
 */
function qaFilter(img) {
  var qa        = img.select('state_1km');
  var clearMask = qa.bitwiseAnd(3).lte(1);
  return img.updateMask(clearMask);
}

// ═══════════════════════════════════════════════════════
// SECTION 4: NDWI computation
// ═══════════════════════════════════════════════════════

/**
 * Compute NDWI = (Green - NIR) / (Green + NIR).
 * MOD09GA bands: sur_refl_b04 = Green (545-565nm), sur_refl_b02 = NIR (841-876nm)
 * Scale factor: × 0.0001 converts stored integers to reflectance.
 */
function computeNDWI(img) {
  var green = img.select('sur_refl_b04').multiply(0.0001);
  var nir   = img.select('sur_refl_b02').multiply(0.0001);
  var ndwi  = green.subtract(nir)
                   .divide(green.add(nir).add(1e-10))
                   .rename('NDWI');
  return img.addBands(ndwi);
}

// ═══════════════════════════════════════════════════════
// SECTION 5: processMonthMODIS
// ═══════════════════════════════════════════════════════

function processMonthMODIS(year, month) {
  var startDate = ee.Date.fromYMD(year, month, 1);
  var endDate   = startDate.advance(1, 'month');
  var dateStr   = startDate.format('YYYY-MM-dd');

  var modisCol = ee.ImageCollection('MODIS/006/MOD09GA')
    .filterDate(startDate, endDate)
    .filterBounds(STUDY_BBOX)
    .select(['sur_refl_b02', 'sur_refl_b04', 'state_1km']);

  var nImages = modisCol.size();

  // QA filter → NDWI → median composite
  var composite = modisCol.map(qaFilter).map(computeNDWI)
                           .select('NDWI').median();

  var gapFlag = ee.Number(ee.Algorithms.If(nImages.lt(MIN_IMAGES_FLAG), 1, 0));

  var features = RESERVOIR_NAMES.map(function(name) {
    var geom   = RESERVOIRS[name];
    var masked = composite.clip(geom).updateMask(jrcMask.clip(geom));

    var validCount = ee.Number(
      masked.reduceRegion({
        reducer: ee.Reducer.count(),
        geometry: geom, scale: 500, maxPixels: 1e7, bestEffort: true
      }).get('NDWI')
    );

    // Water pixels: NDWI > 0.2; 1 pixel at 500m = 0.25 km²
    var waterCount = ee.Number(
      masked.gt(NDWI_THRESHOLD).reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: geom, scale: 500, maxPixels: 1e7, bestEffort: true
      }).get('NDWI')
    );

    var waterArea = waterCount.multiply(0.25);

    // Report -9999 if no valid pixels at all
    var finalArea = ee.Number(ee.Algorithms.If(validCount.gt(0), waterArea, -9999));
    var finalGap  = ee.Number(ee.Algorithms.If(validCount.gt(0), gapFlag,   1));

    return ee.Feature(null, {
      'date':           dateStr,
      'reservoir':      name,
      'water_area_km2': finalArea,
      'n_images':       nImages,
      'gap_flag':       finalGap,
      'sensor':         'MODIS'
    });
  });

  return ee.FeatureCollection(features);
}

// ═══════════════════════════════════════════════════════
// SECTION 6: Month iteration — 2002–2013
// ═══════════════════════════════════════════════════════

var years  = ee.List.sequence(2002, 2013);
var months = ee.List.sequence(1, 12);

// Build flat list FIRST, then wrap in FeatureCollection once.
var allList = years.map(function(year) {
  return months.map(function(month) {
    return processMonthMODIS(
      ee.Number(year).toInt(),
      ee.Number(month).toInt()
    ).toList(3);
  }).flatten();   // 12 months × 3 features = 36 per year
}).flatten();     // 12 years × 36 = 432 features total

var allFeatures = ee.FeatureCollection(allList);

print('Total features (expect 432):', allFeatures.size());

// ═══════════════════════════════════════════════════════
// SECTION 7: Export
// ═══════════════════════════════════════════════════════

Export.table.toDrive({
  collection:     allFeatures,
  description:    'water_area_modis',
  folder:         'dvc_research',
  fileNamePrefix: 'water_area_modis',
  fileFormat:     'CSV',
  selectors:      ['date', 'reservoir', 'water_area_km2', 'n_images', 'gap_flag', 'sensor']
});

// After export completes:
//   Download from Google Drive → data/raw/water_area_modis.csv
