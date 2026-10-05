"""Prueba de la aplicacion de escritorio sin abrir una ventana.

Una interfaz grafica se puede probar de verdad sin pintarla: lo que falla en la
practica no es el dibujo, es el arbol de controles mal construido (un parametro
que Flet ya no acepta, una clave que la API no devuelve, un `None` donde se
esperaba una lista). Eso se detecta armando el arbol.

La prueba:

  1. entra con cada rol real contra el backend y PostgreSQL de verdad;
  2. construye todas las vistas que ese rol puede ver;
  3. recorre el arbol resultante y cuenta controles, para que una vista que
     devuelva un contenedor vacio no pase por buena;
  4. comprueba el filtrado por permisos (el cajero no debe ver Usuarios);
  5. ejercita el carrito del punto de venta: agregar, cantidad, descuento,
     pagos y totales, comparando el total con el que calcula el backend.

Uso:  python pruebas.py  [http://127.0.0.1:8000/api]
"""

from __future__ import annotations

import sys
import traceback
from decimal import Decimal

import flet as ft

from pos_escritorio.aplicacion import Aplicacion
from pos_escritorio.api import Api, ErrorApi
from pos_escritorio.vistas import REGISTRO
from pos_escritorio.vistas.punto_venta import Linea, dinero

SERVIDOR = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"

# Los modulos que cada rol debe ver salen de la tabla `rol_permisos`, no de una
# lista escrita a mano en el codigo. Estos conjuntos son el contrato: si alguien
# cambia los permisos en la base, esta prueba lo dice.
CUENTAS = [
    ("admin", "admin123", {"tablero", "punto-venta", "ventas", "caja", "inventario",
                           "clientes", "garantias", "usuarios"}),
    ("cajero", "cajero123", {"punto-venta", "ventas", "caja", "clientes", "garantias"}),
    ("bodega", "bodega123", {"tablero", "inventario", "clientes"}),
    ("tecnico", "tecnico123", {"clientes", "garantias", "inventario"}),
]

fallos: list[str] = []
pasos = 0


def verificar(condicion: bool, descripcion: str) -> None:
    global pasos
    pasos += 1
    if condicion:
        print(f"  ok    {descripcion}")
    else:
        fallos.append(descripcion)
        print(f"  FALLA {descripcion}")


class PaginaSimulada:
    """Lo minimo de `ft.Page` que las vistas tocan mientras se construyen.

    Las vistas solo llaman `update()` y las propiedades de ventana; nada que
    necesite un proceso de Flutter al otro lado.
    """

    def __init__(self):
        self.controls: list = []
        self.window = type("Ventana", (), {})()
        self.dialogos: list = []
        self.actualizaciones = 0
        self.title = ""
        self.theme = None
        self.theme_mode = None
        self.bgcolor = None
        self.padding = None

    def update(self, *_a, **_k) -> None:
        self.actualizaciones += 1

    def show_dialog(self, dialogo) -> None:
        self.dialogos.append(dialogo)

    def pop_dialog(self, *_a) -> None:
        if self.dialogos:
            self.dialogos.pop()


def contar(control, profundidad: int = 0) -> int:
    """Cuenta los controles del arbol. Sirve para detectar vistas vacias."""
    if profundidad > 60 or control is None:
        return 0
    total = 1
    for atributo in ("controls", "rows", "columns", "actions", "cells", "tabs"):
        hijos = getattr(control, atributo, None)
        if isinstance(hijos, (list, tuple)):
            for h in hijos:
                total += contar(h, profundidad + 1)
    for atributo in ("content", "leading", "trailing", "title", "label"):
        hijo = getattr(control, atributo, None)
        if isinstance(hijo, ft.BaseControl):
            total += contar(hijo, profundidad + 1)
    return total


# ---------------------------------------------------------------------------
# 1. El servidor responde
# ---------------------------------------------------------------------------
print("\n=== 1. Conexion con el backend ===")
sonda = Api(SERVIDOR)
try:
    salud = sonda.salud()
    verificar(salud.get("estado") == "ok", f"el servidor responde ({SERVIDOR})")
    verificar(salud.get("tablas") == 37, f"PostgreSQL tiene 37 tablas (tiene {salud.get('tablas')})")
except ErrorApi as e:
    print(f"  FALLA no hay backend: {e.mensaje}")
    print("\n  Levanta la API antes de correr esta prueba:")
    print("    python -m uvicorn app.main:app --port 8000   (desde la carpeta backend)")
    sys.exit(1)


