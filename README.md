# Sistema POS para la Gestion y Venta de Dispositivos Moviles

Primer avance funcional del proyecto integrador.
Prototipo ejecutable con backend, base de datos y interfaz web.

**Equipo:** Elkin Santiago Marin Duarte, Juan David Zabala Plata
**Stack:** React 18 (Vite, PWA) · FastAPI + SQLAlchemy 2 · PostgreSQL (SQLite para la demo)

---

## 1. Que incluye este avance

| Modulo | Estado | Que resuelve |
|---|---|---|
| Autenticacion y roles | Funcional | JWT con roles `admin`, `cajero`, `bodega`. Contrasenas con hash PBKDF2-SHA256 |
| Caja / Venta (POS) | Funcional | Carrito, descuentos por linea, IVA 19%, 6 metodos de pago, consecutivo de factura, anulacion con reversa |
| Inventario con IMEI | Funcional | Control unidad por unidad, validacion Luhn del IMEI, kardex de movimientos, stock agregado para accesorios |
| Clientes | Funcional | CC/CE/TI/NIT/Pasaporte, busqueda e historial de compras |
| Garantias | Funcional | Se generan automaticamente al vender, flujo de reclamacion y cierre, vencimiento automatico |
| Reportes y dashboard | Funcional | Ventas del dia/mes, ticket promedio, serie de 14 dias, mas vendidos, alertas de stock |

**Verificado:** 33 de 33 pruebas automaticas de extremo a extremo pasan (`backend/tests/test_flujo.py`).

---

## 2. Estructura del proyecto

```
pos-movil/
├── backend/                 API REST en FastAPI
│   ├── app/
│   │   ├── main.py          Arranque, CORS, registro de routers
│   │   ├── config.py        Configuracion por variables de entorno
│   │   ├── database.py      Motor y sesiones SQLAlchemy
│   │   ├── models.py        11 tablas del modelo relacional
│   │   ├── schemas.py       Validacion de entrada/salida (Pydantic v2)
│   │   ├── security.py      Hash de contrasenas y JWT
│   │   ├── deps.py          Dependencias: sesion, usuario actual, roles
│   │   ├── services.py      Reglas de negocio (venta, anulacion, garantias)
│   │   ├── seed.py          Datos de prueba
│   │   └── routers/         auth, productos, inventario, clientes, ventas, garantias, reportes
│   └── tests/test_flujo.py  Prueba de humo de extremo a extremo
├── database/                Scripts SQL para PostgreSQL
│   ├── 01_schema_postgres.sql
│   ├── 02_datos_prueba.sql
│   └── 03_vistas_funciones_triggers.sql
├── frontend/                Aplicacion React (PWA)
│   └── src/pages/           Login, Dashboard, Caja, Ventas, Inventario, Clientes, Garantias
└── docs/ARQUITECTURA.md     Decisiones de diseno y catalogo de endpoints
```

---

## 3. Como ejecutarlo

### Requisitos
Python 3.10 o superior y Node.js 18 o superior.

`requirements.txt` usa rangos minimos (`>=`) y no versiones exactas, a proposito: las
versiones exactas no siempre tienen compilacion disponible para las versiones mas nuevas
de Python (por ejemplo 3.14), y la instalacion falla. Con rangos, pip elige la que
corresponda a tu interprete.

### Desde Visual Studio Code (recomendado)

El proyecto trae la carpeta `.vscode` configurada. Abre **la carpeta `pos-movil` completa**
en VS Code (Archivo > Abrir carpeta), no una subcarpeta.

0. Si algo falla, empieza por `Ctrl+Shift+P` > `Tasks: Run Task` > **0 - Diagnostico**,
   que te dice si faltan Python, Node, el entorno virtual o `node_modules`.
1. `Ctrl+Shift+P` > `Tasks: Run Task` > **INSTALACION COMPLETA (primera vez)**
   Crea el entorno virtual, instala dependencias de Python y de Node, y carga los datos de prueba.
   Solo se hace una vez.
2. `Ctrl+Shift+P` > `Tasks: Run Task` > **INICIAR TODO (API + interfaz)**
   Levanta el backend y el frontend en dos terminales. Atajo: `Ctrl+Shift+B`.
3. Abre `http://localhost:5173`.

Otras tareas disponibles: iniciar solo el backend, solo el frontend, o correr las pruebas
(`Ctrl+Shift+P` > `Tasks: Run Test Task`).

