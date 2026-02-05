# Design — Geospatial Deep Learning for Clean Water & Land Cover

## 1) System Context
The system ingests Sentinel‑2 scenes (via Sentinel Hub or GEE), computes NDVI, trains a **TensorFlow CNN** for land cover classification and a **PyTorch U‑Net** for segmentation, then exports **GeoTIFF** outputs for QGIS/GEE and optionally ranks clean water sources via simple GIS overlays and scoring.

## 2) High‑Level Architecture
```
+-------------------+            +------------------+          +-------------------+
|  Sentinel Hub /   |            |  Preprocessing   |          |  Modeling         |
|  GEE (S2 L2A)     |--B02/3/4/8-|  (normalize,     |--tensors-|  TF CNN (cls)     |
|  (EO Provider)    |            |  NDVI, tiling)   |          |  PT U-Net (segm)  |
+---------+---------+            +---------+--------+          +---------+---------+
          |                                 |                             |
          |                                 v                             v
          |                        +--------+--------+           +--------+--------+
          |                        |  Visualization  |           |  Exporter        |
          |                        |  (RGB, NDVI)    |           |  GeoTIFF + CRS   |
          |                        +--------+--------+           +--------+--------+
          |                                 |                             |
          |                                 v                             v
          |                        +--------+--------+           +--------+--------+
          |                        |  QGIS Desktop   |           |  GEE Asset       |
          |                        +-----------------+           +------------------+
          |
          +-----------------------> Optional: Clean Water Ranking (buffers, overlays, scoring)
```

## 3) Data Flow & Formats
1. Acquisition: TIFF/PNG from Sentinel Hub, or `ee.ImageCollection` from GEE filtered by AOI/date/clouds.
2. Preprocessing: scale to [0,1], compute NDVI, stack into 4‑channel arrays, optionally patch to 128×128 tiles.
3. Training Inputs: classifier (N,128,128,4) and segmenter (N,4,128,128) with integer masks.
4. Outputs: class probabilities / segmentation masks → GeoTIFF with geotransform + CRS.
5. GIS Integration: QGIS styling; GEE upload and visualization.

## 4) Key Components
- Data access layer (Sentinel Hub / GEE)
- Preprocessing & NDVI utilities
- TF CNN classifier and PT U‑Net segmenter
- GeoTIFF exporter
- Optional clean water ranking module

## 5) Algorithms & Training
- Classification: categorical cross‑entropy (Adam), basic augmentation optional.
- Segmentation: cross‑entropy (Adam) for compact U‑Net.
- Ranking: weighted linear score over NDVI, distance-to-pollution, protected-area flag, elevation.

## 6) Data Model
- Raster tensors: float32 (H,W,4) [B02,B03,B04,NDVI]; masks: uint8 (H,W).
- Vector layers: candidate points with attributes (`score`, `ndvi_avg`, `dist_pollution_km`, `protected_flag`, `elevation_m`).

## 7) Evaluation
- Classification: accuracy, precision/recall, confusion matrix.
- Segmentation: pixel accuracy and (optional) mIoU.
- GIS sanity checks: QGIS visual inspection, NDVI histograms.

## 8) Security & Compliance
- Use `.env` or secret manager for credentials. Respect data licensing.

## 9) Scalability & Extensibility
- Use GEE for large‑area inference/visualization; swap in advanced models; add indices (NDWI/SAVI) or bands (SWIR).

## 10) Dev Workflow
- Branching: `main` (stable) / `feature/*` (experiments). CI runs lint + unit tests.
