import { useState } from 'react'
import { useAuth } from '../auth.jsx'

export default function Login() {
  const { iniciarSesion } = useAuth()
  const [usuario, setUsuario] = useState('admin')
  const [clave, setClave] = useState('admin123')
  const [error, setError] = useState('')
  const [enviando, setEnviando] = useState(false)

  const enviar = async (e) => {
    e.preventDefault()
    setError(''); setEnviando(true)
    try {
      await iniciarSesion(usuario, clave)
    } catch (err) {
      setError(err.message)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <div className="login">
      <form className="panel" onSubmit={enviar}>
        <div className="logo">POS <span>Movil</span></div>
        <p className="descripcion">Sistema de gestion y venta de dispositivos moviles</p>

        {error && <div className="mensaje error">{error}</div>}

        <div className="campo">
          <label htmlFor="usuario">Usuario</label>
          <input id="usuario" value={usuario} onChange={(e) => setUsuario(e.target.value)} autoFocus />
        </div>
        <div className="campo">
          <label htmlFor="clave">Contrasena</label>
          <input id="clave" type="password" value={clave} onChange={(e) => setClave(e.target.value)} />
        </div>
        <button type="submit" disabled={enviando} style={{ width: '100%' }}>
          {enviando ? 'Verificando...' : 'Ingresar'}
        </button>

        <div className="pista">
          Usuarios de prueba:<br />
          admin / admin123 &middot; cajero / cajero123 &middot; bodega / bodega123
        </div>
      </form>
    </div>
  )
}
