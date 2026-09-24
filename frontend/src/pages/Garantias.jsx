import { useEffect, useState } from 'react'
import { api } from '../api.js'

const BADGE = { vigente: 'ok', vencida: 'bad', en_reclamacion: 'warn', atendida: 'info' }

export default function Garantias() {
  const [garantias, setGarantias] = useState([])
  const [filtro, setFiltro] = useState('')
  const [mensaje, setMensaje] = useState(null)
  const [reclamando, setReclamando] = useState(null)
  const [texto, setTexto] = useState('')

  const cargar = () => api.garantias(filtro ? { estado: filtro } : {})
    .then(setGarantias).catch((e) => setMensaje({ tipo: 'error', texto: e.message }))
  useEffect(cargar, [filtro])

  const accion = async () => {
    setMensaje(null)
    try {
      if (reclamando.modo === 'reclamar') {
        await api.reclamarGarantia(reclamando.garantia.id, texto)
        setMensaje({ tipo: 'ok', texto: 'Reclamacion abierta. El equipo quedo marcado en garantia.' })
      } else {
        await api.cerrarGarantia(reclamando.garantia.id, texto)
        setMensaje({ tipo: 'ok', texto: 'Reclamacion cerrada y registrada.' })
      }
      setReclamando(null); setTexto(''); cargar()
    } catch (err) {
      setMensaje({ tipo: 'error', texto: err.message })
    }
  }

  return (
    <>
      <h1>Garantias</h1>
      <p className="descripcion">
        Cada venta genera su garantia automaticamente (Ley 1480 de 2011, Estatuto del Consumidor).
      </p>
      {mensaje && <div className={`mensaje ${mensaje.tipo}`}>{mensaje.texto}</div>}

      {reclamando && (
        <div className="panel">
          <h2>{reclamando.modo === 'reclamar' ? 'Abrir reclamacion' : 'Cerrar reclamacion'}</h2>
          <div className="campo">
            <label>{reclamando.modo === 'reclamar' ? 'Descripcion de la falla' : 'Solucion aplicada'}</label>
            <textarea rows={3} value={texto} onChange={(e) => setTexto(e.target.value)} />
          </div>
          <button onClick={accion} disabled={texto.trim().length < 5}>Confirmar</button>{' '}
          <button className="secundario" onClick={() => { setReclamando(null); setTexto('') }}>Cancelar</button>
        </div>
      )}

      <div className="panel">
        <div className="campo" style={{ maxWidth: 260 }}>
          <label>Estado</label>
          <select value={filtro} onChange={(e) => setFiltro(e.target.value)}>
            <option value="">Todas</option>
            <option value="vigente">Vigentes</option>
            <option value="en_reclamacion">En reclamacion</option>
            <option value="atendida">Atendidas</option>
            <option value="vencida">Vencidas</option>
          </select>
        </div>
        <table>
          <thead>
            <tr><th>#</th><th>Inicio</th><th>Vence</th><th className="derecha">Dias rest.</th>
                <th>Estado</th><th>Falla reportada</th><th></th></tr>
          </thead>
          <tbody>
            {garantias.map((g) => (
              <tr key={g.id}>
                <td>{g.id}</td>
                <td>{g.fecha_inicio}</td>
                <td>{g.fecha_fin}</td>
                <td className="derecha">{g.dias_restantes}</td>
                <td><span className={`badge ${BADGE[g.estado]}`}>{g.estado.replace('_', ' ')}</span></td>
                <td>{g.descripcion_falla || '-'}</td>
                <td className="derecha">
                  {g.estado === 'vigente' && (
                    <button className="mini" onClick={() => setReclamando({ garantia: g, modo: 'reclamar' })}>
                      Reclamar
                    </button>
                  )}
                  {g.estado === 'en_reclamacion' && (
                    <button className="mini" onClick={() => setReclamando({ garantia: g, modo: 'cerrar' })}>
                      Cerrar
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {garantias.length === 0 && <div className="vacio">No hay garantias para este filtro.</div>}
      </div>
    </>
  )
}
