package ejemplos

import java.awt.BorderLayout
import java.awt.Color
import java.awt.Dimension
import java.awt.Font
import java.awt.FlowLayout
import javax.swing.BorderFactory
import javax.swing.BoxLayout
import javax.swing.JButton
import javax.swing.JFrame
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.SwingConstants
import javax.swing.SwingUtilities

/**
 * Mi primera ventana en Kotlin.
 *
 * Se usa Swing, que viene dentro del JDK: cero dependencias, compila con solo
 * tener Java instalado. Es el equivalente de Tkinter en Python.
 *
 *     gradlew ventana
 *
 * Lo unico que hay que respetar es la regla del hilo: Swing no es seguro para
 * varios hilos, asi que toda la interfaz se construye y se toca dentro de
 * `SwingUtilities.invokeLater`, que ejecuta el bloque en el hilo de eventos.
 */
fun main() = SwingUtilities.invokeLater {

    // --- 1. La ventana ------------------------------------------------------
    val ventana = JFrame("POS Movil — Mi primera ventana en Kotlin").apply {
        defaultCloseOperation = JFrame.EXIT_ON_CLOSE
        preferredSize = Dimension(520, 300)
        isResizable = false
    }

    val fondo = Color(0xF1, 0xF5, 0xF9)
    val tinta = Color(0x0F, 0x17, 0x2A)
    val tenue = Color(0x64, 0x74, 0x8B)
    val azul = Color(0x1D, 0x4E, 0xD8)
    val verde = Color(0x04, 0x78, 0x57)

    // --- 2. El contenido ----------------------------------------------------
    val panel = JPanel().apply {
        layout = BoxLayout(this, BoxLayout.Y_AXIS)
        background = fondo
        border = BorderFactory.createEmptyBorder(46, 24, 24, 24)
    }

    fun etiqueta(texto: String, tamano: Int, color: Color, negrita: Boolean = false) =
        JLabel(texto, SwingConstants.CENTER).apply {
            font = Font("Segoe UI", if (negrita) Font.BOLD else Font.PLAIN, tamano)
            foreground = color
            alignmentX = JLabel.CENTER_ALIGNMENT
        }

    val titulo = etiqueta("Sistema POS para dispositivos moviles", 18, tinta, negrita = true)
    val sub = etiqueta("Corporacion Unificada Nacional — CUN", 12, tenue)
    val mensaje = etiqueta(" ", 13, verde)

    // --- 3. La interaccion --------------------------------------------------
    // El boton no hace nada por si solo: se le conecta la accion. En Kotlin,
    // `addActionListener` acepta una lambda directamente porque ActionListener
    // es una interfaz de un solo metodo.
    val boton = JButton("Probar").apply {
        font = Font("Segoe UI", Font.BOLD, 13)
        background = azul
        foreground = Color.WHITE
        isFocusPainted = false
        isBorderPainted = false
        isOpaque = true
        alignmentX = JButton.CENTER_ALIGNMENT
        addActionListener {
            mensaje.text = "La ventana funciona. Ya hay interfaz grafica en Kotlin."
        }
    }

    panel.add(titulo)
    panel.add(JPanel(FlowLayout()).apply { background = fondo; add(sub) })
    panel.add(mensaje)
    panel.add(JPanel(FlowLayout()).apply { background = fondo; add(boton) })

    // --- 4. Mostrar ---------------------------------------------------------
    ventana.add(panel, BorderLayout.CENTER)
    ventana.pack()
    ventana.setLocationRelativeTo(null)   // centrada en la pantalla
    ventana.isVisible = true
}
