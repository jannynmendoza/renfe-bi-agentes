"""
Servidor MCP «renfe-bi»: expone el Radar Competitivo de Alta Velocidad como herramientas
que cualquier agente compatible con MCP (Claude Code en VS Code, Claude Desktop, el
orquestador de agents/run_agentes.py…) puede llamar.

Arranque manual:   python -m mcp_server.server        (transporte stdio)
Registro en VS Code / Claude Code: ver .mcp.json en la raíz del proyecto.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Permite ejecutar tanto `python -m mcp_server.server` como `python mcp_server/server.py`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import functools

try:  # SDK MCP para Python >= 2.0
    from mcp.server.mcpserver import MCPServer as _Server
    from mcp.server.mcpserver.exceptions import ToolError
except ImportError:  # SDK MCP 1.x
    from mcp.server.fastmcp import FastMCP as _Server
    from mcp.server.fastmcp.exceptions import ToolError

from mcp_server import bi_core as core
from mcp_server import ine_client

INSTRUCCIONES = (
    "Radar competitivo de la alta velocidad española para Renfe Viajeros. Datos reales "
    "públicos (CNMC, INE, prensa económica) 2025-2026 para los corredores BCN, VLC, ALI, SEV, MAL. "
    "Cita siempre el fuente_id de cada cifra y distingue datos publicados de derivados."
)

mcp = _Server("renfe-bi", instructions=INSTRUCCIONES)


def _tool(fn):
    """Registra la función como herramienta MCP y convierte errores de datos en ToolError legibles."""
    @functools.wraps(fn)
    def envoltura(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except core.DatoNoDisponible as e:
            raise ToolError(str(e)) from e
    return mcp.tool()(envoltura)


def _filas(x: list[dict[str, Any]]) -> dict[str, Any]:
    return {"n": len(x), "filas": x}


@_tool
def estado_conexiones(comprobar_ine: bool = False) -> dict[str, Any]:
    """Health-check: verifica que los 10 datasets cargan y, opcionalmente, que la API del INE responde."""
    out = {"datos_locales": core.estado_datos()}
    if comprobar_ine:
        out["api_ine"] = ine_client.ping()
    return out


@_tool
def listar_corredores() -> dict[str, Any]:
    """Lista los 5 corredores de alta velocidad con operadores, peso de los cánones en el coste y rentabilidad 2025."""
    return _filas(core.listar_corredores())


@_tool
def comparar_corredores() -> dict[str, Any]:
    """Tabla comparativa: viajeros e ingreso medio 2025, mercado estimado (M€), cuota Renfe, última variación interanual 2026."""
    return _filas(core.comparar_corredores())


@_tool
def kpis_corredor(corredor_id: str) -> dict[str, Any]:
    """Ficha completa de un corredor (BCN, VLC, ALI, SEV, MAL): viajeros, precios, cuotas, ocupación y eventos."""
    return core.kpis_corredor(corredor_id)


@_tool
def serie_viajeros(corredor_id: str) -> dict[str, Any]:
    """Serie trimestral 2025T1–2026T2 de viajeros (millones) y variación interanual. Acepta TOTAL."""
    return _filas(core.serie_viajeros(corredor_id))


@_tool
def serie_precios(corredor_id: str, metrica: str | None = None) -> dict[str, Any]:
    """Precios por corredor. metrica opcional: precio_web_trayecto, ingreso_medio_trayecto, ingreso_medio_trayecto_sin_iva, ingreso_viajero_km."""
    return _filas(core.serie_precios(corredor_id, metrica))


@_tool
def cuotas_mercado(corredor_id: str | None = None, periodo: str | None = None) -> dict[str, Any]:
    """Cuotas de mercado por operador (Renfe, Iryo, Ouigo), filtrables por corredor y periodo (p.ej. 2025T4)."""
    return _filas(core.cuotas_mercado(corredor_id, periodo))


@_tool
def elasticidad_precio(corredor_id: str | None = None) -> dict[str, Any]:
    """Elasticidad aparente precio-demanda (%Δviajeros/%Δprecio) por corredor y periodo, con resumen y clase."""
    return core.elasticidad_precio(corredor_id)


@_tool
def simular_escenario_precio(corredor_id: str, cambio_precio_pct: float,
                             elasticidad: float | None = None) -> dict[str, Any]:
    """Simula un cambio de precio (-50..50 %) sobre viajeros, ingresos y ocupación del corredor, con escenarios central/optimista/pesimista."""
    return core.simular_escenario_precio(corredor_id, cambio_precio_pct, elasticidad)


@_tool
def recomendar_accion(corredor_id: str) -> dict[str, Any]:
    """Recomendación de decisión por reglas transparentes (RECUPERAR DEMANDA, PREMIUM CON DEFENSA SELECTIVA, ESTIMULAR VOLUMEN, MANTENER Y VIGILAR)."""
    return core.recomendar_accion(corredor_id)


@_tool
def eventos(corredor_id: str | None = None) -> dict[str, Any]:
    """Eventos que explican la demanda: entrada de competidores, Adamuz, cortes de vía, cambios regulatorios."""
    return _filas(core.eventos(corredor_id))


@_tool
def datos_competidores(empresa: str | None = None) -> dict[str, Any]:
    """Indicadores financieros y operativos de Renfe, Iryo, Ouigo y del sector (2024-2026)."""
    return _filas(core.datos_competidores(empresa))


@_tool
def demanda_mensual(en_vivo: bool = False, filtro: str | None = None) -> dict[str, Any]:
    """Demanda mensual. en_vivo=False: snapshot INE 2026 guardado. en_vivo=True: consulta la API del INE (tabla 49359) en tiempo real."""
    if not en_vivo:
        return {"modo": "snapshot", **_filas(core.demanda_mensual())}
    try:
        return {"modo": "en_vivo", **ine_client.demanda_en_vivo(filtro=filtro or ine_client.FILTRO_DEFECTO)}
    except ine_client.INEError as e:
        return {"modo": "snapshot (fallback)", "error_en_vivo": str(e), **_filas(core.demanda_mensual())}


@_tool
def fuentes(fuente_ids: list[str] | None = None) -> dict[str, Any]:
    """Resuelve fuente_id -> título, organismo, fecha y URL. Sin argumentos devuelve todas."""
    return _filas(core.fuentes(fuente_ids))


@mcp.prompt()
def brief_semanal(corredor_id: str = "BCN") -> str:
    """Plantilla de prompt para pedir el brief de decisión de un corredor."""
    return (f"Prepara el brief de decisión del corredor {corredor_id} siguiendo la skill "
            "informe-decision: usa kpis_corredor, elasticidad_precio, simular_escenario_precio "
            "(+5 % y -5 %) y recomendar_accion; cita fuentes con la herramienta fuentes.")


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
