package ejemplos

import java.math.BigDecimal
import java.sql.Connection
import java.sql.DriverManager
import java.sql.ResultSet
import java.sql.SQLException

/**
 * Query y base de datos: PostgreSQL desde Kotlin con JDBC.
 *
 *     set POS_BD=jdbc:postgresql://localhost:5432/pos_movil?user=postgres^&password=TU_CLAVE
 *     gradlew consulta
 *
 * Si no se define POS_BD, el programa pide la contrasena por consola.
 *
 * Lo importante de este archivo son dos cosas:
 *
 *   - `use { }`: cierra la conexion, la sentencia y el cursor pase lo que pase,
 *     incluso si la consulta lanza una excepcion a la mitad. Es el equivalente
 *     del try-with-resources de Java, pero sin anidar bloques.
 *   - `PreparedStatement`: el dato viaja como parametro, nunca pegado al texto
 *     del SQL. Es la unica forma de que un nombre con comillas no se convierta
 *     en una inyeccion.
 */

private fun cadenaConexion(): String {
    System.getenv("POS_BD")?.let { return it }
    print("Contrasena de PostgreSQL (usuario postgres): ")
    val clave = readlnOrNull().orEmpty()
    return "jdbc:postgresql://localhost:5432/pos_movil?user=postgres&password=$clave"
}

private fun titulo(n: Int, texto: String) {
    println("\n" + "=".repeat(70))
    println("$n. $texto")
    println("=".repeat(70))
}

private fun pesosCo(valor: BigDecimal?): String {
    val n = valor ?: BigDecimal.ZERO
    return "$ " + n.toBigInteger().toString().reversed().chunked(3)
        .joinToString(".").reversed()
}

/** Recorre un ResultSet como si fuera una secuencia de Kotlin. */
private fun <T> ResultSet.mapear(fila: (ResultSet) -> T): List<T> {
    val salida = ArrayList<T>()
    while (next()) salida.add(fila(this))
    return salida
}

