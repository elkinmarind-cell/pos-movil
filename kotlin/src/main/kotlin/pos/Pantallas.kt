package pos

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

// ===========================================================================
// Tablero
// ===========================================================================

/** Lo que el tablero necesita, pedido de una sola vez. */
private data class DatosTablero(
    val resumen: Map<String, Any?>,
    val dias: List<Map<String, Any?>>,
    val vendidos: List<Map<String, Any?>>,
    val alertas: List<Map<String, Any?>>,
)

@Composable
fun PantallaTablero(api: Api) {
    var refresco by remember { mutableStateOf(0) }

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()),
        verticalArrangement = Arrangement.spacedBy(14.dp),
    ) {
        Encabezado(
            "Tablero",
            "Hola, ${api.nombre.substringBefore(' ')}. Sesion como ${api.rol.lowercase()}.",
        ) {
            Boton("Actualizar", { refresco++ }, tono = "neutro")
        }

        Cargador(refresco, {
            // Las cuatro consultas se hacen de una vez y se pintan juntas: asi la
            // pantalla no aparece a pedazos.
            DatosTablero(api.tablero(), api.ventasPorDia(14),
                api.masVendidos(5, 30), api.alertasStock())
        }) { datos ->
            val d = datos.resumen
            val dias = datos.dias
            val vendidos = datos.vendidos
            val alertas = datos.alertas

            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Aviso(
                    if (d.siNo("turno_abierto"))
                        "Tienes un turno de caja abierto. Puedes facturar."
                    else
                        "No hay turno de caja abierto. Abre uno antes de facturar.",
                    if (d.siNo("turno_abierto")) "exito" else "alerta",
                )

                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Kpi("Ventas de hoy", pesos(d["ventas_hoy"]), "acento",
                        "${d.entero("numero_ventas_hoy")} facturas", Modifier.weight(1f))
                    Kpi("Ventas del mes", pesos(d["ventas_mes"]), "exito",
                        "ticket ${pesos(d["ticket_promedio_mes"])}", Modifier.weight(1f))
                    Kpi("Equipos disponibles", entero(d["equipos_disponibles"]), "neutro",
                        "unidades con IMEI libre", Modifier.weight(1f))
                    Kpi("Garantias vigentes", entero(d["garantias_vigentes"]), "acento",
                        "Ley 1480 de 2011", Modifier.weight(1f))
                }
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Kpi("Bajo stock", entero(d["productos_bajo_stock"]), "alerta",
                        "en o bajo el minimo", Modifier.weight(1f))
                    Kpi("Servicio tecnico", entero(d["ordenes_servicio_abiertas"]),
                        "alerta", "ordenes abiertas", Modifier.weight(1f))
                    Kpi("Apartados", entero(d["apartados_vigentes"]), "acento",
                        "con saldo pendiente", Modifier.weight(1f))
                    Kpi("Alertas IoT", entero(d["alertas_sin_atender"]), "peligro",
                        "sin atender", Modifier.weight(1f))
                }

                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Panel(Modifier.weight(3f)) { GraficoVentas(dias) }
                    Panel(Modifier.weight(2f)) { MasVendidos(vendidos) }
                }

                Panel(Modifier.fillMaxWidth()) {
                    Column {
                        Titulo("Alertas de inventario", 15)
                        Spacer(Modifier.height(10.dp))
                        Tabla(
                            listOf(Columna("SKU", 1f), Columna("Producto", 3f),
                                Columna("Disponibles", 1f), Columna("Minimo", 1f)),
                            alertas.map { a ->
                                listOf<@Composable () -> Unit>(
                                    { Dato(a.texto("sku"), FontWeight.SemiBold) },
                                    { Dato(a.texto("nombre")) },
                                    {
                                        Dato(entero(a["disponibles"]), FontWeight.SemiBold,
                                            if (a.entero("disponibles") == 0) Tema.peligro
                                            else Tema.alerta)
                                    },
                                    { Dato(entero(a["stock_minimo"])) },
                                )
                            },
                            "Ningun producto esta por debajo del minimo",
                        )
                    }
                }
            }
        }
    }
}

