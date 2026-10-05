"""Prueba de extremo a extremo del backend contra PostgreSQL real.

Recorre el sistema como lo haria un dia de trabajo: abrir caja, vender, apartar,
devolver, reclamar garantia, reparar, comprar, administrar usuarios y cerrar caja.
Ejecutar con la base recien cargada:  python -m tests.test_api
"""
import sys
from decimal import Decimal

from fastapi.testclient import TestClient

from app.main import app

fallos: list[str] = []
cliente = TestClient(app)


def check(condicion: bool, descripcion: str) -> bool:
    print(f"  [{'PASA' if condicion else 'FALLA'}] {descripcion}")
    if not condicion:
        fallos.append(descripcion)
    return condicion


def login(usuario: str, clave: str) -> dict:
    r = cliente.post("/api/auth/login", data={"username": usuario, "password": clave})
    assert r.status_code == 200, f"login {usuario}: {r.status_code} {r.text[:200]}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def main() -> int:
    print("\n1. Autenticacion y permisos")
    r = cliente.post("/api/auth/login", data={"username": "admin", "password": "admin123"})
    check(r.status_code == 200, "el administrador inicia sesion")
    datos = r.json()
    check(len(datos["permisos"]) == 28, f"el administrador tiene todos los permisos ({len(datos['permisos'])})")
    admin = {"Authorization": f"Bearer {datos['access_token']}"}
    cajero = login("cajero", "cajero123")
    bodega = login("bodega", "bodega123")
    tecnico = login("tecnico", "tecnico123")

    check(cliente.post("/api/auth/login", data={"username": "admin", "password": "mala"}).status_code == 401,
          "rechaza la contrasena incorrecta")
    check(cliente.get("/api/productos").status_code == 401, "el catalogo exige sesion")
    check(len(cliente.post("/api/auth/login", data={"username": "cajero", "password": "cajero123"}).json()["permisos"]) == 11,
          "el cajero tiene solo sus 11 permisos")
    check(cliente.get("/api/usuarios", headers=cajero).status_code == 403,
          "el cajero no puede ver la lista de usuarios")
    check(cliente.get("/api/usuarios", headers=admin).status_code == 200,
          "el administrador si puede")

    print("\n2. Catalogo e inventario")
    productos = cliente.get("/api/productos", headers=cajero).json()
    check(len(productos) == 12, f"el catalogo trae 12 productos ({len(productos)})")
    galaxy = next(p for p in productos if p["sku"] == "SM-A155")
    check(galaxy["disponibles"] == 3, f"quedan 3 Galaxy A15 ({galaxy['disponibles']})")
    cargador = next(p for p in productos if p["sku"] == "AC-CAR20")
    stock_cargador = cargador["disponibles"]

    imeis = cliente.get("/api/inventario/imei", headers=cajero,
                        params={"producto_id": galaxy["id"], "estado": "DISPONIBLE"}).json()
    check(len(imeis) == 3, "se listan los 3 IMEI disponibles del Galaxy")
    imei_a_vender = imeis[0]["imei"]

    r = cliente.post("/api/inventario/imei", headers=bodega,
                     json={"producto_id": galaxy["id"], "imei": "123456789012345", "costo": 100})
    check(r.status_code == 422, "rechaza un IMEI con digito verificador invalido")

    print("\n3. Caja")
    r = cliente.post("/api/ventas", headers=admin, json={"items": [{"producto_id": cargador["id"]}],
                                                         "pagos": [{"metodo": "EFECTIVO", "valor": "47481"}]})
    check(r.status_code == 409 and "caja" in r.json()["detail"].lower(),
          "no se puede vender sin abrir caja")
    r = cliente.post("/api/caja/abrir", headers=admin, json={"caja_id": 2, "base_inicial": "150000"})
    check(r.status_code == 201, "el administrador abre la caja 2")
    r = cliente.post("/api/caja/abrir", headers=admin, json={"caja_id": 2, "base_inicial": "100000"})
    check(r.status_code == 409, "no se puede abrir dos turnos con el mismo usuario")

    print("\n4. Venta con IMEI, accesorio y pago mixto")
    cuerpo = {
        "cliente_id": 1,
        "items": [{"producto_id": galaxy["id"], "imei": imei_a_vender},
                  {"producto_id": cargador["id"], "cantidad": 2, "descuento": "5000"}],
        "pagos": [{"metodo": "EFECTIVO", "valor": "500000"},
                  {"metodo": "DEBITO", "valor": "600393", "referencia": "VOUCHER-991"}],
    }
    r = cliente.post("/api/ventas", headers=cajero, json=cuerpo)
    check(r.status_code == 201, f"la venta se registra ({r.status_code} {r.text[:120] if r.status_code != 201 else ''})")
    if r.status_code != 201:
        return 1
    venta = r.json()
    esperado_sub = Decimal("849900") + Decimal("74800")
    esperado_iva = Decimal("161481.00") + Decimal("14212.00")
    check(Decimal(venta["subtotal"]) == esperado_sub, f"subtotal correcto ({venta['subtotal']})")
    check(Decimal(venta["iva_total"]) == esperado_iva, f"IVA del 19% correcto ({venta['iva_total']})")
    check(Decimal(venta["total"]) == esperado_sub + esperado_iva, f"total correcto ({venta['total']})")
    check(venta["numero"].startswith("FV"), f"consecutivo DIAN {venta['numero']}")
    check(len(venta["pagos"]) == 2, "quedaron los dos pagos registrados")

    r = cliente.post("/api/ventas", headers=cajero,
                     json={"items": [{"producto_id": cargador["id"]}], "pagos": [{"metodo": "EFECTIVO", "valor": "1000"}]})
    check(r.status_code == 400, "rechaza una venta cuyos pagos no cuadran con el total")

    print("\n5. Efecto en inventario (lo hacen los triggers)")
    check(cliente.get(f"/api/inventario/imei/{imei_a_vender}", headers=cajero).json()["estado"] == "VENDIDO",
          "el IMEI vendido quedo VENDIDO")
    check(cliente.get(f"/api/productos/{galaxy['id']}", headers=cajero).json()["disponibles"] == 2,
          "quedan 2 Galaxy disponibles")
    check(cliente.get(f"/api/productos/{cargador['id']}", headers=cajero).json()["disponibles"] == stock_cargador - 2,
          "el stock del cargador bajo en 2")
    kardex = cliente.get(f"/api/productos/{galaxy['id']}/kardex", headers=cajero).json()
    check(any(m["tipo"] == "SALIDA" and m["referencia"] == venta["numero"] for m in kardex),
          "el kardex registro la salida con el numero de factura")
    f = cliente.get(f"/api/ventas/{venta['id']}/factura", headers=cajero).json()
    check(len(f["cufe"]) == 96 and f["estado_dian"] == "PENDIENTE", "se genero la factura electronica con CUFE")

    print("\n6. Reglas que deben fallar")
    for descripcion, cuerpo_malo, esperado in [
        ("no se vende dos veces el mismo IMEI",
         {"items": [{"producto_id": galaxy["id"], "imei": imei_a_vender}], "pagos": [{"metodo": "EFECTIVO", "valor": "1011381"}]}, 409),
        ("un equipo sin IMEI en la linea se rechaza",
         {"items": [{"producto_id": galaxy["id"]}], "pagos": [{"metodo": "EFECTIVO", "valor": "1011381"}]}, 400),
        ("no se vende mas stock del disponible",
         {"items": [{"producto_id": cargador["id"], "cantidad": 99999}], "pagos": [{"metodo": "EFECTIVO", "valor": "1"}]}, 409),
    ]:
        check(cliente.post("/api/ventas", headers=cajero, json=cuerpo_malo).status_code == esperado, descripcion)

    print("\n7. Apartados")
    iphone = next(p for p in productos if p["sku"] == "AP-IP13")
    libres = cliente.get("/api/inventario/imei", headers=cajero,
                         params={"producto_id": iphone["id"], "estado": "DISPONIBLE"}).json()
    r = cliente.post("/api/apartados", headers=cajero,
                     json={"cliente_id": 2, "imei": libres[0]["imei"], "dias_plazo": 15,
                           "abono_inicial": "1000000", "metodo": "EFECTIVO"})
    check(r.status_code == 201, f"se aparta un equipo con abono inicial ({r.status_code})")
    apartado = r.json()
    check(Decimal(apartado["saldo_pendiente"]) == Decimal(apartado["valor_total"]) - 1000000,
          "el abono inicial bajo el saldo")
    check(cliente.get(f"/api/inventario/imei/{libres[0]['imei']}", headers=cajero).json()["estado"] == "APARTADO",
          "el equipo apartado quedo reservado")
    r = cliente.post(f"/api/apartados/{apartado['id']}/abono", headers=cajero,
                     json={"valor": "100000", "metodo": "NEQUI"})
    check(Decimal(r.json()["saldo_pendiente"]) == Decimal(apartado["saldo_pendiente"]) - 100000,
          "el segundo abono tambien descuenta")
    check(cliente.post(f"/api/apartados/{apartado['id']}/abono", headers=cajero,
                       json={"valor": "99999999"}).status_code == 400, "un abono no puede superar el saldo")

    print("\n8. Garantias y servicio tecnico")
    garantias = cliente.get("/api/garantias", headers=cajero, params={"estado": "VIGENTE"}).json()
    check(len(garantias) >= 6, f"hay garantias vigentes ({len(garantias)})")
    g = next(g for g in garantias if g["dias_restantes"] > 300)
    r = cliente.post(f"/api/garantias/{g['id']}/reclamar", headers=cajero,
                     json={"falla": "No enciende despues de la actualizacion"})
    check(r.status_code == 201, f"la reclamacion abre una orden de servicio ({r.status_code})")
    orden = r.json()
    check(orden["numero"].startswith("OS-"), f"numero de orden {orden.get('numero')}")
    r = cliente.put(f"/api/servicio/{orden['id']}", headers=tecnico,
                    json={"estado": "REPARACION", "diagnostico": "Se reinstala el firmware"})
    check(r.status_code == 200 and r.json()["estado"] == "REPARACION", "el tecnico diagnostica")
    r = cliente.put(f"/api/servicio/{orden['id']}", headers=tecnico, json={"estado": "ENTREGADO"})
    check(r.json()["fecha_entrega"] is not None, "al entregar se registra la fecha")
    check(cliente.get("/api/garantias", headers=cajero, params={"estado": "ATENDIDA"}).json(),
          "la garantia quedo atendida")

    print("\n9. Devolucion con nota credito")
    detalle_accesorio = next(d for d in venta["detalles"] if d["equipo_imei_id"] is None)
    r = cliente.post("/api/devoluciones", headers=cajero,
                     json={"venta_id": venta["id"], "motivo": "El cliente se arrepintio del cargador",
                           "tipo_reembolso": "NOTA_CREDITO",
                           "items": [{"venta_detalle_id": detalle_accesorio["id"], "cantidad": 1}]})
    check(r.status_code == 201, f"se registra la devolucion ({r.status_code} {r.text[:100] if r.status_code != 201 else ''})")
    check(cliente.get(f"/api/productos/{cargador['id']}", headers=cajero).json()["disponibles"] == stock_cargador - 1,
          "la devolucion reingreso una unidad al inventario")

    print("\n10. Compras y recepcion")
    r = cliente.post("/api/compras", headers=bodega,
                     json={"proveedor_id": 1, "items": [{"producto_id": galaxy["id"], "cantidad": 2,
                                                         "costo_unitario": "620000"}]})
    check(r.status_code == 201, f"bodega crea la orden de compra ({r.status_code})")
    orden_compra = r.json()
    check(cliente.post("/api/compras", headers=cajero, json={"proveedor_id": 1, "items": []}).status_code in (403, 422),
          "el cajero no puede crear ordenes de compra")
    nuevos = ["356789012345052", "356789012345060"]
    r = cliente.post(f"/api/compras/{orden_compra['id']}/recibir", headers=bodega,
                     json={"items": [{"detalle_id": orden_compra["detalles"][0]["id"], "cantidad": 2,
                                      "imeis": nuevos}]})
    check(r.status_code == 200 and r.json()["estado"] == "RECIBIDA", f"se recibe la mercancia ({r.status_code})")
    check(cliente.get(f"/api/productos/{galaxy['id']}", headers=cajero).json()["disponibles"] == 4,
          "los 2 equipos nuevos entraron al inventario")

    print("\n11. Administracion de usuarios")
    r = cliente.post("/api/usuarios", headers=admin,
                     json={"rol_id": 2, "username": "vendedor2", "nombre_completo": "Maria Fernanda Lopez",
                           "email": "maria@posmovil.co", "password": "vendedor123"})
    check(r.status_code == 201, f"el administrador crea un usuario ({r.status_code})")
    nuevo = r.json()
    check(login("vendedor2", "vendedor123") is not None, "el usuario nuevo puede iniciar sesion")
    r = cliente.put(f"/api/usuarios/{nuevo['id']}", headers=admin, json={"activo": False})
    check(r.status_code == 200, "se desactiva el usuario")
    check(cliente.post("/api/auth/login", data={"username": "vendedor2", "password": "vendedor123"}).status_code == 403,
          "un usuario inactivo no puede entrar")
    check(cliente.put(f"/api/usuarios/1", headers=admin, json={"activo": False}).status_code == 400,
          "nadie puede desactivarse a si mismo")
    permisos_cajero = cliente.get("/api/roles/2/permisos", headers=admin).json()
    check(isinstance(permisos_cajero, list) and permisos_cajero, "se consultan los permisos del rol cajero")

    print("\n12. Telefonia")
    r = cliente.post("/api/telefonia/activaciones", headers=cajero,
                     json={"plan_id": 1, "cliente_id": 1, "numero_linea": "3012223344",
                           "iccid_sim": "8957010000000009999", "tipo": "NUEVA"})
    check(r.status_code == 201, f"se activa una linea ({r.status_code})")
    check(cliente.post("/api/telefonia/activaciones", headers=cajero,
                       json={"plan_id": 1, "cliente_id": 1, "numero_linea": "3012223345",
                             "iccid_sim": "8957010000000009999"}).status_code == 409,
          "no se activa dos veces la misma SIM")

    print("\n13. IoT")
    check(len(cliente.get("/api/iot/dispositivos", headers=admin).json()) == 5, "hay 5 dispositivos IoT")
    alertas = cliente.get("/api/iot/alertas", headers=admin, params={"sin_atender": True}).json()
    check(len(alertas) >= 1, f"hay alertas sin atender ({len(alertas)})")
    r = cliente.post(f"/api/iot/alertas/{alertas[0]['id']}/atender", headers=admin)
    check(r.status_code == 200 and r.json()["fecha_atencion"], "se atiende una alerta")

    print("\n14. Reportes")
    d = cliente.get("/api/reportes/dashboard", headers=admin).json()
    check(d["numero_ventas_hoy"] >= 1, f"el dashboard cuenta las ventas de hoy ({d['numero_ventas_hoy']})")
    check(d["turno_abierto"] is True, "detecta que el administrador tiene caja abierta")
    check(d["apartados_vigentes"] == 2, f"cuenta los apartados vigentes ({d['apartados_vigentes']})")
    check(len(cliente.get("/api/reportes/ventas-por-dia", headers=admin, params={"dias": 7}).json()) == 7,
          "la serie diaria trae 7 puntos")
    check(len(cliente.get("/api/reportes/mas-vendidos", headers=admin).json()) >= 3, "hay productos mas vendidos")
    check(isinstance(cliente.get("/api/reportes/rentabilidad", headers=admin).json(), list), "responde la rentabilidad")
    t = cliente.get(f"/api/reportes/trazabilidad/{imei_a_vender}", headers=admin).json()
    check(t["factura"] == venta["numero"], "la trazabilidad enlaza el IMEI con su factura")
    check(cliente.get("/api/reportes/dashboard", headers=cajero).status_code == 403,
          "el cajero no tiene permiso de reportes")

    print("\n15. Anulacion y cierre de caja")
    check(cliente.post(f"/api/ventas/{venta['id']}/anular", headers=cajero,
                       json={"motivo": "Prueba de permisos"}).status_code == 403,
          "el cajero no puede anular ventas")
    r = cliente.post(f"/api/ventas/{venta['id']}/anular", headers=admin,
                     json={"motivo": "Cliente se arrepintio de toda la compra"})
    check(r.status_code == 200 and r.json()["estado"] == "ANULADA", f"el administrador anula ({r.status_code})")
    check(cliente.get(f"/api/inventario/imei/{imei_a_vender}", headers=admin).json()["estado"] == "DISPONIBLE",
          "la anulacion devolvio el IMEI a disponible")

    arqueo = cliente.get("/api/caja/arqueo", headers=admin).json()
    check(Decimal(arqueo["efectivo_esperado"]) == Decimal("150000"), f"el arqueo calcula el esperado ({arqueo['efectivo_esperado']})")
    cliente.post("/api/caja/movimiento", headers=admin,
                 json={"tipo": "EGRESO", "concepto": "Compra de bolsas", "valor": "20000"})
    arqueo = cliente.get("/api/caja/arqueo", headers=admin).json()
    check(Decimal(arqueo["efectivo_esperado"]) == Decimal("130000"), "el egreso baja el efectivo esperado")
    r = cliente.post("/api/caja/cerrar", headers=admin, json={"efectivo_contado": "125000"})
    check(r.status_code == 200 and Decimal(r.json()["diferencia"]) == Decimal("-5000"),
          f"el cierre calcula el faltante ({r.json().get('diferencia')})")

    print("\n" + "=" * 62)
    if fallos:
        print(f"RESULTADO: {len(fallos)} verificacion(es) fallaron")
        for f in fallos:
            print("  -", f)
        return 1
    print("RESULTADO: todas las verificaciones pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(main())
