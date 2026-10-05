import { useState } from 'react'
import { api, pesos, numero, fecha, fechaHora, legible } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo, Cargando, Estado, Modal, Panel, Tabla, useDatos } from '../componentes/ui.jsx'

export default function Inventario() {
  const { puede } = useAuth()
  const [pestana, setPestana] = useState('productos')
  const [busqueda, setBusqueda] = useState('')
  const [estadoImei, setEstadoImei] = useState('')
  const productos = useDatos(() => api.productos({ q: busqueda }), [busqueda])
  const equipos = useDatos(() => api.equipos({ q: busqueda, estado: estadoImei }), [busqueda, estadoImei])
  const [ventana, setVentana] = useState(null)
  const [form, setForm] = useState({})
  const [kardex, setKardex] = useState(null)
  const [mensaje, setMensaje] = useState(null)

  const ejecutar = async (accion, exito) => {
    setMensaje(null)
    try {
      await accion()
      setVentana(null); setForm({})
      productos.recargar(); equipos.recargar()
      setMensaje({ tipo: 'ok', texto: exito })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const verKardex = async (p) => {
    try { setKardex({ producto: p, movimientos: await api.kardex(p.id) }) }
    catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Inventario</h1>
        <p>Los equipos se controlan unidad por unidad con su IMEI; los accesorios por stock.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <section className="panel">
        <div className="pestanas">
          <button className={`pestana${pestana === 'productos' ? ' activa' : ''}`}
                  onClick={() => setPestana('productos')}>Productos</button>
          <button className={`pestana${pestana === 'imei' ? ' activa' : ''}`}
                  onClick={() => setPestana('imei')}>Equipos por IMEI</button>
        </div>

        <div className="panel-cuerpo">
          <div className="barra-filtros">
            <Campo etiqueta="Buscar">
              <input placeholder={pestana === 'imei' ? 'Dígitos del IMEI…' : 'Nombre, SKU o código de barras…'}
                     value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
            </Campo>
            {pestana === 'imei' && (
              <Campo etiqueta="Estado">
                <select value={estadoImei} onChange={(e) => setEstadoImei(e.target.value)}>
                  <option value="">Todos</option>
                  {['DISPONIBLE', 'APARTADO', 'VENDIDO', 'EN_SERVICIO', 'DEVUELTO', 'DADO_DE_BAJA']
                    .map((e) => <option key={e} value={e}>{legible(e)}</option>)}
                </select>
              </Campo>
            )}
            <div className="espaciador" />
            {puede('inventario.crear') && (
              <div className="acciones">
                <button className="secundario" onClick={() => { setVentana('producto'); setForm({ requiere_imei: false, iva_porcentaje: 19, meses_garantia: 12, stock_minimo: 5, stock_actual: 0 }) }}>
                  Nuevo producto
                </button>
                <button onClick={() => { setVentana('equipo'); setForm({}) }}>Ingresar equipo</button>
              </div>
            )}
          </div>
        </div>

        {pestana === 'productos'
          ? (productos.cargando ? <Cargando /> : (
            <Tabla
              filas={productos.datos ?? []}
              alHacerClic={verKardex}
              columnas={[
                { titulo: 'SKU', clase: 'mono', celda: (p) => p.sku },
                { titulo: 'Producto', celda: (p) => (
                    <>
                      <div className="celda-principal">{p.nombre}</div>
                      <div className="celda-sub">{p.marca?.nombre ?? '—'} · {p.categoria?.nombre ?? '—'}</div>
                    </>) },
                { titulo: 'Tipo', celda: (p) => <Estado valor={p.requiere_imei ? 'IMEI' : 'STOCK'}
                                                        tono={p.requiere_imei ? 'info' : ''} /> },
                { titulo: 'Disp.', derecha: true, celda: (p) => (
                    <Estado valor={numero(p.disponibles)}
                            tono={p.disponibles <= p.stock_minimo ? 'peligro' : 'ok'} /> ) },
                { titulo: 'Costo', derecha: true, celda: (p) => pesos(p.precio_costo) },
                { titulo: 'Venta', derecha: true, celda: (p) => <strong>{pesos(p.precio_venta)}</strong> },
                { titulo: '', derecha: true, celda: (p) => (
                    !p.requiere_imei && puede('inventario.ajustar')
                      ? <button className="secundario pequeno"
                                onClick={(ev) => { ev.stopPropagation(); setVentana('ajuste'); setForm({ producto: p, cantidad: '', motivo: '' }) }}>
                          Ajustar
                        </button>
                      : null) },
              ]} />
          ))
          : (equipos.cargando ? <Cargando /> : (
            <Tabla
              filas={equipos.datos ?? []}
              vacio="No hay equipos con ese filtro."
              columnas={[
                { titulo: 'IMEI', clase: 'mono', celda: (e) => e.imei },
                { titulo: 'Modelo', celda: (e) => e.producto?.nombre ?? `Producto ${e.producto_id}` },
                { titulo: 'Color', celda: (e) => e.color ?? '—' },
                { titulo: 'Alm.', celda: (e) => e.almacenamiento_gb ? `${e.almacenamiento_gb} GB` : '—' },
                { titulo: 'RFID', clase: 'mono', celda: (e) => e.codigo_rfid ?? '—' },
                { titulo: 'Estado', celda: (e) => <Estado valor={e.estado} /> },
                { titulo: 'Ingreso', celda: (e) => fecha(e.fecha_ingreso) },
              ]} />
          ))}
      </section>

      {ventana === 'producto' && (
        <Modal titulo="Nuevo producto" ancho alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.sku || !form.nombre || !form.categoria_id}
                         onClick={() => ejecutar(() => api.crearProducto({
                           ...form, categoria_id: Number(form.categoria_id),
                           marca_id: form.marca_id ? Number(form.marca_id) : null,
                         }), 'Producto creado.')}>Crear</button>
               </>}>
          <FormularioProducto form={form} setForm={setForm} />
        </Modal>
      )}

      {ventana === 'equipo' && (
        <Modal titulo="Ingresar equipo a bodega" alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.producto_id || (form.imei ?? '').length !== 15}
                         onClick={() => ejecutar(() => api.ingresarEquipo({
                           producto_id: Number(form.producto_id), imei: form.imei,
                           color: form.color || null, codigo_rfid: form.codigo_rfid || null,
                           almacenamiento_gb: form.almacenamiento_gb ? Number(form.almacenamiento_gb) : null,
                           costo: form.costo || 0,
                         }), 'Equipo ingresado al inventario.')}>Ingresar</button>
               </>}>
          <Campo etiqueta="Modelo">
            <select value={form.producto_id ?? ''} onChange={(e) => setForm({ ...form, producto_id: e.target.value })}>
              <option value="">Selecciona…</option>
              {(productos.datos ?? []).filter((p) => p.requiere_imei)
                .map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
            </select>
          </Campo>
          <Campo etiqueta="IMEI" ayuda="15 dígitos con dígito verificador válido (algoritmo de Luhn).">
            <input maxLength={15} className="mono" value={form.imei ?? ''}
                   onChange={(e) => setForm({ ...form, imei: e.target.value.replace(/\D/g, '') })} />
          </Campo>
          <div className="fila-campos">
            <Campo etiqueta="Color">
              <input value={form.color ?? ''} onChange={(e) => setForm({ ...form, color: e.target.value })} />
            </Campo>
            <Campo etiqueta="Almacenamiento (GB)">
              <input type="number" value={form.almacenamiento_gb ?? ''}
                     onChange={(e) => setForm({ ...form, almacenamiento_gb: e.target.value })} />
            </Campo>
            <Campo etiqueta="Costo">
              <input type="number" value={form.costo ?? ''} onChange={(e) => setForm({ ...form, costo: e.target.value })} />
            </Campo>
            <Campo etiqueta="Etiqueta RFID">
              <input value={form.codigo_rfid ?? ''} onChange={(e) => setForm({ ...form, codigo_rfid: e.target.value })} />
            </Campo>
          </div>
        </Modal>
      )}

      {ventana === 'ajuste' && (
        <Modal titulo={`Ajustar stock — ${form.producto?.nombre}`} alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.cantidad || !form.motivo}
                         onClick={() => ejecutar(() => api.ajustarStock(form.producto.id, {
                           cantidad: Number(form.cantidad), motivo: form.motivo }), 'Stock ajustado.')}>
                   Aplicar
                 </button>
               </>}>
          <Campo etiqueta="Cantidad" ayuda="Positivo suma unidades, negativo las resta.">
            <input type="number" autoFocus value={form.cantidad ?? ''}
                   onChange={(e) => setForm({ ...form, cantidad: e.target.value })} />
          </Campo>
          <Campo etiqueta="Motivo">
            <input value={form.motivo ?? ''} placeholder="Conteo físico, avería, obsequio…"
                   onChange={(e) => setForm({ ...form, motivo: e.target.value })} />
          </Campo>
        </Modal>
      )}

      {kardex && (
        <Modal titulo={`Kardex — ${kardex.producto.nombre}`} ancho alCerrar={() => setKardex(null)}>
          <Tabla
            filas={kardex.movimientos}
            vacio="Sin movimientos registrados."
            columnas={[
              { titulo: 'Fecha', celda: (m) => fechaHora(m.fecha) },
              { titulo: 'Tipo', celda: (m) => <Estado valor={m.tipo}
                   tono={m.tipo === 'ENTRADA' ? 'ok' : m.tipo === 'SALIDA' ? 'alerta' : 'info'} /> },
              { titulo: 'Cant.', derecha: true, celda: (m) => m.cantidad },
              { titulo: 'Resultante', derecha: true, celda: (m) => m.stock_resultante },
              { titulo: 'Motivo', celda: (m) => m.motivo ?? '—' },
              { titulo: 'Referencia', clase: 'mono', celda: (m) => m.referencia ?? '—' },
            ]} />
        </Modal>
      )}
    </>
  )
}

