package pos

import java.math.BigDecimal

/**
 * Lector y escritor de JSON escrito a mano.
 *
 * Se podria usar kotlinx.serialization o Jackson, pero para hablar con una API
 * propia eso significa arrastrar una dependencia y un plugin del compilador a
 * cambio de doscientas lineas. Esta version alcanza de sobra y deja el proyecto
 * con una sola dependencia de verdad (Compose).
 *
 * El JSON se representa con tipos de Kotlin:
 *
 *   objeto   -> Map<String, Any?>
 *   arreglo  -> List<Any?>
 *   cadena   -> String
 *   numero   -> BigDecimal   (no Double: el dinero no se guarda en coma flotante)
 *   booleano -> Boolean
 *   null     -> null
 */
object Json {

    // ------------------------------------------------------------------ leer

    fun leer(texto: String): Any? = Analizador(texto).let {
        val valor = it.valor()
        it.espacios()
        require(it.terminado()) { "Sobra texto despues del JSON en la posicion ${it.posicion}" }
        valor
    }

    private class Analizador(private val fuente: String) {
        var posicion = 0

        fun terminado() = posicion >= fuente.length

        fun espacios() {
            while (!terminado() && fuente[posicion].isWhitespace()) posicion++
        }

        fun valor(): Any? {
            espacios()
            require(!terminado()) { "JSON vacio o incompleto" }
            return when (val c = fuente[posicion]) {
                '{' -> objeto()
                '[' -> arreglo()
                '"' -> cadena()
                't', 'f' -> booleano()
                'n' -> nulo()
                else -> if (c == '-' || c.isDigit()) numero()
                        else error("Caracter inesperado '$c' en la posicion $posicion")
            }
        }

        private fun objeto(): Map<String, Any?> {
            val campos = LinkedHashMap<String, Any?>()
            posicion++                       // se consume la llave de apertura
            espacios()
            if (!terminado() && fuente[posicion] == '}') { posicion++; return campos }
            while (true) {
                espacios()
                val clave = cadena()
                espacios()
                require(fuente[posicion] == ':') { "Falta ':' en la posicion $posicion" }
                posicion++
                campos[clave] = valor()
                espacios()
                when (fuente[posicion]) {
                    ',' -> posicion++
                    '}' -> { posicion++; return campos }
                    else -> error("Falta ',' o '}' en la posicion $posicion")
                }
            }
        }

        private fun arreglo(): List<Any?> {
            val elementos = ArrayList<Any?>()
            posicion++
            espacios()
            if (!terminado() && fuente[posicion] == ']') { posicion++; return elementos }
            while (true) {
                elementos += valor()
                espacios()
                when (fuente[posicion]) {
                    ',' -> posicion++
                    ']' -> { posicion++; return elementos }
                    else -> error("Falta ',' o ']' en la posicion $posicion")
                }
            }
        }

        private fun cadena(): String {
            require(fuente[posicion] == '"') { "Se esperaba una cadena en la posicion $posicion" }
            posicion++
            val sb = StringBuilder()
            while (fuente[posicion] != '"') {
                val c = fuente[posicion]
                if (c == '\\') {
                    posicion++
                    when (val e = fuente[posicion]) {
                        '"', '\\', '/' -> sb.append(e)
                        'b' -> sb.append('\b')
                        'f' -> sb.append('\u000C')
                        'n' -> sb.append('\n')
                        'r' -> sb.append('\r')
                        't' -> sb.append('\t')
                        'u' -> {
                            // \uXXXX: cuatro digitos hexadecimales
                            val codigo = fuente.substring(posicion + 1, posicion + 5)
                            sb.append(codigo.toInt(16).toChar())
                            posicion += 4
                        }
                        else -> error("Escape desconocido '\\$e' en la posicion $posicion")
                    }
                } else {
                    sb.append(c)
                }
                posicion++
            }
            posicion++
            return sb.toString()
        }

