/**
 * Estilo compartido por los tres documentos del proyecto.
 *
 * Formato APA 7a edicion: Times New Roman 12, interlineado doble, margenes de
 * una pulgada, numero de pagina arriba a la derecha y referencias con sangria
 * francesa. Se define una sola vez aqui para que los tres salgan iguales.
 */

const {
  AlignmentType, BorderStyle, Footer, Header, HeadingLevel, LevelFormat,
  PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow, TextRun,
  VerticalAlign, WidthType,
} = require("docx");

// Carta: 8.5" x 11" en DXA (1440 = 1 pulgada).
const PAGINA = { size: { width: 12240, height: 15840 },
                 margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } };

const FUENTE = "Times New Roman";
const TAM = 24;          // 12 pt en medios puntos
const DOBLE = 480;       // interlineado doble (240 = sencillo)
const SENCILLO = 240;

// Paleta del sistema, para los elementos que no son texto corrido.
const AZUL = "1D4ED8";
const TINTA = "0F172A";
const GRIS = "475569";
const BORDE = "E2E8F0";
const SUAVE = "F8FAFC";

/** Parrafo de texto corrido con interlineado doble y sangria de primera linea. */
function p(texto, opciones = {}) {
  const {
    sangria = false, alineacion = AlignmentType.JUSTIFIED, interlineado = DOBLE,
    antes = 0, despues = 0, negrita = false, cursiva = false, tam = TAM,
    color = "000000", corridas = null,
  } = opciones;
  return new Paragraph({
    alignment: alineacion,
    spacing: { line: interlineado, before: antes, after: despues },
    indent: sangria ? { firstLine: 720 } : undefined,
    children: corridas || [
      new TextRun({ text: texto, font: FUENTE, size: tam, bold: negrita,
                    italics: cursiva, color }),
    ],
  });
}

/** Parrafo con trozos de distinto formato: [["texto", {bold:true}], ...] */
function mixto(trozos, opciones = {}) {
  return p("", {
    ...opciones,
    corridas: trozos.map(([texto, fmt = {}]) =>
      new TextRun({ text: texto, font: FUENTE, size: opciones.tam || TAM, ...fmt })),
  });
}

/** Titulo de nivel 1 (APA: centrado, negrita). */
function h1(texto, saltoAntes = true) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    alignment: AlignmentType.CENTER,
    pageBreakBefore: saltoAntes,
    spacing: { line: DOBLE, before: 0, after: 120 },
    children: [new TextRun({ text: texto, font: FUENTE, size: TAM, bold: true,
                             color: TINTA })],
  });
}

/** Titulo de nivel 2 (APA: alineado a la izquierda, negrita). */
function h2(texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    spacing: { line: DOBLE, before: 240, after: 60 },
    children: [new TextRun({ text: texto, font: FUENTE, size: TAM, bold: true,
                             color: TINTA })],
  });
}

/** Titulo de nivel 3 (APA: izquierda, negrita cursiva). */
function h3(texto) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    spacing: { line: DOBLE, before: 180, after: 60 },
    children: [new TextRun({ text: texto, font: FUENTE, size: TAM, bold: true,
                             italics: true, color: TINTA })],
  });
}

/** Vineta. Usa la numeracion configurada, nunca un caracter '•' escrito a mano. */
function vinieta(texto, nivel = 0, corridas = null) {
  return new Paragraph({
    numbering: { reference: "vinietas", level: nivel },
    spacing: { line: DOBLE, before: 0, after: 0 },
    children: corridas || [new TextRun({ text: texto, font: FUENTE, size: TAM })],
  });
}

let listaActual = -1;

/**
 * Lista numerada completa. Toma una referencia nueva en cada llamada para que
 * empiece en 1; `numerado` suelto seguiria el contador de la lista anterior.
 */
function pasos(items) {
  listaActual = (listaActual + 1) % 20;
  const referencia = `numeros${listaActual}`;
  return items.map((texto) => new Paragraph({
    numbering: { reference: referencia, level: 0 },
    spacing: { line: DOBLE, before: 0, after: 0 },
    children: [new TextRun({ text: texto, font: FUENTE, size: TAM })],
  }));
}

/** Linea de codigo o de consola, en monoespaciada y sobre fondo gris. */
function codigo(texto) {
  return new Paragraph({
    spacing: { line: SENCILLO, before: 0, after: 0 },
    shading: { type: ShadingType.CLEAR, fill: SUAVE },
    indent: { left: 360 },
    children: [new TextRun({ text: texto, font: "Consolas", size: 19,
                             color: TINTA })],
  });
}

/**
 * Rotulo de tabla o figura, segun APA: numero en negrita y titulo en cursiva.
 * Van con `keepNext` para que el salto de pagina no separe el rotulo de su tabla.
 */
