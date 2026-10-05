"""Mi primera ventana — Tkinter.

El punto de partida de cualquier interfaz de escritorio en Python: crear una
ventana, ponerle titulo y tamano, y mostrarla hasta que el usuario la cierre.

Tkinter viene con Python, no hay que instalar nada.

    python 01_mi_primera_ventana.py
"""

import tkinter as tk

# --- 1. La ventana ----------------------------------------------------------
# Tk() crea la ventana principal. Solo puede haber una por programa; las demas
# se crean como Toplevel.
ventana = tk.Tk()
ventana.title("POS Movil — Mi primera ventana")
ventana.geometry("520x300")        # ancho x alto en pixeles
ventana.configure(bg="#F1F5F9")    # el mismo fondo del sistema POS
ventana.resizable(False, False)    # que no se pueda cambiar el tamano

# --- 2. El contenido --------------------------------------------------------
# Un widget se crea diciendo de quien es hijo (aqui, la ventana) y se muestra
# llamando a un gestor de geometria: pack, grid o place.
tk.Label(
    ventana,
    text="Sistema POS para dispositivos moviles",
    font=("Segoe UI", 16, "bold"),
    bg="#F1F5F9",
    fg="#0F172A",
).pack(pady=(46, 6))

tk.Label(
    ventana,
    text="Corporacion Unificada Nacional — CUN",
    font=("Segoe UI", 10),
    bg="#F1F5F9",
    fg="#64748B",
).pack()

mensaje = tk.Label(
    ventana,
    text="",
    font=("Segoe UI", 11),
    bg="#F1F5F9",
    fg="#047857",
)
mensaje.pack(pady=18)


# --- 3. La interaccion ------------------------------------------------------
# Un boton no "hace" nada por si mismo: se le pasa en `command` la funcion que
# debe ejecutarse cuando lo presionen.
def saludar() -> None:
    mensaje.config(text="La ventana funciona. Ya hay interfaz grafica.")


tk.Button(
    ventana,
    text="Probar",
    font=("Segoe UI", 10, "bold"),
    bg="#1D4ED8",
    fg="white",
    activebackground="#1E40AF",
    activeforeground="white",
    relief="flat",
    padx=26,
    pady=8,
    cursor="hand2",
    command=saludar,
).pack()

# --- 4. El bucle de eventos -------------------------------------------------
# mainloop() se queda esperando: dibuja, escucha el teclado y el raton, y llama
# a las funciones que correspondan. El programa vive aqui hasta que se cierre
# la ventana. Sin esta linea, la ventana aparece y desaparece al instante.
ventana.mainloop()
