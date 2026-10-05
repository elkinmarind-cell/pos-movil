import { useState } from 'react'
import { api, pesos, fecha, fechaHora, legible } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo, Cargando, Estado, Modal, Panel, Tabla, useDatos } from '../componentes/ui.jsx'

const ESTADOS_SERVICIO = ['RECIBIDO', 'DIAGNOSTICO', 'REPARACION', 'LISTO', 'ENTREGADO']

export default function Posventa() {
  const { puede } = useAuth()
  const [pestana, setPestana] = useState('garantias')
  const garantias = useDatos(() => api.garantias(), [])
  const servicio = useDatos(() => api.ordenesServicio(), [])
  const apartados = useDatos(() => api.apartados(), [])
  const devoluciones = useDatos(() => api.devoluciones(), [])
  const [ventana, setVentana] = useState(null)
  const [form, setForm] = useState({})
  const [mensaje, setMensaje] = useState(null)

  const ejecutar = async (accion, exito) => {
    setMensaje(null)
    try {
      await accion()
      setVentana(null); setForm({})
      garantias.recargar(); servicio.recargar(); apartados.recargar(); devoluciones.recargar()
      setMensaje({ tipo: 'ok', texto: exito })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const PESTANAS = [
    ['garantias', `Garantías${garantias.datos ? ` (${garantias.datos.length})` : ''}`],
    ['servicio', `Servicio técnico${servicio.datos ? ` (${servicio.datos.length})` : ''}`],
    ['apartados', `Apartados${apartados.datos ? ` (${apartados.datos.length})` : ''}`],
    ['devoluciones', 'Devoluciones'],
  ]

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Posventa</h1>
        <p>Garantías del Estatuto del Consumidor, servicio técnico, apartados y devoluciones.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <section className="panel">
        <div className="pestanas">
          {PESTANAS.map(([k, t]) => (
            <button key={k} className={`pestana${pestana === k ? ' activa' : ''}`} onClick={() => setPestana(k)}>{t}</button>
          ))}
        </div>

        {pestana === 'garantias' && (garantias.cargando ? <Cargando /> : (
          <Tabla
            filas={garantias.datos ?? []}
            vacio="No hay garantías registradas."
            columnas={[
              { titulo: '#', celda: (g) => g.id },
              { titulo: 'Inicio', celda: (g) => fecha(g.fecha_inicio) },
              { titulo: 'Vence', celda: (g) => fecha(g.fecha_fin) },
              { titulo: 'Días', derecha: true, celda: (g) => g.dias_restantes },
              { titulo: 'Meses', derecha: true, celda: (g) => g.meses },
              { titulo: 'Estado', celda: (g) => <Estado valor={g.estado} /> },
              { titulo: '', derecha: true, celda: (g) => g.estado === 'VIGENTE' && puede('garantias.reclamar') && (
                  <button className="secundario pequeno"
                          onClick={() => { setVentana('reclamar'); setForm({ garantia: g, falla: '' }) }}>
                    Reclamar
                  </button>) },
            ]} />
        ))}

        {pestana === 'servicio' && (servicio.cargando ? <Cargando /> : (
          <>
            <div className="panel-cuerpo" style={{ paddingBottom: 0 }}>
              {puede('servicio.crear') &&
                <button onClick={() => { setVentana('servicio'); setForm({}) }}>Recibir equipo</button>}
            </div>
            <Tabla
              filas={servicio.datos ?? []}
              vacio="No hay órdenes de servicio."
              columnas={[
                { titulo: 'Orden', clase: 'mono', celda: (o) => o.numero },
                { titulo: 'Equipo', celda: (o) => o.equipo_externo ?? `IMEI ${o.equipo_imei_id ?? '—'}` },
                { titulo: 'Falla', celda: (o) => <span className="texto-pequeno">{o.falla_reportada}</span> },
                { titulo: 'Garantía', celda: (o) => o.garantia_id
                    ? <Estado valor="POR GARANTIA" tono="info" /> : <span className="texto-tenue">cobrada</span> },
                { titulo: 'Mano de obra', derecha: true, celda: (o) => pesos(o.costo_mano_obra) },
                { titulo: 'Ingreso', celda: (o) => fechaHora(o.fecha_ingreso) },
                { titulo: 'Estado', celda: (o) => <Estado valor={o.estado} /> },
                { titulo: '', derecha: true, celda: (o) => o.estado !== 'ENTREGADO' && puede('servicio.cerrar', 'servicio.crear') && (
                    <button className="secundario pequeno"
                            onClick={() => { setVentana('avanzar'); setForm({ orden: o, estado: o.estado, diagnostico: o.diagnostico ?? '' }) }}>
                      Actualizar
                    </button>) },
              ]} />
          </>
        ))}

        {pestana === 'apartados' && (apartados.cargando ? <Cargando /> : (
          <Tabla
            filas={apartados.datos ?? []}
            vacio="No hay apartados."
            columnas={[
              { titulo: '#', celda: (a) => a.id },
              { titulo: 'Cliente', celda: (a) => a.cliente ? `${a.cliente.nombres} ${a.cliente.apellidos ?? ''}` : '—' },
              { titulo: 'Equipo', clase: 'mono', celda: (a) => a.equipo_imei?.imei ?? '—' },
              { titulo: 'Valor', derecha: true, celda: (a) => pesos(a.valor_total) },
              { titulo: 'Abonado', derecha: true,
                celda: (a) => pesos(Number(a.valor_total) - Number(a.saldo_pendiente)) },
              { titulo: 'Saldo', derecha: true, celda: (a) => <strong>{pesos(a.saldo_pendiente)}</strong> },
              { titulo: 'Vence', celda: (a) => fecha(a.fecha_limite) },
              { titulo: 'Estado', celda: (a) => <Estado valor={a.estado} /> },
              { titulo: '', derecha: true, celda: (a) => a.estado === 'VIGENTE' && puede('ventas.crear') && (
                  <button className="secundario pequeno"
                          onClick={() => { setVentana('abono'); setForm({ apartado: a, valor: '', metodo: 'EFECTIVO' }) }}>
                    Abonar
                  </button>) },
            ]} />
        ))}

        {pestana === 'devoluciones' && (devoluciones.cargando ? <Cargando /> : (
          <Tabla
            filas={devoluciones.datos ?? []}
            vacio="No hay devoluciones registradas."
            columnas={[
              { titulo: '#', celda: (d) => d.id },
              { titulo: 'Venta', celda: (d) => `#${d.venta_id}` },
              { titulo: 'Fecha', celda: (d) => fechaHora(d.fecha) },
              { titulo: 'Motivo', celda: (d) => d.motivo },
              { titulo: 'Reembolso', celda: (d) => <Estado valor={d.tipo_reembolso} tono="info" /> },
              { titulo: 'Total', derecha: true, celda: (d) => <strong>{pesos(d.total)}</strong> },
            ]} />
        ))}
      </section>

      {ventana === 'reclamar' && (
        <Modal titulo={`Reclamar garantía #${form.garantia.id}`} alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={(form.falla ?? '').trim().length < 5}
                         onClick={() => ejecutar(() => api.reclamarGarantia(form.garantia.id, form.falla),
                                                 'Reclamación abierta: se creó la orden de servicio.')}>
                   Abrir reclamación
                 </button>
               </>}>
          <Aviso tipo="info">
            Se creará una orden de servicio técnico sin costo para el cliente y el equipo pasará a estado «en servicio».
          </Aviso>
          <Campo etiqueta="Falla reportada por el cliente">
            <textarea rows={3} autoFocus value={form.falla ?? ''}
                      onChange={(e) => setForm({ ...form, falla: e.target.value })} />
          </Campo>
        </Modal>
      )}

      {ventana === 'avanzar' && (
        <Modal titulo={`Orden ${form.orden.numero}`} alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button onClick={() => ejecutar(() => api.actualizarOrdenServicio(form.orden.id, {
                   estado: form.estado, diagnostico: form.diagnostico || null,
                   costo_mano_obra: form.costo_mano_obra !== undefined ? String(form.costo_mano_obra) : undefined,
                 }), 'Orden actualizada.')}>Guardar</button>
               </>}>
          <Campo etiqueta="Estado">
            <select value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
              {ESTADOS_SERVICIO.map((e) => <option key={e} value={e}>{legible(e)}</option>)}
            </select>
          </Campo>
          <Campo etiqueta="Diagnóstico">
            <textarea rows={3} value={form.diagnostico ?? ''}
                      onChange={(e) => setForm({ ...form, diagnostico: e.target.value })} />
          </Campo>
          <Campo etiqueta="Costo de mano de obra">
            <input type="number" min="0" value={form.costo_mano_obra ?? form.orden.costo_mano_obra}
                   onChange={(e) => setForm({ ...form, costo_mano_obra: e.target.value })} />
          </Campo>
        </Modal>
      )}

      {ventana === 'servicio' && <ModalRecibirEquipo cerrar={() => setVentana(null)} ejecutar={ejecutar} />}

      {ventana === 'abono' && (
        <Modal titulo={`Abono al apartado #${form.apartado.id}`} alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.valor}
                         onClick={() => ejecutar(() => api.abonarApartado(form.apartado.id, {
                           valor: String(form.valor), metodo: form.metodo }), 'Abono registrado.')}>
                   Registrar abono
                 </button>
               </>}>
          <Aviso tipo="info">Saldo pendiente: <strong>{pesos(form.apartado.saldo_pendiente)}</strong></Aviso>
          <div className="fila-campos">
            <Campo etiqueta="Valor">
              <input type="number" min="1" autoFocus value={form.valor ?? ''}
                     onChange={(e) => setForm({ ...form, valor: e.target.value })} />
            </Campo>
            <Campo etiqueta="Método">
              <select value={form.metodo} onChange={(e) => setForm({ ...form, metodo: e.target.value })}>
                {['EFECTIVO', 'DEBITO', 'CREDITO', 'TRANSFERENCIA', 'NEQUI', 'DAVIPLATA']
                  .map((m) => <option key={m} value={m}>{legible(m)}</option>)}
              </select>
            </Campo>
          </div>
        </Modal>
      )}
    </>
  )
}

