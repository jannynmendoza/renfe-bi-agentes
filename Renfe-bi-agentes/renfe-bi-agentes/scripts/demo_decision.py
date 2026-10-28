"""
Demo end-to-end SIN clave de API: el mismo flujo de agentes que /decision-semanal,
pero con agentes deterministas que solo hablan con el servidor MCP (por stdio).

  Analista de mercado  ->  Estratega de pricing  ->  Auditor de datos  ->  Briefs

Genera en reports/:
  brief_<CORREDOR>_<fecha>.md      (uno por corredor)
  resumen_ejecutivo_<fecha>.md     (tabla de decisiones)
  dashboard_<fecha>.html           (cuadro de mando autocontenido)
  traza_mcp_<fecha>.json           (todas las llamadas MCP: evidencia de las conexiones)

Uso: python scripts/demo_decision.py [--corredores BCN SEV ...] [--fecha AAAA-MM-DD]
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

REPORTS = ROOT / "reports"
CORREDORES = ["BCN", "VLC", "ALI", "SEV", "MAL"]


class ClienteMCP:
    """Envuelve la sesión MCP y registra cada llamada (traza auditable)."""

    def __init__(self, session: ClientSession):
        self.s, self.traza = session, []

    async def __call__(self, tool: str, **args):
        res = await self.s.call_tool(tool, args)
        if getattr(res, "isError", False):
            raise RuntimeError(f"{tool}: {res.content[0].text}")
        sc = getattr(res, "structuredContent", None)
        data = sc if isinstance(sc, dict) else json.loads(res.content[0].text)
        if isinstance(data, dict) and set(data) == {"result"}:
            data = data["result"]
        self.traza.append({"tool": tool, "args": args, "ts": dt.datetime.now().isoformat(timespec="seconds")})
        return data


# ------------------------------------------------------------------ agentes
class AnalistaMercado:
    def __init__(self, mcp: ClienteMCP):
        self.mcp = mcp

    async def diagnosticar(self, cid: str) -> dict:
        k = await self.mcp("kpis_corredor", corredor_id=cid)
        r = k["resumen"]
        hechos, fuentes = [], set()
        hechos.append(f"Mercado 2025: **{r['viajeros_2025_M']} M viajeros** × {r['ingreso_medio_2025_eur']:.2f} € "
                      f"= **{r['mercado_estimado_2025_MEUR']} M€** (todos los operadores) *(derivado)* [CNMC_ANUAL25]")
        fuentes.add("CNMC_ANUAL25")
        if r["var_precio_2025_pct"] is not None:
            hechos.append(f"Ingreso medio 2025 {r['var_precio_2025_pct']:+.1f} % y viajeros "
                          f"{r['var_viajeros_2025_pct']:+.1f} % interanual [CNMC_ANUAL25]")
        cuotas = [c for c in k["cuotas"] if c["operador"] == "Renfe"]
        if cuotas:
            c0, c1 = cuotas[0], cuotas[-1]
            txt = f"Cuota Renfe {c1['cuota_pct']:.0f} % en {c1['periodo']}"
            if c0 is not c1:
                txt += f" (desde {c0['cuota_pct']:.0f} % en {c0['periodo']})"
            if c1.get("nota"):
                txt += f" — {c1['nota']}"
            hechos.append(f"{txt} [{c1['fuente_id']}]")
            fuentes.update({c0["fuente_id"], c1["fuente_id"]})
        ult = [v for v in k["viajeros_trimestral"] if v["var_interanual_pct"] is not None][-1]
        nivel = f" (≈{ult['viajeros_millones']} M *(derivado)*)" if ult["tipo_dato"] == "derivado" and ult["viajeros_millones"] else ""
        hechos.append(f"Último dato: viajeros **{ult['var_interanual_pct']:+.0f} %** interanual en {ult['periodo']}"
                      f"{nivel} [{ult['fuente_id']}]")
        fuentes.add(ult["fuente_id"])
        ev = [e for e in k["eventos"] if e["corredor_id"] != "TOTAL"]
        causas = [f"{e['fecha']}: {e['evento']} [{e['fuente_id']}]" for e in ev]
        fuentes.update(e["fuente_id"] for e in ev)
        return {"corredor": cid, "nombre": r["nombre"], "resumen": r, "hechos": hechos,
                "causas": causas, "fuentes": fuentes, "serie": k["viajeros_trimestral"]}


class EstrategaPricing:
    def __init__(self, mcp: ClienteMCP):
        self.mcp = mcp

    async def proponer(self, diag: dict) -> dict:
        cid = diag["corredor"]
        el = await self.mcp("elasticidad_precio", corredor_id=cid)
        sub = await self.mcp("simular_escenario_precio", corredor_id=cid, cambio_precio_pct=5)
        baj = await self.mcp("simular_escenario_precio", corredor_id=cid, cambio_precio_pct=-5)
        rec = await self.mcp("recomendar_accion", corredor_id=cid)
        fuentes = {f for o in el["observaciones"] for f in o["fuentes"]}
        return {"elasticidad": el, "subida": sub, "bajada": baj, "rec": rec, "fuentes": fuentes}


class AuditorDatos:
    def __init__(self, mcp: ClienteMCP):
        self.mcp = mcp

    async def auditar(self, diag: dict, estr: dict) -> dict:
        ids = sorted(diag["fuentes"] | estr["fuentes"])
        f = await self.mcp("fuentes", fuente_ids=ids)
        encontrados = {x["fuente_id"] for x in f["filas"]}
        faltan = set(ids) - encontrados
        derivados = sum(1 for v in diag["serie"] if v["tipo_dato"] == "derivado")
        veredicto = "APTO" if not faltan else "NO APTO"
        if veredicto == "APTO" and (derivados or estr["rec"]["confianza"] == "baja"):
            veredicto = "APTO CON CAMBIOS"
        return {"veredicto": veredicto, "fuentes": f["filas"], "faltan": sorted(faltan),
                "notas": ([f"{derivados} dato(s) trimestral(es) derivados: indicados en el texto."] if derivados else [])
                + ["Elasticidad aparente, no causal; no modela la reacción de Iryo/Ouigo."]}


# ------------------------------------------------------------------ redacción
def _tabla_escenarios(sub: dict, baj: dict) -> str:
    filas = ["| Escenario | Elasticidad | Viajeros | Ingresos corredor | Banda ingresos |", "|---|---|---|---|---|"]
    for etiqueta, s in (("Precio +5 %", sub), ("Precio −5 %", baj)):
        e = s["escenarios"]
        banda = (f"{e['pesimista']['var_ingresos_pct']:+.1f} % a {e['optimista']['var_ingresos_pct']:+.1f} %"
                 if "optimista" in e else "—")
        c = e["central"]
        filas.append(f"| {etiqueta} | {c['elasticidad']} | {c['var_viajeros_pct']:+.1f} % | "
                     f"{c['var_ingresos_pct']:+.1f} % ({c['ingresos_mercado_MEUR']} M€) | {banda} |")
    return "\n".join(filas)


PASOS = {
    "RECUPERAR DEMANDA": [
        "Congelar subidas de tarifa hasta recuperar el nivel de viajeros de 2025 — Revenue Management — KPI: viajeros mensuales INE.",
        "Campaña de confianza: información en tiempo real y compromiso de puntualidad — Marketing/Operaciones — KPI: % trenes < 15 min.",
        "Reforzar Avlo y billetes flexibles para recuperar viajeros desviados a autobús y avión — Producto — KPI: cuota Renfe trimestral CNMC.",
    ],
    "PREMIUM CON DEFENSA SELECTIVA": [
        "Mantener el ingreso medio del AVE en horas punta — Revenue Management — KPI: ingreso medio por trayecto.",
        "Desplegar Avlo en franjas valle y trenes en competencia directa con Iryo/Ouigo — Planificación — KPI: cuota Renfe (objetivo ≥ 58 %).",
        "Piloto de precio dinámico frente a la competencia (datos de QL2/Appia) — RM + Data — KPI: ingreso por plaza ofertada.",
    ],
    "ESTIMULAR VOLUMEN": [
        "Piloto A/B de −5 % en valle durante 8 semanas — Revenue Management — KPI: ingresos por tren.",
        "Vigilar ocupación para no canibalizar punta — Planificación — KPI: ocupación por franja.",
        "Revisar con cánones (coste) el umbral de precio mínimo — Finanzas — KPI: margen por viajero.",
    ],
    "MANTENER Y VIGILAR": [
        "Mantener política de precios — Revenue Management — KPI: ingreso medio por trayecto.",
        "Completar datos de ocupación propios para afinar elasticidad — Data — KPI: cobertura de datos.",
        "Revisión trimestral con el informe CNMC — Dirección Comercial — KPI: cuota Renfe.",
    ],
}


def redactar_brief(diag: dict, estr: dict, aud: dict, fecha: str) -> str:
    rec, el = estr["rec"], estr["elasticidad"]["resumen"]
    s = rec["senales"]
    lineas = [
        f"# Brief de decisión — {diag['nombre']} — {fecha}",
        "",
        f"**Recomendación:** {rec['accion']} (confianza {rec['confianza']})  ",
        f"**Auditoría de datos:** {aud['veredicto']}",
        "",
        f"> {rec['detalle']}",
        "",
        "## Qué está pasando",
        *[f"- {h}" for h in diag["hechos"]],
        "",
        "## Por qué (mercado vs oferta)",
        *([f"- {c}" for c in diag["causas"]] or ["- Sin eventos de oferta registrados: la evolución responde a precio y competencia."]),
        f"- Elasticidad aparente: mediana **{el['mediana']}** ({el['clase']}, {el['n_validas']} observaciones; rango {el['min']} a {el['max']})."
        if el else "- Sin observaciones suficientes para estimar elasticidad.",
        "",
        "## Escenarios de precio (base 2025, mercado total del corredor)",
        _tabla_escenarios(estr["subida"], estr["bajada"]),
        "",
        "## Riesgos y lo que no sabemos",
        *[f"- {n}" for n in aud["notas"]],
        f"- Ocupación de referencia solo disponible para 1T 2025 ({s['ocupacion_ref_pct']} %).",
        "",
        "## Próximos pasos",
        *[f"{i}. {p}" for i, p in enumerate(PASOS[rec["accion"]], 1)],
        "",
        "## Fuentes",
        *[f"- `{f['fuente_id']}` — [{f['titulo']}]({f['url']}) ({f['organismo']}, {f['fecha_publicacion']})" for f in aud["fuentes"]],
        "",
    ]
    return "\n".join(lineas)


def dashboard_html(resultados: list[dict], comp: list[dict], total: list[dict], fecha: str, estado: dict) -> str:
    esc = html.escape
    maxm = max(c["mercado_estimado_2025_MEUR"] for c in comp)
    barras = "".join(
        f'<div class="row"><span class="lbl">{esc(c["nombre"])}</span><span class="bar" style="width:{c["mercado_estimado_2025_MEUR"]/maxm*100:.0f}%"></span>'
        f'<span class="val">{c["mercado_estimado_2025_MEUR"]:.0f} M€ · Renfe {c["cuota_renfe_ultima_pct"]:.0f} %</span></div>'
        for c in comp)
    pts = [t for t in total if t["viajeros_millones"]]
    w, h, pad = 560, 180, 30
    vmax = max(p["viajeros_millones"] for p in pts) * 1.1
    xs = [pad + i * (w - 2 * pad) / (len(pts) - 1) for i in range(len(pts))]
    ys = [h - pad - p["viajeros_millones"] / vmax * (h - 2 * pad) for p in pts]
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in zip(xs, ys))
    puntos = "".join(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="4"/><text x="{x:.0f}" y="{y-10:.0f}" text-anchor="middle">{p["viajeros_millones"]}</text>'
                     f'<text x="{x:.0f}" y="{h-8}" text-anchor="middle" class="ax">{p["periodo"]}</text>' for x, y, p in zip(xs, ys, pts))
    color = {"RECUPERAR DEMANDA": "var(--bad)", "PREMIUM CON DEFENSA SELECTIVA": "var(--accent)",
             "ESTIMULAR VOLUMEN": "var(--good)", "MANTENER Y VIGILAR": "var(--muted)"}
    tarjetas = "".join(
        f'<div class="card"><div class="cid">{esc(r["diag"]["nombre"])}</div>'
        f'<div class="acc" style="color:{color[r["estr"]["rec"]["accion"]]}">{esc(r["estr"]["rec"]["accion"])}</div>'
        f'<div class="meta">Confianza {r["estr"]["rec"]["confianza"]} · Auditoría {esc(r["aud"]["veredicto"])}</div>'
        f'<div class="meta">Último: {r["estr"]["rec"]["senales"]["ultima_var_viajeros_pct"]:+.0f} % ({r["estr"]["rec"]["senales"]["periodo"]})</div></div>'
        for r in resultados)
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Radar Alta Velocidad</title><style>
:root{{--bg:#f7f6f2;--fg:#1d1d1b;--muted:#77756e;--card:#fff;--line:#e3e0d8;--accent:#6b2c91;--good:#2f7d4f;--bad:#b3261e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--fg:#ecebe6;--muted:#a3a19a;--card:#1f1f1d;--line:#33322f;--accent:#c39be0;--good:#7ccf9c;--bad:#f2867e}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif}}main{{max-width:960px;margin:auto;padding:24px 16px}}
h1{{font-size:24px;margin:0}}.sub{{color:var(--muted);margin-bottom:20px}}h2{{font-size:16px;margin:28px 0 10px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}}.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px}}
.cid{{font-weight:600}}.acc{{font-weight:700;font-size:13px;margin:6px 0}}.meta{{color:var(--muted);font-size:12px}}
.row{{display:flex;align-items:center;gap:8px;margin:6px 0}}.lbl{{width:170px;flex:none;font-size:13px}}.bar{{height:14px;background:var(--accent);border-radius:3px}}.val{{font-size:12px;color:var(--muted);white-space:nowrap}}
svg{{width:100%;max-width:560px;background:var(--card);border:1px solid var(--line);border-radius:10px}}svg polyline{{fill:none;stroke:var(--accent);stroke-width:2.5}}svg circle{{fill:var(--accent)}}svg text{{fill:var(--fg);font-size:11px}}svg .ax{{fill:var(--muted)}}
footer{{color:var(--muted);font-size:12px;margin-top:28px}}@media(max-width:520px){{.lbl{{width:110px}}}}
</style></head><body><main>
<h1>Radar competitivo de la alta velocidad — Renfe Viajeros</h1>
<div class="sub">Brief de decisión {esc(fecha)} · datos públicos CNMC / INE · {estado['tablas_ok']} datasets OK · {estado['llamadas']} llamadas MCP</div>
<h2>Decisión por corredor</h2><div class="grid">{tarjetas}</div>
<h2>Viajeros de alta velocidad por trimestre (millones, todos los operadores)</h2>
<svg viewBox="0 0 {w} {h}" role="img" aria-label="Viajeros trimestrales"><polyline points="{poly}"/>{puntos}</svg>
<h2>Tamaño de mercado 2025 y cuota Renfe más reciente</h2>{barras}
<footer>2025T2 derivado de la nota CNMC 2T 2026. Elasticidades aparentes, no causales. Fuentes completas en cada brief.</footer>
</main></body></html>"""


