/**
 * driver_extraction.js
 * DVC Reservoir Attribution Project — Stage 2
 *
 * Purpose: Extract monthly climate/environmental driver variables for the
 *          Damodar catchment, 2002-01-01 to 2023-12-31 (264 months).
 *
 * Outputs (export to Google Drive folder 'DVC_drivers/'):
 *   chirps_monthly.csv  — 264 rows: date, precipitation (mm/month)
 *   era5_monthly.csv    — 264 rows: date, PET_m, SM1_m3m3, SM2_m3m3, T_K
 *   ndvi_monthly.csv    — 264 rows: date, NDVI (scaled 0–1)
 *   aet_monthly.csv     — 264 rows: date, ET (mm/month)
 *   lulc_annual.csv     — 22 rows:  year, LC_crop_frac, LC_forest_frac
 *   ntl_dmsp_annual.csv — 12 rows:  year, NTL_dmsp
 *
 * Run: Paste into code.earthengine.google.com → Run → Submit all 6 export tasks
 * Download: Google Drive → DVC_drivers/ folder → save to data/raw/
 */

// ═══════════════════════════════════════════════════════
// SECTION 1: Geometry and date range
// ═══════════════════════════════════════════════════════

// Full upper Damodar basin catchment — covers Maithon + Panchet watersheds
var CATCHMENT  = ee.Geometry.Rectangle([86.40, 23.20, 87.50, 24.20]);
var START_YEAR = 2002;
var END_YEAR   = 2023;
var years      = ee.List.sequence(START_YEAR, END_YEAR);
var months     = ee.List.sequence(1, 12);

// ═══════════════════════════════════════════════════════
// SECTION 2: Helper — monthly spatial mean of a collection band
// ═══════════════════════════════════════════════════════

function monthlyMean(collection, band, year, month, scale) {
  var start   = ee.Date.fromYMD(year, month, 1);
  var end     = start.advance(1, 'month');
  var dateStr = start.format('YYYY-MM-dd');
  var img = collection.select(band).filterDate(start, end).mean();
  var val = img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: CATCHMENT,
    scale: scale,
    maxPixels: 1e9
  });
  return ee.Feature(null, val.set('date', dateStr));
}

function monthlySum(collection, band, year, month, scale) {
  var start   = ee.Date.fromYMD(year, month, 1);
  var end     = start.advance(1, 'month');
  var dateStr = start.format('YYYY-MM-dd');
  // Sum images, then take spatial mean across catchment
  var img = collection.select(band).filterDate(start, end).sum();
  var val = img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: CATCHMENT,
    scale: scale,
    maxPixels: 1e9
  });
  return ee.Feature(null, val.set('date', dateStr));
}

// ═══════════════════════════════════════════════════════
// SECTION 3: CHIRPS monthly precipitation (mm/month)
// ═══════════════════════════════════════════════════════

var CHIRPS = ee.ImageCollection('UCSB-CHG/CHIRPS/DAILY');

var chirpsList = years.map(function(year) {
  return months.map(function(month) {
    return monthlySum(CHIRPS, 'precipitation', year, month, 5566);
  });
}).flatten();

var chirpsFC = ee.FeatureCollection(chirpsList);

Export.table.toDrive({
  collection: chirpsFC,
  description: 'chirps_monthly',
  folder: 'DVC_drivers',
  fileNamePrefix: 'chirps_monthly',
  fileFormat: 'CSV',
  selectors: ['date', 'precipitation']
});

print('CHIRPS rows (expect 264):', chirpsFC.size());

// ═══════════════════════════════════════════════════════
// SECTION 4: ERA5-Land monthly (PET, soil moisture, temperature)
// ═══════════════════════════════════════════════════════

var ERA5 = ee.ImageCollection('ECMWF/ERA5_LAND/DAILY_AGGR');

var ERA5_BANDS = [
  'potential_evaporation_sum',     // [m/day] — multiply by days_in_month×1000 in Python → mm/month
  'volumetric_soil_water_layer_1', // [m³/m³] 0–7cm
  'volumetric_soil_water_layer_2', // [m³/m³] 7–28cm
  'temperature_2m'                 // [K] — subtract 273.15 in Python → °C
];

