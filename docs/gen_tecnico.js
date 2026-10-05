/**
 * Documento tecnico del proyecto final.
 *
 *     node gen_tecnico.js
 */

const fs = require("fs");
const {
  AlignmentType, Document, Packer, Paragraph, PageBreak, TableOfContents, TextRun,
} = require("docx");
const E = require("./estilo");

const AUTORES = "Elkin Santiago Marín Duarte y Juan David Zabala Plata";
const FECHA = "4 de octubre de 2026";

// --------------------------------------------------------------------- portada
const portada = [
  new Paragraph({ spacing: { before: 2600 }, children: [] }),
  E.p("Sistema POS para la gestión y venta de dispositivos móviles",
      { alineacion: AlignmentType.CENTER, negrita: true, tam: 32 }),
  E.p("Documento técnico del proyecto final",
      { alineacion: AlignmentType.CENTER, cursiva: true, despues: 720 }),
  E.p(AUTORES, { alineacion: AlignmentType.CENTER }),
  E.p("Corporación Unificada Nacional de Educación Superior — CUN",
      { alineacion: AlignmentType.CENTER }),
  E.p("Facultad de Ingeniería", { alineacion: AlignmentType.CENTER }),
  E.p("Tecnología en Sistemas de Información", { alineacion: AlignmentType.CENTER }),
  E.p("Bogotá D. C.", { alineacion: AlignmentType.CENTER }),
  E.p(FECHA, { alineacion: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ------------------------------------------------------------------- contenido
const tdc = [
  E.h1("Tabla de contenido", false),
  new TableOfContents("Contenido", { hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------------------------------------------------------------------- resumen
const resumen = [
  E.h1("Resumen", false),
  E.p("Este documento describe el diseño, la construcción y la verificación de un " +
      "sistema de punto de venta para un comercio de dispositivos móviles. El " +
      "problema no es facturar: es que un celular no se cuenta como se cuenta un " +
      "cargador. Cada equipo es una unidad irrepetible identificada por su IMEI, y " +
      "de esa unidad dependen la garantía legal, la trazabilidad frente al operador " +
      "y la posibilidad de responderle al comprador meses después de la venta. El " +
      "sistema resuelve esa diferencia con dos estrategias de inventario conviviendo " +
      "en el mismo modelo de datos.", { sangria: false }),
  E.p("El resultado es una base PostgreSQL de 37 tablas donde las reglas críticas " +
      "viven en el motor, una API REST de 70 operaciones con control de acceso por " +
      "permisos, y tres clientes distintos —web, escritorio en Python y escritorio " +
      "en Kotlin— construidos sobre la misma API y con el mismo lenguaje visual. " +
      "Todo quedó verificado con seis conjuntos de pruebas automáticas que se " +
      "ejecutan contra la base y la API reales.", { sangria: true }),
  E.mixto([["Palabras clave: ", { italics: true }],
           ["punto de venta, PostgreSQL, IMEI, trazabilidad, garantía legal, " +
            "control de acceso basado en roles, FastAPI, Compose Desktop."]],
          { antes: 240 }),
];

// ----------------------------------------------------------------- introduccion
const introduccion = [
  E.h1("Introducción"),
  E.p("Un local que vende celulares maneja dos negocios a la vez. Vende accesorios " +
      "—forros, cargadores, vidrios templados— que se cuentan por cantidad y se " +
      "reponen cuando bajan del mínimo; y vende equipos, que no se cuentan: se " +
      "identifican. Cada teléfono tiene un IMEI único, y ese número es lo que " +
      "conecta la venta con la garantía, con el cliente que la reclama y con el " +
      "registro ante el operador."),
  E.p("Los sistemas genéricos de punto de venta tratan todo como una cantidad en " +
      "una bodega. Funcionan hasta que un cliente vuelve con un equipo dañado y hay " +
      "que demostrar cuándo se vendió, a quién y si la garantía sigue vigente. Ahí " +
      "la hoja de cálculo no alcanza.", { sangria: true }),
  E.p("Este proyecto construye un sistema donde esa distinción está en el diseño " +
      "desde la primera tabla, y donde las reglas que protegen la integridad del " +
      "inventario no dependen de que la aplicación se porte bien.", { sangria: true }),

  E.h2("Planteamiento del problema"),
  E.p("En un comercio de dispositivos móviles sin sistema, cuatro cosas fallan de " +
      "forma predecible:"),
  E.vinieta("Un mismo equipo se vende dos veces, porque nadie marcó el IMEI como " +
            "vendido al salir."),
  E.vinieta("La garantía se registra en una libreta, o no se registra, y cuando el " +
            "cliente vuelve no hay cómo comprobar la fecha de venta."),
  E.vinieta("El inventario que dice el sistema no es el que hay en la vitrina, " +
            "porque los movimientos no quedan registrados."),
  E.vinieta("La caja no cuadra y no hay forma de saber en qué turno se perdió la " +
            "diferencia."),

  E.h2("Objetivos"),
  E.h3("Objetivo general"),
  E.p("Desarrollar un sistema de punto de venta que gestione el inventario " +
      "serializado por IMEI, la facturación, la caja y la posventa de un comercio " +
      "de dispositivos móviles, con trazabilidad completa de cada equipo desde que " +
      "entra hasta que termina su garantía."),
  E.h3("Objetivos específicos"),
  ...E.pasos([
    "Diseñar un modelo relacional que soporte las dos estrategias de inventario " +
    "—por unidad serializada y por cantidad— sin duplicar la lógica de existencias.",
    "Trasladar al motor de base de datos las reglas que no pueden depender de la " +
    "aplicación: no vender un IMEI dos veces, no dejar existencias negativas, no " +
    "perder un movimiento del kardex.",
    "Construir una API con control de acceso por permisos almacenados en la base, " +
    "de modo que cambiar lo que puede hacer un rol no implique recompilar.",
    "Implementar tres clientes sobre la misma API —web, escritorio en Python y " +
    "escritorio en Kotlin— con una sola identidad visual.",
    "Verificar el sistema con pruebas automáticas que corran contra la base y la " +
    "API reales, no contra simulaciones.",
  ]),

  E.h2("Alcance"),
  E.p("El sistema cubre once módulos: seguridad, catálogo, compras, inventario, " +
      "clientes, caja, ventas, posventa, facturación electrónica, telefonía e " +
      "internet de las cosas. Queda fuera del alcance la integración real con un " +
      "proveedor tecnológico autorizado por la DIAN: el sistema genera el " +
      "consecutivo, el CUFE y el XML, pero no los transmite."),
];

// ------------------------------------------------------------------ marco
const marco = [
  E.h1("Marco de referencia"),
  E.h2("Marco normativo colombiano"),
  E.p("Cuatro normas condicionan el diseño del sistema, y cada una deja una huella " +
      "concreta en el modelo de datos."),
  ...E.rotulo(1, "Normas consideradas y su efecto en el sistema"),
  E.tabla(
    ["Norma", "Qué exige", "Cómo lo cubre el sistema"],
    [
      ["Ley 1480 de 2011 (Estatuto del Consumidor)",
       "Garantía legal registrada y consultable por el comprador",
       "Tabla garantias, creada por un trigger en cada venta, con fecha de inicio, " +
       "fecha de fin y estado"],
      ["Ley 1581 de 2012 (protección de datos)",
       "Recolectar solo los datos necesarios para la finalidad y obtener " +
       "autorización",
       "La tabla clientes guarda lo mínimo para facturar y responder por la " +
       "garantía, con la casilla autoriza_datos explícita"],
      ["Resolución CRC sobre registro de IMEI",
       "Trazabilidad de cada equipo comercializado",
       "Tabla equipos_imei con validación Luhn y la vista v_trazabilidad_imei"],
      ["Facturación electrónica (DIAN)",
       "Numeración autorizada por resolución y consecutivo sin saltos",
       "Tablas resoluciones_dian y facturas_electronicas; la función " +
       "fn_siguiente_numero entrega el consecutivo bajo bloqueo"],
    ], [1.3, 1.5, 2.2]),
  E.nota("El sistema genera el CUFE y el XML de la factura, pero no los transmite a " +
         "un proveedor tecnológico autorizado."),

  E.h2("El algoritmo de Luhn y el IMEI"),
  E.p("El IMEI tiene quince dígitos, y el último es un verificador calculado con el " +
      "algoritmo de Luhn: se recorre el número de derecha a izquierda duplicando una " +
      "de cada dos cifras, restando nueve cuando el resultado pasa de nueve, y la " +
      "suma total debe ser múltiplo de diez. Un dígito mal tecleado hace que la suma " +
      "no cierre."),
  E.p("El sistema valida el IMEI en tres capas: en la interfaz, para avisar de " +
      "inmediato; en la API, con un validador de Pydantic; y en PostgreSQL, con la " +
      "función fn_imei_valido respaldando una restricción CHECK. Las tres hacen lo " +
      "mismo a propósito: la de arriba se puede saltar, la de abajo no.",
      { sangria: true }),
  E.codigo("ALTER TABLE equipos_imei"),
  E.codigo("  ADD CONSTRAINT ck_imei_luhn CHECK (fn_imei_valido(imei));"),

  E.h2("Decisiones tecnológicas"),
  ...E.rotulo(2, "Tecnologías empleadas y razón de la elección"),
  E.tabla(
    ["Capa", "Tecnología", "Por qué"],
    [
      ["Base de datos", "PostgreSQL 16+",
       "Tipos ENUM, restricciones CHECK con funciones propias, triggers y vistas " +
       "materializables; permite poner las reglas donde no se pueden evadir"],
      ["Backend", "FastAPI, SQLAlchemy 2, psycopg 3",
       "Validación declarativa con Pydantic, documentación OpenAPI generada sola y " +
       "un ORM que no esconde el SQL"],
      ["Cliente web", "React 18 con Vite",
       "Interfaz accesible desde cualquier equipo de la red sin instalar nada"],
      ["Cliente de escritorio", "Flet 1.0 (Python)",
       "Mismo lenguaje del backend y empaquetado a un .exe autónomo"],
      ["Cliente de escritorio", "Kotlin 2.0 con Compose Desktop",
       "Interfaz declarativa, tipado fuerte y un instalador nativo"],
    ], [1, 1.3, 2.7]),
];

// ------------------------------------------------------------- arquitectura
const arquitectura = [
  E.h1("Arquitectura"),
  E.h2("Vista general"),
  E.p("El sistema son tres clientes distintos hablando con un solo servidor, que a " +
      "su vez habla con una sola base de datos. Ningún cliente se conecta a " +
      "PostgreSQL directamente."),
  E.codigo("  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐"),
  E.codigo("  │  Web React   │  │ Escritorio   │  │ Escritorio   │"),
  E.codigo("  │   (Vite)     │  │   Flet       │  │   Kotlin     │"),
  E.codigo("  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘"),
  E.codigo("         │   HTTP/JSON     │   JWT           │"),
  E.codigo("         └─────────────────┼─────────────────┘"),
  E.codigo("                  ┌────────▼────────┐"),
  E.codigo("                  │  API  FastAPI   │  70 operaciones"),
  E.codigo("                  │  Pydantic · ORM │  28 permisos"),
  E.codigo("                  └────────┬────────┘"),
  E.codigo("                  ┌────────▼────────┐"),
  E.codigo("                  │   PostgreSQL    │  37 tablas, 8 vistas"),
  E.codigo("                  │  reglas y datos │  9 triggers, 6 rutinas"),
  E.codigo("                  └─────────────────┘"),
  E.p("Que los tres clientes compartan la API no es una comodidad: es lo que " +
      "garantiza que la regla de que un IMEI no se vende dos veces se cumpla igual " +
      "en los tres. Si cada cliente tuviera su propia lógica, habría tres versiones " +
      "de la verdad.", { antes: 240 }),

  E.h2("Decisión central: la base es dueña del inventario"),
  E.p("La decisión de diseño más importante del proyecto es dónde ocurren los " +
      "efectos de una venta. Cuando se registra una línea de factura hay que marcar " +
      "el IMEI como vendido, descontar el stock del accesorio, escribir el " +
      "movimiento en el kardex y crear la garantía. Eso puede hacerlo el backend en " +
      "Python, o puede hacerlo PostgreSQL con triggers."),
  E.p("Se eligió lo segundo. El backend valida, calcula el dinero e inserta; los " +
      "triggers hacen el resto dentro de la misma transacción. La razón es simple: " +
      "si alguien entra por psql, por pgAdmin o por un script, las reglas se siguen " +
      "cumpliendo. Una regla que vive en la aplicación solo protege contra la " +
      "aplicación.", { sangria: true }),
  ...E.rotulo(3, "Reparto de responsabilidades en una venta"),
  E.tabla(
    ["Hace", "Quién", "Dónde"],
    [
      ["Exigir turno de caja abierto", "Backend", "servicios/caja.py"],
      ["Verificar que el IMEI exista y esté disponible", "Backend y trigger",
       "servicios/ventas.py y tr_venta_equipo"],
      ["Calcular base gravable, IVA y total", "Backend", "app/dinero.py (Decimal)"],
      ["Entregar el consecutivo de factura", "PostgreSQL", "fn_siguiente_numero"],
      ["Marcar el IMEI como VENDIDO", "PostgreSQL", "tr_venta_equipo"],
      ["Descontar stock y escribir el kardex", "PostgreSQL", "tr_venta_inventario"],
      ["Crear la garantía de la línea", "PostgreSQL", "tr_venta_equipo"],
      ["Registrar quién hizo el cambio", "PostgreSQL", "trg_auditar"],
      ["Revertir todo al anular", "PostgreSQL", "fn_anular_venta"],
    ], [2.2, 1, 1.8]),

  E.h2("Estructura del backend"),
  E.p("El backend separa cuatro responsabilidades, y la separación se nota en que " +
      "la capa de dominio no importa nada de FastAPI salvo las excepciones HTTP."),
  ...E.rotulo(4, "Capas del backend"),
  E.tabla(
    ["Capa", "Responsabilidad", "Archivos"],
    [
      ["Rutas", "Recibir la petición, exigir el permiso, devolver el esquema de salida",
       "app/routers/ (13 módulos)"],
      ["Validación", "Rechazar el dato malformado antes de que llegue al dominio",
       "app/schemas.py (89 esquemas)"],
      ["Dominio", "Reglas de negocio independientes del transporte",
       "app/servicios/ (5 módulos)"],
      ["Persistencia", "Modelo relacional y sesión",
       "app/models.py (37 clases), app/database.py"],
    ], [1, 2.4, 1.6]),
  E.p("Tanto app/models.py como los scripts SQL se generan desde una sola " +
      "definición del modelo, la misma que produce el diagrama UML. Así el " +
      "diagrama, el esquema y el ORM no pueden contradecirse: no hay tres copias " +
      "que mantener sincronizadas, hay una fuente y tres salidas.", { antes: 240 }),
];

// --------------------------------------------------------------- datos
const datos = [
  E.h1("Modelo de datos"),
  E.p("La base tiene 37 tablas repartidas en once módulos, 59 claves foráneas, " +
      "41 restricciones CHECK, 22 tipos enumerados y 141 índices."),
  ...E.rotulo(5, "Módulos del modelo de datos"),
  E.tabla(
    ["Módulo", "Tablas principales", "Qué resuelve"],
    [
      ["Seguridad", "usuarios, roles, permisos, rol_permisos, auditoria",
       "Quién entra y qué puede hacer; registro de cambios"],
      ["Catálogo", "productos, categorias, marcas, promociones",
       "Qué se vende y a qué precio"],
      ["Compras", "proveedores, ordenes_compra, orden_compra_detalles",
       "Cómo entra la mercancía"],
      ["Inventario", "equipos_imei, movimientos_inventario, alertas_stock",
       "Existencias por unidad y por cantidad, con kardex"],
      ["Clientes", "clientes", "A quién se le vende"],
      ["Caja", "cajas, turnos_caja, movimientos_caja",
       "Quién tiene la caja abierta y cuánto debería haber"],
      ["Ventas", "ventas, venta_detalles, pagos",
       "La factura y su cobro"],
      ["Posventa", "garantias, devoluciones, ordenes_servicio, apartados",
       "Lo que pasa después de la venta"],
      ["DIAN", "resoluciones_dian, facturas_electronicas, notas_credito",
       "Numeración autorizada y documento electrónico"],
      ["Telefonía", "operadores, planes, activaciones",
       "Venta de líneas y recargas"],
      ["IoT", "dispositivos_iot, eventos_iot, alertas_iot",
       "Sensores de la tienda y sus alertas"],
    ], [1, 2.2, 1.8]),

  E.h2("Las dos estrategias de inventario"),
  ...E.rotulo(6, "Cómo se cuentan los dos tipos de producto"),
  E.tabla(
    ["", "Equipos (smartphones)", "Accesorios"],
    [
      ["Se identifican por", "IMEI único por unidad", "SKU del modelo"],
      ["Dónde vive la existencia", "Una fila en equipos_imei por unidad",
       "La columna productos.stock_actual"],
      ["Al vender", "La fila pasa a estado VENDIDO", "Se resta la cantidad"],
      ["Garantía", "Ligada al IMEI concreto", "Ligada a la línea de factura"],
      ["Restricción", "requiere_imei = TRUE obliga a stock_actual = 0", "—"],
    ], [1.2, 1.9, 1.9]),
  E.p("La vista v_inventario_disponible y el campo calculado disponibles presentan " +
      "los dos mundos con la misma forma hacia afuera. La interfaz muestra " +
      "existencias sin tener que saber de qué tipo es el producto.", { antes: 240 }),

  E.h2("Estados de un equipo"),
  E.codigo("DISPONIBLE ──venta──▶ VENDIDO ──reclamo──▶ EN_SERVICIO ──▶ VENDIDO"),
  E.codigo("     ▲                    │"),
  E.codigo("     ├──apartado──▶ APARTADO"),
  E.codigo("     └──anulación─────────┘          DEVUELTO · DADO_DE_BAJA"),

  E.h2("Objetos programados en la base"),
  ...E.rotulo(7, "Vistas, funciones, procedimientos y disparadores"),
  E.tabla(
    ["Tipo", "Nombre", "Propósito"],
    [
      ["Vista", "v_inventario_disponible", "Existencias unificadas con margen"],
      ["Vista", "v_alertas_stock", "Productos en o bajo el mínimo"],
      ["Vista", "v_ventas_diarias", "Consolidado diario con ticket promedio"],
      ["Vista", "v_rentabilidad_producto", "Utilidad bruta por producto"],
      ["Vista", "v_trazabilidad_imei", "Historia completa de un equipo"],
      ["Vista", "v_estado_caja", "Situación de cada caja y su turno"],
      ["Vista", "v_garantias_vigentes", "Garantías activas con días restantes"],
      ["Vista", "v_apartados_pendientes", "Apartados con saldo y vencimiento"],
      ["Función", "fn_imei_valido", "Validación Luhn, usada como CHECK"],
      ["Función", "fn_siguiente_numero", "Consecutivo DIAN bajo bloqueo FOR UPDATE"],
      ["Función", "fn_anular_venta", "Reversa completa en una transacción"],
      ["Procedimiento", "sp_actualizar_garantias_vencidas", "Marca las vencidas"],
      ["Procedimiento", "sp_vencer_apartados", "Libera los apartados vencidos"],
      ["Procedimiento", "sp_cerrar_turno", "Cierra el turno y calcula la diferencia"],
      ["Trigger", "tr_venta_equipo", "Marca el IMEI y crea la garantía"],
      ["Trigger", "tr_venta_inventario", "Descuenta stock y escribe el kardex"],
      ["Trigger", "tr_apartado_reserva", "Reserva el equipo apartado"],
      ["Trigger", "tr_abono_apartado", "Recalcula el saldo del apartado"],
      ["Trigger", "tr_alerta_stock", "Genera la alerta al bajar del mínimo"],
      ["Trigger", "tr_auditoria_* (4)", "Registra quién cambió qué y cuándo"],
    ], [1, 2, 2.4]),

  E.h2("Una restricción que vale por mil validaciones"),
  E.p("Dos turnos abiertos en la misma caja al mismo tiempo romperían el arqueo. " +
      "En lugar de confiar en que la aplicación lo verifique antes de insertar —lo " +
      "que deja una ventana entre la consulta y la inserción— la regla es un índice " +
      "único parcial:"),
  E.codigo("CREATE UNIQUE INDEX ux_turno_abierto_por_caja"),
  E.codigo("  ON turnos_caja (caja_id) WHERE estado = 'ABIERTO';"),
  E.p("PostgreSQL rechaza el segundo turno aunque dos cajeros presionen el botón en " +
      "el mismo milisegundo.", { sangria: true, antes: 120 }),
];

// ------------------------------------------------------------------ seguridad
const seguridad = [
  E.h1("Seguridad y control de acceso"),
  E.h2("Permisos en la base, no en el código"),
  E.p("El control de acceso no se decide con una lista de roles escrita en el " +
      "código, sino con tres tablas: roles, permisos y rol_permisos. Hay 28 " +
      "permisos con códigos como ventas.crear o inventario.ajustar, y una " +
      "dependencia de FastAPI los exige:"),
  E.codigo("@router.post(\"\", dependencies=[Depends(requiere(\"ventas.crear\"))])"),
  E.p("Cambiar lo que puede hacer el cajero es cambiar filas de una tabla. No hay " +
      "que recompilar ni desplegar.", { sangria: true, antes: 120 }),
  ...E.rotulo(8, "Permisos por rol"),
  E.tabla(
    ["Rol", "Permisos", "Módulos que ve"],
    [
      ["Administrador", "28", "Todos"],
      ["Cajero", "11", "Punto de venta, ventas, caja, clientes, garantías"],
      ["Bodega", "8", "Tablero, inventario, compras, clientes"],
      ["Técnico", "8", "Clientes, garantías, servicio técnico, inventario"],
    ], [1, 0.7, 3]),
  E.nota("Los tres clientes arman su menú recorriendo esta misma tabla: un rol sin " +
         "el permiso no ve la opción, y si intenta la ruta directamente la API " +
         "responde 403."),

  E.h2("Contraseñas y sesiones"),
  E.vinieta("Contraseñas con PBKDF2-HMAC-SHA256, 260.000 iteraciones y sal " +
            "aleatoria de 16 bytes por usuario. La base nunca guarda el texto plano."),
  E.vinieta("Sesiones con JWT firmado en HS256, vigencia de ocho horas, verificado " +
            "en cada petición."),
  E.vinieta("La clave de PostgreSQL y la clave de firma del token viven en un " +
            "archivo .env que está en .gitignore; no viajan en el repositorio."),

  E.h2("Auditoría"),
  E.p("Antes de cada operación que modifica datos, el backend deja el identificador " +
      "del usuario en la sesión de PostgreSQL:"),
  E.codigo("SELECT set_config('pos.usuario_id', '3', true);"),
  E.p("Un trigger genérico lo lee y escribe en la tabla auditoria la fila anterior " +
      "y la nueva en formato JSON. El registro no depende de que el programador se " +
      "acuerde de llamarlo en cada endpoint.", { sangria: true, antes: 120 }),
];

// -------------------------------------------------------------------- clientes
const clientes = [
  E.h1("Los tres clientes"),
  E.p("Las tres aplicaciones consumen la misma API y comparten los mismos colores, " +
      "los mismos estados y las mismas reglas de presentación. Lo que cambia es la " +
      "tecnología, no el producto."),
  ...E.rotulo(9, "Comparación de los tres clientes"),
  E.tabla(
    ["", "Web (React)", "Escritorio (Flet)", "Escritorio (Kotlin)"],
    [
      ["Lenguaje", "JavaScript", "Python 3.11+", "Kotlin 2.0"],
      ["Interfaz", "React 18 + Vite", "Flet 1.0 (Flutter)", "Compose Desktop 1.7"],
      ["Líneas de código", "2.816", "3.884", "2.657"],
      ["Se distribuye como", "URL en la red local", "POS-Movil.exe (PyInstaller)",
       "Instalador .msi (jpackage)"],
      ["Necesita instalar", "Nada, solo el navegador", "Nada en el equipo destino",
       "Nada en el equipo destino"],
      ["Ventaja", "Llega a cualquier dispositivo", "Un solo lenguaje con el backend",
       "Tipado fuerte y arranque rápido"],
    ], [1.1, 1.3, 1.3, 1.3]),

  E.h2("Identidad visual compartida"),
  E.p("Los tokens de color se definen una vez y se repiten literalmente en los tres " +
      "clientes: fondo #F1F5F9, panel blanco, acento #1D4ED8, texto #0F172A, éxito " +
      "#047857, alerta #B45309 y peligro #B91C1C. La tabla que traduce un estado de " +
      "negocio a un tono —ANULADA es rojo, VIGENTE es verde— también está repetida " +
      "en los tres."),

  E.h2("Una decisión que se repite: el dinero"),
  E.p("Los tres clientes calculan el total de la factura con aritmética decimal y " +
      "redondeo medio hacia arriba a dos decimales, exactamente como el backend. No " +
      "es duplicación por descuido: el servidor exige que los pagos sumen el total " +
      "al centavo, así que el cliente tiene que llegar a la misma cifra para poder " +
      "cobrar. La cifra que manda es siempre la del servidor; la del cliente sirve " +
      "para mostrar y para cuadrar el cobro."),
  E.p("Ningún cliente usa coma flotante para dinero. Un total de $ 2.999.900 " +
      "calculado con float puede quedar en 2999899,9999999997, y esa diferencia " +
      "hace que el servidor rechace la venta.", { sangria: true }),
];

// --------------------------------------------------------------------- pruebas
const pruebas = [
  E.h1("Verificación"),
  E.p("El sistema se verificó con seis conjuntos de pruebas automáticas. Ninguno " +
      "usa simulaciones: todos corren contra PostgreSQL y contra la API reales."),
  ...E.rotulo(10, "Conjuntos de pruebas y qué comprueba cada uno"),
  E.tabla(
    ["Prueba", "Qué comprueba", "Resultado"],
    [
      ["database/04_pruebas.sql",
       "9 bloques de aserciones en PL/pgSQL, incluidas 6 reglas que deben fallar " +
       "(IMEI inválido, doble venta, stock negativo, turno duplicado)", "Pasa"],
      ["backend/tests/consistencia.py",
       "Compara el ORM contra el esquema real: 37 tablas, 281 columnas, tipos, " +
       "nulabilidad y claves foráneas", "Pasa"],
      ["backend/tests/esquemas.py",
       "Verifica que los 25 esquemas de salida solo pidan campos que el modelo " +
       "puede entregar", "Pasa"],
      ["backend/tests/test_api.py",
       "60+ verificaciones de extremo a extremo en 15 bloques: permisos por rol, " +
       "caja, venta con IMEI y pago mixto, anulación, apartados, garantías, " +
       "servicio, devolución, compras, telefonía, IoT y reportes", "Pasa"],
      ["escritorio/pruebas.py",
       "112 comprobaciones: los cuatro roles, las ocho vistas con sus pestañas y " +
       "diálogos, el carrito completo y una venta registrada de punta a punta",
       "112/112"],
      ["kotlin/prueba_json.py",
       "69 comprobaciones del analizador de JSON contra las 24 respuestas reales de " +
       "la API, casos límite y JSON malformado", "69/69"],
    ], [1.4, 3, 0.7]),

  E.h2("Las pruebas que deben fallar"),
  E.p("Un sistema que solo prueba lo que debe funcionar no prueba nada. Seis de las " +
      "aserciones de la base verifican que una operación prohibida sea rechazada:"),
  E.vinieta("Insertar un IMEI con dígito verificador incorrecto."),
  E.vinieta("Vender dos veces el mismo IMEI."),
  E.vinieta("Dejar el stock de un accesorio en negativo."),
  E.vinieta("Abrir un segundo turno en una caja que ya tiene uno abierto."),
  E.vinieta("Aplicar un descuento mayor que el valor de la línea."),
  E.vinieta("Registrar pagos que no suman el total de la factura."),

  E.h2("Verificación de la interfaz"),
  E.p("La interfaz web se recorrió con un navegador real controlado por Playwright: " +
      "las doce rutas, con dos roles distintos, más una venta completa hecha a " +
      "clics. La aplicación de escritorio en Flet se verificó construyendo el árbol " +
      "de controles de cada vista con los datos reales y contando los nodos, de modo " +
      "que una vista que devolviera un contenedor vacío no pasara por buena."),
  E.p("La aplicación en Kotlin no se pudo compilar en el entorno de desarrollo " +
      "porque el acceso a Maven Central estaba bloqueado. En su lugar se dejó una " +
      "revisión estática del código —equilibrio de símbolos, tipos usados sin " +
      "importar, clases de entrada declaradas— y se verificó la pieza de lógica con " +
      "más riesgo, el analizador de JSON, transcribiéndola y probándola contra las " +
      "respuestas reales de la API. Esa limitación queda declarada aquí porque " +
      "omitirla sería presentar como verificado algo que no lo está.", { sangria: true }),
];

// ----------------------------------------------------------------- resultados
const resultados = [
  E.h1("Resultados"),
  ...E.rotulo(11, "Resumen cuantitativo del sistema"),
  E.tabla(
    ["Componente", "Medida"],
    [
      ["Tablas en PostgreSQL", "37"],
      ["Claves foráneas", "59"],
      ["Restricciones CHECK", "41"],
      ["Tipos enumerados", "22"],
      ["Vistas", "8"],
      ["Funciones y procedimientos", "6"],
      ["Disparadores", "9"],
      ["Operaciones de la API", "70 en 13 grupos"],
      ["Permisos definidos", "28"],
      ["Esquemas de validación", "89"],
      ["Líneas de Python (backend)", "3.369"],
      ["Líneas de Python (escritorio Flet)", "3.884"],
      ["Líneas de JavaScript y CSS (web)", "2.816"],
      ["Líneas de Kotlin", "2.657"],
      ["Líneas de SQL", "1.501"],
      ["Comprobaciones automáticas", "más de 250"],
    ], [2.5, 1]),

  E.h2("Lo que el sistema resuelve"),
  E.p("Volviendo a los cuatro problemas del planteamiento:"),
  E.vinieta("Un equipo no se puede vender dos veces: el trigger tr_venta_equipo " +
            "rechaza la segunda venta de un IMEI que ya está en estado VENDIDO."),
  E.vinieta("La garantía no se olvida: la crea un trigger en el momento de la " +
            "venta, con los meses que el producto tiene configurados."),
  E.vinieta("El inventario coincide: toda alteración de existencias deja su fila en " +
            "el kardex, con quién, cuándo y por qué."),
  E.vinieta("La caja cuadra o se sabe por cuánto no cuadró: el cierre compara el " +
            "efectivo esperado con el contado y guarda la diferencia en el turno."),
];

// --------------------------------------------------------------- conclusiones
const conclusiones = [
  E.h1("Conclusiones"),
  ...E.pasos([
    "Poner las reglas críticas en el motor de base de datos, y no en la " +
             "aplicación, hizo que el sistema fuera correcto por construcción. " +
             "Durante el desarrollo varias pruebas fallaron precisamente porque " +
             "PostgreSQL rechazó operaciones que el código Python habría dejado " +
             "pasar; cada una de esas fallas era un error real atrapado temprano.",
    "Generar el esquema SQL, el ORM y el diagrama UML desde una sola " +
             "definición eliminó una categoría entera de errores. Cuando el modelo " +
             "cambió —al agregar motivo_anulacion a ventas— las tres salidas " +
             "cambiaron juntas y la prueba de consistencia lo confirmó.",
    "Guardar los permisos en tablas en vez de escribirlos en el código " +
             "permitió que los tres clientes armaran su menú sin duplicar reglas. " +
             "El cajero no ve el módulo de usuarios en ninguno de los tres, y la " +
             "razón está en una sola fila de rol_permisos.",
    "Construir tres clientes sobre la misma API dejó claro cuánto del " +
             "sistema es negocio y cuánto es presentación. El negocio son 3.369 " +
             "líneas de backend y 1.501 de SQL; lo demás es forma.",
  ]),
  E.h2("Trabajo futuro"),
  E.vinieta("Integración real con un proveedor tecnológico autorizado por la DIAN " +
            "para transmitir las facturas electrónicas."),
  E.vinieta("Lectura de códigos de barras e IMEI con cámara o pistola láser."),
  E.vinieta("Aplicación móvil para consulta de inventario en sala."),
  E.vinieta("Sincronización entre varias sedes con resolución de conflictos."),
];

// ---------------------------------------------------------------- referencias
const referencias = [
  E.h1("Referencias"),
  ...[
    "Congreso de la República de Colombia. (2011). Ley 1480 de 2011. Por medio de " +
    "la cual se expide el Estatuto del Consumidor. Diario Oficial No. 48.220.",
    "Congreso de la República de Colombia. (2012). Ley 1581 de 2012. Por la cual se " +
    "dictan disposiciones generales para la protección de datos personales. Diario " +
    "Oficial No. 48.587.",
    "Dirección de Impuestos y Aduanas Nacionales. (2020). Resolución 000042 de 2020. " +
    "Por la cual se desarrollan los sistemas de facturación. DIAN.",
    "Fowler, M. (2018). Refactoring: Improving the design of existing code " +
    "(2nd ed.). Addison-Wesley.",
    "JetBrains. (2024). Compose Multiplatform documentation. " +
    "https://www.jetbrains.com/compose-multiplatform/",
    "Kleppmann, M. (2017). Designing data-intensive applications. O'Reilly Media.",
    "Luhn, H. P. (1960). Computer for verifying numbers (U.S. Patent No. 2,950,048). " +
    "U.S. Patent and Trademark Office.",
    "PostgreSQL Global Development Group. (2024). PostgreSQL 16 documentation. " +
    "https://www.postgresql.org/docs/16/",
    "Ramírez, S. (2024). FastAPI documentation. https://fastapi.tiangolo.com/",
  ].map((ref) => new Paragraph({
    spacing: { line: E.DOBLE },
    indent: { left: 720, hanging: 720 },   // sangría francesa, como pide APA
    children: [new TextRun({ text: ref, font: E.FUENTE, size: E.TAM })],
  })),
];

// --------------------------------------------------------------------- anexos
const anexos = [
  E.h1("Anexo A. Estructura de archivos del proyecto"),
  E.codigo("pos-movil/"),
  E.codigo("├── database/        4 scripts SQL: esquema, programación, datos, pruebas"),
  E.codigo("├── backend/         API FastAPI (13 routers, 5 servicios, 3 pruebas)"),
  E.codigo("├── frontend/        cliente web React + Vite (13 páginas)"),
  E.codigo("├── escritorio/      cliente de escritorio en Flet (8 vistas)"),
  E.codigo("├── kotlin/          cliente de escritorio en Kotlin Compose"),
  E.codigo("├── ejemplos/        ejemplos de la rúbrica (Tkinter, Flet, Pygame, BD)"),
  E.codigo("├── docs/            documentación y capturas"),
  E.codigo("└── *.bat            lanzadores para Windows"),

  E.h2("Anexo B. Lanzadores"),
  E.tabla(
    ["Archivo", "Qué hace"],
    [
      ["0-DIAGNOSTICO.bat", "Revisa Python, Node, PostgreSQL y los puertos"],
      ["1-INSTALAR.bat", "Crea el entorno virtual e instala las dependencias"],
      ["2-INICIAR.bat", "Enciende el servidor y abre el navegador"],
      ["3-PRUEBAS.bat", "Corre las tres pruebas del backend"],
      ["5-COMPILAR-INTERFAZ.bat", "Compila la interfaz web"],
      ["6-BASE-DE-DATOS.bat", "Crea el esquema y carga los datos de prueba"],
      ["7-APP-ESCRITORIO.bat", "Abre la aplicación de escritorio en Flet"],
      ["8-CREAR-EJECUTABLE.bat", "Genera POS-Movil.exe"],
      ["9-DETENER.bat", "Detiene el servidor"],
      ["A-APP-KOTLIN.bat", "Compila y abre la aplicación en Kotlin"],
    ], [1.2, 2.8]),

  E.h2("Anexo C. Usuarios de prueba"),
  E.tabla(
    ["Usuario", "Contraseña", "Rol", "Permisos"],
    [
      ["admin", "admin123", "Administrador", "28"],
      ["cajero", "cajero123", "Cajero", "11"],
      ["bodega", "bodega123", "Bodega", "8"],
      ["tecnico", "tecnico123", "Técnico", "8"],
    ], [1, 1, 1.2, 0.8]),
  E.nota("Estas credenciales son únicamente para la demostración. En una " +
         "instalación real deben cambiarse antes de entregar el sistema."),
];

// ----------------------------------------------------------------------------
const doc = new Document({
  creator: AUTORES,
  title: "Sistema POS para la gestión y venta de dispositivos móviles",
  description: "Documento técnico del proyecto final",
  numbering: E.NUMERACION,
  styles: {
    default: {
      document: { run: { font: E.FUENTE, size: E.TAM } },
    },
  },
  features: { updateFields: true },   // para que Word rellene la tabla de contenido
  sections: [{
    properties: { page: E.PAGINA },
    headers: { default: E.encabezado() },
    children: [
      ...portada, ...tdc, ...resumen, ...introduccion, ...marco, ...arquitectura,
      ...datos, ...seguridad, ...clientes, ...pruebas, ...resultados,
      ...conclusiones, ...referencias, ...anexos,
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("Documento-Tecnico-POS-Movil.docx", buffer);
  console.log("escrito: Documento-Tecnico-POS-Movil.docx");
});
