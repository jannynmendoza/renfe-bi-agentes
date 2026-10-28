---
name: verificacion-datos
description: Verifica conexiones y calidad de datos del sistema renfe-bi y audita que cada cifra de un informe esté respaldada por una fuente real. Úsala antes de entregar cualquier análisis o cuando algo "no cuadra".
---

# Verificación de datos y fuentes

## 1. Conexiones
- `mcp__renfe-bi__estado_conexiones(comprobar_ine=true)`:
  - `datos_locales.ok` debe ser `true` (10 tablas).
  - `api_ine.ok = false` no bloquea: el sistema usa el snapshot, pero el informe debe decirlo.
- Desde terminal: `python scripts/test_connections.py --live` prueba todas las herramientas MCP por stdio y la API del INE.

## 2. Auditoría de un informe
Para cada cifra del texto:
1. Localízala en la salida de alguna herramienta (no en la memoria del modelo).
2. Comprueba periodo, unidad y métrica (¿precio web con IVA o ingreso medio sin IVA?).
3. Comprueba que el `fuente_id` existe con `mcp__renfe-bi__fuentes`.
4. Marca como **NO VERIFICADA** cualquier cifra que no cumpla 1-3.

## 3. Controles de coherencia conocidos
- Suma trimestral 2025 ≈ anual: 10,2 + 11,8 + 11,8 + 10,6 = 44,4 M ≈ 44,5 M (CNMC). Desviación aceptable < 1 %.
- Cuotas de un corredor/periodo no deben superar 100 % (BCN 4T25: 56 + 24 + 19 = 99 %).
- Las cifras de víctimas del accidente de Adamuz difieren entre medios: **no las cites**; usa solo fecha e impacto en el servicio.

## Salida
Tabla `cifra | estado (OK / NO VERIFICADA / AJUSTAR) | fuente_id | comentario` y un veredicto final.
