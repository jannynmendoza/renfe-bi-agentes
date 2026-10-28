# Radar Competitivo de la Alta Velocidad — Renfe Viajeros
**Trabajo final · Módulo Big Data, Analytics e IA · Máster en Business Analytics e IA (INESDI)**
Autora: Jannyn Mendoza · Octubre 2026

---

## 1. Empresa y contexto

**Renfe Viajeros** (grupo Renfe, operador público ferroviario de España) compite desde la liberalización de la alta velocidad con **Iryo** (participada por Trenitalia) y **Ouigo** (SNCF) en los cinco grandes corredores desde Madrid: Barcelona, Valencia, Alicante, Sevilla y Málaga/Granada.

Datos clave (fuentes públicas, ver `data/fuentes.csv`):

| Indicador | Valor | Fuente |
|---|---|---|
| Viajeros alta velocidad comercial 2025 | 44,5 M (+12 %, el doble que 2019) | CNMC, informe anual 2025 |
| Beneficio neto Renfe 2025 | 60,2 M€ (vs −2,9 M€ en 2024) | Resultados Renfe 2025 |
| Ingresos por billetes AV y larga distancia 2025 | 1.469 M€ (+7,5 %) | Resultados Renfe 2025 |
| Cuota Renfe en Madrid-Barcelona | 56 % en 4T 2025 (−6 pp) | CNMC 4T 2025 |
| Único corredor con ingresos > costes | Madrid-Barcelona (+6 %) | CNMC, informe anual 2025 |
| Viajeros AV 1T 2026 | 8,05 M (−21 % interanual) | CNMC 1T 2026 |
| Viajeros AV 2T 2026 | 10,6 M (−10 % interanual) | CNMC 2T 2026 |

**2026 es un año de shock**: el accidente de Adamuz (18/01/2026) cortó el corredor Madrid-Andalucía durante semanas; Madrid-Málaga estuvo cerrado hasta el 30/04 por el desprendimiento de Álora y reabrió en vía única; Madrid-Barcelona sufre limitaciones de velocidad. A la vez, la competencia sigue ganando cuota.

## 2. Mercado, soluciones actuales, competidores y limitaciones

### Mercado
- La competencia redujo los precios medios entre un 33 % y un 42 % frente a antes de la liberalización (CNMC 1T 2026) y duplicó la demanda.
- Pero el modelo es frágil: las empresas ferroviarias pasaron de 133 M€ de beneficio (2019) a −99,5 M€ (2024) (CNMC, balance 2024). Los cánones pesan el 46 % del coste en Madrid-Barcelona, el 38 % en Andalucía y el 30 % en Levante.
- En 2025 los corredores divergieron: **Madrid-Barcelona** subió precio (+15,2 %) y perdió viajeros (−1,7 %); el **corredor sur** bajó precio (−12 %, entrada de Ouigo) y creció (+18,7 % Sevilla, +14,1 % Málaga).

### Competidores
| Operador | Situación | Fuente |
|---|---|---|
| **Iryo** | Ingresos 320 M€ en España 2025; pérdidas reducidas de 31,6 a 5 M€. Cuota 20-26 % en los corredores donde opera. | Merca2, CNMC |
| **Ouigo** | 191 M€ de pérdidas acumuladas hasta 2024; en 2025 +44,3 % viajeros y, según prensa, primer año sin pérdidas. Cuota 13-14 % en el sur y 19 % en Madrid-Barcelona (4T 2025). | Merca2, CNMC |
| **Avión y autobús** | Tren = 83,1 % del mercado tren+avión en Madrid-Barcelona. Durante el corte de febrero 2026 el autobús de larga distancia creció un 15,1 %. | CNMC, INE |

### Soluciones actuales en Renfe
- **Revenue management operativo**: Renfe usa **Appia (Expretio)** desde 2011, renovado en junio de 2026, con inteligencia de precios de competidores vía QL2 y migración a Sqills (Railway-News, 03/06/2026).
- **Informes regulatorios**: CNMC (trimestral, ~3 meses de retraso) e INE (mensual).

