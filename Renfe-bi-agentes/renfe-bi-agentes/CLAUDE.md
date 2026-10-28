# Radar Competitivo de Alta Velocidad — Renfe Viajeros (TFM INESDI, módulo Big Data, Analytics e IA)

Sistema agéntico de apoyo a decisiones de precio y capacidad por corredor.

## Piezas
- **MCP `renfe-bi`** (`mcp_server/server.py`, registrado en `.mcp.json`): 14 herramientas sobre datos reales CNMC/INE 2025-2026 y conector en vivo a la API del INE.
- **Skills** (`.claude/skills/`): `analisis-corredor`, `escenarios-precio`, `informe-decision`, `verificacion-datos`.
- **Subagentes** (`.claude/agents/`): `analista-mercado`, `estratega-pricing`, `auditor-datos`.
- **Comando**: `/decision-semanal [corredor|todos]` orquesta el flujo completo.

## Reglas para Claude en este proyecto
- Las cifras salen SIEMPRE de herramientas `mcp__renfe-bi__*`, nunca de memoria. Cita `fuente_id`.
- Distingue datos publicados de derivados y no mezcles métricas de precio.
- Corredores válidos: BCN, VLC, ALI, SEV, MAL (y TOTAL en series de viajeros).
- Los informes se guardan en `reports/`.
- Tests: `pytest tests -v`. Conexiones: `python scripts/test_connections.py --live`.
