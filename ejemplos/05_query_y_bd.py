"""Query y base de datos — conexion directa a PostgreSQL desde Python.

Sin interfaz. Solo el acceso a datos, que es lo que pide el item "Query y BD" de
la rubrica. Recorre de lo mas simple a lo que de verdad usa el sistema:

  1. conectar y leer la version del motor
  2. una consulta sencilla
  3. una consulta parametrizada (la unica forma segura de meter un dato)
  4. una consulta con JOIN y agregacion
  5. leer una vista del sistema
  6. llamar una funcion PL/pgSQL
  7. una transaccion: insertar y deshacer

    set POS_BD=postgresql://postgres:TU_CLAVE@localhost:5432/pos_movil
    python 05_query_y_bd.py
"""

from __future__ import annotations

import os
import sys

import psycopg
from psycopg.rows import dict_row


def conexion() -> str:
    cadena = os.environ.get("POS_BD")
    if cadena:
        return cadena
    clave = input("Contrasena de PostgreSQL (usuario postgres): ")
    return f"postgresql://postgres:{clave}@localhost:5432/pos_movil"


def titulo(n: int, texto: str) -> None:
    print(f"\n{'=' * 70}\n{n}. {texto}\n{'=' * 70}")


def pesos(valor) -> str:
    return f"$ {int(valor or 0):,}".replace(",", ".")


def main() -> None:
    try:
        # `row_factory=dict_row` hace que cada fila llegue como diccionario:
        # fila["nombre"] en vez de fila[2]. Un cambio en el SELECT deja de
        # romper el codigo que lee los resultados.
        cn = psycopg.connect(conexion(), row_factory=dict_row)
    except psycopg.OperationalError as e:
        print(f"\nNo se pudo conectar: {e}")
        print("Revisa que PostgreSQL este encendido y que la clave sea la correcta.")
        sys.exit(1)

    with cn:
        # -- 1 ---------------------------------------------------------------
        titulo(1, "Conexion")
        with cn.cursor() as cur:
            cur.execute("SELECT version() AS v, current_database() AS bd")
            fila = cur.fetchone()
            print(f"Base:  {fila['bd']}")
            print(f"Motor: {fila['v'].split(',')[0]}")

        # -- 2 ---------------------------------------------------------------
        titulo(2, "Consulta sencilla: cuantas filas hay en cada tabla principal")
        with cn.cursor() as cur:
            for tabla in ["productos", "equipos_imei", "clientes", "ventas",
                          "venta_detalles", "garantias", "usuarios"]:
                # El nombre de la tabla no puede ir como parametro (%s solo sirve
                # para valores), por eso se toma de una lista fija del codigo y
                # nunca de algo que escriba el usuario.
                cur.execute(f"SELECT COUNT(*) AS n FROM {tabla}")
                print(f"  {tabla:<16} {cur.fetchone()['n']:>5}")

        # -- 3 ---------------------------------------------------------------
        titulo(3, "Consulta parametrizada: buscar un producto")
        texto = "iphone"
        with cn.cursor() as cur:
            # El valor viaja aparte del SQL. Aunque `texto` trajera comillas o un
            # "; DROP TABLE", PostgreSQL lo trata como texto, no como codigo.
            cur.execute(
                """SELECT sku, nombre, precio_venta
                     FROM productos
                    WHERE nombre ILIKE %s AND activo
                    ORDER BY nombre""",
                (f"%{texto}%",),
            )
            for p in cur.fetchall():
                print(f"  {p['sku']:<10} {p['nombre']:<38} {pesos(p['precio_venta'])}")

        # -- 4 ---------------------------------------------------------------
        titulo(4, "JOIN y agregacion: lo mas vendido")
        with cn.cursor() as cur:
            cur.execute("""
                SELECT p.nombre,
                       SUM(d.cantidad)                      AS unidades,
                       SUM(d.total_linea)                   AS vendido
                  FROM venta_detalles d
                  JOIN productos p ON p.id = d.producto_id
                  JOIN ventas    v ON v.id = d.venta_id
                 WHERE v.estado = 'COMPLETADA'
                 GROUP BY p.nombre
                 HAVING SUM(d.cantidad) > 0
                 ORDER BY unidades DESC, vendido DESC
                 LIMIT 5
            """)
            for f in cur.fetchall():
                print(f"  {f['nombre']:<40} {f['unidades']:>3} u.  {pesos(f['vendido'])}")

        # -- 5 ---------------------------------------------------------------
        titulo(5, "Leer una vista: alertas de stock")
        with cn.cursor() as cur:
            cur.execute("SELECT * FROM v_alertas_stock ORDER BY disponibles")
            filas = cur.fetchall()
            if not filas:
                print("  Ningun producto esta por debajo del minimo.")
            for f in filas:
                print(f"  {f['sku']:<10} {f['nombre']:<38} "
                      f"hay {f['disponibles']}, minimo {f['stock_minimo']}")

        # -- 6 ---------------------------------------------------------------
        titulo(6, "Llamar una funcion de PostgreSQL: validacion de IMEI (Luhn)")
        with cn.cursor() as cur:
            for imei in ["356789012345045", "356789012345046", "123"]:
                cur.execute("SELECT fn_imei_valido(%s) AS ok", (imei,))
                ok = cur.fetchone()["ok"]
                print(f"  {imei:<18} {'valido' if ok else 'invalido'}")
        print("\n  La misma funcion respalda un CHECK de la tabla equipos_imei:")
        print("  un IMEI con digito verificador incorrecto no entra ni por SQL directo.")

        # -- 7 ---------------------------------------------------------------
        titulo(7, "Transaccion: insertar y deshacer")
        with cn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM clientes")
            antes = cur.fetchone()["n"]
            cur.execute("""
                INSERT INTO clientes (tipo_documento, numero_documento, nombres,
                                      apellidos, ciudad, autoriza_datos)
                VALUES ('CC', '999999999', 'Prueba', 'Transaccion', 'Bogota', TRUE)
                RETURNING id
            """)
            nuevo = cur.fetchone()["id"]
            cur.execute("SELECT COUNT(*) AS n FROM clientes")
            print(f"  Dentro de la transaccion: {antes} -> {cur.fetchone()['n']} "
                  f"(cliente id {nuevo})")
            # ROLLBACK deshace todo lo hecho desde el inicio de la transaccion.
            # Es lo que protege una venta: si falla a la mitad, no queda media
            # factura ni un IMEI marcado como vendido sin su linea.
            cn.rollback()
        with cn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM clientes")
            print(f"  Despues del ROLLBACK:     {cur.fetchone()['n']} "
                  f"(el insert se deshizo)")

    print("\nConexion cerrada.\n")


if __name__ == "__main__":
    main()
