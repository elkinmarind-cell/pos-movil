package pos

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxHeight
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.math.BigDecimal

private val METODOS = listOf("EFECTIVO", "DEBITO", "CREDITO", "TRANSFERENCIA",
    "NEQUI", "DAVIPLATA")

/**
 * Punto de venta.
 *
 * El carrito vive en `mutableStateListOf`: Compose observa la lista y vuelve a
 * pintar sola la parte que cambio cuando se agrega una linea o sube una
 * cantidad. No hay que avisarle a nadie ni redibujar la pantalla a mano.
 */
@Composable
fun PantallaPuntoVenta(api: Api) {
    val lineas = remember { mutableStateListOf<Linea>() }
    var productos by remember { mutableStateOf<List<Map<String, Any?>>>(emptyList()) }
    var clientes by remember { mutableStateOf<List<Map<String, Any?>>>(emptyList()) }
    var turno by remember { mutableStateOf<Map<String, Any?>?>(null) }
    var busqueda by remember { mutableStateOf("") }
    var clienteId by remember { mutableStateOf<Int?>(null) }
    var metodo by remember { mutableStateOf("EFECTIVO") }
    var observaciones by remember { mutableStateOf("") }
    var mensaje by remember { mutableStateOf<Pair<String, String>?>(null) }
    var ocupado by remember { mutableStateOf(false) }
    var eligiendoImei by remember { mutableStateOf<Map<String, Any?>?>(null) }
    var recarga by remember { mutableStateOf(0) }
    val alcance = rememberCoroutineScope()

    // Recalculado en cada composicion a partir del carrito: no hay un total
    // guardado que se pueda quedar desactualizado.
    val subtotal = lineas.fold(BigDecimal.ZERO) { s, l -> s.add(l.base) }
    val ivaTotal = lineas.fold(BigDecimal.ZERO) { s, l -> s.add(l.iva) }
    val total = dinero(subtotal.add(ivaTotal))

    fun cargar() {
        alcance.launch {
            try {
                val datos = withContext(Dispatchers.IO) {
                    Triple(api.productos(busqueda.trim().ifBlank { null }),
                        api.clientes(limite = 300), api.turno())
                }
                productos = datos.first
                clientes = datos.second
                turno = datos.third
            } catch (e: ErrorApi) {
                mensaje = "peligro" to e.mensaje
            }
        }
    }

    LaunchedEffect(recarga) { cargar() }

    fun agregar(producto: Map<String, Any?>) {
        if (producto.siNo("requiere_imei")) {
            eligiendoImei = producto
            return
        }
        val disponibles = producto.entero("disponibles")
        val existente = lineas.firstOrNull {
            it.producto.entero("id") == producto.entero("id") && it.imei == null
        }
        if (existente != null) {
            if (existente.cantidad + 1 > disponibles) {
                mensaje = "alerta" to
                        "Solo hay $disponibles unidades de '${producto.texto("nombre")}'."
                return
            }
            // Se reemplaza la linea en lugar de mutarla: la lista observable
            // detecta el cambio de elemento, no la mutacion interna de un objeto.
            lineas[lineas.indexOf(existente)] =
                existente.copy(cantidad = existente.cantidad + 1)
        } else {
            if (disponibles < 1) {
                mensaje = "alerta" to "'${producto.texto("nombre")}' esta agotado."
                return
            }
            lineas.add(Linea(producto))
        }
    }

    fun registrar() {
        if (lineas.isEmpty()) {
            mensaje = "alerta" to "La factura esta vacia."
            return
        }
        ocupado = true
        alcance.launch {
            try {
                val venta = withContext(Dispatchers.IO) {
                    api.registrarVenta(clienteId, lineas.toList(), metodo, observaciones)
                }
                lineas.clear()
                clienteId = null
                observaciones = ""
                mensaje = "exito" to ("Venta ${venta.texto("numero")} registrada por " +
                        pesos(venta["total"], true) + ".")
                recarga++
            } catch (e: ErrorApi) {
                mensaje = "peligro" to e.mensaje
            } finally {
                ocupado = false
            }
        }
    }

    Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Encabezado("Punto de venta",
            "Arma la factura, elige el medio de pago y registra la venta.")

        Aviso(
            if (turno != null)
                "Turno de caja abierto desde ${fechaHora(turno?.get("apertura"))} · " +
                        "base ${pesos(turno?.get("base_inicial"))}"
            else
                "No hay turno de caja abierto. El servidor no deja facturar sin turno.",
            if (turno != null) "exito" else "alerta",
        )
        mensaje?.let { (tono, texto) -> Aviso(texto, tono) }

        Row(Modifier.fillMaxSize(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {

            // ----------------------------------------------------- catalogo
            Panel(Modifier.weight(3f).fillMaxHeight()) {
                Column {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Campo(busqueda, { busqueda = it },
                            "Buscar por SKU, nombre o codigo de barras",
                            Modifier.weight(1f))
                        Spacer(Modifier.width(8.dp))
                        Boton("Buscar", { recarga++ }, tono = "neutro")
                    }
                    Spacer(Modifier.height(12.dp))
                    if (productos.isEmpty()) {
                        Vacio("Ningun producto coincide")
                    } else {
                        LazyColumn(Modifier.fillMaxSize()) {
                            items(productos.size) { i ->
                                FilaProducto(productos[i]) { agregar(productos[i]) }
                                Spacer(Modifier.height(6.dp))
                            }
                        }
                    }
                }
            }

            // ------------------------------------------------------ factura
            Panel(Modifier.weight(2f).fillMaxHeight()) {
                Column(Modifier.fillMaxSize()) {
                    Titulo("Factura", 15)
                    Spacer(Modifier.height(10.dp))

                    val opcionesCliente: List<Pair<Int?, String>> =
                        listOf<Pair<Int?, String>>(null to "Consumidor final") +
                                clientes.map { c ->
                                    c.entero("id") to
                                            "${nombreCliente(c)} · ${c.texto("numero_documento")}"
                                }
                    Selector("Cliente", opcionesCliente, clienteId) { clienteId = it }

                    Spacer(Modifier.height(10.dp))
                    Box(Modifier.weight(1f)) {
                        if (lineas.isEmpty()) {
                            Vacio("La factura esta vacia")
                        } else {
                            Column(Modifier.verticalScroll(rememberScrollState()),
                                verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                lineas.forEachIndexed { i, linea ->
                                    FilaCarrito(
                                        linea,
                                        alCambiar = { delta ->
                                            val nueva = linea.cantidad + delta
                                            val disp = linea.producto.entero("disponibles")
                                            when {
                                                nueva < 1 -> Unit
                                                nueva > disp -> mensaje = "alerta" to
                                                        "Solo hay $disp unidades disponibles."
                                                else -> lineas[i] = linea.copy(cantidad = nueva)
                                            }
                                        },
                                        alQuitar = { lineas.removeAt(i) },
                                    )
                                }
                            }
                        }
                    }

                    Box(Modifier.fillMaxWidth().height(1.dp).background(Tema.borde))
                    Spacer(Modifier.height(10.dp))
                    TotalFila("Subtotal", pesos(subtotal, true))
                    TotalFila("IVA", pesos(ivaTotal, true))
                    TotalFila("Total", pesos(total, true), fuerte = true)
                    Spacer(Modifier.height(10.dp))

                    Selector("Metodo de pago", METODOS.map { it to it.lowercase()
                        .replaceFirstChar { c -> c.uppercase() } }, metodo) { metodo = it }
                    Spacer(Modifier.height(8.dp))
                    Campo(observaciones, { observaciones = it }, "Observaciones (opcional)",
                        Modifier.fillMaxWidth())
                    Spacer(Modifier.height(10.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Boton("Vaciar", { lineas.clear() }, tono = "neutro")
                        Boton(if (ocupado) "Registrando..." else "Registrar venta",
                            { registrar() }, tono = "exito",
                            habilitado = !ocupado && lineas.isNotEmpty(),
                            modifier = Modifier.weight(1f))
                    }
                }
            }
        }
    }

    // Un equipo serializado se vende por unidad: hay que decir cual.
    eligiendoImei?.let { producto ->
        DialogoImei(api, producto, lineas.mapNotNull { it.imei }.toSet(),
            alElegir = { imei ->
                lineas.add(Linea(producto, 1, imei))
                eligiendoImei = null
            },
            alCerrar = { eligiendoImei = null },
            alFallar = { mensaje = "alerta" to it; eligiendoImei = null },
        )
    }
}

// --------------------------------------------------------------------- piezas

@Composable
private fun FilaProducto(producto: Map<String, Any?>, alAgregar: () -> Unit) {
    val disponibles = producto.entero("disponibles")
    val agotado = disponibles <= 0
    Row(
        Modifier.fillMaxWidth()
            .background(if (agotado) Tema.panel else Tema.panelSuave, Tema.radioSm)
            .border(1.dp, Tema.borde, Tema.radioSm)
            .let { if (agotado) it else it.clickable(onClick = alAgregar) }
            .padding(horizontal = 12.dp, vertical = 9.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column(Modifier.weight(1f)) {
            Dato(producto.texto("nombre"), FontWeight.SemiBold)
            Spacer(Modifier.height(3.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Text(producto.texto("sku"), fontSize = 11.sp, color = Tema.textoTenue)
                Spacer(Modifier.width(8.dp))
                Insignia(if (producto.siNo("requiere_imei")) "IMEI" else "STOCK",
                    if (producto.siNo("requiere_imei")) "acento" else "neutro")
                Spacer(Modifier.width(8.dp))
                Text("$disponibles disponibles", fontSize = 11.sp,
                    color = if (agotado) Tema.peligro else Tema.textoTenue)
            }
        }
        Column(horizontalAlignment = Alignment.End) {
            Text(pesos(producto["precio_venta"]), fontSize = 13.sp,
                fontWeight = FontWeight.Bold, color = Tema.texto)
            Text("IVA ${producto.decimal("iva_porcentaje").toBigInteger()}%",
                fontSize = 10.sp, color = Tema.textoTenue)
        }
    }
}

@Composable
private fun FilaCarrito(linea: Linea, alCambiar: (Int) -> Unit, alQuitar: () -> Unit) {
    Column(
        Modifier.fillMaxWidth()
            .background(Tema.panelSuave, Tema.radioSm)
            .border(1.dp, Tema.borde, Tema.radioSm)
            .padding(10.dp)
    ) {
        Row(verticalAlignment = Alignment.Top) {
            Column(Modifier.weight(1f)) {
                Dato(linea.producto.texto("nombre"), FontWeight.SemiBold)
                if (linea.imei != null) {
                    Text("IMEI ${linea.imei}", fontSize = 11.sp, color = Tema.acento)
                }
            }
            TextButton(onClick = alQuitar) {
                Text("Quitar", fontSize = 11.sp, color = Tema.peligro)
            }
        }
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            if (linea.imei == null) {
                TextButton(onClick = { alCambiar(-1) }) {
                    Text("−", fontSize = 16.sp, color = Tema.textoMedio)
                }
                Text("${linea.cantidad}", fontSize = 13.sp,
                    fontWeight = FontWeight.SemiBold, color = Tema.texto)
                TextButton(onClick = { alCambiar(1) }) {
                    Text("+", fontSize = 16.sp, color = Tema.acento)
                }
            }
            Spacer(Modifier.weight(1f))
            Column(horizontalAlignment = Alignment.End) {
                Text(pesos(linea.total), fontSize = 13.sp, fontWeight = FontWeight.Bold,
                    color = Tema.texto)
                Text("IVA ${pesos(linea.iva)}", fontSize = 10.sp, color = Tema.textoTenue)
            }
        }
    }
}

@Composable
private fun TotalFila(etiqueta: String, valor: String, fuerte: Boolean = false) {
    Row(Modifier.fillMaxWidth().padding(vertical = 2.dp),
        verticalAlignment = Alignment.CenterVertically) {
        Text(etiqueta, fontSize = if (fuerte) 15.sp else 13.sp,
            color = if (fuerte) Tema.texto else Tema.textoMedio,
            fontWeight = if (fuerte) FontWeight.SemiBold else FontWeight.Normal,
            modifier = Modifier.weight(1f))
        Text(valor, fontSize = if (fuerte) 19.sp else 13.sp,
            fontWeight = if (fuerte) FontWeight.Bold else FontWeight.SemiBold,
            color = Tema.texto)
    }
}

/**
 * Desplegable hecho con un dialogo.
 *
 * Material 3 trae `ExposedDropdownMenuBox`, pero su API es experimental y cambia
 * entre versiones; esto hace lo mismo con piezas estables.
 */
@Composable
private fun <T> Selector(
    etiqueta: String,
    opciones: List<Pair<T, String>>,
    valor: T,
    alElegir: (T) -> Unit,
) {
    var abierto by remember { mutableStateOf(false) }
    val textoActual = opciones.firstOrNull { it.first == valor }?.second ?: "—"

    Column(Modifier.fillMaxWidth()) {
        Rotulo(etiqueta)
        Spacer(Modifier.height(4.dp))
        Row(
            Modifier.fillMaxWidth()
                .background(Tema.panel, Tema.radioSm)
                .border(1.dp, Tema.bordeFuerte, Tema.radioSm)
                .clickable { abierto = true }
                .padding(horizontal = 12.dp, vertical = 11.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Box(Modifier.weight(1f)) { Dato(textoActual) }
            Text("▾", fontSize = 13.sp, color = Tema.textoMedio)
        }
    }

    if (abierto) {
        AlertDialog(
            onDismissRequest = { abierto = false },
            confirmButton = {
                TextButton(onClick = { abierto = false }) { Text("Cancelar") }
            },
            title = { Titulo(etiqueta, 16) },
            text = {
                LazyColumn(Modifier.fillMaxWidth().height(320.dp)) {
                    items(opciones.size) { i ->
                        val (clave, texto) = opciones[i]
                        Row(
                            Modifier.fillMaxWidth()
                                .background(
                                    if (clave == valor) Tema.acentoSuave else Color.Transparent,
                                    Tema.radioSm,
                                )
                                .clickable { alElegir(clave); abierto = false }
                                .padding(horizontal = 12.dp, vertical = 11.dp)
                        ) {
                            Text(texto, fontSize = 13.sp,
                                color = if (clave == valor) Tema.acento else Tema.texto)
                        }
                    }
                }
            },
            containerColor = Tema.panel,
        )
    }
}

@Composable
private fun DialogoImei(
    api: Api,
    producto: Map<String, Any?>,
    yaUsados: Set<String>,
    alElegir: (String) -> Unit,
    alCerrar: () -> Unit,
    alFallar: (String) -> Unit,
) {
    AlertDialog(
        onDismissRequest = alCerrar,
        confirmButton = { TextButton(onClick = alCerrar) { Text("Cancelar") } },
        title = { Titulo("IMEI disponibles · ${producto.texto("nombre")}", 16) },
        text = {
            Cargador(producto.entero("id"), {
                api.equipos(productoId = producto.entero("id"), estado = "DISPONIBLE")
            }) { todos ->
                val libres = todos.filter { it.texto("imei") !in yaUsados }
                LaunchedEffect(libres.isEmpty()) {
                    if (libres.isEmpty()) {
                        alFallar("No quedan equipos disponibles de " +
                                "'${producto.texto("nombre")}'.")
                    }
                }
                if (libres.isNotEmpty()) {
                    LazyColumn(Modifier.fillMaxWidth().height(320.dp)) {
                        items(libres.size) { i ->
                            val e = libres[i]
                            Row(
                                Modifier.fillMaxWidth()
                                    .clickable { alElegir(e.texto("imei")) }
                                    .padding(horizontal = 10.dp, vertical = 12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                            ) {
                                Box(Modifier.weight(2f)) {
                                    Dato(e.texto("imei"), FontWeight.SemiBold)
                                }
                                Box(Modifier.weight(1f)) { Dato(e.texto("color", "—")) }
                                Box(Modifier.weight(1f)) {
                                    Dato(
                                        if (e["almacenamiento_gb"] != null)
                                            "${e.entero("almacenamiento_gb")} GB" else "—"
                                    )
                                }
                                Text("Elegir", fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold, color = Tema.acento)
                            }
                            Box(Modifier.fillMaxWidth().height(1.dp)
                                .background(Tema.borde))
                        }
                    }
                }
            }
        },
        containerColor = Tema.panel,
    )
}
