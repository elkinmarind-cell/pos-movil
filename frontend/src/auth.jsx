import { createContext, useContext, useEffect, useState } from 'react'
import { api, registrarCierreSesion } from './api.js'

const ContextoAuth = createContext(null)

export function ProveedorAuth({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(true)

  const cerrarSesion = () => {
    localStorage.removeItem('pos_token')
    setUsuario(null)
  }

  useEffect(() => {
    registrarCierreSesion(cerrarSesion)
    if (!localStorage.getItem('pos_token')) { setCargando(false); return }
    api.yo().then(setUsuario).catch(cerrarSesion).finally(() => setCargando(false))
  }, [])

  const iniciarSesion = async (username, password) => {
    const datos = await api.login(username, password)
    localStorage.setItem('pos_token', datos.access_token)
    setUsuario(datos.usuario)
    return datos.usuario
  }

  return (
    <ContextoAuth.Provider value={{ usuario, cargando, iniciarSesion, cerrarSesion }}>
      {children}
    </ContextoAuth.Provider>
  )
}

export const useAuth = () => useContext(ContextoAuth)
