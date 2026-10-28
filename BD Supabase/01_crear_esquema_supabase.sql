-- =====================================================================
-- RENFE BI - Esquema PostgreSQL para Supabase
-- Crea en el esquema public las tablas que reflejan los CSV de
-- Renfe-bi-agentes/renfe-bi-agentes/data. Es re-ejecutable (borra y recrea).
--
-- Se puede ejecutar en Supabase > SQL Editor o con cargar_datos_supabase.py.
-- =====================================================================

DROP TABLE IF EXISTS viajeros_trimestral, viajeros_anual, precios, ocupacion,
  eventos, empresas, demanda_mensual_ine, cuotas, corredores, fuentes CASCADE;

-- ---------------------------------------------------------------------
-- Dimensiones
-- ---------------------------------------------------------------------

-- En todas las tablas la columna id conserva el orden de las filas del CSV.
-- fecha_publicacion es texto porque hay valores como '2026' o 'mensual'
CREATE TABLE fuentes (
  id                 INT GENERATED ALWAYS AS IDENTITY UNIQUE,
  fuente_id          VARCHAR(20)  PRIMARY KEY,
  titulo             VARCHAR(255) NOT NULL,
  organismo          VARCHAR(100),
  fecha_publicacion  VARCHAR(20),
  url                VARCHAR(500)
);

CREATE TABLE corredores (
  id                                INT GENERATED ALWAYS AS IDENTITY UNIQUE,
  corredor_id                       VARCHAR(10)  PRIMARY KEY,
  nombre                            VARCHAR(100) NOT NULL,
  operadores                        VARCHAR(255),
  peso_canones_en_coste_pct         NUMERIC(6,2),
  resultado_billetes_vs_coste_2025  VARCHAR(255),
  cuota_tren_vs_avion_pct           NUMERIC(6,2),
  fuente_id                         VARCHAR(20) REFERENCES fuentes (fuente_id)
);

-- ---------------------------------------------------------------------
-- Hechos
-- viajeros_* usan corredor_id = 'TOTAL' y eventos usa valores compuestos
-- ('SEV;MAL'), por eso esas tablas no llevan FK a corredores.
-- ---------------------------------------------------------------------

CREATE TABLE cuotas (
  id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  periodo      VARCHAR(10)  NOT NULL,
  corredor_id  VARCHAR(10)  NOT NULL REFERENCES corredores (corredor_id),
  operador     VARCHAR(50)  NOT NULL,
  cuota_pct    NUMERIC(6,2),
  nota         VARCHAR(255),
  fuente_id    VARCHAR(20)  REFERENCES fuentes (fuente_id)
);
CREATE INDEX idx_cuotas_periodo ON cuotas (periodo);

CREATE TABLE demanda_mensual_ine (
  id                  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  periodo             VARCHAR(20)  NOT NULL,
  serie               VARCHAR(100) NOT NULL,
  viajeros_millones   NUMERIC(10,2),
  var_interanual_pct  NUMERIC(6,2),
  nota                VARCHAR(255),
  fuente_id           VARCHAR(20)  REFERENCES fuentes (fuente_id)
);

CREATE TABLE empresas (
  id          INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  empresa     VARCHAR(50)  NOT NULL,
  anio        SMALLINT     NOT NULL,
  indicador   VARCHAR(100) NOT NULL,
  valor       NUMERIC(12,2),
  unidad      VARCHAR(20),
  fuente_id   VARCHAR(20)  REFERENCES fuentes (fuente_id)
);
CREATE INDEX idx_empresas_empresa_anio ON empresas (empresa, anio);

CREATE TABLE eventos (
  id           INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  fecha        VARCHAR(20)  NOT NULL,
  corredor_id  VARCHAR(30)  NOT NULL,
  tipo         VARCHAR(30)  NOT NULL,
  evento       VARCHAR(500) NOT NULL,
  fuente_id    VARCHAR(20)  REFERENCES fuentes (fuente_id)
);

CREATE TABLE ocupacion (
  id             INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  periodo        VARCHAR(10)  NOT NULL,
  corredor_id    VARCHAR(10)  NOT NULL REFERENCES corredores (corredor_id),
  ocupacion_pct  NUMERIC(6,2),
  nota           VARCHAR(255),
  fuente_id      VARCHAR(20)  REFERENCES fuentes (fuente_id)
);

CREATE TABLE precios (
  id                  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  periodo             VARCHAR(10)   NOT NULL,
  corredor_id         VARCHAR(10)   NOT NULL REFERENCES corredores (corredor_id),
  precio_eur          NUMERIC(10,2),
  var_interanual_pct  NUMERIC(6,2),
  metrica             VARCHAR(50)   NOT NULL,
  fuente_id           VARCHAR(20)   REFERENCES fuentes (fuente_id)
);
CREATE INDEX idx_precios_periodo ON precios (periodo);

CREATE TABLE viajeros_anual (
  id                  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  anio                SMALLINT      NOT NULL,
  corredor_id         VARCHAR(10)   NOT NULL,
  viajeros_millones   NUMERIC(10,2),
  var_interanual_pct  NUMERIC(6,2),
  fuente_id           VARCHAR(20)   REFERENCES fuentes (fuente_id)
);

CREATE TABLE viajeros_trimestral (
  id                  INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  periodo             VARCHAR(10)   NOT NULL,
  corredor_id         VARCHAR(10)   NOT NULL,
  viajeros_millones   NUMERIC(10,2),
  var_interanual_pct  NUMERIC(6,2),
  tipo_dato           VARCHAR(20)   NOT NULL,
  nota                VARCHAR(255),
  fuente_id           VARCHAR(20)   REFERENCES fuentes (fuente_id)
);
CREATE INDEX idx_vtrim_periodo ON viajeros_trimestral (periodo);

-- ---------------------------------------------------------------------
-- Seguridad: Supabase expone public por su API REST. Se activa RLS sin
-- políticas, así la API anónima no ve nada; la conexión directa del
-- proyecto (usuario postgres) no se ve afectada.
-- ---------------------------------------------------------------------
ALTER TABLE fuentes             ENABLE ROW LEVEL SECURITY;
ALTER TABLE corredores          ENABLE ROW LEVEL SECURITY;
ALTER TABLE cuotas              ENABLE ROW LEVEL SECURITY;
ALTER TABLE demanda_mensual_ine ENABLE ROW LEVEL SECURITY;
ALTER TABLE empresas            ENABLE ROW LEVEL SECURITY;
ALTER TABLE eventos             ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocupacion           ENABLE ROW LEVEL SECURITY;
ALTER TABLE precios             ENABLE ROW LEVEL SECURITY;
ALTER TABLE viajeros_anual      ENABLE ROW LEVEL SECURITY;
ALTER TABLE viajeros_trimestral ENABLE ROW LEVEL SECURITY;
