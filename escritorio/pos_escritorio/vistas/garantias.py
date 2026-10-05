"""Garantias y servicio tecnico: la vida del equipo despues de la venta.

La garantia no es un campo de texto en la factura: es un registro con fecha de
inicio, fecha de fin y estado, consultable por el comprador. Es lo que exige el
Estatuto del Consumidor (Ley 1480 de 2011).
"""

from __future__ import annotations

import flet as ft

from .. import tema as T
from .. import ui
from .base import Vista

ESTADOS = ["VIGENTE", "VENCIDA", "EN_RECLAMACION", "ATENDIDA"]


class Garantias(Vista):
    titulo = "Garantias"
    icono = ft.Icons.VERIFIED_USER
    permisos = ("garantias.ver",)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.pestana = 0
        self.estado: str | None = None

    def construir(self) -> ft.Control:
        return ft.Column(
            [
                self.encabezado("Garantia legal registrada por unidad vendida y "
                                "ordenes de servicio tecnico."),
                ui.segmentado(["Garantias", "Servicio tecnico", "Apartados"],
                              self.pestana, self._cambiar_pestana),
                [self._garantias, self._servicio, self._apartados][self.pestana](),
            ],
            spacing=14,
            expand=True,
        )

    def _cambiar_pestana(self, indice: int) -> None:
        self.pestana = indice
        self.ctx.refrescar()

    # -- garantias ----------------------------------------------------------

    def _garantias(self) -> ft.Control:
        garantias = self.pedir(lambda: self.api.garantias(self.estado), []) or []
        filtro = ui.lista("Estado", [("", "Todas")] + [(e, e.replace("_", " ").title())
                                                       for e in ESTADOS],
                          valor=self.estado or "", ancho=200,
                          al_elegir=self._cambiar_estado)

        filas = []
        for g in garantias:
            dias = g.get("dias_restantes")
            tono = "exito"
            if g["estado"] == "VIGENTE" and isinstance(dias, int) and dias <= 30:
                tono = "alerta"
            acciones = []
            if self.api.puede("garantias.reclamar") and g["estado"] == "VIGENTE":
                acciones.append(ui.icono_boton(
                    ft.Icons.BUILD, lambda e, gr=g: self._dialogo_reclamo(gr),
                    "Abrir reclamacion", T.ACENTO))
            filas.append([
                ui.dato(f"#{g['id']}", ft.FontWeight.W_600),
                ui.numero(g["venta_detalle_id"]),
                ui.fecha(g["fecha_inicio"]),
                ui.fecha(g["fecha_fin"]),
                f"{g['meses']} meses",
                ui.dato(f"{dias} dias" if isinstance(dias, int) else "—",
                        ft.FontWeight.W_600, T.TONOS[tono][0]),
                ui.insignia(g["estado"]),
                ft.Row(acciones, spacing=0),
            ])

        vigentes = [g for g in garantias if g["estado"] == "VIGENTE"]
        por_vencer = [g for g in vigentes
                      if isinstance(g.get("dias_restantes"), int)
                      and g["dias_restantes"] <= 30]
        return ft.Column(
            [
                ft.Row(
                    [
                        ui.kpi("Vigentes", ui.numero(len(vigentes)),
                               ft.Icons.VERIFIED_USER, "exito"),
                        ui.kpi("Por vencer (30 dias)", ui.numero(len(por_vencer)),
                               ft.Icons.WARNING_AMBER, "alerta"),
                        ui.kpi("En reclamacion",
                               ui.numero(len([g for g in garantias
                                              if g["estado"] == "EN_RECLAMACION"])),
                               ft.Icons.BUILD, "acento"),
                        ui.kpi("Vencidas",
                               ui.numero(len([g for g in garantias
                                              if g["estado"] == "VENCIDA"])),
                               ft.Icons.BLOCK, "neutro"),
                    ],
                    spacing=12,
                ),
                ui.panel(
                    ft.Column([
                        filtro,
                        ui.tabla(["Garantia", "Linea de venta", "Inicio", "Vence",
                                  "Cobertura", "Restan", "Estado", ""], filas,
                                 "No hay garantias con ese estado"),
                    ], spacing=12, expand=True),
                    f"{len(garantias)} garantias",
                    expandir=True,
                ),
            ],
            spacing=14,
            expand=True,
        )

    def _cambiar_estado(self, e) -> None:
        self.estado = e.control.value or None
        self.ctx.refrescar()

    def _dialogo_reclamo(self, garantia: dict) -> None:
        falla = ui.campo("Falla reportada por el cliente", multilinea=True,
                         pista="No enciende, pantalla sin imagen, no carga...")

        def confirmar(_e=None):
            texto = (falla.value or "").strip()
            if len(texto) < 5:
                self.ctx.aviso("Describe la falla (minimo 5 letras).", "alerta")
                return
            self.ctx.cerrar()
            self.seguro(lambda: self.api.reclamar_garantia(garantia["id"], texto),
                        "Reclamacion abierta: se creo la orden de servicio.")

        cuerpo = ft.Column(
            [
                ui.aviso(f"Garantia #{garantia['id']} · vence "
                         f"{ui.fecha(garantia['fecha_fin'])}", "acento"),
                falla,
            ],
            spacing=12, tight=True,
        )
        self.ctx.abrir(self.dialogo("Abrir reclamacion de garantia", cuerpo,
                                    "Abrir reclamacion", confirmar))

    # -- servicio tecnico ---------------------------------------------------

    def _servicio(self) -> ft.Control:
        ordenes = self.pedir(self.api.ordenes_servicio, []) or []
        filas = [
            [
                ui.dato(o["numero"], ft.FontWeight.W_600),
                ui.nombre_cliente(o.get("cliente")),
                o.get("equipo_externo") or f"IMEI {o.get('equipo_imei_id') or '—'}",
                ft.Text(o.get("falla_reportada") or "—", size=12, color=T.TEXTO,
                        max_lines=2, overflow=ft.TextOverflow.ELLIPSIS, width=220),
                ui.pesos(o.get("costo_mano_obra")),
                ui.insignia(o["estado"]),
                ui.fecha(o.get("fecha_ingreso")),
            ]
            for o in ordenes
        ]
        return ui.panel(
            ui.tabla(["Orden", "Cliente", "Equipo", "Falla", "Mano de obra",
                      "Estado", "Ingreso"], filas,
                     "No hay ordenes de servicio registradas"),
            f"{len(ordenes)} ordenes de servicio",
            expandir=True,
        )

    # -- apartados ----------------------------------------------------------

    def _apartados(self) -> ft.Control:
        apartados = self.pedir(self.api.apartados, []) or []
        filas = [
            [
                ui.dato(f"#{a['id']}", ft.FontWeight.W_600),
                ui.nombre_cliente(a.get("cliente")),
                (a.get("equipo_imei") or {}).get("imei") or "—",
                ui.pesos(a["valor_total"]),
                ui.dato(ui.pesos(a["saldo_pendiente"]), ft.FontWeight.W_600,
                        T.ALERTA),
                ui.fecha(a["fecha_limite"]),
                ui.insignia(a["estado"]),
            ]
            for a in apartados
        ]
        return ui.panel(
            ft.Column([
                ui.aviso("Al crear un apartado el equipo queda reservado por un "
                         "trigger de PostgreSQL; nadie puede venderlo mientras tanto.",
                         "acento"),
                ui.tabla(["Apartado", "Cliente", "IMEI", "Valor", "Saldo",
                          "Vence", "Estado"], filas,
                         "No hay apartados registrados"),
            ], spacing=12, expand=True),
            f"{len(apartados)} apartados",
            expandir=True,
        )
