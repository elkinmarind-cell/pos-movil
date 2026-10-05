// Capa unica de acceso a la API: centraliza el token, los errores y el formato.
const BASE = '/api'
let alCerrarSesion = () => {}
export function registrarCierreSesion(fn) { alCerrarSesion = fn }

function token() {
  try { return localStorage.getItem('pos_token') } catch { return null }
}

async function peticion(ruta, { metodo = 'GET', cuerpo, formulario } = {}) {
  const cabeceras = {}
  const jwt = token()
  if (jwt) cabeceras.Authorization = `Bearer ${jwt}`

  let body
  if (formulario) {
    body = new URLSearchParams(formulario)
    cabeceras['Content-Type'] = 'application/x-www-form-urlencoded'
  } else if (cuerpo !== undefined) {
    body = JSON.stringify(cuerpo)
    cabeceras['Content-Type'] = 'application/json'
  }

  const r = await fetch(`${BASE}${ruta}`, { method: metodo, headers: cabeceras, body })
  if (r.status === 401) { alCerrarSesion(); throw new Error('La sesion expiro. Vuelve a entrar.') }
  if (!r.ok) {
    let detalle = `Error ${r.status}`
    try {
      const d = await r.json()
      if (typeof d.detail === 'string') detalle = d.detail
      else if (Array.isArray(d.detail)) detalle = d.detail.map((x) => `${x.loc?.at(-1) ?? ''}: ${x.msg}`).join(' · ')
    } catch { /* sin cuerpo JSON */ }
    throw new Error(detalle)
  }
  if (r.status === 204) return null
  return r.json()
}

const qs = (p = {}) => {
  const limpio = Object.fromEntries(Object.entries(p).filter(([, v]) => v !== undefined && v !== '' && v !== null))
  const s = new URLSearchParams(limpio).toString()
  return s ? `?${s}` : ''
}

