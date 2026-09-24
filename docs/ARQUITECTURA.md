# Arquitectura del Sistema POS para Dispositivos Moviles

Documento de soporte del primer avance funcional.

---

## 1. Vista general

```
┌────────────────────────┐     HTTP/JSON      ┌───────────────────────┐
│  Frontend  React 18    │ ─────────────────▶ │  Backend  FastAPI     │
│  Vite · PWA · Router   │ ◀───────────────── │  Pydantic · SQLAlchemy│
│  localhost:5173        │   JWT Bearer       │  localhost:8000       │
└────────────────────────┘                    └───────────┬───────────┘
                                                          │ SQL
                                              ┌───────────▼───────────┐
                                              │  PostgreSQL 14+       │
                                              │  (SQLite en la demo)  │
                                              └───────────────────────┘
```

Arquitectura en tres capas con separacion estricta de responsabilidades:

| Capa | Responsabilidad | Archivos |
|---|---|---|
| Presentacion | Interfaz, estado de la UI, formato local (es-CO, COP) | `frontend/src/` |
| Aplicacion | Rutas HTTP, autenticacion, autorizacion, validacion | `backend/app/routers/`, `deps.py`, `schemas.py` |
| Dominio | Reglas de negocio independientes del transporte | `backend/app/services.py` |
| Persistencia | Modelo relacional, restricciones, integridad | `backend/app/models.py`, `database/*.sql` |

La regla que sostiene el diseno: **`services.py` no importa nada de FastAPI salvo las
excepciones HTTP**, por lo que las reglas de negocio se prueban sin levantar el servidor.

---

## 2. Modelo de datos

11 tablas. Relaciones principales:

```
usuarios ──< ventas >── clientes
                │
                └──< venta_detalles >── productos ──< equipos_imei
                          │                              │
                          └──< garantias ────────────────┘

productos ──< movimientos_inventario >── usuarios   (kardex)
marcas, categorias, proveedores  ──<  productos / equipos_imei
```

### Decision central: dos estrategias de inventario

| | Equipos (smartphones) | Accesorios |
|---|---|---|
| Se identifican por | IMEI unico por unidad | SKU del modelo |
| Donde vive la existencia | Una fila en `equipos_imei` por unidad | `productos.stock_actual` |
| Al vender | La fila cambia a estado `VENDIDO` | Se resta la cantidad |
| Garantia | Ligada al IMEI concreto | Ligada a la linea de factura |
| Restriccion | `requiere_imei = TRUE` fuerza `stock_actual = 0` | — |

La vista `v_inventario_disponible` y el campo calculado `disponibles` presentan ambos
mundos con la misma forma hacia afuera, de modo que la interfaz no necesita distinguirlos
para mostrar existencias.

### Estados del equipo

```
DISPONIBLE ──venta──▶ VENDIDO ──reclamacion──▶ EN_GARANTIA ──cierre──▶ VENDIDO
     ▲                    │
     └───anulacion────────┘
```

`RESERVADO`, `DEVUELTO` y `DADO_DE_BAJA` quedan definidos para el siguiente avance
(apartados y bajas por dano).

---

## 3. Reglas de negocio implementadas

| # | Regla | Donde se aplica |
|---|---|---|
| RN-01 | Un IMEI no puede venderse dos veces | `services.procesar_venta` + trigger `tr_venta_detalle_imei` |
| RN-02 | Un equipo serializado exige IMEI en la linea de venta | `services.procesar_venta` |
| RN-03 | Un equipo serializado se vende de a una unidad por linea | `CHECK ck_detalle_serializado` |
| RN-04 | No se vende mas stock del disponible | `services.procesar_venta` + trigger `tr_venta_detalle_stock` |
| RN-05 | El descuento no puede superar el valor de la linea | `services.procesar_venta` |
| RN-06 | El IMEI debe tener 15 digitos y verificador Luhn valido | `schemas.EquipoImeiCreate` + `fn_imei_valido` |
| RN-07 | Toda venta genera garantia segun los meses del producto | `services.procesar_venta` |
| RN-08 | Anular revierte inventario, kardex y garantia | `services.anular_venta` |
| RN-09 | Solo el rol `admin` anula ventas | `deps.requiere_roles` |
| RN-10 | Toda alteracion de existencias queda en el kardex | `services.registrar_movimiento` |
| RN-11 | Las garantias vencidas se marcan automaticamente | `services.actualizar_garantias_vencidas` |
| RN-12 | El consecutivo de factura no se repite | `siguiente_numero_factura` + `UNIQUE` |

---

## 4. Calculo de impuestos

Por cada linea de la factura:

```
bruto          = precio_unitario × cantidad
base_gravable  = bruto − descuento
iva_valor      = base_gravable × (iva_porcentaje / 100)
total_linea    = base_gravable + iva_valor
```

Y en la cabecera: `total = Σ base_gravable + Σ iva_valor`.

Todo con `Decimal` y redondeo `ROUND_HALF_UP` a dos decimales en una unica funcion
(`services.dinero`). El IVA es un atributo del producto, no una constante, porque en
Colombia no todos los bienes estan gravados a la misma tarifa.

