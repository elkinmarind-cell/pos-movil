"""Tkinter + consulta a la base de datos.

Una ventana real: busca productos en PostgreSQL y los muestra en una tabla.
Es el mismo problema del sistema completo reducido a lo esencial — ventana,
consulta parametrizada y resultado en pantalla — para que se vea la mecanica
sin el ruido de ocho modulos.

    python 02_tkinter_consulta.py
"""

import os
import tkinter as tk
from tkinter import ttk

import psycopg

# La contrasena no se escribe en el codigo: se lee del entorno. Si no esta, se
# pide al arrancar.
CONEXION = os.environ.get(
    "POS_BD",
    "postgresql://postgres:{clave}@localhost:5432/pos_movil",
)

# Consulta parametrizada: el texto buscado viaja como parametro (%s), nunca
# pegado al SQL. Es la unica forma de que un nombre con comillas no pueda
# convertirse en una inyeccion SQL.
CONSULTA = """
    SELECT p.sku,
           p.nombre,
           m.nombre                AS marca,
           p.precio_venta,
           CASE WHEN p.requiere_imei
                THEN (SELECT COUNT(*) FROM equipos_imei e
                       WHERE e.producto_id = p.id AND e.estado = 'DISPONIBLE')
                ELSE p.stock_actual
           END                     AS disponibles
      FROM productos p
      LEFT JOIN marcas m ON m.id = p.marca_id
     WHERE p.activo
       AND (%(texto)s = '' OR p.nombre ILIKE %(patron)s OR p.sku ILIKE %(patron)s)
     ORDER BY p.nombre
     LIMIT 50
"""


class Ventana(tk.Tk):
    def __init__(self, conexion: str):
        super().__init__()
        self.conexion = conexion
        self.title("POS Movil — Consulta de productos")
        self.geometry("860x480")
        self.configure(bg="#F1F5F9")

        tk.Label(self, text="Productos en inventario", font=("Segoe UI", 15, "bold"),
                 bg="#F1F5F9", fg="#0F172A").pack(anchor="w", padx=18, pady=(16, 2))
        tk.Label(self, text="Consulta en vivo contra PostgreSQL",
                 font=("Segoe UI", 9), bg="#F1F5F9", fg="#64748B"
                 ).pack(anchor="w", padx=18)

        barra = tk.Frame(self, bg="#F1F5F9")
        barra.pack(fill="x", padx=18, pady=12)
        self.busqueda = tk.Entry(barra, font=("Segoe UI", 11), relief="solid", bd=1)
        self.busqueda.pack(side="left", fill="x", expand=True, ipady=5)
        self.busqueda.bind("<Return>", lambda _e: self.buscar())
        tk.Button(barra, text="Buscar", font=("Segoe UI", 10, "bold"), bg="#1D4ED8",
                  fg="white", relief="flat", padx=20, cursor="hand2",
                  command=self.buscar).pack(side="left", padx=(8, 0))

        columnas = ("sku", "nombre", "marca", "precio", "disponibles")
        self.tabla = ttk.Treeview(self, columns=columnas, show="headings", height=14)
        for columna, titulo, ancho in [
            ("sku", "SKU", 110), ("nombre", "Producto", 330), ("marca", "Marca", 130),
            ("precio", "Precio", 130), ("disponibles", "Disponibles", 100),
        ]:
            self.tabla.heading(columna, text=titulo)
            self.tabla.column(columna, width=ancho,
                              anchor="e" if columna in ("precio", "disponibles") else "w")
        self.tabla.pack(fill="both", expand=True, padx=18)

        self.estado = tk.Label(self, text="", font=("Segoe UI", 9), bg="#F1F5F9",
                               fg="#475569", anchor="w")
        self.estado.pack(fill="x", padx=18, pady=10)

        self.buscar()

    def buscar(self) -> None:
        texto = self.busqueda.get().strip()
        self.tabla.delete(*self.tabla.get_children())
        try:
            # `with` cierra la conexion y el cursor pase lo que pase, incluso si
            # la consulta lanza una excepcion a la mitad.
            with psycopg.connect(self.conexion) as cn, cn.cursor() as cur:
                cur.execute(CONSULTA, {"texto": texto, "patron": f"%{texto}%"})
                filas = cur.fetchall()
        except psycopg.Error as e:
            self.estado.config(text=f"Error de base de datos: {e}", fg="#B91C1C")
            return

        for sku, nombre, marca, precio, disponibles in filas:
            self.tabla.insert("", "end", values=(
                sku, nombre, marca or "—",
                f"$ {int(precio):,}".replace(",", "."),
                disponibles,
            ))
        self.estado.config(text=f"{len(filas)} productos encontrados", fg="#475569")


def main() -> None:
    conexion = CONEXION
    if "{clave}" in conexion:
        clave = input("Contrasena de PostgreSQL (usuario postgres): ")
        conexion = conexion.format(clave=clave)
    Ventana(conexion).mainloop()


if __name__ == "__main__":
    main()
