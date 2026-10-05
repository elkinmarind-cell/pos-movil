"""Punto de entrada de la aplicacion de escritorio del POS Movil.

Se ejecuta de dos maneras:

    python app.py                 (durante el desarrollo)
    POS_SERVIDOR=... python app.py (apuntando a otro servidor)

y es el archivo que recibe `flet pack` para producir `POS-Movil.exe`.

La direccion del backend se toma de la variable de entorno POS_SERVIDOR para que
el mismo ejecutable sirva en el mostrador (apuntando al equipo donde corre la
API) sin tener que recompilarlo.
"""

import os

import flet as ft

from pos_escritorio.aplicacion import Aplicacion

SERVIDOR = os.environ.get("POS_SERVIDOR", "http://127.0.0.1:8000/api")


def main(page: ft.Page) -> None:
    Aplicacion(page, SERVIDOR).mostrar_ingreso()


if __name__ == "__main__":
    ft.run(main)
