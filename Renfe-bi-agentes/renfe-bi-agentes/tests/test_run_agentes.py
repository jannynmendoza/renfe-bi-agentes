"""Verifica el orquestador de agentes sin red: un cliente falso imita la forma de la Messages API."""
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace as NS

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "agents"))
import run_agentes as ra  # noqa: E402


class ClienteFalso:
    """Primer turno de cada agente: pide una herramienta permitida. Segundo: responde texto."""

    def __init__(self):
        self.llamadas = []
        self.messages = self

    def create(self, **kw):
        self.llamadas.append(kw)
        nombres = {t["name"] for t in kw["tools"]}
        ultimo = kw["messages"][-1]
        if isinstance(ultimo["content"], list) and ultimo["content"][0].get("type") == "tool_result":
            assert not ultimo["content"][0]["is_error"], ultimo
            return NS(stop_reason="end_turn", content=[NS(type="text", text=f"OK con {len(nombres)} herramientas")])
        tool = next(t for t in ("kpis_corredor", "recomendar_accion", "fuentes") if t in nombres)
        args = {} if tool == "fuentes" else {"corredor_id": "BCN"}
        return NS(stop_reason="tool_use", content=[NS(type="tool_use", id=f"t{len(self.llamadas)}", name=tool, input=args)])


def test_definiciones_de_agentes():
    a = ra.cargar_agente("estratega-pricing")
    assert "simular_escenario_precio" in a["tools"]
    assert '<skill nombre="escenarios-precio">' in a["system"]
    assert '<skill nombre="informe-decision">' in a["system"]


def test_orquestacion_completa(tmp_path, monkeypatch):
    cli = ClienteFalso()
    salida = asyncio.run(ra.orquestar(cli, "BCN", None, "2000-01-01"))
    try:
        assert salida.exists()
        assert len(cli.llamadas) == 8  # 4 fases x (tool_use + respuesta)
        # cada agente solo recibe sus herramientas
        tools_auditor = {t["name"] for t in cli.llamadas[-1]["tools"]}
        assert "simular_escenario_precio" not in tools_auditor and "fuentes" in tools_auditor
    finally:
        salida.unlink(missing_ok=True)
        (ROOT / "reports" / "traza_agentes_BCN_2000-01-01.json").unlink(missing_ok=True)
