package pos

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.DpSize
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Window
import androidx.compose.ui.window.application
import androidx.compose.ui.window.rememberWindowState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Aplicacion de escritorio del POS Movil escrita en Kotlin con Compose Desktop.
 *
 * Consume la misma API que la interfaz web y que la aplicacion de Flet, con el
 * mismo diseno. Lo que cambia es la tecnologia, no el producto: eso es
 * justamente lo que se quiere mostrar.
 *
 *   gradlew run              abre la aplicacion
 *   gradlew packageMsi       genera el instalador para Windows
 */

/** Un modulo del sistema: su nombre, su grupo en el menu y que permiso exige. */
data class Modulo(
    val clave: String,
    val titulo: String,
    val grupo: String,
    val permisos: List<String>,
)

val MODULOS = listOf(
    Modulo("tablero", "Tablero", "Operacion", listOf("reportes.ver")),
    Modulo("punto-venta", "Punto de venta", "Operacion", listOf("ventas.crear")),
    Modulo("ventas", "Ventas", "Operacion", listOf("ventas.ver")),
    Modulo("inventario", "Inventario", "Inventario", listOf("inventario.ver")),
    Modulo("clientes", "Clientes", "Clientes", listOf("clientes.ver")),
    Modulo("garantias", "Garantias", "Clientes", listOf("garantias.ver")),
    Modulo("usuarios", "Usuarios", "Direccion", listOf("usuarios.ver")),
)

val GRUPOS = listOf("Operacion", "Inventario", "Clientes", "Direccion")

fun main() = application {
    Window(
        onCloseRequest = ::exitApplication,
        title = "POS Movil · Gestion y venta de dispositivos moviles",
        state = rememberWindowState(size = DpSize(1340.dp, 840.dp)),
    ) {
        TemaPos {
            Aplicacion()
        }
    }
}

@Composable
fun Aplicacion() {
    val api = remember { Api() }
    var dentro by remember { mutableStateOf(false) }
    var modulo by remember { mutableStateOf("tablero") }

    if (!dentro) {
        Ingreso(api) {
            // Al entrar se abre el primer modulo que el rol pueda ver: un cajero
            // no tiene tablero, asi que caer siempre en "tablero" lo dejaria
            // mirando una pantalla vacia.
            modulo = MODULOS.firstOrNull { m -> api.puede(*m.permisos.toTypedArray()) }
                ?.clave ?: "tablero"
            dentro = true
        }
        return
    }

    Row(Modifier.fillMaxSize().background(Tema.fondo)) {
        Lateral(api, modulo, alElegir = { modulo = it }, alSalir = {
            api.salir()
            dentro = false
        })
        Box(Modifier.fillMaxSize().padding(horizontal = 22.dp, vertical = 18.dp)) {
            when (modulo) {
                "tablero" -> PantallaTablero(api)
                "punto-venta" -> PantallaPuntoVenta(api)
                "ventas" -> PantallaVentas(api)
                "inventario" -> PantallaInventario(api)
                "clientes" -> PantallaClientes(api)
                "garantias" -> PantallaGarantias(api)
                "usuarios" -> PantallaUsuarios(api)
            }
        }
    }
}

// --------------------------------------------------------------------- login

@Composable
fun Ingreso(api: Api, alEntrar: () -> Unit) {
    var usuario by remember { mutableStateOf("") }
    var clave by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var ocupado by remember { mutableStateOf(false) }
    var servidor by remember { mutableStateOf<Pair<String, String>?>(null) }
    val alcance = rememberCoroutineScope()

    // Se consulta el estado del servidor apenas abre la ventana: si el backend
    // esta apagado, mejor decirlo antes de que escriba la contrasena.
    LaunchedEffect(Unit) {
        servidor = try {
            val s = withContext(Dispatchers.IO) { api.salud() }
            "exito" to ("Servidor conectado · PostgreSQL " +
                    s.texto("postgresql").substringBefore(' ') +
                    " · " + s.entero("tablas") + " tablas")
        } catch (e: ErrorApi) {
            "peligro" to e.mensaje
        }
    }

    fun entrar() {
        if (ocupado) return
        ocupado = true
        error = null
        alcance.launch {
            try {
                withContext(Dispatchers.IO) { api.entrar(usuario.trim(), clave) }
                alEntrar()
            } catch (e: ErrorApi) {
                error = e.mensaje
            } finally {
                ocupado = false
            }
        }
    }

    Box(Modifier.fillMaxSize().background(Tema.fondo), contentAlignment = Alignment.Center) {
        Panel(Modifier.width(400.dp), relleno = PaddingValues(26.dp)) {
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Box(
                        Modifier.width(42.dp).height(42.dp)
                            .background(Tema.acento, Tema.radioSm),
                        contentAlignment = Alignment.Center,
                    ) {
                        Text("POS", color = Color.White, fontSize = 13.sp,
                            fontWeight = FontWeight.Bold)
                    }
                    Spacer(Modifier.width(12.dp))
                    Column {
                        Titulo("POS Movil", 19)
                        Subtitulo("Gestion y venta de dispositivos moviles")
                    }
                }
                Box(Modifier.fillMaxWidth().height(1.dp).background(Tema.borde))
                Campo(usuario, { usuario = it }, "Usuario", Modifier.fillMaxWidth(),
                    habilitado = !ocupado)
                Campo(clave, { clave = it }, "Contrasena", Modifier.fillMaxWidth(),
                    clave = true, habilitado = !ocupado)
                if (error != null) Aviso(error!!, "peligro")
                Boton(if (ocupado) "Entrando..." else "Entrar", { entrar() },
                    habilitado = !ocupado, modifier = Modifier.fillMaxWidth())
                servidor?.let { (tono, texto) -> Aviso(texto, tono) }
            }
        }
    }
}

