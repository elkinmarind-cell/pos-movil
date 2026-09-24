import { useEffect, useState } from 'react'
import { api, pesos } from '../api.js'

const VACIO = {
  tipo_documento: 'CC', numero_documento: '', nombres: '', apellidos: '',
  telefono: '', email: '', direccion: '', ciudad: 'Bogota',
}

export default function Clientes() {
  const [clientes, setClientes] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [formulario, setFormulario] = useState(VACIO)
  const [mensaje, setMensaje] = useState(null)
  const [historial, setHistorial] = useState(null)

  const cargar = () => api.clientes(busqueda).then(setClientes).catch((e) => setMensaje({ tipo: 'error', texto: e.message }))
  useEffect(() => { cargar() }, [busqueda])

  const guardar = async (e) => {
    e.preventDefault()
    setMensaje(null)
    try {
      const datos = { ...formulario }
      Object.keys(datos).forEach((k) => { if (datos[k] === '') datos[k] = null })
      datos.tipo_documento = formulario.tipo_documento
      datos.numero_documento = formulario.numero_documento
      datos.nombres = formulario.nombres
      await api.crearCliente(datos)
      setMensaje({ tipo: 'ok', texto: 'Cliente registrado correctamente.' })
      setFormulario(VACIO)
      cargar()
    } catch (err) {
      setMensaje({ tipo: 'error', texto: err.message })
    }
  }

  const verHistorial = async (cliente) => {
    const compras = await api.comprasCliente(cliente.id)
    setHistorial({ cliente, compras })
  }

  return (
    <>
      <h1>Clientes</h1>
      <p className="descripcion">Registro de compradores y su historial, base para el servicio de garantias.</p>
      {mensaje && <div className={`mensaje ${mensaje.tipo}`}>{mensaje.texto}</div>}

      <div className="panel">
        <h2>Registrar cliente</h2>
        <form onSubmit={guardar}>
          <div className="fila">
            <div className="campo">
              <label>Tipo de documento</label>
              <select value={formulario.tipo_documento}
                      onChange={(e) => setFormulario({ ...formulario, tipo_documento: e.target.value })}>
                <option value="CC">Cedula de ciudadania</option>
                <option value="CE">Cedula de extranjeria</option>
                <option value="TI">Tarjeta de identidad</option>
                <option value="NIT">NIT</option>
                <option value="PASAPORTE">Pasaporte</option>
              </select>
            </div>
            <div className="campo">
              <label>Numero</label>
              <input required value={formulario.numero_documento}
                     onChange={(e) => setFormulario({ ...formulario, numero_documento: e.target.value })} />
            </div>
            <div className="campo">
              <label>Nombres</label>
              <input required value={formulario.nombres}
                     onChange={(e) => setFormulario({ ...formulario, nombres: e.target.value })} />
            </div>
            <div className="campo">
              <label>Apellidos</label>
              <input value={formulario.apellidos}
                     onChange={(e) => setFormulario({ ...formulario, apellidos: e.target.value })} />
            </div>
            <div className="campo">
              <label>Telefono</label>
              <input value={formulario.telefono}
                     onChange={(e) => setFormulario({ ...formulario, telefono: e.target.value })} />
            </div>
            <div className="campo">
              <label>Correo</label>
              <input type="email" value={formulario.email}
                     onChange={(e) => setFormulario({ ...formulario, email: e.target.value })} />
            </div>
            <div className="campo">
              <label>Direccion</label>
              <input value={formulario.direccion}
                     onChange={(e) => setFormulario({ ...formulario, direccion: e.target.value })} />
            </div>
            <div className="campo">
              <label>Ciudad</label>
              <input value={formulario.ciudad}
                     onChange={(e) => setFormulario({ ...formulario, ciudad: e.target.value })} />
            </div>
          </div>
          <button type="submit">Guardar cliente</button>
        </form>
      </div>

      <div className="panel">
        <h2>Clientes registrados</h2>
        <div className="campo">
          <input placeholder="Buscar por documento, nombre o telefono..."
                 value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
        </div>
        <table>
          <thead><tr><th>Documento</th><th>Nombre</th><th>Telefono</th><th>Ciudad</th><th></th></tr></thead>
          <tbody>
            {clientes.map((c) => (
              <tr key={c.id}>
                <td>{c.tipo_documento} {c.numero_documento}</td>
                <td>{c.nombres} {c.apellidos || ''}</td>
                <td>{c.telefono || '-'}</td>
                <td>{c.ciudad || '-'}</td>
                <td className="derecha">
                  <button className="secundario mini" onClick={() => verHistorial(c)}>Historial</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {clientes.length === 0 && <div className="vacio">Sin clientes para esta busqueda.</div>}
      </div>

      {historial && (
        <div className="panel">
          <h2>Compras de {historial.cliente.nombres} {historial.cliente.apellidos || ''}</h2>
          {historial.compras.length === 0 ? <div className="vacio">Este cliente aun no tiene compras.</div> : (
            <table>
              <thead><tr><th>Factura</th><th>Fecha</th><th>Items</th><th>Estado</th><th className="derecha">Total</th></tr></thead>
              <tbody>
                {historial.compras.map((v) => (
                  <tr key={v.id}>
                    <td>{v.numero_factura}</td>
                    <td>{new Date(v.fecha).toLocaleString('es-CO')}</td>
                    <td>{v.detalles.map((d) => d.descripcion).join(', ')}</td>
                    <td><span className={`badge ${v.estado === 'completada' ? 'ok' : 'bad'}`}>{v.estado}</span></td>
                    <td className="derecha">{pesos(v.total)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <br />
          <button className="secundario" onClick={() => setHistorial(null)}>Cerrar</button>
        </div>
      )}
    </>
  )
}