async def ejecutar(corredores: list[str], fecha: str) -> dict:
    REPORTS.mkdir(exist_ok=True)
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"], cwd=str(ROOT),
                                   env={"PYTHONPATH": str(ROOT), **{k: v for k, v in __import__("os").environ.items()
                                                                     if k in ("PATH", "HOME", "SYSTEMROOT")}})
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            mcp = ClienteMCP(session)
            estado = await mcp("estado_conexiones", comprobar_ine=False)
            analista, estratega, auditor = AnalistaMercado(mcp), EstrategaPricing(mcp), AuditorDatos(mcp)
            resultados = []
            for cid in corredores:
                diag = await analista.diagnosticar(cid)
                estr = await estratega.proponer(diag)
                aud = await auditor.auditar(diag, estr)
                ruta = REPORTS / f"brief_{cid}_{fecha}.md"
                ruta.write_text(redactar_brief(diag, estr, aud, fecha), encoding="utf-8")
                resultados.append({"diag": diag, "estr": estr, "aud": aud, "ruta": ruta})
                print(f"[{cid}] {estr['rec']['accion']:<30} confianza {estr['rec']['confianza']:<6} auditoría {aud['veredicto']:<17} -> {ruta.relative_to(ROOT)}")
            comp = (await mcp("comparar_corredores"))["filas"]
            total = (await mcp("serie_viajeros", corredor_id="TOTAL"))["filas"]

            resumen = [f"# Resumen ejecutivo — Radar competitivo alta velocidad — {fecha}", "",
                       "| Corredor | Acción | Confianza | Último dato viajeros | Cuota Renfe | KPI a vigilar |",
                       "|---|---|---|---|---|---|"]
            for x in resultados:
                rec, rs = x["estr"]["rec"], x["diag"]["resumen"]
                kpi = PASOS[rec["accion"]][0].split("KPI: ")[-1].rstrip(".")
                resumen.append(f"| {rs['nombre']} | **{rec['accion']}** | {rec['confianza']} | "
                               f"{rec['senales']['ultima_var_viajeros_pct']:+.0f} % ({rec['senales']['periodo']}) | "
                               f"{rs['cuota_renfe_ultima_pct']:.0f} % ({rs['periodo_cuota']}) | {kpi} |")
            (REPORTS / f"resumen_ejecutivo_{fecha}.md").write_text("\n".join(resumen) + "\n", encoding="utf-8")
            info = {"tablas_ok": sum(t["ok"] for t in estado["datos_locales"]["tablas"].values()),
                    "llamadas": len(mcp.traza) + 1}
            (REPORTS / f"dashboard_{fecha}.html").write_text(dashboard_html(resultados, comp, total, fecha, info), encoding="utf-8")
            (REPORTS / f"traza_mcp_{fecha}.json").write_text(json.dumps(mcp.traza, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"\n{len(mcp.traza)} llamadas MCP · resumen, dashboard y traza en reports/")
            return {"resultados": resultados, "llamadas": len(mcp.traza)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corredores", nargs="+", default=CORREDORES)
    ap.add_argument("--fecha", default=dt.date.today().isoformat())
    a = ap.parse_args()
    asyncio.run(ejecutar([c.upper() for c in a.corredores], a.fecha))


if __name__ == "__main__":
    main()
