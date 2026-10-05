import { useState } from 'react'
import { api, pesos, fechaHora, legible } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo, Cargando, Estado, Modal, Panel, Tabla, useDatos } from '../componentes/ui.jsx'

export default function Ventas() {
  const { puede } = useAuth()
  const [filtros, setFiltros] = useState({ desde: '', hasta: '', estado: '' })
  const ventas = useDatos(() => api.ventas(filtros), [filtros.desde, filtros.hasta, filtros.estado])
  const [detalle, setDetalle] = useState(null)
  const [anulando, setAnulando] = useState(null)
  const [motivo, setMotivo] = useState('')
  const [mensaje, setMensaje] = useState(null)

  const abrir = async (v) => {
    try {
      const [completa, factura] = await Promise.all([api.venta(v.id), api.facturaDe(v.id).catch(() => null)])
      setDetalle({ ...completa, factura })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const anular = async () => {
    try {
      await api.anularVenta(anulando.id, motivo)
      setMensaje({ tipo: 'ok', texto: 'Venta anulada. Inventario y garantías revertidos.' })
      setAnulando(null); setMotivo(''); setDetalle(null); ventas.recargar()
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Ventas</h1>
        <p>Historial de facturas. Anular revierte inventario, kardex y garantías.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <Panel titulo="Filtros">
        <div className="barra-filtros">
          <Campo etiqueta="Desde">
            <input type="date" value={filtros.desde} onChange={(e) => setFiltros({ ...filtros, desde: e.target.value })} />
          </Campo>
          <Campo etiqueta="Hasta">
            <input type="date" value={filtros.hasta} onChange={(e) => setFiltros({ ...filtros, hasta: e.target.value })} />
          </Campo>
          <Campo etiqueta="Estado">
            <select value={filtros.estado} onChange={(e) => setFiltros({ ...filtros, estado: e.target.value })}>
              <option value="">Todas</option>
              <option value="COMPLETADA">Completadas</option>
              <option value="ANULADA">Anuladas</option>
            </select>
          </Campo>
          <button className="secundario" onClick={() => setFiltros({ desde: '', hasta: '', estado: '' })}>Limpiar</button>
        </div>
      </Panel>

      <Panel titulo={`Facturas${ventas.datos ? ` (${ventas.datos.length})` : ''}`} sinRelleno>
        {ventas.cargando ? <Cargando /> : (
          <Tabla
            filas={ventas.datos ?? []}
            alHacerClic={abrir}
            vacio="No hay ventas con esos filtros."
            columnas={[
              { titulo: 'Factura', clase: 'mono', celda: (v) => v.numero },
              { titulo: 'Fecha', celda: (v) => fechaHora(v.fecha) },
              { titulo: 'Cliente', celda: (v) => v.cliente
                  ? `${v.cliente.nombres} ${v.cliente.apellidos ?? ''}` : <span className="texto-tenue">Consumidor final</span> },
              { titulo: 'Items', derecha: true, celda: (v) => v.detalles?.length ?? 0 },
              { titulo: 'Estado', celda: (v) => <Estado valor={v.estado} /> },
              { titulo: 'Total', derecha: true, celda: (v) => <strong>{pesos(v.total)}</strong> },
            ]} />
        )}
      </Panel>

      {detalle && (
        <Modal titulo={`Factura ${detalle.numero}`} ancho alCerrar={() => setDetalle(null)}
               pie={<>
                 {puede('ventas.anular') && detalle.estado === 'COMPLETADA' &&
                   <button className="peligro" onClick={() => setAnulando(detalle)}>Anular venta</button>}
                 <button className="secundario" onClick={() => setDetalle(null)}>Cerrar</button>
               </>}>
          <p className="texto-tenue texto-pequeno" style={{ marginBottom: 14 }}>
            {fechaHora(detalle.fecha)} · atendido por {detalle.usuario?.nombre_completo}
            {detalle.motivo_anulacion && <> · <strong>Anulada:</strong> {detalle.motivo_anulacion}</>}
          </p>
          <Tabla
            filas={detalle.detalles}
            columnas={[
              { titulo: 'Descripción', celda: (d) => (
                  <>
                    <div className="celda-principal">{d.producto?.nombre ?? `Producto ${d.producto_id}`}</div>
                    {d.equipo_imei && <div className="celda-sub mono">IMEI {d.equipo_imei.imei}</div>}
                  </>) },
              { titulo: 'Cant.', derecha: true, celda: (d) => d.cantidad },
              { titulo: 'Unitario', derecha: true, celda: (d) => pesos(d.precio_unitario) },
              { titulo: 'IVA', derecha: true, celda: (d) => pesos(d.iva_valor) },
              { titulo: 'Total', derecha: true, celda: (d) => pesos(d.total_linea) },
            ]} />
          <div className="totales">
            <div className="linea"><span>Subtotal</span><span>{pesos(detalle.subtotal)}</span></div>
            <div className="linea"><span>IVA</span><span>{pesos(detalle.iva_total)}</span></div>
            <div className="gran-total"><span>Total</span><span>{pesos(detalle.total)}</span></div>
          </div>
          <div className="separador" />
          <div className="texto-pequeno texto-tenue">
            Pagos: {detalle.pagos?.map((p) => `${legible(p.metodo)} ${pesos(p.valor)}`).join(' · ') || '—'}
          </div>
          {detalle.factura && (
            <div className="texto-pequeno texto-tenue" style={{ marginTop: 6 }}>
              Factura electrónica {detalle.factura.numero} · CUFE <span className="mono">{detalle.factura.cufe.slice(0, 32)}…</span>
            </div>
          )}
        </Modal>
      )}

      {anulando && (
        <Modal titulo={`Anular ${anulando.numero}`} alCerrar={() => setAnulando(null)}
               pie={<>
                 <button className="secundario" onClick={() => setAnulando(null)}>Cancelar</button>
                 <button className="peligro" disabled={motivo.trim().length < 5} onClick={anular}>Confirmar anulación</button>
               </>}>
          <Aviso tipo="alerta">
            Los equipos vuelven a estar disponibles, el stock se repone y las garantías se eliminan.
          </Aviso>
          <Campo etiqueta="Motivo de la anulación" ayuda="Queda registrado en la factura y en la auditoría.">
            <input autoFocus value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          </Campo>
        </Modal>
      )}
    </>
  )
}