        private fun numero(): BigDecimal {
            val inicio = posicion
            if (fuente[posicion] == '-') posicion++
            while (!terminado() && (fuente[posicion].isDigit() ||
                        fuente[posicion] in ".eE+-")) {
                // El '+' y el '-' solo valen dentro de un exponente; si aparecen
                // despues de un digito sin 'e' delante, el numero ya termino.
                if (fuente[posicion] in "+-" &&
                    fuente[posicion - 1] !in "eE") break
                posicion++
            }
            return BigDecimal(fuente.substring(inicio, posicion))
        }

        private fun booleano(): Boolean = when {
            fuente.startsWith("true", posicion) -> { posicion += 4; true }
            fuente.startsWith("false", posicion) -> { posicion += 5; false }
            else -> error("Booleano mal formado en la posicion $posicion")
        }

        private fun nulo(): Any? {
            require(fuente.startsWith("null", posicion)) {
                "Se esperaba null en la posicion $posicion"
            }
            posicion += 4
            return null
        }
    }

    // --------------------------------------------------------------- escribir

    fun escribir(valor: Any?): String = StringBuilder().also { escribirEn(valor, it) }.toString()

    private fun escribirEn(valor: Any?, sb: StringBuilder) {
        when (valor) {
            null -> sb.append("null")
            is Boolean -> sb.append(valor)
            is Number -> sb.append(valor.toString())
            is String -> escapar(valor, sb)
            is Map<*, *> -> {
                sb.append('{')
                valor.entries.forEachIndexed { i, (clave, v) ->
                    if (i > 0) sb.append(',')
                    escapar(clave.toString(), sb)
                    sb.append(':')
                    escribirEn(v, sb)
                }
                sb.append('}')
            }
            is Iterable<*> -> {
                sb.append('[')
                valor.forEachIndexed { i, v ->
                    if (i > 0) sb.append(',')
                    escribirEn(v, sb)
                }
                sb.append(']')
            }
            else -> escapar(valor.toString(), sb)
        }
    }

    private fun escapar(texto: String, sb: StringBuilder) {
        sb.append('"')
        for (c in texto) {
            when {
                c == '"' -> sb.append("\\\"")
                c == '\\' -> sb.append("\\\\")
                c == '\n' -> sb.append("\\n")
                c == '\r' -> sb.append("\\r")
                c == '\t' -> sb.append("\\t")
                c < ' ' -> sb.append("\\u%04x".format(c.code))
                else -> sb.append(c)
            }
        }
        sb.append('"')
    }
}

// ---------------------------------------------------------------------------
// Accesos comodos. Convierten `Any?` en el tipo que se espera sin repetir
// `as?` y `?:` en cada pantalla. Si la clave no existe o viene con otro tipo,
// devuelven el valor neutro en lugar de reventar: una pantalla no deberia
// caerse porque un campo opcional llego nulo.
// ---------------------------------------------------------------------------

@Suppress("UNCHECKED_CAST")
fun Any?.objeto(): Map<String, Any?> = this as? Map<String, Any?> ?: emptyMap()

fun Any?.lista(): List<Any?> = this as? List<Any?> ?: emptyList()

fun Any?.objetos(): List<Map<String, Any?>> = lista().map { it.objeto() }

fun Map<String, Any?>.texto(clave: String, porDefecto: String = ""): String =
    this[clave]?.toString() ?: porDefecto

fun Map<String, Any?>.entero(clave: String, porDefecto: Int = 0): Int =
    when (val v = this[clave]) {
        is BigDecimal -> v.toInt()
        is Number -> v.toInt()
        is String -> v.toIntOrNull() ?: porDefecto
        else -> porDefecto
    }

fun Map<String, Any?>.decimal(clave: String): BigDecimal =
    when (val v = this[clave]) {
        is BigDecimal -> v
        is Number -> BigDecimal(v.toString())
        // La API envia los NUMERIC como texto ("2999900.00") justamente para que
        // no pasen por un Double y pierdan centavos.
        is String -> v.toBigDecimalOrNull() ?: BigDecimal.ZERO
        else -> BigDecimal.ZERO
    }

fun Map<String, Any?>.siNo(clave: String): Boolean = this[clave] as? Boolean ?: false

fun Map<String, Any?>.sub(clave: String): Map<String, Any?> = this[clave].objeto()