# ---------------------------------------------------------------------------
# 2. Ingreso, menu por permisos y construccion de todas las vistas
# ---------------------------------------------------------------------------
for usuario, clave, esperadas in CUENTAS:
    print(f"\n=== 2. Rol '{usuario}' ===")
    pagina = PaginaSimulada()
    app = Aplicacion(pagina, SERVIDOR)

    try:
        app.api.entrar(usuario, clave)
    except ErrorApi as e:
        verificar(False, f"{usuario}: ingreso ({e.mensaje})")
        continue
    verificar(True, f"{usuario}: ingreso correcto como {app.api.rol}")

    disponibles = {c for c, _g, cl in REGISTRO
                   if not cl.permisos or app.api.puede(*cl.permisos)}
    verificar(
        disponibles == esperadas,
        f"{usuario}: ve exactamente sus modulos "
        f"({', '.join(sorted(disponibles))})",
    )

    app.mostrar_principal()
    verificar(pagina.controls != [], f"{usuario}: la ventana principal se dibuja")

    for clave in sorted(disponibles):
        vista = app.vistas[clave]
        try:
            arbol = vista.construir()
            nodos = contar(arbol)
        except Exception:
            verificar(False, f"{usuario}: vista '{clave}' se construye")
            traceback.print_exc(limit=6)
            continue
        verificar(nodos > 12,
                  f"{usuario}: vista '{clave}' se construye ({nodos} controles)")

    # Pestanas internas: cada una consulta cosas distintas de la API.
    if "inventario" in disponibles:
        v = app.vistas["inventario"]
        for pestana, nombre in ((0, "productos"), (1, "equipos")):
            v.pestana = pestana
            try:
                nodos = contar(v.construir())
                verificar(nodos > 12,
                          f"{usuario}: inventario/{nombre} ({nodos} controles)")
            except Exception:
                verificar(False, f"{usuario}: inventario/{nombre}")
                traceback.print_exc(limit=6)
        v.pestana = 0

    if "garantias" in disponibles:
        v = app.vistas["garantias"]
        for pestana, nombre in ((0, "garantias"), (1, "servicio"), (2, "apartados")):
            v.pestana = pestana
            try:
                nodos = contar(v.construir())
                verificar(nodos > 10, f"{usuario}: garantias/{nombre} ({nodos} controles)")
            except Exception:
                verificar(False, f"{usuario}: garantias/{nombre}")
                traceback.print_exc(limit=6)
        v.pestana = 0

    if "usuarios" in disponibles:
        v = app.vistas["usuarios"]
        for pestana, nombre in ((0, "usuarios"), (1, "permisos")):
            v.pestana = pestana
            try:
                nodos = contar(v.construir())
                verificar(nodos > 20, f"{usuario}: usuarios/{nombre} ({nodos} controles)")
            except Exception:
                verificar(False, f"{usuario}: usuarios/{nombre}")
                traceback.print_exc(limit=6)
        v.pestana = 0

    # Los dialogos tambien son arbol de controles y es donde suele romperse.
    if "clientes" in disponibles:
        v = app.vistas["clientes"]
        v.construir()
        antes = len(pagina.dialogos)
        try:
            v._dialogo()
            verificar(len(pagina.dialogos) == antes + 1 and contar(pagina.dialogos[-1]) > 20,
                      f"{usuario}: dialogo de nuevo cliente")
            app.cerrar()
        except Exception:
            verificar(False, f"{usuario}: dialogo de nuevo cliente")
            traceback.print_exc(limit=6)

    if "ventas" in disponibles:
        v = app.vistas["ventas"]
        v.construir()
        ventas = app.api.ventas(limite=1)
        if ventas:
            try:
                v._dialogo_detalle(ventas[0])
                verificar(contar(pagina.dialogos[-1]) > 30,
                          f"{usuario}: dialogo de detalle de factura")
                app.cerrar()
            except Exception:
                verificar(False, f"{usuario}: dialogo de detalle de factura")
                traceback.print_exc(limit=6)

    if "caja" in disponibles and app.api.puede("caja.movimiento"):
        v = app.vistas["caja"]
        v.construir()
        try:
            v._dialogo_movimiento()
            verificar(contar(pagina.dialogos[-1]) > 8,
                      f"{usuario}: dialogo de movimiento de caja")
            app.cerrar()
        except Exception:
            verificar(False, f"{usuario}: dialogo de movimiento de caja")
            traceback.print_exc(limit=6)

    # Navegacion: cambiar de modulo no debe dejar la ventana en blanco.
    for clave in sorted(disponibles):
        app.ir_a(clave)
        verificar(app.actual == clave and app.contenido.content is not None,
                  f"{usuario}: navega a '{clave}'")

    app._salir()
    verificar(app.api.token is None, f"{usuario}: cierra sesion")


