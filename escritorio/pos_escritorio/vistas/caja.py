"""Caja: turnos, movimientos y arqueo.

Sin turno abierto no se puede facturar. Esa regla no es un capricho de la
interfaz: la hace cumplir el backend y la respalda un indice unico parcial en
PostgreSQL que impide dos turnos abiertos en la misma caja.
"""

from __future__ import annotations

from decimal import Decimal

import flet as ft

from .. import tema as T
from .. import ui
from .base import Vista


class Caja(Vista):
    titulo = "Caja"
    icono = ft.Icons.SAVINGS
    permisos = ("caja.abrir", "caja.cerrar", "caja.movimiento")

    def construir(self) -> ft.Control:
        turno = self.pedir(self.api.turno)
        cajas = self.pedir(self.api.cajas, []) or []
        historial = self.pedir(lambda: self.api.turnos(20), []) or []

        bloque = self._turno_abierto(turno, cajas) if turno else self._sin_turno(cajas)
        return ft.Column(
            [
                self.encabezado("Un turno abierto por caja. El cierre compara lo "
                                "esperado con lo contado y deja la diferencia."),
                bloque,
                self._historial(historial, cajas),
            ],
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # -- sin turno ----------------------------------------------------------

    def _sin_turno(self, cajas: list[dict]) -> ft.Control:
        libres = [c for c in cajas if c.get("activa") and not c.get("ocupada")]
        if not self.api.puede("caja.abrir"):
            return ui.panel(
                ui.aviso("No tienes turno abierto y tu rol no puede abrir caja. "
                         "Pide a un cajero o al administrador que abra el turno.",
                         "alerta"),
                "Sin turno",
            )
        if not libres:
            return ui.panel(
                ui.aviso("Todas las cajas tienen un turno abierto por otro usuario. "
                         "Hay que cerrar uno antes de abrir otro.", "alerta"),
                "Sin turno",
            )

        selector = ui.lista("Caja", [(c["id"], f"{c['nombre']} · {c.get('ubicacion') or ''}")
                                     for c in libres], valor=libres[0]["id"], ancho=320)
        base = ui.campo("Base inicial en efectivo", "0", ancho=220,
                        teclado=ft.KeyboardType.NUMBER)

        def abrir(_e=None):
            if not selector.value:
                self.ctx.aviso("Elige la caja.", "alerta")
                return
            try:
                valor = Decimal((base.value or "0").replace(".", "").replace(",", "."))
            except Exception:
                self.ctx.aviso("La base inicial debe ser un numero.", "alerta")
                return
            if valor < 0:
                self.ctx.aviso("La base inicial no puede ser negativa.", "alerta")
                return
            self.seguro(lambda: self.api.abrir_turno(int(selector.value), float(valor)),
                        "Turno abierto. Ya puedes facturar.")

        return ui.panel(
            ft.Column(
                [
                    ui.aviso("No tienes un turno abierto. Mientras no lo abras, el "
                             "punto de venta no deja registrar facturas.", "alerta"),
                    ft.Row([selector, base,
                            ui.boton("Abrir turno", abrir, ft.Icons.LOCK_OPEN, "exito")],
                           spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ],
                spacing=12,
            ),
            "Abrir turno de caja",
        )

    # -- turno abierto ------------------------------------------------------

    def _turno_abierto(self, turno: dict, cajas: list[dict]) -> ft.Control:
        arqueo = self.pedir(self.api.arqueo, {}) or {}
        nombre_caja = next((c["nombre"] for c in cajas if c["id"] == turno["caja_id"]),
                           f"Caja {turno['caja_id']}")

        indicadores = ft.Row(
            [
                ui.kpi("Base inicial", ui.pesos(arqueo.get("base_inicial",
                                                           turno["base_inicial"])),
                       ft.Icons.ACCOUNT_BALANCE_WALLET, "neutro"),
                ui.kpi("Efectivo por ventas", ui.pesos(arqueo.get("efectivo_ventas")),
                       ft.Icons.POINT_OF_SALE, "exito"),
                ui.kpi("Otros movimientos", ui.pesos(arqueo.get("otros_movimientos")),
                       ft.Icons.SWAP_HORIZ, "alerta"),
                ui.kpi("Efectivo esperado", ui.pesos(arqueo.get("efectivo_esperado")),
                       ft.Icons.SAVINGS, "acento",
                       f"recaudo total {ui.pesos(arqueo.get('recaudo_total'))}"),
            ],
            spacing=12,
        )

        acciones: list[ft.Control] = []
        if self.api.puede("caja.movimiento"):
            acciones.append(ui.boton("Registrar movimiento", self._dialogo_movimiento,
                                     ft.Icons.SWAP_HORIZ, "neutro"))
        if self.api.puede("caja.cerrar"):
            acciones.append(ui.boton("Cerrar turno",
                                     lambda e: self._dialogo_cierre(arqueo),
                                     ft.Icons.LOCK_OUTLINE, "peligro"))

        return ft.Column(
            [
                ui.aviso(f"Turno #{turno['id']} abierto en {nombre_caja} desde "
                         f"{ui.fecha_hora(turno['apertura'])}", "exito"),
                indicadores,
                ui.panel(
                    ft.Row(acciones, spacing=10) if acciones else
                    ui.aviso("Tu rol no puede mover ni cerrar la caja.", "neutro"),
                    "Operaciones del turno",
                ),
            ],
            spacing=14,
        )

    def _dialogo_movimiento(self, _=None) -> None:
        tipo = ui.lista("Tipo", [("INGRESO", "Ingreso de efectivo"),
                                 ("EGRESO", "Egreso de efectivo")],
                        valor="EGRESO", ancho=240)
        concepto = ui.campo("Concepto", pista="Pago de domicilio, cambio, consignacion...")
        valor = ui.campo("Valor", teclado=ft.KeyboardType.NUMBER)

        def guardar(_e=None):
            if len((concepto.value or "").strip()) < 3:
                self.ctx.aviso("Escribe el concepto del movimiento.", "alerta")
                return
            try:
                monto = Decimal((valor.value or "0").replace(".", "").replace(",", "."))
            except Exception:
                self.ctx.aviso("El valor debe ser un numero.", "alerta")
                return
            if monto <= 0:
                self.ctx.aviso("El valor debe ser mayor que cero.", "alerta")
                return
            self.ctx.cerrar()
            self.seguro(
                lambda: self.api.movimiento_caja(tipo.value, concepto.value.strip(),
                                                 float(monto)),
                "Movimiento registrado.")

        cuerpo = ft.Column([tipo, concepto, valor], spacing=12, tight=True)
        self.ctx.abrir(self.dialogo("Movimiento de caja", cuerpo, "Registrar", guardar))

    def _dialogo_cierre(self, arqueo: dict) -> None:
        esperado = Decimal(str(arqueo.get("efectivo_esperado") or 0))
        contado = ui.campo("Efectivo contado", str(int(esperado)),
                           teclado=ft.KeyboardType.NUMBER)
        diferencia = ft.Text("Diferencia: $ 0", size=13, color=T.TEXTO_MEDIO,
                             weight=ft.FontWeight.W_600)

        def recalcular(e) -> None:
            try:
                valor = Decimal((e.control.value or "0").replace(".", "").replace(",", "."))
            except Exception:
                diferencia.value = "Diferencia: —"
                diferencia.color = T.TEXTO_MEDIO
            else:
                d = valor - esperado
                diferencia.value = (f"Diferencia: {ui.pesos(d, True)}"
                                    + ("  (sobrante)" if d > 0 else
                                       "  (faltante)" if d < 0 else "  (cuadra)"))
                diferencia.color = T.EXITO if d == 0 else (T.ALERTA if d > 0 else T.PELIGRO)
            self.ctx.page.update()

        contado.on_change = recalcular

        def cerrar_turno(_e=None):
            try:
                valor = Decimal((contado.value or "0").replace(".", "").replace(",", "."))
            except Exception:
                self.ctx.aviso("El efectivo contado debe ser un numero.", "alerta")
                return
            self.ctx.cerrar()
            self.seguro(lambda: self.api.cerrar_turno(float(valor)),
                        "Turno cerrado.")

        cuerpo = ft.Column(
            [
                ui.aviso(f"Efectivo esperado en caja: {ui.pesos(esperado, True)}. "
                         f"Cuenta el dinero y escribe lo que hay.", "acento"),
                contado,
                diferencia,
            ],
            spacing=12, tight=True,
        )
        self.ctx.abrir(self.dialogo("Cerrar turno de caja", cuerpo, "Cerrar turno",
                                    cerrar_turno, tono="peligro"))

    # -- historial ----------------------------------------------------------

    def _historial(self, turnos: list[dict], cajas: list[dict]) -> ft.Control:
        nombres = {c["id"]: c["nombre"] for c in cajas}
        filas = []
        for t in turnos:
            d = t.get("diferencia")
            tono = "neutro"
            if d is not None:
                valor = Decimal(str(d))
                tono = "exito" if valor == 0 else ("alerta" if valor > 0 else "peligro")
            filas.append([
                ui.dato(f"#{t['id']}", ft.FontWeight.W_600),
                nombres.get(t["caja_id"], f"Caja {t['caja_id']}"),
                ui.fecha_hora(t["apertura"]),
                ui.fecha_hora(t.get("cierre")),
                ui.pesos(t["base_inicial"]),
                ui.pesos(t.get("efectivo_esperado")),
                ui.pesos(t.get("efectivo_contado")),
                ui.dato(ui.pesos(d) if d is not None else "—",
                        ft.FontWeight.W_600, T.TONOS[tono][0]),
                ui.insignia(t["estado"]),
            ])
        return ui.panel(
            ui.tabla(["Turno", "Caja", "Apertura", "Cierre", "Base", "Esperado",
                      "Contado", "Diferencia", "Estado"], filas,
                     "Todavia no hay turnos registrados", alto=300),
            "Historial de turnos",
        )
