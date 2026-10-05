import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, registrarCierreSesion } from './api.js'

const Contexto = createContext(null)

export function ProveedorAuth({ children }) {
  const [sesion, setSesion] = useState(null)   // { usuario, permisos }
  const [cargando, setCargando] = useState(true)

  const cerrarSesion = useCallback(() => {
    try { localStorage.removeItem('pos_token') } catch { /* sin almacenamiento */ }
    setSesion(null)
  }, [])

  useEffect(() => {
    registrarCierreSesion(cerrarSesion)
    let hay = null
    try { hay = localStorage.getItem('pos_token') } catch { /* sin almacenamiento */ }
    if (!hay) { setCargando(false); return }
    api.yo()
      .then((d) => setSesion({ usuario: d.usuario, permisos: d.permisos }))
      .catch(cerrarSesion)
      .finally(() => setCargando(false))
  }, [cerrarSesion])

  const iniciarSesion = async (username, password) => {
    const d = await api.login(username, password)
    try { localStorage.setItem('pos_token', d.access_token) } catch { /* sin almacenamiento */ }
    setSesion({ usuario: d.usuario, permisos: d.permisos })
  }

  const puede = useCallback(
    (...codigos) => !!sesion && codigos.some((c) => sesion.permisos.includes(c)),
    [sesion],
  )

  return (
    <Contexto.Provider value={{ ...sesion, cargando, iniciarSesion, cerrarSesion, puede }}>
      {children}
    </Contexto.Provider>
  )
}

export const useAuth = () => useContext(Contexto)
