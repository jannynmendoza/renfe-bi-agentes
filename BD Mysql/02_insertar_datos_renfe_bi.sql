-- Generado por cargar_datos_mysql.py a partir de renfe-bi-agentes/data/*.csv
SET NAMES utf8mb4;
USE renfe_bi;
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE viajeros_trimestral;
TRUNCATE TABLE viajeros_anual;
TRUNCATE TABLE precios;
TRUNCATE TABLE ocupacion;
TRUNCATE TABLE eventos;
TRUNCATE TABLE empresas;
TRUNCATE TABLE demanda_mensual_ine;
TRUNCATE TABLE cuotas;
TRUNCATE TABLE corredores;
TRUNCATE TABLE fuentes;
SET FOREIGN_KEY_CHECKS = 1;

-- fuentes: 14 filas
INSERT INTO fuentes (fuente_id, titulo, organismo, fecha_publicacion, url) VALUES
  ('CNMC_1T25', 'Nota de prensa: informe trimestral ferroviario 1T 2025 (corredor sur)', 'CNMC', '2025-06-25', 'https://cnmc.es/prensa/alta-velocidad-corredor-sur-20250625'),
  ('CNMC_3T25', 'Nota de prensa: los precios caen más de un 30% en el corredor sur (3T 2025, INF/DTSP/042/25)', 'CNMC', '2025-12-09', 'https://www.cnmc.es/los-precios-caen-mas-de-un-30-en-el-corredor-sur-gracias-la-competencia-417601'),
  ('CNMC_4T25', 'Nota de prensa: informe trimestral transporte ferroviario 4T 2025', 'CNMC', '2026-03-25', 'https://cnmc.es/prensa/informe-trimestral-transporte-ferroviario-20260325'),
  ('CNMC_1T26', 'Nota de prensa: informe trimestral transporte ferroviario 1T 2026', 'CNMC', '2026-06-29', 'https://cnmc.es/prensa/informe-trimestral-transporte-ferroviario-20260629'),
  ('CNMC_2T26', 'Nota de prensa: informe trimestral transporte ferroviario 2T 2026 (INF/DTSP/038/26)', 'CNMC', '2026-09-22', 'https://cnmc.es/prensa/informe-trimestral-transporte-ferroviario-20260922'),
  ('CNMC_ANUAL25', 'Informe anual del sector ferroviario 2025 (vía El Español, 17/07/2026)', 'CNMC / El Español', '2026-07-17', 'https://www.elespanol.com/invertia/observatorios/movilidad/20260717/alta-velocidad-duplica-numero-viajeros-rebaja-precios-liberalizacion/1003744325128_0.html'),
  ('CNMC_BAL24', 'Nota de prensa: balance de la liberalización 2024', 'CNMC', '2025-09-22', 'https://www.cnmc.es/sites/default/files/editor_contenidos/Notas%20de%20prensa/2025/20250922_NP_INF_Balance_Liberalizaci%C3%B3n_2024.pdf'),
  ('RENFE_RES25', 'Renfe logra 60 millones de beneficio en 2025', 'Demócrata', '2026', 'https://www.democrata.es/economia/renfe-logra-60-millones-de-beneficio-en-2025-impulsada-por-un-19-mas-de-ingresos-en-billetes/'),
  ('IRYO_RES25', 'Iryo se acerca a los números verdes tras los resultados de 2025', 'Merca2', '2026-04-21', 'https://www.merca2.es/2026/04/21/iryo-resultados-trenes-2370772/'),
  ('OUIGO_RES25', 'Ouigo y Renfe salían de los números rojos antes del accidente en Adamuz', 'Merca2', '2026-03-04', 'https://www.merca2.es/2026/03/04/ouigo-renfe-numeros-rojos-2357156/'),
  ('MD_PUNT', 'Renfe pierde el 10,8% de viajeros en media distancia (CNMC / portal de Renfe)', 'Moncloa.com', '2026-07-21', 'https://www.moncloa.com/2026/07/21/renfe-pierde-viajeros-media-distancia-cnmc-3403274/'),
  ('INE_AV26', 'La alta velocidad no remonta tras Adamuz: -20% de viajeros en cuatro meses (datos INE)', 'WWWhatsnew', '2026-06-18', 'https://wwwhatsnew.com/2026/06/18/alta-velocidad-espana-caida-20-por-ciento-viajeros-adamuz-2026/'),
  ('INE_49359', 'INE tabla 49359 - Total de viajeros por tipo, medio de transporte y distancia (API JSON)', 'INE', 'mensual', 'https://servicios.ine.es/wstempus/js/es/DATOS_TABLA/49359?tip=AM'),
  ('EXPRETIO26', 'Renfe renews partnership with Expretio (Appia revenue management)', 'Railway-News', '2026-06-03', 'https://railway-news.com/renfe-renews-partnership-with-expretio-strengthening-rail-revenue-management-innovation/');

-- corredores: 5 filas
INSERT INTO corredores (corredor_id, nombre, operadores, peso_canones_en_coste_pct, resultado_billetes_vs_coste_2025, cuota_tren_vs_avion_pct, fuente_id) VALUES
  ('BCN', 'Madrid-Barcelona', 'Renfe (AVE/Avlo), Iryo, Ouigo', 46, 'ingresos superan costes en 6% (único corredor positivo)', 83.1, 'CNMC_ANUAL25'),
  ('VLC', 'Madrid-Valencia', 'Renfe (AVE/Avlo), Iryo, Ouigo', 30, 'pérdidas', NULL, 'CNMC_ANUAL25'),
  ('ALI', 'Madrid-Alicante', 'Renfe (AVE/Avlo), Iryo (solo fines de semana fuera de verano), Ouigo', 30, 'pérdidas', NULL, 'CNMC_ANUAL25'),
  ('SEV', 'Madrid-Sevilla', 'Renfe (AVE/Avlo), Iryo, Ouigo (desde enero 2025)', 38, 'pérdidas', NULL, 'CNMC_ANUAL25'),
  ('MAL', 'Madrid-Málaga/Granada', 'Renfe (AVE/Avlo), Iryo, Ouigo (desde enero 2025)', 38, 'pérdidas', NULL, 'CNMC_ANUAL25');

-- cuotas: 18 filas
INSERT INTO cuotas (periodo, corredor_id, operador, cuota_pct, nota, fuente_id) VALUES
  ('2025T1', 'SEV', 'Renfe', 64, NULL, 'CNMC_1T25'),
  ('2025T1', 'SEV', 'Iryo', 24, NULL, 'CNMC_1T25'),
  ('2025T1', 'SEV', 'Ouigo', 11, NULL, 'CNMC_1T25'),
  ('2025T1', 'MAL', 'Renfe', 70, NULL, 'CNMC_1T25'),
  ('2025T1', 'MAL', 'Iryo', 21, NULL, 'CNMC_1T25'),
  ('2025T1', 'MAL', 'Ouigo', 9, NULL, 'CNMC_1T25'),
  ('2025T3', 'VLC', 'Renfe', 50, NULL, 'CNMC_3T25'),
  ('2025T3', 'BCN', 'Renfe', 62, 'aprox.; ~62% en todos salvo VLC', 'CNMC_3T25'),
  ('2025T3', 'SEV', 'Renfe', 62, 'aprox.; ~62% en todos salvo VLC', 'CNMC_3T25'),
  ('2025T3', 'MAL', 'Renfe', 62, 'aprox.; Ouigo +4 pp, Iryo +2 pp vs 2T', 'CNMC_3T25'),
  ('2025T3', 'ALI', 'Renfe', 62, 'aprox.; Iryo +4 pp vs 2T', 'CNMC_3T25'),
  ('2025T4', 'BCN', 'Renfe', 56, '-6 pp interanual', 'CNMC_4T25'),
  ('2025T4', 'BCN', 'Ouigo', 19, '+4 pp', 'CNMC_4T25'),
  ('2025T4', 'BCN', 'Iryo', 24, '+2 pp', 'CNMC_4T25'),
  ('2025T4', 'VLC', 'Renfe', 51, NULL, 'CNMC_4T25'),
  ('2025T4', 'SEV', 'Renfe', 60, '>60% (-4 pp); Ouigo +6 pp, Iryo -2 pp', 'CNMC_4T25'),
  ('2025T4', 'ALI', 'Renfe', 60, '>60%; Ouigo +6 pp', 'CNMC_4T25'),
  ('2025T4', 'MAL', 'Renfe', 60, '>60%', 'CNMC_4T25');

-- demanda_mensual_ine: 5 filas
INSERT INTO demanda_mensual_ine (periodo, serie, viajeros_millones, var_interanual_pct, nota, fuente_id) VALUES
  ('2026-02', 'Alta velocidad (AVE+Avlo+Iryo+Ouigo)', 2.16, -32.1, 'peor mes tras Adamuz', 'INE_AV26'),
  ('2026-03', 'Alta velocidad (AVE+Avlo+Iryo+Ouigo)', NULL, -17.7, NULL, 'INE_AV26'),
  ('2026-04', 'Alta velocidad (AVE+Avlo+Iryo+Ouigo)', NULL, -15.0, NULL, 'INE_AV26'),
  ('2026-01..04', 'Alta velocidad (AVE+Avlo+Iryo+Ouigo)', 11.06, -19.6, '13,75 M en ene-abr 2025', 'INE_AV26'),
  ('2026-02', 'Autobús larga distancia', NULL, 15.1, 'trasvase modal durante el corte', 'INE_AV26');

-- empresas: 20 filas
INSERT INTO empresas (empresa, anio, indicador, valor, unidad, fuente_id) VALUES
  ('Renfe', 2025, 'beneficio_neto_consolidado', 60.2, 'M EUR', 'RENFE_RES25'),
  ('Renfe', 2024, 'beneficio_neto_consolidado', -2.9, 'M EUR', 'RENFE_RES25'),
  ('Renfe', 2025, 'ingresos_billetes_total', 2000, 'M EUR', 'RENFE_RES25'),
  ('Renfe', 2025, 'ingresos_billetes_AV_y_larga_distancia', 1469, 'M EUR', 'RENFE_RES25'),
  ('Renfe', 2025, 'var_ingresos_AV_y_larga_distancia', 7.5, '%', 'RENFE_RES25'),
  ('Renfe', 2025, 'ingresos_billetes_OSP', 532, 'M EUR', 'RENFE_RES25'),
  ('Renfe', 2025, 'viajeros_totales', 531.4, 'M', 'RENFE_RES25'),
  ('Renfe', 2025, 'viajes_AV_y_larga_distancia', 37, 'M', 'OUIGO_RES25'),
  ('Renfe', 2025, 'liquidez', 1059.5, 'M EUR', 'RENFE_RES25'),
  ('Renfe', 2025, 'puntualidad_media_distancia', 59.4, '%', 'MD_PUNT'),
  ('Renfe', 2026, 'larga_distancia_trenes_con_retraso_ene_may', 28.8, '%', 'MD_PUNT'),
  ('Renfe', 2026, 'larga_distancia_retraso_mas_30min_ene_may', 11.7, '%', 'MD_PUNT'),
  ('Renfe', 2024, 'cuota_mercado_corredores_liberalizados', 72, '%', 'CNMC_BAL24'),
  ('Iryo', 2025, 'ingresos_espana', 320, 'M EUR', 'IRYO_RES25'),
  ('Iryo', 2025, 'perdidas', 5, 'M EUR', 'IRYO_RES25'),
  ('Iryo', 2024, 'perdidas', 31.6, 'M EUR', 'IRYO_RES25'),
  ('Ouigo', 2024, 'perdidas_acumuladas_hasta_2024', 191, 'M EUR', 'OUIGO_RES25'),
  ('Ouigo', 2025, 'var_viajeros', 44.3, '%', 'OUIGO_RES25'),
  ('Sector', 2024, 'puntualidad_rutas_competencia_menos_15min', 94, '%', 'CNMC_BAL24'),
  ('Sector', 2024, 'resultado_empresas_ferroviarias', -99.5, 'M EUR', 'CNMC_BAL24');

-- eventos: 8 filas
INSERT INTO eventos (fecha, corredor_id, tipo, evento, fuente_id) VALUES
  ('2025-01', 'SEV;MAL', 'competencia', 'Entrada de Ouigo en el corredor sur (enero 2025): precios -12% en 2025', 'CNMC_ANUAL25'),
  ('2025-06-30', 'TOTAL', 'regulacion', 'Fin de la gratuidad para viajeros recurrentes de Cercanías y Media Distancia', 'CNMC_2T26'),
  ('2025', 'BCN', 'competencia', 'Ouigo reduce frecuencias en Madrid-Barcelona; el corredor cae -1,7% en 2025', 'MD_PUNT'),
  ('2026-01-18', 'SEV;MAL', 'incidente', 'Accidente ferroviario de Adamuz (Córdoba): corte del corredor Madrid-Andalucía durante semanas', 'INE_AV26'),
  ('2026-02', 'SEV', 'operacion', 'Restablecimiento parcial de Madrid-Sevilla a mediados de febrero', 'INE_AV26'),
  ('2026-04-30', 'MAL', 'operacion', 'Reapertura Madrid-Málaga/Granada en vía única tras el desprendimiento de Álora', 'CNMC_2T26'),
  ('2026T2', 'BCN', 'operacion', 'Limitaciones de velocidad en Madrid-Barcelona alargan el tiempo de viaje', 'CNMC_2T26'),
  ('2026-06-03', 'TOTAL', 'tecnologia', 'Renfe renueva Appia (Expretio) para revenue management y migra a Sqills', 'EXPRETIO26');

-- ocupacion: 5 filas
INSERT INTO ocupacion (periodo, corredor_id, ocupacion_pct, nota, fuente_id) VALUES
  ('2025T1', 'BCN', 78, 'viajeros.km / plazas.km', 'CNMC_1T25'),
  ('2025T1', 'VLC', 65, 'corredores a Levante', 'CNMC_1T25'),
  ('2025T1', 'ALI', 65, 'corredores a Levante', 'CNMC_1T25'),
  ('2025T1', 'SEV', 71, NULL, 'CNMC_1T25'),
  ('2025T1', 'MAL', 67, 'empeoró al aumentar la oferta', 'CNMC_1T25');

-- precios: 30 filas
INSERT INTO precios (periodo, corredor_id, precio_eur, var_interanual_pct, metrica, fuente_id) VALUES
  ('2025T1', 'BCN', 50, 0, 'precio_web_trayecto', 'CNMC_1T25'),
  ('2025T1', 'SEV', 39, -18, 'precio_web_trayecto', 'CNMC_1T25'),
  ('2025T1', 'MAL', 37, -17, 'precio_web_trayecto', 'CNMC_1T25'),
  ('2025T1', 'ALI', 29, -19, 'precio_web_trayecto', 'CNMC_1T25'),
  ('2025T1', 'VLC', 24, -10, 'precio_web_trayecto', 'CNMC_1T25'),
  ('2025T3', 'BCN', 64, NULL, 'precio_web_trayecto', 'CNMC_3T25'),
  ('2025T3', 'BCN', NULL, 14, 'ingreso_viajero_km', 'CNMC_3T25'),
  ('2025T3', 'MAL', 42, NULL, 'precio_web_trayecto', 'CNMC_3T25'),
  ('2025T3', 'SEV', 40, NULL, 'precio_web_trayecto', 'CNMC_3T25'),
  ('2025T3', 'ALI', 38, NULL, 'precio_web_trayecto', 'CNMC_3T25'),
  ('2025T3', 'VLC', 31, NULL, 'precio_web_trayecto', 'CNMC_3T25'),
  ('2025T4', 'BCN', NULL, 36, 'ingreso_viajero_km', 'CNMC_4T25'),
  ('2025T4', 'VLC', NULL, 23, 'ingreso_viajero_km', 'CNMC_4T25'),
  ('2025T4', 'SEV', NULL, -10, 'ingreso_viajero_km', 'CNMC_4T25'),
  ('2025T4', 'MAL', NULL, -10, 'ingreso_viajero_km', 'CNMC_4T25'),
  ('2025', 'BCN', 52.89, 15.2, 'ingreso_medio_trayecto', 'CNMC_ANUAL25'),
  ('2025', 'VLC', 27.04, NULL, 'ingreso_medio_trayecto', 'CNMC_ANUAL25'),
  ('2025', 'SEV', 38.41, -12, 'ingreso_medio_trayecto', 'CNMC_ANUAL25'),
  ('2025', 'MAL', 37.61, -12, 'ingreso_medio_trayecto', 'CNMC_ANUAL25'),
  ('2025', 'ALI', 31.34, NULL, 'ingreso_medio_trayecto', 'CNMC_ANUAL25'),
  ('2026T1', 'BCN', 46, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_1T26'),
  ('2026T1', 'SEV', 33, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_1T26'),
  ('2026T1', 'MAL', 32, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_1T26'),
  ('2026T1', 'ALI', 27, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_1T26'),
  ('2026T1', 'VLC', 26, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_1T26'),
  ('2026T2', 'BCN', 56, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_2T26'),
  ('2026T2', 'SEV', 44, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_2T26'),
  ('2026T2', 'MAL', 40, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_2T26'),
  ('2026T2', 'ALI', 32, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_2T26'),
  ('2026T2', 'VLC', 31, NULL, 'ingreso_medio_trayecto_sin_iva', 'CNMC_2T26');

-- viajeros_anual: 6 filas
INSERT INTO viajeros_anual (anio, corredor_id, viajeros_millones, var_interanual_pct, fuente_id) VALUES
  (2025, 'TOTAL', 44.5, 12, 'CNMC_ANUAL25'),
  (2025, 'BCN', 14.4, -1.7, 'CNMC_ANUAL25'),
  (2025, 'VLC', 6.2, NULL, 'CNMC_ANUAL25'),
  (2025, 'SEV', 5.9, 18.7, 'CNMC_ANUAL25'),
  (2025, 'MAL', 5.8, 14.1, 'CNMC_ANUAL25'),
  (2025, 'ALI', 4.5, NULL, 'CNMC_ANUAL25');

-- viajeros_trimestral: 30 filas
INSERT INTO viajeros_trimestral (periodo, corredor_id, viajeros_millones, var_interanual_pct, tipo_dato, nota, fuente_id) VALUES
  ('2025T1', 'TOTAL', 10.2, 19, 'publicado', NULL, 'CNMC_1T25'),
  ('2025T1', 'SEV', 1.4, 23, 'publicado', NULL, 'CNMC_1T25'),
  ('2025T1', 'MAL', 1.2, 14, 'publicado', NULL, 'CNMC_1T25'),
  ('2025T1', 'ALI', NULL, 17, 'publicado', NULL, 'CNMC_1T25'),
  ('2025T1', 'BCN', NULL, 4, 'publicado', NULL, 'CNMC_1T25'),
  ('2025T1', 'VLC', NULL, 3, 'publicado', NULL, 'CNMC_1T25'),
  ('2025T2', 'TOTAL', 11.8, NULL, 'derivado', '2T26 = 10,6 M y 1,2 M menos que 2T25', 'CNMC_2T26'),
  ('2025T2', 'BCN', 3.85, NULL, 'derivado', '2T26 tuvo >0,5 M menos (-13%)', 'CNMC_2T26'),
  ('2025T2', 'MAL', 1.67, NULL, 'derivado', '2T26 perdió ~0,5 M (-30%)', 'CNMC_2T26'),
  ('2025T3', 'TOTAL', 11.8, 10.4, 'publicado', NULL, 'CNMC_3T25'),
  ('2025T3', 'MAL', 1.6, 17.7, 'publicado', NULL, 'CNMC_3T25'),
  ('2025T3', 'SEV', 1.4, 13.2, 'publicado', NULL, 'CNMC_3T25'),
  ('2025T3', 'ALI', 1.3, 8.9, 'publicado', NULL, 'CNMC_3T25'),
  ('2025T3', 'VLC', 1.7, 4.7, 'publicado', NULL, 'CNMC_3T25'),
  ('2025T3', 'BCN', NULL, -0.3, 'publicado', NULL, 'CNMC_3T25'),
  ('2025T4', 'TOTAL', 10.6, 5.3, 'publicado', NULL, 'CNMC_4T25'),
  ('2025T4', 'BCN', 3.3, -13, 'publicado', 'plazas ofertadas -4,4%', 'CNMC_4T25'),
  ('2025T4', 'VLC', 1.5, 26, 'publicado', NULL, 'CNMC_4T25'),
  ('2025T4', 'SEV', 1.6, 18.1, 'publicado', NULL, 'CNMC_4T25'),
  ('2025T4', 'MAL', 1.4, 9.2, 'publicado', NULL, 'CNMC_4T25'),
  ('2025T4', 'ALI', 1.0, 0.4, 'publicado', NULL, 'CNMC_4T25'),
  ('2026T1', 'TOTAL', 8.05, -21, 'publicado', 'Adamuz (18/01/2026), cortes de vía y limitaciones de velocidad', 'CNMC_1T26'),
  ('2026T1', 'MAL', 0.47, -61, 'derivado', '1,2 M (1T25) x (1-0,61); corredor cerrado por Álora hasta 30/04', 'CNMC_1T26'),
  ('2026T1', 'SEV', 1.02, -27, 'derivado', '1,4 M (1T25) x (1-0,27)', 'CNMC_1T26'),
  ('2026T1', 'BCN', NULL, -17, 'publicado', NULL, 'CNMC_1T26'),
  ('2026T1', 'VLC', NULL, -8, 'publicado', NULL, 'CNMC_1T26'),
  ('2026T1', 'ALI', NULL, -6, 'publicado', NULL, 'CNMC_1T26'),
  ('2026T2', 'TOTAL', 10.6, -10, 'publicado', NULL, 'CNMC_2T26'),
  ('2026T2', 'MAL', 1.17, -30, 'derivado', 'reabierto 30/04 en vía única; plazas -30%', 'CNMC_2T26'),
  ('2026T2', 'BCN', 3.35, -13, 'derivado', 'limitaciones de velocidad', 'CNMC_2T26');
