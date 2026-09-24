import { useEffect, useState } from 'react'
import { api, pesos } from '../api.js'
import { useAuth } from '../auth.jsx'

const BADGE = {
  disponible: 'ok', vendido: 'info', reservado: 'warn',
  en_garantia: 'warn', devuelto: 'warn', dado_de_baja: 'bad',
}

export default function Inventario() {
  const { usuario } = useAuth()
  const [productos, setProductos] = useState([])
  const [equipos, setEquipos] = useState([])
  const [filtroEstado, setFiltroEstado] = useState('')
  const [buscarImei, setBuscarImei] = useState('')
  const [nuevo, setNuevo] = useState({ imei: '', producto_id: '', color: '', almacenamiento_gb: '' })
  const [mensaje, setMensaje] = useState(null)
  const puedeEditar = usuario.rol === 'admin' || usuario.rol === 'bodega'

  const cargar = () => {
    api.productos().then(setProductos).catch(() => {})
    api.imeis({ ...(filtroEstado && { estado: filtroEstado }), ...(buscarImei && { q: buscarImei }) })
      .then(setEquipos).catch((e) => setMensaje({ tipo: 'error', texto: e.message }))
  }
  useEffect(cargar, [filtroEstado, buscarImei])

  const ingresar = async (e) => {
    e.preventDefault()
    setMensaje(null)
    try {
      await api.ingresarImei({
        imei: nuevo.imei.trim(),
        producto_id: Number(nuevo.producto_id),
        color: nuevo.color || null,
        almacenamiento_gb: nuevo.almacenamiento_gb ? Number(nuevo.almacenamiento_gb) : null,
      })
      setMensaje({ tipo: 'ok', texto: `Equipo ${nuevo.imei} ingresado al inventario.` })
      setNuevo({ imei: '', producto_id: '', color: '', almacenamiento_gb: '' })
      cargar()
    } catch (err) {
      setMensaje({ tipo: 'error', texto: err.message })
    }
  }

  const serializados = productos.filter((p) => p.requiere_imei)
  const accesorios = productos.filter((p) => !p.requiere_imei)

  return (
    <>
      <h1>Inventario e IMEI</h1>
      <p className="descripcion">
        Los equipos se controlan unidad por unidad con su IMEI; los accesorios por stock agregado.
      </p>
      {mensaje && <div className={`mensaje ${mensaje.tipo}`}>{mensaje.texto}</div>}

      {puedeEditar && (
        <div className="panel">
          <h2>Ingresar equipo a bodega</h2>
          <form onSubmit={ingresar}>
            <div className="fila">
              <div className="campo">
                <label>IMEI (15 digitos, con verificador Luhn valido)</label>
                <input required minLength={15} maxLength={15} value={nuevo.imei}
                       onChange={(e) => setNuevo({ ...nuevo, imei: e.target.value })} />
              </div>
              <div className="campo">
                <label>Modelo</label>
                <select required value={nuevo.producto_id}
                        onChange={(e) => setNuevo({ ...nuevo, producto_id: e.target.value })}>
                  <option value="">Selecciona...</option>
                  {serializados.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                </select>
              </div>
              <div className="campo">
                <label>Color</label>
                <input value={nuevo.color} onChange={(e) => setNuevo({ ...nuevo, color: e.target.value })} />
              </div>
              <div className="campo">
                <label>Almacenamiento (GB)</label>
                <input type="number" value={nuevo.almacenamiento_gb}
                       onChange={(e) => setNuevo({ ...nuevo, almacenamiento_gb: e.target.value })} />
              </div>
            </div>
            <button type="submit">Ingresar equipo</button>
          </form>
        </div>
      )}

      <div className="panel">
        <h2>Equipos serializados</h2>
        <div className="fila" style={{ marginBottom: 14 }}>
          <div className="campo">
            <label>Buscar IMEI</label>
            <input value={buscarImei} onChange={(e) => setBuscarImei(e.target.value)} placeholder="Digitos del IMEI" />
          </div>
          <div className="campo">
            <label>Estado</label>
            <select value={filtroEstado} onChange={(e) => setFiltroEstado(e.target.value)}>
              <option value="">Todos</option>
              <option value="disponible">Disponible</option>
              <option value="vendido">Vendido</option>
              <option value="en_garantia">En garantia</option>
              <option value="devuelto">Devuelto</option>
              <option value="dado_de_baja">Dado de baja</option>
            </select>
          </div>
        </div>
        <table>
          <thead>
            <tr><th>IMEI</th><th>Modelo</th><th>Color</th><th>Alm.</th><th>Estado</th><th>Ingreso</th></tr>
          </thead>
          <tbody>
            {equipos.map((e) => {
              const producto = productos.find((p) => p.id === e.producto_id)
              return (
                <tr key={e.id}>
                  <td style={{ fontFamily: 'monospace' }}>{e.imei}</td>
                  <td>{producto ? producto.nombre : e.producto_id}</td>
                  <td>{e.color || '-'}</td>
                  <td>{e.almacenamiento_gb ? `${e.almacenamiento_gb} GB` : '-'}</td>
                  <td><span className={`badge ${BADGE[e.estado] || 'info'}`}>{e.estado.replace('_', ' ')}</span></td>
                  <td>{new Date(e.fecha_ingreso).toLocaleDateString('es-CO')}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
        {equipos.length === 0 && <div className="vacio">Sin equipos para este filtro.</div>}
      </div>

      <div className="panel">
        <h2>Accesorios y consumibles</h2>
        <table>
          <thead>
            <tr><th>SKU</th><th>Producto</th><th className="derecha">Stock</th><th className="derecha">Minimo</th>
                <th className="derecha">Costo</th><th className="derecha">Venta</th></tr>
          </thead>
          <tbody>
            {accesorios.map((p) => (
              <tr key={p.id}>
                <td>{p.sku}</td>
                <td>{p.nombre}</td>
                <td className="derecha">
                  <span className={`badge ${p.disponibles <= p.stock_minimo ? 'bad' : 'ok'}`}>{p.disponibles}</span>
                </td>
                <td className="derecha">{p.stock_minimo}</td>
                <td className="derecha">{pesos(p.precio_costo)}</td>
                <td className="derecha">{pesos(p.precio_venta)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  )
}
