/* Piezas reutilizables: toda la interfaz se arma con estas. */
import { useEffect, useState } from 'react'

export function Panel({ titulo, sub, acciones, children, sinRelleno }) {
  return (
    <section className="panel">
      {(titulo || acciones) && (
        <header className="panel-cabecera">
          <div>
            {titulo && <h2>{titulo}</h2>}
            {sub && <div className="sub">{sub}</div>}
          </div>
          <div className="espaciador" />
          {acciones}
        </header>
      )}
      <div className={`panel-cuerpo${sinRelleno ? ' sin-relleno' : ''}`}>{children}</div>
    </section>
  )
}

export function Kpi({ etiqueta, valor, nota, tono = '' }) {
  return (
    <div className={`tarjeta-kpi ${tono}`}>
      <div className="etiqueta">{etiqueta}</div>
      <div className="valor">{valor}</div>
      {nota && <div className="nota">{nota}</div>}
    </div>
  )
}

const TONOS = {
  DISPONIBLE: 'ok', ACTIVA: 'ok', COMPLETADA: 'ok', VIGENTE: 'ok', ACEPTADA: 'ok', ABIERTO: 'ok',
  RECIBIDA: 'ok', ATENDIDA: 'info', ENTREGADO: 'ok', LISTO: 'ok',
  VENDIDO: 'info', CERRADO: 'info', COMPLETADO: 'info', PENDIENTE: 'alerta', ENVIADA: 'alerta',
  APARTADO: 'alerta', EN_SERVICIO: 'alerta', EN_RECLAMACION: 'alerta', RECIBIDA_PARCIAL: 'alerta',
  DIAGNOSTICO: 'alerta', REPARACION: 'alerta', RECIBIDO: 'alerta', BORRADOR: '',
  ANULADA: 'peligro', VENCIDA: 'peligro', VENCIDO: 'peligro', RECHAZADA: 'peligro',
  CANCELADO: 'peligro', DADO_DE_BAJA: 'peligro', DEVUELTO: 'alerta',
  CRITICA: 'peligro', ALTA: 'peligro', MEDIA: 'alerta', BAJA: 'info',
}

export function Estado({ valor, tono }) {
  if (!valor) return <span className="texto-tenue">—</span>
  const clase = tono ?? TONOS[valor] ?? ''
  return (
    <span className={`marca-estado ${clase}`}>
      <span className="punto" />
      {String(valor).replaceAll('_', ' ').toLowerCase()}
    </span>
  )
}

export function Aviso({ tipo = 'info', children, alCerrar }) {
  if (!children) return null
  return (
    <div className={`aviso ${tipo}`}>
      <div style={{ flex: 1 }}>{children}</div>
      {alCerrar && <button className="fantasma pequeno" onClick={alCerrar} aria-label="Cerrar">✕</button>}
    </div>
  )
}

export function Vacio({ icono = '○', children }) {
  return <div className="vacio"><span className="icono">{icono}</span>{children}</div>
}

export function Tabla({ columnas, filas, clave = (f) => f.id, vacio = 'Sin registros', alHacerClic }) {
  if (!filas?.length) return <Vacio>{vacio}</Vacio>
  return (
    <div className="tabla-envoltura">
      <table>
        <thead>
          <tr>{columnas.map((c, i) => <th key={i} className={c.derecha ? 'derecha' : ''}>{c.titulo}</th>)}</tr>
        </thead>
        <tbody>
          {filas.map((f) => (
            <tr key={clave(f)} onClick={alHacerClic ? () => alHacerClic(f) : undefined}
                style={alHacerClic ? { cursor: 'pointer' } : undefined}>
              {columnas.map((c, i) => (
                <td key={i} className={[c.derecha ? 'derecha' : '', c.clase || ''].join(' ').trim()}>
                  {c.celda(f)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function Modal({ titulo, children, pie, alCerrar, ancho }) {
  useEffect(() => {
    const esc = (e) => e.key === 'Escape' && alCerrar?.()
    window.addEventListener('keydown', esc)
    return () => window.removeEventListener('keydown', esc)
  }, [alCerrar])
  return (
    <div className="velo" onClick={(e) => e.target === e.currentTarget && alCerrar?.()}>
      <div className={`modal${ancho ? ' ancho' : ''}`}>
        <header className="modal-cabecera">
          <h2>{titulo}</h2>
          <div className="espaciador" />
          <button className="fantasma" onClick={alCerrar} aria-label="Cerrar">✕</button>
        </header>
        <div className="modal-cuerpo">{children}</div>
        {pie && <footer className="modal-pie">{pie}</footer>}
      </div>
    </div>
  )
}

export function Campo({ etiqueta, ayuda, children }) {
  return (
    <div className="campo">
      {etiqueta && <label>{etiqueta}</label>}
      {children}
      {ayuda && <div className="ayuda">{ayuda}</div>}
    </div>
  )
}

export function Cargando({ children = 'Cargando…' }) {
  return <div className="cargando">{children}</div>
}

/** Carga datos de la API y entrega { datos, error, cargando, recargar }. */
export function useDatos(fn, deps = []) {
  const [estado, setEstado] = useState({ datos: null, error: '', cargando: true })
  const [sello, setSello] = useState(0)
  useEffect(() => {
    let vivo = true
    setEstado((e) => ({ ...e, cargando: true }))
    Promise.resolve()
      .then(fn)
      .then((datos) => vivo && setEstado({ datos, error: '', cargando: false }))
      .catch((e) => vivo && setEstado({ datos: null, error: e.message, cargando: false }))
    return () => { vivo = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, sello])
  return { ...estado, recargar: () => setSello((s) => s + 1) }
}