function rotulo(numero, titulo, tipo = "Tabla") {
  const comun = { alignment: AlignmentType.LEFT, keepNext: true };
  return [
    new Paragraph({
      ...comun,
      spacing: { line: DOBLE, before: 240 },
      children: [new TextRun({ text: `${tipo} ${numero}`, font: FUENTE, size: TAM,
                               bold: true })],
    }),
    new Paragraph({
      ...comun,
      spacing: { line: DOBLE, after: 60 },
      children: [new TextRun({ text: titulo, font: FUENTE, size: TAM,
                               italics: true })],
    }),
  ];
}

/** Nota al pie de una tabla o figura. */
function nota(texto) {
  return p("", {
    corridas: [
      new TextRun({ text: "Nota. ", font: FUENTE, size: 20, italics: true }),
      new TextRun({ text: texto, font: FUENTE, size: 20 }),
    ],
    alineacion: AlignmentType.LEFT, interlineado: SENCILLO, antes: 60, despues: 240,
  });
}

/**
 * Tabla con el ancho repartido por pesos.
 * docx-js exige el ancho en la tabla y en cada celda, los dos en DXA.
 */
function tabla(encabezados, filas, pesos = null) {
  const ANCHO = 9360;   // 6.5" utiles entre margenes
  const n = encabezados.length;
  const reparto = pesos || Array(n).fill(1);
  const suma = reparto.reduce((a, b) => a + b, 0);
  const anchos = reparto.map((x) => Math.round((ANCHO * x) / suma));
  // El redondeo puede dejar sobra o falta: se ajusta la ultima columna.
  anchos[n - 1] += ANCHO - anchos.reduce((a, b) => a + b, 0);

  const celda = (contenido, i, cabecera) => new TableCell({
    width: { size: anchos[i], type: WidthType.DXA },
    shading: cabecera ? { type: ShadingType.CLEAR, fill: SUAVE } : undefined,
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      spacing: { line: SENCILLO, before: 20, after: 20 },
      children: [new TextRun({ text: String(contenido), font: FUENTE, size: 20,
                               bold: cabecera, color: cabecera ? TINTA : "000000" })],
    })],
  });

  const linea = (sz) => ({ style: BorderStyle.SINGLE, size: sz, color: BORDE });
  return new Table({
    columnWidths: anchos,
    width: { size: ANCHO, type: WidthType.DXA },
    borders: {
      top: linea(6), bottom: linea(6), left: linea(6), right: linea(6),
      insideHorizontal: linea(4), insideVertical: linea(4),
    },
    rows: [
      new TableRow({
        tableHeader: true,
        children: encabezados.map((h, i) => celda(h, i, true)),
      }),
      ...filas.map((f) => new TableRow({
        children: f.map((c, i) => celda(c, i, false)),
      })),
    ],
  });
}

/** Numeracion de vinietas y de listas. */
const NUMERACION = {
  config: [
    {
      reference: "vinietas",
      levels: [0, 1, 2].map((nivel) => ({
        level: nivel,
        format: LevelFormat.BULLET,
        text: ["•", "◦", "▪"][nivel],
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720 + nivel * 360, hanging: 360 } } },
      })),
    },
    // Veinte referencias independientes para listas numeradas. docx-js lleva un
    // contador por referencia, asi que cada lista nueva toma una libre y empieza
    // en 1 en vez de continuar donde quedo la anterior.
    ...Array.from({ length: 20 }, (_, i) => ({
      reference: `numeros${i}`,
      levels: [0, 1].map((nivel) => ({
        level: nivel,
        format: nivel === 0 ? LevelFormat.DECIMAL : LevelFormat.LOWER_LETTER,
        text: nivel === 0 ? "%1." : "%2.",
        alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720 + nivel * 360, hanging: 360 } } },
      })),
    })),
  ],
};

/** Encabezado APA: numero de pagina arriba a la derecha. */
function encabezado() {
  return new Header({
    children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FUENTE,
                               size: TAM })],
    })],
  });
}

function piePagina(texto) {
  return new Footer({
    children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: texto, font: FUENTE, size: 18, color: GRIS })],
    })],
  });
}

/** Linea horizontal: un parrafo con borde inferior, no una tabla. */
function separador() {
  return new Paragraph({
    spacing: { before: 120, after: 120 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: BORDE } },
    children: [new TextRun({ text: "", size: 2 })],
  });
}

module.exports = {
  PAGINA, FUENTE, TAM, DOBLE, SENCILLO, AZUL, TINTA, GRIS, BORDE, SUAVE,
  NUMERACION, p, mixto, h1, h2, h3, vinieta, pasos, codigo, rotulo, nota,
  tabla, encabezado, piePagina, separador,
};
