"""
Conector en vivo con la API JSON del INE (Tempus3) — sin claves, sin dependencias.

Tabla por defecto: 49359 "Total de viajeros por tipo, medio de transporte (terrestre,
aéreo y marítimo) y distancia" (Estadística de Transporte de Viajeros, mensual), que
incluye la serie de alta velocidad de Renfe (AVE) junto a autobús y avión.

Documentación de la API: https://www.ine.es/dyngs/DAB/index.htm?cid=1099
"""
from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.request
from typing import Any

INE_BASE = "https://servicios.ine.es/wstempus/js/ES/DATOS_TABLA/{tabla}"
TABLA_DEFECTO = 49359
FILTRO_DEFECTO = r"(alta velocidad|AVE|larga distancia|a[eé]reo|autob[uú]s)"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


class INEError(RuntimeError):
    pass


def _ssl_context() -> ssl.SSLContext:
    cafile = os.environ.get("SSL_CERT_FILE") or os.environ.get("REQUESTS_CA_BUNDLE")
    return ssl.create_default_context(cafile=cafile) if cafile else ssl.create_default_context()


def descargar_tabla(tabla: int = TABLA_DEFECTO, ultimos: int = 12, timeout: float = 20.0) -> Any:
    """Descarga la tabla del INE. `ultimos` = número de periodos más recientes (nult)."""
    url = INE_BASE.format(tabla=int(tabla)) + f"?nult={int(ultimos)}"
    req = urllib.request.Request(url, headers={"User-Agent": "renfe-bi-agentes/1.0 (TFM INESDI)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise INEError(f"No se pudo leer {url}: {e}") from e


def parsear_series(payload: Any, filtro: str = FILTRO_DEFECTO,
                   solo_viajeros: bool = True) -> list[dict[str, Any]]:
    """
    Convierte la respuesta Tempus3 ([{COD, Nombre, Data:[{Anyo, FK_Periodo, Valor}]}])
    en una lista limpia. Filtra por nombre de serie (regex, sin distinguir mayúsculas)
    y, por defecto, descarta las series de variación (%).
    """
    if not isinstance(payload, list):
        raise INEError("Formato inesperado: se esperaba una lista de series")
    patron = re.compile(filtro, re.IGNORECASE)
    salida = []
    for serie in payload:
        nombre = str(serie.get("Nombre", ""))
        if not patron.search(nombre):
            continue
        if solo_viajeros and re.search(r"variaci[oó]n", nombre, re.IGNORECASE):
            continue
        datos = []
        for d in serie.get("Data") or []:
            if d.get("Valor") is None:
                continue
            mes = d.get("FK_Periodo")
            etiqueta = f"{d.get('Anyo')}-{int(mes):02d}" if isinstance(mes, int) and 1 <= mes <= 12 else str(d.get("Anyo"))
            datos.append({"periodo": etiqueta, "valor": d["Valor"]})
        salida.append({"cod": serie.get("COD"), "nombre": nombre.strip(),
                       "datos": sorted(datos, key=lambda x: x["periodo"])})
    return salida


def demanda_en_vivo(tabla: int = TABLA_DEFECTO, filtro: str = FILTRO_DEFECTO,
                    ultimos: int = 12) -> dict[str, Any]:
    series = parsear_series(descargar_tabla(tabla, ultimos), filtro)
    return {"tabla": tabla, "fuente": INE_BASE.format(tabla=tabla), "n_series": len(series), "series": series}


def ping(timeout: float = 10.0) -> dict[str, Any]:
    """Comprobación ligera de conectividad con la API del INE."""
    try:
        payload = descargar_tabla(TABLA_DEFECTO, ultimos=1, timeout=timeout)
        return {"ok": True, "series_en_tabla": len(payload)}
    except INEError as e:
        return {"ok": False, "error": str(e)}
