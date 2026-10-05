"""Cliente HTTP del backend.

La aplicacion de escritorio no habla con PostgreSQL: habla con la misma API
FastAPI que usa la interfaz web. Asi las reglas de negocio (un IMEI no se vende
dos veces, no se vende sin turno de caja abierto, el IVA se calcula igual) viven
en un solo lugar y los dos clientes obedecen exactamente las mismas reglas.

Toda la capa de red esta encerrada aqui. Las vistas llaman metodos con nombre de
negocio (`api.ventas()`, `api.abrir_turno(...)`) y nunca construyen una URL.
"""

from __future__ import annotations

from typing import Any

import requests

TIEMPO_ESPERA = 20  # segundos; una consulta normal responde en milisegundos


class ErrorApi(Exception):
    """Fallo al hablar con el backend, ya traducido a algo legible.

    `codigo` es el estado HTTP cuando el servidor respondio, o 0 cuando no se
    pudo ni establecer la conexion.
    """

    def __init__(self, mensaje: str, codigo: int = 0):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class Api:
    """Sesion contra el backend: guarda el token, el usuario y sus permisos."""

    def __init__(self, base: str = "http://127.0.0.1:8000/api"):
        self.base = base.rstrip("/")
        self.sesion = requests.Session()
        self.token: str | None = None
        self.usuario: dict[str, Any] = {}
        self.permisos: set[str] = set()

    # -- infraestructura ----------------------------------------------------

    def _pedir(self, metodo: str, ruta: str, **kw) -> Any:
        cabeceras = dict(kw.pop("headers", {}))
        if self.token:
            cabeceras["Authorization"] = f"Bearer {self.token}"
        try:
            r = self.sesion.request(
                metodo, f"{self.base}{ruta}", headers=cabeceras,
                timeout=TIEMPO_ESPERA, **kw
            )
        except requests.exceptions.ConnectionError:
            raise ErrorApi(
                "No hay conexion con el servidor. Verifica que el backend este "
                f"encendido en {self.base.replace('/api', '')}."
            ) from None
        except requests.exceptions.Timeout:
            raise ErrorApi("El servidor tardo demasiado en responder.") from None

        if r.status_code == 204 or not r.content:
            return None
        if r.ok:
            return r.json()
        raise ErrorApi(self._mensaje_de_error(r), r.status_code)

    @staticmethod
    def _mensaje_de_error(r: requests.Response) -> str:
        """Convierte la respuesta de error de FastAPI en una sola frase.

        FastAPI devuelve `detail` como texto cuando es un `HTTPException` y como
        lista de errores cuando la validacion de Pydantic rechaza el cuerpo; hay
        que cubrir los dos casos.
        """
        try:
            detalle = r.json().get("detail")
        except ValueError:
            return f"Error {r.status_code} del servidor."
        if isinstance(detalle, str):
            return detalle
        if isinstance(detalle, list):
            partes = []
            for e in detalle:
                campo = ".".join(str(x) for x in e.get("loc", [])[1:]) or "dato"
                partes.append(f"{campo}: {e.get('msg', 'invalido')}")
            return " · ".join(partes)
        return f"Error {r.status_code} del servidor."

    def _get(self, ruta: str, **params) -> Any:
        limpios = {k: v for k, v in params.items() if v not in (None, "")}
        return self._pedir("GET", ruta, params=limpios)

    def _post(self, ruta: str, cuerpo: Any = None) -> Any:
        return self._pedir("POST", ruta, json=cuerpo)

    def _put(self, ruta: str, cuerpo: Any = None) -> Any:
        return self._pedir("PUT", ruta, json=cuerpo)

    def _patch(self, ruta: str, cuerpo: Any = None) -> Any:
        return self._pedir("PATCH", ruta, json=cuerpo)

    # -- sesion y permisos --------------------------------------------------

    def salud(self) -> dict:
        """Diagnostico publico: sirve para saber si el backend esta arriba."""
        return self._pedir("GET", "/salud")

    def entrar(self, usuario: str, clave: str) -> dict:
        """Inicia sesion. El login usa formulario porque es un OAuth2 estandar."""
        datos = self._pedir(
            "POST", "/auth/login", data={"username": usuario, "password": clave}
        )
        self.token = datos["access_token"]
        self.usuario = datos["usuario"]
        self.permisos = set(datos["permisos"])
        return datos

    def salir(self) -> None:
        self.token = None
        self.usuario = {}
        self.permisos = set()

    def puede(self, *codigos: str) -> bool:
        """True si el rol tiene al menos uno de los permisos indicados."""
        return bool(self.permisos & set(codigos))

    @property
    def nombre(self) -> str:
        return self.usuario.get("nombre_completo", "")

    @property
    def rol(self) -> str:
        return (self.usuario.get("rol") or {}).get("nombre", "")

    # -- tablero ------------------------------------------------------------

    def tablero(self) -> dict:
        return self._get("/reportes/dashboard")

    def ventas_por_dia(self, dias: int = 14) -> list[dict]:
        return self._get("/reportes/ventas-por-dia", dias=dias)

    def mas_vendidos(self, limite: int = 5, dias: int = 30) -> list[dict]:
        return self._get("/reportes/mas-vendidos", limite=limite, dias=dias)

    def alertas_stock(self) -> list[dict]:
        return self._get("/reportes/alertas-stock")

    def rentabilidad(self) -> list[dict]:
        return self._get("/reportes/rentabilidad")

    def trazabilidad(self, imei: str) -> dict:
        return self._get(f"/reportes/trazabilidad/{imei}")

    # -- catalogo e inventario ---------------------------------------------

    def productos(self, q: str | None = None, categoria_id: int | None = None,
                  solo_disponibles: bool | None = None, limite: int = 200) -> list[dict]:
        return self._get("/productos", q=q, categoria_id=categoria_id,
                         solo_disponibles=solo_disponibles, limite=limite)

    def producto(self, producto_id: int) -> dict:
        return self._get(f"/productos/{producto_id}")

    def crear_producto(self, datos: dict) -> dict:
        return self._post("/productos", datos)

    def ajustar_stock(self, producto_id: int, cantidad: int, motivo: str) -> dict:
        return self._post(f"/productos/{producto_id}/ajuste-stock",
                          {"cantidad": cantidad, "motivo": motivo})

    def kardex(self, producto_id: int, limite: int = 100) -> list[dict]:
        return self._get(f"/productos/{producto_id}/kardex", limite=limite)

    def categorias(self) -> list[dict]:
        return self._get("/categorias")

    def marcas(self) -> list[dict]:
        return self._get("/marcas")

    def equipos(self, producto_id: int | None = None, estado: str | None = None,
                q: str | None = None, limite: int = 200) -> list[dict]:
        return self._get("/inventario/imei", producto_id=producto_id,
                         estado=estado, q=q, limite=limite)

    def equipo(self, imei: str) -> dict:
        return self._get(f"/inventario/imei/{imei}")

    def ingresar_equipo(self, datos: dict) -> dict:
        return self._post("/inventario/imei", datos)

    def cambiar_estado_equipo(self, imei: str, estado: str, motivo: str) -> dict:
        return self._patch(f"/inventario/imei/{imei}/estado",
                           {"estado": estado, "motivo": motivo})

    # -- clientes -----------------------------------------------------------

    def clientes(self, q: str | None = None, limite: int = 200) -> list[dict]:
        return self._get("/clientes", q=q, limite=limite)

    def crear_cliente(self, datos: dict) -> dict:
        return self._post("/clientes", datos)

    def actualizar_cliente(self, cliente_id: int, datos: dict) -> dict:
        return self._put(f"/clientes/{cliente_id}", datos)

    def compras_cliente(self, cliente_id: int) -> list[dict]:
        return self._get(f"/clientes/{cliente_id}/compras")

    # -- ventas -------------------------------------------------------------

    def ventas(self, desde: str | None = None, hasta: str | None = None,
               estado: str | None = None, limite: int = 100) -> list[dict]:
        return self._get("/ventas", desde=desde, hasta=hasta,
                         estado=estado, limite=limite)

    def venta(self, venta_id: int) -> dict:
        return self._get(f"/ventas/{venta_id}")

    def factura(self, venta_id: int) -> dict:
        return self._get(f"/ventas/{venta_id}/factura")

    def registrar_venta(self, datos: dict) -> dict:
        return self._post("/ventas", datos)

    def anular_venta(self, venta_id: int, motivo: str) -> dict:
        return self._post(f"/ventas/{venta_id}/anular", {"motivo": motivo})

    # -- caja ---------------------------------------------------------------

    def cajas(self) -> list[dict]:
        return self._get("/caja/cajas")

    def turno(self) -> dict | None:
        return self._get("/caja/turno")

    def turnos(self, limite: int = 50) -> list[dict]:
        return self._get("/caja/turnos", limite=limite)

    def abrir_turno(self, caja_id: int, base_inicial: float) -> dict:
        return self._post("/caja/abrir",
                          {"caja_id": caja_id, "base_inicial": str(base_inicial)})

    def arqueo(self) -> dict:
        return self._get("/caja/arqueo")

    def cerrar_turno(self, efectivo_contado: float) -> dict:
        return self._post("/caja/cerrar", {"efectivo_contado": str(efectivo_contado)})

    def movimiento_caja(self, tipo: str, concepto: str, valor: float) -> dict:
        return self._post("/caja/movimiento",
                          {"tipo": tipo, "concepto": concepto, "valor": str(valor)})

    # -- posventa -----------------------------------------------------------

    def garantias(self, estado: str | None = None) -> list[dict]:
        return self._get("/garantias", estado=estado)

    def reclamar_garantia(self, garantia_id: int, falla: str) -> dict:
        return self._post(f"/garantias/{garantia_id}/reclamar", {"falla": falla})

    def ordenes_servicio(self, estado: str | None = None) -> list[dict]:
        return self._get("/servicio", estado=estado)

    def apartados(self, estado: str | None = None) -> list[dict]:
        return self._get("/apartados", estado=estado)

    def devoluciones(self, limite: int = 100) -> list[dict]:
        return self._get("/devoluciones", limite=limite)

    # -- seguridad ----------------------------------------------------------

    def usuarios(self) -> list[dict]:
        return self._get("/usuarios")

    def crear_usuario(self, datos: dict) -> dict:
        return self._post("/usuarios", datos)

    def actualizar_usuario(self, usuario_id: int, datos: dict) -> dict:
        return self._put(f"/usuarios/{usuario_id}", datos)

    def roles(self) -> list[dict]:
        return self._get("/roles")

    def catalogo_permisos(self) -> list[dict]:
        return self._get("/permisos")

    def permisos_de_rol(self, rol_id: int) -> list[str]:
        return self._get(f"/roles/{rol_id}/permisos")