### Limitaciones detectadas
1. Appia optimiza **tren a tren y día a día**; no responde a preguntas **estratégicas por corredor** ("¿defendemos cuota o margen en Barcelona?").
2. La información de mercado (CNMC, INE, prensa) está **dispersa**, en PDF y notas de prensa, con **métricas no comparables** (precio web con IVA vs ingreso medio sin IVA).
3. No hay una capa que **separe causas de oferta** (Adamuz, cortes) de **causas de mercado** (precio, competencia) antes de decidir.
4. El análisis depende de analistas que tardan días en consolidar cada informe trimestral.

## 3. Pensamiento divergente: 5 problemas de Business Intelligence

| # | Problema | Pregunta de decisión | Datos reales disponibles |
|---|---|---|---|
| P1 | **Precio vs cuota en Madrid-Barcelona** | ¿Seguimos subiendo precio (corredor rentable, demanda inelástica) o defendemos cuota frente a Iryo y Ouigo? | CNMC trimestral y anual: precios, viajeros, cuotas |
| P2 | **Recuperación de la demanda tras Adamuz** en el corredor sur | ¿Cuándo y cómo recuperar los viajeros perdidos (−27 % Sevilla, −61 % Málaga en 1T 2026)? ¿Tarifas, confianza, capacidad? | CNMC, INE mensual, eventos |
| P3 | **Fuga de viajeros de Media Distancia** (−10,8 % en 2025; puntualidad 59,4 %) | ¿Qué líneas OSP priorizar en inversión de fiabilidad para frenar el abandono? | CNMC, portal de puntualidad de Renfe |
| P4 | **Coste de la impuntualidad en larga distancia** (28,8 % con retraso ene-may 2026) | ¿Cuánto cuestan las compensaciones y la pérdida de demanda por retrasos, y dónde actuar primero? | Portal Renfe, CNMC |
| P5 | **Asignación de flota AVE / Avlo entre corredores** con distinto peso de cánones | ¿Dónde rinde más cada tren: en qué corredor y franja colocar Avlo y AVE? | CNMC (cánones, ocupación), resultados Renfe |

## 4. Pensamiento convergente: comparación y elección

Criterios (peso): **impacto económico** (30 %), **disponibilidad de datos reales públicos** (25 %), **viabilidad de un sistema agéntico funcional** (20 %), **urgencia** (15 %), **medibilidad con KPI** (10 %). Escala 1-5.

| Problema | Impacto | Datos | Viabilidad | Urgencia | Medible | **Total** |
|---|---|---|---|---|---|---|
| P1 Precio vs cuota BCN | 5 | 5 | 5 | 4 | 5 | **4,85** |
| P2 Recuperación post-Adamuz | 4 | 4 | 4 | 5 | 4 | **4,15** |
| P3 Media Distancia | 3 | 3 | 3 | 4 | 4 | 3,25 |
| P4 Coste impuntualidad | 3 | 2 | 3 | 4 | 3 | 2,90 |
| P5 Flota AVE/Avlo | 4 | 2 | 2 | 3 | 3 | 2,85 |

*(Total = Σ puntuación × peso.)*

**Elección: P1 + P2 integrados en un "Radar Competitivo de Alta Velocidad"**: un sistema que, corredor a corredor, decide entre **defender margen, defender cuota o recuperar demanda**. P1 y P2 comparten datos, herramientas y usuario, y juntos cubren los 5 corredores (≈1.515 M€ de mercado estimado en 2025). P3-P5 quedan como extensiones: necesitan datos internos que hoy no son públicos.

## 5. Usuario, propuesta de valor, objetivos y KPI

### Usuario
- **Primario**: Gerente de corredor / Revenue Manager estratégico de la Dirección Comercial de Renfe Viajeros. Decide política de precios y mix AVE/Avlo por corredor cada semana-trimestre.
- **Secundario**: Dirección Comercial (consume el resumen ejecutivo) y equipo de Data (mantiene conectores).

### Propuesta de valor
> *"En minutos, no en días: una recomendación por corredor —margen, cuota o recuperación— basada solo en datos públicos verificables, que separa el efecto de la competencia del efecto de los incidentes y cita la fuente de cada cifra."*

Diferencial frente a Appia/QL2: **capa estratégica y explicable** por encima del RM operativo; complementa, no sustituye.

### Objetivos (OKR del piloto, 1 trimestre)
- **O1. Decidir antes**: el brief trimestral sale el mismo día de publicación de la CNMC.
- **O2. Decidir mejor**: cada recomendación con evidencia auditada y escenarios.
- **O3. Recuperar mercado**: frenar la pérdida de cuota en Madrid-Barcelona y recuperar la demanda del sur.

