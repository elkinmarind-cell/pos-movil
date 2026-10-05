package pos

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.heightIn
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextFieldDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// --------------------------------------------------------------------- texto

@Composable
fun Titulo(texto: String, tamano: Int = 20) =
    Text(texto, fontSize = tamano.sp, fontWeight = FontWeight.SemiBold, color = Tema.texto)

@Composable
fun Subtitulo(texto: String) =
    Text(texto, fontSize = 13.sp, color = Tema.textoTenue)

@Composable
fun Rotulo(texto: String) =
    Text(texto.uppercase(), fontSize = 10.sp, fontWeight = FontWeight.SemiBold,
        color = Tema.textoTenue)

@Composable
fun Dato(
    texto: String,
    peso: FontWeight = FontWeight.Normal,
    color: Color = Tema.texto,
    tamano: Int = 13,
) = Text(texto, fontSize = tamano.sp, fontWeight = peso, color = color,
    maxLines = 1, overflow = TextOverflow.Ellipsis)

// -------------------------------------------------------------------- avisos

@Composable
fun Aviso(texto: String, tono: String = "acento", modifier: Modifier = Modifier) {
    val (color, fondo) = Tema.tono(tono)
    Box(
        modifier = modifier
            .fillMaxWidth()
            .background(fondo, Tema.radioSm)
            .border(1.dp, color.copy(alpha = 0.22f), Tema.radioSm)
            .padding(horizontal = 12.dp, vertical = 10.dp)
    ) {
        Text(texto, fontSize = 13.sp, color = color)
    }
}

@Composable
fun Vacio(texto: String = "No hay datos para mostrar") {
    Box(Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
        Text(texto, fontSize = 13.sp, color = Tema.textoTenue)
    }
}

@Composable
fun Cargando(texto: String = "Cargando...") {
    Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            CircularProgressIndicator(Modifier.size(28.dp), color = Tema.acento,
                strokeWidth = 3.dp)
            Spacer(Modifier.height(12.dp))
            Text(texto, fontSize = 13.sp, color = Tema.textoTenue)
        }
    }
}

// ------------------------------------------------------------------ entradas

