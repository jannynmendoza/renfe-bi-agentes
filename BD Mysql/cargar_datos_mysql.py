"""
Carga los CSV de renfe-bi-agentes/data en MySQL/MariaDB local (XAMPP).

1. Genera 02_insertar_datos_renfe_bi.sql a partir de los CSV (valores vacios -> NULL).
2. Ejecuta 01_crear_esquema_renfe_bi.sql y 02_insertar_datos_renfe_bi.sql con mysql.exe.
3. Muestra el recuento de filas por tabla.

Uso:
    python cargar_datos_mysql.py               # genera y carga
    python cargar_datos_mysql.py --solo-generar   # solo genera el .sql (para importarlo en phpMyAdmin)

Variables opcionales: MYSQL_BIN, MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD
"""
import csv
import os
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DATA_DIR = BASE.parent / "Renfe-bi-agentes" / "renfe-bi-agentes" / "data"
SQL_ESQUEMA = BASE / "01_crear_esquema_renfe_bi.sql"
SQL_DATOS = BASE / "02_insertar_datos_renfe_bi.sql"
DB = "renfe_bi"

MYSQL_BIN = os.getenv("MYSQL_BIN", r"C:\xampp\mysql\bin\mysql.exe")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")

# Orden de carga: primero las tablas referenciadas por claves foraneas
TABLAS = [
    "fuentes",
    "corredores",
    "cuotas",
    "demanda_mensual_ine",
    "empresas",
    "eventos",
    "ocupacion",
    "precios",
    "viajeros_anual",
    "viajeros_trimestral",
]

# Columnas de texto que pueden parecer numeros y deben ir entre comillas
COLUMNAS_TEXTO = {"periodo", "fecha", "fecha_publicacion", "corredor_id", "fuente_id"}

NUMERO = re.compile(r"^-?\d+(\.\d+)?$")


def literal_sql(columna, valor):
    valor = valor.strip()
    if valor == "":
        return "NULL"
    if columna not in COLUMNAS_TEXTO and NUMERO.match(valor):
        return valor
    return "'" + valor.replace("\\", "\\\\").replace("'", "''") + "'"


def generar_inserts():
    lineas = [
        "-- Generado por cargar_datos_mysql.py a partir de renfe-bi-agentes/data/*.csv",
        "SET NAMES utf8mb4;",
        f"USE {DB};",
        "SET FOREIGN_KEY_CHECKS = 0;",
    ]
    lineas += [f"TRUNCATE TABLE {t};" for t in reversed(TABLAS)]
    lineas.append("SET FOREIGN_KEY_CHECKS = 1;")

    for tabla in TABLAS:
        with open(DATA_DIR / f"{tabla}.csv", encoding="utf-8-sig", newline="") as f:
            lector = csv.reader(f)
            columnas = next(lector)
            filas = [fila for fila in lector if any(c.strip() for c in fila)]
        valores = [
            "  (" + ", ".join(literal_sql(c, v) for c, v in zip(columnas, fila)) + ")"
            for fila in filas
        ]
        lineas.append("")
        lineas.append(f"-- {tabla}: {len(filas)} filas")
        lineas.append(f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES")
        lineas.append(",\n".join(valores) + ";")

    SQL_DATOS.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"Generado {SQL_DATOS.name}")


def ejecutar_mysql(sql_bytes, *extra):
    cmd = [MYSQL_BIN, "-h", MYSQL_HOST, "-P", MYSQL_PORT, "-u", MYSQL_USER,
           "--default-character-set=utf8mb4", *extra]
    if MYSQL_PASSWORD:
        cmd.insert(1, f"-p{MYSQL_PASSWORD}")
    res = subprocess.run(cmd, input=sql_bytes, capture_output=True)
    if res.returncode != 0:
        sys.exit(res.stderr.decode("utf-8", "replace"))
    return res.stdout.decode("utf-8", "replace")


def main():
    generar_inserts()
    if "--solo-generar" in sys.argv:
        return

    ejecutar_mysql(SQL_ESQUEMA.read_bytes())
    print(f"Esquema creado en la base de datos '{DB}'")
    ejecutar_mysql(SQL_DATOS.read_bytes())
    print("Datos insertados\n")

    recuento = " UNION ALL ".join(f"SELECT '{t}' AS tabla, COUNT(*) AS filas FROM {t}" for t in TABLAS)
    print(ejecutar_mysql(f"{recuento};".encode(), "-t", DB))


if __name__ == "__main__":
    main()
