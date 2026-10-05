/**
 * Manual de usuario del POS Movil, con capturas reales de la interfaz.
 *
 *     node gen_manual.js
 */

const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, ImageRun, Packer, PageBreak, Paragraph,
  TextRun,
} = require("docx");
const E = require("./estilo");

const CAPTURAS = path.join(__dirname, "capturas");

/**
 * Inserta una captura con su rotulo de figura.
 * El ancho util entre margenes es de 6.5 pulgadas = 624 puntos.
 */
let figura = 0;
function imagen(archivo, titulo, anchoPt = 600) {
  const ruta = path.join(CAPTURAS, archivo);
  if (!fs.existsSync(ruta)) {
    return [E.p(`[falta la captura ${archivo}]`, { cursiva: true })];
  }
  figura += 1;
  // Las capturas se tomaron a 1440x900 con escala 2, o sea 2880x1800.
  const alto = Math.round((anchoPt * 1800) / 2880);
  return [
    ...E.rotulo(figura, titulo, "Figura"),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 60, after: 240 },
      border: {
        top: { style: BorderStyle.SINGLE, size: 4, color: E.BORDE },
        bottom: { style: BorderStyle.SINGLE, size: 4, color: E.BORDE },
        left: { style: BorderStyle.SINGLE, size: 4, color: E.BORDE },
        right: { style: BorderStyle.SINGLE, size: 4, color: E.BORDE },
      },
      children: [new ImageRun({
        type: "png",
        data: fs.readFileSync(ruta),
        transformation: { width: anchoPt, height: alto },
      })],
    }),
  ];
}

