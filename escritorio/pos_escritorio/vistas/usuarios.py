"""Usuarios, roles y permisos.

El control de acceso no se decide con una lista de roles escrita a mano en el
codigo: se decide con la tabla `rol_permisos`. Cambiar lo que puede hacer el
cajero es cambiar filas, no recompilar. Esta pantalla es la que permite verlo y
hacerlo.
"""

from __future__ import annotations

import flet as ft

from .. import tema as T
from .. import ui
from .base import Vista


class Usuarios(Vista):
    titulo = "Usuarios y permisos"
    icono = ft.Icons.MANAGE_ACCOUNTS
    permisos = ("usuarios.ver",)

    def __init__(self, ctx):
        super().__init__(ctx)
        self.pestana = 0

    def construir(self) -> ft.Control:
        return ft.Column(
            [
                self.encabezado("Los permisos viven en la base de datos. El menu de "
                                "cada usuario se arma con los suyos."),
                ui.segmentado(["Usuarios", "Roles y permisos"], self.pestana,
                              self._cambiar_pestana),
                (self._usuarios if self.pestana == 0 else self._permisos)(),
            ],
            spacing=14,
            expand=True,
        )

    def _cambiar_pestana(self, indice: int) -> None:
        self.pestana = indice
        self.ctx.refrescar()

    # -- usuarios -----------------------------------------------------------

    def _usuarios(self) -> ft.Control:
        usuarios = self.pedir(self.api.usuarios, []) or []
        roles = self.pedir(self.api.roles, []) or []

        filas = []
        for u in usuarios:
            acciones = []
            if self.api.puede("usuarios.editar"):
                acciones.append(ui.icono_boton(
                    ft.Icons.EDIT_OUTLINED, lambda e, us=u: self._dialogo(us, roles),
                    "Editar usuario", T.ACENTO))
            filas.append([
                ui.dato(u["username"], ft.FontWeight.W_600),
                u["nombre_completo"],
                u["email"],
                ui.insignia(u.get("rol", {}).get("nombre", "—"), "acento"),
                ui.insignia("ACTIVA" if u["activo"] else "CANCELADO",
                            "exito" if u["activo"] else "peligro"),
                ui.fecha_hora(u.get("ultimo_acceso")),
                ft.Row(acciones, spacing=0),
            ])

        barra: list[ft.Control] = []
        if self.api.puede("usuarios.crear"):
            barra.append(ui.boton("Nuevo usuario", lambda e: self._dialogo(None, roles),
                                  ft.Icons.ADD, "acento"))
        return ui.panel(
            ft.Column(
                ([ft.Row(barra, spacing=10)] if barra else []) + [
                    ui.tabla(["Usuario", "Nombre", "Correo", "Rol", "Estado",
                              "Ultimo acceso", ""], filas, "No hay usuarios"),
                ],
                spacing=12, expand=True,
            ),
            f"{len(usuarios)} usuarios",
            expandir=True,
        )

    def _dialogo(self, usuario: dict | None, roles: list[dict]) -> None:
        editando = usuario is not None
        u = usuario or {}
        username = ui.campo("Usuario", u.get("username", ""))
        nombre = ui.campo("Nombre completo", u.get("nombre_completo", ""))
        correo = ui.campo("Correo", u.get("email", ""), teclado=ft.KeyboardType.EMAIL)
        rol = ui.lista("Rol", [(r["id"], r["nombre"]) for r in roles],
                       valor=u.get("rol_id"))
        clave = ui.campo("Contrasena", clave=True)
        activo = ft.Switch(label="Usuario activo", value=bool(u.get("activo", True)),
                           active_color=T.ACENTO)
        if editando:
            username.read_only = True  # el nombre de usuario identifica la cuenta

        def guardar(_e=None):
            if not (nombre.value or "").strip() or not (correo.value or "").strip():
                self.ctx.aviso("El nombre y el correo son obligatorios.", "alerta")
                return
            if not rol.value:
                self.ctx.aviso("Elige el rol.", "alerta")
                return
            if editando:
                cuerpo = {
                    "rol_id": int(rol.value),
                    "nombre_completo": nombre.value.strip(),
                    "email": correo.value.strip(),
                    "activo": bool(activo.value),
                }
                self.ctx.cerrar()
                self.seguro(lambda: self.api.actualizar_usuario(u["id"], cuerpo),
                            "Usuario actualizado.")
                return
            if len((clave.value or "")) < 6:
                self.ctx.aviso("La contrasena debe tener al menos 6 caracteres.",
                               "alerta")
                return
            cuerpo = {
                "rol_id": int(rol.value),
                "username": (username.value or "").strip().lower(),
                "nombre_completo": nombre.value.strip(),
                "email": correo.value.strip(),
                "password": clave.value,
            }
            if not cuerpo["username"]:
                self.ctx.aviso("Escribe el nombre de usuario.", "alerta")
                return
            self.ctx.cerrar()
            self.seguro(lambda: self.api.crear_usuario(cuerpo),
                        f"Usuario {cuerpo['username']} creado.")

        campos: list[ft.Control] = [
            ft.Row([username, rol], spacing=10),
            nombre,
            correo,
        ]
        campos.append(activo if editando else clave)
        campos.append(ui.aviso(
            "La contrasena se guarda con PBKDF2-HMAC-SHA256 y sal por usuario; "
            "la base nunca almacena el texto plano.", "acento"))
        self.ctx.abrir(self.dialogo(
            "Editar usuario" if editando else "Nuevo usuario",
            ft.Column(campos, spacing=12, tight=True),
            "Guardar" if editando else "Crear", guardar, ancho=600))

    # -- roles y permisos ---------------------------------------------------

    def _permisos(self) -> ft.Control:
        roles = self.pedir(self.api.roles, []) or []
        catalogo = self.pedir(self.api.catalogo_permisos, []) or []
        if not roles or not catalogo:
            return ui.panel(ui.vacio("No se pudo leer el catalogo de permisos"),
                            "Roles y permisos")

        asignados = {r["id"]: set(self.pedir(lambda i=r["id"]: self.api.permisos_de_rol(i), []) or [])
                     for r in roles}

        # Los permisos se agrupan por modulo para que la matriz se lea de un golpe.
        modulos: dict[str, list[dict]] = {}
        for p in catalogo:
            modulos.setdefault(p["modulo"], []).append(p)

        bloques: list[ft.Control] = []
        for modulo, permisos in sorted(modulos.items()):
            filas = []
            for p in sorted(permisos, key=lambda x: x["codigo"]):
                celdas: list[ft.Control] = [
                    ft.Column([ui.dato(p["codigo"], ft.FontWeight.W_600),
                               ft.Text(p.get("descripcion") or "", size=11,
                                       color=T.TEXTO_TENUE)], spacing=1),
                ]
                for r in roles:
                    tiene = p["codigo"] in asignados[r["id"]]
                    celdas.append(
                        ft.Icon(ft.Icons.CHECK_CIRCLE if tiene else ft.Icons.REMOVE,
                                color=T.EXITO if tiene else T.BORDE_FUERTE, size=17)
                    )
                filas.append(celdas)
            bloques.append(
                ui.panel(
                    ui.tabla(["Permiso"] + [r["nombre"].title() for r in roles], filas,
                             alto=None),
                    f"Modulo {modulo}",
                )
            )

        resumen = ft.Row(
            [ui.kpi(r["nombre"].title(), f"{len(asignados[r['id']])} permisos",
                    ft.Icons.LOCK_OUTLINE,
                    "acento" if r["nombre"] == "ADMINISTRADOR" else "neutro",
                    r.get("descripcion") or "")
             for r in roles],
            spacing=12,
        )

        return ft.Column(
            [resumen] + bloques,
            spacing=14,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