var era5List = years.map(function(year) {
  return months.map(function(month) {
    var start   = ee.Date.fromYMD(year, month, 1);
    var end     = start.advance(1, 'month');
    var dateStr = start.format('YYYY-MM-dd');
    var img = ERA5.select(ERA5_BANDS).filterDate(start, end).mean();
    var vals = img.reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: CATCHMENT,
      scale: 11132,
      maxPixels: 1e9
    });
    return ee.Feature(null, vals.set('date', dateStr));
  });
}).flatten();

var era5FC = ee.FeatureCollection(era5List);

Export.table.toDrive({
  collection: era5FC,
  description: 'era5_monthly',
  folder: 'DVC_drivers',
  fileNamePrefix: 'era5_monthly',
  fileFormat: 'CSV',
  selectors: ['date',
              'potential_evaporation_sum',
              'volumetric_soil_water_layer_1',
              'volumetric_soil_water_layer_2',
              'temperature_2m']
});

print('ERA5 rows (expect 264):', era5FC.size());

// ═══════════════════════════════════════════════════════
// SECTION 5: MODIS NDVI monthly (MOD13Q1, 16-day, 250m)
// ═══════════════════════════════════════════════════════

var MODIS_NDVI = ee.ImageCollection('MODIS/006/MOD13Q1');

var ndviList = years.map(function(year) {
  return months.map(function(month) {
    var start   = ee.Date.fromYMD(year, month, 1);
    var end     = start.advance(1, 'month');
    var dateStr = start.format('YYYY-MM-dd');
    var col = MODIS_NDVI.select('NDVI').filterDate(start, end);
    // Guard against empty collection (some months have no composites)
    var img = ee.Algorithms.If(
      col.size().gt(0),
      col.mean().multiply(0.0001),
      ee.Image.constant(-9999).rename('NDVI')
    );
    var vals = ee.Image(img).reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: CATCHMENT,
      scale: 250,
      maxPixels: 1e9
    });
    return ee.Feature(null, vals.set('date', dateStr));
  });
}).flatten();

var ndviFC = ee.FeatureCollection(ndviList);

Export.table.toDrive({
  collection: ndviFC,
  description: 'ndvi_monthly',
  folder: 'DVC_drivers',
  fileNamePrefix: 'ndvi_monthly',
  fileFormat: 'CSV',
  selectors: ['date', 'NDVI']
});

print('NDVI rows (expect 264):', ndviFC.size());

// ═══════════════════════════════════════════════════════
// SECTION 6: MODIS Actual ET monthly (MOD16A2, 8-day, 500m)
// ═══════════════════════════════════════════════════════

var MODIS_ET = ee.ImageCollection('MODIS/006/MOD16A2');

var aetList = years.map(function(year) {
  return months.map(function(month) {
    var start   = ee.Date.fromYMD(year, month, 1);
    var end     = start.advance(1, 'month');
    var dateStr = start.format('YYYY-MM-dd');
    var col = MODIS_ET.select('ET').filterDate(start, end);
    // Guard against empty collection (cloud gaps, sparse composites)
    // Scale factor 0.1: raw units are 0.1 kg/m²/8-day → sum → monthly mm
    var img = ee.Algorithms.If(
      col.size().gt(0),
      col.sum().multiply(0.1),
      ee.Image.constant(-9999).rename('ET')
    );
    var vals = ee.Image(img).reduceRegion({
      reducer: ee.Reducer.mean(),
      geometry: CATCHMENT,
      scale: 500,
      maxPixels: 1e9
    });
    return ee.Feature(null, vals.set('date', dateStr));
  });
}).flatten();

var aetFC = ee.FeatureCollection(aetList);

Export.table.toDrive({
  collection: aetFC,
  description: 'aet_monthly',
  folder: 'DVC_drivers',
  fileNamePrefix: 'aet_monthly',
  fileFormat: 'CSV',
  selectors: ['date', 'ET']
});

print('AET rows (expect 264):', aetFC.size());

