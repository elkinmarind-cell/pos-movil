import { useState } from 'react'
import { api, pesos, fecha, fechaHora, legible } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo, Cargando, Estado, Modal, Panel, Tabla, useDatos } from '../componentes/ui.jsx'

const DOCUMENTOS = ['CC', 'CE', 'TI', 'NIT', 'PASAPORTE']

export default function Clientes() {
  const { puede } = useAuth()
  const [busqueda, setBusqueda] = useState('')
  const clientes = useDatos(() => api.clientes(busqueda), [busqueda])
  const [ventana, setVentana] = useState(null)
  const [form, setForm] = useState({})
  const [historial, setHistorial] = useState(null)
  const [mensaje, setMensaje] = useState(null)

  const guardar = async () => {
    setMensaje(null)
    try {
      if (form.id) await api.actualizarCliente(form.id, {
        nombres: form.nombres, apellidos: form.apellidos, telefono: form.telefono,
        email: form.email || null, direccion: form.direccion, ciudad: form.ciudad,
        autoriza_datos: !!form.autoriza_datos })
      else await api.crearCliente({ ...form, email: form.email || null })
      setVentana(null); setForm({}); clientes.recargar()
      setMensaje({ tipo: 'ok', texto: 'Cliente guardado.' })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const verHistorial = async (c) => {
    try { setHistorial({ cliente: c, compras: await api.comprasCliente(c.id) }) }
    catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Clientes</h1>
        <p>El cliente es la base de la garantía: sin él no hay reclamación posible.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <Panel titulo={`Registrados${clientes.datos ? ` (${clientes.datos.length})` : ''}`}
             acciones={puede('clientes.crear') &&
               <button onClick={() => { setVentana('cliente'); setForm({ tipo_documento: 'CC', ciudad: 'Bogota', autoriza_datos: true }) }}>
                 Nuevo cliente
               </button>}
             sinRelleno>
        <div className="panel-cuerpo" style={{ paddingBottom: 0 }}>
          <Campo etiqueta="Buscar">
            <input placeholder="Documento, nombre o teléfono…" value={busqueda}
                   onChange={(e) => setBusqueda(e.target.value)} />
          </Campo>
        </div>
        {clientes.cargando ? <Cargando /> : (
          <Tabla
            filas={clientes.datos ?? []}
            alHacerClic={verHistorial}
            vacio="No hay clientes con esa búsqueda."
            columnas={[
              { titulo: 'Documento', clase: 'mono', celda: (c) => `${c.tipo_documento} ${c.numero_documento}` },
              { titulo: 'Nombre', celda: (c) => (
                  <>
                    <div className="celda-principal">{c.nombres} {c.apellidos ?? ''}</div>
                    <div className="celda-sub">{c.email ?? 'sin correo'}</div>
                  </>) },
              { titulo: 'Teléfono', celda: (c) => c.telefono ?? '—' },
              { titulo: 'Ciudad', celda: (c) => c.ciudad ?? '—' },
              { titulo: 'Datos', celda: (c) => <Estado valor={c.autoriza_datos ? 'AUTORIZA' : 'SIN AUTORIZAR'}
                                                       tono={c.autoriza_datos ? 'ok' : 'alerta'} /> },
              { titulo: '', derecha: true, celda: (c) => puede('clientes.editar') && (
                  <button className="secundario pequeno"
                          onClick={(e) => { e.stopPropagation(); setVentana('cliente'); setForm(c) }}>Editar</button>) },
            ]} />
        )}
      </Panel>

      {ventana === 'cliente' && (
        <Modal titulo={form.id ? 'Editar cliente' : 'Nuevo cliente'} ancho alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.nombres || !form.numero_documento} onClick={guardar}>Guardar</button>
               </>}>
          <div className="fila-campos">
            <Campo etiqueta="Tipo de documento">
              <select value={form.tipo_documento ?? 'CC'} disabled={!!form.id}
                      onChange={(e) => setForm({ ...form, tipo_documento: e.target.value })}>
                {DOCUMENTOS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </Campo>
            <Campo etiqueta="Número">
              <input value={form.numero_documento ?? ''} disabled={!!form.id}
                     onChange={(e) => setForm({ ...form, numero_documento: e.target.value })} />
            </Campo>
            <Campo etiqueta="Nombres">
              <input value={form.nombres ?? ''} onChange={(e) => setForm({ ...form, nombres: e.target.value })} />
            </Campo>
            <Campo etiqueta="Apellidos">
              <input value={form.apellidos ?? ''} onChange={(e) => setForm({ ...form, apellidos: e.target.value })} />
            </Campo>
            <Campo etiqueta="Teléfono">
              <input value={form.telefono ?? ''} onChange={(e) => setForm({ ...form, telefono: e.target.value })} />
            </Campo>
            <Campo etiqueta="Correo">
              <input type="email" value={form.email ?? ''} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </Campo>
            <Campo etiqueta="Dirección">
              <input value={form.direccion ?? ''} onChange={(e) => setForm({ ...form, direccion: e.target.value })} />
            </Campo>
            <Campo etiqueta="Ciudad">
              <input value={form.ciudad ?? ''} onChange={(e) => setForm({ ...form, ciudad: e.target.value })} />
            </Campo>
          </div>
          <Campo ayuda="Ley 1581 de 2012: el cliente debe autorizar el tratamiento de sus datos.">
            <label style={{ display: 'flex', gap: 8, alignItems: 'center', fontWeight: 500 }}>
              <input type="checkbox" style={{ width: 'auto' }} checked={!!form.autoriza_datos}
                     onChange={(e) => setForm({ ...form, autoriza_datos: e.target.checked })} />
              Autoriza el tratamiento de sus datos personales
            </label>
          </Campo>
        </Modal>
      )}

      {historial && (
        <Modal titulo={`Compras de ${historial.cliente.nombres} ${historial.cliente.apellidos ?? ''}`} ancho
               alCerrar={() => setHistorial(null)}>
          <Tabla
            filas={historial.compras}
            vacio="Este cliente todavía no tiene compras."
            columnas={[
              { titulo: 'Factura', clase: 'mono', celda: (v) => v.numero },
              { titulo: 'Fecha', celda: (v) => fechaHora(v.fecha) },
              { titulo: 'Items', celda: (v) => v.detalles?.map((d) => d.producto?.nombre).filter(Boolean).join(', ') || '—' },
              { titulo: 'Estado', celda: (v) => <Estado valor={v.estado} /> },
              { titulo: 'Total', derecha: true, celda: (v) => <strong>{pesos(v.total)}</strong> },
            ]} />
        </Modal>
      )}
    </>
  )
}
