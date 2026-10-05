"""Contrato comun de las vistas.

Cada modulo del sistema es una clase `Vista`. La aplicacion la instancia con un
contexto (la sesion de API y utilidades de interfaz) y le pide `construir()`,
que devuelve un unico control de Flet. Nada mas.

Ese contrato es lo que permite probar las vistas sin abrir una ventana: en la
prueba se pasa un contexto con una pagina simulada y se comprueba que el arbol
de controles se arma sin excepciones y con los datos reales de PostgreSQL.
"""

from __future__ import annotations

from typing import Any, Callable, Protocol

import flet as ft

from .. import ui
from ..api import Api, ErrorApi


class Contexto(Protocol):
    """Lo que la aplicacion le presta a cada vista."""

    api: Api
    page: ft.Page

    def aviso(self, texto: str, tono: str = "acento") -> None: ...
    def abrir(self, dialogo: ft.AlertDialog) -> None: ...
    def cerrar(self, _=None) -> None: ...
    def refrescar(self) -> None: ...
    def ir_a(self, clave: str) -> None: ...


class Vista:
    """Base de todas las vistas."""

    titulo: str = ""
    icono: str = ft.Icons.CIRCLE
    permisos: tuple[str, ...] = ()

    def __init__(self, ctx: Contexto):
        self.ctx = ctx
        self.api = ctx.api

    # -- a implementar ------------------------------------------------------

    def construir(self) -> ft.Control:  # pragma: no cover - lo hacen las hijas
        raise NotImplementedError

    # -- utilidades para las hijas -----------------------------------------

    def encabezado(self, descripcion: str,
                   acciones: list[ft.Control] | None = None) -> ft.Control:
        """Franja superior de la vista: titulo, una linea de contexto y acciones."""
        return ft.Row(
            [
                ft.Column([ui.titulo(self.titulo), ui.subtitulo(descripcion)],
                          spacing=2, expand=True),
                ft.Row(acciones or [], spacing=8),
            ],
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

    def seguro(self, accion: Callable[[], Any], exito: str | None = None) -> Any:
        """Ejecuta una accion contra la API y convierte el fallo en un aviso.

        Sin esto, cada boton tendria su propio `try/except` y un error de red
        dejaria la ventana en silencio, sin decirle nada a quien la usa.
        """
        try:
            resultado = accion()
        except ErrorApi as e:
            self.ctx.aviso(e.mensaje, "peligro")
            return None
        if exito:
            self.ctx.aviso(exito, "exito")
        self.ctx.refrescar()
        return resultado

    def pedir(self, accion: Callable[[], Any], por_defecto: Any = None) -> Any:
        """Lee datos para dibujar. Si falla, avisa y devuelve el valor neutro."""
        try:
            return accion()
        except ErrorApi as e:
            self.ctx.aviso(e.mensaje, "peligro")
            return por_defecto

    def dialogo(self, titulo: str, contenido: ft.Control,
                confirmar: str, al_confirmar: Callable,
                tono: str = "acento", ancho: int = 460) -> ft.AlertDialog:
        """Ventana modal con el mismo marco en todo el sistema."""
        return ft.AlertDialog(
            modal=True,
            title=ui.titulo(titulo, 16),
            content=ft.Container(content=contenido, width=ancho),
            actions=[
                ui.boton("Cancelar", self.ctx.cerrar, tono="neutro"),
                ui.boton(confirmar, al_confirmar, tono=tono),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