function FormularioProducto({ form, setForm }) {
  const categorias = useDatos(() => api.categorias(), [])
  const marcas = useDatos(() => api.marcas(), [])
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })
  return (
    <>
      <div className="fila-campos">
        <Campo etiqueta="SKU"><input value={form.sku ?? ''} onChange={set('sku')} /></Campo>
        <Campo etiqueta="Código de barras"><input value={form.codigo_barras ?? ''} onChange={set('codigo_barras')} /></Campo>
      </div>
      <Campo etiqueta="Nombre"><input value={form.nombre ?? ''} onChange={set('nombre')} /></Campo>
      <div className="fila-campos">
        <Campo etiqueta="Categoría">
          <select value={form.categoria_id ?? ''} onChange={set('categoria_id')}>
            <option value="">Selecciona…</option>
            {(categorias.datos ?? []).map((c) => <option key={c.id} value={c.id}>{c.nombre}</option>)}
          </select>
        </Campo>
        <Campo etiqueta="Marca">
          <select value={form.marca_id ?? ''} onChange={set('marca_id')}>
            <option value="">Sin marca</option>
            {(marcas.datos ?? []).map((m) => <option key={m.id} value={m.id}>{m.nombre}</option>)}
          </select>
        </Campo>
      </div>
      <div className="fila-campos">
        <Campo etiqueta="Precio de costo"><input type="number" value={form.precio_costo ?? ''} onChange={set('precio_costo')} /></Campo>
        <Campo etiqueta="Precio de venta"><input type="number" value={form.precio_venta ?? ''} onChange={set('precio_venta')} /></Campo>
        <Campo etiqueta="IVA (%)"><input type="number" value={form.iva_porcentaje ?? 19} onChange={set('iva_porcentaje')} /></Campo>
      </div>
      <div className="fila-campos">
        <Campo etiqueta="Control">
          <select value={form.requiere_imei ? '1' : '0'}
                  onChange={(e) => setForm({ ...form, requiere_imei: e.target.value === '1', stock_actual: 0 })}>
            <option value="0">Por stock (accesorios)</option>
            <option value="1">Por IMEI (equipos)</option>
          </select>
        </Campo>
        <Campo etiqueta="Garantía (meses)"><input type="number" value={form.meses_garantia ?? 12} onChange={set('meses_garantia')} /></Campo>
        <Campo etiqueta="Stock mínimo"><input type="number" value={form.stock_minimo ?? 5} onChange={set('stock_minimo')} /></Campo>
        {!form.requiere_imei &&
          <Campo etiqueta="Stock inicial"><input type="number" value={form.stock_actual ?? 0} onChange={set('stock_actual')} /></Campo>}
      </div>
    </>
  )
}