Para depurar con puntos de interrupcion, ve a la pestana **Ejecutar y depurar** (`Ctrl+Shift+D`)
y elige **API FastAPI (con depurador)**.

El archivo `.vscode/api.http` permite probar los endpoints sin salir del editor
(requiere la extension REST Client, que VS Code te ofrecera instalar al abrir el proyecto).

### Desde la terminal

#### Backend

```bash
cd pos-movil/backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux / macOS

pip install -r requirements.txt
python -m app.seed              # crea las tablas y carga datos de prueba
python -m uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`.
Documentacion interactiva (Swagger): `http://127.0.0.1:8000/docs`.

#### Frontend

En otra terminal:

```bash
cd pos-movil/frontend
npm install
npm run dev
```

Abre `http://localhost:5173`. Vite redirige `/api` al backend automaticamente.

### Usuarios de prueba

| Usuario | Contrasena | Rol | Puede |
|---|---|---|---|
| `admin` | `admin123` | Administrador | Todo, incluida la anulacion de ventas |
| `cajero` | `cajero123` | Cajero | Vender y consultar |
| `bodega` | `bodega123` | Bodega | Ingresar equipos y ajustar stock |

---

## 4. Usar PostgreSQL en lugar de SQLite

SQLite viene por defecto para que el prototipo arranque sin instalar nada.
Para la entrega del componente de bases de datos:

El conector de PostgreSQL se instala aparte, porque el prototipo no lo necesita para
funcionar con SQLite:

```bash
pip install -r backend/requirements-postgres.txt
```

```bash
createdb pos_movil
psql -d pos_movil -f database/01_schema_postgres.sql
psql -d pos_movil -f database/03_vistas_funciones_triggers.sql
```

Luego, en `backend/.env` (copia de `.env.example`):

```
DATABASE_URL=postgresql+psycopg://postgres:TU_CLAVE@localhost:5432/pos_movil
```

> Los triggers del script 03 replican la logica que el backend ya aplica.
> Si va a correr la API sobre PostgreSQL, deshabilitelos (el propio script explica como)
> para no descontar el inventario dos veces.

---

## 5. Decisiones de diseno relevantes

**Dos formas de controlar existencias.** Un celular no es intercambiable con otro del mismo
modelo: tiene IMEI, garantia y trazabilidad propias. Por eso los equipos viven en
`equipos_imei` (una fila por unidad fisica, con estado) y los accesorios usan `stock_actual`
en `productos`. La vista `v_inventario_disponible` y el campo calculado `disponibles` unifican
ambos conteos para quien consulta.

**Validacion Luhn del IMEI.** Un IMEI valido tiene 15 digitos y un digito verificador
calculado con el algoritmo de Luhn. Se valida en tres capas: Pydantic (API), `CHECK` con
`fn_imei_valido` (PostgreSQL) y el formulario (interfaz).

**La venta es una transaccion atomica.** `services.procesar_venta` valida stock, IMEI,
descuentos e impuestos antes de tocar nada; si una linea falla, no se vende ninguna.
La anulacion es la reversa completa: devuelve el IMEI a `disponible`, repone stock, borra
la garantia y deja rastro en el kardex.

**Dinero con `Decimal`, nunca `float`.** Toda cifra monetaria usa `Decimal` y se redondea
con `ROUND_HALF_UP` a dos decimales en un unico punto (`services.dinero`), de modo que
subtotal, IVA y total siempre cuadran.

**Kardex append-only.** `movimientos_inventario` nunca se actualiza ni se borra: cada entrada,
salida, ajuste y devolucion queda registrada con usuario, fecha y referencia de factura.

---

## 6. Pruebas

```bash
cd pos-movil/backend
python -m tests.test_flujo
```

Cubre login y control de acceso, venta mixta (equipo + accesorio), calculo de IVA,
efecto sobre el inventario y el kardex, las reglas que deben fallar (IMEI repetido,
equipo sin IMEI, stock insuficiente, IMEI con verificador invalido), el ciclo completo
de garantia y la anulacion con reversa.

---

## 7. Pendiente para el siguiente avance

- Cierre de caja y arqueo por turno
- Impresion de factura en formato POS de 58/80 mm
- Facturacion electronica DIAN (proveedor tecnologico)
- Componente IoT: lector de codigo de barras / QR para el IMEI
- Reporte de reabastecimiento sugerido segun rotacion
- Despliegue y manual de usuario
