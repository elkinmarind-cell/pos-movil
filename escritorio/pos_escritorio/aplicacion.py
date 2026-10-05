"""Armazon de la aplicacion: ingreso, menu lateral y cambio de vista.

La clase `Aplicacion` es el contexto que reciben las vistas. Hace tres cosas:
guarda la sesion, dibuja el menu con los permisos del usuario que entro y cambia
el contenido del area derecha cuando se elige otro modulo.
"""

from __future__ import annotations

import flet as ft

from . import tema as T
from . import ui
from .api import Api, ErrorApi
from .vistas import REGISTRO, Vista

TITULO = "POS Movil · Gestion y venta de dispositivos moviles"
GRUPOS = ["Operacion", "Inventario", "Clientes", "Direccion"]


class Aplicacion:
    """Contexto de la aplicacion. Lo que las vistas llaman `ctx`."""

    def __init__(self, page: ft.Page, servidor: str = "http://127.0.0.1:8000/api"):
        self.page = page
        self.api = Api(servidor)
        self.servidor = servidor
        self.vistas: dict[str, Vista] = {}
        self.actual: str = "tablero"
        self.contenido = ft.Container(expand=True)

        page.title = TITULO
        page.theme = T.tema()
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = T.FONDO
        page.padding = 0
        page.window.width = 1360
        page.window.height = 840
        page.window.min_width = 1040
        page.window.min_height = 680
        page.window.title_bar_hidden = False

    # -- utilidades que usan las vistas -------------------------------------

    def aviso(self, texto: str, tono: str = "acento") -> None:
        """Mensaje efimero al pie de la ventana."""
        color, fondo = T.TONOS[tono]
        self.page.show_dialog(
            ft.SnackBar(
                content=ft.Text(texto, size=13, color=color),
                bgcolor=fondo,
                behavior=ft.SnackBarBehavior.FLOATING,
                shape=ft.RoundedRectangleBorder(radius=T.RADIO_SM),
                duration=4500,
            )
        )

    def abrir(self, dialogo: ft.AlertDialog) -> None:
        self.page.show_dialog(dialogo)

    def cerrar(self, _=None) -> None:
        self.page.pop_dialog()

    def refrescar(self) -> None:
        """Vuelve a construir la vista actual conservando su estado interno."""
        self.ir_a(self.actual, forzar=True)

    def ir_a(self, clave: str, forzar: bool = False) -> None:
        if clave not in self.vistas:
            return
        self.actual = clave
        if not forzar and hasattr(self, "menu"):
            self._marcar_menu()
        self.contenido.content = ft.Container(
            content=self.vistas[clave].construir(),
            padding=ft.Padding.symmetric(vertical=18, horizontal=22),
            expand=True,
        )
        if hasattr(self, "menu"):
            self._marcar_menu()
        self.page.update()

    # -- ingreso ------------------------------------------------------------

    def mostrar_ingreso(self, mensaje: str | None = None) -> None:
        usuario = ui.campo("Usuario", icono=ft.Icons.PERSON_OUTLINE, foco=True)
        clave = ui.campo("Contrasena", clave=True, icono=ft.Icons.LOCK_OUTLINE)
        error = ft.Text("", size=12, color=T.PELIGRO)
        boton = ui.boton("Entrar", None, ft.Icons.ARROW_FORWARD, "acento")

        def entrar(_e=None):
            error.value = ""
            boton.disabled = True
            self.page.update()
            try:
                self.api.entrar((usuario.value or "").strip(), clave.value or "")
            except ErrorApi as ex:
                error.value = ex.mensaje
                boton.disabled = False
                self.page.update()
                return
            self.mostrar_principal()

        boton.on_click = entrar
        usuario.on_submit = entrar
        clave.on_submit = entrar

        estado_servidor = self._estado_servidor()

        tarjeta = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.POINT_OF_SALE,
                                                color=ft.Colors.WHITE, size=22),
                                bgcolor=T.ACENTO, border_radius=T.RADIO_SM, padding=10,
                            ),
                            ft.Column(
                                [ui.titulo("POS Movil", 19),
                                 ui.subtitulo("Gestion y venta de dispositivos moviles")],
                                spacing=1,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=1, bgcolor=T.BORDE),
                    usuario,
                    clave,
                    error,
                    boton,
                    estado_servidor,
                ],
                spacing=14,
                tight=True,
            ),
            width=400,
            bgcolor=T.PANEL,
            border=ft.Border.all(1, T.BORDE),
            border_radius=T.RADIO,
            padding=26,
        )

        hijos: list[ft.Control] = [tarjeta]
        if mensaje:
            hijos.insert(0, ft.Container(content=ui.aviso(mensaje, "exito"), width=400))

        self.page.controls = [
            ft.Container(
                content=ft.Column(hijos, spacing=14,
                                  horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.Alignment.CENTER,
                bgcolor=T.FONDO,
                expand=True,
            )
        ]
        self.page.update()

    def _estado_servidor(self) -> ft.Control:
        """Dice de entrada si el backend responde; evita el clasico 'no pasa nada'."""
        try:
            salud = self.api.salud()
        except ErrorApi as e:
            return ui.aviso(e.mensaje, "peligro")
        return ui.aviso(
            f"Servidor conectado · PostgreSQL {str(salud.get('postgresql', '')).split(' ')[0]}"
            f" · {salud.get('tablas', 0)} tablas",
            "exito",
        )

    # -- ventana principal --------------------------------------------------

    def mostrar_principal(self) -> None:
        self.vistas = {}
        for clave, _grupo, clase in REGISTRO:
            if not clase.permisos or self.api.puede(*clase.permisos):
                self.vistas[clave] = clase(self)
        if not self.vistas:
            self.mostrar_ingreso("Tu rol no tiene ningun modulo habilitado.")
            return
        self.actual = "tablero" if "tablero" in self.vistas else next(iter(self.vistas))

        self.menu = ft.Column(spacing=2)
        self._marcar_menu()

        lateral = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.POINT_OF_SALE,
                                                color=ft.Colors.WHITE, size=18),
                                bgcolor=T.ACENTO, border_radius=6, padding=8,
                            ),
                            ft.Column([ft.Text("POS Movil", size=14,
                                               weight=ft.FontWeight.W_700, color=T.TEXTO),
                                       ft.Text("Dispositivos moviles", size=10,
                                               color=T.TEXTO_TENUE)], spacing=0),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=1, bgcolor=T.BORDE),
                    ft.Container(content=self.menu, expand=True),
                    ft.Container(height=1, bgcolor=T.BORDE),
                    self._pie_usuario(),
                ],
                spacing=14,
                expand=True,
            ),
            width=236,
            bgcolor=T.PANEL,
            border=ft.Border.only(right=ft.BorderSide(1, T.BORDE)),
            padding=ft.Padding.symmetric(vertical=16, horizontal=14),
        )

        self.page.controls = [
            ft.Row([lateral, self.contenido], spacing=0, expand=True)
        ]
        self.ir_a(self.actual, forzar=True)

    def _marcar_menu(self) -> None:
        """Dibuja el menu agrupado, resaltando el modulo abierto."""
        self.menu.controls = []
        for grupo in GRUPOS:
            claves = [c for c, g, _ in REGISTRO if g == grupo and c in self.vistas]
            if not claves:
                continue
            self.menu.controls.append(
                ft.Container(content=ui.rotulo(grupo),
                             padding=ft.Padding.only(left=8, top=10, bottom=2))
            )
            for clave in claves:
                vista = self.vistas[clave]
                activo = clave == self.actual
                self.menu.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Icon(vista.icono, size=17,
                                        color=T.ACENTO if activo else T.TEXTO_TENUE),
                                ft.Text(vista.titulo, size=13,
                                        weight=ft.FontWeight.W_600 if activo
                                        else ft.FontWeight.W_500,
                                        color=T.ACENTO if activo else T.TEXTO_MEDIO),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                        bgcolor=T.ACENTO_SUAVE if activo else None,
                        border_radius=T.RADIO_SM,
                        padding=ft.Padding.symmetric(vertical=9, horizontal=10),
                        on_click=(lambda e, k=clave: self.ir_a(k)),
                    )
                )

    def _pie_usuario(self) -> ft.Control:
        iniciales = "".join(p[0] for p in self.api.nombre.split()[:2]).upper() or "?"
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Text(iniciales, size=12,
                                            weight=ft.FontWeight.W_700,
                                            color=T.ACENTO),
                            bgcolor=T.ACENTO_SUAVE, border_radius=99,
                            width=34, height=34, alignment=ft.Alignment.CENTER,
                        ),
                        ft.Column(
                            [
                                ft.Text(self.api.nombre, size=12,
                                        weight=ft.FontWeight.W_600, color=T.TEXTO,
                                        max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(self.api.rol.title(), size=10,
                                        color=T.TEXTO_TENUE),
                            ],
                            spacing=0, expand=True,
                        ),
                    ],
                    spacing=10,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ui.boton("Cerrar sesion", self._salir, ft.Icons.LOGOUT, "neutro"),
            ],
            spacing=10,
        )

    def _salir(self, _=None) -> None:
        self.api.salir()
        self.vistas = {}
        if hasattr(self, "menu"):
            del self.menu
        self.mostrar_ingreso("Sesion cerrada.")
