"""Ventas: consulta de facturas, detalle y anulacion.

Anular no borra nada: deja la factura marcada con su motivo y la reversa de
inventario, kardex y garantia la ejecuta PostgreSQL en una sola transaccion
(`fn_anular_venta`). Una factura emitida es un documento, no una fila que se
pueda tachar.
"""

from __future__ import annotations

from datetime import date, timedelta

import flet as ft

from .. import tema as T
from .. import ui
from .base import Vista


class Ventas(Vista):
    titulo = "Ventas"
    icono = ft.Icons.RECEIPT_LONG
    permisos = ("ventas.ver",)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.dias = 30
        self.estado: str | None = None

    def construir(self) -> ft.Control:
        desde = (date.today() - timedelta(days=self.dias)).isoformat()
        ventas = self.pedir(
            lambda: self.api.ventas(desde=desde, estado=self.estado, limite=300), []) or []

        periodo = ui.lista("Periodo", [(7, "Ultimos 7 dias"), (30, "Ultimos 30 dias"),
                                       (90, "Ultimos 90 dias"), (365, "Ultimo ano")],
                           valor=self.dias, ancho=190, al_elegir=self._cambiar_periodo)
        estado = ui.lista("Estado", [("", "Todas"), ("COMPLETADA", "Completadas"),
                                     ("ANULADA", "Anuladas")],
                          valor=self.estado or "", ancho=170,
                          al_elegir=self._cambiar_estado)

        filas = []
        for v in ventas:
            acciones = [ui.icono_boton(ft.Icons.VISIBILITY,
                                       lambda e, vt=v: self._dialogo_detalle(vt),
                                       "Ver detalle y factura")]
            if self.api.puede("ventas.anular") and v["estado"] == "COMPLETADA":
                acciones.append(ui.icono_boton(
                    ft.Icons.BLOCK, lambda e, vt=v: self._dialogo_anular(vt),
                    "Anular venta", T.PELIGRO))
            filas.append([
                ui.dato(v["numero"], ft.FontWeight.W_600),
                ui.fecha_hora(v["fecha"]),
                ui.nombre_cliente(v.get("cliente")),
                (v.get("usuario") or {}).get("nombre_completo", "—"),
                ui.numero(len(v.get("detalles") or [])),
                ui.pesos(v["total"]),
                ui.insignia(v["estado"]),
                ft.Row(acciones, spacing=0),
            ])

        completadas = [v for v in ventas if v["estado"] == "COMPLETADA"]
        total = sum(float(v["total"]) for v in completadas)
        resumen = ft.Row(
            [
                ui.kpi("Facturas del periodo", ui.numero(len(ventas)),
                       ft.Icons.RECEIPT_LONG, "acento"),
                ui.kpi("Recaudo (sin anuladas)", ui.pesos(total),
                       ft.Icons.PAYMENTS, "exito"),
                ui.kpi("Anuladas", ui.numero(len(ventas) - len(completadas)),
                       ft.Icons.BLOCK, "peligro"),
                ui.kpi("Ticket promedio",
                       ui.pesos(total / len(completadas) if completadas else 0),
                       ft.Icons.TRENDING_UP, "neutro"),
            ],
            spacing=12,
        )

        return ft.Column(
            [
                self.encabezado("Historial de facturacion. Anular revierte inventario, "
                                "kardex y garantia en una sola transaccion."),
                resumen,
                ui.panel(
                    ft.Column([
                        ft.Row([periodo, estado], spacing=10),
                        ui.tabla(["Factura", "Fecha", "Cliente", "Vendedor", "Lineas",
                                  "Total", "Estado", ""], filas,
                                 "No hay ventas en el periodo elegido"),
                    ], spacing=12, expand=True),
                    f"{len(ventas)} facturas",
                    expandir=True,
                ),
            ],
            spacing=14,
            expand=True,
        )

    def _cambiar_periodo(self, e) -> None:
        self.dias = int(e.control.value or 30)
        self.ctx.refrescar()

    def _cambiar_estado(self, e) -> None:
        self.estado = e.control.value or None
        self.ctx.refrescar()

    # -- detalle ------------------------------------------------------------

    def _dialogo_detalle(self, venta: dict) -> None:
        v = self.pedir(lambda: self.api.venta(venta["id"]), {}) or {}
        if not v:
            return
        factura = self.pedir(lambda: self.api.factura(venta["id"]), {}) or {}

        lineas = [
            [
                (d.get("producto") or {}).get("nombre", "—"),
                (d.get("equipo_imei") or {}).get("imei") or "—",
                ui.numero(d["cantidad"]),
                ui.pesos(d["precio_unitario"]),
                ui.pesos(d["descuento"]),
                ui.pesos(d["iva_valor"]),
                ui.dato(ui.pesos(d["total_linea"]), ft.FontWeight.W_600),
            ]
            for d in (v.get("detalles") or [])
        ]
        pagos = ft.Row(
            [ft.Row([ui.insignia(p["metodo"], "acento"),
                     ft.Text(ui.pesos(p["valor"], True), size=12, color=T.TEXTO)],
                    spacing=6)
             for p in (v.get("pagos") or [])] or [ft.Text("—", size=12)],
            spacing=14, wrap=True,
        )

        def total(etiqueta: str, valor, fuerte=False) -> ft.Row:
            return ft.Row(
                [ft.Text(etiqueta, size=13 if not fuerte else 15, color=T.TEXTO_MEDIO),
                 ft.Text(ui.pesos(valor, True), size=13 if not fuerte else 18,
                         weight=ft.FontWeight.W_700 if fuerte else ft.FontWeight.W_600,
                         color=T.TEXTO)],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )

        encabezado = ft.Row(
            [
                ft.Column([ui.rotulo("Cliente"),
                           ft.Text(ui.nombre_cliente(v.get("cliente")), size=13,
                                   color=T.TEXTO)], spacing=2, expand=True),
                ft.Column([ui.rotulo("Vendedor"),
                           ft.Text((v.get("usuario") or {}).get("nombre_completo", "—"),
                                   size=13, color=T.TEXTO)], spacing=2, expand=True),
                ft.Column([ui.rotulo("Estado"), ui.insignia(v["estado"])],
                          spacing=2),
            ],
            spacing=14,
        )

        cuerpo = [
            encabezado,
            ft.Container(height=1, bgcolor=T.BORDE),
            ui.tabla(["Producto", "IMEI", "Cant.", "Precio", "Descuento", "IVA",
                      "Total"], lineas, "Factura sin lineas", alto=220),
            ft.Container(height=1, bgcolor=T.BORDE),
            ft.Column([ui.rotulo("Pagos"), pagos], spacing=6),
            ft.Container(height=1, bgcolor=T.BORDE),
            total("Subtotal", v["subtotal"]),
            total("Descuentos", v["descuento_total"]),
            total("IVA", v["iva_total"]),
            total("Total", v["total"], True),
        ]
        if factura:
            cuerpo += [
                ft.Container(height=1, bgcolor=T.BORDE),
                ft.Column(
                    [
                        ui.rotulo("Factura electronica (DIAN)"),
                        ft.Text(f"Numero {factura.get('numero', '—')} · estado "
                                f"{factura.get('estado', '—')}", size=12, color=T.TEXTO),
                        ft.Text(f"CUFE {str(factura.get('cufe', ''))[:48]}...", size=10,
                                color=T.TEXTO_TENUE, selectable=True),
                    ],
                    spacing=3,
                ),
            ]
        if v.get("motivo_anulacion"):
            cuerpo.append(ui.aviso(f"Anulada: {v['motivo_anulacion']}", "peligro"))

        dlg = ft.AlertDialog(
            modal=True,
            title=ui.titulo(f"Factura {v['numero']} · {ui.fecha_hora(v['fecha'])}", 16),
            content=ft.Container(
                content=ft.Column(cuerpo, spacing=10, scroll=ft.ScrollMode.AUTO),
                width=780, height=520,
            ),
            actions=[ui.boton("Cerrar", self.ctx.cerrar, tono="neutro")],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.ctx.abrir(dlg)

    def _dialogo_anular(self, venta: dict) -> None:
        motivo = ui.campo("Motivo de la anulacion", multilinea=True,
                          pista="Devolucion del cliente, error de digitacion...")

        def confirmar(_e=None):
            texto = (motivo.value or "").strip()
            if len(texto) < 5:
                self.ctx.aviso("Escribe el motivo de la anulacion (minimo 5 letras).",
                               "alerta")
                return
            self.ctx.cerrar()
            self.seguro(lambda: self.api.anular_venta(venta["id"], texto),
                        f"Factura {venta['numero']} anulada. Inventario y garantia "
                        f"revertidos.")

        cuerpo = ft.Column(
            [
                ui.aviso(f"Vas a anular la factura {venta['numero']} por "
                         f"{ui.pesos(venta['total'], True)}. Los equipos vuelven a "
                         f"estar disponibles y las garantias se anulan.", "peligro"),
                motivo,
            ],
            spacing=12, tight=True,
        )
        self.ctx.abrir(self.dialogo("Anular venta", cuerpo, "Anular", confirmar,
                                    tono="peligro"))
