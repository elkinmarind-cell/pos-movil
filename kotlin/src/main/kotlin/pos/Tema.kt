package pos

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * Los mismos colores de la interfaz web y de la aplicacion de Flet.
 * Tres clientes distintos, un solo lenguaje visual.
 */
object Tema {
    val fondo = Color(0xFFF1F5F9)
    val panel = Color(0xFFFFFFFF)
    val panelSuave = Color(0xFFF8FAFC)
    val borde = Color(0xFFE2E8F0)
    val bordeFuerte = Color(0xFFCBD5E1)

    val texto = Color(0xFF0F172A)
    val textoMedio = Color(0xFF475569)
    val textoTenue = Color(0xFF64748B)

    val acento = Color(0xFF1D4ED8)
    val acentoFuerte = Color(0xFF1E40AF)
    val acentoSuave = Color(0xFFEFF6FF)
    val exito = Color(0xFF047857)
    val exitoSuave = Color(0xFFECFDF5)
    val alerta = Color(0xFFB45309)
    val alertaSuave = Color(0xFFFFFBEB)
    val peligro = Color(0xFFB91C1C)
    val peligroSuave = Color(0xFFFEF2F2)
    val neutroSuave = Color(0xFFF1F5F9)

    val radio = RoundedCornerShape(10.dp)
    val radioSm = RoundedCornerShape(7.dp)

    /** Pareja (texto, fondo) de cada tono. */
    fun tono(nombre: String): Pair<Color, Color> = when (nombre) {
        "exito" -> exito to exitoSuave
        "alerta" -> alerta to alertaSuave
        "peligro" -> peligro to peligroSuave
        "acento" -> acento to acentoSuave
        else -> textoMedio to neutroSuave
    }

    /** Estado de negocio -> tono visual. La misma tabla en los tres clientes. */
    fun tonoDeEstado(estado: String): String = when (estado.uppercase()) {
        "DISPONIBLE", "COMPLETADA", "VIGENTE", "ABIERTO", "ACTIVA" -> "exito"
        "APARTADO", "RESERVADO", "RECIBIDA" -> "acento"
        "EN_SERVICIO", "EN_RECLAMACION", "PENDIENTE", "DIAGNOSTICO", "REPARACION" -> "alerta"
        "ANULADA", "VENCIDA", "DEVUELTO", "DADO_DE_BAJA", "CANCELADO" -> "peligro"
        else -> "neutro"
    }
}

@Composable
fun TemaPos(contenido: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = lightColorScheme(
            primary = Tema.acento,
            onPrimary = Color.White,
            primaryContainer = Tema.acentoSuave,
            onPrimaryContainer = Tema.acentoFuerte,
            secondary = Tema.textoMedio,
            onSecondary = Color.White,
            error = Tema.peligro,
            onError = Color.White,
            background = Tema.fondo,
            onBackground = Tema.texto,
            surface = Tema.panel,
            onSurface = Tema.texto,
            onSurfaceVariant = Tema.textoMedio,
            outline = Tema.bordeFuerte,
            outlineVariant = Tema.borde,
        ),
        content = contenido,
    )
}

/** Pildora de color con un estado de negocio. */
@Composable
fun Insignia(estado: String, tonoForzado: String? = null) {
    val (color, fondo) = Tema.tono(tonoForzado ?: Tema.tonoDeEstado(estado))
    Box(
        modifier = Modifier
            .background(fondo, RoundedCornerShape(99.dp))
            .padding(horizontal = 9.dp, vertical = 4.dp)
    ) {
        Text(
            estado.replace('_', ' '),
            color = color,
            fontSize = 11.sp,
            fontWeight = FontWeight.SemiBold,
        )
    }
}

/** Tarjeta blanca con borde suave: la unidad de composicion de las pantallas. */
@Composable
fun Panel(
    modifier: Modifier = Modifier,
    relleno: PaddingValues = PaddingValues(16.dp),
    contenido: @Composable () -> Unit,
) {
    Box(
        modifier = modifier
            .background(Tema.panel, Tema.radio)
            .border(1.dp, Tema.borde, Tema.radio)
            .padding(relleno)
    ) {
        contenido()
    }
}
