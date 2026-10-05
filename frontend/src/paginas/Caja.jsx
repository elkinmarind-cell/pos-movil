import { useState } from 'react'
import { api, pesos, fechaHora } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo, Cargando, Estado, Kpi, Modal, Panel, Tabla, Vacio, useDatos } from '../componentes/ui.jsx'

export default function Caja() {
  const { puede } = useAuth()
  const turno = useDatos(() => api.miTurno(), [])
  const cajas = useDatos(() => api.cajas(), [])
  const historial = useDatos(() => api.turnos(), [])
  const [mensaje, setMensaje] = useState(null)
  const [ventana, setVentana] = useState(null)   // 'abrir' | 'cerrar' | 'movimiento'
  const [form, setForm] = useState({})
  const [arqueo, setArqueo] = useState(null)

  const refrescar = () => { turno.recargar(); cajas.recargar(); historial.recargar(); setArqueo(null) }

  const cargarArqueo = async () => {
    try { setArqueo(await api.arqueo()) } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const ejecutar = async (accion) => {
    setMensaje(null)
    try {
      await accion()
      setVentana(null); setForm({}); refrescar()
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  if (turno.cargando || cajas.cargando) return <Cargando />

  const abierto = turno.datos

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Caja</h1>
        <p>Un turno abierto es obligatorio para registrar ventas y recibir dinero.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      {abierto ? (
        <>
          <div className="rejilla c4" style={{ marginBottom: 18 }}>
            <Kpi etiqueta="Estado" valor="Caja abierta" tono="exito"
                 nota={`desde ${fechaHora(abierto.apertura)}`} />
            <Kpi etiqueta="Base inicial" valor={pesos(abierto.base_inicial)} />
            <Kpi etiqueta="Efectivo esperado" tono="acento"
                 valor={arqueo ? pesos(arqueo.efectivo_esperado) : '—'}
                 nota={arqueo ? `recaudo total ${pesos(arqueo.recaudo_total)}` : 'calcula el arqueo'} />
            <Kpi etiqueta="Terminal" valor={arqueo?.caja ?? `Caja ${abierto.caja_id}`}
                 nota={arqueo?.cajero} />
          </div>

          <Panel titulo="Operaciones del turno">
            <div className="acciones">
              <button className="secundario" onClick={cargarArqueo}>Calcular arqueo</button>
              {puede('caja.movimiento') &&
                <button className="secundario" onClick={() => { setVentana('movimiento'); setForm({ tipo: 'EGRESO' }) }}>
                  Registrar ingreso o egreso
                </button>}
              {puede('caja.cerrar') &&
                <button className="peligro" onClick={async () => { await cargarArqueo(); setVentana('cerrar') }}>
                  Cerrar caja
                </button>}
            </div>
            {arqueo && (
              <>
                <div className="separador" />
                <div className="totales">
                  <div className="linea"><span>Base inicial</span><span>{pesos(arqueo.base_inicial)}</span></div>
                  <div className="linea"><span>Efectivo recibido en ventas y abonos</span><span>{pesos(arqueo.efectivo_ventas)}</span></div>
                  <div className="linea"><span>Otros movimientos de caja</span><span>{pesos(arqueo.otros_movimientos)}</span></div>
                  <div className="gran-total"><span>Efectivo esperado</span><span>{pesos(arqueo.efectivo_esperado)}</span></div>
                </div>
                <p className="texto-tenue texto-pequeno" style={{ marginTop: 8 }}>
                  El recaudo total del turno, incluyendo tarjetas y transferencias, es {pesos(arqueo.recaudo_total)}.
                </p>
              </>
            )}
          </Panel>
        </>
      ) : (
        <Panel titulo="No tienes caja abierta">
          <Vacio icono="🏦">
            Para vender necesitas abrir un turno con su base inicial.
            <div style={{ marginTop: 14 }}>
              {puede('caja.abrir')
                ? <button onClick={() => { setVentana('abrir'); setForm({ caja_id: '', base_inicial: '' }) }}>
                    Abrir caja
                  </button>
                : <span className="texto-tenue">Tu rol no tiene permiso para abrir caja.</span>}
            </div>
          </Vacio>
        </Panel>
      )}

      <Panel titulo="Terminales" sinRelleno>
        <Tabla
          filas={cajas.datos ?? []}
          columnas={[
            { titulo: 'Caja', celda: (c) => <span className="celda-principal">{c.nombre}</span> },
            { titulo: 'Ubicación', celda: (c) => c.ubicacion ?? '—' },
            { titulo: 'Estado', celda: (c) => <Estado valor={c.ocupada ? 'ABIERTO' : 'CERRADO'} /> },
          ]} />
      </Panel>

      <Panel titulo="Historial de turnos" sinRelleno>
        <Tabla
          filas={historial.datos ?? []}
          vacio="Todavía no hay turnos registrados."
          columnas={[
            { titulo: 'Apertura', celda: (t) => fechaHora(t.apertura) },
            { titulo: 'Cierre', celda: (t) => fechaHora(t.cierre) },
            { titulo: 'Base', derecha: true, celda: (t) => pesos(t.base_inicial) },
            { titulo: 'Esperado', derecha: true, celda: (t) => t.efectivo_esperado ? pesos(t.efectivo_esperado) : '—' },
            { titulo: 'Contado', derecha: true, celda: (t) => t.efectivo_contado ? pesos(t.efectivo_contado) : '—' },
            { titulo: 'Diferencia', derecha: true,
              celda: (t) => t.diferencia == null ? '—'
                : <Estado valor={pesos(t.diferencia)} tono={Number(t.diferencia) === 0 ? 'ok' : 'peligro'} /> },
            { titulo: 'Estado', celda: (t) => <Estado valor={t.estado} /> },
          ]} />
      </Panel>

      {ventana === 'abrir' && (
        <Modal titulo="Abrir caja" alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.caja_id || form.base_inicial === ''}
                         onClick={() => ejecutar(() => api.abrirCaja({ caja_id: Number(form.caja_id), base_inicial: form.base_inicial }))}>
                   Abrir turno
                 </button>
               </>}>
          <Campo etiqueta="Terminal">
            <select value={form.caja_id} onChange={(e) => setForm({ ...form, caja_id: e.target.value })}>
              <option value="">Selecciona…</option>
              {(cajas.datos ?? []).filter((c) => !c.ocupada && c.activa)
                .map((c) => <option key={c.id} value={c.id}>{c.nombre} — {c.ubicacion}</option>)}
            </select>
          </Campo>
          <Campo etiqueta="Base inicial" ayuda="Dinero con el que arranca el turno.">
            <input type="number" min="0" value={form.base_inicial}
                   onChange={(e) => setForm({ ...form, base_inicial: e.target.value })} />
          </Campo>
        </Modal>
      )}

      {ventana === 'cerrar' && (
        <Modal titulo="Cerrar caja" alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button className="peligro" disabled={form.efectivo_contado === undefined || form.efectivo_contado === ''}
                         onClick={() => ejecutar(() => api.cerrarCaja({ efectivo_contado: form.efectivo_contado }))}>
                   Cerrar turno
                 </button>
               </>}>
          {arqueo && (
            <Aviso tipo="info">
              El sistema espera encontrar <strong>{pesos(arqueo.efectivo_esperado)}</strong> en efectivo.
            </Aviso>
          )}
          <Campo etiqueta="Efectivo contado" ayuda="Cuenta el dinero físico y escribe el total.">
            <input type="number" min="0" autoFocus value={form.efectivo_contado ?? ''}
                   onChange={(e) => setForm({ ...form, efectivo_contado: e.target.value })} />
          </Campo>
          {arqueo && form.efectivo_contado !== undefined && form.efectivo_contado !== '' && (
            <p className="texto-pequeno">
              Diferencia: <strong>{pesos(Number(form.efectivo_contado) - Number(arqueo.efectivo_esperado))}</strong>
            </p>
          )}
        </Modal>
      )}

      {ventana === 'movimiento' && (
        <Modal titulo="Movimiento de caja" alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.concepto || !form.valor}
                         onClick={() => ejecutar(() => api.movimientoCaja({
                           tipo: form.tipo, concepto: form.concepto, valor: form.valor }))}>
                   Registrar
                 </button>
               </>}>
          <div className="fila-campos">
            <Campo etiqueta="Tipo">
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                <option value="EGRESO">Egreso (sale dinero)</option>
                <option value="INGRESO">Ingreso (entra dinero)</option>
              </select>
            </Campo>
            <Campo etiqueta="Valor">
              <input type="number" min="1" value={form.valor ?? ''}
                     onChange={(e) => setForm({ ...form, valor: e.target.value })} />
            </Campo>
          </div>
          <Campo etiqueta="Concepto">
            <input value={form.concepto ?? ''} placeholder="Compra de rollos de factura"
                   onChange={(e) => setForm({ ...form, concepto: e.target.value })} />
          </Campo>
        </Modal>
      )}
    </>
  )
}
