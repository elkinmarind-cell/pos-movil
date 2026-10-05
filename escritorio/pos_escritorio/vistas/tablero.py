"""Tablero: el estado del negocio en una sola pantalla."""

from __future__ import annotations

from decimal import Decimal

import flet as ft

from .. import tema as T
from .. import ui
from .base import Vista


class Tablero(Vista):
    titulo = "Tablero"
    icono = ft.Icons.SPACE_DASHBOARD
    permisos = ("reportes.ver",)

    def construir(self) -> ft.Control:
        d = self.pedir(self.api.tablero, {}) or {}
        dias = self.pedir(lambda: self.api.ventas_por_dia(14), []) or []
        vendidos = self.pedir(lambda: self.api.mas_vendidos(5, 30), []) or []
        alertas = self.pedir(self.api.alertas_stock, []) or []

        turno = d.get("turno_abierto")
        franja = ui.aviso(
            "Tienes un turno de caja abierto. Puedes facturar."
            if turno else
            "No hay turno de caja abierto. Abre uno en Caja para poder facturar.",
            "exito" if turno else "alerta",
        )

        indicadores = ft.Row(
            [
                ui.kpi("Ventas de hoy", ui.pesos(d.get("ventas_hoy")),
                       ft.Icons.POINT_OF_SALE, "acento",
                       f"{d.get('numero_ventas_hoy', 0)} facturas"),
                ui.kpi("Ventas del mes", ui.pesos(d.get("ventas_mes")),
                       ft.Icons.TRENDING_UP, "exito",
                       f"ticket promedio {ui.pesos(d.get('ticket_promedio_mes'))}"),
                ui.kpi("Equipos disponibles", ui.numero(d.get("equipos_disponibles")),
                       ft.Icons.SMARTPHONE, "neutro", "unidades con IMEI libre"),
                ui.kpi("Garantias vigentes", ui.numero(d.get("garantias_vigentes")),
                       ft.Icons.VERIFIED_USER, "acento", "Ley 1480 de 2011"),
            ],
            spacing=12,
        )

        segunda_fila = ft.Row(
            [
                ui.kpi("Bajo stock", ui.numero(d.get("productos_bajo_stock")),
                       ft.Icons.WARNING_AMBER, "alerta", "productos en o bajo el minimo"),
                ui.kpi("Servicio tecnico", ui.numero(d.get("ordenes_servicio_abiertas")),
                       ft.Icons.BUILD, "alerta", "ordenes abiertas"),
                ui.kpi("Apartados vigentes", ui.numero(d.get("apartados_vigentes")),
                       ft.Icons.PLAYLIST_ADD_CHECK, "acento", "con saldo pendiente"),
                ui.kpi("Alertas IoT", ui.numero(d.get("alertas_sin_atender")),
                       ft.Icons.SENSORS, "peligro", "sin atender"),
            ],
            spacing=12,
        )

        return ft.Column(
            [
                self.encabezado(
                    f"Hola, {self.api.nombre.split(' ')[0]}. "
                    f"Sesion como {self.api.rol.lower()}.",
                    [ui.boton("Actualizar", lambda _: self.ctx.refrescar(),
                              ft.Icons.REFRESH, "neutro")],
                ),
                franja,
                indicadores,
                segunda_fila,
                ft.Row(
                    [
                        ft.Container(content=self._grafico(dias), expand=3),
                        ft.Container(content=self._mas_vendidos(vendidos), expand=2),
                    ],
                    spacing=12,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                ),
                self._alertas(alertas),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # -- piezas -------------------------------------------------------------

    def _grafico(self, dias: list[dict]) -> ft.Control:
        """Barras verticales dibujadas con contenedores.

        Un grafico de barras es geometria simple; no vale la pena arrastrar una
        dependencia de graficos al ejecutable por catorce rectangulos.
        """
        if not dias:
            return ui.panel(ui.vacio("Sin ventas registradas"), "Ventas de los ultimos 14 dias")

        montos = [Decimal(str(x.get("total") or 0)) for x in dias]
        techo = max(montos) or Decimal(1)
        barras = []
        for registro, monto in zip(dias, montos):
            alto = int(130 * float(monto / techo)) if monto else 2
            dia = str(registro.get("fecha", ""))[-2:]
            barras.append(
                ft.Column(
                    [
                        ft.Container(
                            content=ft.Container(
                                bgcolor=T.ACENTO if monto else T.BORDE,
                                border_radius=ft.BorderRadius.only(top_left=4, top_right=4),
                                height=max(alto, 2),
                                width=22,
                                tooltip=f"{registro.get('fecha')}\n"
                                        f"{ui.pesos(monto)} · {registro.get('cantidad', 0)} ventas",
                            ),
                            height=130,
                            alignment=ft.Alignment.BOTTOM_CENTER,
                        ),
                        ft.Text(dia, size=10, color=T.TEXTO_TENUE),
                    ],
                    spacing=5,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

        total = sum(montos)
        return ui.panel(
            ft.Column(
                [
                    ft.Row(barras, spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                           vertical_alignment=ft.CrossAxisAlignment.END),
                    ft.Text(f"Total del periodo: {ui.pesos(total)}  ·  "
                            f"maximo diario: {ui.pesos(techo)}",
                            size=11, color=T.TEXTO_TENUE),
                ],
                spacing=10,
            ),
            "Ventas de los ultimos 14 dias",
        )

    def _mas_vendidos(self, filas: list[dict]) -> ft.Control:
        if not filas:
            return ui.panel(ui.vacio("Sin ventas en los ultimos 30 dias"), "Mas vendidos")
        techo = max((int(f.get("unidades") or 0) for f in filas), default=1) or 1
        lineas = []
        for f in filas:
            unidades = int(f.get("unidades") or 0)
            lineas.append(
                ft.Column(
                    [
                        ft.Row(
                            [
                                ft.Text(f.get("nombre", ""), size=12, color=T.TEXTO,
                                        expand=True, max_lines=1,
                                        overflow=ft.TextOverflow.ELLIPSIS),
                                ft.Text(f"{unidades} u.", size=12,
                                        weight=ft.FontWeight.W_600, color=T.TEXTO_MEDIO),
                            ],
                            spacing=8,
                        ),
                        ft.Row(
                            [
                                ui.barra_proporcion(unidades, techo, T.ACENTO, 150),
                                ft.Text(ui.pesos(f.get("total_vendido")), size=11,
                                        color=T.TEXTO_TENUE),
                            ],
                            spacing=10,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        ),
                    ],
                    spacing=4,
                )
            )
        return ui.panel(ft.Column(lineas, spacing=12), "Mas vendidos (30 dias)")

    def _alertas(self, alertas: list[dict]) -> ft.Control:
        filas = [
            [
                f.get("sku", ""),
                f.get("nombre", ""),
                ui.dato(ui.numero(f.get("disponibles")), ft.FontWeight.W_600,
                        T.PELIGRO if int(f.get("disponibles") or 0) == 0 else T.ALERTA),
                ui.numero(f.get("stock_minimo")),
                ui.insignia("AGOTADO" if int(f.get("disponibles") or 0) == 0 else "BAJO",
                            "peligro" if int(f.get("disponibles") or 0) == 0 else "alerta"),
            ]
            for f in alertas
        ]
        return ui.panel(
            ui.tabla(["SKU", "Producto", "Disponibles", "Minimo", "Estado"], filas,
                     "Ningun producto esta por debajo del minimo", alto=230),
            "Alertas de inventario",
            [ui.boton("Ver inventario", lambda _: self.ctx.ir_a("inventario"),
                      ft.Icons.ARROW_FORWARD, "neutro")]
            if self.api.puede("inventario.ver") else None,
        )
