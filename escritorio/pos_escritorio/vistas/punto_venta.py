"""Punto de venta: buscar, armar la factura, cobrar.

Es la unica vista con estado propio (el carrito y los pagos), por eso construye
los controles una vez y los modifica en el sitio en lugar de volver a dibujar
todo con cada clic: asi no se pierde el foco ni lo que ya se habia agregado.

El calculo del dinero se repite aqui con `Decimal` y redondeo medio hacia arriba
exactamente como en `backend/app/dinero.py`. No es duplicar la regla por gusto:
el backend exige que los pagos sumen el total al centavo, asi que el cliente
tiene que llegar a la misma cifra. La version que manda es siempre la del
servidor; esta solo sirve para mostrar y para cuadrar el cobro.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

import flet as ft

from .. import tema as T
from .. import ui
from ..api import ErrorApi
from .base import Vista

METODOS = ["EFECTIVO", "DEBITO", "CREDITO", "TRANSFERENCIA", "NEQUI", "DAVIPLATA"]


def dinero(valor) -> Decimal:
    """Dos decimales, medio hacia arriba. Igual que `backend/app/dinero.py`."""
    return Decimal(str(valor or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class Linea:
    """Una linea de la factura en construccion."""

    def __init__(self, producto: dict, cantidad: int = 1, imei: str | None = None):
        self.producto = producto
        self.cantidad = cantidad
        self.imei = imei
        self.descuento = Decimal("0")

    @property
    def precio(self) -> Decimal:
        return dinero(self.producto.get("precio_venta"))

    @property
    def bruto(self) -> Decimal:
        return dinero(self.precio * self.cantidad)

    @property
    def base(self) -> Decimal:
        return dinero(self.bruto - self.descuento)

    @property
    def iva(self) -> Decimal:
        return dinero(self.base * dinero(self.producto.get("iva_porcentaje")) / 100)

    @property
    def total(self) -> Decimal:
        return dinero(self.base + self.iva)

    def a_json(self) -> dict:
        cuerpo: dict = {"producto_id": self.producto["id"], "cantidad": self.cantidad,
                        "descuento": str(self.descuento)}
        if self.imei:
            cuerpo["imei"] = self.imei
        return cuerpo


class PuntoVenta(Vista):
    titulo = "Punto de venta"
    icono = ft.Icons.POINT_OF_SALE
    permisos = ("ventas.crear",)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.lineas: list[Linea] = []
        self.pagos: list[tuple[str, Decimal]] = []
        self.cliente_id: int | None = None
        self.productos: list[dict] = []
        self.clientes: list[dict] = []

    # -- construccion -------------------------------------------------------

    def construir(self) -> ft.Control:
        turno = self.pedir(self.api.turno)
        self.clientes = self.pedir(lambda: self.api.clientes(limite=300), []) or []
        self.productos = self.pedir(lambda: self.api.productos(limite=300), []) or []

        self.buscador = ui.campo(
            "Buscar por SKU, nombre o codigo de barras",
            icono=ft.Icons.SEARCH, al_enviar=self._buscar,
        )
        self.catalogo = ft.Column(spacing=6, scroll=ft.ScrollMode.AUTO, expand=True)
        self.carrito = ft.Column(spacing=8, scroll=ft.ScrollMode.AUTO, expand=True)
        self.resumen = ft.Column(spacing=6)
        self.lista_pagos = ft.Column(spacing=6)

        self.selector_cliente = ui.lista(
            "Cliente",
            [("", "Consumidor final")]
            + [(c["id"], f"{ui.nombre_cliente(c)} · {c['numero_documento']}")
               for c in self.clientes],
            valor="" if self.cliente_id is None else self.cliente_id,
            al_elegir=self._elegir_cliente,
        )
        self.metodo = ui.lista("Metodo de pago", [(m, m.title()) for m in METODOS],
                               valor="EFECTIVO", ancho=170)
        self.valor_pago = ui.campo("Valor", ancho=150, teclado=ft.KeyboardType.NUMBER)
        self.observaciones = ui.campo("Observaciones (opcional)")

        self._pintar_catalogo()
        self._pintar_carrito()

        if not turno:
            encabezado_aviso = ui.aviso(
                "No hay turno de caja abierto. Abre un turno en Caja antes de facturar.",
                "alerta",
            )
        else:
            caja = next((c for c in (self.pedir(self.api.cajas, []) or [])
                         if c["id"] == turno["caja_id"]), {})
            encabezado_aviso = ui.aviso(
                f"Turno abierto en {caja.get('nombre', 'caja')} desde "
                f"{ui.fecha_hora(turno['apertura'])} · base {ui.pesos(turno['base_inicial'])}",
                "exito",
            )

        izquierda = ui.panel(
            ft.Column([self.buscador, ft.Container(height=1, bgcolor=T.BORDE),
                       self.catalogo], spacing=10, expand=True),
            "Catalogo",
            [ui.boton("Limpiar", self._limpiar_busqueda, ft.Icons.CLEAR, "neutro")],
            expandir=True,
        )

        derecha = ui.panel(
            ft.Column(
                [
                    self.selector_cliente,
                    ft.Container(height=1, bgcolor=T.BORDE),
                    self.carrito,
                    ft.Container(height=1, bgcolor=T.BORDE),
                    self.resumen,
                    ft.Row([self.metodo, self.valor_pago,
                            ui.icono_boton(ft.Icons.ADD, self._agregar_pago,
                                           "Agregar este pago", T.ACENTO)],
                           spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self.lista_pagos,
                    self.observaciones,
                    ui.boton("Registrar venta", self._registrar,
                             ft.Icons.CHECK_CIRCLE, "exito"),
                ],
                spacing=10,
                expand=True,
            ),
            "Factura",
            [ui.boton("Vaciar", self._vaciar, ft.Icons.DELETE_OUTLINE, "neutro")],
            expandir=True,
        )

        return ft.Column(
            [
                self.encabezado("Arma la factura, elige el medio de pago y registra la venta."),
                encabezado_aviso,
                ft.Row([ft.Container(content=izquierda, expand=3),
                        ft.Container(content=derecha, expand=2)],
                       spacing=12, expand=True,
                       vertical_alignment=ft.CrossAxisAlignment.STRETCH),
            ],
            spacing=14,
            expand=True,
        )

    # -- catalogo -----------------------------------------------------------

    def _buscar(self, _=None) -> None:
        texto = (self.buscador.value or "").strip()
        self.productos = self.pedir(
            lambda: self.api.productos(q=texto or None, limite=300), []) or []
        self._pintar_catalogo()
        self.ctx.page.update()

    def _limpiar_busqueda(self, _=None) -> None:
        self.buscador.value = ""
        self._buscar()

    def _pintar_catalogo(self) -> None:
        self.catalogo.controls = []
        if not self.productos:
            self.catalogo.controls.append(ui.vacio("Ningun producto coincide"))
            return
        for p in self.productos:
            disponibles = int(p.get("disponibles") or 0)
            agotado = disponibles <= 0
            self.catalogo.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Column(
                                [
                                    ft.Text(p["nombre"], size=13,
                                            weight=ft.FontWeight.W_600, color=T.TEXTO,
                                            max_lines=1, overflow=ft.TextOverflow.ELLIPSIS),
                                    ft.Row(
                                        [
                                            ft.Text(p["sku"], size=11, color=T.TEXTO_TENUE),
                                            ui.insignia("IMEI" if p["requiere_imei"] else "STOCK",
                                                        "acento" if p["requiere_imei"] else "neutro"),
                                            ft.Text(f"{disponibles} disponibles", size=11,
                                                    color=T.PELIGRO if agotado else T.TEXTO_TENUE),
                                        ],
                                        spacing=8,
                                    ),
                                ],
                                spacing=3,
                                expand=True,
                            ),
                            ft.Column(
                                [
                                    ft.Text(ui.pesos(p["precio_venta"]), size=13,
                                            weight=ft.FontWeight.W_700, color=T.TEXTO),
                                    ft.Text(f"IVA {int(float(p['iva_porcentaje']))}%",
                                            size=10, color=T.TEXTO_TENUE),
                                ],
                                spacing=1,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                            ),
                            ui.icono_boton(
                                ft.Icons.ADD_SHOPPING_CART,
                                (lambda e, prod=p: self._agregar(prod)) if not agotado else None,
                                "Agregar a la factura" if not agotado else "Sin existencias",
                                T.BORDE_FUERTE if agotado else T.ACENTO,
                            ),
                        ],
                        spacing=10,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    bgcolor=T.PANEL_SUAVE if not agotado else T.PANEL,
                    border=ft.Border.all(1, T.BORDE),
                    border_radius=T.RADIO_SM,
                    padding=ft.Padding.symmetric(vertical=9, horizontal=12),
                )
            )

    # -- carrito ------------------------------------------------------------

    def _agregar(self, producto: dict) -> None:
        if producto["requiere_imei"]:
            self._elegir_imei(producto)
            return
        existente = next((l for l in self.lineas
                          if l.producto["id"] == producto["id"] and not l.imei), None)
        disponibles = int(producto.get("disponibles") or 0)
        if existente:
            if existente.cantidad + 1 > disponibles:
                self.ctx.aviso(f"Solo hay {disponibles} unidades de "
                               f"'{producto['nombre']}'.", "alerta")
                return
            existente.cantidad += 1
        else:
            self.lineas.append(Linea(producto))
        self._pintar_carrito()
        self.ctx.page.update()

    def _elegir_imei(self, producto: dict) -> None:
        """Un equipo serializado se vende por unidad: hay que decir cual."""
        libres = self.pedir(
            lambda: self.api.equipos(producto_id=producto["id"], estado="DISPONIBLE"),
            [],
        ) or []
        ya = {l.imei for l in self.lineas if l.imei}
        libres = [e for e in libres if e["imei"] not in ya]
        if not libres:
            self.ctx.aviso(f"No quedan equipos disponibles de '{producto['nombre']}'.",
                           "alerta")
            return

        def tomar(imei: str):
            def _(_e=None):
                self.lineas.append(Linea(producto, 1, imei))
                self.ctx.cerrar()
                self._pintar_carrito()
                self.ctx.page.update()
            return _

        filas = [
            [
                ft.Text(e["imei"], size=12, weight=ft.FontWeight.W_600, color=T.TEXTO),
                e.get("color") or "—",
                f"{e['almacenamiento_gb']} GB" if e.get("almacenamiento_gb") else "—",
                ui.boton("Elegir", tomar(e["imei"]), ft.Icons.CHECK, "acento"),
            ]
            for e in libres
        ]
        dlg = ft.AlertDialog(
            modal=True,
            title=ui.titulo(f"IMEI disponibles · {producto['nombre']}", 16),
            content=ft.Container(
                content=ui.tabla(["IMEI", "Color", "Capacidad", ""], filas, alto=320),
                width=560,
            ),
            actions=[ui.boton("Cancelar", self.ctx.cerrar, tono="neutro")],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=ft.Colors.WHITE,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.ctx.abrir(dlg)

    def _quitar(self, linea: Linea) -> None:
        self.lineas.remove(linea)
        self._pintar_carrito()
        self.ctx.page.update()

    def _cambiar_cantidad(self, linea: Linea, delta: int) -> None:
        nueva = linea.cantidad + delta
        disponibles = int(linea.producto.get("disponibles") or 0)
        if nueva < 1:
            return
        if nueva > disponibles:
            self.ctx.aviso(f"Solo hay {disponibles} unidades disponibles.", "alerta")
            return
        linea.cantidad = nueva
        self._pintar_carrito()
        self.ctx.page.update()

    def _cambiar_descuento(self, linea: Linea, texto: str) -> None:
        try:
            valor = dinero(texto.replace(".", "").replace(",", ".") or 0)
        except Exception:
            return
        linea.descuento = valor if 0 <= valor <= linea.bruto else Decimal("0")
        self._pintar_carrito()
        self.ctx.page.update()

    def _vaciar(self, _=None) -> None:
        self.lineas.clear()
        self.pagos.clear()
        self._pintar_carrito()
        self.ctx.page.update()

    def _pintar_carrito(self) -> None:
        self.carrito.controls = []
        if not self.lineas:
            self.carrito.controls.append(ui.vacio("La factura esta vacia"))
        for linea in self.lineas:
            detalle = [ft.Text(linea.producto["sku"], size=11, color=T.TEXTO_TENUE)]
            if linea.imei:
                detalle.append(ft.Text(f"IMEI {linea.imei}", size=11, color=T.ACENTO))
            controles_cantidad: list[ft.Control] = []
            if not linea.imei:
                controles_cantidad = [
                    ui.icono_boton(ft.Icons.REMOVE,
                                   lambda e, l=linea: self._cambiar_cantidad(l, -1),
                                   "Quitar una"),
                    ft.Text(str(linea.cantidad), size=13, weight=ft.FontWeight.W_600,
                            color=T.TEXTO),
                    ui.icono_boton(ft.Icons.ADD,
                                   lambda e, l=linea: self._cambiar_cantidad(l, 1),
                                   "Agregar una"),
                ]
            descuento = ui.campo("Descuento", str(int(linea.descuento)), ancho=110,
                                 teclado=ft.KeyboardType.NUMBER)
            descuento.on_blur = lambda e, l=linea: self._cambiar_descuento(l, e.control.value or "0")

            self.carrito.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Column(
                                        [ft.Text(linea.producto["nombre"], size=13,
                                                 weight=ft.FontWeight.W_600, color=T.TEXTO,
                                                 max_lines=2,
                                                 overflow=ft.TextOverflow.ELLIPSIS),
                                         ft.Row(detalle, spacing=8)],
                                        spacing=3, expand=True,
                                    ),
                                    ui.icono_boton(ft.Icons.DELETE_OUTLINE,
                                                   lambda e, l=linea: self._quitar(l),
                                                   "Quitar linea", T.PELIGRO),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
                            ft.Row(
                                controles_cantidad + [
                                    ft.Container(expand=True),
                                    descuento,
                                    ft.Column(
                                        [ft.Text(ui.pesos(linea.total), size=13,
                                                 weight=ft.FontWeight.W_700, color=T.TEXTO),
                                         ft.Text(f"IVA {ui.pesos(linea.iva)}", size=10,
                                                 color=T.TEXTO_TENUE)],
                                        spacing=1,
                                        horizontal_alignment=ft.CrossAxisAlignment.END,
                                    ),
                                ],
                                spacing=8,
                                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            ),
                        ],
                        spacing=6,
                    ),
                    bgcolor=T.PANEL_SUAVE,
                    border=ft.Border.all(1, T.BORDE),
                    border_radius=T.RADIO_SM,
                    padding=10,
                )
            )
        self._pintar_resumen()

    # -- dinero -------------------------------------------------------------

    @property
    def subtotal(self) -> Decimal:
        return dinero(sum((l.base for l in self.lineas), Decimal("0")))

    @property
    def iva_total(self) -> Decimal:
        return dinero(sum((l.iva for l in self.lineas), Decimal("0")))

    @property
    def total(self) -> Decimal:
        return dinero(self.subtotal + self.iva_total)

    @property
    def pagado(self) -> Decimal:
        return dinero(sum((v for _, v in self.pagos), Decimal("0")))

    def _pintar_resumen(self) -> None:
        saldo = dinero(self.total - self.pagado)
        def fila(etiqueta: str, valor: str, fuerte: bool = False) -> ft.Row:
            return ft.Row(
                [
                    ft.Text(etiqueta, size=13 if not fuerte else 15,
                            color=T.TEXTO_MEDIO if not fuerte else T.TEXTO,
                            weight=ft.FontWeight.W_600 if fuerte else ft.FontWeight.NORMAL),
                    ft.Text(valor, size=13 if not fuerte else 19,
                            weight=ft.FontWeight.W_700 if fuerte else ft.FontWeight.W_600,
                            color=T.TEXTO),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            )
        self.resumen.controls = [
            fila("Subtotal", ui.pesos(self.subtotal, True)),
            fila("IVA", ui.pesos(self.iva_total, True)),
            fila("Total", ui.pesos(self.total, True), True),
        ]
        if self.pagos:
            self.resumen.controls.append(
                fila("Saldo por cobrar", ui.pesos(saldo, True))
            )
        self._pintar_pagos()

    def _pintar_pagos(self) -> None:
        self.lista_pagos.controls = []
        for i, (metodo, valor) in enumerate(self.pagos):
            self.lista_pagos.controls.append(
                ft.Row(
                    [
                        ui.insignia(metodo, "acento"),
                        ft.Text(ui.pesos(valor, True), size=12, color=T.TEXTO,
                                expand=True),
                        ui.icono_boton(ft.Icons.CLOSE,
                                       lambda e, k=i: self._quitar_pago(k),
                                       "Quitar pago", T.PELIGRO),
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                )
            )

    def _agregar_pago(self, _=None) -> None:
        if not self.lineas:
            self.ctx.aviso("Agrega productos antes de registrar un pago.", "alerta")
            return
        crudo = (self.valor_pago.value or "").replace(".", "").replace(",", ".").strip()
        saldo = dinero(self.total - self.pagado)
        valor = dinero(crudo) if crudo else saldo
        if valor <= 0:
            self.ctx.aviso("El valor del pago debe ser mayor que cero.", "alerta")
            return
        if valor > saldo:
            self.ctx.aviso(f"El pago excede el saldo por cobrar ({ui.pesos(saldo, True)}).",
                           "alerta")
            return
        self.pagos.append((self.metodo.value or "EFECTIVO", valor))
        self.valor_pago.value = ""
        self._pintar_resumen()
        self.ctx.page.update()

    def _quitar_pago(self, indice: int) -> None:
        del self.pagos[indice]
        self._pintar_resumen()
        self.ctx.page.update()

    def _elegir_cliente(self, e) -> None:
        valor = self.selector_cliente.value
        self.cliente_id = int(valor) if valor else None

    # -- registro -----------------------------------------------------------

    def _registrar(self, _=None) -> None:
        if not self.lineas:
            self.ctx.aviso("La factura esta vacia.", "alerta")
            return
        pagos = list(self.pagos)
        if not pagos:
            # Caso normal del mostrador: un solo medio de pago por el total.
            pagos = [(self.metodo.value or "EFECTIVO", self.total)]
        if dinero(sum(v for _, v in pagos)) != self.total:
            self.ctx.aviso(
                f"Los pagos suman {ui.pesos(sum(v for _, v in pagos), True)} y el total "
                f"es {ui.pesos(self.total, True)}.", "alerta")
            return

        cuerpo = {
            "cliente_id": self.cliente_id,
            "observaciones": (self.observaciones.value or "").strip() or None,
            "items": [l.a_json() for l in self.lineas],
            "pagos": [{"metodo": m, "valor": str(v)} for m, v in pagos],
        }
        try:
            venta = self.api.registrar_venta(cuerpo)
        except ErrorApi as e:
            self.ctx.aviso(e.mensaje, "peligro")
            return
        # El carrito se limpia antes de redibujar; si se hiciera al contrario, la
        # vista se reconstruiria todavia con la factura que ya se registro.
        self.lineas.clear()
        self.pagos.clear()
        self.cliente_id = None
        self.ctx.aviso(
            f"Venta {venta['numero']} registrada por {ui.pesos(venta['total'], True)}.",
            "exito",
        )
        self.ctx.refrescar()
