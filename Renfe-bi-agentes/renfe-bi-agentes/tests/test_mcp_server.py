"""Test de integración: arranca el servidor MCP por stdio y llama a las 14 herramientas."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import test_connections as tc  # noqa: E402


def test_mcp_stdio_todas_las_herramientas():
    resultados = asyncio.run(tc.probar_mcp(live=False))
    fallos = [r for r in resultados if not r["ok"]]
    assert not fallos, fallos
    assert sum(1 for r in resultados if r["prueba"].startswith("tool ")) == 14


def test_artefactos_agenticos():
    fallos = [r for r in tc.probar_artefactos() if not r["ok"]]
    assert not fallos, fallos
