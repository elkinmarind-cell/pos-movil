import { NavLink, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import { Cargando } from './componentes/ui.jsx'
import Login from './paginas/Login.jsx'
import Dashboard from './paginas/Dashboard.jsx'
import Caja from './paginas/Caja.jsx'
import PuntoVenta from './paginas/PuntoVenta.jsx'
import Ventas from './paginas/Ventas.jsx'
import Inventario from './paginas/Inventario.jsx'
import Compras from './paginas/Compras.jsx'
import Clientes from './paginas/Clientes.jsx'
import Posventa from './paginas/Posventa.jsx'
import Telefonia from './paginas/Telefonia.jsx'
import Iot from './paginas/Iot.jsx'
import Reportes from './paginas/Reportes.jsx'
import Usuarios from './paginas/Usuarios.jsx'
import { Panel, Vacio } from './componentes/ui.jsx'

const MENU = [
  { grupo: 'Operación', items: [
    { ruta: '/', texto: 'Panel', icono: '▣', fin: true },
    { ruta: '/venta', texto: 'Punto de venta', icono: '🛒', permiso: 'ventas.crear' },
    { ruta: '/caja', texto: 'Caja', icono: '🏦', permiso: 'caja.abrir' },
    { ruta: '/ventas', texto: 'Ventas', icono: '🧾', permiso: 'ventas.ver' },
  ]},
  { grupo: 'Inventario', items: [
    { ruta: '/inventario', texto: 'Productos e IMEI', icono: '📦', permiso: 'inventario.ver' },
    { ruta: '/compras', texto: 'Compras', icono: '🚚', permiso: 'compras.ver' },
  ]},
  { grupo: 'Clientes', items: [
    { ruta: '/clientes', texto: 'Clientes', icono: '👥', permiso: 'clientes.ver' },
    { ruta: '/posventa', texto: 'Posventa', icono: '🛠', permiso: 'garantias.ver', permiso2: 'servicio.ver' },
    { ruta: '/telefonia', texto: 'Líneas', icono: '📱', permiso: 'ventas.ver' },
  ]},
  { grupo: 'Dirección', items: [
    { ruta: '/reportes', texto: 'Reportes', icono: '📊', permiso: 'reportes.ver' },
    { ruta: '/iot', texto: 'IoT y alertas', icono: '📡' },
    { ruta: '/usuarios', texto: 'Usuarios y roles', icono: '🔑', permiso: 'usuarios.ver' },
  ]},
]

const TITULOS = {
  '/': ['Panel de control', 'Resumen del día'],
  '/venta': ['Punto de venta', 'Registrar una venta'],
  '/caja': ['Caja', 'Apertura, movimientos y arqueo'],
  '/ventas': ['Ventas', 'Historial de facturas'],
  '/inventario': ['Inventario', 'Productos, equipos y kardex'],
  '/compras': ['Compras', 'Órdenes y recepción de mercancía'],
  '/clientes': ['Clientes', 'Registro e historial'],
  '/posventa': ['Posventa', 'Garantías, devoluciones, servicio y apartados'],
  '/telefonia': ['Líneas', 'Activación de líneas con operadores'],
  '/reportes': ['Reportes', 'Indicadores y rentabilidad'],
  '/iot': ['IoT', 'Dispositivos, eventos y alertas'],
  '/usuarios': ['Usuarios y roles', 'Accesos y permisos del sistema'],
}

function SinPermiso() {
  return (
    <Panel titulo="Sin permiso">
      <Vacio icono="🔒">
        Tu rol no tiene acceso a esta sección. Si la necesitas, pídele al administrador
        que te la habilite desde Usuarios y roles.
      </Vacio>
    </Panel>
  )
}

/** Envuelve una pagina: si el rol no tiene el permiso, muestra el aviso en vez de la pagina. */
function Protegida({ permiso, children }) {
  const { puede } = useAuth()
  if (permiso && !puede(permiso)) return <SinPermiso />
  return children
}

function iniciales(nombre = '') {
  return nombre.split(' ').filter(Boolean).slice(0, 2).map((p) => p[0]).join('').toUpperCase()
}

export default function App() {
  const { usuario, cargando, cerrarSesion, puede } = useAuth()
  const ubicacion = useLocation()

  if (cargando) return <Cargando>Verificando la sesión…</Cargando>
  if (!usuario) return <Login />

  const [titulo, sub] = TITULOS[ubicacion.pathname] ?? ['POS Móvil', '']
  const visible = (i) => !i.permiso || puede(i.permiso, i.permiso2 ?? i.permiso)

  return (
    <div className="app">
      <aside className="lateral">
        <div className="marca">
          <div className="nombre">POS <span>Móvil</span></div>
          <div className="lema">Gestión y venta de dispositivos</div>
        </div>

        <nav className="nav">
          {MENU.map((g) => {
            const items = g.items.filter(visible)
            if (!items.length) return null
            return (
              <div key={g.grupo}>
                <div className="nav-grupo">{g.grupo}</div>
                {items.map((i) => (
                  <NavLink key={i.ruta} to={i.ruta} end={i.fin}
                           className={({ isActive }) => `nav-item${isActive ? ' activo' : ''}`}>
                    <span className="icono">{i.icono}</span>{i.texto}
                  </NavLink>
                ))}
              </div>
            )
          })}
        </nav>

        <div className="pie-lateral">
          <div className="usuario-chip">
            <div className="avatar">{iniciales(usuario.nombre_completo)}</div>
            <div className="datos">
              <div className="nom">{usuario.nombre_completo}</div>
              <div className="rol">{usuario.rol?.nombre?.toLowerCase() ?? ''}</div>
            </div>
          </div>
          <button className="secundario pequeno ancho" onClick={cerrarSesion}>Cerrar sesión</button>
        </div>
      </aside>

      <main className="contenido">
        <header className="barra-superior">
          <div>
            <div className="titulo">{titulo}</div>
            <div className="sub">{sub}</div>
          </div>
        </header>

        <div className="pagina">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/venta" element={<Protegida permiso="ventas.crear"><PuntoVenta /></Protegida>} />
            <Route path="/caja" element={<Protegida permiso="caja.abrir"><Caja /></Protegida>} />
            <Route path="/ventas" element={<Protegida permiso="ventas.ver"><Ventas /></Protegida>} />
            <Route path="/inventario" element={<Protegida permiso="inventario.ver"><Inventario /></Protegida>} />
            <Route path="/compras" element={<Protegida permiso="compras.ver"><Compras /></Protegida>} />
            <Route path="/clientes" element={<Protegida permiso="clientes.ver"><Clientes /></Protegida>} />
            <Route path="/posventa" element={<Posventa />} />
            <Route path="/telefonia" element={<Telefonia />} />
            <Route path="/iot" element={<Iot />} />
            <Route path="/reportes" element={<Protegida permiso="reportes.ver"><Reportes /></Protegida>} />
            <Route path="/usuarios" element={<Protegida permiso="usuarios.ver"><Usuarios /></Protegida>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </main>
    </div>
  )
}
