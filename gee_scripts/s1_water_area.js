/**
 * s1_water_area.js
 * DVC Reservoir Attribution Project — Stage 1
 *
 * Purpose: Extract monthly water area (km²) from Sentinel-1 SAR for
 *          Maithon, Panchet, and Durgapur reservoirs, 2014–2024.
 *
 * Output:  water_area_sentinel1.csv (396 rows: 132 months × 3 reservoirs)
 * Columns: date, reservoir, water_area_km2, n_images, gap_flag
 *
 * v2 changes (fixes):
 *   - Removed per-image Refined Lee filter (caused out-of-memory at 11-year scale)
 *     Replacement: median monthly composite is equivalent despeckling for
 *     reservoir classification and standard in the SAR hydrology literature.
 *   - Fixed allFeatures flatten: double-flatten list BEFORE wrapping in
 *     FeatureCollection (was calling .flatten() on FC of Features → error 3)
 *   - Otsu histogram dict path corrected (.get('VV') → pass inner dict)
 */

// ═══════════════════════════════════════════════════════
// SECTION 1: Reservoir geometries
// ═══════════════════════════════════════════════════════

var RESERVOIRS = {
  maithon:  ee.Geometry.Rectangle([86.75, 23.78, 86.90, 23.90]),
  // Tightened to 86.95°E (v3): bbox [87.05] included 30km of Damodar river
  // valley + DVC irrigation canal network → bimodal contamination (140–370 km²
  // in dry season). Actual Panchet lake body stays within 86.95°E.
  panchet:  ee.Geometry.Rectangle([86.72, 23.52, 86.95, 23.68]),
  durgapur: ee.Geometry.Rectangle([87.25, 23.44, 87.38, 23.54])
};
var RESERVOIR_NAMES = ['maithon', 'panchet', 'durgapur'];
var STUDY_BBOX = ee.Geometry.Rectangle([86.70, 23.40, 87.45, 23.95]);

// ═══════════════════════════════════════════════════════
// SECTION 2: JRC permanent water mask
// ═══════════════════════════════════════════════════════

var jrcMask = ee.Image('JRC/GSW1_4/GlobalSurfaceWater')
  .select('max_extent')
  .eq(1)
  .focal_max(500, 'circle', 'meters');

// ═══════════════════════════════════════════════════════
// SECTION 3: Otsu threshold
// ═══════════════════════════════════════════════════════

/**
 * Compute Otsu threshold from histogram inner dict
 * (the object with 'histogram' and 'bucketMeans' keys).
 * Uses sort() instead of argmax() to avoid server-side index issues.
 * Uses .max(1) instead of ee.Algorithms.If for zero-division guard.
 */
function otsuThreshold(histDict) {
  var counts = ee.Array(ee.Dictionary(histDict).get('histogram'));
  var means  = ee.Array(ee.Dictionary(histDict).get('bucketMeans'));
  var size   = means.length().get([0]);
  var total  = counts.reduce(ee.Reducer.sum(), [0]).get([0]);
  var sum    = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0]);

  var bss = ee.Array(
    ee.List.sequence(1, size.subtract(1)).map(function(i) {
      i = ee.Number(i);
      var aCount = counts.slice(0, 0, i).reduce(ee.Reducer.sum(), [0]).get([0]);
      var bCount = total.subtract(aCount);
      var aSum   = means.slice(0, 0, i).multiply(counts.slice(0, 0, i))
                     .reduce(ee.Reducer.sum(), [0]).get([0]);
      var aMean  = aSum.divide(aCount.max(1));
      var bMean  = sum.subtract(aSum).divide(bCount.max(1));
      return aCount.multiply(bCount).multiply(aMean.subtract(bMean).pow(2));
    })
  );

  // Sort candidate means by bss ascending; last = argmax
  return means.slice(0, 0, size.subtract(1)).sort(bss).get([-1]);
}

// ═══════════════════════════════════════════════════════
// SECTION 4: processMonth
// ═══════════════════════════════════════════════════════

