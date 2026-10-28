"""Tests del conector INE con una respuesta con la estructura real de la API Tempus3."""
import json
from pathlib import Path

import pytest

from mcp_server import ine_client

FIX = json.loads((Path(__file__).parent / "fixtures/ine_49359_muestra.json").read_text(encoding="utf-8"))


def test_parsea_y_filtra_variaciones():
    series = ine_client.parsear_series(FIX)
    nombres = [s["nombre"] for s in series]
    assert len(series) == 2
    assert all("Variación" not in n for n in nombres)
    ave = series[0]
    assert ave["datos"] == [{"periodo": "2026-01", "valor": 2.10}, {"periodo": "2026-02", "valor": 1.95}]


def test_descarta_valores_nulos():
    bus = [s for s in ine_client.parsear_series(FIX) if "autobús" in s["nombre"]][0]
    assert len(bus["datos"]) == 1


def test_formato_invalido():
    with pytest.raises(ine_client.INEError):
        ine_client.parsear_series({"error": "x"})


def test_demanda_en_vivo_con_descarga_simulada(monkeypatch):
    monkeypatch.setattr(ine_client, "descargar_tabla", lambda *a, **k: FIX)
    r = ine_client.demanda_en_vivo()
    assert r["n_series"] == 2 and r["tabla"] == 49359


@pytest.mark.live
def test_api_ine_real():
    """Ejecutar con: pytest -m live (requiere Internet)."""
    r = ine_client.ping()
    assert r["ok"], r
