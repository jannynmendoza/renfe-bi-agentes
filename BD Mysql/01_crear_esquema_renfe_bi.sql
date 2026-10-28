-- =====================================================================
-- RENFE BI - Esquema MySQL/MariaDB
-- Crea la base de datos renfe_bi y las tablas que reflejan los CSV de
-- renfe-bi-agentes/data. Es re-ejecutable (borra y recrea las tablas).
-- =====================================================================

SET NAMES utf8mb4;

CREATE DATABASE IF NOT EXISTS renfe_bi
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE renfe_bi;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS viajeros_trimestral;
DROP TABLE IF EXISTS viajeros_anual;
DROP TABLE IF EXISTS precios;
DROP TABLE IF EXISTS ocupacion;
DROP TABLE IF EXISTS eventos;
DROP TABLE IF EXISTS empresas;
DROP TABLE IF EXISTS demanda_mensual_ine;
DROP TABLE IF EXISTS cuotas;
DROP TABLE IF EXISTS corredores;
DROP TABLE IF EXISTS fuentes;
SET FOREIGN_KEY_CHECKS = 1;

-- ---------------------------------------------------------------------
-- Dimensiones
-- ---------------------------------------------------------------------

-- fecha_publicacion es texto porque hay valores como '2026' o 'mensual'
CREATE TABLE fuentes (
  fuente_id          VARCHAR(20)  NOT NULL,
  titulo             VARCHAR(255) NOT NULL,
  organismo          VARCHAR(100) NULL,
  fecha_publicacion  VARCHAR(20)  NULL,
  url                VARCHAR(500) NULL,
  PRIMARY KEY (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE corredores (
  corredor_id                       VARCHAR(10)   NOT NULL,
  nombre                            VARCHAR(100)  NOT NULL,
  operadores                        VARCHAR(255)  NULL,
  peso_canones_en_coste_pct         DECIMAL(6,2)  NULL,
  resultado_billetes_vs_coste_2025  VARCHAR(255)  NULL,
  cuota_tren_vs_avion_pct           DECIMAL(6,2)  NULL,
  fuente_id                         VARCHAR(20)   NULL,
  PRIMARY KEY (corredor_id),
  CONSTRAINT fk_corredores_fuente FOREIGN KEY (fuente_id) REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------
-- Hechos
-- Nota: viajeros_* usan corredor_id = 'TOTAL' y eventos usa valores
-- compuestos ('SEV;MAL'), por eso esas tablas no llevan FK a corredores.
-- ---------------------------------------------------------------------

CREATE TABLE cuotas (
  id           INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  periodo      VARCHAR(10)   NOT NULL,
  corredor_id  VARCHAR(10)   NOT NULL,
  operador     VARCHAR(50)   NOT NULL,
  cuota_pct    DECIMAL(6,2)  NULL,
  nota         VARCHAR(255)  NULL,
  fuente_id    VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  KEY idx_cuotas_periodo (periodo),
  CONSTRAINT fk_cuotas_corredor FOREIGN KEY (corredor_id) REFERENCES corredores (corredor_id),
  CONSTRAINT fk_cuotas_fuente   FOREIGN KEY (fuente_id)   REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE demanda_mensual_ine (
  id                  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  periodo             VARCHAR(20)   NOT NULL,
  serie               VARCHAR(100)  NOT NULL,
  viajeros_millones   DECIMAL(10,2) NULL,
  var_interanual_pct  DECIMAL(6,2)  NULL,
  nota                VARCHAR(255)  NULL,
  fuente_id           VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_demanda_fuente FOREIGN KEY (fuente_id) REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE empresas (
  id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  empresa     VARCHAR(50)   NOT NULL,
  anio        SMALLINT      NOT NULL,
  indicador   VARCHAR(100)  NOT NULL,
  valor       DECIMAL(12,2) NULL,
  unidad      VARCHAR(20)   NULL,
  fuente_id   VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  KEY idx_empresas_empresa_anio (empresa, anio),
  CONSTRAINT fk_empresas_fuente FOREIGN KEY (fuente_id) REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE eventos (
  id           INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  fecha        VARCHAR(20)   NOT NULL,
  corredor_id  VARCHAR(30)   NOT NULL,
  tipo         VARCHAR(30)   NOT NULL,
  evento       VARCHAR(500)  NOT NULL,
  fuente_id    VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_eventos_fuente FOREIGN KEY (fuente_id) REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ocupacion (
  id             INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  periodo        VARCHAR(10)   NOT NULL,
  corredor_id    VARCHAR(10)   NOT NULL,
  ocupacion_pct  DECIMAL(6,2)  NULL,
  nota           VARCHAR(255)  NULL,
  fuente_id      VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_ocupacion_corredor FOREIGN KEY (corredor_id) REFERENCES corredores (corredor_id),
  CONSTRAINT fk_ocupacion_fuente   FOREIGN KEY (fuente_id)   REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE precios (
  id                  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  periodo             VARCHAR(10)   NOT NULL,
  corredor_id         VARCHAR(10)   NOT NULL,
  precio_eur          DECIMAL(10,2) NULL,
  var_interanual_pct  DECIMAL(6,2)  NULL,
  metrica             VARCHAR(50)   NOT NULL,
  fuente_id           VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  KEY idx_precios_periodo (periodo),
  CONSTRAINT fk_precios_corredor FOREIGN KEY (corredor_id) REFERENCES corredores (corredor_id),
  CONSTRAINT fk_precios_fuente   FOREIGN KEY (fuente_id)   REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE viajeros_anual (
  id                  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  anio                SMALLINT      NOT NULL,
  corredor_id         VARCHAR(10)   NOT NULL,
  viajeros_millones   DECIMAL(10,2) NULL,
  var_interanual_pct  DECIMAL(6,2)  NULL,
  fuente_id           VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  CONSTRAINT fk_vanual_fuente FOREIGN KEY (fuente_id) REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE viajeros_trimestral (
  id                  INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  periodo             VARCHAR(10)   NOT NULL,
  corredor_id         VARCHAR(10)   NOT NULL,
  viajeros_millones   DECIMAL(10,2) NULL,
  var_interanual_pct  DECIMAL(6,2)  NULL,
  tipo_dato           VARCHAR(20)   NOT NULL,
  nota                VARCHAR(255)  NULL,
  fuente_id           VARCHAR(20)   NULL,
  PRIMARY KEY (id),
  KEY idx_vtrim_periodo (periodo),
  CONSTRAINT fk_vtrim_fuente FOREIGN KEY (fuente_id) REFERENCES fuentes (fuente_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