function ModalRecibirEquipo({ cerrar, ejecutar }) {
  const clientes = useDatos(() => api.clientes(), [])
  const [f, setF] = useState({ cliente_id: '', imei: '', equipo_externo: '', falla_reportada: '', costo_mano_obra: 0 })
  return (
    <Modal titulo="Recibir equipo en servicio técnico" ancho alCerrar={cerrar}
           pie={<>
             <button className="secundario" onClick={cerrar}>Cancelar</button>
             <button disabled={!f.cliente_id || f.falla_reportada.length < 5 || (!f.imei && !f.equipo_externo)}
                     onClick={() => ejecutar(() => api.crearOrdenServicio({
                       cliente_id: Number(f.cliente_id), imei: f.imei || null,
                       equipo_externo: f.equipo_externo || null, falla_reportada: f.falla_reportada,
                       costo_mano_obra: String(f.costo_mano_obra || 0),
                     }), 'Orden de servicio creada.')}>Crear orden</button>
           </>}>
      <Campo etiqueta="Cliente">
        <select value={f.cliente_id} onChange={(e) => setF({ ...f, cliente_id: e.target.value })}>
          <option value="">Selecciona…</option>
          {(clientes.datos ?? []).map((c) => (
            <option key={c.id} value={c.id}>{c.numero_documento} — {c.nombres} {c.apellidos ?? ''}</option>))}
        </select>
      </Campo>
      <div className="fila-campos">
        <Campo etiqueta="IMEI (si se vendió aquí)">
          <input className="mono" maxLength={15} value={f.imei}
                 onChange={(e) => setF({ ...f, imei: e.target.value.replace(/\D/g, '') })} />
        </Campo>
        <Campo etiqueta="Equipo externo" ayuda="Si el equipo no salió de esta tienda.">
          <input value={f.equipo_externo} placeholder="Samsung A34 del cliente"
                 onChange={(e) => setF({ ...f, equipo_externo: e.target.value })} />
        </Campo>
        <Campo etiqueta="Mano de obra estimada">
          <input type="number" min="0" value={f.costo_mano_obra}
                 onChange={(e) => setF({ ...f, costo_mano_obra: e.target.value })} />
        </Campo>
      </div>
      <Campo etiqueta="Falla reportada">
        <textarea rows={3} value={f.falla_reportada}
                  onChange={(e) => setF({ ...f, falla_reportada: e.target.value })} />
      </Campo>
    </Modal>
  )
}