// ═══════════════════════════════════════════════════════
// SECTION 7: MODIS LULC annual (MCD12Q1, IGBP, 500m)
// ═══════════════════════════════════════════════════════

var MODIS_LULC = ee.ImageCollection('MODIS/006/MCD12Q1');

// IGBP LC_Type1 forest classes: 1=EBF, 2=EDF, 3=DNF, 4=DBF, 5=Mixed Forest
// IGBP cropland classes: 12=Croplands, 14=Cropland/Natural Mosaic
var lulcYears = ee.List.sequence(2001, 2022);

var lulcList = lulcYears.map(function(year) {
  var col = MODIS_LULC.select('LC_Type1')
              .filterDate(ee.Date.fromYMD(year, 1, 1),
                          ee.Date.fromYMD(ee.Number(year).add(1), 1, 1));

  // Guard: .first() returns null when no image for that year
  var img = ee.Image(ee.Algorithms.If(
    col.size().gt(0),
    col.first(),
    ee.Image.constant(0).rename('LC_Type1').toUint8()
  ));

  var total = img.reduceRegion({
    reducer: ee.Reducer.count(),
    geometry: CATCHMENT,
    scale: 500,
    maxPixels: 1e9
  }).getNumber('LC_Type1');

  // Avoid divide-by-zero when total = 0 (fallback image)
  var safetotal = total.max(1);

  var nForest = img.lte(5).and(img.gte(1)).rename('forest')
                  .reduceRegion({reducer: ee.Reducer.sum(),
                                 geometry: CATCHMENT, scale: 500, maxPixels: 1e9})
                  .getNumber('forest');

  var nCrop = img.eq(12).or(img.eq(14)).rename('crop')
                .reduceRegion({reducer: ee.Reducer.sum(),
                               geometry: CATCHMENT, scale: 500, maxPixels: 1e9})
                .getNumber('crop');

  return ee.Feature(null, {
    'year':           year,
    'LC_forest_frac': nForest.divide(safetotal),
    'LC_crop_frac':   nCrop.divide(safetotal)
  });
});

var lulcFC = ee.FeatureCollection(lulcList);

Export.table.toDrive({
  collection: lulcFC,
  description: 'lulc_annual',
  folder: 'DVC_drivers',
  fileNamePrefix: 'lulc_annual',
  fileFormat: 'CSV',
  selectors: ['year', 'LC_forest_frac', 'LC_crop_frac']
});

print('LULC rows (expect 22):', lulcFC.size());

// ═══════════════════════════════════════════════════════
// SECTION 8: DMSP-OLS Night Lights annual 2002–2013
// ═══════════════════════════════════════════════════════

var DMSP = ee.ImageCollection('NOAA/DMSP-OLS/NIGHTTIME_LIGHTS');

var ntlYears = ee.List.sequence(2002, 2013);

var ntlList = ntlYears.map(function(year) {
  var img = DMSP.select('stable_lights')
              .filterDate(ee.Date.fromYMD(year, 1, 1),
                          ee.Date.fromYMD(ee.Number(year).add(1), 1, 1))
              .mean();
  var vals = img.reduceRegion({
    reducer: ee.Reducer.mean(),
    geometry: CATCHMENT,
    scale: 927,
    maxPixels: 1e9
  });
  return ee.Feature(null, vals.set('year', year));
});

var ntlFC = ee.FeatureCollection(ntlList);

Export.table.toDrive({
  collection: ntlFC,
  description: 'ntl_dmsp_annual',
  folder: 'DVC_drivers',
  fileNamePrefix: 'ntl_dmsp_annual',
  fileFormat: 'CSV',
  selectors: ['year', 'stable_lights']
});

print('NTL rows (expect 12):', ntlFC.size());

// ═══════════════════════════════════════════════════════
// Console summary
// ═══════════════════════════════════════════════════════
print('=== Stage 2 Driver Extraction — 6 exports submitted ===');
print('Catchment: [86.40, 23.20, 87.50, 24.20] (upper Damodar basin)');
print('Period: 2002-01 to 2023-12 (264 months)');
print('After export: download DVC_drivers/ from Drive → data/raw/');
print('Then run: uv run python src/02_feature_engineering.py');
