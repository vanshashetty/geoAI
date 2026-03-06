import importlib
app = importlib.import_module("app")


def test_index_formulas_exist():
    assert "NDVI" in app.INDEX_HELP and "NDWI" in app.INDEX_HELP
