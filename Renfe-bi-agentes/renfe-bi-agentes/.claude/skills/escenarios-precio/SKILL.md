---
name: escenarios-precio
description: Estima la elasticidad aparente precio-demanda de un corredor y simula escenarios de subida o bajada de precio (viajeros, ingresos, ocupación) con el servidor MCP renfe-bi. Úsala para preguntas de pricing tipo "¿y si subimos un 5 % el Madrid-Barcelona?".
---

# Escenarios de precio

## Procedimiento
1. `mcp__renfe-bi__elasticidad_precio(corredor_id)`: revisa cada observación.
   - Descarta mentalmente las marcadas `interpretable: false` (precio y demanda suben a la vez → desplazamiento de demanda, p. ej. más oferta).
   - Clases: `inelastica` (|e| < 0,5), `moderada` (0,5–1), `elastica` (> 1).
2. Simula **siempre al menos dos escenarios simétricos** (p. ej. +5 % y −5 %) con `mcp__renfe-bi__simular_escenario_precio`.
3. Lee la banda optimista/pesimista: si ambas tienen el mismo signo en `var_ingresos_pct`, la conclusión es robusta; si cambian de signo, la decisión es incierta y debe pilotarse.
4. Revisa `riesgo_capacidad`: con ocupación estimada > 90 % la bajada de precio no se traduce en viajeros (no hay plazas).

## Interpretación de referencia (datos 2025-2026)
- **Madrid-Barcelona**: elasticidad aparente entre −0,02 y −0,36 → subir precio aumentó ingresos del corredor, pero Renfe perdió 6 pp de cuota (56 % en 4T 2025). El riesgo no es el ingreso de hoy sino la cuota de mañana.
- **Corredor sur (SEV, MAL)**: elasticidades de −0,8 a −1,8 tras la entrada de Ouigo → la demanda responde fuerte al precio.

## Advertencias obligatorias en la respuesta
- Elasticidad **aparente**, no causal (la oferta de plazas y la competencia cambian a la vez).
- Base = mercado total del corredor (todos los operadores), no solo Renfe.
- No modela la reacción de Iryo/Ouigo: recomiéndalo como siguiente paso si la decisión es grande.
