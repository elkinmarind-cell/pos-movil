"""Inventario: productos (existencias por SKU) y equipos (existencias por IMEI).

Las dos estrategias de inventario del sistema viven en la misma pantalla, en dos
pestanas, porque son dos formas de responder la misma pregunta: que hay para
vender. Un accesorio se cuenta; un celular se identifica.
"""

from __future__ import annotations

import flet as ft

from .. import tema as T
from .. import ui
from .base import Vista

ESTADOS_IMEI = ["DISPONIBLE", "APARTADO", "VENDIDO", "DEVUELTO",
                "EN_SERVICIO", "DADO_DE_BAJA"]


class Inventario(Vista):
    titulo = "Inventario"
    icono = ft.Icons.INVENTORY_2
    permisos = ("inventario.ver",)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.pestana = 0
        self.filtro_productos = ""
        self.filtro_equipos = ""
        self.estado_equipos: str | None = None

    def construir(self) -> ft.Control:
        contenido = (self._productos() if self.pestana == 0 else self._equipos())
        return ft.Column(
            [
                self.encabezado(
                    "Un accesorio se cuenta por unidades; un equipo se identifica "
                    "por IMEI. Aqui estan los dos."
                ),
                ui.segmentado(["Productos", "Equipos por IMEI"], self.pestana,
                              self._cambiar_pestana),
                contenido,
            ],
            spacing=14,
            expand=True,
        )

    def _cambiar_pestana(self, indice: int) -> None:
        self.pestana = indice
        self.ctx.refrescar()

    # -- productos ----------------------------------------------------------

    def _productos(self) -> ft.Control:
        productos = self.pedir(
            lambda: self.api.productos(q=self.filtro_productos or None, limite=300), []
        ) or []
        buscador = ui.campo("Buscar producto", self.filtro_productos, 320,
                            icono=ft.Icons.SEARCH, al_enviar=self._buscar_productos)

        filas = []
        for p in productos:
            disponibles = int(p.get("disponibles") or 0)
            minimo = int(p.get("stock_minimo") or 0)
            tono = "peligro" if disponibles == 0 else ("alerta" if disponibles <= minimo else "exito")
            acciones = []
            if self.api.puede("inventario.ajustar") and not p["requiere_imei"]:
                acciones.append(ui.icono_boton(
                    ft.Icons.EDIT_OUTLINED,
                    lambda e, prod=p: self._dialogo_ajuste(prod),
                    "Ajustar existencias", T.ACENTO))
            acciones.append(ui.icono_boton(
                ft.Icons.HISTORY, lambda e, prod=p: self._dialogo_kardex(prod),
                "Ver kardex"))
            filas.append([
                ui.dato(p["sku"], ft.FontWeight.W_600),
                p["nombre"],
                (p.get("marca") or {}).get("nombre") or "—",
                (p.get("categoria") or {}).get("nombre") or "—",
                ui.pesos(p["precio_venta"]),
                ui.dato(ui.numero(disponibles), ft.FontWeight.W_600,
                        T.TONOS[tono][0]),
                ui.insignia("IMEI" if p["requiere_imei"] else "STOCK",
                            "acento" if p["requiere_imei"] else "neutro"),
                ft.Row(acciones, spacing=0),
            ])

        acciones_panel = [buscador]
        if self.api.puede("inventario.crear"):
            acciones_panel.append(ui.boton("Nuevo producto", self._dialogo_producto,
                                           ft.Icons.ADD, "acento"))
        return ui.panel(
            ft.Column([
                ft.Row(acciones_panel, spacing=10,
                       vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ui.tabla(["SKU", "Producto", "Marca", "Categoria", "Precio",
                          "Disponibles", "Tipo", ""], filas,
                         "Ningun producto coincide con la busqueda"),
            ], spacing=12, expand=True),
            f"{len(productos)} productos",
            expandir=True,
        )

    def _buscar_productos(self, e) -> None:
        self.filtro_productos = (e.control.value or "").strip()
        self.ctx.refrescar()

    def _dialogo_producto(self, _=None) -> None:
        categorias = self.pedir(self.api.categorias, []) or []
        marcas = self.pedir(self.api.marcas, []) or []
        sku = ui.campo("SKU")
        nombre = ui.campo("Nombre")
        categoria = ui.lista("Categoria", [(c["id"], c["nombre"]) for c in categorias])
        marca = ui.lista("Marca", [(m["id"], m["nombre"]) for m in marcas])
        costo = ui.campo("Precio de costo", "0", teclado=ft.KeyboardType.NUMBER)
        venta = ui.campo("Precio de venta", "0", teclado=ft.KeyboardType.NUMBER)
        iva = ui.campo("IVA %", "19", teclado=ft.KeyboardType.NUMBER)
        meses = ui.campo("Meses de garantia", "12", teclado=ft.KeyboardType.NUMBER)
        minimo = ui.campo("Stock minimo", "5", teclado=ft.KeyboardType.NUMBER)
        inicial = ui.campo("Stock inicial", "0", teclado=ft.KeyboardType.NUMBER)
        serializado = ft.Switch(label="Se controla por IMEI", value=False,
                                active_color=T.ACENTO)

        def guardar(_e=None):
            if not (sku.value or "").strip() or not (nombre.value or "").strip():
                self.ctx.aviso("El SKU y el nombre son obligatorios.", "alerta")
                return
            if not categoria.value:
                self.ctx.aviso("Elige una categoria.", "alerta")
                return
            cuerpo = {
                "sku": sku.value.strip().upper(),
                "nombre": nombre.value.strip(),
                "categoria_id": int(categoria.value),
                "marca_id": int(marca.value) if marca.value else None,
                "precio_costo": (costo.value or "0").strip(),
                "precio_venta": (venta.value or "0").strip(),
                "iva_porcentaje": (iva.value or "19").strip(),
                "requiere_imei": bool(serializado.value),
                "meses_garantia": int(meses.value or 12),
                "stock_minimo": int(minimo.value or 5),
                "stock_actual": 0 if serializado.value else int(inicial.value or 0),
            }
            self.ctx.cerrar()
            self.seguro(lambda: self.api.crear_producto(cuerpo),
                        f"Producto {cuerpo['sku']} creado.")

        formulario = ft.Column(
            [
                ft.Row([sku, nombre], spacing=10),
                ft.Row([categoria, marca], spacing=10),
                ft.Row([costo, venta, iva], spacing=10),
                ft.Row([meses, minimo, inicial], spacing=10),
                serializado,
                ui.aviso("Un producto controlado por IMEI no lleva stock: cada unidad "
                         "entra por separado en la pestana de equipos.", "acento"),
            ],
            spacing=12,
            tight=True,
        )
        self.ctx.abrir(self.dialogo("Nuevo producto", formulario, "Crear", guardar,
                                    ancho=620))

    def _dialogo_ajuste(self, producto: dict) -> None:
        cantidad = ui.campo("Cantidad (positiva entra, negativa sale)", "0",
                            teclado=ft.KeyboardType.NUMBER)
        motivo = ui.campo("Motivo", pista="Conteo fisico, averia, devolucion...")

        def guardar(_e=None):
            try:
                n = int((cantidad.value or "0").strip())
            except ValueError:
                self.ctx.aviso("La cantidad debe ser un numero entero.", "alerta")
                return
            if n == 0:
                self.ctx.aviso("La cantidad no puede ser cero.", "alerta")
                return
            if len((motivo.value or "").strip()) < 3:
                self.ctx.aviso("Escribe el motivo del ajuste.", "alerta")
                return
            self.ctx.cerrar()
            self.seguro(lambda: self.api.ajustar_stock(producto["id"], n, motivo.value.strip()),
                        "Existencias ajustadas y registradas en el kardex.")

        cuerpo = ft.Column(
            [
                ui.aviso(f"{producto['nombre']} · existencias actuales: "
                         f"{producto.get('disponibles', 0)}", "acento"),
                cantidad, motivo,
            ],
            spacing=12, tight=True,
        )
        self.ctx.abrir(self.dialogo("Ajustar existencias", cuerpo, "Ajustar", guardar))

    def _dialogo_kardex(self, producto: dict) -> None:
        movimientos = self.pedir(lambda: self.api.kardex(producto["id"], 100), []) or []
        filas = [
            [
                ui.fecha_hora(m["fecha"]),
                ui.insignia(m["tipo"], "exito" if m["tipo"] in ("ENTRADA", "DEVOLUCION")
                            else ("peligro" if m["tipo"] == "SALIDA" else "neutro")),
                ui.numero(m["cantidad"]),
                ui.numero(m["stock_resultante"]),
                m.get("motivo") or "—",
                m.get("referencia") or "—",
            ]
            for m in movimientos
        ]
        dlg = ft.AlertDialog(
            modal=True,
            title=ui.titulo(f"Kardex · {producto['nombre']}", 16),
            content=ft.Container(
                content=ui.tabla(["Fecha", "Tipo", "Cantidad", "Saldo", "Motivo",
                                  "Referencia"], filas,
                                 "Este producto no tiene movimientos", alto=380),
                width=760,
            ),
            actions=[ui.boton("Cerrar", self.ctx.cerrar, tono="neutro")],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.ctx.abrir(dlg)

    # -- equipos ------------------------------------------------------------

    def _equipos(self) -> ft.Control:
        equipos = self.pedir(
            lambda: self.api.equipos(q=self.filtro_equipos or None,
                                     estado=self.estado_equipos, limite=300), []
        ) or []
        buscador = ui.campo("Buscar por IMEI o RFID", self.filtro_equipos, 300,
                            icono=ft.Icons.SEARCH, al_enviar=self._buscar_equipos)
        filtro = ui.lista("Estado", [("", "Todos")] + [(e, e.replace("_", " ").title())
                                                       for e in ESTADOS_IMEI],
                          valor=self.estado_equipos or "", ancho=190,
                          al_elegir=self._filtrar_equipos)

        filas = []
        for e in equipos:
            producto = e.get("producto") or {}
            acciones = []
            if self.api.puede("inventario.ajustar"):
                acciones.append(ui.icono_boton(
                    ft.Icons.SWAP_HORIZ, lambda _e, eq=e: self._dialogo_estado(eq),
                    "Cambiar estado", T.ACENTO))
            acciones.append(ui.icono_boton(
                ft.Icons.TIMELINE, lambda _e, eq=e: self._dialogo_trazabilidad(eq),
                "Trazabilidad"))
            filas.append([
                ui.dato(e["imei"], ft.FontWeight.W_600),
                producto.get("nombre") or "—",
                e.get("color") or "—",
                f"{e['almacenamiento_gb']} GB" if e.get("almacenamiento_gb") else "—",
                ui.pesos(e.get("costo")),
                ui.insignia(e["estado"]),
                ui.fecha(e.get("fecha_ingreso")),
                ft.Row(acciones, spacing=0),
            ])

        barra = [buscador, filtro]
        if self.api.puede("inventario.crear"):
            barra.append(ui.boton("Ingresar equipo", self._dialogo_equipo,
                                  ft.Icons.ADD, "acento"))
        return ui.panel(
            ft.Column([
                ft.Row(barra, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ui.tabla(["IMEI", "Producto", "Color", "Capacidad", "Costo",
                          "Estado", "Ingreso", ""], filas,
                         "Ningun equipo coincide con el filtro"),
            ], spacing=12, expand=True),
            f"{len(equipos)} equipos",
            expandir=True,
        )

    def _buscar_equipos(self, e) -> None:
        self.filtro_equipos = (e.control.value or "").strip()
        self.ctx.refrescar()

    def _filtrar_equipos(self, e) -> None:
        self.estado_equipos = e.control.value or None
        self.ctx.refrescar()

    def _dialogo_equipo(self, _=None) -> None:
        serializados = [p for p in (self.pedir(lambda: self.api.productos(limite=300), []) or [])
                        if p.get("requiere_imei")]
        producto = ui.lista("Producto", [(p["id"], f"{p['sku']} · {p['nombre']}")
                                         for p in serializados])
        imei = ui.campo("IMEI (15 digitos)", pista="356789012345045")
        imei2 = ui.campo("IMEI 2 (opcional)")
        rfid = ui.campo("Codigo RFID (opcional)")
        color = ui.campo("Color")
        capacidad = ui.campo("Almacenamiento GB", teclado=ft.KeyboardType.NUMBER)
        costo = ui.campo("Costo", "0", teclado=ft.KeyboardType.NUMBER)

        def guardar(_e=None):
            if not producto.value:
                self.ctx.aviso("Elige el producto al que pertenece el equipo.", "alerta")
                return
            cuerpo = {
                "producto_id": int(producto.value),
                "imei": (imei.value or "").strip(),
                "imei2": (imei2.value or "").strip() or None,
                "codigo_rfid": (rfid.value or "").strip() or None,
                "color": (color.value or "").strip() or None,
                "almacenamiento_gb": int(capacidad.value) if (capacidad.value or "").strip() else None,
                "costo": (costo.value or "0").strip(),
            }
            self.ctx.cerrar()
            self.seguro(lambda: self.api.ingresar_equipo(cuerpo),
                        f"Equipo {cuerpo['imei']} ingresado al inventario.")

        cuerpo = ft.Column(
            [
                producto,
                ft.Row([imei, imei2], spacing=10),
                ft.Row([rfid, color, capacidad], spacing=10),
                costo,
                ui.aviso("El IMEI se valida con el algoritmo de Luhn en la interfaz, "
                         "en la API y en PostgreSQL.", "acento"),
            ],
            spacing=12, tight=True,
        )
        self.ctx.abrir(self.dialogo("Ingresar equipo", cuerpo, "Ingresar", guardar,
                                    ancho=620))

    def _dialogo_estado(self, equipo: dict) -> None:
        nuevo = ui.lista("Nuevo estado", [(e, e.replace("_", " ").title())
                                          for e in ESTADOS_IMEI],
                         valor=equipo["estado"])
        motivo = ui.campo("Motivo")

        def guardar(_e=None):
            if not nuevo.value:
                self.ctx.aviso("Elige el nuevo estado.", "alerta")
                return
            if len((motivo.value or "").strip()) < 3:
                self.ctx.aviso("Escribe el motivo del cambio.", "alerta")
                return
            self.ctx.cerrar()
            self.seguro(
                lambda: self.api.cambiar_estado_equipo(equipo["imei"], nuevo.value,
                                                       motivo.value.strip()),
                f"El equipo {equipo['imei']} quedo en estado {nuevo.value}.")

        cuerpo = ft.Column([ui.aviso(f"IMEI {equipo['imei']} · estado actual "
                                     f"{equipo['estado']}", "acento"), nuevo, motivo],
                           spacing=12, tight=True)
        self.ctx.abrir(self.dialogo("Cambiar estado del equipo", cuerpo, "Cambiar",
                                    guardar))

    def _dialogo_trazabilidad(self, equipo: dict) -> None:
        t = self.pedir(lambda: self.api.trazabilidad(equipo["imei"]), {}) or {}
        if not t:
            return

        def linea(etiqueta: str, valor: str) -> ft.Row:
            return ft.Row(
                [ft.Text(etiqueta, size=12, color=T.TEXTO_TENUE, width=150),
                 ft.Text(valor, size=12, color=T.TEXTO, expand=True)],
                spacing=8,
            )

        cuerpo = ft.Column(
            [
                linea("IMEI", t.get("imei", "—")),
                linea("Producto", t.get("producto") or "—"),
                linea("Estado del equipo", t.get("estado") or "—"),
                linea("Ingreso al inventario", ui.fecha_hora(t.get("fecha_ingreso"))),
                ft.Container(height=1, bgcolor=T.BORDE),
                linea("Factura", t.get("factura") or "sin vender"),
                linea("Fecha de venta", ui.fecha_hora(t.get("fecha_venta"))),
                linea("Cliente", t.get("cliente") or "—"),
                ft.Container(height=1, bgcolor=T.BORDE),
                linea("Garantia hasta", ui.fecha(t.get("garantia_hasta"))),
                linea("Estado de garantia", t.get("estado_garantia") or "—"),
            ],
            spacing=8, tight=True,
        )
        dlg = ft.AlertDialog(
            modal=True,
            title=ui.titulo("Trazabilidad del equipo", 16),
            content=ft.Container(content=cuerpo, width=520),
            actions=[ui.boton("Cerrar", self.ctx.cerrar, tono="neutro")],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.ctx.abrir(dlg)
