/**
 * Guion de sustentacion: que decir, en que orden y que mostrar mientras se dice.
 *
 *     node gen_guion.js
 */

const fs = require("fs");
const { AlignmentType, Document, Packer, PageBreak, Paragraph } = require("docx");
const E = require("./estilo");

const portada = [
  new Paragraph({ spacing: { before: 2800 }, children: [] }),
  E.p("Guion de sustentación", { alineacion: AlignmentType.CENTER, negrita: true,
                                 tam: 36 }),
  E.p("Sistema POS para la gestión y venta de dispositivos móviles",
      { alineacion: AlignmentType.CENTER, cursiva: true, despues: 720 }),
  E.p("Elkin Santiago Marín Duarte y Juan David Zabala Plata",
      { alineacion: AlignmentType.CENTER }),
  E.p("Corporación Unificada Nacional de Educación Superior — CUN",
      { alineacion: AlignmentType.CENTER }),
  E.p("4 de octubre de 2026", { alineacion: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),
];

const preparacion = [
  E.h1("Antes de entrar", false),
  E.p("La demostración solo sale bien si el sistema está listo antes de empezar a " +
      "hablar. Diez minutos antes:"),
  ...E.pasos([
    "Correr 6-BASE-DE-DATOS.bat para dejar los datos de prueba frescos. Si se " +
    "demostró algo ayer, el inventario quedó movido.",
    "Correr 2-INICIAR.bat y comprobar que el navegador abre en 127.0.0.1:8000.",
    "Entrar como admin y abrir un turno de caja. Sin turno no se puede facturar y " +
    "es el error más probable en vivo.",
    "Dejar abiertas tres pestañas: el sistema, la documentación de la API en /docs " +
    "y pgAdmin con la base pos_movil.",
    "Tener a mano un IMEI válido para escribir: 356789012345045.",
    "Si se va a mostrar la app de escritorio, abrirla antes con 7-APP-ESCRITORIO.bat " +
    "y dejarla minimizada.",
  ]),
  E.mixto([["Plan B: ", { bold: true }],
           ["si el servidor no levanta, están las capturas del manual de usuario. " +
            "Mejor mostrar una captura y explicarla bien que perder cinco minutos " +
            "depurando en frente del jurado."]], { antes: 180 }),

  E.h2("Reparto"),
  E.p("Si sustentan los dos, conviene repartir por capas y no por minutos: quien " +
      "explica la base de datos sigue con las reglas y los triggers; quien explica " +
      "la aplicación sigue con la demostración en vivo. Así cada uno defiende un " +
      "bloque completo y las preguntas tienen dueño."),
];

const estructura = [
  E.h1("Estructura de la sustentación"),
  ...E.rotulo(1, "Distribución del tiempo para una sustentación de 15 minutos"),
  E.tabla(
    ["Min.", "Bloque", "Qué se muestra"],
    [
      ["0–1", "El problema", "Nada todavía; se habla"],
      ["1–3", "Cómo se resolvió: la decisión de diseño", "Diagrama de arquitectura"],
      ["3–5", "La base de datos", "pgAdmin: tablas, triggers, el índice parcial"],
      ["5–10", "Demostración en vivo", "El sistema: venta completa y anulación"],
      ["10–12", "Las otras dos aplicaciones", "Escritorio en Flet y en Kotlin"],
      ["12–14", "Cómo se verificó", "Las pruebas corriendo"],
      ["14–15", "Cierre", "Conclusiones"],
    ], [0.6, 1.8, 2.2]),
  E.nota("Si el tiempo es de 10 minutos, se recorta el bloque de las otras dos " +
         "aplicaciones a una frase y se acorta la demostración a la venta, sin la " +
         "anulación."),
];

const guion = [
  E.h1("El guion"),

  E.h2("Minuto 0 a 1 — El problema"),
  E.p("«Un local que vende celulares maneja dos negocios al mismo tiempo. Vende " +
      "accesorios, que se cuentan: hay treinta cargadores y se venden tres, quedan " +
      "veintisiete. Y vende equipos, que no se cuentan: se identifican. Cada " +
      "teléfono tiene un IMEI único, y de ese número dependen la garantía, la " +
      "trazabilidad y la posibilidad de responderle al cliente seis meses después.»"),
  E.p("«Los sistemas genéricos tratan todo como una cantidad en una bodega. " +
      "Funcionan hasta que un cliente vuelve con un equipo dañado y hay que " +
      "demostrar cuándo se vendió y a quién. Nuestro sistema parte de esa " +
      "diferencia.»", { sangria: true }),
  E.mixto([["Nota para quien expone: ", { italics: true }],
           ["este minuto no lleva pantalla. Mirar al jurado. Es el único momento " +
            "en que se está vendiendo el problema y no el producto."]],
          { antes: 120 }),

  E.h2("Minuto 1 a 3 — La decisión de diseño"),
  E.p("«La decisión más importante del proyecto no fue qué framework usar, sino " +
      "dónde poner las reglas. Cuando se vende un equipo hay que marcar el IMEI " +
      "como vendido, descontar el stock, escribir el kardex y crear la garantía. " +
      "Eso lo puede hacer el backend en Python, o lo puede hacer PostgreSQL con " +
      "triggers.»"),
  E.p("«Lo pusimos en PostgreSQL. La razón es simple: si alguien entra por pgAdmin, " +
      "por un script o por otra aplicación, las reglas se siguen cumpliendo. Una " +
      "regla que vive en la aplicación solo protege contra la aplicación.»",
      { sangria: true }),
  E.p("«Por eso hay tres clientes distintos —web, escritorio en Python y escritorio " +
      "en Kotlin— y los tres obedecen exactamente las mismas reglas sin tener que " +
      "repetirlas.»", { sangria: true }),

  E.h2("Minuto 3 a 5 — La base de datos"),
  E.p("Mostrar en pgAdmin: la lista de tablas, y abrir una consulta."),
  E.p("«Son 37 tablas en once módulos, con 59 claves foráneas, 41 restricciones " +
      "CHECK y 22 tipos enumerados. Pero lo que quiero mostrar son dos cosas " +
      "concretas.»", { sangria: true }),
  E.p("Primera: la validación de IMEI.", { antes: 120 }),
  E.codigo("SELECT fn_imei_valido('356789012345045');   -- true"),
  E.codigo("SELECT fn_imei_valido('356789012345046');   -- false"),
  E.p("«Es el algoritmo de Luhn escrito en PL/pgSQL, y respalda una restricción " +
      "CHECK de la tabla. Un IMEI con el dígito verificador malo no entra ni " +
      "escribiendo el INSERT a mano.»", { sangria: true }),
  E.p("Segunda: el índice único parcial.", { antes: 120 }),
  E.codigo("CREATE UNIQUE INDEX ux_turno_abierto_por_caja"),
  E.codigo("  ON turnos_caja (caja_id) WHERE estado = 'ABIERTO';"),
  E.p("«Dos turnos abiertos en la misma caja romperían el arqueo. En vez de " +
      "verificarlo en la aplicación —lo que deja una ventana entre la consulta y la " +
      "inserción— lo prohíbe el motor. Aunque dos cajeros presionen el botón en el " +
      "mismo milisegundo, el segundo falla.»", { sangria: true }),

  E.h2("Minuto 5 a 10 — Demostración en vivo"),
  E.p("Este es el bloque que hay que ensayar. La secuencia exacta:"),
  ...E.pasos([
    "Entrar como admin. Señalar el panel: ventas del día, equipos disponibles, " +
    "alertas de stock.",
    "Ir a Punto de venta. Agregar un accesorio —un cargador, por ejemplo— y " +
    "subir la cantidad a dos.",
    "Agregar un equipo. Decir en voz alta: «aquí el sistema me obliga a elegir el " +
    "IMEI, y solo me muestra los que están disponibles».",
    "Elegir un cliente, revisar el total y facturar.",
    "Ir a Inventario, pestaña de equipos. Mostrar que ese IMEI quedó en VENDIDO.",
    "Ir a Posventa. Mostrar que la garantía se creó sola, con su fecha de " +
    "vencimiento.",
    "Volver a Ventas y anular la factura con un motivo.",
    "Volver a Inventario: el IMEI está otra vez DISPONIBLE. Volver a Posventa: la " +
    "garantía quedó anulada.",
  ]),
  E.p("«Eso que acaban de ver —que al anular todo volviera atrás— no lo hace el " +
      "programa en Python. Lo hace una función de PostgreSQL en una sola " +
      "transacción. O se deshace todo, o no se deshace nada.»",
      { sangria: true, antes: 120 }),
  E.mixto([["Si algo falla en vivo: ", { bold: true }],
           ["decirlo y seguir. «Me está pidiendo abrir caja, que es justamente la " +
            "regla que les mencioné» convierte un tropiezo en una demostración. " +
            "Callarse y teclear en silencio, no."]], { antes: 120 }),

  E.h2("Minuto 10 a 12 — Las otras dos aplicaciones"),
  E.p("Abrir la aplicación de escritorio en Flet al lado del navegador."),
  E.p("«Es la misma aplicación. Mismos colores, mismo menú, mismas reglas. Lo único " +
      "que cambia es que esta está escrita en Python con Flet y se empaqueta en un " +
      ".exe que corre sin tener Python instalado. Y hay una tercera en Kotlin con " +
      "Compose Desktop.»", { sangria: true }),
  E.p("«El punto no es que haya tres. El punto es que las tres consumen la misma " +
      "API, y por eso ninguna puede saltarse una regla. Si mañana hay que cambiar " +
      "cómo se calcula el IVA, se cambia en un solo lugar.»", { sangria: true }),

  E.h2("Minuto 12 a 14 — Cómo se verificó"),
  E.p("Correr 3-PRUEBAS.bat en una ventana, o mostrar la salida ya capturada."),
  E.p("«Hay seis conjuntos de pruebas automáticas, más de 250 comprobaciones, y " +
      "ninguna usa simulaciones: todas corren contra PostgreSQL y contra la API " +
      "reales.»", { sangria: true }),
  E.p("«Lo que más me interesa de las pruebas no es lo que verifica que funcione, " +
      "sino las seis que verifican que algo falle: insertar un IMEI inválido, " +
      "vender dos veces el mismo equipo, dejar el stock en negativo, abrir dos " +
      "turnos en una caja, descontar más de lo que vale la línea y pagar una " +
      "factura con un valor que no cuadra. Si alguna de esas pasara, el sistema " +
      "estaría roto.»", { sangria: true }),

  E.h2("Minuto 14 a 15 — Cierre"),
  E.p("«Tres conclusiones.»"),
  E.p("«Primera: poner las reglas en el motor y no en la aplicación hizo el sistema " +
      "correcto por construcción. Durante el desarrollo varias pruebas fallaron " +
      "porque PostgreSQL rechazó operaciones que el código Python habría dejado " +
      "pasar. Cada una de esas fallas era un error real atrapado temprano.»",
      { sangria: true }),
  E.p("«Segunda: generar el esquema SQL, el modelo de objetos y el diagrama UML " +
      "desde una sola definición eliminó una categoría entera de errores. No hay " +
      "tres copias que mantener sincronizadas: hay una fuente y tres salidas.»",
      { sangria: true }),
  E.p("«Tercera: guardar los permisos en tablas en vez de escribirlos en el código " +
      "permitió que los tres clientes armen su menú sin duplicar reglas. El cajero " +
      "no ve el módulo de usuarios en ninguno de los tres, y la razón está en una " +
      "sola fila de una tabla.»", { sangria: true }),
];

const preguntas = [
  E.h1("Preguntas que probablemente hagan"),
  E.p("Las respuestas están en el sistema; lo que sigue es cómo encontrarlas rápido."),

  E.h2("«¿Por qué PostgreSQL y no MySQL?»"),
  E.p("Por tres cosas concretas que el proyecto usa: tipos ENUM nativos, " +
      "restricciones CHECK que pueden llamar funciones propias —ahí vive la " +
      "validación de IMEI— e índices únicos parciales, que son los que impiden dos " +
      "turnos abiertos en una caja. En MySQL habría que simular las tres."),

  E.h2("«¿Qué pasa si dos cajeros venden el mismo equipo al tiempo?»"),
  E.p("Gana el primero en confirmar. El segundo recibe un error que dice que el " +
      "equipo ya no está disponible, porque el trigger verifica el estado dentro de " +
      "la misma transacción. No es una comprobación previa que se pueda quedar " +
      "vieja: es parte de la escritura."),

  E.h2("«¿Por qué repiten el cálculo del dinero en los tres clientes?»"),
  E.p("Porque el servidor exige que los pagos sumen el total exacto al centavo, así " +
      "que el cliente tiene que llegar a la misma cifra para poder cobrar. Pero la " +
      "cifra que manda es la del servidor: si no coinciden, la venta se rechaza y " +
      "el mensaje dice cuánto sumaron los pagos y cuánto era el total. Los tres " +
      "usan aritmética decimal con redondeo medio hacia arriba, nunca coma flotante."),

  E.h2("«¿Cómo saben que funciona?»"),
  E.p("Más de 250 comprobaciones automáticas en seis conjuntos, todas contra la " +
      "base y la API reales. La tabla 10 del documento técnico las lista una por " +
      "una. Y la interfaz web se recorrió con un navegador controlado por " +
      "Playwright: las doce rutas, con dos roles distintos, más una venta completa " +
      "hecha a clics."),

  E.h2("«¿Esto sirve para un negocio real?»"),
  E.p("Para un local pequeño o mediano, sí, con una advertencia honesta: falta la " +
      "integración con un proveedor tecnológico autorizado por la DIAN. El sistema " +
      "genera el consecutivo, el CUFE y el XML, pero no los transmite. Esa " +
      "integración es un trámite con un tercero, no un problema de diseño."),

  E.h2("«¿Qué fue lo más difícil?»"),
  E.p("Decidir dónde ponían las reglas. La primera versión tenía la lógica de " +
      "inventario en Python, y funcionaba. Moverla a triggers obligó a reescribir " +
      "el servicio de ventas completo, pero dejó el sistema a prueba de lo que pase " +
      "por fuera de la aplicación. Fue la decisión que más tiempo costó y la que " +
      "más valor dio."),

  E.h2("«¿Qué no alcanzaron a hacer?»"),
  E.p("Compilar la aplicación de Kotlin en el entorno de desarrollo: el acceso a " +
      "Maven Central estaba bloqueado. Se mitigó con una revisión estática del " +
      "código y verificando la lógica del analizador de JSON contra las respuestas " +
      "reales de la API, pero la compilación se hace en el equipo del usuario. " +
      "Está declarado en el documento técnico."),
  E.mixto([["Nota: ", { italics: true }],
           ["decir esto sin rodeos. Un jurado valora más una limitación reconocida " +
            "que una omitida que luego descubre."]], { antes: 120 }),
];

const cifras = [
  E.h1("Cifras para tener a mano"),
  E.tabla(
    ["Qué", "Cuánto"],
    [
      ["Tablas", "37 en 11 módulos"],
      ["Claves foráneas / CHECK / ENUM", "59 / 41 / 22"],
      ["Vistas / funciones y procedimientos / triggers", "8 / 6 / 9"],
      ["Operaciones de la API", "70 en 13 grupos"],
      ["Permisos / roles", "28 / 4"],
      ["Líneas de código (total)", "cerca de 14.700"],
      ["Comprobaciones automáticas", "más de 250"],
      ["Clientes construidos", "3 (web, Flet, Kotlin)"],
    ], [2.4, 1.2]),
  E.nota("Si no se recuerda una cifra exacta, es mejor decir «alrededor de» que " +
         "inventar un número. Una cifra inventada que el jurado verifica cuesta más " +
         "que una aproximación."),
];

const doc = new Document({
  creator: "Elkin Santiago Marín Duarte y Juan David Zabala Plata",
  title: "Guion de sustentación — POS Móvil",
  numbering: E.NUMERACION,
  styles: { default: { document: { run: { font: E.FUENTE, size: E.TAM } } } },
  sections: [{
    properties: { page: E.PAGINA },
    headers: { default: E.encabezado() },
    children: [...portada, ...preparacion, ...estructura, ...guion, ...preguntas,
               ...cifras],
  }],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.writeFileSync("Guion-de-Sustentacion-POS-Movil.docx", buffer);
  console.log("escrito: Guion-de-Sustentacion-POS-Movil.docx");
});