fun main() {
    val url = cadenaConexion()

    val conexion: Connection = try {
        DriverManager.getConnection(url)
    } catch (e: SQLException) {
        println("\nNo se pudo conectar: ${e.message}")
        println("Revisa que PostgreSQL este encendido y que la clave sea la correcta.")
        return
    }

    conexion.use { cn ->

        // -- 1 ---------------------------------------------------------------
        titulo(1, "Conexion")
        cn.createStatement().use { st ->
            st.executeQuery("SELECT version() AS v, current_database() AS bd").use { rs ->
                if (rs.next()) {
                    println("Base:  ${rs.getString("bd")}")
                    println("Motor: ${rs.getString("v").substringBefore(',')}")
                }
            }
        }

        // -- 2 ---------------------------------------------------------------
        titulo(2, "Cuantas filas hay en cada tabla principal")
        // El nombre de la tabla no puede ir como parametro: '?' solo sirve para
        // valores. Por eso sale de una lista fija del codigo y nunca de algo que
        // escriba el usuario.
        listOf("productos", "equipos_imei", "clientes", "ventas", "venta_detalles",
            "garantias", "usuarios").forEach { tabla ->
            cn.createStatement().use { st ->
                st.executeQuery("SELECT COUNT(*) FROM $tabla").use { rs ->
                    rs.next()
                    println("  ${tabla.padEnd(16)} ${rs.getInt(1).toString().padStart(5)}")
                }
            }
        }

        // -- 3 ---------------------------------------------------------------
        titulo(3, "Consulta parametrizada: buscar un producto")
        cn.prepareStatement(
            """SELECT sku, nombre, precio_venta
                 FROM productos
                WHERE nombre ILIKE ? AND activo
                ORDER BY nombre"""
        ).use { ps ->
            ps.setString(1, "%iphone%")
            ps.executeQuery().use { rs ->
                rs.mapear { Triple(it.getString(1), it.getString(2), it.getBigDecimal(3)) }
                    .forEach { (sku, nombre, precio) ->
                        println("  ${sku.padEnd(10)} ${nombre.padEnd(38)} ${pesosCo(precio)}")
                    }
            }
        }

        // -- 4 ---------------------------------------------------------------
        titulo(4, "JOIN y agregacion: lo mas vendido")
        cn.createStatement().use { st ->
            st.executeQuery(
                """SELECT p.nombre,
                          SUM(d.cantidad)    AS unidades,
                          SUM(d.total_linea) AS vendido
                     FROM venta_detalles d
                     JOIN productos p ON p.id = d.producto_id
                     JOIN ventas    v ON v.id = d.venta_id
                    WHERE v.estado = 'COMPLETADA'
                    GROUP BY p.nombre
                    ORDER BY unidades DESC, vendido DESC
                    LIMIT 5"""
            ).use { rs ->
                rs.mapear {
                    Triple(it.getString("nombre"), it.getInt("unidades"),
                        it.getBigDecimal("vendido"))
                }.forEach { (nombre, unidades, vendido) ->
                    println("  ${nombre.padEnd(40)} ${unidades.toString().padStart(3)} u.  " +
                            pesosCo(vendido))
                }
            }
        }

        // -- 5 ---------------------------------------------------------------
        titulo(5, "Leer una vista del sistema: alertas de stock")
        cn.createStatement().use { st ->
            st.executeQuery("SELECT * FROM v_alertas_stock ORDER BY disponibles").use { rs ->
                val filas = rs.mapear {
                    listOf(it.getString("sku"), it.getString("nombre"),
                        it.getInt("disponibles").toString(),
                        it.getInt("stock_minimo").toString())
                }
                if (filas.isEmpty()) println("  Ningun producto esta por debajo del minimo.")
                filas.forEach { (sku, nombre, hay, minimo) ->
                    println("  ${sku.padEnd(10)} ${nombre.padEnd(38)} hay $hay, minimo $minimo")
                }
            }
        }

        // -- 6 ---------------------------------------------------------------
        titulo(6, "Llamar una funcion de PostgreSQL: validacion de IMEI")
        cn.prepareStatement("SELECT fn_imei_valido(?)").use { ps ->
            listOf("356789012345045", "356789012345046", "123").forEach { imei ->
                ps.setString(1, imei)
                ps.executeQuery().use { rs ->
                    rs.next()
                    println("  ${imei.padEnd(18)} ${if (rs.getBoolean(1)) "valido" else "invalido"}")
                }
            }
        }
        println("\n  La misma funcion respalda un CHECK de la tabla equipos_imei:")
        println("  un IMEI con digito verificador incorrecto no entra ni por SQL directo.")

        // -- 7 ---------------------------------------------------------------
        titulo(7, "Transaccion: insertar y deshacer")
        // Por defecto JDBC confirma cada sentencia. Se apaga el autocommit para
        // poder decidir al final si se confirma o se descarta todo el bloque.
        cn.autoCommit = false
        try {
            val antes = contar(cn, "clientes")
            cn.prepareStatement(
                """INSERT INTO clientes (tipo_documento, numero_documento, nombres,
                                         apellidos, ciudad, autoriza_datos)
                   VALUES ('CC', ?, 'Prueba', 'Transaccion', 'Bogota', TRUE)"""
            ).use { ps ->
                ps.setString(1, "999999998")
                ps.executeUpdate()
            }
            println("  Dentro de la transaccion: $antes -> ${contar(cn, "clientes")}")
            cn.rollback()
            println("  Despues del ROLLBACK:     ${contar(cn, "clientes")} (el insert se deshizo)")
        } catch (e: SQLException) {
            cn.rollback()
            println("  La transaccion fallo y se deshizo: ${e.message}")
        } finally {
            cn.autoCommit = true
        }
    }

    println("\nConexion cerrada.\n")
}

private fun contar(cn: Connection, tabla: String): Int =
    cn.createStatement().use { st ->
        st.executeQuery("SELECT COUNT(*) FROM $tabla").use { rs ->
            rs.next()
            rs.getInt(1)
        }
    }
