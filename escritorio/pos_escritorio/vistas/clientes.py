"""Clientes: el registro minimo que exige la venta y la garantia.

Solo se piden los datos necesarios para facturar y para hacer valer la garantia.
Esa contencion no es pereza: la Ley 1581 de 2012 obliga a pedir unicamente lo
que la finalidad justifica, y la casilla de autorizacion queda explicita.
"""

from __future__ import annotations

import flet as ft

from .. import tema as T
from .. import ui
from .base import Vista

DOCUMENTOS = ["CC", "CE", "TI", "NIT", "PASAPORTE"]


class Clientes(Vista):
    titulo = "Clientes"
    icono = ft.Icons.PEOPLE_ALT
    permisos = ("clientes.ver",)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.filtro = ""

    def construir(self) -> ft.Control:
        clientes = self.pedir(
            lambda: self.api.clientes(q=self.filtro or None, limite=300), []) or []
        buscador = ui.campo("Buscar por documento, nombre o telefono", self.filtro, 360,
                            icono=ft.Icons.SEARCH, al_enviar=self._buscar)

        filas = []
        for c in clientes:
            acciones = []
            if self.api.puede("clientes.editar"):
                acciones.append(ui.icono_boton(
                    ft.Icons.EDIT_OUTLINED, lambda e, cl=c: self._dialogo(cl),
                    "Editar cliente", T.ACENTO))
            acciones.append(ui.icono_boton(
                ft.Icons.RECEIPT_LONG, lambda e, cl=c: self._dialogo_compras(cl),
                "Historial de compras"))
            filas.append([
                ft.Row([ui.insignia(c["tipo_documento"], "neutro"),
                        ui.dato(c["numero_documento"], ft.FontWeight.W_600)], spacing=6),
                ui.nombre_cliente(c),
                c.get("telefono") or "—",
                c.get("email") or "—",
                c.get("ciudad") or "—",
                ui.insignia("SI" if c.get("autoriza_datos") else "NO",
                            "exito" if c.get("autoriza_datos") else "alerta"),
                ft.Row(acciones, spacing=0),
            ])

        barra = [buscador]
        if self.api.puede("clientes.crear"):
            barra.append(ui.boton("Nuevo cliente", lambda e: self._dialogo(),
                                  ft.Icons.ADD, "acento"))
        return ft.Column(
            [
                self.encabezado("Datos minimos para facturar y para responder por la "
                                "garantia legal."),
                ui.panel(
                    ft.Column([
                        ft.Row(barra, spacing=10,
                               vertical_alignment=ft.CrossAxisAlignment.CENTER),
                        ui.tabla(["Documento", "Nombre", "Telefono", "Correo",
                                  "Ciudad", "Autoriza datos", ""], filas,
                                 "Ningun cliente coincide con la busqueda"),
                    ], spacing=12, expand=True),
                    f"{len(clientes)} clientes",
                    expandir=True,
                ),
            ],
            spacing=14,
            expand=True,
        )

    def _buscar(self, e) -> None:
        self.filtro = (e.control.value or "").strip()
        self.ctx.refrescar()

    # -- alta y edicion -----------------------------------------------------

    def _dialogo(self, cliente: dict | None = None) -> None:
        editando = cliente is not None
        c = cliente or {}
        tipo = ui.lista("Tipo de documento", [(d, d) for d in DOCUMENTOS],
                        valor=c.get("tipo_documento", "CC"), ancho=200)
        documento = ui.campo("Numero de documento", c.get("numero_documento", ""))
        nombres = ui.campo("Nombres", c.get("nombres", ""))
        apellidos = ui.campo("Apellidos", c.get("apellidos") or "")
        telefono = ui.campo("Telefono", c.get("telefono") or "",
                            teclado=ft.KeyboardType.PHONE)
        correo = ui.campo("Correo", c.get("email") or "",
                          teclado=ft.KeyboardType.EMAIL)
        direccion = ui.campo("Direccion", c.get("direccion") or "")
        ciudad = ui.campo("Ciudad", c.get("ciudad") or "Bogota")
        autoriza = ft.Switch(label="Autoriza el tratamiento de sus datos",
                             value=bool(c.get("autoriza_datos")),
                             active_color=T.ACENTO)
        if editando:
            documento.read_only = True  # el documento identifica al cliente

        def guardar(_e=None):
            if not (nombres.value or "").strip():
                self.ctx.aviso("El nombre es obligatorio.", "alerta")
                return
            if not editando and not (documento.value or "").strip():
                self.ctx.aviso("El numero de documento es obligatorio.", "alerta")
                return
            cuerpo = {
                "nombres": nombres.value.strip(),
                "apellidos": (apellidos.value or "").strip() or None,
                "telefono": (telefono.value or "").strip() or None,
                "email": (correo.value or "").strip() or None,
                "direccion": (direccion.value or "").strip() or None,
                "ciudad": (ciudad.value or "").strip() or None,
                "autoriza_datos": bool(autoriza.value),
            }
            self.ctx.cerrar()
            if editando:
                self.seguro(lambda: self.api.actualizar_cliente(c["id"], cuerpo),
                            "Cliente actualizado.")
            else:
                cuerpo["tipo_documento"] = tipo.value or "CC"
                cuerpo["numero_documento"] = documento.value.strip()
                self.seguro(lambda: self.api.crear_cliente(cuerpo), "Cliente creado.")

        formulario = ft.Column(
            [
                ft.Row([tipo, documento], spacing=10),
                ft.Row([nombres, apellidos], spacing=10),
                ft.Row([telefono, correo], spacing=10),
                ft.Row([direccion, ciudad], spacing=10),
                autoriza,
                ui.aviso("Ley 1581 de 2012: solo se guardan los datos necesarios para "
                         "la venta y la garantia.", "acento"),
            ],
            spacing=12, tight=True,
        )
        self.ctx.abrir(self.dialogo(
            "Editar cliente" if editando else "Nuevo cliente", formulario,
            "Guardar" if editando else "Crear", guardar, ancho=620))

    def _dialogo_compras(self, cliente: dict) -> None:
        compras = self.pedir(lambda: self.api.compras_cliente(cliente["id"]), []) or []
        filas = [
            [
                ui.dato(v["numero"], ft.FontWeight.W_600),
                ui.fecha_hora(v["fecha"]),
                ui.numero(len(v.get("detalles") or [])),
                ui.pesos(v["total"]),
                ui.insignia(v["estado"]),
            ]
            for v in compras
        ]
        dlg = ft.AlertDialog(
            modal=True,
            title=ui.titulo(f"Compras de {ui.nombre_cliente(cliente)}", 16),
            content=ft.Container(
                content=ui.tabla(["Factura", "Fecha", "Lineas", "Total", "Estado"],
                                 filas, "Este cliente aun no tiene compras", alto=340),
                width=640,
            ),
            actions=[ui.boton("Cerrar", self.ctx.cerrar, tono="neutro")],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.ctx.abrir(dlg)
