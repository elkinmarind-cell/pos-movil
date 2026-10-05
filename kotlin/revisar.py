"""Revision estatica del codigo Kotlin, sin compilador.

Maven Central y services.gradle.org estan bloqueados en el entorno donde se
escribio este proyecto, asi que no se pudo ejecutar `gradlew build`. Este script
hace lo que si se puede hacer sin compilador y atrapa los errores que de verdad
aparecen cuando uno escribe Kotlin sin IDE:

  1. llaves, parentesis y corchetes descuadrados (ignorando los que van dentro
     de cadenas y comentarios);
  2. tipos usados sin importar ni declarar en el proyecto;
  3. imports que no se usan;
  4. nombres de clase que el build.gradle.kts invoca y que no existen.

No reemplaza a `gradlew build`, pero sin esto el primer intento de compilar seria
a ciegas.

    python revisar.py
"""

from __future__ import annotations

import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).parent
FUENTES = sorted((RAIZ / "src/main/kotlin").rglob("*.kt"))

# Lo que trae Kotlin y la JVM sin importar nada.
PRECARGADO = {
    # kotlin
    "String", "Int", "Long", "Double", "Float", "Boolean", "Char", "Byte", "Short",
    "Any", "Unit", "Nothing", "Array", "List", "MutableList", "ArrayList", "Map",
    "MutableMap", "LinkedHashMap", "HashMap", "Set", "MutableSet", "HashSet",
    "Pair", "Triple", "Exception", "RuntimeException", "IllegalStateException",
    "IllegalArgumentException", "Throwable", "Comparable", "Iterable", "Sequence",
    "Regex", "StringBuilder", "Result", "Number", "Collection", "Lazy",
    "Deprecated", "JvmStatic", "JvmName", "Suppress", "Volatile", "Synchronized",
    "Override", "System", "Math", "Thread", "Runnable", "Object", "Class",
    "Comparator", "CharSequence", "Enum", "Error", "StackTraceElement",
}

# Simbolos que el propio proyecto declara (se completan leyendo las fuentes).
DECLARADOS: set[str] = set()

problemas: list[str] = []
avisos: list[str] = []


def sin_texto(codigo: str) -> str:
    """Quita comentarios y cadenas: lo que hay dentro no es codigo."""
    salida = []
    i, n = 0, len(codigo)
    while i < n:
        c = codigo[i]
        if c == "/" and i + 1 < n and codigo[i + 1] == "/":
            while i < n and codigo[i] != "\n":
                i += 1
        elif c == "/" and i + 1 < n and codigo[i + 1] == "*":
            i += 2
            while i + 1 < n and not (codigo[i] == "*" and codigo[i + 1] == "/"):
                i += 1
            i += 2
        elif codigo.startswith('"""', i):
            i += 3
            while i < n and not codigo.startswith('"""', i):
                i += 1
            i += 3
        elif c == '"':
            i += 1
            while i < n and codigo[i] != '"':
                i += 2 if codigo[i] == "\\" else 1
            i += 1
        elif c == "'":
            i += 1
            while i < n and codigo[i] != "'":
                i += 2 if codigo[i] == "\\" else 1
            i += 1
        else:
            salida.append(c)
            i += 1
    return "".join(salida)


# --- 1. equilibrio de simbolos ----------------------------------------------
print("1. Equilibrio de llaves, parentesis y corchetes")
for archivo in FUENTES:
    codigo = sin_texto(archivo.read_text(encoding="utf-8"))
    pila = []
    pareja = {")": "(", "]": "[", "}": "{"}
    linea = 1
    descuadrado = False
    for c in codigo:
        if c == "\n":
            linea += 1
        elif c in "([{":
            pila.append((c, linea))
        elif c in ")]}":
            if not pila or pila[-1][0] != pareja[c]:
                problemas.append(f"{archivo.name}:{linea} '{c}' sin su pareja")
                descuadrado = True
                break
            pila.pop()
    if pila and not descuadrado:
        simbolo, donde = pila[-1]
        problemas.append(f"{archivo.name}:{donde} '{simbolo}' quedo sin cerrar")
        descuadrado = True
    print(f"   {'FALLA' if descuadrado else 'ok   '}  {archivo.name}")


# --- 2. inventario de lo que declara el proyecto -----------------------------
PATRON_DECL = re.compile(
    r"^\s*(?:private |internal |public |abstract |sealed |open |data |value )*"
    r"(?:class|interface|object|enum class|annotation class)\s+([A-Z]\w*)",
    re.M,
)
PATRON_FUN = re.compile(r"^\s*(?:@Composable\s+)?(?:private |internal |public |inline )*"
                        r"fun\s+(?:<[^>]+>\s+)?(?:[\w.<>?]+\.)?([A-Z]\w*)\s*\(", re.M)
