"""Punto de entrada de la API del POS de dispositivos moviles."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import Base, engine
from .routers import auth, clientes, garantias, inventario, productos, reportes, ventas


@asynccontextmanager
async def ciclo_vida(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "API del sistema POS para la gestion y venta de dispositivos moviles.\n\n"
        "Modulos: caja/ventas con IVA, inventario serializado por IMEI, clientes, "
        "garantias y reportes gerenciales."
    ),
    lifespan=ciclo_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for modulo in (auth, productos, inventario, clientes, ventas, garantias, reportes):
    app.include_router(modulo.router)


@app.get("/api/salud", tags=["Sistema"], summary="Verificacion de estado")
def salud():
    return {
        "estado": "ok",
        "aplicacion": settings.app_name,
        "version": settings.version,
        "motor": "PostgreSQL" if settings.es_postgres else "SQLite",
    }


# --------------------------------------------------------------------------
# Interfaz compilada
# --------------------------------------------------------------------------
# Si existe frontend/dist, el backend la sirve en la raiz. Asi el sistema
# completo corre con un solo proceso y sin Node instalado. Durante el
# desarrollo se usa el servidor de Vite (puerto 5173), que tiene recarga
# automatica; este bloque no estorba en ese caso.
DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"

if DIST.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST / "assets"), name="assets")

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest():
        return FileResponse(DIST / "manifest.webmanifest")

    @app.get("/{ruta_spa:path}", include_in_schema=False)
    def interfaz(ruta_spa: str):
        """Entrega index.html para que React Router maneje la navegacion."""
        archivo = DIST / ruta_spa
        if ruta_spa and archivo.is_file():
            return FileResponse(archivo)
        return FileResponse(DIST / "index.html")
