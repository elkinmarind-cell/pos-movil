import { useEffect, useMemo, useState } from 'react'
import { api, pesos } from '../api.js'

export default function Caja() {
  const [productos, setProductos] = useState([])
  const [clientes, setClientes] = useState([])
  const [busqueda, setBusqueda] = useState('')
  const [carrito, setCarrito] = useState([])
  const [clienteId, setClienteId] = useState('')
  const [metodoPago, setMetodoPago] = useState('efectivo')
  const [imeiPendiente, setImeiPendiente] = useState(null)   // producto que espera IMEI
  const [imeisDisponibles, setImeisDisponibles] = useState([])
  const [error, setError] = useState('')
  const [factura, setFactura] = useState(null)
  const [procesando, setProcesando] = useState(false)

  const cargar = () => {
    api.productos({ solo_disponibles: 'true' }).then(setProductos).catch((e) => setError(e.message))
  }
  useEffect(() => { cargar(); api.clientes().then(setClientes).catch(() => {}) }, [])

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase()
    if (!q) return productos
    return productos.filter((p) => p.nombre.toLowerCase().includes(q) || p.sku.toLowerCase().includes(q))
  }, [productos, busqueda])

  const agregar = async (producto) => {
    setError('')
    if (producto.requiere_imei) {
      const lista = await api.imeis({ producto_id: producto.id, estado: 'disponible' })
      const usados = carrito.filter((l) => l.imei).map((l) => l.imei)
      const libres = lista.filter((e) => !usados.includes(e.imei))
      if (libres.length === 0) { setError(`No quedan equipos disponibles de ${producto.nombre}`); return }
      setImeisDisponibles(libres)
      setImeiPendiente(producto)
      return
    }
    setCarrito((prev) => {
      const existente = prev.find((l) => l.producto_id === producto.id && !l.imei)
      if (existente) {
        if (existente.cantidad + 1 > producto.disponibles) { setError(`Solo hay ${producto.disponibles} unidades`); return prev }
        return prev.map((l) => (l === existente ? { ...l, cantidad: l.cantidad + 1 } : l))
      }
      return [...prev, {
        producto_id: producto.id, nombre: producto.nombre, cantidad: 1,
        precio: Number(producto.precio_venta), iva: Number(producto.iva_porcentaje),
        descuento: 0, imei: null,
      }]
    })
  }

  const confirmarImei = (imei) => {
    const p = imeiPendiente
    setCarrito((prev) => [...prev, {
      producto_id: p.id, nombre: `${p.nombre} - IMEI ${imei}`, cantidad: 1,
      precio: Number(p.precio_venta), iva: Number(p.iva_porcentaje), descuento: 0, imei,
    }])
    setImeiPendiente(null); setImeisDisponibles([])
  }

  const quitar = (indice) => setCarrito((prev) => prev.filter((_, i) => i !== indice))

  const cambiarDescuento = (indice, valor) =>
    setCarrito((prev) => prev.map((l, i) => (i === indice ? { ...l, descuento: Math.max(0, Number(valor) || 0) } : l)))

  const totales = useMemo(() => {
    let subtotal = 0, iva = 0, descuentos = 0
    for (const l of carrito) {
      const bruto = l.precio * l.cantidad
      const base = Math.max(bruto - l.descuento, 0)
      subtotal += base
      descuentos += l.descuento
      iva += base * (l.iva / 100)
    }
    return { subtotal, iva: Math.round(iva), descuentos, total: subtotal + Math.round(iva) }
  }, [carrito])

  const facturar = async () => {
    setError(''); setProcesando(true)
    try {
      const venta = await api.crearVenta({
        cliente_id: clienteId ? Number(clienteId) : null,
        metodo_pago: metodoPago,
        items: carrito.map((l) => ({
          producto_id: l.producto_id, cantidad: l.cantidad,
          imei: l.imei, descuento: String(l.descuento),
        })),
      })
      setFactura(venta)
      setCarrito([])
      cargar()
    } catch (e) {
      setError(e.message)
    } finally {
      setProcesando(false)
    }
  }

  if (factura) {
    return (
      <>
        <h1>Venta registrada</h1>
        <p className="descripcion">Factura {factura.numero_factura}</p>
        <div className="mensaje ok">La venta se registro correctamente y el inventario ya fue actualizado.</div>
        <div className="panel">
          <h2>{factura.numero_factura}</h2>
          <p className="descripcion">
            {new Date(factura.fecha).toLocaleString('es-CO')} &middot; Atendido por {factura.usuario.nombre_completo}
            {factura.cliente && ` · Cliente: ${factura.cliente.nombres} ${factura.cliente.apellidos || ''}`}
          </p>
          <table>
            <thead>
              <tr><th>Descripcion</th><th className="derecha">Cant.</th><th className="derecha">Unitario</th>
                  <th className="derecha">IVA</th><th className="derecha">Total</th></tr>
            </thead>
            <tbody>
              {factura.detalles.map((d) => (
                <tr key={d.id}>
                  <td>{d.descripcion}</td>
                  <td className="derecha">{d.cantidad}</td>
                  <td className="derecha">{pesos(d.precio_unitario)}</td>
                  <td className="derecha">{pesos(d.iva_valor)}</td>
                  <td className="derecha">{pesos(d.total_linea)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="totales">
            <div><span>Subtotal</span><span>{pesos(factura.subtotal)}</span></div>
            <div><span>Descuentos</span><span>- {pesos(factura.descuento_total)}</span></div>
            <div><span>IVA</span><span>{pesos(factura.iva_total)}</span></div>
            <div className="granTotal"><span>TOTAL</span><span>{pesos(factura.total)}</span></div>
          </div>
        </div>
        <button onClick={() => setFactura(null)}>Nueva venta</button>{' '}
        <button className="secundario" onClick={() => window.print()}>Imprimir</button>
      </>
    )
  }

  return (
    <>
      <h1>Caja</h1>
      <p className="descripcion">Registra una venta. Los equipos exigen seleccionar el IMEI que sale de bodega.</p>
      {error && <div className="mensaje error">{error}</div>}

      {imeiPendiente && (
        <div className="panel">
          <h2>Selecciona el IMEI de {imeiPendiente.nombre}</h2>
          <table>
            <thead><tr><th>IMEI</th><th>Color</th><th>Almacenamiento</th><th></th></tr></thead>
            <tbody>
              {imeisDisponibles.map((e) => (
                <tr key={e.id}>
                  <td style={{ fontFamily: 'monospace' }}>{e.imei}</td>
                  <td>{e.color || '-'}</td>
                  <td>{e.almacenamiento_gb ? `${e.almacenamiento_gb} GB` : '-'}</td>
                  <td className="derecha"><button className="mini" onClick={() => confirmarImei(e.imei)}>Elegir</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <br />
          <button className="secundario" onClick={() => { setImeiPendiente(null); setImeisDisponibles([]) }}>Cancelar</button>
        </div>
      )}

      <div className="caja">
        <div className="panel">
          <h2>Catalogo</h2>
          <div className="campo">
            <input placeholder="Buscar por nombre o SKU..." value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
          </div>
          <div className="lista-scroll">
            {filtrados.map((p) => (
              <div key={p.id} className="producto-item" onClick={() => agregar(p)}>
                <div>
                  <div>{p.nombre}</div>
                  <div className="meta">
                    {p.sku} &middot; {p.requiere_imei ? 'Serializado (IMEI)' : 'Accesorio'} &middot; {p.disponibles} disp.
                  </div>
                </div>
                <div style={{ fontWeight: 600 }}>{pesos(p.precio_venta)}</div>
              </div>
            ))}
            {filtrados.length === 0 && <div className="vacio">Sin resultados.</div>}
          </div>
        </div>

        <div className="panel">
          <h2>Factura en curso</h2>
          <div className="campo">
            <label>Cliente</label>
            <select value={clienteId} onChange={(e) => setClienteId(e.target.value)}>
              <option value="">Consumidor final</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.numero_documento} - {c.nombres} {c.apellidos || ''}
                </option>
              ))}
            </select>
          </div>
          <div className="campo">
            <label>Metodo de pago</label>
            <select value={metodoPago} onChange={(e) => setMetodoPago(e.target.value)}>
              <option value="efectivo">Efectivo</option>
              <option value="tarjeta_debito">Tarjeta debito</option>
              <option value="tarjeta_credito">Tarjeta credito</option>
              <option value="transferencia">Transferencia</option>
              <option value="nequi">Nequi</option>
              <option value="daviplata">Daviplata</option>
            </select>
          </div>

          {carrito.length === 0 ? <div className="vacio">Agrega productos desde el catalogo.</div> : (
            <table>
              <thead><tr><th>Item</th><th className="derecha">Cant.</th><th className="derecha">Desc.</th><th></th></tr></thead>
              <tbody>
                {carrito.map((l, i) => (
                  <tr key={i}>
                    <td>
                      {l.nombre}
                      <div className="meta" style={{ fontSize: 12, color: 'var(--tenue)' }}>{pesos(l.precio)} c/u</div>
                    </td>
                    <td className="derecha">{l.cantidad}</td>
                    <td className="derecha" style={{ width: 110 }}>
                      <input type="number" min="0" value={l.descuento}
                             onChange={(e) => cambiarDescuento(i, e.target.value)} />
                    </td>
                    <td className="derecha">
                      <button className="peligro mini" onClick={() => quitar(i)}>X</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          <div className="totales">
            <div><span>Subtotal</span><span>{pesos(totales.subtotal)}</span></div>
            <div><span>Descuentos</span><span>- {pesos(totales.descuentos)}</span></div>
            <div><span>IVA (19%)</span><span>{pesos(totales.iva)}</span></div>
            <div className="granTotal"><span>TOTAL</span><span>{pesos(totales.total)}</span></div>
          </div>

          <br />
          <button style={{ width: '100%' }} disabled={carrito.length === 0 || procesando} onClick={facturar}>
            {procesando ? 'Procesando...' : 'Facturar'}
          </button>
        </div>
      </div>
    </>
  )
}
