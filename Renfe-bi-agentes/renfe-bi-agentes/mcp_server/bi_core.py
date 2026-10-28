"""
Núcleo analítico del Radar Competitivo de Alta Velocidad (Renfe Viajeros).

Todo el cálculo vive aquí, en Python puro (sin dependencias externas), para que:
  * el servidor MCP (server.py) solo exponga funciones ya probadas,
  * los tests unitarios (tests/test_bi_core.py) puedan validarlas sin levantar MCP.

Los datos están en ../data/*.csv y proceden de fuentes públicas reales
(CNMC, INE, prensa económica). Cada fila lleva su `fuente_id`, resoluble con fuentes().
Las filas con tipo_dato="derivado" se calculan a partir de cifras publicadas y lo indican.
"""
from __future__ import annotations

import csv
import os
import statistics
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("RENFE_BI_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))

CORREDORES_VALIDOS = ("BCN", "VLC", "ALI", "SEV", "MAL")
ORDEN_PERIODOS = ["2025T1", "2025T2", "2025T3", "2025T4", "2026T1", "2026T2"]

TABLAS = (
    "fuentes", "corredores", "viajeros_trimestral", "viajeros_anual", "precios",
    "cuotas", "ocupacion", "demanda_mensual_ine", "eventos", "empresas",
)
_NUMERICAS = {
    "viajeros_millones", "var_interanual_pct", "precio_eur", "cuota_pct", "ocupacion_pct",
    "peso_canones_en_coste_pct", "cuota_tren_vs_avion_pct", "valor",
}


class DatoNoDisponible(ValueError):
    """Se lanza cuando se pide un corredor o métrica que no existe en los datos."""


# --------------------------------------------------------------------------- carga
def _convertir(fila: dict[str, str]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in fila.items():
        v = (v or "").strip()
        if k in _NUMERICAS:
            out[k] = float(v) if v not in ("", None) else None
        else:
            out[k] = v
    return out


@lru_cache(maxsize=None)
def cargar(tabla: str) -> tuple[dict[str, Any], ...]:
    if tabla not in TABLAS:
        raise DatoNoDisponible(f"Tabla desconocida: {tabla}")
    ruta = DATA_DIR / f"{tabla}.csv"
    with ruta.open(encoding="utf-8", newline="") as f:
        return tuple(_convertir(r) for r in csv.DictReader(f))


def _validar_corredor(corredor_id: str) -> str:
    cid = (corredor_id or "").strip().upper()
    if cid not in CORREDORES_VALIDOS:
        raise DatoNoDisponible(
            f"Corredor '{corredor_id}' no válido. Usa uno de: {', '.join(CORREDORES_VALIDOS)}"
        )
    return cid


def _orden(periodo: str) -> int:
    return ORDEN_PERIODOS.index(periodo) if periodo in ORDEN_PERIODOS else -1


# ----------------------------------------------------------------- consultas básicas
def estado_datos() -> dict[str, Any]:
    """Comprueba que todas las tablas cargan y cuenta filas (health-check)."""
    resumen = {}
    for t in TABLAS:
        try:
            resumen[t] = {"ok": True, "filas": len(cargar(t))}
        except Exception as e:  # noqa: BLE001
            resumen[t] = {"ok": False, "error": str(e)}
    return {"data_dir": str(DATA_DIR), "tablas": resumen, "ok": all(v["ok"] for v in resumen.values())}


def fuentes(fuente_ids: list[str] | None = None) -> list[dict[str, Any]]:
    filas = list(cargar("fuentes"))
    if fuente_ids:
        ids = {f.strip() for f in fuente_ids}
        filas = [f for f in filas if f["fuente_id"] in ids]
    return filas


def listar_corredores() -> list[dict[str, Any]]:
    return list(cargar("corredores"))


def serie_viajeros(corredor_id: str) -> list[dict[str, Any]]:
    cid = (corredor_id or "").upper()
    if cid != "TOTAL":
        cid = _validar_corredor(cid)
    filas = [r for r in cargar("viajeros_trimestral") if r["corredor_id"] == cid]
    return sorted(filas, key=lambda r: _orden(r["periodo"]))


def serie_precios(corredor_id: str, metrica: str | None = None) -> list[dict[str, Any]]:
    cid = _validar_corredor(corredor_id)
    filas = [r for r in cargar("precios") if r["corredor_id"] == cid]
    if metrica:
        filas = [r for r in filas if r["metrica"] == metrica]
    return filas


def cuotas_mercado(corredor_id: str | None = None, periodo: str | None = None) -> list[dict[str, Any]]:
    filas = list(cargar("cuotas"))
    if corredor_id:
        cid = _validar_corredor(corredor_id)
        filas = [r for r in filas if r["corredor_id"] == cid]
    if periodo:
        filas = [r for r in filas if r["periodo"] == periodo]
    return sorted(filas, key=lambda r: (_orden(r["periodo"]), r["corredor_id"], r["operador"]))


def eventos(corredor_id: str | None = None) -> list[dict[str, Any]]:
    filas = list(cargar("eventos"))
    if corredor_id:
        cid = _validar_corredor(corredor_id)
        filas = [r for r in filas if cid in r["corredor_id"].split(";") or r["corredor_id"] == "TOTAL"]
    return filas


def datos_competidores(empresa: str | None = None) -> list[dict[str, Any]]:
    filas = list(cargar("empresas"))
    if empresa:
        filas = [r for r in filas if r["empresa"].lower() == empresa.lower()]
    return filas


def demanda_mensual() -> list[dict[str, Any]]:
    return list(cargar("demanda_mensual_ine"))


# --------------------------------------------------------------------- analítica
def _ultimo_yoy(cid: str) -> dict[str, Any] | None:
    con_var = [r for r in serie_viajeros(cid) if r["var_interanual_pct"] is not None]
    return con_var[-1] if con_var else None


def _anual(cid: str) -> dict[str, Any] | None:
    return next((r for r in cargar("viajeros_anual") if r["corredor_id"] == cid), None)


def _precio_anual(cid: str) -> dict[str, Any] | None:
    return next(
        (r for r in cargar("precios") if r["corredor_id"] == cid and r["periodo"] == "2025"), None
    )


def _cuota_renfe(cid: str) -> list[dict[str, Any]]:
    return [r for r in cuotas_mercado(cid) if r["operador"] == "Renfe"]


def comparar_corredores() -> list[dict[str, Any]]:
    """Tabla comparativa 2025 + señal más reciente de 2026 para los 5 corredores."""
    out = []
    corr = {c["corredor_id"]: c for c in cargar("corredores")}
    for cid in CORREDORES_VALIDOS:
        anual = _anual(cid) or {}
        precio = _precio_anual(cid) or {}
        cuota = _cuota_renfe(cid)
        ult = _ultimo_yoy(cid)
        viaj = anual.get("viajeros_millones")
        p = precio.get("precio_eur")
        mercado = round(viaj * p, 1) if viaj and p else None
        cuota_ult = cuota[-1]["cuota_pct"] if cuota else None
        out.append({
            "corredor_id": cid,
            "nombre": corr[cid]["nombre"],
            "viajeros_2025_M": viaj,
            "var_viajeros_2025_pct": anual.get("var_interanual_pct"),
            "ingreso_medio_2025_eur": p,
            "var_precio_2025_pct": precio.get("var_interanual_pct"),
            "mercado_estimado_2025_MEUR": mercado,
            "cuota_renfe_ultima_pct": cuota_ult,
            "periodo_cuota": cuota[-1]["periodo"] if cuota else None,
            "ingreso_renfe_estimado_2025_MEUR": round(mercado * cuota_ult / 100, 1) if mercado and cuota_ult else None,
            "ultima_var_interanual_pct": ult["var_interanual_pct"] if ult else None,
            "periodo_ultima_var": ult["periodo"] if ult else None,
            "peso_canones_en_coste_pct": corr[cid]["peso_canones_en_coste_pct"],
            "resultado_billetes_vs_coste": corr[cid]["resultado_billetes_vs_coste_2025"],
        })
    return out


def elasticidad_precio(corredor_id: str | None = None) -> dict[str, Any]:
    """
    Elasticidad aparente = %Δ viajeros / %Δ precio, emparejando por corredor y periodo.
    No es una elasticidad causal: la oferta de plazas, la entrada de competidores y los
    incidentes también mueven la demanda. Las observaciones con signo positivo se marcan
    como 'no interpretable' (desplazamiento de la curva de demanda, no movimiento sobre ella).
    """
    viaj_t = {(r["periodo"], r["corredor_id"]): r for r in cargar("viajeros_trimestral")}
    viaj_a = {("2025", r["corredor_id"]): r for r in cargar("viajeros_anual")}
    obs = []
    for pr in cargar("precios"):
        if pr["var_interanual_pct"] in (None, 0.0):
            continue
        key = (pr["periodo"], pr["corredor_id"])
        vr = viaj_t.get(key) or viaj_a.get(key)
        if not vr or vr["var_interanual_pct"] is None:
            continue
        e = round(vr["var_interanual_pct"] / pr["var_interanual_pct"], 2)
        obs.append({
            "periodo": pr["periodo"],
            "corredor_id": pr["corredor_id"],
            "var_precio_pct": pr["var_interanual_pct"],
            "metrica_precio": pr["metrica"],
            "var_viajeros_pct": vr["var_interanual_pct"],
            "elasticidad_aparente": e,
            "interpretable": e < 0,
            "fuentes": sorted({pr["fuente_id"], vr["fuente_id"]}),
        })
    if corredor_id:
        cid = _validar_corredor(corredor_id)
        obs = [o for o in obs if o["corredor_id"] == cid]
    validas = [o["elasticidad_aparente"] for o in obs if o["interpretable"]]
    resumen = None
    if validas:
        med = statistics.median(validas)
        resumen = {
            "n_validas": len(validas),
            "mediana": round(med, 2),
            "min": min(validas),
            "max": max(validas),
            "clase": _clase_elasticidad(med),
        }
    return {"observaciones": obs, "resumen": resumen,
            "advertencia": "Elasticidad aparente (ratio de variaciones interanuales), no causal."}


def _clase_elasticidad(e: float) -> str:
    a = abs(e)
    if a < 0.5:
        return "inelastica"
    if a <= 1.0:
        return "moderada"
    return "elastica"


def simular_escenario_precio(corredor_id: str, cambio_precio_pct: float,
                             elasticidad: float | None = None) -> dict[str, Any]:
    """
    Simula el efecto de un cambio de precio sobre viajeros e ingresos del corredor
    (modelo de elasticidad constante: Q1 = Q0 * (1+Δp)^e), sobre la base anual 2025.
    Si no se da elasticidad se usa la mediana del corredor y, como banda, su min/max;
    si el corredor no tiene observaciones válidas, se usan las de todos los corredores.
    """
    cid = _validar_corredor(corredor_id)
    if not -50 <= cambio_precio_pct <= 50:
        raise DatoNoDisponible("cambio_precio_pct debe estar entre -50 y 50")
    anual, precio = _anual(cid), _precio_anual(cid)
    if not anual or not precio or precio["precio_eur"] is None:
        raise DatoNoDisponible(f"Sin base anual 2025 para {cid}")
    q0, p0 = anual["viajeros_millones"], precio["precio_eur"]

    origen = "usuario"
    if elasticidad is None:
        res = elasticidad_precio(cid)["resumen"]
        origen = f"mediana corredor {cid}"
        if res is None:
            res = elasticidad_precio()["resumen"]
            origen = "mediana todos los corredores"
        escenarios = {"central": res["mediana"], "_a": res["max"], "_b": res["min"]}
    else:
        escenarios = {"central": elasticidad}

    dp = cambio_precio_pct / 100
    ocup = next((o["ocupacion_pct"] for o in cargar("ocupacion") if o["corredor_id"] == cid), None)
    resultados = {}
    for nombre, e in escenarios.items():
        fq = (1 + dp) ** e
        q1, p1 = q0 * fq, p0 * (1 + dp)
        r0, r1 = q0 * p0, q1 * p1
        fila = {
            "elasticidad": e,
            "viajeros_M": round(q1, 2),
            "var_viajeros_pct": round((fq - 1) * 100, 1),
            "ingresos_mercado_MEUR": round(r1, 1),
            "var_ingresos_pct": round((r1 / r0 - 1) * 100, 1),
        }
        if ocup is not None:
            o1 = ocup * fq
            fila["ocupacion_estimada_pct"] = round(o1, 1)
            fila["riesgo_capacidad"] = o1 > 90
        resultados[nombre] = fila
    if "_a" in resultados:  # etiqueta por resultado en ingresos, no por signo de la elasticidad
        a, b = resultados.pop("_a"), resultados.pop("_b")
        hi, lo = (a, b) if a["var_ingresos_pct"] >= b["var_ingresos_pct"] else (b, a)
        resultados["optimista"], resultados["pesimista"] = hi, lo
    return {
        "corredor_id": cid,
        "base_2025": {"viajeros_M": q0, "ingreso_medio_eur": p0,
                      "ingresos_mercado_MEUR": round(q0 * p0, 1), "ocupacion_ref_pct": ocup},
        "cambio_precio_pct": cambio_precio_pct,
        "origen_elasticidad": origen,
        "escenarios": resultados,
        "supuestos": [
            "Oferta de plazas constante y sin reacción de precios de la competencia.",
            "Base: viajeros e ingreso medio 2025 del corredor (todos los operadores), CNMC.",
            "Ocupación de referencia: 1T 2025 (única publicada por corredor).",
        ],
    }


def recomendar_accion(corredor_id: str) -> dict[str, Any]:
    """Reglas de decisión transparentes (ver .claude/skills/informe-decision/SKILL.md)."""
    cid = _validar_corredor(corredor_id)
    comp = next(c for c in comparar_corredores() if c["corredor_id"] == cid)
    el = elasticidad_precio(cid)["resumen"]
    clase = el["clase"] if el else "desconocida"
    cuota = _cuota_renfe(cid)
    tendencia_cuota = None
    if len(cuota) >= 2:
        tendencia_cuota = round(cuota[-1]["cuota_pct"] - cuota[0]["cuota_pct"], 1)
    ult = _ultimo_yoy(cid)
    yoy = ult["var_interanual_pct"] if ult else None
    shocks = [e for e in eventos(cid) if e["tipo"] in ("incidente", "operacion") and e["fecha"].startswith("2026")
              and e["corredor_id"] != "TOTAL"]
    rentable = "superan" in (comp["resultado_billetes_vs_coste"] or "")
    ocup = next((o["ocupacion_pct"] for o in cargar("ocupacion") if o["corredor_id"] == cid), None)

    senales = {
        "ultima_var_viajeros_pct": yoy, "periodo": ult["periodo"] if ult else None,
        "clase_elasticidad": clase, "tendencia_cuota_renfe_pp": tendencia_cuota,
        "corredor_rentable": rentable, "ocupacion_ref_pct": ocup,
        "shocks_2026": [e["evento"] for e in shocks],
    }

    shock_grave = any(e["tipo"] == "incidente" for e in shocks) or (bool(shocks) and (yoy or 0) <= -20)
    if shock_grave and yoy is not None and yoy <= -10:
        accion = "RECUPERAR DEMANDA"
        detalle = ("Shock de oferta/confianza activo. No subir precios; priorizar fiabilidad "
                   "(información en tiempo real, compensaciones), Avlo y tarifas flexibles para "
                   "recuperar a quien se fue al autobús o al avión. Seguimiento mensual con INE.")
    elif clase == "inelastica" and rentable and (tendencia_cuota or 0) < 0:
        accion = "PREMIUM CON DEFENSA SELECTIVA"
        detalle = ("Demanda poco sensible al precio y corredor rentable: mantener el ingreso medio "
                   "del AVE, pero frenar la pérdida de cuota con Avlo en franjas valle y en los "
                   "trenes donde compiten Iryo/Ouigo. Vigilar cuota trimestral CNMC.")
    elif clase == "elastica" and (ocup is None or ocup < 75):
        accion = "ESTIMULAR VOLUMEN"
        detalle = ("Demanda sensible al precio y ocupación con margen: bajadas tácticas en valle "
                   "pueden aumentar ingresos totales. Validar en piloto A/B antes de generalizar.")
    else:
        accion = "MANTENER Y VIGILAR"
        detalle = "Señales mixtas o insuficientes: mantener política y reforzar la recogida de datos."

    n_obs = el["n_validas"] if el else 0
    derivados = sum(1 for r in serie_viajeros(cid) if r["tipo_dato"] == "derivado")
    confianza = "alta" if n_obs >= 3 and derivados <= 1 else "media" if n_obs >= 1 else "baja"
    return {"corredor_id": cid, "nombre": comp["nombre"], "accion": accion, "detalle": detalle,
            "confianza": confianza, "senales": senales}


def kpis_corredor(corredor_id: str) -> dict[str, Any]:
    """Ficha completa de un corredor: todo lo que un analista necesita en una llamada."""
    cid = _validar_corredor(corredor_id)
    comp = next(c for c in comparar_corredores() if c["corredor_id"] == cid)
    return {
        "resumen": comp,
        "viajeros_trimestral": serie_viajeros(cid),
        "precios": serie_precios(cid),
        "cuotas": cuotas_mercado(cid),
        "ocupacion": [o for o in cargar("ocupacion") if o["corredor_id"] == cid],
        "eventos": eventos(cid),
    }
