---
name: informe-decision
description: Redacta el brief de decisión semanal para la Dirección Comercial / Revenue Management de Renfe Viajeros a partir de los resultados del servidor MCP renfe-bi. Úsala al final de un análisis, o cuando pidan "el brief", "el informe para dirección" o "qué decidimos en X corredor".
---

# Brief de decisión (1 página por corredor)

## Reglas de decisión (las mismas que `recomendar_accion`)
| Orden | Condición | Acción |
|---|---|---|
| 1 | Incidente en 2026 (o corte con caída ≤ −20 %) **y** viajeros ≤ −10 % interanual | **RECUPERAR DEMANDA** — no subir precios; fiabilidad, información, Avlo y flexibilidad |
| 2 | Elasticidad inelástica **y** corredor rentable **y** cuota Renfe cayendo | **PREMIUM CON DEFENSA SELECTIVA** — mantener ingreso medio AVE; Avlo en valle y trenes en competencia directa |
| 3 | Elasticidad elástica **y** ocupación < 75 % | **ESTIMULAR VOLUMEN** — bajadas tácticas en valle con piloto A/B |
| 4 | Resto | **MANTENER Y VIGILAR** |

Puedes matizar la recomendación con evidencia adicional, pero si te apartas de la regla, dilo y explica por qué.

## Estructura obligatoria
```
# Brief de decisión — <Corredor> — <fecha>
**Recomendación:** <ACCIÓN> (confianza <alta/media/baja>)
## Qué está pasando (3 viñetas con cifra + fuente_id)
## Por qué (mercado vs oferta)
## Escenarios de precio (tabla +5 % / −5 %: viajeros, ingresos, banda)
## Riesgos y lo que no sabemos
## Próximos pasos (máx. 3, con responsable y KPI de seguimiento)
## Fuentes (lista de fuente_id → URL, usando la herramienta fuentes)
```

## Estilo
- Español, frases cortas, cifras con unidad y periodo (p. ej. "−13 % interanual, 2T 2026").
- Ninguna cifra sin fuente. Señala con *(derivado)* las cifras calculadas.
- Guarda el resultado en `reports/brief_<corredor>_<AAAA-MM-DD>.md` si trabajas en el proyecto.
