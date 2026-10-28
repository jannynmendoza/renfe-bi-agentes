"""
Prueba TODAS las conexiones del sistema:
  1. Arranca el servidor MCP renfe-bi por stdio (igual que lo hará Claude Code / VS Code).
  2. Hace el handshake MCP, lista herramientas y prompts.
  3. Llama a cada una de las 14 herramientas con argumentos reales y valida la respuesta.
  4. (--live) Comprueba la API del INE directamente y a través del MCP.
  5. Verifica que las skills, subagentes y el comando existen y tienen frontmatter válido.

Uso:  python scripts/test_connections.py [--live] [--json salida.json]
Código de salida 0 si todo lo obligatorio pasa.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

# herramienta -> (argumentos, validador)
CASOS = {
    "estado_conexiones": ({}, lambda r: r["datos_locales"]["ok"] is True),
    "listar_corredores": ({}, lambda r: r["n"] == 5),
    "comparar_corredores": ({}, lambda r: r["n"] == 5 and r["filas"][0]["mercado_estimado_2025_MEUR"] > 0),
    "kpis_corredor": ({"corredor_id": "BCN"}, lambda r: r["resumen"]["corredor_id"] == "BCN"),
    "serie_viajeros": ({"corredor_id": "TOTAL"}, lambda r: r["n"] == 6),
    "serie_precios": ({"corredor_id": "SEV", "metrica": "ingreso_medio_trayecto_sin_iva"}, lambda r: r["n"] == 2),
    "cuotas_mercado": ({"corredor_id": "BCN", "periodo": "2025T4"}, lambda r: 95 <= sum(f["cuota_pct"] for f in r["filas"]) <= 100),
    "elasticidad_precio": ({"corredor_id": "BCN"}, lambda r: r["resumen"]["clase"] == "inelastica"),
    "simular_escenario_precio": ({"corredor_id": "BCN", "cambio_precio_pct": 5}, lambda r: "central" in r["escenarios"]),
    "recomendar_accion": ({"corredor_id": "SEV"}, lambda r: r["accion"] == "RECUPERAR DEMANDA"),
    "eventos": ({"corredor_id": "MAL"}, lambda r: r["n"] >= 2),
    "datos_competidores": ({"empresa": "Iryo"}, lambda r: r["n"] >= 2),
    "demanda_mensual": ({}, lambda r: r["modo"] == "snapshot" and r["n"] >= 1),
    "fuentes": ({"fuente_ids": ["CNMC_4T25"]}, lambda r: r["n"] == 1 and r["filas"][0]["url"].startswith("https://")),
}


def _payload(res) -> dict:
    if getattr(res, "isError", False) or getattr(res, "is_error", False):
        raise RuntimeError(res.content[0].text if res.content else "error")
    sc = getattr(res, "structuredContent", None) or getattr(res, "structured_content", None)
    if isinstance(sc, dict):
        return sc.get("result", sc) if set(sc) == {"result"} else sc
    return json.loads(res.content[0].text)


def _check_frontmatter(path: Path, claves: tuple[str, ...]) -> bool:
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", txt, re.S)
    return bool(m) and all(re.search(rf"^{k}:\s*\S", m.group(1), re.M) for k in claves)


async def probar_mcp(live: bool) -> list[dict]:
    resultados = []
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"],
                                   cwd=str(ROOT), env={"PYTHONPATH": str(ROOT), **_env_base()})
    t0 = time.perf_counter()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            init = await session.initialize()
            nombre = getattr(getattr(init, "serverInfo", None) or getattr(init, "server_info", None), "name", "?")
            resultados.append({"prueba": "handshake MCP (stdio)", "ok": nombre == "renfe-bi",
                               "detalle": f"servidor={nombre} en {time.perf_counter()-t0:.2f}s"})
            tools = {t.name for t in (await session.list_tools()).tools}
            faltan = set(CASOS) - tools
            resultados.append({"prueba": "list_tools", "ok": not faltan,
                               "detalle": f"{len(tools)} herramientas" + (f"; faltan {faltan}" if faltan else "")})
            prompts = [p.name for p in (await session.list_prompts()).prompts]
            resultados.append({"prueba": "list_prompts", "ok": "brief_semanal" in prompts, "detalle": ", ".join(prompts)})

            for nombre_t, (args, validar) in CASOS.items():
                t = time.perf_counter()
                try:
                    r = _payload(await session.call_tool(nombre_t, args))
                    ok = bool(validar(r))
                    det = f"{(time.perf_counter()-t)*1000:.0f} ms"
                except Exception as e:  # noqa: BLE001
                    ok, det = False, f"{type(e).__name__}: {e}"
                resultados.append({"prueba": f"tool {nombre_t}", "ok": ok, "detalle": det})

            datos = _payload(await session.call_tool("estado_conexiones", {}))["datos_locales"]
            destino = datos.get("host") or datos.get("data_dir")
            resultados.append({"prueba": f"origen de datos ({datos['origen']})", "ok": datos["ok"],
                               "detalle": f"{destino}; {sum(t.get('filas', 0) for t in datos['tablas'].values())} filas"})

            # error controlado: corredor inexistente debe devolver error, no tumbar el servidor
            r = await session.call_tool("kpis_corredor", {"corredor_id": "XXX"})
            err = getattr(r, "isError", getattr(r, "is_error", False))
            resultados.append({"prueba": "manejo de errores (corredor XXX)", "ok": bool(err),
                               "detalle": "devuelve isError=true" if err else "no devolvió error"})

            if live:
                r = _payload(await session.call_tool("estado_conexiones", {"comprobar_ine": True}))
                resultados.append({"prueba": "API INE vía MCP (ping)", "ok": r["api_ine"]["ok"],
                                   "detalle": json.dumps(r["api_ine"], ensure_ascii=False)[:160], "opcional": True})
                r = _payload(await session.call_tool("demanda_mensual", {"en_vivo": True}))
                ok = r["modo"] == "en_vivo" and r.get("n_series", 0) > 0
                det = f"{r.get('n_series')} series INE" if ok else r.get("error_en_vivo", r["modo"])
                resultados.append({"prueba": "demanda_mensual en vivo (INE 49359)", "ok": ok,
                                   "detalle": str(det)[:160], "opcional": True})
    return resultados


def _env_base() -> dict:
    import os
    keep = ("PATH", "HOME", "SYSTEMROOT", "HTTPS_PROXY", "HTTP_PROXY", "NO_PROXY",
            "SSL_CERT_FILE", "REQUESTS_CA_BUNDLE", "USERPROFILE", "APPDATA",
            "SUPABASE_DB_URL", "RENFE_BI_ORIGEN")
    return {k: os.environ[k] for k in keep if k in os.environ}


def probar_artefactos() -> list[dict]:
    res = []
    for s in ("analisis-corredor", "escenarios-precio", "informe-decision", "verificacion-datos"):
        p = ROOT / ".claude/skills" / s / "SKILL.md"
        res.append({"prueba": f"skill {s}", "ok": p.exists() and _check_frontmatter(p, ("name", "description")),
                    "detalle": str(p.relative_to(ROOT))})
    for a in ("analista-mercado", "estratega-pricing", "auditor-datos"):
        p = ROOT / ".claude/agents" / f"{a}.md"
        res.append({"prueba": f"subagente {a}", "ok": p.exists() and _check_frontmatter(p, ("name", "description", "tools")),
                    "detalle": str(p.relative_to(ROOT))})
    p = ROOT / ".claude/commands/decision-semanal.md"
    res.append({"prueba": "comando /decision-semanal", "ok": p.exists() and _check_frontmatter(p, ("description",)),
                "detalle": str(p.relative_to(ROOT))})
    cfg = json.loads((ROOT / ".mcp.json").read_text())
    res.append({"prueba": ".mcp.json registra renfe-bi", "ok": "renfe-bi" in cfg.get("mcpServers", {}), "detalle": ".mcp.json"})
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="probar también la API del INE en vivo")
    ap.add_argument("--json", help="guardar resultados en este archivo JSON")
    a = ap.parse_args()

    resultados = probar_artefactos() + asyncio.run(probar_mcp(a.live))
    ancho = max(len(r["prueba"]) for r in resultados)
    for r in resultados:
        estado = "OK  " if r["ok"] else ("AVISO" if r.get("opcional") else "FALLO")
        print(f"[{estado}] {r['prueba']:<{ancho}}  {r['detalle']}")
    obligatorios = [r for r in resultados if not r.get("opcional")]
    n_ok = sum(r["ok"] for r in obligatorios)
    print(f"\n{n_ok}/{len(obligatorios)} pruebas obligatorias OK"
          + ("" if not a.live else f"; en vivo: {sum(r['ok'] for r in resultados if r.get('opcional'))}/2"))
    if a.json:
        Path(a.json).write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if n_ok == len(obligatorios) else 1


if __name__ == "__main__":
    sys.exit(main())
