package ejemplos

import java.math.BigDecimal
import java.math.RoundingMode

/**
 * Recorrido por Kotlin con el dominio del proyecto.
 *
 * No es un "hola mundo": cada apartado resuelve algo que el POS necesita de
 * verdad, para que se vea por que el lenguaje ayuda y no solo que existe.
 *
 *     gradlew ejemplo
 */

// --- 1. Clases de datos -----------------------------------------------------
// `data class` genera equals, hashCode, toString y copy. Una linea hace lo que
// en Java son cuarenta.
data class Producto(
    val sku: String,
    val nombre: String,
    val precio: BigDecimal,
    val iva: BigDecimal = BigDecimal("19"),
    val requiereImei: Boolean = false,
    val existencias: Int = 0,
)

// --- 2. Clases selladas -----------------------------------------------------
// Una jerarquia cerrada: el compilador sabe que no hay mas casos y obliga a
// cubrirlos todos en el `when`. Si manana se agrega un medio de pago, el codigo
// que falte deja de compilar en lugar de fallar de noche en el mostrador.
sealed class Pago {
    abstract val valor: BigDecimal

    data class Efectivo(override val valor: BigDecimal, val recibido: BigDecimal) : Pago()
    data class Tarjeta(override val valor: BigDecimal, val ultimos4: String) : Pago()
    data class Transferencia(override val valor: BigDecimal, val referencia: String) : Pago()
}

fun describir(pago: Pago): String = when (pago) {
    is Pago.Efectivo -> "Efectivo ${pesos(pago.valor)} (vuelto ${pesos(pago.recibido - pago.valor)})"
    is Pago.Tarjeta -> "Tarjeta terminada en ${pago.ultimos4} por ${pesos(pago.valor)}"
    is Pago.Transferencia -> "Transferencia ${pago.referencia} por ${pesos(pago.valor)}"
}

// --- 3. Funciones de extension ----------------------------------------------
// Se le agrega un metodo a BigDecimal sin tocar la clase ni heredar de ella.
fun BigDecimal.aDinero(): BigDecimal = setScale(2, RoundingMode.HALF_UP)

fun pesos(valor: BigDecimal): String =
    "$ " + valor.aDinero().toBigInteger().toString()
        .reversed().chunked(3).joinToString(".").reversed()

// --- 4. Reglas de negocio con tipos ------------------------------------------
data class LineaFactura(val producto: Producto, val cantidad: Int, val imei: String? = null) {
    val base: BigDecimal get() = (producto.precio * BigDecimal(cantidad)).aDinero()
    val ivaValor: BigDecimal get() = (base * producto.iva / BigDecimal(100)).aDinero()
    val total: BigDecimal get() = (base + ivaValor).aDinero()
}

/**
 * El tipo de retorno dice que puede fallar y por que. No hay excepciones ni
 * codigos de error sueltos: quien llama tiene que mirar el resultado.
 */
sealed class Resultado<out T> {
    data class Exito<T>(val valor: T) : Resultado<T>()
    data class Fallo(val motivo: String) : Resultado<Nothing>()
}

fun armarLinea(producto: Producto, cantidad: Int, imei: String?): Resultado<LineaFactura> = when {
    producto.requiereImei && imei == null ->
        Resultado.Fallo("'${producto.nombre}' requiere IMEI y no se envio ninguno")
    producto.requiereImei && cantidad != 1 ->
        Resultado.Fallo("'${producto.nombre}' se vende por unidad: una linea por IMEI")
    !producto.requiereImei && cantidad > producto.existencias ->
        Resultado.Fallo("Stock insuficiente de '${producto.nombre}': " +
                "hay ${producto.existencias}, piden $cantidad")
    else -> Resultado.Exito(LineaFactura(producto, cantidad, imei))
}

// --- 5. El algoritmo de Luhn, para validar un IMEI ---------------------------
fun imeiValido(imei: String): Boolean {
    if (imei.length != 15 || !imei.all { it.isDigit() }) return false
    // Se recorre de derecha a izquierda duplicando una de cada dos cifras.
    val suma = imei.reversed().mapIndexed { posicion, caracter ->
        val d = caracter.digitToInt()
        if (posicion % 2 == 1) (d * 2).let { if (it > 9) it - 9 else it } else d
    }.sum()
    return suma % 10 == 0
}