@Composable
fun Boton(
    texto: String,
    alHacerClic: () -> Unit,
    tono: String = "acento",
    habilitado: Boolean = true,
    modifier: Modifier = Modifier,
) {
    val fondo = when (tono) {
        "exito" -> Tema.exito
        "peligro" -> Tema.peligro
        "neutro" -> Tema.panel
        else -> Tema.acento
    }
    val color = if (tono == "neutro") Tema.textoMedio else Color.White
    Button(
        onClick = alHacerClic,
        enabled = habilitado,
        shape = Tema.radioSm,
        colors = ButtonDefaults.buttonColors(
            containerColor = fondo,
            contentColor = color,
            disabledContainerColor = Tema.borde,
            disabledContentColor = Tema.textoTenue,
        ),
        contentPadding = PaddingValues(horizontal = 18.dp, vertical = 12.dp),
        modifier = modifier.then(
            if (tono == "neutro") Modifier.border(1.dp, Tema.bordeFuerte, Tema.radioSm)
            else Modifier
        ),
    ) {
        Text(texto, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
fun Campo(
    valor: String,
    alCambiar: (String) -> Unit,
    etiqueta: String,
    modifier: Modifier = Modifier,
    clave: Boolean = false,
    habilitado: Boolean = true,
) {
    OutlinedTextField(
        value = valor,
        onValueChange = alCambiar,
        label = { Text(etiqueta, fontSize = 12.sp) },
        singleLine = true,
        enabled = habilitado,
        shape = Tema.radioSm,
        visualTransformation =
            if (clave) PasswordVisualTransformation() else VisualTransformation.None,
        colors = TextFieldDefaults.colors(
            focusedContainerColor = Tema.panel,
            unfocusedContainerColor = Tema.panel,
            disabledContainerColor = Tema.panelSuave,
            focusedIndicatorColor = Tema.acento,
            unfocusedIndicatorColor = Tema.bordeFuerte,
            focusedTextColor = Tema.texto,
            unfocusedTextColor = Tema.texto,
            focusedLabelColor = Tema.acento,
            unfocusedLabelColor = Tema.textoMedio,
        ),
        modifier = modifier,
    )
}

// ------------------------------------------------------------------ tableros

@Composable
fun Kpi(
    etiqueta: String,
    valor: String,
    tono: String = "acento",
    pie: String? = null,
    modifier: Modifier = Modifier,
) {
    val (color, fondo) = Tema.tono(tono)
    Panel(modifier = modifier, relleno = PaddingValues(14.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            // Marca de color en lugar de un icono: menos dependencias y el
            // significado lo da el tono, igual que en los otros dos clientes.
            Box(Modifier.width(4.dp).height(38.dp)
                .background(color, RoundedCornerShape(99.dp)))
            Spacer(Modifier.width(12.dp))
            Column {
                Rotulo(etiqueta)
                Text(valor, fontSize = 19.sp, fontWeight = FontWeight.Bold,
                    color = Tema.texto, maxLines = 1, overflow = TextOverflow.Ellipsis)
                if (pie != null) {
                    Text(pie, fontSize = 11.sp, color = Tema.textoTenue,
                        maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
            }
            Spacer(Modifier.width(8.dp))
            Box(Modifier.size(8.dp).background(fondo, RoundedCornerShape(99.dp)))
        }
    }
}

// -------------------------------------------------------------------- tablas

data class Columna(val titulo: String, val peso: Float = 1f)

/**
 * Tabla con encabezado fijo y cuerpo desplazable.
 *
 * Las celdas llegan como funciones composables, no como texto, para que una
 * columna pueda traer una insignia de color o un boton sin inventar un sistema
 * de plantillas.
 */
@Composable
fun Tabla(
    columnas: List<Columna>,
    filas: List<List<@Composable () -> Unit>>,
    vacia: String = "No hay registros",
    modifier: Modifier = Modifier,
) {
    Column(modifier.fillMaxWidth()) {
        Row(
            Modifier.fillMaxWidth()
                .background(Tema.panelSuave, RoundedCornerShape(6.dp))
                .padding(horizontal = 10.dp, vertical = 8.dp)
        ) {
            columnas.forEach { c ->
                Box(Modifier.weight(c.peso)) {
                    Text(c.titulo, fontSize = 11.sp, fontWeight = FontWeight.SemiBold,
                        color = Tema.textoTenue)
                }
            }
        }
        if (filas.isEmpty()) {
            Vacio(vacia)
            return@Column
        }
        LazyColumn(Modifier.fillMaxWidth().heightIn(max = 2000.dp)) {
            items(filas.size) { i ->
                Row(
                    Modifier.fillMaxWidth()
                        .background(if (i % 2 == 0) Tema.panel else Tema.panelSuave)
                        .padding(horizontal = 10.dp, vertical = 11.dp),
                    verticalAlignment = Alignment.CenterVertically,
                ) {
                    filas[i].forEachIndexed { j, celda ->
                        Box(Modifier.weight(columnas.getOrElse(j) { Columna("") }.peso)) {
                            celda()
                        }
                    }
                }
                Box(Modifier.fillMaxWidth().height(1.dp).background(Tema.borde))
            }
        }
    }
}

/** Fila de menu del panel lateral. */
@Composable
fun OpcionMenu(texto: String, activa: Boolean, alElegir: () -> Unit) {
    Row(
        Modifier.fillMaxWidth()
            .background(if (activa) Tema.acentoSuave else Color.Transparent, Tema.radioSm)
            .clickable(onClick = alElegir)
            .padding(horizontal = 10.dp, vertical = 9.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.Start,
    ) {
        Box(Modifier.size(6.dp)
            .background(if (activa) Tema.acento else Tema.bordeFuerte,
                RoundedCornerShape(99.dp)))
        Spacer(Modifier.width(10.dp))
        Text(
            texto,
            fontSize = 13.sp,
            fontWeight = if (activa) FontWeight.SemiBold else FontWeight.Medium,
            color = if (activa) Tema.acento else Tema.textoMedio,
        )
    }
}

/** Barra horizontal simple, para comparar magnitudes sin libreria de graficos. */
@Composable
fun Barra(parte: Double, total: Double, color: Color = Tema.acento, ancho: Int = 150) {
    val fraccion = if (total <= 0.0) 0.0 else (parte / total).coerceIn(0.0, 1.0)
    Box(
        Modifier.width(ancho.dp).height(8.dp)
            .background(Tema.neutroSuave, RoundedCornerShape(99.dp))
    ) {
        Box(
            Modifier.width((ancho * fraccion).dp.coerceAtLeast(2.dp)).height(8.dp)
                .background(color, RoundedCornerShape(99.dp))
        )
    }
}