const portada = [
  new Paragraph({ spacing: { before: 2800 }, children: [] }),
  E.p("Manual de usuario", { alineacion: AlignmentType.CENTER, negrita: true,
                             tam: 36 }),
  E.p("Sistema POS para la gestión y venta de dispositivos móviles",
      { alineacion: AlignmentType.CENTER, cursiva: true, despues: 720 }),
  E.p("Elkin Santiago Marín Duarte y Juan David Zabala Plata",
      { alineacion: AlignmentType.CENTER }),
  E.p("Corporación Unificada Nacional de Educación Superior — CUN",
      { alineacion: AlignmentType.CENTER }),
  E.p("Versión 1.0 — 4 de octubre de 2026", { alineacion: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),
];

const intro = [
  E.h1("Qué es este sistema", false),
  E.p("El POS Móvil administra la venta de celulares y accesorios. Hace cuatro " +
      "cosas que una hoja de cálculo no hace:"),
  E.vinieta("Controla cada equipo por su IMEI, de modo que un teléfono no se puede " +
            "vender dos veces."),
  E.vinieta("Crea la garantía sola, en el momento de la venta, con los meses que " +
            "tenga configurados el producto."),
  E.vinieta("Lleva el kardex: cada vez que cambian las existencias queda registrado " +
            "quién lo hizo, cuándo y por qué."),
  E.vinieta("Controla la caja por turnos y calcula la diferencia al cerrar."),
  E.p("Hay tres formas de usarlo, y las tres hacen lo mismo porque hablan con el " +
      "mismo servidor: desde el navegador, desde la aplicación de escritorio en " +
      "Python y desde la aplicación de escritorio en Kotlin. Este manual usa las " +
      "pantallas del navegador; las otras dos se ven y se usan igual.",
      { antes: 180 }),

  E.h2("Antes de empezar"),
  E.p("El sistema necesita tres cosas instaladas en el equipo que hace de servidor:"),
  E.tabla(
    ["Programa", "Para qué", "Dónde se consigue"],
    [
      ["Python 3.11 o superior", "El servidor y la app de escritorio",
       "python.org (marcar «Add Python to PATH»)"],
      ["Node.js", "Compilar la interfaz web", "nodejs.org"],
      ["PostgreSQL 14 o superior", "La base de datos", "postgresql.org"],
    ], [1.2, 1.5, 1.8]),
];

const instalacion = [
  E.h1("Instalación"),
  E.p("Se hace una sola vez. Todos los pasos son archivos .bat: se abren con doble " +
      "clic desde la carpeta pos-movil."),
  E.h2("Paso 1. Instalar las dependencias"),
  E.p("Doble clic en 1-INSTALAR.bat. Crea el entorno de Python, instala lo que " +
      "necesitan el servidor y la aplicación de escritorio, y compila la interfaz " +
      "web. Tarda entre cinco y quince minutos la primera vez."),
  E.h2("Paso 2. Crear la base de datos"),
  E.p("Doble clic en 6-BASE-DE-DATOS.bat. Pide el usuario y la contraseña de " +
      "PostgreSQL, crea las 37 tablas, las vistas, las funciones y los " +
      "disparadores, y carga los datos de prueba. Al final corre las pruebas de la " +
      "base y avisa si algo falló."),
  E.mixto([["Atención: ", { bold: true }],
           ["este paso borra y vuelve a crear el esquema. Pide confirmación " +
            "escribiendo SI antes de hacerlo."]], { antes: 120 }),
  E.h2("Paso 3. Encender el sistema"),
  E.p("Doble clic en 2-INICIAR.bat. Enciende el servidor y abre el navegador en " +
      "http://127.0.0.1:8000. La ventana negra del servidor debe quedarse abierta: " +
      "si se cierra, el sistema se apaga."),
  E.p("Para apagarlo, 9-DETENER.bat.", { sangria: true }),

  E.h2("Si algo sale mal"),
  E.tabla(
    ["Lo que ves", "Qué pasa", "Qué hacer"],
    [
      ["«No se encontró Python»", "Python no está en el PATH",
       "Reinstalarlo marcando «Add Python to PATH»"],
      ["«Falta el entorno virtual»", "No se ejecutó la instalación",
       "Correr 1-INSTALAR.bat"],
      ["El navegador abre pero se ve la versión vieja", "Caché del navegador",
       "Ctrl + F5 para recargar sin caché"],
      ["«El puerto 8000 está ocupado»", "Quedó un servidor anterior corriendo",
       "Correr 9-DETENER.bat y volver a iniciar"],
      ["«No hay conexión con el servidor»", "El servidor está apagado",
       "Correr 2-INICIAR.bat y dejar la ventana abierta"],
    ], [1.4, 1.3, 1.8]),
];

const ingreso = [
  E.h1("Entrar al sistema"),
  ...imagen("01-ingreso.png", "Pantalla de ingreso"),
  E.p("Cada persona entra con su usuario. Lo que ve después depende de su rol: el " +
      "sistema arma el menú con los permisos que tenga, así que dos personas " +
      "distintas ven menús distintos."),
  ...E.rotulo(1, "Usuarios de prueba"),
  E.tabla(
    ["Usuario", "Contraseña", "Rol", "Qué puede hacer"],
    [
      ["admin", "admin123", "Administrador", "Todo, incluida la anulación de ventas"],
      ["cajero", "cajero123", "Cajero", "Vender, cobrar, abrir y cerrar caja"],
      ["bodega", "bodega123", "Bodega", "Inventario, compras y ajustes de stock"],
      ["tecnico", "tecnico123", "Técnico", "Garantías y servicio técnico"],
    ], [0.9, 1, 1.1, 2.3]),
  E.nota("Estas contraseñas son para la demostración. En una instalación real hay " +
         "que cambiarlas antes de entregar el sistema."),
];

const panel = [
  E.h1("El panel de control"),
  ...imagen("02-tablero.png", "Panel de control del administrador"),
  E.p("Es lo primero que aparece. Muestra cómo va el negocio hoy y qué necesita " +
      "atención:"),
  E.vinieta("Ventas de hoy y del mes, con el ticket promedio."),
  E.vinieta("Equipos disponibles: unidades con IMEI que todavía están en bodega."),
  E.vinieta("Bajo mínimo: productos que hay que reabastecer."),
  E.vinieta("Garantías vigentes y cuántas están en servicio técnico."),
  E.vinieta("El gráfico de los últimos catorce días: pasar el cursor sobre una " +
            "barra muestra el detalle de ese día."),
  E.vinieta("Las alertas de inventario, con los productos que ya tocaron el mínimo."),
  E.p("El aviso de arriba dice si hay un turno de caja abierto. Sin turno abierto " +
      "no se puede facturar.", { antes: 180 }),
];

const vender = [
  E.h1("Cómo registrar una venta"),
  E.p("Es la operación más frecuente, así que vale la pena hacerla despacio la " +
      "primera vez."),
  E.h2("Antes: abrir la caja"),
  ...imagen("04-caja.png", "Módulo de caja"),
  E.p("Sin turno de caja abierto el sistema no deja facturar, y no es un capricho " +
      "de la pantalla: el servidor lo rechaza. Para abrirlo:"),
  ...E.pasos([
    "Entrar a Caja.",
    "Elegir la caja y escribir la base inicial, que es el efectivo con el " +
             "que arranca el turno.",
    "Presionar «Abrir turno».",
  ]),
  E.p("Solo puede haber un turno abierto por caja. Si otra persona ya la abrió, hay " +
      "que cerrarla antes.", { sangria: true, antes: 120 }),

  E.h2("Armar la factura"),
  ...imagen("03-punto-venta.png", "Punto de venta"),
  ...E.pasos([
    "Entrar a Punto de venta.",
    "Buscar el producto por nombre, SKU o código de barras, y hacer clic " +
             "para agregarlo.",
    "Si el producto es un equipo, el sistema pide elegir el IMEI concreto: " +
             "muestra solo los que están disponibles. Si es un accesorio, se " +
             "ajusta la cantidad con los botones.",
    "Elegir el cliente, o dejar «Consumidor final».",
    "Revisar el total. El sistema calcula el IVA de cada línea con el " +
             "porcentaje que tenga configurado el producto, no con uno fijo.",
    "Elegir el método de pago y presionar «Facturar».",
  ]),
  E.p("Si hace falta cobrar con dos medios —parte en efectivo, parte con tarjeta— " +
      "se usa «Dividir el pago». La suma de los pagos tiene que dar exactamente el " +
      "total; el servidor rechaza la venta si no cuadra al centavo.",
      { sangria: true, antes: 120 }),

  E.h2("Qué pasa cuando se presiona «Facturar»"),
  E.p("En una sola operación, y de forma que o pasa todo o no pasa nada:"),
  E.vinieta("Se asigna el número de factura siguiendo la resolución de la DIAN, sin " +
            "saltos ni repeticiones."),
  E.vinieta("El equipo vendido queda marcado como VENDIDO y no se puede volver a " +
            "vender."),
  E.vinieta("Se descuenta el stock de los accesorios y se escribe el movimiento en " +
            "el kardex."),
  E.vinieta("Se crea la garantía de cada línea, con la fecha de vencimiento ya " +
            "calculada."),
  E.vinieta("Se genera la factura electrónica con su CUFE."),
  E.p("Si algo falla a la mitad —por ejemplo, que otro cajero vendió ese mismo " +
      "equipo un segundo antes— no queda media factura: se deshace todo y aparece " +
      "el mensaje de por qué.", { sangria: true, antes: 120 }),
];

const otros = [
  E.h1("Los demás módulos"),

  E.h2("Ventas"),
  ...imagen("05-ventas.png", "Historial de ventas"),
  E.p("El historial de facturas con su estado. Al abrir una se ve el detalle " +
      "completo: las líneas, los IMEI vendidos, los pagos y los datos de la factura " +
      "electrónica."),
  E.p("Anular una venta es un permiso del administrador. Anular no borra la " +
      "factura: la deja marcada como ANULADA con el motivo, devuelve los equipos a " +
      "DISPONIBLE, repone el stock, escribe los movimientos de reversa en el kardex " +
      "y anula las garantías. Una factura emitida es un documento, no una fila que " +
      "se pueda tachar.", { sangria: true }),

  E.h2("Inventario"),
  ...imagen("06-inventario.png", "Productos e inventario"),
  E.p("Dos pestañas, porque hay dos formas de contar:"),
  E.vinieta("Productos: el catálogo. Los accesorios muestran su cantidad; los " +
            "equipos muestran cuántas unidades con IMEI hay disponibles."),
  E.vinieta("Equipos por IMEI: una fila por teléfono, con su estado, su color, su " +
            "capacidad y su costo."),
  E.p("Desde aquí se ingresa mercancía, se ajustan existencias con su motivo y se " +
      "consulta el kardex de cualquier producto. La trazabilidad de un equipo " +
      "muestra toda su historia: cuándo entró, en qué factura salió, a qué cliente " +
      "y hasta cuándo tiene garantía.", { antes: 120 }),

  E.h2("Clientes"),
  ...imagen("07-clientes.png", "Clientes"),
  E.p("Solo se piden los datos necesarios para facturar y para responder por la " +
      "garantía. La casilla de autorización de tratamiento de datos es explícita, " +
      "como lo exige la Ley 1581 de 2012. Desde la ficha de cada cliente se puede " +
      "ver todo lo que ha comprado."),

  E.h2("Posventa: garantías, servicio técnico y apartados"),
  ...imagen("08-posventa.png", "Posventa"),
  E.p("Las garantías se crean solas con la venta. Esta pantalla muestra cuáles " +
      "están vigentes, cuáles están por vencer en los próximos treinta días y " +
      "cuáles ya vencieron. Cuando un cliente reclama, se abre la reclamación desde " +
      "aquí y el sistema crea la orden de servicio técnico enlazada a esa garantía " +
      "y a ese IMEI."),
  E.p("Los apartados reservan un equipo concreto: el sistema lo marca como APARTADO " +
      "y nadie lo puede vender mientras tanto. Los abonos van bajando el saldo " +
      "pendiente.", { sangria: true }),

  E.h2("Compras"),
  ...imagen("09-compras.png", "Órdenes de compra"),
  E.p("Las órdenes a proveedores y su recepción. Al recibir una orden, los equipos " +
      "entran al inventario con su IMEI y los accesorios suman al stock, todo con " +
      "su movimiento en el kardex."),

  E.h2("Líneas y recargas"),
  ...imagen("10-telefonia.png", "Activación de líneas"),
  E.p("Activación de líneas prepago y pospago con los operadores y planes " +
      "configurados."),

  E.h2("IoT y alertas"),
  ...imagen("11-iot.png", "Dispositivos y alertas"),
  E.p("Los sensores de la tienda y las alertas que generan. Es el módulo que conecta " +
      "el sistema con el curso de redes."),

  E.h2("Reportes"),
  ...imagen("12-reportes.png", "Reportes"),
  E.p("Ventas por día, productos más vendidos, rentabilidad por producto y " +
      "trazabilidad de cualquier IMEI."),

  E.h2("Usuarios y roles"),
  ...imagen("13-usuarios.png", "Usuarios y permisos"),
  E.p("Crear usuarios, asignarles rol y ver la matriz de permisos. Lo importante de " +
      "esta pantalla es que los permisos no están escritos en el programa: están en " +
      "la base de datos. Cambiar lo que puede hacer el cajero es cambiar filas de " +
      "una tabla, no recompilar el sistema."),
];

const escritorio = [
  E.h1("Las aplicaciones de escritorio"),
  E.p("Además del navegador, el sistema tiene dos aplicaciones de escritorio. Las " +
      "dos hacen lo mismo que la web y se ven igual, porque hablan con el mismo " +
      "servidor."),

  E.h2("Aplicación en Python (Flet)"),
  ...E.pasos([
    "Con el servidor encendido, doble clic en 7-APP-ESCRITORIO.bat.",
    "Para tener un ejecutable que funcione sin Python instalado, doble " +
             "clic en 8-CREAR-EJECUTABLE.bat. Genera escritorio\\dist\\POS-Movil.exe.",
  ]),
  E.p("Si el servidor está en otro equipo de la red, antes de abrir el ejecutable " +
      "hay que indicarle dónde está:", { antes: 120 }),
  E.codigo("set POS_SERVIDOR=http://192.168.1.50:8000/api"),
  E.codigo("POS-Movil.exe"),

  E.h2("Aplicación en Kotlin (Compose Desktop)"),
  E.p("Necesita un JDK 17 o superior. La forma más fácil es abrir la carpeta kotlin " +
      "con IntelliJ IDEA Community, que descarga Java y Gradle por su cuenta; o, " +
      "con Gradle instalado, doble clic en A-APP-KOTLIN.bat."),
  E.p("El paso a paso completo, con los errores típicos y qué significan, está en " +
      "kotlin\\COMO-COMPILAR.md.", { sangria: true }),
];

const reglas = [
  E.h1("Las reglas que el sistema no deja saltarse"),
  E.p("Conviene conocerlas, porque cuando aparece un mensaje de error casi siempre " +
      "es una de estas:"),
  ...E.rotulo(2, "Reglas de negocio aplicadas por el sistema"),
  E.tabla(
    ["Regla", "Qué pasa si se intenta"],
    [
      ["Un IMEI no se vende dos veces", "La venta se rechaza indicando el estado " +
       "del equipo"],
      ["Un equipo serializado exige IMEI", "No deja facturar la línea sin elegir " +
       "una unidad"],
      ["Un equipo se vende de a una unidad por línea", "Rechaza cantidades mayores " +
       "que uno"],
      ["No se vende más stock del que hay", "Indica cuántas unidades hay y cuántas " +
       "se piden"],
      ["El descuento no supera el valor de la línea", "Rechaza el descuento"],
      ["El IMEI debe tener quince dígitos válidos", "No deja ingresarlo al " +
       "inventario"],
      ["No se factura sin turno de caja abierto", "Pide abrir la caja primero"],
      ["Los pagos suman el total exacto", "Dice cuánto suman los pagos y cuánto es " +
       "el total"],
      ["Solo el administrador anula ventas", "Responde que no tiene permiso"],
      ["Una caja no tiene dos turnos abiertos", "Rechaza el segundo turno"],
      ["Toda alteración de existencias queda en el kardex", "No hay forma de " +
       "evitarlo: lo escribe la base"],
    ], [1.8, 2.2]),
];

const glosario = [
  E.h1("Glosario"),
  E.tabla(
    ["Término", "Qué significa"],
    [
      ["IMEI", "Número único de quince dígitos que identifica un teléfono. El " +
       "último dígito es un verificador."],
      ["SKU", "Código interno con el que se identifica un modelo de producto."],
      ["Kardex", "Registro de todos los movimientos de existencias de un producto."],
      ["Turno de caja", "Periodo entre que se abre y se cierra una caja, con un " +
       "responsable."],
      ["Arqueo", "Comparación entre el efectivo que debería haber y el que hay."],
      ["Apartado", "Reserva de un equipo concreto mientras el cliente termina de " +
       "pagarlo."],
      ["CUFE", "Código único que identifica una factura electrónica ante la DIAN."],
      ["Serializado", "Producto que se controla unidad por unidad, no por cantidad."],
      ["Rol", "Conjunto de permisos que define qué puede hacer una persona."],
    ], [1, 3]),
];

const doc = new Document({
  creator: "Elkin Santiago Marín Duarte y Juan David Zabala Plata",
  title: "Manual de usuario — POS Móvil",
  numbering: E.NUMERACION,
  styles: { default: { document: { run: { font: E.FUENTE, size: E.TAM } } } },
  sections: [{
    properties: { page: E.PAGINA },
    headers: { default: E.encabezado() },
    children: [
      ...portada, ...intro, ...instalacion, ...ingreso, ...panel, ...vender,
      ...otros, ...escritorio, ...reglas, ...glosario,
    ],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("Manual-de-Usuario-POS-Movil.docx", buffer);
  console.log("escrito: Manual-de-Usuario-POS-Movil.docx");
});
