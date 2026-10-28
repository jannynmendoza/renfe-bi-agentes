"""
Frontend de escritorio del Radar Competitivo de Alta Velocidad.

Levanta un servidor HTTP local (solo 127.0.0.1) que expone bi_core como API JSON y sirve
la interfaz de frontend/static. La interfaz se abre en una ventana propia (pywebview) o,
si no está disponible, en el navegador.

Los datos salen del mismo sitio que el servidor MCP: Supabase si SUPABASE_DB_URL está
definida (en un .env junto al .exe o en el del proyecto), si no los CSV de data/.

Uso:   python frontend/app.py [--navegador | --servidor]
       --navegador  abre la interfaz en el navegador en lugar de en una ventana propia
       --servidor   solo levanta el servidor (puerto fijo con RADAR_PUERTO)
Empaquetado (.exe):  ver frontend/build_exe.ps1
"""
from __future__ import annotations

import json
import sys
import threading
import traceback
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Recursos (static, data, mcp_server): dentro del .exe están en sys._MEIPASS
CONGELADO = getattr(sys, "frozen", False)
RECURSOS = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
APP_DIR = Path(sys.executable).parent if CONGELADO else RECURSOS
STATIC = RECURSOS / "frontend" / "static"

# En un .exe sin consola stdout/stderr son None y cualquier print fallaría
if sys.stdout is None or sys.stderr is None:
    import os
    sys.stdout = sys.stderr = open(os.devnull, "w", encoding="utf-8")

sys.path.insert(0, str(RECURSOS))
try:  # el .env junto al .exe tiene prioridad sobre el del proyecto
    from dotenv import load_dotenv
    load_dotenv(APP_DIR / ".env")
except ImportError:
    pass

from mcp_server import bi_core as core  # noqa: E402
from mcp_server import ine_client  # noqa: E402

TIPOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".ico": "image/x-icon"}


def _num(v: str | None) -> float | None:
    return float(v) if v not in (None, "") else None


# ------------------------------------------------------------------ endpoints
def api_estado(q):
    return core.estado_datos()


def api_resumen(q):
    filas = core.comparar_corredores()
    for f in filas:
        rec = core.recomendar_accion(f["corredor_id"])
        f["accion"], f["confianza"] = rec["accion"], rec["confianza"]
    total = next((r for r in core.cargar("viajeros_anual") if r["corredor_id"] == "TOTAL"), {})
    return {"corredores": filas, "total_2025": total, "serie_total": core.serie_viajeros("TOTAL"),
            "origen": core.ORIGEN}


def api_corredor(q):
    cid = q.get("id", "BCN")
    return {**core.kpis_corredor(cid), "recomendacion": core.recomendar_accion(cid),
            "elasticidad": core.elasticidad_precio(cid)}


def api_simular(q):
    return core.simular_escenario_precio(q.get("id", "BCN"), _num(q.get("pct")) or 0.0,
                                         _num(q.get("elasticidad")))


def api_competidores(q):
    return {"filas": core.datos_competidores(q.get("empresa") or None)}


def api_demanda(q):
    if q.get("vivo") != "1":
        return {"modo": "snapshot", "filas": core.demanda_mensual()}
    try:
        return {"modo": "en_vivo", **ine_client.demanda_en_vivo()}
    except ine_client.INEError as e:
        return {"modo": "snapshot (fallback)", "error_en_vivo": str(e), "filas": core.demanda_mensual()}


def api_fuentes(q):
    return {"filas": core.fuentes()}


def api_recargar(q):
    core.cargar.cache_clear()
    if hasattr(core, "_cargar_supabase"):
        core._cargar_supabase.cache_clear()
    return core.estado_datos()


RUTAS = {
    "/api/estado": api_estado, "/api/resumen": api_resumen, "/api/corredor": api_corredor,
    "/api/simular": api_simular, "/api/competidores": api_competidores,
    "/api/demanda": api_demanda, "/api/fuentes": api_fuentes, "/api/recargar": api_recargar,
}


class Manejador(BaseHTTPRequestHandler):
    def log_message(self, *args):  # silencioso
        pass

    def _enviar(self, codigo: int, cuerpo: bytes, tipo: str):
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _json(self, codigo: int, datos):
        self._enviar(codigo, json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8"),
                     "application/json; charset=utf-8")

    def do_GET(self):
        url = urlparse(self.path)
        if url.path in RUTAS:
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            try:
                self._json(200, RUTAS[url.path](q))
            except core.DatoNoDisponible as e:
                self._json(400, {"error": str(e)})
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                self._json(500, {"error": f"{type(e).__name__}: {e}"})
            return
        nombre = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
        ruta = (STATIC / nombre).resolve()
        if STATIC.resolve() not in ruta.parents or not ruta.is_file():
            self._enviar(404, b"No encontrado", "text/plain; charset=utf-8")
            return
        self._enviar(200, ruta.read_bytes(), TIPOS.get(ruta.suffix, "application/octet-stream"))

    do_POST = do_GET


def main() -> None:
    import os
    servidor = ThreadingHTTPServer(("127.0.0.1", int(os.environ.get("RADAR_PUERTO", "0"))), Manejador)
    url = f"http://127.0.0.1:{servidor.server_port}/"
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    if "--servidor" in sys.argv:  # solo API + web, sin abrir ventana ni navegador
        print(f"Servidor en {url}")
        threading.Event().wait()

    if "--navegador" not in sys.argv:
        try:
            import webview
            webview.create_window("Radar Competitivo AV · Renfe Viajeros", url,
                                  width=1380, height=900, min_size=(1000, 680))
            webview.start()
            return
        except Exception as e:  # noqa: BLE001
            print(f"No se pudo abrir la ventana de escritorio ({e}); se usa el navegador.")

    print(f"Radar Competitivo AV en {url}  (Ctrl+C o cerrar esta ventana para salir)")
    webbrowser.open(url)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
