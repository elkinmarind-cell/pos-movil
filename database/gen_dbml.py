"""Genera el diagrama de relaciones para dbdiagram.io desde el modelo general.

Dos salidas, de la misma fuente que ya produce el esquema SQL, el ORM y el
diagrama UML (`/home/claude/uml/modelo.py`). Que salgan de ahi es el punto: el
diagrama no puede contradecir a la base porque no es una copia hecha a mano.

    database/diagrama.dbml   -> se pega directo en dbdiagram.io (recomendado)
    database/diagrama.sql    -> DDL limpio, por si se prefiere "Import from SQL"

    python gen_dbml.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, "/home/claude/uml")
import modelo as M                                   # noqa: E402
from gen_esquema import (CHECKS, COMENTARIOS, UNICOS_COMPUESTOS,  # noqa: E402
                         por_defecto)

SALIDA = Path(__file__).parent / "database"

# PostgreSQL -> DBML. dbdiagram.io acepta cualquier texto como tipo, pero con
# los nombres que conoce dibuja el icono correcto y no inventa longitudes.
TIPOS = {
    "SERIAL": "serial",
    "BIGSERIAL": "bigserial",
    "INTEGER": "integer",
    "SMALLINT": "smallint",
    "BIGINT": "bigint",
    "BOOLEAN": "boolean",
    "TEXT": "text",
    "DATE": "date",
    "TIMESTAMPTZ": "timestamptz",
    "JSONB": "jsonb",
    "INET": "inet",
    "MACADDR": "macaddr",
}


def tipo_dbml(tipo: str) -> str:
    if tipo in TIPOS:
        return TIPOS[tipo]
    if tipo.startswith("VARCHAR") or tipo.startswith("NUMERIC"):
        return tipo.lower()
    return tipo            # los ENUM van con su nombre tal cual


def escapar(texto: str) -> str:
    """Las notas de una linea van entre comillas simples; hay que escaparlas."""
    return texto.replace("\\", "\\\\").replace("'", "\\'")


# ---------------------------------------------------------------------------
# 1. DBML
# ---------------------------------------------------------------------------

def dbml() -> str:
    L: list[str] = []
    a = L.append

    a("// ===========================================================================")
    a("// Sistema POS para la gestion y venta de dispositivos moviles")
    a("// Diagrama entidad-relacion para dbdiagram.io")
    a("//")
    a("// Generado desde el modelo general del proyecto. No editar a mano: se")
    a("// regenera con  python gen_dbml.py")
    a("//")
    a("// Como usarlo:  entrar a https://dbdiagram.io/d  -> borrar el ejemplo ->")
    a("// pegar todo este archivo.")
    a("// ===========================================================================")
    a("")
    a("Project pos_movil {")
    a("  database_type: 'PostgreSQL'")
    a("  Note: '''")
    a("    Sistema POS para dispositivos moviles — CUN")
    a("    Elkin Santiago Marin Duarte y Juan David Zabala Plata")
    a("")
    a(f"    {len(M.T)} tablas en {len(M.MODULOS)} modulos, {len(M.relaciones())} claves foraneas")
    a(f"    y {len(M.ENUMS)} tipos enumerados.")
    a("")
    a("    Dos estrategias de inventario conviven en el modelo:")
    a("      · equipos_imei  -> una fila por unidad fisica, identificada por IMEI")
    a("      · productos.stock_actual -> cantidad, para los accesorios")
    a("  '''")
    a("}")
    a("")

    # -- tipos enumerados ---------------------------------------------------
    a("// ---------------------------------------------------------------------------")
    a("// Tipos enumerados")
    a("// ---------------------------------------------------------------------------")
    a("")
    for nombre, valores in M.ENUMS:
        a(f"Enum {nombre} {{")
        for v in [x.strip() for x in valores.split(",")]:
            a(f"  {v}")
        a("}")
        a("")

    # -- tablas, agrupadas por modulo --------------------------------------
    for modulo, info in M.MODULOS.items():
        tablas = [n for n, t in M.T.items() if t["modulo"] == modulo]
        if not tablas:
            continue
        a("// ---------------------------------------------------------------------------")
        a(f"// {info['titulo']}")
        a("// ---------------------------------------------------------------------------")
        a("")
        for nombre in tablas:
            a(tabla_dbml(nombre, info["borde"]))

    # -- relaciones ---------------------------------------------------------
    a("// ---------------------------------------------------------------------------")
    a("// Relaciones")
    a("//   >  muchos a uno        -  uno a uno")
    a("// ---------------------------------------------------------------------------")
    a("")
    for r in M.relaciones():
        cols = M.T[r["origen"]]["cols"]
        flags = next(c[2] for c in cols if c[0] == r["fk"])
        simbolo = "-" if "UK" in flags else ">"
        # Misma regla que el esquema: una composicion arrastra a sus hijos, una
        # asociacion opcional se queda en NULL y el resto se bloquea.
        accion = ("cascade" if r["clase"] == "comp"
                  else ("set null" if "N" in flags else "restrict"))
        a(f"Ref: {r['origen']}.{r['fk']} {simbolo} {r['destino']}.id "
          f"[delete: {accion}]")
    a("")

    # -- grupos -------------------------------------------------------------
    a("// ---------------------------------------------------------------------------")
    a("// Modulos")
    a("// ---------------------------------------------------------------------------")
    a("")
    for modulo, info in M.MODULOS.items():
        tablas = [n for n, t in M.T.items() if t["modulo"] == modulo]
        if not tablas:
            continue
        a(f"TableGroup {modulo} {{")
        for t in tablas:
            a(f"  {t}")
        a("}")
        a("")

    return "\n".join(L)


def tabla_dbml(nombre: str, color: str) -> str:
    t = M.T[nombre]
    cols = t["cols"]
    pks = [c[0] for c in cols if "PK" in c[2]]
    compuesta = len(pks) > 1

    L = [f"Table {nombre} [headercolor: {color}] {{"]
    for col, tipo, flags, destino in cols:
        ajustes = []
        if "PK" in flags and not compuesta:
            ajustes.append("pk")
        # No se agrega `increment`: el tipo `serial` ya lo implica.
        if "N" in flags:
            ajustes.append("null")
        else:
            ajustes.append("not null")
        if "UK" in flags:
            ajustes.append("unique")
        defecto = por_defecto(nombre, col, tipo, flags)
        if defecto:
            # En DBML el valor por defecto va entre backticks cuando es una
            # expresion, y entre comillas cuando es un literal.
            if defecto.upper() in ("TRUE", "FALSE") or re.fullmatch(r"-?\d+", defecto):
                ajustes.append(f"default: {defecto.lower()}")
            elif defecto.startswith("'"):
                ajustes.append(f"default: {defecto}")
            else:
                ajustes.append(f"default: `{defecto}`")
        if destino:
            ajustes.append(f"note: 'FK a {destino[0]}'")

        L.append(f"  {col} {tipo_dbml(tipo)} [{', '.join(ajustes)}]")

    # Indices: clave primaria compuesta y claves unicas de varias columnas.
    indices = []
    if compuesta:
        indices.append(f"    ({', '.join(pks)}) [pk]")
    for _restriccion, columnas in UNICOS_COMPUESTOS.get(nombre, []):
        indices.append(f"    ({columnas}) [unique]")
    if indices:
        L.append("")
        L.append("  indexes {")
        L.extend(indices)
        L.append("  }")

    # Nota: para que las reglas no se pierdan al mirar solo el dibujo.
    notas = [M.MODULOS[t["modulo"]]["titulo"]]
    if nombre in COMENTARIOS:
        notas.append(COMENTARIOS[nombre])
    notas += list(t["restricciones"])
    notas += [f"CHECK {expr}" for _n, expr in CHECKS.get(nombre, [])]
    if notas:
        L.append("")
        L.append("  Note: '''")
        for n in notas:
            L.append(f"    {n}")
        L.append("  '''")

    L.append("}")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# 2. DDL limpio, por si se prefiere importar SQL
# ---------------------------------------------------------------------------

def ddl() -> str:
    """Solo tipos, tablas y claves. Sin funciones, triggers ni indices parciales.

    El esquema completo (`01_esquema.sql`) tiene objetos que los importadores de
    diagramas no entienden y que, al fallar, se saltan tablas enteras. Este
    archivo es el mismo modelo reducido a lo que un lector de diagramas necesita.
    """
    L: list[str] = []
    a = L.append
    a("-- ==========================================================================")
    a("-- Sistema POS para dispositivos moviles — estructura para diagramar")
    a("--")
    a("-- Solo tipos, tablas, claves primarias, foraneas y unicas. Es el mismo")
    a("-- modelo de 01_esquema.sql sin funciones, triggers ni indices parciales,")
    a("-- que son los objetos que hacen fallar a los importadores de diagramas.")
    a("--")
    a("-- Generado con  python gen_dbml.py")
    a("-- ==========================================================================")
    a("")
    for nombre, valores in M.ENUMS:
        lista = ", ".join(f"'{v.strip()}'" for v in valores.split(","))
        a(f"CREATE TYPE {nombre} AS ENUM ({lista});")
    a("")

    # Las tablas se emiten en orden topologico para que ninguna FK apunte a una
    # tabla que todavia no existe.
    for nombre in orden_topologico():
        t = M.T[nombre]
        cols = t["cols"]
        pks = [c[0] for c in cols if "PK" in c[2]]
        lineas = []
        for col, tipo, flags, destino in cols:
            pieza = f"    {col} {tipo}"
            if "PK" in flags and len(pks) == 1:
                pieza += " PRIMARY KEY"
            elif "N" not in flags:
                pieza += " NOT NULL"
            if "UK" in flags:
                pieza += " UNIQUE"
            defecto = por_defecto(nombre, col, tipo, flags)
            if defecto:
                pieza += f" DEFAULT {defecto}"
            if destino:
                accion = ("CASCADE" if destino[1] == "comp"
                          else ("SET NULL" if "N" in flags else "RESTRICT"))
                pieza += f" REFERENCES {destino[0]}(id) ON DELETE {accion}"
            lineas.append(pieza)
        if len(pks) > 1:
            lineas.append(f"    PRIMARY KEY ({', '.join(pks)})")
        for _restriccion, columnas in UNICOS_COMPUESTOS.get(nombre, []):
            lineas.append(f"    UNIQUE ({columnas})")

        a(f"-- {M.MODULOS[t['modulo']]['titulo']}")
        a(f"CREATE TABLE {nombre} (")
        a(",\n".join(lineas))
        a(");")
        a("")
    return "\n".join(L)


def orden_topologico() -> list[str]:
    """Padres antes que hijos. Una FK a la misma tabla no cuenta como espera."""
    pendientes = dict(M.T)
    listas: list[str] = []
    while pendientes:
        libres = [
            n for n, t in pendientes.items()
            if all(c[3] is None or c[3][0] == n or c[3][0] in listas for c in t["cols"])
        ]
        if not libres:
            raise RuntimeError(f"ciclo de claves foraneas entre {list(pendientes)}")
        for n in sorted(libres):
            listas.append(n)
            del pendientes[n]
    return listas


# ---------------------------------------------------------------------------
# 3. Verificacion
# ---------------------------------------------------------------------------

def verificar(texto_dbml: str) -> list[str]:
    """Revisa el DBML generado antes de entregarlo.

    No hay un analizador de DBML a mano, asi que se comprueba lo que de verdad
    rompe un diagrama: una referencia a una tabla que no existe, un tipo
    enumerado usado sin declarar, llaves descuadradas o una tabla que se quedo
    por fuera de su grupo.
    """
    problemas = []

    declaradas = set(re.findall(r"^Table (\w+) ", texto_dbml, re.M))
    faltan = set(M.T) - declaradas
    if faltan:
        problemas.append(f"tablas que no se emitieron: {sorted(faltan)}")

    enums = set(re.findall(r"^Enum (\w+) \{", texto_dbml, re.M))
    usados = {c[1] for t in M.T.values() for c in t["cols"] if c[1].islower()}
    if usados - enums:
        problemas.append(f"enums usados sin declarar: {sorted(usados - enums)}")

    # Toda referencia debe apuntar a una tabla declarada y a su columna id.
    for origen, col, destino in re.findall(
            r"^Ref: (\w+)\.(\w+) [->] (\w+)\.id ", texto_dbml, re.M):
        if origen not in declaradas:
            problemas.append(f"Ref desde tabla inexistente: {origen}")
        if destino not in declaradas:
            problemas.append(f"Ref hacia tabla inexistente: {destino}")
        if col not in {c[0] for c in M.T[origen]["cols"]}:
            problemas.append(f"Ref desde columna inexistente: {origen}.{col}")

    n_refs = len(re.findall(r"^Ref: ", texto_dbml, re.M))
    if n_refs != len(M.relaciones()):
        problemas.append(f"se emitieron {n_refs} relaciones y el modelo tiene "
                         f"{len(M.relaciones())}")

    agrupadas = set()
    for bloque in re.findall(r"^TableGroup \w+ \{\n(.*?)\n\}", texto_dbml, re.M | re.S):
        agrupadas |= {x.strip() for x in bloque.splitlines() if x.strip()}
    if agrupadas != set(M.T):
        problemas.append(f"tablas fuera de su grupo: {sorted(set(M.T) - agrupadas)}")

    # Llaves equilibradas, ignorando las que van dentro de una nota.
    sin_notas = re.sub(r"'''.*?'''", "", texto_dbml, flags=re.S)
    if sin_notas.count("{") != sin_notas.count("}"):
        problemas.append(f"llaves descuadradas: {sin_notas.count('{')} abren y "
                         f"{sin_notas.count('}')} cierran")

    return problemas


if __name__ == "__main__":
    SALIDA.mkdir(exist_ok=True)

    texto = dbml()
    problemas = verificar(texto)
    if problemas:
        print("NO se escribio nada. Problemas encontrados:")
        for p in problemas:
            print(f"  · {p}")
        sys.exit(1)

    (SALIDA / "diagrama.dbml").write_text(texto, encoding="utf-8")
    (SALIDA / "diagrama.sql").write_text(ddl(), encoding="utf-8")

    print(f"database/diagrama.dbml  {len(texto.splitlines()):>4} lineas")
    print(f"database/diagrama.sql   {len(ddl().splitlines()):>4} lineas")
    print(f"  {len(M.T)} tablas · {len(M.relaciones())} relaciones · "
          f"{len(M.ENUMS)} enums · {len(M.MODULOS)} modulos")
    print("  verificacion: sin problemas")
