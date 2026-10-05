"""Flet — el ejemplo minimo.

La aplicacion de escritorio completa esta en la carpeta `escritorio`. Este
archivo es la version de una pagina: lo suficiente para ver como funciona Flet
y en que se diferencia de Tkinter.

La diferencia esta en el modelo. En Tkinter se modifica el widget
(`etiqueta.config(text=...)`). En Flet se cambia el dato y se llama a
`page.update()`: Flet compara el arbol de controles con el que ya estaba
pintado y manda a Flutter solo lo que cambio.

    python 03_flet_ejemplo.py
"""

from decimal import ROUND_HALF_UP, Decimal

import flet as ft

IVA = Decimal("19")


def dinero(valor) -> Decimal:
    """Dos decimales, medio hacia arriba. La misma regla que usa el backend."""
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def main(page: ft.Page) -> None:
    page.title = "POS Movil — Ejemplo con Flet"
    page.bgcolor = "#F1F5F9"
    page.padding = 28
    page.window.width = 560
    page.window.height = 520

    precio = ft.TextField(label="Precio sin IVA", value="1000000", dense=True,
                          keyboard_type=ft.KeyboardType.NUMBER, border_radius=7,
                          bgcolor="#FFFFFF", filled=True)
    cantidad = ft.TextField(label="Cantidad", value="1", dense=True,
                            keyboard_type=ft.KeyboardType.NUMBER, border_radius=7,
                            bgcolor="#FFFFFF", filled=True)
    descuento = ft.TextField(label="Descuento", value="0", dense=True,
                             keyboard_type=ft.KeyboardType.NUMBER, border_radius=7,
                             bgcolor="#FFFFFF", filled=True)

    base_txt = ft.Text("—", size=14, color="#475569")
    iva_txt = ft.Text("—", size=14, color="#475569")
    total_txt = ft.Text("—", size=26, weight=ft.FontWeight.W_700, color="#0F172A")
    error_txt = ft.Text("", size=12, color="#B91C1C")

    def formatear(n: Decimal) -> str:
        return f"$ {int(n):,}".replace(",", ".")

    def calcular(_e=None) -> None:
        error_txt.value = ""
        try:
            bruto = dinero(Decimal(precio.value or 0) * int(cantidad.value or 0))
            desc = dinero(descuento.value or 0)
        except Exception:
            error_txt.value = "Escribe numeros validos."
            page.update()
            return
        if desc > bruto:
            error_txt.value = "El descuento no puede superar el valor de la linea."
            desc = Decimal("0")
        base = dinero(bruto - desc)
        iva = dinero(base * IVA / 100)
        base_txt.value = formatear(base)
        iva_txt.value = formatear(iva)
        total_txt.value = formatear(dinero(base + iva))
        # Un solo update: Flet recalcula el arbol y refresca lo que cambio.
        page.update()

    for campo in (precio, cantidad, descuento):
        campo.on_change = calcular

    def linea(etiqueta: str, control: ft.Control) -> ft.Row:
        return ft.Row([ft.Text(etiqueta, size=14, color="#475569"), control],
                      alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    page.controls = [
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Calculo de una linea de factura", size=18,
                            weight=ft.FontWeight.W_600, color="#0F172A"),
                    ft.Text("IVA del 19% — Colombia", size=12, color="#64748B"),
                    ft.Container(height=1, bgcolor="#E2E8F0"),
                    precio, cantidad, descuento,
                    error_txt,
                    ft.Container(height=1, bgcolor="#E2E8F0"),
                    linea("Base gravable", base_txt),
                    linea("IVA", iva_txt),
                    linea("Total", total_txt),
                ],
                spacing=14,
                tight=True,
            ),
            bgcolor="#FFFFFF",
            border=ft.Border.all(1, "#E2E8F0"),
            border_radius=10,
            padding=22,
        )
    ]
    calcular()


if __name__ == "__main__":
    ft.run(main)
