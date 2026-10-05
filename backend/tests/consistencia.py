"""Verifica que el modelo ORM y el esquema real de PostgreSQL digan lo mismo.

Es la red de seguridad entre database/01_esquema.sql y app/models.py: si alguien
cambia una columna en un lado y no en el otro, esta prueba lo dice.
"""
import sys

from sqlalchemy import inspect

from app.database import Base, engine
from app import models  # noqa: F401  (registra las clases en el metadata)

EQUIVALENTES = {
    "VARCHAR": {"VARCHAR", "CHARACTER VARYING"}, "CHAR": {"CHAR", "CHARACTER", "BPCHAR"},
    "INTEGER": {"INTEGER", "SERIAL", "INT4"}, "BIGINT": {"BIGINT", "BIGSERIAL", "INT8"},
    "SMALLINT": {"SMALLINT", "INT2"}, "TIMESTAMP": {"TIMESTAMP", "TIMESTAMPTZ", "DATETIME"},
    "NUMERIC": {"NUMERIC", "DECIMAL"}, "BOOLEAN": {"BOOLEAN", "BOOL"}, "TEXT": {"TEXT"},
    "DATE": {"DATE"}, "JSONB": {"JSONB"}, "INET": {"INET"}, "MACADDR": {"MACADDR"},
}

def familia(nombre: str) -> str:
    nombre = nombre.upper().split("(")[0].strip()
    for fam, miembros in EQUIVALENTES.items():
        if nombre in miembros:
            return fam
    return nombre

def main() -> int:
    insp = inspect(engine)
    reales = set(insp.get_table_names(schema="public"))
    orm = set(Base.metadata.tables)
    fallos = []

    faltan = orm - reales
    sobran = reales - orm
    if faltan:
        fallos.append(f"tablas del ORM que no existen en la base: {sorted(faltan)}")
    if sobran:
        fallos.append(f"tablas de la base que el ORM no mapea: {sorted(sobran)}")

    for tabla in sorted(orm & reales):
        cols_bd = {c["name"]: c for c in insp.get_columns(tabla, schema="public")}
        cols_orm = {c.name: c for c in Base.metadata.tables[tabla].columns}
        for falta in set(cols_orm) - set(cols_bd):
            fallos.append(f"{tabla}.{falta}: esta en el ORM y no en la base")
        for falta in set(cols_bd) - set(cols_orm):
            fallos.append(f"{tabla}.{falta}: esta en la base y no en el ORM")
        for nombre in set(cols_bd) & set(cols_orm):
            bd, o = cols_bd[nombre], cols_orm[nombre]
            f_bd, f_orm = familia(str(bd["type"])), familia(str(o.type))
            if f_bd != f_orm and not (f_bd == f_orm.lower()):
                fallos.append(f"{tabla}.{nombre}: tipo {bd['type']} en la base vs {o.type} en el ORM")
            if bool(bd["nullable"]) != bool(o.nullable):
                fallos.append(f"{tabla}.{nombre}: nulabilidad {bd['nullable']} en la base vs {o.nullable} en el ORM")

    # las claves foraneas deben existir en ambos lados
    for tabla in sorted(orm & reales):
        fk_bd = {(tuple(f["constrained_columns"]), f["referred_table"]) for f in insp.get_foreign_keys(tabla, schema="public")}
        fk_orm = {((c.name,), list(c.foreign_keys)[0].column.table.name)
                  for c in Base.metadata.tables[tabla].columns if c.foreign_keys}
        for falta in fk_orm - fk_bd:
            fallos.append(f"{tabla}: FK {falta} esta en el ORM y no en la base")
        for falta in fk_bd - fk_orm:
            fallos.append(f"{tabla}: FK {falta} esta en la base y no en el ORM")

    print(f"tablas comparadas: {len(orm & reales)} | columnas en el ORM: "
          f"{sum(len(t.columns) for t in Base.metadata.tables.values())}")
    if fallos:
        print(f"\n{len(fallos)} DIFERENCIAS entre el ORM y la base:")
        for f in fallos[:40]:
            print("  -", f)
        return 1
    print("El modelo ORM y el esquema de PostgreSQL coinciden exactamente.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
