---
name: analisis-corredor
description: Analiza un corredor de alta velocidad (BCN, VLC, ALI, SEV, MAL) para Renfe Viajeros — demanda, precios, cuotas frente a Iryo y Ouigo, ocupación y eventos — usando el servidor MCP renfe-bi. Úsala cuando pidan diagnosticar un corredor, compararlos o explicar por qué cae o sube la demanda.
---

# Análisis de corredor de alta velocidad

## Cuándo usarla
Diagnóstico de uno o varios corredores Madrid-X antes de decidir precio o capacidad.

## Procedimiento
1. `mcp__renfe-bi__comparar_corredores` → sitúa el corredor frente al resto (tamaño de mercado, ingreso medio, cuota Renfe, última variación).
2. `mcp__renfe-bi__kpis_corredor(corredor_id)` → serie trimestral, precios, cuotas, ocupación, eventos.
3. `mcp__renfe-bi__eventos(corredor_id)` → separa causas **de mercado** (entrada de Ouigo, subidas de precio) de causas **de oferta** (Adamuz 18/01/2026, Álora, limitaciones de velocidad). Nunca atribuyas al precio una caída que coincide con un corte de vía.
4. Si la pregunta es de tendencia reciente: `mcp__renfe-bi__demanda_mensual(en_vivo=true)`; si falla, el servidor devuelve el snapshot y lo indica.

## KPIs y cómo leerlos
| KPI | Definición | Lectura |
|---|---|---|
| Viajeros (M) y var. interanual | CNMC trimestral / anual | Tendencia de demanda del corredor (todos los operadores) |
| Ingreso medio por trayecto (€) | ingresos / viajeros | Proxy del precio real pagado. **No mezclar** metodologías: `precio_web_trayecto` (con IVA, webs) ≠ `ingreso_medio_trayecto_sin_iva` |
| Cuota Renfe (%) | CNMC | Pérdida de cuota con mercado creciendo = presión competitiva; con mercado cayendo = puede ser shock de oferta |
| Ocupación (%) | viajeros·km / plazas·km | Solo 1T 2025 publicada; úsala como referencia, no como dato actual |
| Mercado estimado (M€) | viajeros 2025 × ingreso medio 2025 | Tamaño del premio en juego por corredor |
| Peso de cánones en coste | CNMC | Cuanto mayor, menos margen para bajar precios |

## Reglas de rigor
- Indica siempre `tipo_dato` (publicado / derivado) y el `fuente_id`.
- Las cuotas "≈62 %" y ">60 %" son aproximadas en la fuente: dilo.
- No inventes cifras de operadores que la CNMC no publica (p. ej. cuota de Avlo por separado).

## Salida esperada
Diagnóstico en 5-8 viñetas: qué pasa, por qué (causa de mercado vs oferta), qué cifra lo prueba (con fuente) y qué no sabemos.