fun main() {
    fun titulo(n: Int, texto: String) =
        println("\n" + "=".repeat(68) + "\n$n. $texto\n" + "=".repeat(68))

    val catalogo = listOf(
        Producto("SM-A155", "Samsung Galaxy A15 128GB", BigDecimal("849900"),
            requiereImei = true),
        Producto("AP-IP13", "Apple iPhone 13 128GB", BigDecimal("2999900"),
            requiereImei = true),
        Producto("AC-CAR20", "Cargador rapido 20W USB-C", BigDecimal("39900"),
            existencias = 38),
        Producto("AC-VID01", "Vidrio templado universal", BigDecimal("15000"),
            existencias = 117),
        Producto("AU-BT500", "Audifonos Bluetooth TWS", BigDecimal("89900"),
            existencias = 21),
    )

    // --- Colecciones: la cadena se lee como una frase ------------------------
    titulo(1, "Colecciones")
    val accesorios = catalogo
        .filter { !it.requiereImei }
        .sortedByDescending { it.precio }
    println("Accesorios de mayor a menor precio:")
    accesorios.forEach { println("  ${it.sku.padEnd(10)} ${it.nombre.padEnd(34)} ${pesos(it.precio)}") }

    val porTipo = catalogo.groupBy { if (it.requiereImei) "Con IMEI" else "Por stock" }
    println("\nAgrupado por tipo de inventario:")
    porTipo.forEach { (tipo, productos) -> println("  $tipo: ${productos.size} productos") }

    val valorInventario = catalogo.sumOf { it.precio * BigDecimal(it.existencias) }
    println("\nValor del inventario de accesorios: ${pesos(valorInventario)}")

    // --- Seguridad de nulos --------------------------------------------------
    titulo(2, "Seguridad de nulos")
    val buscado: Producto? = catalogo.find { it.sku == "NO-EXISTE" }
    // `?.` no entra si es nulo; `?:` da el valor de reemplazo. El NullPointerException
    // deja de ser algo que se descubre en produccion.
    println("Buscando NO-EXISTE: ${buscado?.nombre ?: "no esta en el catalogo"}")
    val encontrado = catalogo.find { it.sku == "AP-IP13" }
    println("Buscando AP-IP13:   ${encontrado?.nombre ?: "no esta en el catalogo"}")

    // --- Reglas de negocio ---------------------------------------------------
    titulo(3, "Reglas de la venta")
    val intentos = listOf(
        Triple(catalogo[0], 1, "356789012345045"),
        Triple(catalogo[0], 1, null),
        Triple(catalogo[1], 2, "353333444555021"),
        Triple(catalogo[2], 500, null),
        Triple(catalogo[4], 3, null),
    )
    intentos.forEach { (producto, cantidad, imei) ->
        when (val r = armarLinea(producto, cantidad, imei)) {
            is Resultado.Exito ->
                println("  OK      ${producto.sku} x$cantidad -> ${pesos(r.valor.total)} " +
                        "(IVA ${pesos(r.valor.ivaValor)})")
            is Resultado.Fallo -> println("  RECHAZO ${r.motivo}")
        }
    }

    // --- Medios de pago ------------------------------------------------------
    titulo(4, "Medios de pago (clases selladas)")
    listOf(
        Pago.Efectivo(BigDecimal("150000"), BigDecimal("200000")),
        Pago.Tarjeta(BigDecimal("89900"), "4417"),
        Pago.Transferencia(BigDecimal("2999900"), "NEQUI-88213"),
    ).forEach { println("  " + describir(it)) }

    // --- Validacion de IMEI --------------------------------------------------
    titulo(5, "Validacion de IMEI (algoritmo de Luhn)")
    listOf("356789012345045", "356789012345046", "12345", "35678901234504X").forEach {
        println("  ${it.padEnd(18)} ${if (imeiValido(it)) "valido" else "invalido"}")
    }
    println("\n  La misma validacion esta en la interfaz, en la API y en un CHECK de")
    println("  PostgreSQL: tres capas, porque la de arriba se puede saltar.")

    println()
}