PATRON_VAL = re.compile(r"^\s*(?:private |internal )?(?:const )?(?:val|var)\s+([A-Z][A-Z_0-9]*)\s*[:=]", re.M)
# Parametros genericos: el <T> de `fun <T> Cargador(...)` o `class Caja<T>`.
PATRON_GENERICO = re.compile(r"(?:fun|class|interface)\s*(?:\w+\s*)?<([^>]+)>")

for archivo in FUENTES:
    codigo = archivo.read_text(encoding="utf-8")
    DECLARADOS.update(PATRON_DECL.findall(codigo))
    DECLARADOS.update(PATRON_FUN.findall(codigo))
    DECLARADOS.update(PATRON_VAL.findall(codigo))
    for grupo in PATRON_GENERICO.findall(codigo):
        for parametro in grupo.split(","):
            nombre = parametro.strip().removeprefix("out ").removeprefix("in ")
            nombre = nombre.split(":")[0].strip()
            if re.fullmatch(r"[A-Z]\w*", nombre):
                DECLARADOS.add(nombre)

print(f"\n2. El proyecto declara {len(DECLARADOS)} tipos y funciones con mayuscula inicial")

# --- 3. tipos usados sin importar -------------------------------------------
print("\n3. Tipos usados sin importar ni declarar")
PATRON_IMPORT = re.compile(r"^import\s+([\w.]+)(?:\s+as\s+(\w+))?\s*$", re.M)
PATRON_USO = re.compile(r"\b([A-Z]\w*)\b")

for archivo in FUENTES:
    bruto = archivo.read_text(encoding="utf-8")
    codigo = sin_texto(bruto)
    importados = set()
    for ruta, alias in PATRON_IMPORT.findall(bruto):
        importados.add(alias or ruta.rsplit(".", 1)[-1])

    # Un uso cualificado (java.awt.Color) no necesita import.
    cualificados = set(re.findall(r"\b[a-z][\w]*(?:\.[a-z][\w]*)*\.([A-Z]\w*)", codigo))

    faltantes = set()
    for nombre in PATRON_USO.findall(codigo):
        if (nombre in importados or nombre in DECLARADOS or nombre in PRECARGADO
                or nombre in cualificados):
            continue
        # Un miembro de algo ya conocido (Tema.acento, Icons.Default) no cuenta.
        if re.search(rf"\b[A-Z]\w*\.{nombre}\b", codigo):
            continue
        faltantes.add(nombre)

    if faltantes:
        for nombre in sorted(faltantes):
            problemas.append(f"{archivo.name}: '{nombre}' se usa sin importar ni declarar")
        print(f"   FALLA  {archivo.name}: {', '.join(sorted(faltantes))}")
    else:
        print(f"   ok     {archivo.name}")

# --- 4. imports sin usar -----------------------------------------------------
print("\n4. Imports que no se usan")
for archivo in FUENTES:
    bruto = archivo.read_text(encoding="utf-8")
    codigo = sin_texto(re.sub(r"^import .*$", "", bruto, flags=re.M))
    sobrantes = []
    for ruta, alias in PATRON_IMPORT.findall(bruto):
        nombre = alias or ruta.rsplit(".", 1)[-1]
        delegado = nombre in ("getValue", "setValue") and re.search(r"\bby\s+remember", codigo)
        if not delegado and not re.search(rf"\b{re.escape(nombre)}\b", codigo):
            sobrantes.append(ruta)
    if sobrantes:
        avisos.append(f"{archivo.name}: sobran {len(sobrantes)} imports")
        print(f"   aviso  {archivo.name}: {', '.join(r.rsplit('.', 1)[-1] for r in sobrantes)}")
    else:
        print(f"   ok     {archivo.name}")

# --- 5. las clases que invoca Gradle existen ---------------------------------
print("\n5. Clases de entrada declaradas en build.gradle.kts")
gradle = (RAIZ / "build.gradle.kts").read_text(encoding="utf-8")
for clase in re.findall(r'"((?:\w+\.)+\w+Kt)"', gradle) + re.findall(r'mainClass\s*=\s*"([\w.]+)"', gradle):
    paquete, _, nombre = clase.rpartition(".")
    archivo = nombre.removesuffix("Kt") + ".kt"
    ruta = RAIZ / "src/main/kotlin" / paquete.replace(".", "/") / archivo
    tiene_main = ruta.exists() and re.search(r"^fun main\(", ruta.read_text(encoding="utf-8"), re.M)
    if tiene_main:
        print(f"   ok     {clase} -> {ruta.relative_to(RAIZ)}")
    else:
        problemas.append(f"{clase}: no existe {ruta.relative_to(RAIZ)} con 'fun main('")
        print(f"   FALLA  {clase} -> falta {ruta.relative_to(RAIZ)} con 'fun main('")

# -----------------------------------------------------------------------------
print("\n" + "=" * 70)
if problemas:
    print(f"RESULTADO: {len(problemas)} problemas\n")
    for p in problemas:
        print(f"  · {p}")
    sys.exit(1)
print(f"RESULTADO: sin problemas en {len(FUENTES)} archivos"
      + (f" ({len(avisos)} avisos)" if avisos else ""))
