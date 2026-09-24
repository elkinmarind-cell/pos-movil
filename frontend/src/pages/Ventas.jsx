import { useEffect, useState } from 'react'
import { api, pesos } from '../api.js'
import { useAuth } from '../auth.jsx'

export default function Ventas() {
  const { usuario } = useAuth()
  const [ventas, setVentas] = useState([])
  const [detalle, setDetalle] = useState(null)
  const [mensaje, setMensaje] = useState(null)
  const [anulando, setAnulando] = useState(null)
  const [motivo, setMotivo] = useState('')

  const cargar = () => api.ventas().then(setVentas).catch((e) => setMensaje({ tipo: 'error', texto: e.message }))
  useEffect(cargar, [])

  const anular = async () => {
    setMensaje(null)
    try {
      await api.anularVenta(anulando.id, motivo)
      setMensaje({ tipo: 'ok', texto: 'Venta anulada. El inventario y las garantias fueron reversados.' })
      setAnulando(null); setMotivo(''); setDetalle(null); cargar()
    } catch (err) {
      setMensaje({ tipo: 'error', texto: err.message })
    }
  }

  return (
    <>
      <h1>Ventas</h1>
      <p className="descripcion">Historial de facturas. La anulacion revierte inventario y garantias.</p>
      {mensaje && <div className={`mensaje ${mensaje.tipo}`}>{mensaje.texto}</div>}

      {anulando && (
        <div className="panel">
          <h2>Anular factura {anulando.numero_factura}</h2>
          <div className="campo">
            <label>Motivo de la anulacion (minimo 5 caracteres)</label>
            <input value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          </div>
          <button className="peligro" onClick={anular} disabled={motivo.trim().length < 5}>Confirmar anulacion</button>{' '}
          <button className="secundario" onClick={() => { setAnulando(null); setMotivo('') }}>Cancelar</button>
        </div>
      )}

      <div className="panel">
        <table>
          <thead>
            <tr><th>Factura</th><th>Fecha</th><th>Cliente</th><th>Pago</th><th>Estado</th>
                <th className="derecha">Total</th><th></th></tr>
          </thead>
          <tbody>
            {ventas.map((v) => (
              <tr key={v.id}>
                <td>{v.numero_factura}</td>
                <td>{new Date(v.fecha).toLocaleString('es-CO')}</td>
                <td>{v.cliente ? `${v.cliente.nombres} ${v.cliente.apellidos || ''}` : 'Consumidor final'}</td>
                <td>{v.metodo_pago.replace('_', ' ')}</td>
                <td><span className={`badge ${v.estado === 'completada' ? 'ok' : 'bad'}`}>{v.estado}</span></td>
                <td className="derecha">{pesos(v.total)}</td>
                <td className="derecha">
                  <button className="secundario mini" onClick={() => setDetalle(v)}>Ver</button>{' '}
                  {usuario.rol === 'admin' && v.estado === 'completada' && (
                    <button className="peligro mini" onClick={() => setAnulando(v)}>Anular</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {ventas.length === 0 && <div className="vacio">Aun no hay ventas registradas.</div>}
      </div>

      {detalle && (
        <div className="panel">
          <h2>Factura {detalle.numero_factura}</h2>
          <p className="descripcion">
            {new Date(detalle.fecha).toLocaleString('es-CO')} &middot; Atendido por {detalle.usuario.nombre_completo}
            {detalle.motivo_anulacion && ` · Anulada: ${detalle.motivo_anulacion}`}
          </p>
          <table>
            <thead>
              <tr><th>Descripcion</th><th className="derecha">Cant.</th><th className="derecha">Unitario</th>
                  <th className="derecha">Descuento</th><th className="derecha">IVA</th><th className="derecha">Total</th></tr>
            </thead>
            <tbody>
              {detalle.detalles.map((d) => (
                <tr key={d.id}>
                  <td>{d.descripcion}</td>
                  <td className="derecha">{d.cantidad}</td>
                  <td className="derecha">{pesos(d.precio_unitario)}</td>
                  <td className="derecha">{pesos(d.descuento)}</td>
                  <td className="derecha">{pesos(d.iva_valor)}</td>
                  <td className="derecha">{pesos(d.total_linea)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="totales">
            <div><span>Subtotal</span><span>{pesos(detalle.subtotal)}</span></div>
            <div><span>IVA</span><span>{pesos(detalle.iva_total)}</span></div>
            <div className="granTotal"><span>TOTAL</span><span>{pesos(detalle.total)}</span></div>
          </div>
          <br />
          <button className="secundario" onClick={() => setDetalle(null)}>Cerrar</button>
        </div>
      )}
    </>
  )
}
