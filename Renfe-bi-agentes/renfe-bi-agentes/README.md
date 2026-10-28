# Radar Competitivo de Alta Velocidad — Renfe Viajeros

Sistema agéntico (MCP + Skills + subagentes) que recomienda, corredor a corredor, si Renfe debe **defender margen, defender cuota o recuperar demanda** frente a Iryo y Ouigo, con **datos reales** de la CNMC y el INE (2025-2026).

> Trabajo final del módulo *Big Data, Analytics e IA* — Máster en Business Analytics e IA, INESDI.
> El análisis de negocio completo (5 problemas, mercado, competidores, matriz de decisión, usuario, KPI) está en [`docs/propuesta.md`](docs/propuesta.md).

## Estructura
```
renfe-bi-agentes/
├── .mcp.json                 # registro del servidor MCP para Claude Code
├── .vscode/                  # mcp.json (Copilot/VS Code), tareas, depuración, extensiones
├── .claude/
│   ├── skills/               # 4 skills (SKILL.md)
│   ├── agents/               # 3 subagentes: analista-mercado, estratega-pricing, auditor-datos
│   ├── commands/             # /decision-semanal
│   └── settings.json         # permisos de herramientas MCP
├── CLAUDE.md                 # contexto del proyecto para Claude
├── mcp_server/               # servidor MCP renfe-bi (14 herramientas + 1 prompt)
│   ├── server.py  bi_core.py  ine_client.py
├── data/                     # 10 datasets reales con fuente_id por fila + fuentes.csv
├── agents/run_agentes.py     # equipo de agentes con la API de Claude (reutiliza .claude/)
├── scripts/
│   ├── test_connections.py   # prueba TODAS las conexiones
│   └── demo_decision.py      # demo sin API key: briefs + dashboard
├── tests/                    # 22 tests pytest
├── reports/                  # salidas (incluye una ejecución de ejemplo)
└── docs/propuesta.md         # documento de negocio
```

## Puesta en marcha (VS Code)
1. Abre la carpeta en VS Code (*File → Open Folder*). Acepta las extensiones recomendadas.
2. Crea el entorno: *Terminal → Run Task → "1. Instalar entorno"*, o:
   ```bash
   python -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Comprueba que todo conecta:
   ```bash
   pytest -v                                   # 22 tests
   python scripts/test_connections.py --live   # MCP por stdio + API INE en vivo
   ```
4. Demo sin clave de API:
   ```bash
   python scripts/demo_decision.py
   ```
   Abre `reports/dashboard_<fecha>.html` y los `brief_*.md`.

## Usar los agentes
### Opción A — Claude Code en VS Code (recomendada)
Con el venv activado, abre Claude Code en la carpeta del proyecto. Detectará `.mcp.json` (servidor `renfe-bi`), las skills, los subagentes y el comando. Ejecuta `/mcp` para ver el servidor conectado y luego:
```
/decision-semanal todos
/decision-semanal BCN
¿Qué pasa si subimos un 8 % el Madrid-Barcelona?
```

### Opción B — API de Claude (script)
```bash
cp .env.example .env      # añade ANTHROPIC_API_KEY
python agents/run_agentes.py --corredor SEV --pregunta "¿Bajamos un 10 % para recuperar demanda?"
```

### Opción C — Otros clientes MCP
- **GitHub Copilot (modo agente) en VS Code**: usa `.vscode/mcp.json` (en Windows cambia `.venv/bin/python` por `.venv\\Scripts\\python.exe`).
- **MCP Inspector**: tarea "MCP Inspector" (requiere Node.js).

## Herramientas MCP
| Herramienta | Qué hace |
|---|---|
| `estado_conexiones` | Health-check de datasets y API INE |
| `listar_corredores`, `comparar_corredores`, `kpis_corredor` | Visión de mercado por corredor |
| `serie_viajeros`, `serie_precios`, `cuotas_mercado`, `eventos` | Series y contexto |
| `elasticidad_precio`, `simular_escenario_precio` | Analítica de pricing |
| `recomendar_accion` | Regla de decisión explicable |
| `datos_competidores` | Finanzas Renfe / Iryo / Ouigo |
| `demanda_mensual` | Snapshot INE o **en vivo** (tabla INE 49359) con fallback |
| `fuentes` | Resuelve `fuente_id` → URL |

## Aplicación de escritorio (frontend)
Interfaz para usuarios de negocio sobre los mismos datos y reglas que el servidor MCP: resumen del mercado, ficha por corredor con la acción recomendada, simulador de precios, competidores, demanda INE (guardada o en vivo) y fuentes.
- **Ejecutable:** `App/RadarCompetitivoAV.exe` (en la carpeta del trabajo). Doble clic y se abre en su propia ventana. Lee de Supabase si junto al `.exe` hay un `.env` con `SUPABASE_DB_URL`; si no, usa los CSV que lleva incluidos.
- **Desde el código:** `python frontend/app.py` (`--navegador` para abrirlo en el navegador, `--servidor` solo para levantar la API).
- **Regenerar el .exe:** `powershell -ExecutionPolicy Bypass -File frontend\build_exe.ps1`

## Base de datos (Supabase)
Los 10 datasets se publican en una base de datos PostgreSQL de [Supabase](https://supabase.com/dashboard/organizations) y el servidor MCP los lee de allí.
1. En Supabase crea un proyecto y copia la cadena de *Connect → Session pooler*.
2. Añádela al `.env` como `SUPABASE_DB_URL` (ver `.env.example`).
3. Carga los datos (crea las tablas e inserta las filas de `data/*.csv`):
   ```bash
   python "../../BD Supabase/cargar_datos_supabase.py"
   ```
   O pega `01_crear_esquema_supabase.sql` y `02_insertar_datos_supabase.sql` en el *SQL Editor* de Supabase.
4. Comprueba: `python scripts/test_connections.py` muestra `origen de datos (supabase)` y `pytest` verifica que Supabase coincide con los CSV.

Sin `SUPABASE_DB_URL` (o con `RENFE_BI_ORIGEN=csv`) el proyecto usa los CSV de `data/`.

## Datos
Todas las cifras proceden de fuentes públicas listadas en `data/fuentes.csv` (notas trimestrales y anual de la CNMC, INE, resultados publicados de Renfe, Iryo y Ouigo). Las filas con `tipo_dato=derivado` se calculan a partir de variaciones publicadas y lo indican en `nota`. Las cifras de víctimas de Adamuz no se incluyen porque difieren entre medios.

## Notas
- Probado con Python 3.13 y SDK `mcp` 2.x; el servidor también funciona con `mcp` 1.x.
- `python` en `.mcp.json` debe ser el del venv: abre VS Code / Claude Code con el venv activado.