// ------------------------------------------------------------------- lateral

@Composable
fun Lateral(api: Api, actual: String, alElegir: (String) -> Unit, alSalir: () -> Unit) {
    val visibles = MODULOS.filter { api.puede(*it.permisos.toTypedArray()) }
    Column(
        Modifier.width(236.dp).fillMaxHeight()
            .background(Tema.panel)
            .border(1.dp, Tema.borde)
            .padding(horizontal = 14.dp, vertical = 16.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                Modifier.width(34.dp).height(34.dp)
                    .background(Tema.acento, RoundedCornerShape(6.dp)),
                contentAlignment = Alignment.Center,
            ) {
                Text("POS", color = Color.White, fontSize = 11.sp,
                    fontWeight = FontWeight.Bold)
            }
            Spacer(Modifier.width(10.dp))
            Column {
                Text("POS Movil", fontSize = 14.sp, fontWeight = FontWeight.Bold,
                    color = Tema.texto)
                Text("Dispositivos moviles", fontSize = 10.sp, color = Tema.textoTenue)
            }
        }
        Spacer(Modifier.height(14.dp))
        Box(Modifier.fillMaxWidth().height(1.dp).background(Tema.borde))

        Column(Modifier.weight(1f).padding(top = 10.dp)) {
            GRUPOS.forEach { grupo ->
                val delGrupo = visibles.filter { it.grupo == grupo }
                if (delGrupo.isEmpty()) return@forEach
                Box(Modifier.padding(start = 8.dp, top = 10.dp, bottom = 3.dp)) {
                    Rotulo(grupo)
                }
                delGrupo.forEach { m ->
                    OpcionMenu(m.titulo, m.clave == actual) { alElegir(m.clave) }
                }
            }
        }

        Box(Modifier.fillMaxWidth().height(1.dp).background(Tema.borde))
        Spacer(Modifier.height(12.dp))
        Text(api.nombre, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
            color = Tema.texto)
        Text(api.rol.lowercase().replaceFirstChar { it.uppercase() },
            fontSize = 10.sp, color = Tema.textoTenue)
        Spacer(Modifier.height(10.dp))
        Boton("Cerrar sesion", alSalir, tono = "neutro",
            modifier = Modifier.fillMaxWidth())
    }
}

// ------------------------------------------------------------------- cargador

/**
 * Pide datos al servidor fuera del hilo de la interfaz y pinta uno de tres
 * estados: cargando, error o contenido. Sin esto cada pantalla repetiria el
 * mismo try/catch y una peticion lenta congelaria la ventana.
 *
 * `clave` es lo que dispara una recarga: cambiarla (por ejemplo, el texto de
 * busqueda o un contador de refresco) vuelve a ejecutar la consulta.
 */
@Composable
fun <T> Cargador(
    clave: Any?,
    obtener: suspend () -> T,
    contenido: @Composable (T) -> Unit,
) {
    var valor by remember(clave) { mutableStateOf<T?>(null) }
    var error by remember(clave) { mutableStateOf<String?>(null) }

    LaunchedEffect(clave) {
        error = null
        valor = null
        try {
            valor = withContext(Dispatchers.IO) { obtener() }
        } catch (e: ErrorApi) {
            error = e.mensaje
        } catch (e: Exception) {
            error = "Error inesperado: ${e.message}"
        }
    }

    val actual = valor
    when {
        error != null -> Aviso(error!!, "peligro")
        actual == null -> Cargando()
        else -> contenido(actual)
    }
}

/** Franja superior de cada pantalla: titulo, contexto y acciones. */
@Composable
fun Encabezado(titulo: String, descripcion: String, acciones: @Composable () -> Unit = {}) {
    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
        Column(Modifier.weight(1f)) {
            Titulo(titulo)
            Subtitulo(descripcion)
        }
        acciones()
    }
}
