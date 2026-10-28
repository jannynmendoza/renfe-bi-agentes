---
description: Genera el brief de decisión semanal de uno o todos los corredores con el equipo de agentes (analista → estratega → auditor).
argument-hint: [BCN|VLC|ALI|SEV|MAL|todos]
---

Corredor(es) a analizar: **$ARGUMENTS** (si está vacío, usa `todos`).

Orquesta el equipo así, en orden:

1. Llama a `mcp__renfe-bi__estado_conexiones` con `comprobar_ine=true` e indica en una línea el estado.
2. Para cada corredor, delega en el subagente **analista-mercado** el diagnóstico.
3. Pasa ese diagnóstico al subagente **estratega-pricing** para escenarios y recomendación.
4. Redacta el brief con la skill **informe-decision**.
5. Entrega el borrador al subagente **auditor-datos**; aplica sus correcciones.
6. Guarda cada brief en `reports/brief_<CORREDOR>_<AAAA-MM-DD>.md` y, si son varios, un `reports/resumen_ejecutivo_<AAAA-MM-DD>.md` con una tabla corredor | acción | confianza | KPI a vigilar.

Termina con 3 líneas: decisiones clave, riesgos principales y la ruta de los archivos.
