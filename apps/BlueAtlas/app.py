
# app.py
# GEE Water & Indices Explorer (no TF/PyTorch)
# Author: Vamsha Shetty + Copilot
import os
from datetime import datetime
from pathlib import Path

import ee
import folium
import gradio as gr
import yaml
from dotenv import load_dotenv

# ---------------------------- Config & Auth ----------------------------
load_dotenv()
GEE_PROJECT = os.getenv('GEE_PROJECT')

# palettes / CSS (yellow-black-red accent per Vamsha preferences)
CUSTOM_CSS = """
:root { --accent: #ffc400; --background-fill-primary: #0b0b0b; --block-title-text-color: #ffc400; }
.gradio-container { background: #0b0b0b; color: #f2f2f2; }
button { background: #111; border: 1px solid #333; }
button.primary { background: #ffc400; color: #111; }
label, .label-wrap { color: #ddd; }
"""

PRESETS_FILE = Path(__file__).with_name('presets.yaml')

def load_presets():
    if PRESETS_FILE.exists():
        try:
            return yaml.safe_load(PRESETS_FILE.read_text()) or {}
        except Exception:
            return {}
    return {}


def _ensure_ee_initialized():
    try:
        if GEE_PROJECT:
            ee.Initialize(project=GEE_PROJECT)
        else:
            ee.Initialize()
    except Exception:
        ee.Authenticate()
        if GEE_PROJECT:
            ee.Initialize(project=GEE_PROJECT)
        else:
            ee.Initialize()

# ---------------------------- Cloud masks ----------------------------

def mask_s2_sr(image: ee.Image) -> ee.Image:
    qa = image.select('QA60')
    cloud_bit = 1 << 10
    cirrus_bit = 1 << 11
    qa_clear = qa.bitwiseAnd(cloud_bit).eq(0).And(qa.bitwiseAnd(cirrus_bit).eq(0))

    scl = image.select('SCL')
    mask = (qa_clear
            .And(scl.neq(3))   # shadow
            .And(scl.neq(8))   # medium cloud
            .And(scl.neq(9))   # high cloud
            .And(scl.neq(10))) # cirrus
    return image.updateMask(mask).divide(10000)


def mask_l8_sr(image: ee.Image) -> ee.Image:
    qa = image.select('QA_PIXEL')
    clear = (qa.bitwiseAnd(1 << 3).eq(0)  # shadow
             .And(qa.bitwiseAnd(1 << 5).eq(0))  # cloud
             .And(qa.bitwiseAnd(1 << 9).eq(0))) # cirrus
    scaled = image.updateMask(clear)
    sr = scaled.select(['SR_B2','SR_B3','SR_B4','SR_B5','SR_B6','SR_B7']).multiply(0.0000275).add(-0.2)
    return sr.rename(['B2','B3','B4','B5','B6','B7'])

# ---------------------------- Indices ----------------------------
INDEX_HELP = {
    'NDVI': 'Normalized Difference Vegetation Index (NIR-Red)/(NIR+Red)',
    'NDWI': 'McFeeters NDWI (Green-NIR)/(Green+NIR)',
    'MNDWI': 'Modified NDWI (Green-SWIR1)/(Green+SWIR1)',
    'NBR':  'Normalized Burn Ratio (NIR-SWIR2)/(NIR+SWIR2)',
    'NDTI': 'Normalized Difference Turbidity Index (Red-Blue)/(Red+Blue)'
}

def calc_index(image: ee.Image, satellite: str, index: str) -> ee.Image:
    if satellite == 'Sentinel-2':
        b = {'BLUE':'B2','GREEN':'B3','RED':'B4','NIR':'B8','SWIR1':'B11','SWIR2':'B12'}
    else:
        b = {'BLUE':'B2','GREEN':'B3','RED':'B4','NIR':'B5','SWIR1':'B6','SWIR2':'B7'}
    if index == 'NDVI':
        idx = image.normalizedDifference([b['NIR'], b['RED']]).rename('NDVI')
    elif index == 'NDWI':
        idx = image.normalizedDifference([b['GREEN'], b['NIR']]).rename('NDWI')
    elif index == 'MNDWI':
        idx = image.normalizedDifference([b['GREEN'], b['SWIR1']]).rename('MNDWI')
    elif index == 'NBR':
        idx = image.normalizedDifference([b['NIR'], b['SWIR2']]).rename('NBR')
    elif index == 'NDTI':
        idx = image.normalizedDifference([b['RED'], b['BLUE']]).rename('NDTI')
    else:
        raise ValueError(f'Unsupported index: {index}')
    return image.addBands(idx)

# ------------------------- Core processing -------------------------

def load_composite(aoi: ee.Geometry, start_date: str, end_date: str, satellite: str, cloud_pct: int=20) -> ee.Image:
    if satellite == 'Sentinel-2':
        col = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
               .filterDate(start_date, end_date)
               .filterBounds(aoi)
               .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_pct))
               .map(mask_s2_sr))
        comp = col.median().select(['B2','B3','B4','B8','B11','B12'])
    else:
        col = (ee.ImageCollection('LANDSAT/LC08/C02/T1_SR')
               .filterDate(start_date, end_date)
               .filterBounds(aoi)
               .filter(ee.Filter.lt('CLOUD_COVER', cloud_pct))
               .map(mask_l8_sr))
        comp = col.median().select(['B2','B3','B4','B5','B6','B7'])
    return comp


