// Capa unica de acceso a la API. Centraliza el token y el manejo de errores.
const BASE = '/api'

let alCerrarSesion = () => {}
export function registrarCierreSesion(fn) { alCerrarSesion = fn }

function token() {
  return localStorage.getItem('pos_token')
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

  const respuesta = await fetch(`${BASE}${ruta}`, { method: metodo, headers: cabeceras, body })

  if (respuesta.status === 401) {
    alCerrarSesion()
    throw new Error('La sesion expiro. Vuelve a iniciar sesion.')
  }
  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`
    try {
      const datos = await respuesta.json()
      if (typeof datos.detail === 'string') detalle = datos.detail
      else if (Array.isArray(datos.detail)) detalle = datos.detail.map((d) => d.msg).join(' | ')
    } catch { /* respuesta sin cuerpo JSON */ }
    throw new Error(detalle)
  }
  if (respuesta.status === 204) return null
  return respuesta.json()
}

export const api = {
  login: (username, password) => peticion('/auth/login', { metodo: 'POST', formulario: { username, password } }),
  yo: () => peticion('/auth/yo'),

  productos: (params = {}) => peticion(`/productos?${new URLSearchParams(params)}`),
  producto: (id) => peticion(`/productos/${id}`),
  crearProducto: (datos) => peticion('/productos', { metodo: 'POST', cuerpo: datos }),
  ajustarStock: (id, datos) => peticion(`/productos/${id}/ajuste-stock`, { metodo: 'POST', cuerpo: datos }),
  kardex: (id) => peticion(`/productos/${id}/kardex`),
  categorias: () => peticion('/productos/categorias'),

  imeis: (params = {}) => peticion(`/inventario/imei?${new URLSearchParams(params)}`),
  consultarImei: (imei) => peticion(`/inventario/imei/${imei}`),
  ingresarImei: (datos) => peticion('/inventario/imei', { metodo: 'POST', cuerpo: datos }),

  clientes: (q = '') => peticion(`/clientes?${new URLSearchParams(q ? { q } : {})}`),
  crearCliente: (datos) => peticion('/clientes', { metodo: 'POST', cuerpo: datos }),
  comprasCliente: (id) => peticion(`/clientes/${id}/compras`),

  ventas: (params = {}) => peticion(`/ventas?${new URLSearchParams(params)}`),
  venta: (id) => peticion(`/ventas/${id}`),
  crearVenta: (datos) => peticion('/ventas', { metodo: 'POST', cuerpo: datos }),
  anularVenta: (id, motivo) => peticion(`/ventas/${id}/anular`, { metodo: 'POST', cuerpo: { motivo } }),

  garantias: (params = {}) => peticion(`/garantias?${new URLSearchParams(params)}`),
  reclamarGarantia: (id, descripcion_falla) =>
    peticion(`/garantias/${id}/reclamar`, { metodo: 'POST', cuerpo: { descripcion_falla } }),
  cerrarGarantia: (id, solucion) =>
    peticion(`/garantias/${id}/cerrar`, { metodo: 'POST', cuerpo: { solucion } }),

  dashboard: () => peticion('/reportes/dashboard'),
  ventasPorDia: (dias = 14) => peticion(`/reportes/ventas-por-dia?dias=${dias}`),
  masVendidos: () => peticion('/reportes/mas-vendidos'),
  alertasStock: () => peticion('/reportes/alertas-stock'),
}

export function pesos(valor) {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency: 'COP', maximumFractionDigits: 0,
  }).format(Number(valor || 0))
}
