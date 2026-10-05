# Aplicación de escritorio en Kotlin — cómo compilarla y ejecutarla

Esta carpeta es un proyecto Gradle independiente. Contiene la tercera versión
del cliente del POS Móvil: la misma API, el mismo diseño, escrita en **Kotlin con
Compose Desktop**.

---

## Lo que hay que tener instalado

Una de estas dos opciones. La primera es la más fácil.

### Opción A — IntelliJ IDEA Community (recomendada)

1. Descarga **IntelliJ IDEA Community Edition** (es gratis) de
   <https://www.jetbrains.com/idea/download/>.
2. Ábrelo y elige **Open**, luego selecciona esta carpeta `kotlin`.
3. IntelliJ detecta que es un proyecto Gradle, descarga por su cuenta Gradle, el
   JDK 17 y todas las dependencias. La primera vez tarda entre 5 y 15 minutos
   según la conexión.
4. Cuando termine, en el panel **Gradle** (a la derecha) abre
   `pos-movil-kotlin → Tasks → compose desktop → run` y haz doble clic.

No hace falta instalar Java ni Gradle aparte: IntelliJ los baja.

### Opción B — Gradle desde la consola

1. Instala un **JDK 17 o superior**. El más cómodo es Temurin:
   <https://adoptium.net/>. Verifica con `java -version`.
2. Instala **Gradle 8.5 o superior**: <https://gradle.org/install/>, o con
   `winget install Gradle.Gradle` en Windows 11.
3. Desde esta carpeta:

   ```
   gradle run
   ```

   La primera vez Gradle descarga Compose y sus dependencias (unos 300 MB).

> Si prefieres tener el *wrapper* (`gradlew.bat`) para no depender del Gradle
> instalado, ejecútalo una sola vez: `gradle wrapper --gradle-version 8.10`.
> A partir de ahí puedes usar `gradlew run` y el proyecto es autosuficiente.

---

## Qué se puede ejecutar

| Comando | Qué hace |
|---|---|
| `gradle run` | Abre la aplicación de escritorio completa |
| `gradle ventana` | Ejemplo de la rúbrica: *mi primera ventana* (Swing) |
| `gradle ejemplo` | Ejemplo de la rúbrica: recorrido por el lenguaje |
| `gradle consulta` | Ejemplo de la rúbrica: *query y BD* con JDBC |
| `gradle packageMsi` | Genera el instalador `.msi` para Windows |
| `gradle build` | Solo compila, sin ejecutar |

El servidor tiene que estar encendido antes de `gradle run`: abre
`2-INICIAR.bat` en la carpeta de arriba y déjalo abierto. Si la API está en otro
equipo, defínelo antes:

```
set POS_SERVIDOR=http://192.168.1.50:8000/api
gradle run
```

Para el ejemplo de base de datos, la conexión se pasa igual:

```
set POS_BD=jdbc:postgresql://localhost:5432/pos_movil?user=postgres^&password=TU_CLAVE
gradle consulta
```

Si no la defines, el programa te pide la contraseña por consola. En Windows el
`&` dentro de `set` se escribe `^&`.

---

## Cómo está organizado

```
src/main/kotlin/
  pos/
    Main.kt          ventana, ingreso, menú lateral y ruteo entre módulos
    Tema.kt          colores y tema de Material 3 (los mismos de la web)
    Componentes.kt   piezas reutilizables: panel, tabla, KPI, insignia, campo
    Api.kt           cliente HTTP del backend; toda la red vive aquí
    Json.kt          lector y escritor de JSON escrito a mano
    Modelos.kt       dinero, fechas y la línea de factura
    Pantallas.kt     tablero, inventario, clientes, ventas, garantías, usuarios
    PuntoVenta.kt    el punto de venta, que es el único con estado propio
  ejemplos/
    MiPrimeraVentana.kt   rúbrica: "mi primera ventana"
    Ejemplo.kt            rúbrica: "Kotlin" y "ejemplo"
    QueryBD.kt            rúbrica: "query y BD"
```

### Por qué el proyecto tiene una sola dependencia de verdad

Compose es lo único que se trae de fuera (más el driver JDBC, que solo usa el
ejemplo de base de datos). El cliente HTTP es `java.net.http.HttpClient`, que
viene con el JDK, y el JSON lo lee un analizador propio de doscientas líneas.
Menos dependencias significa menos versiones que puedan pelearse entre ellas y un
instalador más pequeño.

### Las versiones están fijadas a propósito

```
Kotlin 2.0.21  +  org.jetbrains.kotlin.plugin.compose 2.0.21  +  Compose 1.7.3
```

Desde Kotlin 2.0 el compilador de Compose dejó de venir dentro del plugin de
Compose y pasó a ser un plugin aparte que debe tener **exactamente** la misma
versión que Kotlin. Si cambias una sola de las tres, la compilación falla con un
mensaje que no dice eso.

---

## Si algo falla

| Mensaje | Qué pasa |
|---|---|
| `Unsupported class file major version` | El JDK es anterior al 17. Instala Temurin 17+ y vuelve a abrir la consola. |
| `Could not resolve org.jetbrains.compose...` | No hay salida a internet o un proxy bloquea Maven Central. |
| `This version of the Compose Compiler requires Kotlin version...` | Alguien cambió una de las tres versiones del bloque `plugins`. |
| `No hay conexión con el servidor` dentro de la app | El backend está apagado: abre `2-INICIAR.bat`. |
| Java heap space al compilar | Sube el valor de `org.gradle.jvmargs` en `gradle.properties`. |

---

## Revisión sin compilador

En el entorno donde se escribió este proyecto, Maven Central y
`services.gradle.org` estaban bloqueados, así que no se pudo ejecutar
`gradle build`. Para no escribir a ciegas se dejó una revisión estática:

```
python revisar.py
```

Comprueba el equilibrio de llaves y paréntesis, que no se use ningún tipo sin
importar, que no sobren imports y que las clases de entrada que invoca
`build.gradle.kts` existan con su `fun main(`. No reemplaza al compilador, pero
atrapa los errores que de verdad aparecen al escribir Kotlin sin IDE.
