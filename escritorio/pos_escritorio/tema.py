"""Sistema visual de la aplicacion de escritorio.

Son los mismos colores, radios y pesos tipograficos que usa la interfaz web
(`frontend/src/estilos.css`). Un solo lenguaje visual para los dos clientes:
quien usa el escritorio y quien entra por el navegador ven el mismo producto.
"""

import flet as ft

# --- superficie -------------------------------------------------------------
FONDO = "#F1F5F9"
PANEL = "#FFFFFF"
PANEL_SUAVE = "#F8FAFC"
BORDE = "#E2E8F0"
BORDE_FUERTE = "#CBD5E1"

# --- texto ------------------------------------------------------------------
TEXTO = "#0F172A"
TEXTO_MEDIO = "#475569"
TEXTO_TENUE = "#64748B"

# --- marca y estados --------------------------------------------------------
ACENTO = "#1D4ED8"
ACENTO_FUERTE = "#1E40AF"
ACENTO_SUAVE = "#EFF6FF"
ACENTO_BORDE = "#BFDBFE"
EXITO = "#047857"
EXITO_SUAVE = "#ECFDF5"
ALERTA = "#B45309"
ALERTA_SUAVE = "#FFFBEB"
PELIGRO = "#B91C1C"
PELIGRO_SUAVE = "#FEF2F2"
NEUTRO_SUAVE = "#F1F5F9"

# --- forma ------------------------------------------------------------------
RADIO = 10
RADIO_SM = 7

# Cada tono resuelve a (color de texto, color de fondo). Lo usan las insignias
# de estado y los avisos, para no repetir la pareja de colores en cada vista.
TONOS: dict[str, tuple[str, str]] = {
    "neutro": (TEXTO_MEDIO, NEUTRO_SUAVE),
    "acento": (ACENTO, ACENTO_SUAVE),
    "exito": (EXITO, EXITO_SUAVE),
    "alerta": (ALERTA, ALERTA_SUAVE),
    "peligro": (PELIGRO, PELIGRO_SUAVE),
}

# Estado de negocio -> tono visual. La misma tabla que la interfaz web, para que
# "ANULADA" se vea rojo en los dos clientes.
ESTADOS: dict[str, str] = {
    "DISPONIBLE": "exito",
    "COMPLETADA": "exito",
    "VIGENTE": "exito",
    "ABIERTO": "exito",
    "ENTREGADA": "exito",
    "ACTIVA": "exito",
    "APARTADO": "acento",
    "RESERVADO": "acento",
    "RECIBIDA": "acento",
    "EN_SERVICIO": "alerta",
    "EN_RECLAMACION": "alerta",
    "PENDIENTE": "alerta",
    "DIAGNOSTICO": "alerta",
    "REPARACION": "alerta",
    "POR_VENCER": "alerta",
    "VENDIDO": "neutro",
    "CERRADO": "neutro",
    "ATENDIDA": "neutro",
    "ENTREGADO": "neutro",
    "ANULADA": "peligro",
    "VENCIDA": "peligro",
    "DEVUELTO": "peligro",
    "DADO_DE_BAJA": "peligro",
    "CANCELADO": "peligro",
    "RECHAZADA": "peligro",
}


def tono_de(estado: str | None) -> str:
    """Tono visual que le corresponde a un estado de negocio."""
    return ESTADOS.get((estado or "").upper(), "neutro")


def tema() -> ft.Theme:
    """Tema de Flet derivado de los tokens de arriba.

    Se define el `ColorScheme` completo en lugar de un `color_scheme_seed` para
    que el azul sea exactamente el de la marca y no una aproximacion calculada
    por Material 3.
    """
    return ft.Theme(
        use_material3=True,
        font_family="Segoe UI",
        color_scheme=ft.ColorScheme(
            primary=ACENTO,
            on_primary=ft.Colors.WHITE,
            primary_container=ACENTO_SUAVE,
            on_primary_container=ACENTO_FUERTE,
            secondary=TEXTO_MEDIO,
            on_secondary=ft.Colors.WHITE,
            error=PELIGRO,
            on_error=ft.Colors.WHITE,
            surface=PANEL,
            on_surface=TEXTO,
            on_surface_variant=TEXTO_MEDIO,
            outline=BORDE_FUERTE,
            outline_variant=BORDE,
        ),
        scaffold_bgcolor=FONDO,
        card_bgcolor=PANEL,
        divider_color=BORDE,
        hint_color=TEXTO_TENUE,
        visual_density=ft.VisualDensity.COMPACT,
    )
