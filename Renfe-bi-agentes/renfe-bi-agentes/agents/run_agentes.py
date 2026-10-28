"""
Equipo de agentes con la API de Claude, fuera de Claude Code.

Reutiliza EXACTAMENTE las mismas definiciones que usa Claude Code en VS Code:
  * prompts y herramientas permitidas -> .claude/agents/*.md (frontmatter `tools`, `skills`)
  * conocimiento procedimental       -> .claude/skills/*/SKILL.md (se inyecta en el system prompt)
  * herramientas                     -> servidor MCP renfe-bi (stdio), traducidas a tool use de la API

Flujo:  analista-mercado -> estratega-pricing -> auditor-datos -> brief final (skill informe-decision)

Uso:
  cp .env.example .env   # pon tu ANTHROPIC_API_KEY
  python agents/run_agentes.py --corredor BCN
  python agents/run_agentes.py --corredor SEV --pregunta "¿Bajamos un 10 % el Avlo?"
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

PREFIJO = "mcp__renfe-bi__"
MODELO = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
MAX_TURNOS = 12


# ------------------------------------------------------------ definiciones
def leer_md(path: Path) -> tuple[dict[str, str], str]:
    txt = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", txt, re.S)
    if not m:
        return {}, txt
    meta = {}
    for linea in m.group(1).splitlines():
        if ":" in linea:
            k, v = linea.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, m.group(2).strip()


def cargar_agente(nombre: str) -> dict[str, Any]:
    meta, cuerpo = leer_md(ROOT / ".claude/agents" / f"{nombre}.md")
    tools = [t.strip()[len(PREFIJO):] for t in meta.get("tools", "").split(",") if t.strip().startswith(PREFIJO)]
    skills = [s.strip() for s in meta.get("skills", "").split(",") if s.strip()]
    textos_skill = []
    for s in skills:
        _, body = leer_md(ROOT / ".claude/skills" / s / "SKILL.md")
        textos_skill.append(f"<skill nombre=\"{s}\">\n{body}\n</skill>")
    system = (cuerpo + "\n\nReglas del proyecto: las cifras salen solo de las herramientas; cita fuente_id. "
              "Las herramientas se llaman sin el prefijo mcp__renfe-bi__.\n\n" + "\n\n".join(textos_skill))
    return {"nombre": nombre, "system": system, "tools": tools}


# ------------------------------------------------------------ MCP -> API
def mcp_a_tool_api(t) -> dict[str, Any]:
    schema = getattr(t, "inputSchema", None) or getattr(t, "input_schema", None) or {"type": "object", "properties": {}}
    return {"name": t.name, "description": (t.description or "")[:1000], "input_schema": schema}


async def llamar_mcp(session: ClientSession, nombre: str, args: dict) -> tuple[str, bool]:
    res = await session.call_tool(nombre, args)
    texto = "\n".join(getattr(c, "text", "") for c in res.content)
    return texto[:20000], bool(getattr(res, "isError", False))


def _bloques_a_dict(content) -> list[dict[str, Any]]:
    out = []
    for b in content:
        if b.type == "text":
            out.append({"type": "text", "text": b.text})
        elif b.type == "tool_use":
            out.append({"type": "tool_use", "id": b.id, "name": b.name, "input": b.input})
    return out


async def ejecutar_agente(cliente, session, agente: dict, tools_api: list[dict], tarea: str,
                          traza: list[dict]) -> str:
    tools = [t for t in tools_api if t["name"] in agente["tools"]]
    mensajes: list[dict[str, Any]] = [{"role": "user", "content": tarea}]
    for _ in range(MAX_TURNOS):
        resp = cliente.messages.create(model=MODELO, max_tokens=4000, system=agente["system"],
                                       tools=tools, messages=mensajes)
        bloques = _bloques_a_dict(resp.content)
        mensajes.append({"role": "assistant", "content": bloques})
        usos = [b for b in bloques if b["type"] == "tool_use"]
        if resp.stop_reason != "tool_use" or not usos:
            return "\n".join(b["text"] for b in bloques if b["type"] == "text").strip()
        resultados = []
        for u in usos:
            if u["name"] not in agente["tools"]:
                texto, err = f"Herramienta {u['name']} no permitida para {agente['nombre']}", True
            else:
                texto, err = await llamar_mcp(session, u["name"], u["input"])
            traza.append({"agente": agente["nombre"], "tool": u["name"], "args": u["input"], "error": err})
            print(f"   · {agente['nombre']} -> {u['name']}({json.dumps(u['input'], ensure_ascii=False)})")
            resultados.append({"type": "tool_result", "tool_use_id": u["id"], "content": texto, "is_error": err})
        mensajes.append({"role": "user", "content": resultados})
    return "(límite de turnos alcanzado)"


async def orquestar(cliente, corredor: str, pregunta: str | None, fecha: str) -> Path:
    params = StdioServerParameters(command=sys.executable, args=["-m", "mcp_server.server"], cwd=str(ROOT),
                                   env={"PYTHONPATH": str(ROOT), **{k: v for k, v in os.environ.items()
                                                                     if k in ("PATH", "HOME", "SYSTEMROOT")}})
    traza: list[dict] = []
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            tools_api = [mcp_a_tool_api(t) for t in (await session.list_tools()).tools]
            analista, estratega, auditor = (cargar_agente(n) for n in
                                            ("analista-mercado", "estratega-pricing", "auditor-datos"))
            extra = f"\nPregunta de negocio: {pregunta}" if pregunta else ""

            print(f"[1/4] analista-mercado · {corredor}")
            diag = await ejecutar_agente(cliente, session, analista, tools_api,
                                         f"Diagnostica el corredor {corredor}.{extra}", traza)
            print(f"[2/4] estratega-pricing · {corredor}")
            estr = await ejecutar_agente(cliente, session, estratega, tools_api,
                                         f"Corredor {corredor}.{extra}\n\nDiagnóstico del analista:\n{diag}", traza)
            print("[3/4] estratega redacta el brief (skill informe-decision)")
            borrador = await ejecutar_agente(
                cliente, session, estratega, tools_api,
                f"Redacta el brief final del corredor {corredor} con fecha {fecha} siguiendo la skill "
                f"informe-decision, usando:\n\nDIAGNÓSTICO:\n{diag}\n\nPROPUESTA:\n{estr}", traza)
            print("[4/4] auditor-datos")
            auditoria = await ejecutar_agente(cliente, session, auditor, tools_api,
                                              f"Audita este brief:\n\n{borrador}", traza)

    (ROOT / "reports").mkdir(exist_ok=True)
    salida = ROOT / "reports" / f"brief_agentes_{corredor}_{fecha}.md"
    salida.write_text(f"{borrador}\n\n---\n\n## Auditoría de datos (agente auditor-datos)\n\n{auditoria}\n",
                      encoding="utf-8")
    (ROOT / "reports" / f"traza_agentes_{corredor}_{fecha}.json").write_text(
        json.dumps(traza, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(traza)} llamadas MCP · brief en {salida.relative_to(ROOT)}")
    return salida


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corredor", default="BCN", choices=["BCN", "VLC", "ALI", "SEV", "MAL"])
    ap.add_argument("--pregunta")
    ap.add_argument("--fecha", default=dt.date.today().isoformat())
    a = ap.parse_args()
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("Falta ANTHROPIC_API_KEY (copia .env.example a .env). Sin clave usa: python scripts/demo_decision.py")
    import anthropic
    asyncio.run(orquestar(anthropic.Anthropic(), a.corredor, a.pregunta, a.fecha))


if __name__ == "__main__":
    main()