/** Barras verticales dibujadas con cajas: catorce rectangulos no justifican una libreria. */
@Composable
private fun GraficoVentas(dias: List<Map<String, Any?>>) {
    val montos = dias.map { it.decimal("total").toDouble() }
    val techo = montos.maxOrNull() ?: 0.0
    Column {
        Titulo("Ventas de los ultimos 14 dias", 15)
        Spacer(Modifier.height(14.dp))
        if (techo <= 0.0) {
            Vacio("Sin ventas registradas en el periodo")
            return@Column
        }
        Row(
            Modifier.fillMaxWidth().height(150.dp),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalAlignment = Alignment.Bottom,
        ) {
            dias.forEachIndexed { i, registro ->
                val alto = (130.0 * (montos[i] / techo)).coerceAtLeast(2.0)
                Column(
                    Modifier.weight(1f),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Bottom,
                ) {
                    Box(
                        Modifier.fillMaxWidth().height(alto.dp)
                            .background(
                                if (montos[i] > 0) Tema.acento else Tema.borde,
                                RoundedCornerShape(topStart = 4.dp, topEnd = 4.dp),
                            )
                    )
                    Spacer(Modifier.height(5.dp))
                    Text(registro.texto("fecha").takeLast(2), fontSize = 10.sp,
                        color = Tema.textoTenue)
                }
            }
        }
        Spacer(Modifier.height(10.dp))
        Text(
            "Total del periodo: ${pesos(montos.sum())}  ·  maximo diario: ${pesos(techo)}",
            fontSize = 11.sp, color = Tema.textoTenue,
        )
    }
}

@Composable
private fun MasVendidos(filas: List<Map<String, Any?>>) {
    Column {
        Titulo("Mas vendidos (30 dias)", 15)
        Spacer(Modifier.height(14.dp))
        if (filas.isEmpty()) {
            Vacio("Sin ventas en los ultimos 30 dias")
            return@Column
        }
        val techo = filas.maxOf { it.entero("unidades") }.coerceAtLeast(1)
        Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
            filas.forEach { f ->
                Column {
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Box(Modifier.weight(1f)) { Dato(f.texto("nombre"), tamano = 12) }
                        Text("${f.entero("unidades")} u.", fontSize = 12.sp,
                            fontWeight = FontWeight.SemiBold, color = Tema.textoMedio)
                    }
                    Spacer(Modifier.height(4.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Barra(f.entero("unidades").toDouble(), techo.toDouble())
                        Spacer(Modifier.width(10.dp))
                        Text(pesos(f["total_vendido"]), fontSize = 11.sp,
                            color = Tema.textoTenue)
                    }
                }
            }
        }
    }
}

// ===========================================================================
// Inventario
// ===========================================================================

@Composable
fun PantallaInventario(api: Api) {
    var pestana by remember { mutableStateOf(0) }
    var busqueda by remember { mutableStateOf("") }
    var aplicada by remember { mutableStateOf("") }

    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Encabezado("Inventario",
            "Un accesorio se cuenta por unidades; un equipo se identifica por IMEI.")

        Row(horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Boton("Productos", { pestana = 0 },
                tono = if (pestana == 0) "acento" else "neutro")
            Boton("Equipos por IMEI", { pestana = 1 },
                tono = if (pestana == 1) "acento" else "neutro")
            Spacer(Modifier.width(10.dp))
            Campo(busqueda, { busqueda = it },
                if (pestana == 0) "Buscar producto" else "Buscar por IMEI o RFID",
                Modifier.width(300.dp))
            Boton("Buscar", { aplicada = busqueda.trim() }, tono = "neutro")
        }

        Panel(Modifier.fillMaxSize()) {
            if (pestana == 0) {
                Cargador("prod:$aplicada", { api.productos(aplicada.ifBlank { null }) }) { lista ->
                    Column {
                        Titulo("${lista.size} productos", 15)
                        Spacer(Modifier.height(10.dp))
                        Tabla(
                            listOf(Columna("SKU", 1f), Columna("Producto", 3f),
                                Columna("Marca", 1.2f), Columna("Precio", 1.3f),
                                Columna("Disponibles", 1f), Columna("Tipo", 1f)),
                            lista.map { p ->
                                val disp = p.entero("disponibles")
                                val minimo = p.entero("stock_minimo")
                                listOf<@Composable () -> Unit>(
                                    { Dato(p.texto("sku"), FontWeight.SemiBold) },
                                    { Dato(p.texto("nombre")) },
                                    { Dato(p.sub("marca").texto("nombre", "—")) },
                                    { Dato(pesos(p["precio_venta"])) },
                                    {
                                        Dato(entero(disp), FontWeight.SemiBold,
                                            when {
                                                disp == 0 -> Tema.peligro
                                                disp <= minimo -> Tema.alerta
                                                else -> Tema.exito
                                            })
                                    },
                                    {
                                        Insignia(if (p.siNo("requiere_imei")) "IMEI" else "STOCK",
                                            if (p.siNo("requiere_imei")) "acento" else "neutro")
                                    },
                                )
                            },
                            "Ningun producto coincide con la busqueda",
                        )
                    }
                }
            } else {
                Cargador("imei:$aplicada", { api.equipos(q = aplicada.ifBlank { null }) }) { lista ->
                    Column {
                        Titulo("${lista.size} equipos", 15)
                        Spacer(Modifier.height(10.dp))
                        Tabla(
                            listOf(Columna("IMEI", 1.6f), Columna("Producto", 2.6f),
                                Columna("Color", 1f), Columna("Costo", 1.2f),
                                Columna("Estado", 1.3f), Columna("Ingreso", 1.2f)),
                            lista.map { e ->
                                listOf<@Composable () -> Unit>(
                                    { Dato(e.texto("imei"), FontWeight.SemiBold) },
                                    { Dato(e.sub("producto").texto("nombre", "—")) },
                                    { Dato(e.texto("color", "—")) },
                                    { Dato(pesos(e["costo"])) },
                                    { Insignia(e.texto("estado")) },
                                    { Dato(fecha(e["fecha_ingreso"])) },
                                )
                            },
                            "Ningun equipo coincide con el filtro",
                        )
                    }
                }
            }
        }
    }
}