---

## 5. Seguridad

- **Contrasenas:** PBKDF2-HMAC-SHA256, 260.000 iteraciones, salt aleatorio de 16 bytes por
  usuario. La base nunca guarda la contrasena.
- **Sesiones:** JWT firmado HS256, vigencia de 8 horas, verificado en cada peticion.
- **Autorizacion:** tres roles con permisos distintos, aplicados con dependencias de FastAPI.
- **Validacion de entrada:** Pydantic rechaza el dato malformado antes de que llegue al dominio.
- **Integridad en el motor:** claves foraneas, `UNIQUE` y `CHECK`; la base no depende de que
  la aplicacion se porte bien.
- **Trazabilidad:** el kardex registra quien movio que, cuando y con que referencia.

---

## 6. Catalogo de endpoints

`GET /api/salud` — estado del servicio (publico).

### Autenticacion — `/api/auth`
| Metodo | Ruta | Rol |
|---|---|---|
| POST | `/login` | publico |
| GET | `/yo` | autenticado |
| POST | `/usuarios` | admin |
| GET | `/usuarios` | admin |

### Productos — `/api/productos`
| Metodo | Ruta | Rol |
|---|---|---|
| GET | `` (filtros: `q`, `categoria_id`, `solo_disponibles`) | autenticado |
| GET | `/categorias`, `/marcas` | autenticado |
| POST | `` | admin, bodega |
| GET | `/{id}` | autenticado |
| PUT | `/{id}` | admin, bodega |
| POST | `/{id}/ajuste-stock` | admin, bodega |
| GET | `/{id}/kardex` | autenticado |

### Inventario / IMEI — `/api/inventario`
| Metodo | Ruta | Rol |
|---|---|---|
| GET | `/imei` (filtros: `producto_id`, `estado`, `q`) | autenticado |
| GET | `/imei/{imei}` | autenticado |
| POST | `/imei` | admin, bodega |
| POST | `/imei/lote` | admin, bodega |
| PATCH | `/imei/{imei}/estado` | admin, bodega |

### Clientes — `/api/clientes`
| Metodo | Ruta | Rol |
|---|---|---|
| GET | `` (filtro `q`), POST `` | autenticado |
| GET | `/{id}`, PUT `/{id}` | autenticado |
| GET | `/{id}/compras` | autenticado |

### Ventas — `/api/ventas`
| Metodo | Ruta | Rol |
|---|---|---|
| POST | `` | autenticado |
| GET | `` (filtros: `desde`, `hasta`, `estado`, `cliente_id`) | autenticado |
| GET | `/{id}` | autenticado |
| POST | `/{id}/anular` | admin |

### Garantias — `/api/garantias`
| Metodo | Ruta | Rol |
|---|---|---|
| GET | `` (filtros: `estado`, `cliente_id`, `imei`) | autenticado |
| POST | `/{id}/reclamar` | autenticado |
| POST | `/{id}/cerrar` | autenticado |

### Reportes — `/api/reportes`
| Metodo | Ruta | Rol |
|---|---|---|
| GET | `/dashboard` | autenticado |
| GET | `/ventas-por-dia?dias=N` | autenticado |
| GET | `/mas-vendidos?limite=N&dias=N` | autenticado |
| GET | `/alertas-stock` | autenticado |

Total: 34 operaciones. La especificacion OpenAPI completa se genera sola en `/docs`.

---

## 7. Objetos de base de datos (script 03)

| Tipo | Nombre | Proposito |
|---|---|---|
| Vista | `v_inventario_disponible` | Existencias unificadas con margen por producto |
| Vista | `v_alertas_stock` | Productos en o bajo el minimo |
| Vista | `v_ventas_diarias` | Consolidado diario con ticket promedio |
| Vista | `v_rentabilidad_producto` | Utilidad bruta por producto |
| Vista | `v_trazabilidad_imei` | Historia completa de un equipo: ingreso, venta, cliente, garantia |
| Funcion | `fn_imei_valido` | Validacion Luhn en PL/pgSQL, usada como `CHECK` |
| Trigger | `tr_venta_detalle_imei` | Impide vender un equipo no disponible |
| Trigger | `tr_venta_detalle_stock` | Descuenta stock y escribe en el kardex |
| Procedimiento | `sp_actualizar_garantias_vencidas` | Marca garantias vencidas (job diario) |

---

## 8. Marco normativo colombiano considerado

- **Ley 1480 de 2011 (Estatuto del Consumidor):** la garantia legal debe quedar registrada y
  ser consultable por el comprador. Lo cubre la tabla `garantias` y el flujo de reclamacion.
- **Registro de IMEI (CRC):** la comercializacion de equipos exige trazabilidad del IMEI.
  Lo cubre `equipos_imei` y la vista de trazabilidad.
- **Facturacion electronica (DIAN):** este avance genera el consecutivo interno; la
  integracion con un proveedor tecnologico queda para el siguiente entregable.
- **Ley 1581 de 2012 (proteccion de datos):** los datos de clientes se limitan a los
  necesarios para la venta y la garantia.
