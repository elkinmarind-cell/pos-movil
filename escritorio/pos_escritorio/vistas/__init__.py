"""Registro de vistas.

Un solo lugar define que modulos existen, en que orden aparecen en el menu y en
que grupo. La aplicacion no sabe nada mas: recorre esta lista, descarta lo que
el rol no puede ver y arma el menu con lo que queda.
"""

from __future__ import annotations

from .base import Contexto, Vista
from .caja import Caja
from .clientes import Clientes
from .garantias import Garantias
from .inventario import Inventario
from .punto_venta import PuntoVenta
from .tablero import Tablero
from .usuarios import Usuarios
from .ventas import Ventas

# (clave, grupo, clase)
REGISTRO: list[tuple[str, str, type[Vista]]] = [
    ("tablero", "Operacion", Tablero),
    ("punto-venta", "Operacion", PuntoVenta),
    ("ventas", "Operacion", Ventas),
    ("caja", "Operacion", Caja),
    ("inventario", "Inventario", Inventario),
    ("clientes", "Clientes", Clientes),
    ("garantias", "Clientes", Garantias),
    ("usuarios", "Direccion", Usuarios),
]

__all__ = ["REGISTRO", "Contexto", "Vista", "Tablero", "PuntoVenta", "Ventas",
           "Caja", "Inventario", "Clientes", "Garantias", "Usuarios"]
