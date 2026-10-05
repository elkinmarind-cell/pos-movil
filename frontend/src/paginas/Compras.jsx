import { useState } from 'react'
import { api, pesos, fecha, numero } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo, Cargando, Estado, Modal, Panel, Tabla, Vacio, useDatos } from '../componentes/ui.jsx'

export default function Compras() {
  const { puede } = useAuth()
  const ordenes = useDatos(() => api.ordenesCompra(), [])
  const proveedores = useDatos(() => api.proveedores(), [])
  const productos = useDatos(() => api.productos(), [])
  const [ventana, setVentana] = useState(null)
  const [nueva, setNueva] = useState({ proveedor_id: '', items: [] })
  const [recepcion, setRecepcion] = useState(null)
  const [mensaje, setMensaje] = useState(null)

  const crear = async () => {
    setMensaje(null)
    try {
      await api.crearOrdenCompra({
        proveedor_id: Number(nueva.proveedor_id),
        items: nueva.items.map((i) => ({ producto_id: Number(i.producto_id), cantidad: Number(i.cantidad),
                                         costo_unitario: String(i.costo_unitario) })),
      })
      setVentana(null); setNueva({ proveedor_id: '', items: [] }); ordenes.recargar()
      setMensaje({ tipo: 'ok', texto: 'Orden de compra creada.' })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const recibir = async () => {
    setMensaje(null)
    try {
      await api.recibirCompra(recepcion.orden.id, {
        items: recepcion.lineas.filter((l) => Number(l.cantidad) > 0).map((l) => ({
          detalle_id: l.detalle_id, cantidad: Number(l.cantidad),
          imeis: l.imeis.split(/[\s,;]+/).map((s) => s.trim()).filter(Boolean),
        })),
      })
      setRecepcion(null); ordenes.recargar(); productos.recargar()
      setMensaje({ tipo: 'ok', texto: 'Mercancía recibida e ingresada al inventario.' })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const abrirRecepcion = async (orden) => {
    const completa = await api.ordenCompra(orden.id)
    setRecepcion({
      orden: completa,
      lineas: completa.detalles.map((d) => ({
        detalle_id: d.id, nombre: d.producto?.nombre ?? `Producto ${d.producto_id}`,
        requiere_imei: d.producto?.requiere_imei,
        pendiente: d.cantidad_pedida - d.cantidad_recibida,
        cantidad: d.cantidad_pedida - d.cantidad_recibida, imeis: '',
      })),
    })
  }

  const totalNueva = nueva.items.reduce((s, i) => s + Number(i.cantidad || 0) * Number(i.costo_unitario || 0), 0)

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Compras</h1>
        <p>Al recibir la mercancía, cada equipo entra con su IMEI y queda en el kardex.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <Panel titulo="Órdenes de compra"
             acciones={puede('compras.crear') &&
               <button onClick={() => { setVentana('nueva'); setNueva({ proveedor_id: '', items: [{ producto_id: '', cantidad: 1, costo_unitario: '' }] }) }}>
                 Nueva orden
               </button>}
             sinRelleno>
        {ordenes.cargando ? <Cargando /> : (
          <Tabla
            filas={ordenes.datos ?? []}
            vacio="Todavía no hay órdenes de compra."
            columnas={[
              { titulo: 'Número', clase: 'mono', celda: (o) => o.numero },
              { titulo: 'Fecha', celda: (o) => fecha(o.fecha) },
              { titulo: 'Renglones', derecha: true, celda: (o) => o.detalles?.length ?? 0 },
              { titulo: 'Estado', celda: (o) => <Estado valor={o.estado} /> },
              { titulo: 'Total', derecha: true, celda: (o) => <strong>{pesos(o.total)}</strong> },
              { titulo: '', derecha: true, celda: (o) => puede('compras.recibir') &&
                  ['ENVIADA', 'RECIBIDA_PARCIAL', 'BORRADOR'].includes(o.estado) && (
                    <button className="secundario pequeno" onClick={() => abrirRecepcion(o)}>Recibir</button>) },
            ]} />
        )}
      </Panel>

      {ventana === 'nueva' && (
        <Modal titulo="Nueva orden de compra" ancho alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!nueva.proveedor_id || !nueva.items.some((i) => i.producto_id && i.cantidad)}
                         onClick={crear}>Crear orden por {pesos(totalNueva)}</button>
               </>}>
          <Campo etiqueta="Proveedor">
            <select value={nueva.proveedor_id} onChange={(e) => setNueva({ ...nueva, proveedor_id: e.target.value })}>
              <option value="">Selecciona…</option>
              {(proveedores.datos ?? []).map((p) => <option key={p.id} value={p.id}>{p.razon_social}</option>)}
            </select>
          </Campo>
          {nueva.items.map((item, i) => (
            <div className="fila-campos" key={i}>
              <Campo etiqueta={i === 0 ? 'Producto' : ' '}>
                <select value={item.producto_id}
                        onChange={(e) => setNueva({ ...nueva, items: nueva.items.map((x, j) =>
                          j === i ? { ...x, producto_id: e.target.value,
                                      costo_unitario: (productos.datos ?? []).find((p) => String(p.id) === e.target.value)?.precio_costo ?? x.costo_unitario } : x) })}>
                  <option value="">Selecciona…</option>
                  {(productos.datos ?? []).map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
                </select>
              </Campo>
              <Campo etiqueta={i === 0 ? 'Cantidad' : ' '}>
                <input type="number" min="1" value={item.cantidad}
                       onChange={(e) => setNueva({ ...nueva, items: nueva.items.map((x, j) => j === i ? { ...x, cantidad: e.target.value } : x) })} />
              </Campo>
              <Campo etiqueta={i === 0 ? 'Costo unitario' : ' '}>
                <input type="number" min="1" value={item.costo_unitario}
                       onChange={(e) => setNueva({ ...nueva, items: nueva.items.map((x, j) => j === i ? { ...x, costo_unitario: e.target.value } : x) })} />
              </Campo>
            </div>
          ))}
          <button className="fantasma pequeno"
                  onClick={() => setNueva({ ...nueva, items: [...nueva.items, { producto_id: '', cantidad: 1, costo_unitario: '' }] })}>
            + Agregar renglón
          </button>
        </Modal>
      )}

      {recepcion && (
        <Modal titulo={`Recibir ${recepcion.orden.numero}`} ancho alCerrar={() => setRecepcion(null)}
               pie={<>
                 <button className="secundario" onClick={() => setRecepcion(null)}>Cancelar</button>
                 <button onClick={recibir}>Confirmar recepción</button>
               </>}>
          <Aviso tipo="info">
            Los equipos serializados exigen un IMEI por unidad. Sepáralos por espacios, comas o saltos de línea.
          </Aviso>
          {recepcion.lineas.map((l, i) => (
            <div key={l.detalle_id} style={{ borderBottom: '1px solid var(--borde)', paddingBottom: 12, marginBottom: 12 }}>
              <div className="celda-principal">{l.nombre}</div>
              <div className="celda-sub" style={{ marginBottom: 8 }}>
                pendientes por recibir: {numero(l.pendiente)}
              </div>
              <div className="fila-campos">
                <Campo etiqueta="Cantidad a recibir">
                  <input type="number" min="0" max={l.pendiente} value={l.cantidad}
                         onChange={(e) => setRecepcion({ ...recepcion, lineas: recepcion.lineas.map((x, j) =>
                           j === i ? { ...x, cantidad: e.target.value } : x) })} />
                </Campo>
              </div>
              {l.requiere_imei && (
                <Campo etiqueta="IMEI de las unidades">
                  <textarea rows={2} className="mono" value={l.imeis}
                            onChange={(e) => setRecepcion({ ...recepcion, lineas: recepcion.lineas.map((x, j) =>
                              j === i ? { ...x, imeis: e.target.value } : x) })} />
                </Campo>
              )}
            </div>
          ))}
          {!recepcion.lineas.length && <Vacio>Esta orden no tiene renglones pendientes.</Vacio>}
        </Modal>
      )}
    </>
  )
}
