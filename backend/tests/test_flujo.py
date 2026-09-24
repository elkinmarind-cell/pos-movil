"""Prueba de humo de extremo a extremo del POS.

Ejecutar desde la carpeta backend/:   python -m tests.test_flujo
Valida las reglas criticas: login, venta con IMEI, descuento de inventario,
calculo de IVA, bloqueo de IMEI ya vendido, garantia automatica y anulacion.
"""
import os
import sys
import tempfile
from decimal import Decimal

BD = os.path.join(tempfile.mkdtemp(prefix="pos_test_"), "prueba.db")
os.environ["DATABASE_URL"] = f"sqlite:///{BD}"

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.seed import sembrar  # noqa: E402

fallos: list[str] = []


def verificar(condicion: bool, descripcion: str) -> None:
    estado = "PASA" if condicion else "FALLA"
    print(f"  [{estado}] {descripcion}")
    if not condicion:
        fallos.append(descripcion)


def main() -> int:
    sembrar()
    cliente = TestClient(app)

    print("\n1. Autenticacion")
    r = cliente.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    verificar(r.status_code == 200, "login con credenciales validas devuelve 200")
    token = r.json()["access_token"]
    cab = {"Authorization": f"Bearer {token}"}

    r = cliente.post("/api/auth/login", data={"username": "admin", "password": "incorrecta"})
    verificar(r.status_code == 401, "login con clave incorrecta devuelve 401")

    r = cliente.get("/api/productos")
    verificar(r.status_code == 401, "el catalogo exige autenticacion")

    print("\n2. Catalogo e inventario")
    r = cliente.get("/api/productos", headers=cab)
    productos = r.json()
    verificar(len(productos) == 9, f"el catalogo tiene 9 productos (obtenidos: {len(productos)})")

    equipo_prod = next(p for p in productos if p["sku"] == "SM-A155")
    verificar(equipo_prod["disponibles"] == 4, "Galaxy A15 tiene 4 equipos disponibles")

    r = cliente.get("/api/inventario/imei", headers=cab, params={"producto_id": equipo_prod["id"]})
    imeis = [e["imei"] for e in r.json()]
    verificar(len(imeis) == 4, "se listan los 4 IMEI del Galaxy A15")

    accesorio = next(p for p in productos if p["sku"] == "AC-CAR20")
    stock_inicial = accesorio["disponibles"]

    print("\n3. Venta con IMEI + accesorio")
    cuerpo = {
        "cliente_id": 1,
        "metodo_pago": "tarjeta_debito",
        "items": [
            {"producto_id": equipo_prod["id"], "cantidad": 1, "imei": imeis[0]},
            {"producto_id": accesorio["id"], "cantidad": 2, "descuento": "5000"},
        ],
    }
    r = cliente.post("/api/ventas", json=cuerpo, headers=cab)
    verificar(r.status_code == 201, f"la venta se registra (status {r.status_code})")
    venta = r.json()

    # Equipo: 849900 base -> IVA 19% = 161481 -> 1011381
    # Accesorio: 39900*2 = 79800 - 5000 = 74800 -> IVA 14212 -> 89012
    esperado_subtotal = Decimal("849900") + Decimal("74800")
    esperado_iva = Decimal("161481.00") + Decimal("14212.00")
    verificar(Decimal(venta["subtotal"]) == esperado_subtotal, f"subtotal correcto ({venta['subtotal']})")
    verificar(Decimal(venta["iva_total"]) == esperado_iva, f"IVA del 19% correcto ({venta['iva_total']})")
    verificar(
        Decimal(venta["total"]) == esperado_subtotal + esperado_iva,
        f"total = subtotal + IVA ({venta['total']})",
    )
    verificar(venta["numero_factura"].startswith("FV-"), f"consecutivo de factura {venta['numero_factura']}")

    print("\n4. Efecto sobre el inventario")
    r = cliente.get(f"/api/inventario/imei/{imeis[0]}", headers=cab)
    verificar(r.json()["estado"] == "vendido", "el IMEI vendido queda en estado 'vendido'")

    r = cliente.get(f"/api/productos/{equipo_prod['id']}", headers=cab)
    verificar(r.json()["disponibles"] == 3, "quedan 3 Galaxy A15 disponibles")

    r = cliente.get(f"/api/productos/{accesorio['id']}", headers=cab)
    verificar(r.json()["disponibles"] == stock_inicial - 2, "el stock del accesorio bajo en 2 unidades")

    r = cliente.get(f"/api/productos/{equipo_prod['id']}/kardex", headers=cab)
    verificar(any(m["tipo"] == "salida" for m in r.json()), "el kardex registra la salida")

    print("\n5. Reglas de negocio")
    r = cliente.post("/api/ventas", json={
        "cliente_id": 1, "metodo_pago": "efectivo",
        "items": [{"producto_id": equipo_prod["id"], "cantidad": 1, "imei": imeis[0]}],
    }, headers=cab)
    verificar(r.status_code == 409, "no se puede vender dos veces el mismo IMEI")

    r = cliente.post("/api/ventas", json={
        "cliente_id": 1, "metodo_pago": "efectivo",
        "items": [{"producto_id": equipo_prod["id"], "cantidad": 1}],
    }, headers=cab)
    verificar(r.status_code == 400, "un equipo sin IMEI en la linea se rechaza")

    r = cliente.post("/api/ventas", json={
        "cliente_id": 1, "metodo_pago": "efectivo",
        "items": [{"producto_id": accesorio["id"], "cantidad": 99999}],
    }, headers=cab)
    verificar(r.status_code == 409, "no se vende mas stock del disponible")

    r = cliente.post("/api/inventario/imei", json={
        "imei": "123456789012345", "producto_id": equipo_prod["id"],
    }, headers=cab)
    verificar(r.status_code == 422, "un IMEI con digito verificador invalido se rechaza")

    print("\n6. Garantias")
    r = cliente.get("/api/garantias", headers=cab, params={"imei": imeis[0]})
    garantias = r.json()
    verificar(len(garantias) == 1, "la venta genero garantia automatica")
    garantia = garantias[0]
    verificar(garantia["meses"] == 12, "la garantia del equipo es de 12 meses")
    verificar(garantia["estado"] == "vigente", "la garantia nace vigente")

    r = cliente.post(f"/api/garantias/{garantia['id']}/reclamar",
                     json={"descripcion_falla": "No enciende despues de actualizar"}, headers=cab)
    verificar(r.json()["estado"] == "en_reclamacion", "se abre la reclamacion")
    r = cliente.get(f"/api/inventario/imei/{imeis[0]}", headers=cab)
    verificar(r.json()["estado"] == "en_garantia", "el equipo pasa a estado 'en_garantia'")

    r = cliente.post(f"/api/garantias/{garantia['id']}/cerrar",
                     json={"solucion": "Cambio de placa por el fabricante"}, headers=cab)
    verificar(r.json()["estado"] == "atendida", "se cierra la reclamacion")

    print("\n7. Reportes")
    r = cliente.get("/api/reportes/dashboard", headers=cab)
    tablero = r.json()
    verificar(tablero["numero_ventas_hoy"] == 1, "el dashboard cuenta 1 venta hoy")
    verificar(Decimal(tablero["ventas_hoy"]) == Decimal(venta["total"]), "el total del dia coincide")

    r = cliente.get("/api/reportes/mas-vendidos", headers=cab)
    verificar(len(r.json()) == 2, "el reporte de mas vendidos trae 2 productos")

    r = cliente.get("/api/reportes/ventas-por-dia", headers=cab, params={"dias": 7})
    verificar(len(r.json()) == 7, "la serie diaria trae 7 puntos")

    r = cliente.get("/api/reportes/alertas-stock", headers=cab)
    verificar(isinstance(r.json(), list), "el reporte de alertas de stock responde")

    print("\n8. Anulacion de venta")
    r = cliente.post("/api/auth/login", data={"username": "cajero", "password": "cajero123"})
    cab_cajero = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = cliente.post(f"/api/ventas/{venta['id']}/anular", json={"motivo": "Prueba de permisos"},
                     headers=cab_cajero)
    verificar(r.status_code == 403, "un cajero no puede anular ventas")

    r = cliente.post(f"/api/ventas/{venta['id']}/anular",
                     json={"motivo": "Cliente se arrepintio de la compra"}, headers=cab)
    verificar(r.json()["estado"] == "anulada", "el administrador anula la venta")

    r = cliente.get(f"/api/inventario/imei/{imeis[0]}", headers=cab)
    verificar(r.json()["estado"] == "disponible", "la anulacion devuelve el IMEI a disponible")

    r = cliente.get(f"/api/productos/{accesorio['id']}", headers=cab)
    verificar(r.json()["disponibles"] == stock_inicial, "la anulacion repone el stock del accesorio")

    r = cliente.get("/api/garantias", headers=cab, params={"imei": imeis[0]})
    verificar(len(r.json()) == 0, "la anulacion elimina la garantia asociada")

    print("\n" + "=" * 60)
    if fallos:
        print(f"RESULTADO: {len(fallos)} verificacion(es) fallaron")
        for f in fallos:
            print(f"  - {f}")
        return 1
    print("RESULTADO: todas las verificaciones pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(main())
