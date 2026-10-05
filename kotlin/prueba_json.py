"""Prueba de la logica del analizador de JSON de Json.kt.

No se puede compilar Kotlin en este entorno (Maven Central esta bloqueado), pero
el algoritmo del analizador si se puede probar: se transcribe linea por linea a
Python y se le dan de comer las respuestas reales de la API. Si el analizador
transcrito devuelve exactamente lo mismo que `json.loads`, la logica de Json.kt
es correcta; lo unico que quedaria por verificar es la sintaxis de Kotlin.

La transcripcion es deliberadamente literal —mismos nombres, mismo orden, mismas
condiciones— para que un cambio en Json.kt se pueda reflejar aqui sin pensar.

    python prueba_json.py
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal

import requests

SERVIDOR = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"


# --- transcripcion literal de la clase Analizador de Json.kt -----------------

class Analizador:
    def __init__(self, fuente: str):
        self.fuente = fuente
        self.posicion = 0

    def terminado(self) -> bool:
        return self.posicion >= len(self.fuente)

    def espacios(self) -> None:
        while not self.terminado() and self.fuente[self.posicion].isspace():
            self.posicion += 1

    def valor(self):
        self.espacios()
        assert not self.terminado(), "JSON vacio o incompleto"
        c = self.fuente[self.posicion]
        if c == "{":
            return self.objeto()
        if c == "[":
            return self.arreglo()
        if c == '"':
            return self.cadena()
        if c in "tf":
            return self.booleano()
        if c == "n":
            return self.nulo()
        if c == "-" or c.isdigit():
            return self.numero()
        raise AssertionError(f"Caracter inesperado '{c}' en la posicion {self.posicion}")

    def objeto(self) -> dict:
        campos: dict = {}
        self.posicion += 1
        self.espacios()
        if not self.terminado() and self.fuente[self.posicion] == "}":
            self.posicion += 1
            return campos
        while True:
            self.espacios()
            clave = self.cadena()
            self.espacios()
            assert self.fuente[self.posicion] == ":", f"Falta ':' en {self.posicion}"
            self.posicion += 1
            campos[clave] = self.valor()
            self.espacios()
            c = self.fuente[self.posicion]
            if c == ",":
                self.posicion += 1
            elif c == "}":
                self.posicion += 1
                return campos
            else:
                raise AssertionError(f"Falta ',' o '}}' en {self.posicion}")

    def arreglo(self) -> list:
        elementos: list = []
        self.posicion += 1
        self.espacios()
        if not self.terminado() and self.fuente[self.posicion] == "]":
            self.posicion += 1
            return elementos
        while True:
            elementos.append(self.valor())
            self.espacios()
            c = self.fuente[self.posicion]
            if c == ",":
                self.posicion += 1
            elif c == "]":
                self.posicion += 1
                return elementos
            else:
                raise AssertionError(f"Falta ',' o ']' en {self.posicion}")

    def cadena(self) -> str:
        assert self.fuente[self.posicion] == '"', f"Se esperaba cadena en {self.posicion}"
        self.posicion += 1
        sb = []
        while self.fuente[self.posicion] != '"':
            c = self.fuente[self.posicion]
            if c == "\\":
                self.posicion += 1
                e = self.fuente[self.posicion]
                if e in '"\\/':
                    sb.append(e)
                elif e == "b":
                    sb.append("\b")
                elif e == "f":
                    sb.append("\u000C")
                elif e == "n":
                    sb.append("\n")
                elif e == "r":
                    sb.append("\r")
                elif e == "t":
                    sb.append("\t")
                elif e == "u":
                    codigo = self.fuente[self.posicion + 1:self.posicion + 5]
                    sb.append(chr(int(codigo, 16)))
                    self.posicion += 4
                else:
                    raise AssertionError(f"Escape desconocido '\\{e}' en {self.posicion}")
            else:
                sb.append(c)
            self.posicion += 1
        self.posicion += 1
        return "".join(sb)

    def numero(self) -> Decimal:
        inicio = self.posicion
        if self.fuente[self.posicion] == "-":
            self.posicion += 1
        while not self.terminado() and (self.fuente[self.posicion].isdigit()
                                        or self.fuente[self.posicion] in ".eE+-"):
            if (self.fuente[self.posicion] in "+-"
                    and self.fuente[self.posicion - 1] not in "eE"):
                break
            self.posicion += 1
        return Decimal(self.fuente[inicio:self.posicion])

    def booleano(self) -> bool:
        if self.fuente.startswith("true", self.posicion):
            self.posicion += 4
            return True
        if self.fuente.startswith("false", self.posicion):
            self.posicion += 5
            return False
        raise AssertionError(f"Booleano mal formado en {self.posicion}")

    def nulo(self):
        assert self.fuente.startswith("null", self.posicion), \
            f"Se esperaba null en {self.posicion}"
        self.posicion += 4
        return None


def leer(texto: str):
    a = Analizador(texto)
    valor = a.valor()
    a.espacios()
    assert a.terminado(), f"Sobra texto despues del JSON en la posicion {a.posicion}"
    return valor


# --- transcripcion del escritor ---------------------------------------------

def escribir(valor) -> str:
    if valor is None:
        return "null"
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if isinstance(valor, (int, float, Decimal)):
        return str(valor)
    if isinstance(valor, str):
        return escapar(valor)
    if isinstance(valor, dict):
        return "{" + ",".join(f"{escapar(str(k))}:{escribir(v)}"
                              for k, v in valor.items()) + "}"
    if isinstance(valor, (list, tuple)):
        return "[" + ",".join(escribir(v) for v in valor) + "]"
    return escapar(str(valor))


def escapar(texto: str) -> str:
    sb = ['"']
    for c in texto:
        if c == '"':
            sb.append('\\"')
        elif c == "\\":
            sb.append("\\\\")
        elif c == "\n":
            sb.append("\\n")
        elif c == "\r":
            sb.append("\\r")
        elif c == "\t":
            sb.append("\\t")
        elif c < " ":
            sb.append("\\u%04x" % ord(c))
        else:
            sb.append(c)
    sb.append('"')
    return "".join(sb)


# --- comparacion -------------------------------------------------------------

def normalizar(valor):
    """Los Decimal del analizador se comparan contra los numeros de json.loads."""
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, dict):
        return {k: normalizar(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [normalizar(v) for v in valor]
    return valor


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


print("=== 1. Casos limite ===")
CASOS = [
    "{}", "[]", "null", "true", "false", "0", "-0", "123", "-123", "1.5", "-1.5",
    "1e3", "1E3", "1.5e-3", "-2.5E+4", '""', '"hola"', '"con \\"comillas\\""',
    '"salto\\nlinea"', '"tab\\ty"', '"barra\\\\invertida"', '"unicode \\u00f1"',
    '"emoji \\u263a"', "[1,2,3]", "[[1],[2]]", '{"a":1}', '{"a":{"b":[1,2,{"c":null}]}}',
    '  {  "a" : 1 , "b" : [ true , false ] }  ',
    '{"vacio":"","cero":0,"nulo":null,"lista":[]}',
    '{"negativo":-99.95,"grande":2999900.00,"exp":1.2e10}',
    '[{"n":1},{"n":2},{"n":3}]',
    '{"acentos":"Garantía con ñ y tildes áéíóú"}',
]
for caso in CASOS:
    try:
        mio = normalizar(leer(caso))
        suyo = json.loads(caso)
        verificar(mio == suyo, f"{caso[:48]:<50} -> {mio!r:.40}")
    except Exception as e:
        verificar(False, f"{caso[:48]:<50} -> {type(e).__name__}: {e}")

print("\n=== 2. Textos que deben ser rechazados ===")
MALOS = ['{"a":1', "[1,2", '{"a" 1}', "{,}", '"sin cerrar', "tru", "[1,2]basura",
         "{'a':1}", ""]
for caso in MALOS:
    try:
        leer(caso)
        verificar(False, f"{caso!r:<22} deberia haber fallado")
    except Exception:
        verificar(True, f"{caso!r:<22} rechazado correctamente")

print("\n=== 3. Ida y vuelta: escribir y volver a leer ===")
OBJETOS = [
    {"cliente_id": None, "items": [{"producto_id": 1, "cantidad": 2,
                                    "descuento": "0", "imei": "356789012345045"}],
     "pagos": [{"metodo": "EFECTIVO", "valor": "106981.00"}]},
    {"texto": 'comillas " y barra \\ y salto\nlinea', "vacio": "", "cero": 0},
    {"anidado": {"a": [1, [2, [3, {"b": True}]]]}},
]
for obj in OBJETOS:
    texto = escribir(obj)
    verificar(json.loads(texto) == obj, f"ida y vuelta: {texto[:56]}")

print("\n=== 4. Respuestas reales de la API ===")
try:
    t = requests.post(f"{SERVIDOR}/auth/login",
                      data={"username": "admin", "password": "admin123"},
                      timeout=15)
    verificar(t.ok, "login contra la API")
    token = t.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    rutas = ["/salud", "/auth/yo", "/reportes/dashboard", "/reportes/ventas-por-dia?dias=14",
             "/reportes/mas-vendidos", "/reportes/alertas-stock", "/productos?limite=50",
             "/inventario/imei?limite=50", "/clientes?limite=50", "/ventas?limite=50",
             "/garantias", "/usuarios", "/caja/cajas", "/caja/turno", "/roles",
             "/permisos", "/apartados", "/servicio", "/compras/proveedores",
             "/telefonia/planes", "/iot/alertas", "/categorias", "/marcas"]
    # El login tambien: es la respuesta mas anidada de todas.
    rutas.append(None)
    for ruta in rutas:
        bruto = t.text if ruta is None else requests.get(SERVIDOR + ruta, headers=h,
                                                         timeout=20).text
        nombre = "POST /auth/login" if ruta is None else ruta
        try:
            verificar(normalizar(leer(bruto)) == json.loads(bruto),
                      f"{nombre:<38} ({len(bruto):>6} bytes)")
        except Exception as e:
            verificar(False, f"{nombre}: {type(e).__name__}: {e}")
except requests.exceptions.RequestException as e:
    verificar(False, f"no se pudo hablar con la API: {e}")

print("\n" + "=" * 70)
if fallos:
    print(f"RESULTADO: {len(fallos)} de {pasos} comprobaciones fallaron\n")
    for f in fallos:
        print(f"  · {f}")
    sys.exit(1)
print(f"RESULTADO: {pasos} comprobaciones, todas correctas")
