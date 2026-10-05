package pos

import java.math.BigDecimal
import java.net.URI
import java.net.URLEncoder
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.charset.StandardCharsets
import java.time.Duration

/**
 * Fallo al hablar con el backend, ya traducido a una frase que se le puede
 * mostrar a quien esta en el mostrador.
 */
class ErrorApi(val mensaje: String, val codigo: Int = 0) : Exception(mensaje)

/**
 * Cliente del backend.
 *
 * La aplicacion de Kotlin consume la misma API que la web y que la de Flet.
 * Las reglas de negocio (un IMEI no se vende dos veces, no se factura sin turno
 * de caja, el IVA sale del producto) viven una sola vez, en el servidor; los
 * tres clientes se limitan a pedir y mostrar.
 *
 * Se usa `java.net.http.HttpClient`, que viene con el JDK desde la version 11:
 * una dependencia menos que empaquetar.
 */
class Api(private val base: String = System.getenv("POS_SERVIDOR")
    ?: "http://127.0.0.1:8000/api") {

    private val cliente: HttpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(10))
        .build()

    var token: String? = null
        private set
    var usuario: Map<String, Any?> = emptyMap()
        private set
    var permisos: Set<String> = emptySet()
        private set

    val nombre: String get() = usuario.texto("nombre_completo")
    val rol: String get() = usuario.sub("rol").texto("nombre")

    /** True si el rol tiene al menos uno de los permisos indicados. */
    fun puede(vararg codigos: String): Boolean = codigos.any { it in permisos }

    // ------------------------------------------------------------ transporte

    private fun pedir(metodo: String, ruta: String, cuerpo: String? = null,
                      formulario: Boolean = false): Any? {
        val peticion = HttpRequest.newBuilder()
            .uri(URI.create(base + ruta))
            .timeout(Duration.ofSeconds(30))
            .header("Accept", "application/json")
            .apply {
                token?.let { header("Authorization", "Bearer $it") }
                if (cuerpo != null) {
                    header("Content-Type",
                        if (formulario) "application/x-www-form-urlencoded"
                        else "application/json")
                }
            }
            .method(metodo,
                if (cuerpo == null) HttpRequest.BodyPublishers.noBody()
                else HttpRequest.BodyPublishers.ofString(cuerpo, StandardCharsets.UTF_8))
            .build()

        val respuesta: HttpResponse<String> = try {
            cliente.send(peticion, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8))
        } catch (e: java.net.ConnectException) {
            throw ErrorApi("No hay conexion con el servidor. Verifica que el backend " +
                    "este encendido en ${base.removeSuffix("/api")}.")
        } catch (e: java.io.IOException) {
            throw ErrorApi("Fallo la comunicacion con el servidor: ${e.message}")
        }

        val texto = respuesta.body()
        if (respuesta.statusCode() in 200..299) {
            return if (texto.isBlank()) null else Json.leer(texto)
        }
        throw ErrorApi(mensajeDeError(texto, respuesta.statusCode()), respuesta.statusCode())
    }

    /**
     * FastAPI devuelve `detail` como texto cuando es un HTTPException y como
     * lista de errores cuando Pydantic rechaza el cuerpo. Hay que cubrir los dos
     * casos o el usuario termina viendo un corchete.
     */
    private fun mensajeDeError(texto: String, codigo: Int): String {
        val generico = "Error $codigo del servidor."
        val detalle = runCatching { Json.leer(texto).objeto()["detail"] }.getOrNull()
        return when (detalle) {
            is String -> detalle
            is List<*> -> detalle.joinToString(" · ") { e ->
                val error = e.objeto()
                val campo = error["loc"].lista().drop(1).joinToString(".") { it.toString() }
                "${campo.ifBlank { "dato" }}: ${error.texto("msg", "invalido")}"
            }
            else -> generico
        }
    }

    private fun consulta(parametros: Map<String, Any?>): String {
        val utiles = parametros.filterValues { it != null && it.toString().isNotBlank() }
        if (utiles.isEmpty()) return ""
        return utiles.entries.joinToString("&", prefix = "?") { (clave, valor) ->
            "$clave=" + URLEncoder.encode(valor.toString(), StandardCharsets.UTF_8)
        }
    }

    private fun get(ruta: String, vararg parametros: Pair<String, Any?>): Any? =
        pedir("GET", ruta + consulta(parametros.toMap()))

    private fun post(ruta: String, cuerpo: Any? = null): Any? =
        pedir("POST", ruta, Json.escribir(cuerpo ?: emptyMap<String, Any?>()))

    // --------------------------------------------------------------- sesion

    fun salud(): Map<String, Any?> = pedir("GET", "/salud").objeto()

    fun entrar(usuario: String, clave: String): Map<String, Any?> {
        // El login es un OAuth2 estandar: viaja como formulario, no como JSON.
        val cuerpo = "username=" + URLEncoder.encode(usuario, StandardCharsets.UTF_8) +
                "&password=" + URLEncoder.encode(clave, StandardCharsets.UTF_8)
        val datos = pedir("POST", "/auth/login", cuerpo, formulario = true).objeto()
        token = datos.texto("access_token")
        this.usuario = datos.sub("usuario")
        permisos = datos["permisos"].lista().map { it.toString() }.toSet()
        return datos
    }

    fun salir() {
        token = null
        usuario = emptyMap()
        permisos = emptySet()
    }

    // -------------------------------------------------------------- consulta

    fun tablero(): Map<String, Any?> = get("/reportes/dashboard").objeto()

    fun ventasPorDia(dias: Int = 14): List<Map<String, Any?>> =
        get("/reportes/ventas-por-dia", "dias" to dias).objetos()

    fun masVendidos(limite: Int = 5, dias: Int = 30): List<Map<String, Any?>> =
        get("/reportes/mas-vendidos", "limite" to limite, "dias" to dias).objetos()

    fun alertasStock(): List<Map<String, Any?>> = get("/reportes/alertas-stock").objetos()

    fun productos(q: String? = null, limite: Int = 200): List<Map<String, Any?>> =
        get("/productos", "q" to q, "limite" to limite).objetos()

    fun equipos(productoId: Int? = null, estado: String? = null,
                q: String? = null, limite: Int = 200): List<Map<String, Any?>> =
        get("/inventario/imei", "producto_id" to productoId, "estado" to estado,
            "q" to q, "limite" to limite).objetos()

    fun clientes(q: String? = null, limite: Int = 200): List<Map<String, Any?>> =
        get("/clientes", "q" to q, "limite" to limite).objetos()

    fun ventas(limite: Int = 100, estado: String? = null): List<Map<String, Any?>> =
        get("/ventas", "limite" to limite, "estado" to estado).objetos()

    fun venta(id: Int): Map<String, Any?> = get("/ventas/$id").objeto()

    fun garantias(estado: String? = null): List<Map<String, Any?>> =
        get("/garantias", "estado" to estado).objetos()

    fun turno(): Map<String, Any?>? = get("/caja/turno")?.objeto()

    fun cajas(): List<Map<String, Any?>> = get("/caja/cajas").objetos()

    fun usuarios(): List<Map<String, Any?>> = get("/usuarios").objetos()

    // ----------------------------------------------------------- operaciones

    fun abrirTurno(cajaId: Int, baseInicial: BigDecimal): Map<String, Any?> =
        post("/caja/abrir", mapOf(
            "caja_id" to cajaId,
            "base_inicial" to baseInicial.toPlainString(),
        )).objeto()

    fun cerrarTurno(contado: BigDecimal): Map<String, Any?> =
        post("/caja/cerrar", mapOf("efectivo_contado" to contado.toPlainString())).objeto()

    fun registrarVenta(clienteId: Int?, lineas: List<Linea>,
                       metodo: String, observaciones: String?): Map<String, Any?> {
        val total = lineas.fold(BigDecimal.ZERO) { suma, l -> suma + l.total }
        return post("/ventas", mapOf(
            "cliente_id" to clienteId,
            "observaciones" to observaciones?.ifBlank { null },
            "items" to lineas.map { it.aMapa() },
            // El backend exige que los pagos sumen el total al centavo.
            "pagos" to listOf(mapOf("metodo" to metodo, "valor" to total.toPlainString())),
        )).objeto()
    }

    fun anularVenta(id: Int, motivo: String): Map<String, Any?> =
        post("/ventas/$id/anular", mapOf("motivo" to motivo)).objeto()

    fun crearCliente(datos: Map<String, Any?>): Map<String, Any?> =
        post("/clientes", datos).objeto()
}