# ---------------------------------------------------------------------------
# 3. El carrito del punto de venta
# ---------------------------------------------------------------------------
print("\n=== 3. Carrito del punto de venta ===")
pagina = PaginaSimulada()
app = Aplicacion(pagina, SERVIDOR)
app.api.entrar("admin", "admin123")
app.mostrar_principal()

# Sin turno abierto el backend rechaza la venta antes de mirar los pagos, asi que
# el turno se abre aqui: lo que se quiere comprobar es el calculo del dinero.
if not app.api.turno():
    libres = [c for c in app.api.cajas() if c.get("activa") and not c.get("ocupada")]
    if libres:
        app.api.abrir_turno(libres[0]["id"], 100000)
verificar(app.api.turno() is not None, "hay turno de caja abierto para las pruebas")
pos = app.vistas["punto-venta"]
pos.construir()

accesorio = next((p for p in pos.productos
                  if not p["requiere_imei"] and int(p.get("disponibles") or 0) >= 3), None)
serializado = next((p for p in pos.productos
                    if p["requiere_imei"] and int(p.get("disponibles") or 0) >= 1), None)
verificar(accesorio is not None, "hay un accesorio con existencias para la prueba")
verificar(serializado is not None, "hay un equipo con IMEI disponible para la prueba")

if accesorio:
    pos._agregar(accesorio)
    verificar(len(pos.lineas) == 1 and pos.lineas[0].cantidad == 1,
              "agregar un accesorio crea una linea")
    pos._agregar(accesorio)
    verificar(len(pos.lineas) == 1 and pos.lineas[0].cantidad == 2,
              "agregarlo otra vez suma cantidad en la misma linea")
    pos._cambiar_cantidad(pos.lineas[0], 1)
    verificar(pos.lineas[0].cantidad == 3, "el boton de cantidad sube a 3")
    pos._cambiar_cantidad(pos.lineas[0], -5)
    verificar(pos.lineas[0].cantidad == 3, "no deja bajar por debajo de 1")

    # Tope por existencias: pedir mas de lo que hay no debe entrar al carrito.
    tope = int(accesorio.get("disponibles") or 0)
    pos.lineas[0].cantidad = tope
    pos._cambiar_cantidad(pos.lineas[0], 1)
    verificar(pos.lineas[0].cantidad == tope,
              f"no deja pasar de las {tope} unidades disponibles")
    pos.lineas[0].cantidad = 2

    linea = pos.lineas[0]
    precio = dinero(accesorio["precio_venta"])
    iva_pct = dinero(accesorio["iva_porcentaje"])
    esperado_base = dinero(precio * 2)
    esperado_iva = dinero(esperado_base * iva_pct / 100)
    verificar(linea.base == esperado_base, "la base de la linea cuadra")
    verificar(linea.iva == esperado_iva, "el IVA de la linea cuadra")
    verificar(linea.total == dinero(esperado_base + esperado_iva),
              "el total de la linea cuadra")

    pos._cambiar_descuento(linea, "1000")
    verificar(linea.descuento == Decimal("1000.00"), "aplica el descuento")
    verificar(linea.base == dinero(esperado_base - 1000),
              "el descuento baja la base gravable")
    pos._cambiar_descuento(linea, str(int(linea.bruto) + 50000))
    verificar(linea.descuento == Decimal("0"),
              "rechaza un descuento mayor que el valor de la linea")

if serializado:
    libres = app.api.equipos(producto_id=serializado["id"], estado="DISPONIBLE")
    verificar(bool(libres), "la API devuelve los IMEI disponibles del producto")
    antes = len(pagina.dialogos)
    pos._elegir_imei(serializado)
    verificar(len(pagina.dialogos) == antes + 1,
              "el equipo serializado abre el selector de IMEI")
    app.cerrar()
    pos.lineas.append(Linea(serializado, 1, libres[0]["imei"]))
    verificar(any(l.imei for l in pos.lineas), "la linea queda con su IMEI")

