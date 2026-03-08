
# BlueAtlas — Clean Water Geospatial ML + GEE Water Indices Explorer

Blue Atlas is a satellite‑driven water‑intelligence system designed to detect, quantify, and monitor surface‑water presence and dynamics using multispectral Earth‑observation data. Leveraging atmospherically corrected surface‑reflectance products from the Sentinel‑2 SR (HARMONIZED) constellation, which provides operational 10–20 m multispectral measurements suitable for consistent cross‑date hydrological analysis, and Landsat 8/9 Level‑2 products that offer calibrated VNIR and SWIR reflectance with global continuity for long‑term surface‑water monitoring, Blue Atlas constructs harmonized temporal composites to characterize water signatures across diverse landforms.<img width="6917" height="49" alt="image" src="https://github.com/user-attachments/assets/3f3b2e9f-604c-41c3-9910-c0f8504626f8" />


**geoAI** is a poly‑repo for **geospatial ML** (TensorFlow/PyTorch workflows) plus a lightweight **Google Earth Engine (GEE) Water & Indices Explorer** for quick, no‑GPU exploration of **Sentinel‑2** and **Landsat 8/9**.  
The GEE app builds **cloud‑masked composites** and visualizes **NDVI, NDWI, MNDWI, NBR, NDTI** with an interactive **Gradio + Folium** UI.

*   The **ML stack** (training/inference, notebooks, scripts) remains **unchanged**.
*   The **GEE app** lives under `apps/BlueAtlas/` and can be run or deployed independently.

***

##  Features

*   **Fast water‑centric exploration** (no ML libraries required)
*   **Cloud masking**:
    *   Sentinel‑2: `QA60` bits 10/11 (opaque/cirrus) + `SCL` excludes 3 (shadow), 8/9 (cloud), 10 (cirrus)
    *   Landsat 8/9: `QA_PIXEL` bits 3 (shadow), 5 (cloud), 9 (cirrus)
*   **Indices**:
    *   NDVI = (NIR − Red)/(NIR + Red)
    *   NDWI (McFeeters) = (Green − NIR)/(Green + NIR)
    *   MNDWI (Xu) = (Green − SWIR1)/(Green + SWIR1)
    *   NBR = (NIR − SWIR2)/(NIR + SWIR2)
    *   NDTI = (Red − Blue)/(Red + Blue)
*   **Presets** via `presets.yaml` (saved AOIs & thresholds)
*   **Clean UI** with a yellow‑black‑red theme

> **Note:** NDWI/MNDWI thresholds are scene‑dependent. Start near `0.00` and explore `−0.10 … +0.30` based on season/sensor.

***

##  Repository Layout

    geoAI/
    ├─ README.md                     # ← this file
    ├─ requirements.txt              # ML stack deps (TF/PyTorch etc.)
    ├─ docs/
    │  ├─ design.md                  # Architecture for ML + GEE explorer (Mermaid)
    │  └─ requirements.md            # (optional, if present)
    ├─ src/                          # ML modules (tba)
    ├─ scripts/                      # CLI helpers (tba)
    ├─ notebooks/                    # Jupyter workflows (unchanged)
    ├─ tests/                        # ML/unit tests (unchanged)
    ├─ .github/workflows/            # CI for repo (tba)
    └─ apps/
       └─ BlueAtlas/        # NEW: Standalone GEE UI (no ML deps)
          ├─ app.py
          ├─ requirements.txt        # earthengine-api, folium, gradio, PyYAML, dotenv
          ├─ presets.yaml            # saved AOIs and thresholds
          ├─ Dockerfile              # slim container for Cloud Run
          ├─ deploy_cloud_run.sh     # gcloud deploy helper
          └─ README_SPACES.md        # tips for Hugging Face Spaces

Why separate `requirements.txt`?

*   Root env: **ML stack** (heavy)
*   App env: **GEE UI only** (light)  
    This keeps installs fast and containers small.

***

##  Quickstarts

### A) Run the **GEE Water & Indices Explorer** (no ML deps)

```bash
cd apps/BlueAtlas
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Must be a GEE-registered Google Cloud project ID
export GEE_PROJECT=<your-gee-registered-gcp-project-id>

python app.py
```

*   First run triggers a one‑time `ee.Authenticate()`; later runs reuse cached creds.
*   Choose **Sentinel‑2** or **Landsat 8/9**, pick an index (NDVI/NDWI/MNDWI/NBR/NDTI), and (optionally) set **NDWI/MNDWI threshold** to draw a **Water mask**.
*   Quick run from repo root (no venv creation shown):

```bash
python apps/BlueAtlas/app.py
```

### B) Run the **ML stack** (original flows; TF/PyTorch)

```bash
# from repo root
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# then your usual scripts/notebooks, e.g.:
python scripts/<your_cli>.py
# or
jupyter lab
```

***

##  Deployment (optional)

### Hugging Face Spaces (Gradio)

```bash
# Create a new Gradio Space and push only the app folder contents
cd apps/BlueAtlas
# Upload app.py + requirements.txt (+ presets.yaml if you want)
# Add a Space secret named: GEE_PROJECT
```

### Google Cloud Run (container + HTTPS + autoscaling)

```bash
cd apps/BlueAtlas
export PROJECT=<your-project-id>
bash deploy_cloud_run.sh
```

The script:

*   Builds a slim image from this folder
*   Deploys to Cloud Run
*   Sets `GEE_PROJECT=$PROJECT`

***

##  Tips & Thresholds

*   **NDWI/MNDWI thresholds**: start at `0.00`, explore `−0.10 … +0.30` depending on turbidity/sunglint/season.
*   **Empty composites**: widen dates, increase cloud % filter, grow AOI buffer.
*   **Auth loops**: clear cached EE creds and re‑run `app.py`.

***

##  Optional Makefile (copy & paste)

> Tabs are **real tabs** below (required by `make`).

```makefile
.PHONY: gee run-gee docker-gee

gee:
	python -m venv .venv_gee && . .venv_gee/bin/activate && pip install -r apps/BlueAtlas/requirements.txt

run-gee:
	cd apps/BlueAtlas && GEE_PROJECT=$(GEE_PROJECT) python app.py

docker-gee:
	cd apps/BlueAtlas && docker build -t gee-water . && docker run -p 7860:7860 --env GEE_PROJECT=$(GEE_PROJECT) gee-water
```

Usage:

```bash
make gee
GEE_PROJECT=<your-project> make run-gee
```

***

##  Notes

*   The GEE app is **qualitative** for water presence/turbidity proxies (NDWI/MNDWI/NDTI).  
    Quantitative water‑quality (e.g., chlorophyll‑a, TSS) needs sensor‑specific algorithms and in‑situ calibration/validation.
*   Keep **ML** and **GEE UI** environments separate for a clean developer experience.

***

##  License

MIT (see `LICENSE`).

***

## Ideator

**Vamsha Shetty** (@vanshashetty)

***

### Appendix — Handy one‑liners

**From root:**

```bash
python apps/BlueAtlas/app.py
```

**Docker (local):**

```bash
cd apps/BlueAtlas
docker build -t gee-water .
docker run -p 7860:7860 --env GEE_PROJECT=<your-project> gee-water
```

**Create `.env` next to app.py (optional alternative to export):**

```bash
cd apps/BlueAtlas
printf "GEE_PROJECT=<your-gee-project-id>\n" > .env
python app.py
```


Recorded video of the prototype: 
[Recording 2026-03-06 224027.zip](https://github.com/user-attachments/files/25816805/Recording.2026-03-06.224027.zip)
