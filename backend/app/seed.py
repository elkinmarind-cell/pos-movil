"""Carga de datos de prueba. Ejecutar:  python -m app.seed"""
from decimal import Decimal

from .database import Base, SessionLocal, engine
from .models import (
    Categoria, Cliente, EquipoImei, EstadoImei, Marca, Producto,
    Proveedor, RolUsuario, TipoDocumento, Usuario,
)
from .security import hash_password


def digito_luhn(base14: str) -> str:
    """Calcula el digito verificador que hace valido un IMEI de 15 posiciones."""
    suma = 0
    for i, caracter in enumerate(base14[::-1]):
        digito = int(caracter)
        if i % 2 == 0:  # posiciones que se duplican al anteponer el verificador
            digito *= 2
            if digito > 9:
                digito -= 9
        suma += digito
    return str((10 - suma % 10) % 10)


def imei(base14: str) -> str:
    return base14 + digito_luhn(base14)


def sembrar() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(Usuario).count():
            print("La base ya tiene datos. No se sembro nada.")
            return

        # ---------------- Usuarios ----------------
        usuarios = [
            Usuario(username="admin", nombre_completo="Elkin Santiago Marin Duarte",
                    email="admin@posmovil.co", password_hash=hash_password("admin123"),
                    rol=RolUsuario.ADMIN),
            Usuario(username="cajero", nombre_completo="Juan David Zabala Plata",
                    email="cajero@posmovil.co", password_hash=hash_password("cajero123"),
                    rol=RolUsuario.CAJERO),
            Usuario(username="bodega", nombre_completo="Operario de Bodega",
                    email="bodega@posmovil.co", password_hash=hash_password("bodega123"),
                    rol=RolUsuario.BODEGA),
        ]
        db.add_all(usuarios)

        # ---------------- Catalogo ----------------
        categorias = {
            "Smartphones": Categoria(nombre="Smartphones", descripcion="Equipos moviles con control por IMEI"),
            "Accesorios": Categoria(nombre="Accesorios", descripcion="Cargadores, forros, vidrios templados"),
            "Audio": Categoria(nombre="Audio", descripcion="Audifonos y parlantes"),
            "SIM y recargas": Categoria(nombre="SIM y recargas", descripcion="Lineas nuevas y recargas"),
        }
        marcas = {
            "Samsung": Marca(nombre="Samsung", pais_origen="Corea del Sur"),
            "Xiaomi": Marca(nombre="Xiaomi", pais_origen="China"),
            "Motorola": Marca(nombre="Motorola", pais_origen="Estados Unidos"),
            "Apple": Marca(nombre="Apple", pais_origen="Estados Unidos"),
            "Genericos": Marca(nombre="Genericos", pais_origen="Varios"),
        }
        db.add_all(list(categorias.values()) + list(marcas.values()))
        db.flush()

        proveedor = Proveedor(nit="900123456-7", razon_social="Distribuidora Movil Andina S.A.S.",
                              contacto="Carolina Ruiz", telefono="3105558877", email="ventas@movilandina.co")
        db.add(proveedor)
        db.flush()

        # ---------------- Productos ----------------
        equipos = [
            ("SM-A155", "Samsung Galaxy A15 128GB", "Samsung", Decimal("620000"), Decimal("849900")),
            ("XM-RN13", "Xiaomi Redmi Note 13 256GB", "Xiaomi", Decimal("680000"), Decimal("929900")),
            ("MT-G24", "Motorola Moto G24 128GB", "Motorola", Decimal("410000"), Decimal("599900")),
            ("AP-IP13", "Apple iPhone 13 128GB", "Apple", Decimal("2350000"), Decimal("2999900")),
        ]
        productos: dict[str, Producto] = {}
        for sku, nombre, marca, costo, venta in equipos:
            producto = Producto(
                sku=sku, nombre=nombre, marca_id=marcas[marca].id,
                categoria_id=categorias["Smartphones"].id,
                precio_costo=costo, precio_venta=venta, iva_porcentaje=Decimal("19"),
                requiere_imei=True, meses_garantia=12, stock_minimo=2,
                descripcion="Equipo nuevo, sellado, con garantia de fabrica.",
            )
            productos[sku] = producto
            db.add(producto)

        accesorios = [
            ("AC-CAR20", "Cargador rapido 20W USB-C", "Accesorios", "Genericos",
             Decimal("18000"), Decimal("39900"), 40),
            ("AC-VID01", "Vidrio templado universal", "Accesorios", "Genericos",
             Decimal("3500"), Decimal("15000"), 120),
            ("AC-FOR01", "Forro antichoque", "Accesorios", "Genericos",
             Decimal("6000"), Decimal("25000"), 80),
            ("AU-BT500", "Audifonos Bluetooth TWS", "Audio", "Genericos",
             Decimal("45000"), Decimal("89900"), 25),
            ("SM-SIM01", "SIM card prepago", "SIM y recargas", "Genericos",
             Decimal("1000"), Decimal("5000"), 200),
        ]
        for sku, nombre, cat, marca, costo, venta, stock in accesorios:
            producto = Producto(
                sku=sku, nombre=nombre, marca_id=marcas[marca].id, categoria_id=categorias[cat].id,
                precio_costo=costo, precio_venta=venta, iva_porcentaje=Decimal("19"),
                requiere_imei=False, meses_garantia=3, stock_actual=stock, stock_minimo=10,
            )
            productos[sku] = producto
            db.add(producto)
        db.flush()

        # ---------------- IMEI en bodega ----------------
        bases = {
            "SM-A155": ["35678901234501", "35678901234502", "35678901234503", "35678901234504"],
            "XM-RN13": ["35912345678011", "35912345678012", "35912345678013"],
            "MT-G24":  ["35455566677701", "35455566677702", "35455566677703", "35455566677704"],
            "AP-IP13": ["35333344455501", "35333344455502"],
        }
        colores = ["Negro", "Azul", "Plata", "Verde"]
        for sku, lista in bases.items():
            for i, base in enumerate(lista):
                db.add(EquipoImei(
                    imei=imei(base),
                    producto_id=productos[sku].id,
                    proveedor_id=proveedor.id,
                    color=colores[i % len(colores)],
                    almacenamiento_gb=128 if "128" in productos[sku].nombre else 256,
                    precio_costo=productos[sku].precio_costo,
                    estado=EstadoImei.DISPONIBLE,
                ))

        # ---------------- Clientes ----------------
        db.add_all([
            Cliente(tipo_documento=TipoDocumento.CC, numero_documento="1012345678",
                    nombres="Laura", apellidos="Gomez Rivera", telefono="3001234567",
                    email="laura.gomez@example.com", direccion="Calle 45 #12-30", ciudad="Bogota"),
            Cliente(tipo_documento=TipoDocumento.CC, numero_documento="79654321",
                    nombres="Carlos", apellidos="Perez Nino", telefono="3129876543",
                    email="carlos.perez@example.com", direccion="Carrera 7 #98-15", ciudad="Bogota"),
            Cliente(tipo_documento=TipoDocumento.NIT, numero_documento="901456789",
                    nombres="Papeleria La 80", apellidos=None, telefono="6014567890",
                    email="compras@papeleria80.co", direccion="Av 80 #45-10", ciudad="Bogota"),
        ])

        db.commit()
        print("Datos de prueba cargados correctamente.")
        print("  admin  / admin123   (administrador)")
        print("  cajero / cajero123  (cajero)")
        print("  bodega / bodega123  (bodega)")
        print(f"  {sum(len(v) for v in bases.values())} equipos con IMEI disponibles")
    finally:
        db.close()


if __name__ == "__main__":
    sembrar()