# Pagos
total = pos.total
verificar(total > 0, f"el total de la factura es {total}")
pos.metodo.value = "EFECTIVO"
pos.valor_pago.value = str(int(total / 2))
pos._agregar_pago()
verificar(len(pos.pagos) == 1, "registra un primer pago parcial")
pos.valor_pago.value = str(int(total * 2))
pos._agregar_pago()
verificar(len(pos.pagos) == 1, "rechaza un pago mayor que el saldo")
pos.metodo.value = "NEQUI"
pos.valor_pago.value = ""
pos._agregar_pago()
verificar(len(pos.pagos) == 2 and pos.pagado == total,
          "el segundo pago sin valor toma el saldo exacto")
verificar({m for m, _ in pos.pagos} == {"EFECTIVO", "NEQUI"},
          "quedan los dos medios de pago")

# El total calculado aqui tiene que ser el mismo que calcula el backend.
# Se comprueba contra la API sin registrar la venta: se manda un pago de menos y
# el servidor responde con el total que el calculo, que debe coincidir.
cuerpo = {
    "cliente_id": None,
    "items": [l.a_json() for l in pos.lineas],
    "pagos": [{"metodo": "EFECTIVO", "valor": "1"}],
}
try:
    app.api.registrar_venta(cuerpo)
    verificar(False, "el backend rechaza una venta con pagos que no cuadran")
except ErrorApi as e:
    verificar("suman" in e.mensaje,
              f"el backend rechaza pagos que no cuadran: {e.mensaje}")
    # El mensaje tiene la forma "Los pagos suman 1.00 y el total es 123.00".
    cifra = e.mensaje.rstrip(".").split()[-1]
    try:
        del_servidor = dinero(cifra)
    except Exception:
        verificar(False, f"no se pudo leer el total en el mensaje: {e.mensaje}")
    else:
        verificar(del_servidor == total,
                  f"el total del cliente ({total}) es el mismo del servidor ({cifra})")

pos._vaciar()
verificar(pos.lineas == [] and pos.pagos == [], "vaciar deja la factura limpia")


# ---------------------------------------------------------------------------
# 4. Una venta completa de punta a punta
# ---------------------------------------------------------------------------
print("\n=== 4. Venta completa desde la aplicacion ===")
turno = app.api.turno()
if not turno:
    libres = [c for c in app.api.cajas() if c.get("activa") and not c.get("ocupada")]
    if libres:
        app.api.abrir_turno(libres[0]["id"], 100000)
        turno = app.api.turno()
verificar(turno is not None, "hay un turno de caja abierto para facturar")

if turno:
    pos.construir()
    producto = next((p for p in pos.productos
                     if not p["requiere_imei"] and int(p.get("disponibles") or 0) >= 1), None)
    if producto:
        antes = len(app.api.ventas(limite=500))
        pos._agregar(producto)
        clientes = app.api.clientes(limite=1)
        pos.cliente_id = clientes[0]["id"] if clientes else None
        esperado = pos.total
        pos.metodo.value = "EFECTIVO"
        pos._registrar()
        verificar(pos.lineas == [], "el carrito queda vacio despues de registrar")
        ventas = app.api.ventas(limite=500)
        verificar(len(ventas) == antes + 1, "la venta quedo registrada en la base")
        if len(ventas) == antes + 1:
            ultima = max(ventas, key=lambda v: v["id"])
            verificar(dinero(ultima["total"]) == esperado,
                      f"el total guardado ({ultima['total']}) es el que mostro la "
                      f"aplicacion ({esperado})")
            verificar(ultima["estado"] == "COMPLETADA", "la venta quedo COMPLETADA")
            detalle = app.api.venta(ultima["id"])
            verificar(len(detalle.get("pagos") or []) == 1,
                      "la venta quedo con su pago registrado")
    else:
        verificar(False, "hay un producto con existencias para la venta de prueba")


# ---------------------------------------------------------------------------
print("\n" + "=" * 66)
if fallos:
    print(f"RESULTADO: {len(fallos)} de {pasos} comprobaciones fallaron\n")
    for f in fallos:
        print(f"  · {f}")
    sys.exit(1)
print(f"RESULTADO: {pasos} comprobaciones, todas correctas")