def make_map(aoi: ee.Geometry, composite: ee.Image, satellite: str, index_name: str, threshold: float|None=None) -> folium.Map:
    img = calc_index(composite, satellite, index_name)
    lon, lat = aoi.centroid().coordinates().getInfo()
    m = folium.Map(location=[lat, lon], zoom_start=11, control_scale=True)

    # true color
    tc = composite.select(['B4','B3','B2'])
    tc_mapid = ee.data.getMapId({'image': tc, 'visParams': {'min':0, 'max':0.3, 'gamma':1.2}})
    folium.TileLayer(tiles=tc_mapid['tile_fetcher'].url_format, name=f'{satellite} True Color').add_to(m)

    palette_map = {
        'NDVI':['#440154','#3b528b','#21918c','#5ec962','#fde725'],
        'NDWI':['#8c510a','#d8b365','#f6e8c3','#c7eae5','#5ab4ac','#01665e'],
        'MNDWI':['#8c510a','#d8b365','#f6e8c3','#c7eae5','#5ab4ac','#01665e'],
        'NBR':['#7f0000','#b30000','#f3f3f3','#4daf4a','#006837'],
        'NDTI':['#313695','#4575b4','#74add1','#ffffbf','#f46d43','#a50026']
    }
    idx_band = img.select(index_name)
    idx_mapid = ee.data.getMapId({'image': idx_band, 'visParams': {'min':-0.5,'max':0.8,'palette':palette_map[index_name]}})
    folium.TileLayer(tiles=idx_mapid['tile_fetcher'].url_format, name=index_name).add_to(m)

    if index_name in ('NDWI','MNDWI') and threshold is not None:
        wm = idx_band.gt(threshold)
        wm_mapid = ee.data.getMapId({'image': wm.updateMask(wm), 'visParams': {'palette':['#00ffff']}})
        folium.TileLayer(tiles=wm_mapid['tile_fetcher'].url_format, name=f'Water mask ({index_name}>{threshold})').add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    return m

# ------------------------------ UI ---------------------------------

def app(lat: float, lon: float, buffer_km: float, start_date: str, end_date: str, satellite: str, index_name: str, threshold: float):
    _ensure_ee_initialized()
    try:
        datetime.fromisoformat(start_date); datetime.fromisoformat(end_date)
    except Exception as e:
        return f"<p style='color:red'>Invalid date: {e}</p>"
    aoi = ee.Geometry.Point([lon, lat]).buffer(buffer_km*1000).bounds()
    comp = load_composite(aoi, start_date, end_date, satellite)
    m = make_map(aoi, comp, satellite, index_name, threshold if index_name in ('NDWI','MNDWI') else None)
    return m._repr_html_()


def build_ui():
    presets = load_presets()
    names = list(presets.keys())
    with gr.Blocks(title='GEE Water & Indices Explorer', css=CUSTOM_CSS) as demo:
        gr.Markdown("""### GEE Water & Indices Explorer
**Tip**: Pick a preset AOI, then adjust dates or NDWI/MNDWI **water threshold**.
""")
        with gr.Row():
            lat = gr.Number(value=13.3409, label='Latitude')
            lon = gr.Number(value=74.7421, label='Longitude')
            buffer_km = gr.Slider(0.5, 25.0, value=2.0, step=0.5, label='AOI buffer (km)')
        with gr.Row():
            start_date = gr.Textbox(value='2023-01-01', label='Start date (YYYY-MM-DD)')
            end_date = gr.Textbox(value='2023-12-31', label='End date (YYYY-MM-DD)')
        with gr.Row():
            satellite = gr.Dropdown(['Sentinel-2','Landsat 8/9'], value='Sentinel-2', label='Satellite')
            index_name = gr.Dropdown(['NDVI','NDWI','MNDWI','NBR','NDTI'], value='NDWI', label='Index')
            threshold = gr.Slider(-0.2, 0.6, value=0.0, step=0.02, label='Water threshold')
        with gr.Row():
            preset = gr.Dropdown(names, label='Preset AOI', value=names[0] if names else None)
            def fill_from_preset(name):
                if not name or name not in presets: return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
                p = presets[name]
                return p.get('lat'), p.get('lon'), p.get('buffer_km',2.0), p.get('start','2023-01-01'), p.get('end','2023-12-31'), p.get('threshold',0.0)
            preset.change(fill_from_preset, inputs=preset, outputs=[lat, lon, buffer_km, start_date, end_date, threshold])

        go = gr.Button('Generate Map', variant='primary')
        out = gr.HTML()
        go.click(app, inputs=[lat, lon, buffer_km, start_date, end_date, satellite, index_name, threshold], outputs=out)
    return demo

if __name__ == '__main__':
    ui = build_ui()
    ui.launch(share=False)