// ===========================================================================
// Clientes
// ===========================================================================

@Composable
fun PantallaClientes(api: Api) {
    var busqueda by remember { mutableStateOf("") }
    var aplicada by remember { mutableStateOf("") }

    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Encabezado("Clientes",
            "Datos minimos para facturar y para responder por la garantia legal.")
        Row(horizontalArrangement = Arrangement.spacedBy(10.dp),
            verticalAlignment = Alignment.CenterVertically) {
            Campo(busqueda, { busqueda = it }, "Documento, nombre o telefono",
                Modifier.width(360.dp))
            Boton("Buscar", { aplicada = busqueda.trim() }, tono = "neutro")
        }
        Panel(Modifier.fillMaxSize()) {
            Cargador("cli:$aplicada", { api.clientes(aplicada.ifBlank { null }) }) { lista ->
                Column {
                    Titulo("${lista.size} clientes", 15)
                    Spacer(Modifier.height(10.dp))
                    Tabla(
                        listOf(Columna("Documento", 1.4f), Columna("Nombre", 2.2f),
                            Columna("Telefono", 1.2f), Columna("Correo", 2f),
                            Columna("Ciudad", 1.2f), Columna("Autoriza datos", 1.2f)),
                        lista.map { c ->
                            listOf<@Composable () -> Unit>(
                                {
                                    Dato("${c.texto("tipo_documento")} ${c.texto("numero_documento")}",
                                        FontWeight.SemiBold)
                                },
                                { Dato(nombreCliente(c)) },
                                { Dato(c.texto("telefono", "—")) },
                                { Dato(c.texto("email", "—")) },
                                { Dato(c.texto("ciudad", "—")) },
                                {
                                    Insignia(if (c.siNo("autoriza_datos")) "SI" else "NO",
                                        if (c.siNo("autoriza_datos")) "exito" else "alerta")
                                },
                            )
                        },
                        "Ningun cliente coincide con la busqueda",
                    )
                }
            }
        }
    }
}

// ===========================================================================
// Ventas
// ===========================================================================

@Composable
fun PantallaVentas(api: Api) {
    var refresco by remember { mutableStateOf(0) }

    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Encabezado("Ventas", "Historial de facturacion.") {
            Boton("Actualizar", { refresco++ }, tono = "neutro")
        }
        Cargador(refresco, { api.ventas(limite = 200) }) { lista ->
            val completadas = lista.filter { it.texto("estado") == "COMPLETADA" }
            val total = completadas.fold(0.0) { s, v -> s + v.decimal("total").toDouble() }
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Kpi("Facturas", entero(lista.size), "acento", null, Modifier.weight(1f))
                    Kpi("Recaudo", pesos(total), "exito", "sin anuladas", Modifier.weight(1f))
                    Kpi("Anuladas", entero(lista.size - completadas.size), "peligro",
                        null, Modifier.weight(1f))
                    Kpi("Ticket promedio",
                        pesos(if (completadas.isEmpty()) 0.0 else total / completadas.size),
                        "neutro", null, Modifier.weight(1f))
                }
                Panel(Modifier.fillMaxSize()) {
                    Tabla(
                        listOf(Columna("Factura", 1f), Columna("Fecha", 1.6f),
                            Columna("Cliente", 2f), Columna("Vendedor", 2f),
                            Columna("Total", 1.3f), Columna("Estado", 1.2f)),
                        lista.map { v ->
                            listOf<@Composable () -> Unit>(
                                { Dato(v.texto("numero"), FontWeight.SemiBold) },
                                { Dato(fechaHora(v["fecha"])) },
                                { Dato(nombreCliente(v.sub("cliente"))) },
                                { Dato(v.sub("usuario").texto("nombre_completo", "—")) },
                                { Dato(pesos(v["total"]), FontWeight.SemiBold) },
                                { Insignia(v.texto("estado")) },
                            )
                        },
                        "Todavia no hay ventas registradas",
                    )
                }
            }
        }
    }
}

