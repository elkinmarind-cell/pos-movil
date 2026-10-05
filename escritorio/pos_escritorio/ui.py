"""Piezas visuales reutilizables.

Si un panel, una tabla o una insignia de estado se dibujan igual en ocho vistas,
se definen una sola vez aqui. Es el equivalente de `frontend/src/componentes/ui.jsx`
en la version web.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Iterable, Sequence

import flet as ft

from . import tema as T

# ---------------------------------------------------------------------------
# Formato
# ---------------------------------------------------------------------------


def pesos(valor: Any, decimales: bool = False) -> str:
    """Formatea un valor como moneda colombiana: `$ 2.999.900`.

    El backend serializa los `NUMERIC` como texto para no perder precision, por
    eso se recibe `str` y se convierte con `Decimal` y no con `float`.
    """
    if valor is None or valor == "":
        return "—"
    try:
        n = Decimal(str(valor))
    except (InvalidOperation, ValueError):
        return str(valor)
    entero, resto = divmod(abs(n).quantize(Decimal("0.01")), 1)
    miles = f"{int(entero):,}".replace(",", ".")
    signo = "-" if n < 0 else ""
    if decimales:
        return f"{signo}$ {miles},{int(resto * 100):02d}"
    return f"{signo}$ {miles}"


def numero(valor: Any) -> str:
    """Entero con separador de miles."""
    try:
        return f"{int(Decimal(str(valor))):,}".replace(",", ".")
    except (InvalidOperation, ValueError, TypeError):
        return str(valor if valor is not None else "—")


def _parsear(iso: str | None) -> datetime | None:
    if not iso:
        return None
    try:
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None


def fecha(iso: str | None) -> str:
    d = _parsear(iso)
    return d.strftime("%d/%m/%Y") if d else "—"


def fecha_hora(iso: str | None) -> str:
    d = _parsear(iso)
    return d.strftime("%d/%m/%Y %I:%M %p").lower() if d else "—"


def nombre_cliente(cliente: dict | None) -> str:
    if not cliente:
        return "Consumidor final"
    return f"{cliente.get('nombres', '')} {cliente.get('apellidos') or ''}".strip()


# ---------------------------------------------------------------------------
# Texto
# ---------------------------------------------------------------------------


def titulo(texto: str, tamano: int = 20) -> ft.Text:
    return ft.Text(texto, size=tamano, weight=ft.FontWeight.W_600, color=T.TEXTO)


def subtitulo(texto: str) -> ft.Text:
    return ft.Text(texto, size=13, color=T.TEXTO_TENUE)


def rotulo(texto: str) -> ft.Text:
    """Etiqueta pequena en mayusculas, para encabezar un dato."""
    return ft.Text(texto.upper(), size=10, weight=ft.FontWeight.W_600,
                   color=T.TEXTO_TENUE)


def dato(texto: str, peso: ft.FontWeight | None = None,
         color: str | None = None, tamano: int = 13) -> ft.Text:
    return ft.Text(str(texto), size=tamano, color=color or T.TEXTO,
                   weight=peso or ft.FontWeight.NORMAL)


# ---------------------------------------------------------------------------
# Contenedores
# ---------------------------------------------------------------------------


def panel(contenido: ft.Control, encabezado: str | None = None,
          acciones: list[ft.Control] | None = None,
          relleno: int = 16, expandir: bool = False) -> ft.Container:
    """Tarjeta blanca con borde suave; la unidad de composicion de las vistas."""
    hijos: list[ft.Control] = []
    if encabezado or acciones:
        hijos.append(
            ft.Row(
                [
                    titulo(encabezado or "", 15),
                    ft.Row(acciones or [], spacing=8),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        hijos.append(ft.Container(height=1, bgcolor=T.BORDE))
    hijos.append(contenido)
    return ft.Container(
        content=ft.Column(hijos, spacing=12, expand=expandir),
        bgcolor=T.PANEL,
        border=ft.Border.all(1, T.BORDE),
        border_radius=T.RADIO,
        padding=relleno,
        expand=expandir,
    )


def insignia(texto: str, tono: str | None = None) -> ft.Container:
    """Pildora de color para un estado de negocio."""
    color, fondo = T.TONOS[tono or T.tono_de(texto)]
    return ft.Container(
        content=ft.Text(str(texto).replace("_", " "), size=11,
                        weight=ft.FontWeight.W_600, color=color),
        bgcolor=fondo,
        border_radius=99,
        padding=ft.Padding.symmetric(vertical=4, horizontal=9),
    )


def aviso(texto: str, tono: str = "acento",
          icono: str | None = None) -> ft.Container:
    color, fondo = T.TONOS[tono]
    iconos = {"exito": ft.Icons.CHECK_CIRCLE, "alerta": ft.Icons.WARNING_AMBER,
              "peligro": ft.Icons.ERROR_OUTLINE, "acento": ft.Icons.INFO_OUTLINE,
              "neutro": ft.Icons.INFO_OUTLINE}
    return ft.Container(
        content=ft.Row(
            [
                ft.Icon(icono or iconos[tono], color=color, size=18),
                ft.Text(texto, size=13, color=color, expand=True),
            ],
            spacing=10,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=fondo,
        border=ft.Border.all(1, color + "33"),
        border_radius=T.RADIO_SM,
        padding=ft.Padding.symmetric(vertical=10, horizontal=12),
    )


def vacio(texto: str = "No hay datos para mostrar") -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.INBOX, size=32, color=T.BORDE_FUERTE),
                ft.Text(texto, size=13, color=T.TEXTO_TENUE),
            ],
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER,
        padding=32,
    )


def kpi(etiqueta: str, valor: str, icono: str,
        tono: str = "acento", pie: str | None = None) -> ft.Container:
    """Indicador del tablero: rotulo, cifra grande y un icono de apoyo."""
    color, fondo = T.TONOS[tono]
    return ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=ft.Icon(icono, color=color, size=20),
                    bgcolor=fondo, border_radius=T.RADIO_SM, padding=9,
                ),
                ft.Column(
                    [
                        rotulo(etiqueta),
                        ft.Text(valor, size=19, weight=ft.FontWeight.W_700,
                                color=T.TEXTO, no_wrap=True),
                    ]
                    + ([ft.Text(pie, size=11, color=T.TEXTO_TENUE)] if pie else []),
                    spacing=1,
                    expand=True,
                ),
            ],
            spacing=12,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        bgcolor=T.PANEL,
        border=ft.Border.all(1, T.BORDE),
        border_radius=T.RADIO,
        padding=14,
        expand=True,
    )


# ---------------------------------------------------------------------------
# Tablas
# ---------------------------------------------------------------------------


def tabla(columnas: Sequence[str], filas: Iterable[Sequence[ft.Control | str]],
          vacia: str = "No hay registros", alto: int | None = None) -> ft.Control:
    """Tabla con encabezado fijo y desplazamiento vertical.

    Acepta celdas ya construidas (`ft.Control`) o texto plano, que se envuelve
    automaticamente; asi las vistas simples no tienen que escribir `ft.Text`.
    """
    filas = list(filas)
    if not filas:
        return vacio(vacia)

    def celda(v: Any) -> ft.Control:
        return v if isinstance(v, ft.Control) else dato("—" if v is None else str(v))

    t = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(c, size=11, weight=ft.FontWeight.W_600,
                                  color=T.TEXTO_TENUE))
            for c in columnas
        ],
        rows=[ft.DataRow(cells=[ft.DataCell(celda(v)) for v in f]) for f in filas],
        heading_row_height=36,
        data_row_min_height=42,
        data_row_max_height=52,
        column_spacing=22,
        horizontal_margin=10,
        divider_thickness=1,
        heading_row_color=T.PANEL_SUAVE,
        show_bottom_border=False,
    )
    return ft.Column([t], scroll=ft.ScrollMode.AUTO, height=alto, expand=alto is None)


# ---------------------------------------------------------------------------
# Entradas
# ---------------------------------------------------------------------------


def campo(etiqueta: str, valor: str = "", ancho: int | None = None,
          clave: bool = False, icono: str | None = None,
          pista: str | None = None, solo_lectura: bool = False,
          al_enviar: Callable | None = None,
          al_cambiar: Callable | None = None,
          teclado: ft.KeyboardType | None = None,
          multilinea: bool = False, foco: bool = False) -> ft.TextField:
    """Campo de texto con el aspecto de la marca ya aplicado."""
    return ft.TextField(
        label=etiqueta,
        value=valor,
        width=ancho,
        autofocus=foco,
        password=clave,
        can_reveal_password=clave,
        prefix_icon=icono,
        hint_text=pista,
        read_only=solo_lectura,
        on_submit=al_enviar,
        on_change=al_cambiar,
        keyboard_type=teclado or ft.KeyboardType.TEXT,
        multiline=multilinea,
        min_lines=3 if multilinea else 1,
        text_size=13,
        label_style=ft.TextStyle(size=12, color=T.TEXTO_MEDIO),
        border_radius=T.RADIO_SM,
        border_color=T.BORDE_FUERTE,
        focused_border_color=T.ACENTO,
        bgcolor=T.PANEL,
        filled=True,
        fill_color=T.PANEL,
        color=T.TEXTO,
        content_padding=ft.Padding.symmetric(vertical=10, horizontal=12),
        dense=True,
    )


def lista(etiqueta: str, opciones: Sequence[tuple[Any, str]],
          valor: Any = None, ancho: int | None = None,
          al_elegir: Callable | None = None) -> ft.Dropdown:
    """Desplegable. Las claves se guardan como texto porque Flet asi las maneja."""
    return ft.Dropdown(
        label=etiqueta,
        value=None if valor is None else str(valor),
        width=ancho,
        options=[ft.DropdownOption(key=str(k), text=t) for k, t in opciones],
        on_select=al_elegir,
        text_size=13,
        label_style=ft.TextStyle(size=12, color=T.TEXTO_MEDIO),
        border_radius=T.RADIO_SM,
        border_color=T.BORDE_FUERTE,
        focused_border_color=T.ACENTO,
        bgcolor=T.PANEL,
        filled=True,
        fill_color=T.PANEL,
        color=T.TEXTO,
        content_padding=ft.Padding.symmetric(vertical=10, horizontal=12),
        dense=True,
    )


def boton(texto: str, al_hacer_clic: Callable | None = None,
          icono: str | None = None, tono: str = "acento",
          ancho: int | None = None, desactivado: bool = False) -> ft.Control:
    """Boton primario (azul) o secundario (contorno), segun el tono."""
    estilos = {
        "acento": (ft.Colors.WHITE, T.ACENTO),
        "exito": (ft.Colors.WHITE, T.EXITO),
        "peligro": (ft.Colors.WHITE, T.PELIGRO),
        "neutro": (T.TEXTO_MEDIO, T.PANEL),
    }
    color, fondo = estilos.get(tono, estilos["acento"])
    return ft.Button(
        texto,
        icon=icono,
        icon_color=color,
        color=color,
        bgcolor=fondo,
        width=ancho,
        disabled=desactivado,
        on_click=al_hacer_clic,
        elevation=0,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=T.RADIO_SM),
            padding=ft.Padding.symmetric(vertical=12, horizontal=18),
            side=ft.BorderSide(1, T.BORDE_FUERTE) if tono == "neutro" else None,
            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_600),
        ),
    )


def icono_boton(icono: str, al_hacer_clic: Callable | None = None,
                ayuda: str | None = None, color: str | None = None,
                desactivado: bool | None = None) -> ft.IconButton:
    """Boton de solo icono. Sin accion queda desactivado, no muerto en silencio."""
    return ft.IconButton(
        icon=icono, on_click=al_hacer_clic, tooltip=ayuda,
        icon_color=color or T.TEXTO_MEDIO, icon_size=18,
        disabled=al_hacer_clic is None if desactivado is None else desactivado,
    )


def segmentado(opciones: Sequence[str], activo: int,
               al_elegir: Callable[[int], None]) -> ft.Container:
    """Conmutador de pestanas hecho con contenedores.

    Reemplaza a `ft.Tabs`, que en Flet 1.0 exige declarar el contenido de todas
    las pestanas de una vez; aqui la vista se reconstruye con la pestana elegida
    y solo se consulta a la API lo que esa pestana necesita.
    """
    botones: list[ft.Control] = []
    for i, texto in enumerate(opciones):
        seleccionado = i == activo
        botones.append(
            ft.Container(
                content=ft.Text(texto, size=13,
                                weight=ft.FontWeight.W_600 if seleccionado else ft.FontWeight.W_500,
                                color=T.ACENTO if seleccionado else T.TEXTO_MEDIO),
                bgcolor=T.PANEL if seleccionado else None,
                border=ft.Border.all(1, T.BORDE if seleccionado else "#00000000"),
                border_radius=T.RADIO_SM,
                padding=ft.Padding.symmetric(vertical=7, horizontal=14),
                on_click=(lambda e, k=i: al_elegir(k)),
            )
        )
    return ft.Container(
        content=ft.Row(botones, spacing=4),
        bgcolor=T.NEUTRO_SUAVE,
        border_radius=T.RADIO,
        padding=4,
    )


def cargando(texto: str = "Cargando...") -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [ft.ProgressRing(width=26, height=26, stroke_width=3, color=T.ACENTO),
             ft.Text(texto, size=13, color=T.TEXTO_TENUE)],
            spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.Alignment.CENTER, padding=40, expand=True,
    )


def barra_proporcion(parte: float, total: float, color: str | None = None,
                     ancho: int = 120) -> ft.Control:
    """Barra horizontal simple; evita depender de una libreria de graficos."""
    fraccion = 0.0 if not total else max(0.0, min(1.0, parte / total))
    return ft.Container(
        content=ft.Container(
            bgcolor=color or T.ACENTO,
            border_radius=99,
            width=max(2.0, ancho * fraccion) if fraccion else 2.0,
            height=8,
        ),
        bgcolor=T.NEUTRO_SUAVE,
        border_radius=99,
        width=ancho,
        height=8,
        alignment=ft.Alignment.CENTER_LEFT,
    )
