"""API del Sistema POS para la gestion y venta de dispositivos moviles."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from .config import settings
from .database import engine
from .routers import (auth, caja, catalogo, clientes, compras, inventario, iot, posventa,
                      reportes, telefonia, usuarios, ventas)

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(f"{settings.descripcion}\n\n"
                 "Modulos: seguridad con roles y permisos, catalogo, inventario serializado por "
                 "IMEI, compras, clientes, caja con arqueo, ventas con facturacion electronica, "
                 "apartados, posventa, servicio tecnico, activacion de lineas, IoT y reportes."),
)

app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

for modulo in (auth, usuarios, catalogo, inventario, clientes, compras, caja, ventas,
               posventa, telefonia, iot, reportes):
    app.include_router(modulo.router)


@app.get("/api/salud", tags=["Sistema"], summary="Estado del servicio")
def salud():
    with engine.connect() as cx:
        version = cx.execute(text("SHOW server_version")).scalar()
        tablas = cx.execute(text("SELECT COUNT(*) FROM information_schema.tables "
                                 "WHERE table_schema='public' AND table_type='BASE TABLE'")).scalar()
    return {"estado": "ok", "aplicacion": settings.app_name, "version": settings.version,
            "postgresql": version, "tablas": tablas}


# La interfaz compilada se sirve desde el mismo proceso cuando existe
DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

# index.html nunca se cachea: si se guardara, el navegador seguiria pidiendo una
# version vieja de la interfaz despues de cada compilacion. Los archivos de
# /assets si se cachean, porque su nombre lleva el hash del contenido.
SIN_CACHE = {"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0", "Pragma": "no-cache"}

if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/{ruta_spa:path}", include_in_schema=False)
    def interfaz(ruta_spa: str):
        archivo = DIST / ruta_spa
        if ruta_spa and archivo.is_file():
            return FileResponse(archivo)
        return FileResponse(DIST / "index.html", headers=SIN_CACHE)
