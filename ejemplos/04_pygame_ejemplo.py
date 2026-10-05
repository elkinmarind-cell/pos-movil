"""Pygame — grafico de ventas dibujado cuadro a cuadro.

Tkinter y Flet dibujan widgets: uno describe un boton y la libreria lo pinta.
Pygame no tiene widgets. Da una superficie de pixeles y un bucle; todo lo demas
—las barras, los ejes, el resaltado bajo el raton— se dibuja a mano, sesenta
veces por segundo.

Por eso se usa en juegos y en visualizaciones: a cambio de escribir mas, se
controla cada pixel y cada cuadro.

    pip install pygame
    python 04_pygame_ejemplo.py

Datos: si hay conexion a PostgreSQL toma las ventas reales de los ultimos 14
dias; si no, usa una serie de ejemplo para que el programa corra igual.
"""

from __future__ import annotations

import os
import sys
from datetime import date, timedelta

import pygame

ANCHO, ALTO = 940, 560
FONDO = (241, 245, 249)
PANEL = (255, 255, 255)
BORDE = (226, 232, 240)
TEXTO = (15, 23, 42)
TENUE = (100, 116, 139)
ACENTO = (29, 78, 216)
ACENTO_CLARO = (96, 136, 232)
EXITO = (4, 120, 87)


def datos_de_ejemplo() -> list[tuple[str, float]]:
    base = date.today() - timedelta(days=13)
    serie = [0, 0, 1_250_000, 980_000, 0, 2_340_000, 1_875_000,
             3_100_000, 0, 1_420_000, 2_780_000, 1_980_000, 3_450_000, 2_337_874]
    return [((base + timedelta(days=i)).isoformat(), float(v))
            for i, v in enumerate(serie)]


def datos_de_postgres() -> list[tuple[str, float]] | None:
    """Intenta leer las ventas reales. Si no se puede, devuelve None."""
    cadena = os.environ.get("POS_BD")
    if not cadena:
        return None
    try:
        import psycopg
        with psycopg.connect(cadena) as cn, cn.cursor() as cur:
            # generate_series con INTERVAL devuelve timestamps; hay que bajarlos a
            # fecha para que la etiqueta sea 2026-09-28 y no 2026-09-28 00:00:00.
            cur.execute("""
                SELECT d.dia::date::text,
                       COALESCE(SUM(v.total), 0)::float
                  FROM generate_series(CURRENT_DATE - INTERVAL '13 days',
                                       CURRENT_DATE, '1 day') AS d(dia)
                  LEFT JOIN ventas v
                         ON v.fecha::date = d.dia::date
                        AND v.estado = 'COMPLETADA'
                 GROUP BY d.dia::date
                 ORDER BY d.dia::date
            """)
            return [(f, float(t)) for f, t in cur.fetchall()]
    except Exception:
        return None


def pesos(valor: float) -> str:
    return f"$ {int(valor):,}".replace(",", ".")


def main() -> None:
    datos = datos_de_postgres() or datos_de_ejemplo()
    en_vivo = datos_de_postgres() is not None

    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("POS Movil — Ventas de los ultimos 14 dias")
    reloj = pygame.time.Clock()

    titulo_f = pygame.font.SysFont("Segoe UI", 24, bold=True)
    sub_f = pygame.font.SysFont("Segoe UI", 13)
    pequeno_f = pygame.font.SysFont("Segoe UI", 12)
    valor_f = pygame.font.SysFont("Segoe UI", 15, bold=True)

    techo = max((v for _f, v in datos), default=1) or 1
    izq, arriba, alto_area = 70, 150, 300
    ancho_barra = (ANCHO - izq - 60) / len(datos)

    # El bucle principal: eventos -> estado -> dibujo. Tres pasos, cada cuadro.
    ejecutando = True
    while ejecutando:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                ejecutando = False
            elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                ejecutando = False

        raton_x, raton_y = pygame.mouse.get_pos()

        pantalla.fill(FONDO)
        pygame.draw.rect(pantalla, PANEL, (28, 28, ANCHO - 56, ALTO - 56),
                         border_radius=12)
        pygame.draw.rect(pantalla, BORDE, (28, 28, ANCHO - 56, ALTO - 56), 1,
                         border_radius=12)

        pantalla.blit(titulo_f.render("Ventas de los ultimos 14 dias", True, TEXTO),
                      (56, 54))
        pantalla.blit(
            sub_f.render(
                "Datos en vivo desde PostgreSQL" if en_vivo
                else "Serie de ejemplo — define POS_BD para leer la base real",
                True, EXITO if en_vivo else TENUE),
            (56, 88))

        # Lineas guia horizontales con su valor.
        for i in range(5):
            y = arriba + alto_area - (alto_area * i / 4)
            pygame.draw.line(pantalla, BORDE, (izq, y), (ANCHO - 60, y), 1)
            etiqueta = pequeno_f.render(pesos(techo * i / 4), True, TENUE)
            pantalla.blit(etiqueta, (izq - etiqueta.get_width() - 10, y - 8))

        resaltada = None
        for i, (fecha, valor) in enumerate(datos):
            x = izq + i * ancho_barra
            ancho = ancho_barra * 0.62
            altura = (valor / techo) * alto_area if valor else 2
            rect = pygame.Rect(x + (ancho_barra - ancho) / 2,
                               arriba + alto_area - altura, ancho, max(altura, 2))
            encima = rect.collidepoint(raton_x, raton_y) or (
                x <= raton_x < x + ancho_barra and arriba <= raton_y <= arriba + alto_area)
            color = ACENTO_CLARO if encima else (ACENTO if valor else BORDE)
            pygame.draw.rect(pantalla, color, rect, border_radius=5)
            if encima:
                resaltada = (fecha, valor, rect)
            dia = pequeno_f.render(fecha[-2:], True, TENUE)
            pantalla.blit(dia, (x + (ancho_barra - dia.get_width()) / 2,
                                arriba + alto_area + 10))

        pygame.draw.line(pantalla, (203, 213, 225), (izq, arriba + alto_area),
                         (ANCHO - 60, arriba + alto_area), 2)

        # Globo con el detalle de la barra senalada.
        if resaltada:
            fecha, valor, rect = resaltada
            texto = f"{fecha} · {pesos(valor)}"
            render = valor_f.render(texto, True, (255, 255, 255))
            globo = pygame.Rect(0, 0, render.get_width() + 20, render.get_height() + 12)
            globo.centerx = min(max(rect.centerx, 100), ANCHO - 100)
            globo.bottom = max(rect.top - 8, arriba - 6)
            pygame.draw.rect(pantalla, TEXTO, globo, border_radius=6)
            pantalla.blit(render, (globo.x + 10, globo.y + 6))

        total = sum(v for _f, v in datos)
        pantalla.blit(valor_f.render(f"Total del periodo: {pesos(total)}", True, TEXTO),
                      (56, ALTO - 68))
        pantalla.blit(pequeno_f.render(
            "Pasa el raton sobre una barra para ver el detalle · ESC para salir",
            True, TENUE), (56, ALTO - 44))

        pygame.display.flip()
        reloj.tick(60)   # 60 cuadros por segundo

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
