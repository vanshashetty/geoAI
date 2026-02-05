
# Clean Water Geospatial ML

An end-to-end, repo-ready scaffold for geospatial deep learning with **Sentinel-2**, **TensorFlow** (classification), **PyTorch** (segmentation), **NDVI** preprocessing, **GeoTIFF** export, and optional **QGIS/GEE** integration. Includes a simple GIS-based **clean water source ranking** demo.

> Quick start: create a Python env, install `requirements.txt`, copy `.env.example` to `.env`, then run the scripts/notebooks under `notebooks/` and `scripts/`.

## Contents
- `docs/requirements.md` — functional/non-functional requirements
- `docs/design.md` — high-level design and architecture
- `src/` — Python modules for data access, preprocessing, models, export
- `scripts/` — CLI-style scripts for quick tasks
- `notebooks/` — starter notebooks for each stage
- `tests/` — minimal unit tests
- `.github/workflows/` — starter CI

## Disclaimers
This is a **POC scaffold**. Replace dummy code/arrays with real Sentinel-2 pulls via **Sentinel Hub** or **Google Earth Engine**. Do not commit credentials.
