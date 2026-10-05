import { useState } from 'react'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo } from '../componentes/ui.jsx'

export default function Login() {
  const { iniciarSesion } = useAuth()
  const [usuario, setUsuario] = useState('')
  const [clave, setClave] = useState('')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  const enviar = async (e) => {
    e.preventDefault()
    setError(''); setEnviando(true)
    try { await iniciarSesion(usuario.trim(), clave) }
    catch (err) { setError(err.message) }
    finally { setEnviando(false) }
  }

  return (
    <div className="login">
      <section className="login-lado">
        <div className="login-marca">POS Móvil</div>
        <h1>Gestión y venta de dispositivos móviles</h1>
        <p>
          Inventario serializado por IMEI, caja con arqueo, facturación electrónica
          y trazabilidad completa de cada equipo.
        </p>
        <ul>
          <li>Control unidad por unidad con validación de IMEI</li>
          <li>Garantías y servicio técnico enlazados a la venta</li>
          <li>Reportes de rentabilidad y rotación en tiempo real</li>
        </ul>
      </section>

      <section className="login-form">
        <form className="caja-form" onSubmit={enviar}>
          <h2>Iniciar sesión</h2>
          <p className="sub">Ingresa con las credenciales que te asignó el administrador.</p>

          {error && <Aviso tipo="error">{error}</Aviso>}

          <Campo etiqueta="Usuario">
            <input value={usuario} onChange={(e) => setUsuario(e.target.value)}
                   autoFocus autoComplete="username" placeholder="tu.usuario" />
          </Campo>
          <Campo etiqueta="Contraseña">
            <input type="password" value={clave} onChange={(e) => setClave(e.target.value)}
                   autoComplete="current-password" placeholder="••••••••" />
          </Campo>

          <button type="submit" className="ancho" disabled={enviando || !usuario || !clave}>
            {enviando ? 'Verificando…' : 'Entrar'}
          </button>
        </form>
      </section>
    </div>
  )
}
