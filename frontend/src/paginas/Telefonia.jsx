import { useState } from 'react'
import { api, pesos, fechaHora, legible } from '../api.js'
import { Aviso, Campo, Cargando, Estado, Modal, Panel, Tabla, useDatos } from '../componentes/ui.jsx'

export default function Telefonia() {
  const activaciones = useDatos(() => api.activaciones(), [])
  const planes = useDatos(() => api.planes(), [])
  const clientes = useDatos(() => api.clientes(), [])
  const [ventana, setVentana] = useState(false)
  const [f, setF] = useState({ tipo: 'NUEVA' })
  const [mensaje, setMensaje] = useState(null)

  const activar = async () => {
    setMensaje(null)
    try {
      await api.activarLinea({
        plan_id: Number(f.plan_id), cliente_id: Number(f.cliente_id),
        numero_linea: f.numero_linea, iccid_sim: f.iccid_sim, tipo: f.tipo,
      })
      setVentana(false); setF({ tipo: 'NUEVA' }); activaciones.recargar()
      setMensaje({ tipo: 'ok', texto: 'Línea registrada.' })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const comision = planes.datos?.find((p) => String(p.id) === String(f.plan_id))?.comision

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Activación de líneas</h1>
        <p>Cada línea activada deja una comisión del operador para la tienda.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <Panel titulo="Planes disponibles" sinRelleno>
        {planes.cargando ? <Cargando /> : (
          <Tabla
            filas={planes.datos ?? []}
            columnas={[
              { titulo: 'Operador', celda: (p) => <span className="celda-principal">{p.operador?.nombre}</span> },
              { titulo: 'Plan', celda: (p) => p.nombre },
              { titulo: 'Modalidad', celda: (p) => <Estado valor={p.modalidad} tono="info" /> },
              { titulo: 'Datos', derecha: true, celda: (p) => p.datos_gb ? `${Number(p.datos_gb)} GB` : '—' },
              { titulo: 'Cargo mensual', derecha: true, celda: (p) => pesos(p.cargo_mensual) },
              { titulo: 'Comisión', derecha: true, celda: (p) => <strong>{pesos(p.comision)}</strong> },
            ]} />
        )}
      </Panel>

      <Panel titulo="Líneas activadas"
             acciones={<button onClick={() => setVentana(true)}>Activar línea</button>} sinRelleno>
        {activaciones.cargando ? <Cargando /> : (
          <Tabla
            filas={activaciones.datos ?? []}
            vacio="Todavía no hay líneas activadas."
            columnas={[
              { titulo: 'Línea', clase: 'mono', celda: (a) => a.numero_linea },
              { titulo: 'Plan', celda: (a) => a.plan ? `${a.plan.operador?.nombre ?? ''} · ${a.plan.nombre}` : `Plan ${a.plan_id}` },
              { titulo: 'SIM (ICCID)', clase: 'mono', celda: (a) => a.iccid_sim },
              { titulo: 'Tipo', celda: (a) => legible(a.tipo) },
              { titulo: 'Fecha', celda: (a) => fechaHora(a.fecha) },
              { titulo: 'Estado', celda: (a) => <Estado valor={a.estado} /> },
            ]} />
        )}
      </Panel>

      {ventana && (
        <Modal titulo="Activar una línea" ancho alCerrar={() => setVentana(false)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(false)}>Cancelar</button>
                 <button disabled={!f.plan_id || !f.cliente_id || !/^3\d{9}$/.test(f.numero_linea ?? '') || (f.iccid_sim ?? '').length < 18}
                         onClick={activar}>Activar</button>
               </>}>
          <div className="fila-campos">
            <Campo etiqueta="Cliente">
              <select value={f.cliente_id ?? ''} onChange={(e) => setF({ ...f, cliente_id: e.target.value })}>
                <option value="">Selecciona…</option>
                {(clientes.datos ?? []).map((c) => (
                  <option key={c.id} value={c.id}>{c.numero_documento} — {c.nombres} {c.apellidos ?? ''}</option>))}
              </select>
            </Campo>
            <Campo etiqueta="Plan">
              <select value={f.plan_id ?? ''} onChange={(e) => setF({ ...f, plan_id: e.target.value })}>
                <option value="">Selecciona…</option>
                {(planes.datos ?? []).map((p) => (
                  <option key={p.id} value={p.id}>{p.operador?.nombre} · {p.nombre}</option>))}
              </select>
            </Campo>
            <Campo etiqueta="Número de línea" ayuda="Diez dígitos que empiezan por 3.">
              <input className="mono" maxLength={10} value={f.numero_linea ?? ''}
                     onChange={(e) => setF({ ...f, numero_linea: e.target.value.replace(/\D/g, '') })} />
            </Campo>
            <Campo etiqueta="ICCID de la SIM">
              <input className="mono" maxLength={22} value={f.iccid_sim ?? ''}
                     onChange={(e) => setF({ ...f, iccid_sim: e.target.value })} />
            </Campo>
            <Campo etiqueta="Tipo">
              <select value={f.tipo} onChange={(e) => setF({ ...f, tipo: e.target.value })}>
                <option value="NUEVA">Línea nueva</option>
                <option value="PORTABILIDAD">Portabilidad</option>
                <option value="REPOSICION">Reposición de SIM</option>
              </select>
            </Campo>
          </div>
          {comision && <Aviso tipo="ok">Comisión para la tienda: <strong>{pesos(comision)}</strong></Aviso>}
        </Modal>
      )}
    </>
  )
}