export const api = {
  login: (username, password) => peticion('/auth/login', { metodo: 'POST', formulario: { username, password } }),
  yo: () => peticion('/auth/yo'),
  salud: () => peticion('/salud'),

  roles: () => peticion('/roles'),
  permisos: () => peticion('/permisos'),
  permisosDeRol: (id) => peticion(`/roles/${id}/permisos`),
  guardarPermisosDeRol: (id, permisos) => peticion(`/roles/${id}/permisos`, { metodo: 'PUT', cuerpo: { permisos } }),
  usuarios: () => peticion('/usuarios'),
  crearUsuario: (d) => peticion('/usuarios', { metodo: 'POST', cuerpo: d }),
  actualizarUsuario: (id, d) => peticion(`/usuarios/${id}`, { metodo: 'PUT', cuerpo: d }),
  cambiarClave: (id, password) => peticion(`/usuarios/${id}/clave`, { metodo: 'PUT', cuerpo: { password } }),

  categorias: () => peticion('/categorias'),
  marcas: () => peticion('/marcas'),
  productos: (p) => peticion(`/productos${qs(p)}`),
  producto: (id) => peticion(`/productos/${id}`),
  crearProducto: (d) => peticion('/productos', { metodo: 'POST', cuerpo: d }),
  actualizarProducto: (id, d) => peticion(`/productos/${id}`, { metodo: 'PUT', cuerpo: d }),
  ajustarStock: (id, d) => peticion(`/productos/${id}/ajuste-stock`, { metodo: 'POST', cuerpo: d }),
  kardex: (id) => peticion(`/productos/${id}/kardex`),

  equipos: (p) => peticion(`/inventario/imei${qs(p)}`),
  equipo: (imei) => peticion(`/inventario/imei/${imei}`),
  ingresarEquipo: (d) => peticion('/inventario/imei', { metodo: 'POST', cuerpo: d }),
  cambiarEstadoEquipo: (imei, d) => peticion(`/inventario/imei/${imei}/estado`, { metodo: 'PATCH', cuerpo: d }),

  clientes: (q) => peticion(`/clientes${qs({ q })}`),
  cliente: (id) => peticion(`/clientes/${id}`),
  crearCliente: (d) => peticion('/clientes', { metodo: 'POST', cuerpo: d }),
  actualizarCliente: (id, d) => peticion(`/clientes/${id}`, { metodo: 'PUT', cuerpo: d }),
  comprasCliente: (id) => peticion(`/clientes/${id}/compras`),

  proveedores: () => peticion('/compras/proveedores'),
  ordenesCompra: () => peticion('/compras'),
  ordenCompra: (id) => peticion(`/compras/${id}`),
  crearOrdenCompra: (d) => peticion('/compras', { metodo: 'POST', cuerpo: d }),
  recibirCompra: (id, d) => peticion(`/compras/${id}/recibir`, { metodo: 'POST', cuerpo: d }),

  cajas: () => peticion('/caja/cajas'),
  miTurno: () => peticion('/caja/turno'),
  turnos: () => peticion('/caja/turnos'),
  abrirCaja: (d) => peticion('/caja/abrir', { metodo: 'POST', cuerpo: d }),
  arqueo: () => peticion('/caja/arqueo'),
  cerrarCaja: (d) => peticion('/caja/cerrar', { metodo: 'POST', cuerpo: d }),
  movimientoCaja: (d) => peticion('/caja/movimiento', { metodo: 'POST', cuerpo: d }),

  ventas: (p) => peticion(`/ventas${qs(p)}`),
  venta: (id) => peticion(`/ventas/${id}`),
  crearVenta: (d) => peticion('/ventas', { metodo: 'POST', cuerpo: d }),
  anularVenta: (id, motivo) => peticion(`/ventas/${id}/anular`, { metodo: 'POST', cuerpo: { motivo } }),
  facturaDe: (id) => peticion(`/ventas/${id}/factura`),

  garantias: (p) => peticion(`/garantias${qs(p)}`),
  reclamarGarantia: (id, falla) => peticion(`/garantias/${id}/reclamar`, { metodo: 'POST', cuerpo: { falla } }),
  devoluciones: () => peticion('/devoluciones'),
  crearDevolucion: (d) => peticion('/devoluciones', { metodo: 'POST', cuerpo: d }),
  ordenesServicio: (p) => peticion(`/servicio${qs(p)}`),
  crearOrdenServicio: (d) => peticion('/servicio', { metodo: 'POST', cuerpo: d }),
  actualizarOrdenServicio: (id, d) => peticion(`/servicio/${id}`, { metodo: 'PUT', cuerpo: d }),
  apartados: (p) => peticion(`/apartados${qs(p)}`),
  crearApartado: (d) => peticion('/apartados', { metodo: 'POST', cuerpo: d }),
  abonarApartado: (id, d) => peticion(`/apartados/${id}/abono`, { metodo: 'POST', cuerpo: d }),

  operadores: () => peticion('/telefonia/operadores'),
  planes: () => peticion('/telefonia/planes'),
  activaciones: () => peticion('/telefonia/activaciones'),
  activarLinea: (d) => peticion('/telefonia/activaciones', { metodo: 'POST', cuerpo: d }),

  dispositivos: () => peticion('/iot/dispositivos'),
  eventos: () => peticion('/iot/eventos'),
  alertas: (p) => peticion(`/iot/alertas${qs(p)}`),
  atenderAlerta: (id) => peticion(`/iot/alertas/${id}/atender`, { metodo: 'POST' }),

  dashboard: () => peticion('/reportes/dashboard'),
  ventasPorDia: (dias = 14) => peticion(`/reportes/ventas-por-dia${qs({ dias })}`),
  masVendidos: () => peticion('/reportes/mas-vendidos'),
  rentabilidad: () => peticion('/reportes/rentabilidad'),
  alertasStock: () => peticion('/reportes/alertas-stock'),
  trazabilidad: (imei) => peticion(`/reportes/trazabilidad/${imei}`),
}

// ------------------------------------------------------------------ formato
export const pesos = (v) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 })
    .format(Number(v || 0))

export const numero = (v) => new Intl.NumberFormat('es-CO').format(Number(v || 0))

export const fecha = (v) =>
  v ? new Date(v).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' }) : '—'

export const fechaHora = (v) =>
  v ? new Date(v).toLocaleString('es-CO', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'

export const legible = (v) => (v ? String(v).replaceAll('_', ' ').toLowerCase() : '')