// ===========================================================================
// Garantias
// ===========================================================================

@Composable
fun PantallaGarantias(api: Api) {
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Encabezado("Garantias",
            "Garantia legal registrada por unidad vendida (Ley 1480 de 2011).")
        Cargador(Unit, { api.garantias() }) { lista ->
            val vigentes = lista.count { it.texto("estado") == "VIGENTE" }
            val porVencer = lista.count {
                it.texto("estado") == "VIGENTE" && it.entero("dias_restantes") <= 30
            }
            Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    Kpi("Vigentes", entero(vigentes), "exito", null, Modifier.weight(1f))
                    Kpi("Por vencer", entero(porVencer), "alerta", "en 30 dias",
                        Modifier.weight(1f))
                    Kpi("En reclamacion",
                        entero(lista.count { it.texto("estado") == "EN_RECLAMACION" }),
                        "acento", null, Modifier.weight(1f))
                    Kpi("Vencidas",
                        entero(lista.count { it.texto("estado") == "VENCIDA" }),
                        "neutro", null, Modifier.weight(1f))
                }
                Panel(Modifier.fillMaxSize()) {
                    Tabla(
                        listOf(Columna("Garantia", 1f), Columna("Linea de venta", 1.3f),
                            Columna("Inicio", 1.2f), Columna("Vence", 1.2f),
                            Columna("Cobertura", 1.2f), Columna("Restan", 1.2f),
                            Columna("Estado", 1.4f)),
                        lista.map { g ->
                            val dias = g.entero("dias_restantes")
                            listOf<@Composable () -> Unit>(
                                { Dato("#${g.entero("id")}", FontWeight.SemiBold) },
                                { Dato(entero(g["venta_detalle_id"])) },
                                { Dato(fecha(g["fecha_inicio"])) },
                                { Dato(fecha(g["fecha_fin"])) },
                                { Dato("${g.entero("meses")} meses") },
                                {
                                    Dato("$dias dias", FontWeight.SemiBold,
                                        if (dias <= 30) Tema.alerta else Tema.exito)
                                },
                                { Insignia(g.texto("estado")) },
                            )
                        },
                        "No hay garantias registradas",
                    )
                }
            }
        }
    }
}

// ===========================================================================
// Usuarios
// ===========================================================================

@Composable
fun PantallaUsuarios(api: Api) {
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Encabezado("Usuarios",
            "Los permisos viven en la base de datos; el menu de cada quien se arma con los suyos.")
        Cargador(Unit, { api.usuarios() }) { lista ->
            Panel(Modifier.fillMaxSize()) {
                Column {
                    Titulo("${lista.size} usuarios", 15)
                    Spacer(Modifier.height(10.dp))
                    Tabla(
                        listOf(Columna("Usuario", 1.2f), Columna("Nombre", 2.2f),
                            Columna("Correo", 2f), Columna("Rol", 1.6f),
                            Columna("Estado", 1.1f), Columna("Ultimo acceso", 1.6f)),
                        lista.map { u ->
                            listOf<@Composable () -> Unit>(
                                { Dato(u.texto("username"), FontWeight.SemiBold) },
                                { Dato(u.texto("nombre_completo")) },
                                { Dato(u.texto("email")) },
                                { Insignia(u.sub("rol").texto("nombre", "—"), "acento") },
                                {
                                    Insignia(if (u.siNo("activo")) "ACTIVA" else "CANCELADO",
                                        if (u.siNo("activo")) "exito" else "peligro")
                                },
                                { Dato(fechaHora(u["ultimo_acceso"])) },
                            )
                        },
                        "No hay usuarios",
                    )
                }
            }
        }
    }
}