### KPI
| Tipo | KPI | Línea base (dato real) | Meta piloto |
|---|---|---|---|
| Negocio | Cuota Renfe Madrid-Barcelona | 56 % (4T 2025) | ≥ 58 % |
| Negocio | Viajeros corredor sur vs mismo periodo 2025 | −27 % SEV / −61 % MAL (1T 2026) | ≥ −5 % al cierre de 4T 2026 |
| Negocio | Ingreso medio por trayecto Madrid-Barcelona | 56 € sin IVA (2T 2026) | Mantener ± 3 % |
| Negocio | Ingresos por billetes AV + LD | 1.469 M€ (2025) | Crecimiento ≥ inflación |
| Sistema | Tiempo de elaboración del brief | días (manual) | < 10 min |
| Sistema | % cifras con fuente verificada (auditor) | — | 100 % |
| Sistema | Disponibilidad de conectores (`test_connections`) | — | 27/27 pruebas OK |
| Adopción | Decisiones de comité que citan el brief | — | ≥ 3 por trimestre |

## 6. Solución construida (sistema agéntico)

```
             ┌────────────── /decision-semanal (comando) ──────────────┐
             │                                                         │
   analista-mercado ──► estratega-pricing ──► auditor-datos ──► brief + dashboard
   skill: analisis-     skills: escenarios-   skill: verificacion-
   corredor             precio, informe-      datos
                        decision
             │                 │                      │
             └──────────── MCP renfe-bi (14 herramientas, stdio) ────────┘
                               │                         │
                 10 datasets reales (CNMC, INE,     API INE en vivo
                 prensa) con fuente_id por fila     (tabla 49359)
```

- **Datos reales**: 10 tablas CSV con 130+ filas, cada una con `fuente_id` → URL pública.
- **MCP**: `estado_conexiones, listar_corredores, comparar_corredores, kpis_corredor, serie_viajeros, serie_precios, cuotas_mercado, elasticidad_precio, simular_escenario_precio, recomendar_accion, eventos, datos_competidores, demanda_mensual (snapshot / en vivo INE), fuentes` + prompt `brief_semanal`.
- **Skills**: 4 (`analisis-corredor`, `escenarios-precio`, `informe-decision`, `verificacion-datos`).
- **Agentes**: 3 subagentes de Claude Code + orquestador Python con la API de Claude que reutiliza las mismas definiciones.
- **Pruebas**: 22 tests pytest + `scripts/test_connections.py` (27 pruebas obligatorias + 2 en vivo).

## 7. Resultado de la demo (datos a 2T 2026)

| Corredor | Recomendación | Por qué |
|---|---|---|
| Madrid-Barcelona | **PREMIUM CON DEFENSA SELECTIVA** | Elasticidad aparente −0,02 a −0,36: +5 % de precio ≈ +4,4 % de ingresos del corredor. Pero Renfe cayó a 56 % de cuota → defender con Avlo en valle y trenes en competencia directa. |
| Madrid-Sevilla | **RECUPERAR DEMANDA** | −27 % viajeros en 1T 2026 tras Adamuz; demanda elástica (−1,3 a −1,8): no es momento de subir precio. |
| Madrid-Málaga/Granada | **RECUPERAR DEMANDA** | −30 % en 2T 2026 con vía única y −30 % de plazas. |
| Madrid-Valencia / Alicante | **MANTENER Y VIGILAR** | Señales mixtas; caídas moderadas (−8 % / −6 %). |

**Insight principal**: Madrid-Barcelona y el corredor sur piden políticas *opuestas*. Una política de precios única para la alta velocidad destruiría valor en uno de los dos.

## 8. Limitaciones y siguientes pasos
- Datos públicos agregados: la elasticidad es **aparente**, no causal. Siguiente paso: conectar datos internos de ventas (Appia/Sqills) como un segundo servidor MCP.
- Algunos trimestres por corredor se **derivan** de variaciones publicadas (marcados en los datos).
- No se modela la reacción de la competencia: extensión con teoría de juegos o simulación de agentes.
- Ampliar a P3-P5 añadiendo datos de puntualidad por línea.