function processMonth(year, month) {
  var startDate = ee.Date.fromYMD(year, month, 1);
  var endDate   = startDate.advance(1, 'month');
  var dateStr   = startDate.format('YYYY-MM-dd');

  var s1Col = ee.ImageCollection('COPERNICUS/S1_GRD')
    .filter(ee.Filter.eq('instrumentMode', 'IW'))
    .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
    .filter(ee.Filter.eq('orbitProperties_pass', 'ASCENDING'))
    .filterDate(startDate, endDate)
    .filterBounds(STUDY_BBOX)
    .select('VV');

  var nImages   = s1Col.size();
  // Median composite — despeckling equivalent to Refined Lee for reservoir
  // classification; avoids per-image neighbourhood operations (memory fix)
  var composite = s1Col.median();

  var features = RESERVOIR_NAMES.map(function(name) {
    var geom   = RESERVOIRS[name];
    var masked = composite.clip(geom).updateMask(jrcMask.clip(geom));

    // Count valid (non-masked) pixels
    var validCount = ee.Number(
      masked.reduceRegion({
        reducer: ee.Reducer.count(),
        geometry: geom, scale: 20, maxPixels: 1e8, bestEffort: true
      }).get('VV')
    );

    // Compute histogram for Otsu; fall back to -16 dB if < 100 valid pixels
    var histResult = masked.reduceRegion({
      reducer: ee.Reducer.histogram(256, null, null),
      geometry: geom, scale: 20, maxPixels: 1e8, bestEffort: true
    });

    var threshold = ee.Number(
      ee.Algorithms.If(
        validCount.gte(100),
        otsuThreshold(histResult.get('VV')),
        -16
      )
    );

    // Water pixels: backscatter < threshold; 1 pixel at 20m = 0.0004 km²
    var waterCount = ee.Number(
      masked.lt(threshold).reduceRegion({
        reducer: ee.Reducer.sum(),
        geometry: geom, scale: 20, maxPixels: 1e8, bestEffort: true
      }).get('VV')
    );

    var waterArea = waterCount.multiply(0.0004);

    // If no S1 images this month, report gap
    var finalArea = ee.Number(ee.Algorithms.If(nImages.gt(0), waterArea, -9999));
    var gapFlag   = ee.Number(ee.Algorithms.If(nImages.gt(0), 0, 1));

    return ee.Feature(null, {
      'date':           dateStr,
      'reservoir':      name,
      'water_area_km2': finalArea,
      'n_images':       nImages,
      'gap_flag':       gapFlag
    });
  });

  return ee.FeatureCollection(features);
}

// ═══════════════════════════════════════════════════════
// SECTION 5: Month iteration — 2014–2024
// ═══════════════════════════════════════════════════════

var years  = ee.List.sequence(2014, 2024);
var months = ee.List.sequence(1, 12);

// Build flat list FIRST, then wrap in FeatureCollection once.
// Never call .flatten() on a FeatureCollection — that requires FC of FCs.
var allList = years.map(function(year) {
  return months.map(function(month) {
    return processMonth(
      ee.Number(year).toInt(),
      ee.Number(month).toInt()
    ).toList(3);
  }).flatten();   // flatten 12 months × 3 features = 36 per year
}).flatten();     // flatten 11 years × 36 = 396 features total

var allFeatures = ee.FeatureCollection(allList);

print('Total features (expect 396):', allFeatures.size());

// ═══════════════════════════════════════════════════════
// SECTION 6: Export
// ═══════════════════════════════════════════════════════

Export.table.toDrive({
  collection:     allFeatures,
  description:    'water_area_sentinel1',
  folder:         'dvc_research',
  fileNamePrefix: 'water_area_sentinel1',
  fileFormat:     'CSV',
  selectors:      ['date', 'reservoir', 'water_area_km2', 'n_images', 'gap_flag']
});

// After export completes:
//   Download from Google Drive → data/raw/water_area_sentinel1.csv
//   Then run: uv run python src/01_storage_reconstruction.py
