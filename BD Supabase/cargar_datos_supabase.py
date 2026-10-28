"""
Carga los CSV de Renfe-bi-agentes/renfe-bi-agentes/data en Supabase (PostgreSQL).

1. Genera 02_insertar_datos_supabase.sql a partir de los CSV (valores vacios -> NULL).
2. Ejecuta 01_crear_esquema_supabase.sql y 02_insertar_datos_supabase.sql en Supabase.
3. Muestra el recuento de filas por tabla y lo compara con los CSV.

La cadena de conexion se lee de SUPABASE_DB_URL (variable de entorno o el .env del
proyecto renfe-bi-agentes). En Supabase: Project > Connect > Session pooler, p. ej.
    postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres

Uso:
    python cargar_datos_supabase.py                 # genera y carga
    python cargar_datos_supabase.py --solo-generar  # solo genera el .sql (para el SQL Editor)

Requiere: pip install "psycopg[binary]" python-dotenv
"""
import csv
import os
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROYECTO = BASE.parent / "Renfe-bi-agentes" / "renfe-bi-agentes"
DATA_DIR = PROYECTO / "data"
SQL_ESQUEMA = BASE / "01_crear_esquema_supabase.sql"
SQL_DATOS = BASE / "02_insertar_datos_supabase.sql"

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
    return "'" + valor.replace("'", "''") + "'"


def leer_csv(tabla):
    with open(DATA_DIR / f"{tabla}.csv", encoding="utf-8-sig", newline="") as f:
        lector = csv.reader(f)
        columnas = next(lector)
        filas = [fila for fila in lector if any(c.strip() for c in fila)]
    return columnas, filas


def generar_inserts():
    lineas = [
        "-- Generado por cargar_datos_supabase.py a partir de data/*.csv",
        "-- Ejecutar despues de 01_crear_esquema_supabase.sql",
        "TRUNCATE " + ", ".join(reversed(TABLAS)) + " RESTART IDENTITY CASCADE;",
    ]
    for tabla in TABLAS:
        columnas, filas = leer_csv(tabla)
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


def url_conexion():
    try:
        from dotenv import load_dotenv
        load_dotenv(PROYECTO / ".env")
    except ImportError:
        pass
    url = os.getenv("SUPABASE_DB_URL")
    if not url:
        sys.exit("Falta SUPABASE_DB_URL (define la variable o añadela al .env del proyecto).")
    return url


def main():
    generar_inserts()
    if "--solo-generar" in sys.argv:
        return

    import psycopg

    with psycopg.connect(url_conexion(), connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute(SQL_ESQUEMA.read_text(encoding="utf-8"))
            print("Esquema creado en Supabase")
            cur.execute(SQL_DATOS.read_text(encoding="utf-8"))
            print("Datos insertados\n")

            ok = True
            print(f"{'tabla':<22}{'Supabase':>9}{'CSV':>6}")
            for tabla in TABLAS:
                cur.execute(f"SELECT COUNT(*) FROM {tabla}")
                en_bd = cur.fetchone()[0]
                en_csv = len(leer_csv(tabla)[1])
                ok &= en_bd == en_csv
                print(f"{tabla:<22}{en_bd:>9}{en_csv:>6}{'' if en_bd == en_csv else '  <- NO COINCIDE'}")
    print("\nCarga completa y verificada." if ok else "\nHay diferencias entre Supabase y los CSV.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
