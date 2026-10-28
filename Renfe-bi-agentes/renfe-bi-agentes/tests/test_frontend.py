"""Tests de la API del frontend (frontend/app.py) levantando el servidor HTTP local."""
import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

import pytest

from frontend import app


@pytest.fixture(scope="module")
def base():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), app.Manejador)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def get(base, ruta):
    with urllib.request.urlopen(base + ruta, timeout=30) as r:
        return r.status, r.headers.get("Content-Type"), r.read()


def get_json(base, ruta):
    return json.loads(get(base, ruta)[2])


def test_sirve_la_interfaz(base):
    st, tipo, cuerpo = get(base, "/")
    assert st == 200 and tipo.startswith("text/html") and b"Radar Competitivo AV" in cuerpo
    assert get(base, "/chart.umd.min.js")[0] == 200


def test_resumen(base):
    d = get_json(base, "/api/resumen")
    assert len(d["corredores"]) == 5 and all(c["accion"] for c in d["corredores"])
    assert d["total_2025"]["viajeros_millones"] == 44.5


def test_corredor_y_simulador(base):
    d = get_json(base, "/api/corredor?id=SEV")
    assert d["recomendacion"]["accion"] == "RECUPERAR DEMANDA" and d["elasticidad"]["resumen"]
    s = get_json(base, "/api/simular?id=BCN&pct=5")
    assert set(s["escenarios"]) == {"central", "optimista", "pesimista"}
    s = get_json(base, "/api/simular?id=ALI&pct=-10&elasticidad=-1")
    assert list(s["escenarios"]) == ["central"]


def test_resto_de_endpoints(base):
    assert get_json(base, "/api/estado")["ok"]
    assert len(get_json(base, "/api/fuentes")["filas"]) == 14
    assert get_json(base, "/api/competidores?empresa=Iryo")["filas"]
    assert get_json(base, "/api/demanda")["modo"] == "snapshot"


def test_errores_controlados(base):
    with pytest.raises(urllib.error.HTTPError) as e:
        get(base, "/api/corredor?id=XXX")
    assert e.value.code == 400
    with pytest.raises(urllib.error.HTTPError) as e:
        get(base, "/../.env")
    assert e.value.code == 404
