import { Navigate, NavLink, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth.jsx'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Caja from './pages/Caja.jsx'
import Inventario from './pages/Inventario.jsx'
import Clientes from './pages/Clientes.jsx'
import Garantias from './pages/Garantias.jsx'
import Ventas from './pages/Ventas.jsx'

const MENU = [
  { ruta: '/', texto: 'Dashboard' },
  { ruta: '/caja', texto: 'Caja / Venta' },
  { ruta: '/ventas', texto: 'Ventas' },
  { ruta: '/inventario', texto: 'Inventario e IMEI' },
  { ruta: '/clientes', texto: 'Clientes' },
  { ruta: '/garantias', texto: 'Garantias' },
]

export default function App() {
  const { usuario, cargando, cerrarSesion } = useAuth()

  if (cargando) return <div className="login"><p>Cargando...</p></div>
  if (!usuario) return <Login />

  return (
    <div className="app">
      <aside className="lateral">
        <div className="logo">POS <span>Movil</span></div>
        <div className="subtitulo">Gestion y venta de dispositivos moviles</div>
        {MENU.map((item) => (
          <NavLink
            key={item.ruta}
            to={item.ruta}
            end={item.ruta === '/'}
            className={({ isActive }) => `nav-item ${isActive ? 'activo' : ''}`}
          >
            {item.texto}
          </NavLink>
        ))}
        <div className="pie-lateral">
          <div style={{ marginBottom: 8 }}>
            <strong style={{ color: 'var(--texto)' }}>{usuario.nombre_completo}</strong><br />
            <span className="badge info">{usuario.rol}</span>
          </div>
          <button className="secundario mini" onClick={cerrarSesion}>Cerrar sesion</button>
        </div>
      </aside>

      <main className="contenido">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/caja" element={<Caja />} />
          <Route path="/ventas" element={<Ventas />} />
          <Route path="/inventario" element={<Inventario />} />
          <Route path="/clientes" element={<Clientes />} />
          <Route path="/garantias" element={<Garantias />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  )
}
