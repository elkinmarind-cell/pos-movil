import { useEffect, useMemo, useState } from 'react'
import { api, pesos, legible } from '../api.js'
import { Aviso, Campo, Cargando, Modal, Panel, Tabla, Vacio, useDatos } from '../componentes/ui.jsx'

const METODOS = ['EFECTIVO', 'DEBITO', 'CREDITO', 'TRANSFERENCIA', 'NEQUI', 'DAVIPLATA']
const IVA = 19

export default function PuntoVenta() {
  const productos = useDatos(() => api.productos({ solo_disponibles: true }), [])
  const clientes = useDatos(() => api.clientes(), [])
  const turno = useDatos(() => api.miTurno(), [])

  const [busqueda, setBusqueda] = useState('')
  const [carrito, setCarrito] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [pagos, setPagos] = useState([{ metodo: 'EFECTIVO', valor: '' }])
  const [eligiendo, setEligiendo] = useState(null)   // { producto, equipos }
  const [error, setError] = useState('')
  const [factura, setFactura] = useState(null)
  const [procesando, setProcesando] = useState(false)

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    const lista = productos.datos ?? []
    if (!q) return lista.slice(0, 50)
    return lista.filter((p) =>
      p.nombre.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q) ||
      (p.codigo_barras ?? '').includes(q)).slice(0, 50)
  }, [productos.datos, busqueda])

  const totales = useMemo(() => {
    let base = 0, iva = 0, desc = 0
    for (const l of carrito) {
      const bruto = l.precio * l.cantidad
      const d = Number(l.descuento || 0)
      const b = Math.max(bruto - d, 0)
      base += b; desc += d; iva += Math.round(b * l.iva / 100)
    }
    return { base, iva, desc, total: base + iva }
  }, [carrito])

  const pagado = pagos.reduce((s, p) => s + Number(p.valor || 0), 0)
  const falta = totales.total - pagado

  useEffect(() => {
    if (pagos.length === 1 && carrito.length) {
      setPagos([{ ...pagos[0], valor: String(totales.total) }])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [totales.total])

  const agregar = async (p) => {
    setError('')
    if (p.requiere_imei) {
      const usados = carrito.filter((l) => l.imei).map((l) => l.imei)
      const equipos = (await api.equipos({ producto_id: p.id, estado: 'DISPONIBLE' }))
        .filter((e) => !usados.includes(e.imei))
      if (!equipos.length) { setError(`No quedan unidades disponibles de ${p.nombre}`); return }
      setEligiendo({ producto: p, equipos })
      return
    }
    setCarrito((prev) => {
      const ya = prev.find((l) => l.producto_id === p.id && !l.imei)
      if (ya) {
        if (ya.cantidad + 1 > p.disponibles) { setError(`Solo hay ${p.disponibles} unidades de ${p.nombre}`); return prev }
        return prev.map((l) => (l === ya ? { ...l, cantidad: l.cantidad + 1 } : l))
      }
      return [...prev, { producto_id: p.id, nombre: p.nombre, cantidad: 1,
                         precio: Number(p.precio_venta), iva: Number(p.iva_porcentaje), descuento: 0, imei: null }]
    })
  }

  const elegirEquipo = (equipo) => {
    const p = eligiendo.producto
    setCarrito((prev) => [...prev, {
      producto_id: p.id, nombre: p.nombre, cantidad: 1, precio: Number(p.precio_venta),
      iva: Number(p.iva_porcentaje), descuento: 0, imei: equipo.imei,
    }])
    setEligiendo(null)
  }

  const facturar = async () => {
    setError(''); setProcesando(true)
    try {
      const venta = await api.crearVenta({
        cliente_id: clienteId ? Number(clienteId) : null,
        items: carrito.map((l) => ({ producto_id: l.producto_id, cantidad: l.cantidad,
                                     imei: l.imei, descuento: String(l.descuento || 0) })),
        pagos: pagos.filter((p) => Number(p.valor) > 0)
                    .map((p) => ({ metodo: p.metodo, valor: String(p.valor), referencia: p.referencia || null })),
      })
      setFactura(venta)
      setCarrito([]); setPagos([{ metodo: 'EFECTIVO', valor: '' }]); setClienteId('')
      productos.recargar()
    } catch (e) { setError(e.message) } finally { setProcesando(false) }
  }

  if (productos.cargando || turno.cargando) return <Cargando />

  if (factura) {
    return (
      <>
        <Aviso tipo="ok">Venta registrada. El inventario y las garantías ya quedaron actualizados.</Aviso>
        <Panel titulo={`Factura ${factura.numero}`}
               sub={`${new Date(factura.fecha).toLocaleString('es-CO')} · atendido por ${factura.usuario?.nombre_completo ?? ''}`}
               acciones={<div className="acciones">
                 <button className="secundario" onClick={() => window.print()}>Imprimir</button>
                 <button onClick={() => setFactura(null)}>Nueva venta</button>
               </div>}>
          <Tabla
            filas={factura.detalles}
            columnas={[
              { titulo: 'Descripción', celda: (d) => (
                  <>
                    <div className="celda-principal">{d.producto?.nombre ?? `Producto ${d.producto_id}`}</div>
                    {d.equipo_imei && <div className="celda-sub mono">IMEI {d.equipo_imei.imei}</div>}
                  </>) },
              { titulo: 'Cant.', derecha: true, celda: (d) => d.cantidad },
              { titulo: 'Unitario', derecha: true, celda: (d) => pesos(d.precio_unitario) },
              { titulo: 'Desc.', derecha: true, celda: (d) => pesos(d.descuento) },
              { titulo: 'IVA', derecha: true, celda: (d) => pesos(d.iva_valor) },
              { titulo: 'Total', derecha: true, celda: (d) => <strong>{pesos(d.total_linea)}</strong> },
            ]} />
          <div className="totales">
            <div className="linea"><span>Subtotal</span><span>{pesos(factura.subtotal)}</span></div>
            <div className="linea"><span>Descuentos</span><span>− {pesos(factura.descuento_total)}</span></div>
            <div className="linea"><span>IVA</span><span>{pesos(factura.iva_total)}</span></div>
            <div className="gran-total"><span>Total</span><span>{pesos(factura.total)}</span></div>
          </div>
          <div className="separador" />
          <div className="texto-pequeno texto-tenue">
            Pagos: {factura.pagos.map((p) => `${legible(p.metodo)} ${pesos(p.valor)}`).join(' · ')}
          </div>
        </Panel>
      </>
    )
  }

  if (!turno.datos) {
    return (
      <Panel titulo="Caja cerrada">
        <Vacio icono="🏦">
          Necesitas abrir la caja antes de vender.
          <div style={{ marginTop: 14 }}>
            <a href="/caja"><button>Ir a caja</button></a>
          </div>
        </Vacio>
      </Panel>
    )
  }

  return (
    <>
      {error && <Aviso tipo="error" alCerrar={() => setError('')}>{error}</Aviso>}

      <div className="rejilla caja">
        <Panel titulo="Catálogo" sub="Busca por nombre, SKU o código de barras" sinRelleno>
          <div style={{ padding: 14, borderBottom: '1px solid var(--borde)' }}>
            <input autoFocus placeholder="Buscar producto…" value={busqueda}
                   onChange={(e) => setBusqueda(e.target.value)} />
          </div>
          <div className="lista-productos">
            {filtrados.map((p) => (
              <div key={p.id} className="producto-fila" onClick={() => agregar(p)}>
                <div className="info">
                  <div className="nombre">{p.nombre}</div>
                  <div className="meta">
                    {p.sku} · {p.requiere_imei ? 'serializado' : 'accesorio'} · {p.disponibles} disp.
                  </div>
                </div>
                <div className="precio">{pesos(p.precio_venta)}</div>
              </div>
            ))}
            {!filtrados.length && <Vacio>Sin resultados para esa búsqueda.</Vacio>}
          </div>
        </Panel>

        <Panel titulo="Factura en curso">
          <Campo etiqueta="Cliente">
            <select value={clienteId} onChange={(e) => setClienteId(e.target.value)}>
              <option value="">Consumidor final</option>
              {(clientes.datos ?? []).map((c) => (
                <option key={c.id} value={c.id}>
                  {c.numero_documento} — {c.nombres} {c.apellidos ?? ''}
                </option>))}
            </select>
          </Campo>

          {carrito.length === 0
            ? <Vacio icono="🛒">Agrega productos desde el catálogo.</Vacio>
            : (
              <table>
                <thead>
                  <tr><th>Item</th><th className="derecha">Cant.</th><th className="derecha">Desc.</th><th /></tr>
                </thead>
                <tbody>
                  {carrito.map((l, i) => (
                    <tr key={i}>
                      <td>
                        <div className="celda-principal">{l.nombre}</div>
                        <div className="celda-sub">
                          {l.imei ? <span className="mono">IMEI {l.imei}</span> : `${pesos(l.precio)} c/u`}
                        </div>
                      </td>
                      <td className="derecha">{l.cantidad}</td>
                      <td className="derecha" style={{ width: 110 }}>
                        <input type="number" min="0" value={l.descuento}
                               onChange={(e) => setCarrito((prev) => prev.map((x, j) =>
                                 j === i ? { ...x, descuento: Math.max(0, Number(e.target.value) || 0) } : x))} />
                      </td>
                      <td className="derecha">
                        <button className="fantasma pequeno"
                                onClick={() => setCarrito((prev) => prev.filter((_, j) => j !== i))}>✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

          <div className="totales">
            <div className="linea"><span>Subtotal</span><span>{pesos(totales.base)}</span></div>
            <div className="linea"><span>Descuentos</span><span>− {pesos(totales.desc)}</span></div>
            <div className="linea"><span>IVA ({IVA}%)</span><span>{pesos(totales.iva)}</span></div>
            <div className="gran-total"><span>Total</span><span>{pesos(totales.total)}</span></div>
          </div>

          <div className="separador" />
          <h3 style={{ marginBottom: 10 }}>Pago</h3>
          {pagos.map((p, i) => (
            <div className="fila-campos" key={i}>
              <Campo etiqueta={i === 0 ? 'Método' : ' '}>
                <select value={p.metodo}
                        onChange={(e) => setPagos((prev) => prev.map((x, j) => j === i ? { ...x, metodo: e.target.value } : x))}>
                  {METODOS.map((m) => <option key={m} value={m}>{legible(m)}</option>)}
                </select>
              </Campo>
              <Campo etiqueta={i === 0 ? 'Valor' : ' '}>
                <input type="number" min="0" value={p.valor}
                       onChange={(e) => setPagos((prev) => prev.map((x, j) => j === i ? { ...x, valor: e.target.value } : x))} />
              </Campo>
            </div>
          ))}
          <div className="acciones">
            <button className="fantasma pequeno"
                    onClick={() => setPagos((prev) => [...prev, { metodo: 'DEBITO', valor: String(Math.max(falta, 0)) }])}>
              + Dividir el pago
            </button>
            {pagos.length > 1 && (
              <button className="fantasma pequeno" onClick={() => setPagos((prev) => prev.slice(0, -1))}>
                Quitar el último
              </button>
            )}
          </div>
          {carrito.length > 0 && falta !== 0 && (
            <p className="texto-pequeno" style={{ color: 'var(--alerta)', marginTop: 6 }}>
              {falta > 0 ? `Faltan ${pesos(falta)} por cubrir` : `Hay ${pesos(-falta)} de más`}
            </p>
          )}

          <div style={{ marginTop: 14 }}>
            <button className="ancho" disabled={!carrito.length || procesando || falta !== 0} onClick={facturar}>
              {procesando ? 'Procesando…' : `Facturar ${pesos(totales.total)}`}
            </button>
          </div>
        </Panel>
      </div>

      {eligiendo && (
        <Modal titulo={`Selecciona el equipo — ${eligiendo.producto.nombre}`} ancho
               alCerrar={() => setEligiendo(null)}>
          <Tabla
            filas={eligiendo.equipos}
            alHacerClic={elegirEquipo}
            columnas={[
              { titulo: 'IMEI', clase: 'mono', celda: (e) => e.imei },
              { titulo: 'Color', celda: (e) => e.color ?? '—' },
              { titulo: 'Almacenamiento', celda: (e) => e.almacenamiento_gb ? `${e.almacenamiento_gb} GB` : '—' },
              { titulo: '', derecha: true, celda: () => <button className="pequeno">Elegir</button> },
            ]} />
        </Modal>
      )}
    </>
  )
}
