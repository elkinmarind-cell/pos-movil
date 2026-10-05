package pos

import java.math.BigDecimal
import java.math.RoundingMode
import java.time.OffsetDateTime
import java.time.format.DateTimeFormatter
import java.util.Locale

/** Dos decimales, medio hacia arriba. La misma regla que el backend y la base. */
fun dinero(valor: Any?): BigDecimal = when (valor) {
    null -> BigDecimal.ZERO
    is BigDecimal -> valor.setScale(2, RoundingMode.HALF_UP)
    is Number -> BigDecimal(valor.toString()).setScale(2, RoundingMode.HALF_UP)
    else -> (valor.toString().toBigDecimalOrNull() ?: BigDecimal.ZERO)
        .setScale(2, RoundingMode.HALF_UP)
}

private const val PESO = "$"

/** `2999900` -> `$ 2.999.900`. El punto como separador de miles, como en Colombia. */
fun pesos(valor: Any?, conDecimales: Boolean = false): String {
    val n = dinero(valor)
    val miles = n.abs().toBigInteger().toString()
        .reversed().chunked(3).joinToString(".").reversed()
    val signo = if (n.signum() < 0) "-" else ""
    if (!conDecimales) return "$signo$PESO $miles"
    val centavos = n.abs().remainder(BigDecimal.ONE)
        .movePointRight(2).toBigInteger().toInt()
    return "$signo$PESO %s,%02d".format(miles, centavos)
}

fun entero(valor: Any?): String =
    (valor?.toString()?.toBigDecimalOrNull()?.toBigInteger()?.toString() ?: "0")
        .reversed().chunked(3).joinToString(".").reversed()

private val CO: Locale = Locale.forLanguageTag("es-CO")
private val FECHA = DateTimeFormatter.ofPattern("dd/MM/yyyy", CO)
private val FECHA_HORA = DateTimeFormatter.ofPattern("dd/MM/yyyy hh:mm a", CO)

fun fecha(iso: Any?): String = formatear(iso, FECHA)
fun fechaHora(iso: Any?): String = formatear(iso, FECHA_HORA)

private fun formatear(iso: Any?, formato: DateTimeFormatter): String {
    val texto = iso?.toString()?.takeIf { it.isNotBlank() } ?: return "—"
    return runCatching { OffsetDateTime.parse(texto).format(formato) }
        .recoverCatching {
            // Las columnas DATE llegan como "2026-10-04", sin hora ni zona.
            java.time.LocalDate.parse(texto.take(10)).format(formato)
        }
        .getOrDefault(texto)
}

fun nombreCliente(cliente: Map<String, Any?>?): String {
    if (cliente.isNullOrEmpty()) return "Consumidor final"
    return (cliente.texto("nombres") + " " + cliente.texto("apellidos")).trim()
}

/**
 * Una linea de la factura que se esta armando en el punto de venta.
 *
 * El calculo se repite aqui porque el backend exige que los pagos sumen el total
 * exacto: el cliente tiene que llegar al mismo centavo. La cifra que manda es
 * siempre la del servidor; esta solo sirve para mostrar y para cobrar.
 */
data class Linea(
    val producto: Map<String, Any?>,
    var cantidad: Int = 1,
    val imei: String? = null,
    var descuento: BigDecimal = BigDecimal.ZERO,
) {
    val precio: BigDecimal get() = dinero(producto["precio_venta"])
    val bruto: BigDecimal get() = dinero(precio.multiply(BigDecimal(cantidad)))
    val base: BigDecimal get() = dinero(bruto.subtract(descuento))
    val iva: BigDecimal
        get() = dinero(base.multiply(dinero(producto["iva_porcentaje"]))
            .divide(BigDecimal(100), 4, RoundingMode.HALF_UP))
    val total: BigDecimal get() = dinero(base.add(iva))

    fun aMapa(): Map<String, Any?> = buildMap {
        put("producto_id", producto.entero("id"))
        put("cantidad", cantidad)
        put("descuento", descuento.toPlainString())
        if (imei != null) put("imei", imei)
    }
}
