import { useState } from 'react'
import { api, pesos, numero, fecha, fechaHora } from '../api.js'
import { Aviso, Campo, Cargando, Estado, Kpi, Panel, Tabla, Vacio, useDatos } from '../componentes/ui.jsx'

export default function Reportes() {
  const [dias, setDias] = useState(30)
  const serie = useDatos(() => api.ventasPorDia(dias), [dias])
  const rentabilidad = useDatos(() => api.rentabilidad(), [])
  const stock = useDatos(() => api.alertasStock(), [])
  const [imei, setImei] = useState('')
  const [traza, setTraza] = useState(null)
  const [error, setError] = useState('')

  const buscar = async () => {
    setError(''); setTraza(null)
    try { setTraza(await api.trazabilidad(imei.trim())) }
    catch (e) { setError(e.message) }
  }

  const totalPeriodo = (serie.datos ?? []).reduce((s, d) => s + Number(d.total), 0)
  const ventasPeriodo = (serie.datos ?? []).reduce((s, d) => s + d.cantidad, 0)
  const utilidadTotal = (rentabilidad.datos ?? []).reduce((s, r) => s + Number(r.utilidad), 0)
  const maximo = Math.max(...(serie.datos ?? []).map((d) => Number(d.total)), 1)

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Reportes</h1>
        <p>Indicadores calculados por las vistas de la base de datos.</p>
      </div>

      <div className="rejilla c4" style={{ marginBottom: 18 }}>
        <Kpi etiqueta={`Ventas (${dias} días)`} valor={pesos(totalPeriodo)} tono="acento"
             nota={`${ventasPeriodo} facturas`} />
        <Kpi etiqueta="Ticket promedio" tono="exito"
             valor={pesos(ventasPeriodo ? totalPeriodo / ventasPeriodo : 0)} />
        <Kpi etiqueta="Utilidad bruta acumulada" valor={pesos(utilidadTotal)}
             nota="ingreso sin IVA menos costo" />
        <Kpi etiqueta="Productos bajo mínimo" valor={numero(stock.datos?.length ?? 0)}
             tono={stock.datos?.length ? 'alerta' : ''} />
      </div>

      <Panel titulo="Ventas por día"
             acciones={
               <select value={dias} onChange={(e) => setDias(Number(e.target.value))} style={{ width: 160 }}>
                 <option value={7}>Últimos 7 días</option>
                 <option value={14}>Últimos 14 días</option>
                 <option value={30}>Últimos 30 días</option>
                 <option value={90}>Últimos 90 días</option>
               </select>}>
        {serie.cargando ? <Cargando /> : (
          <div className="barras">
            {(serie.datos ?? []).map((d) => (
              <div className="barra-col" key={d.fecha} title={`${d.fecha}: ${pesos(d.total)} · ${d.cantidad} venta(s)`}>
                <div className="barra" style={{ height: `${(Number(d.total) / maximo) * 100}%` }} />
                {dias <= 14 && <div className="dia">{d.fecha.slice(8)}</div>}
              </div>
            ))}
          </div>
        )}
      </Panel>

      <Panel titulo="Rentabilidad por producto" sub="Vista v_rentabilidad_producto" sinRelleno>
        {rentabilidad.cargando ? <Cargando /> : (
          <Tabla
            filas={rentabilidad.datos ?? []}
            clave={(r) => r.producto_id}
            vacio="Aún no hay ventas para calcular rentabilidad."
            columnas={[
              { titulo: 'SKU', clase: 'mono', celda: (r) => r.sku },
              { titulo: 'Producto', celda: (r) => <span className="celda-principal">{r.nombre}</span> },
              { titulo: 'Unid.', derecha: true, celda: (r) => numero(r.unidades) },
              { titulo: 'Ingreso sin IVA', derecha: true, celda: (r) => pesos(r.ingreso_sin_iva) },
              { titulo: 'Costo', derecha: true, celda: (r) => pesos(r.costo) },
              { titulo: 'Utilidad', derecha: true,
                celda: (r) => <strong style={{ color: Number(r.utilidad) >= 0 ? 'var(--exito)' : 'var(--peligro)' }}>
                  {pesos(r.utilidad)}</strong> },
            ]} />
        )}
      </Panel>

      <Panel titulo="Trazabilidad de un equipo" sub="Vista v_trazabilidad_imei">
        <div className="barra-filtros">
          <Campo etiqueta="IMEI">
            <input className="mono" maxLength={15} value={imei} placeholder="15 dígitos"
                   onChange={(e) => setImei(e.target.value.replace(/\D/g, ''))} />
          </Campo>
          <button disabled={imei.length !== 15} onClick={buscar}>Consultar</button>
        </div>
        {error && <Aviso tipo="error" alCerrar={() => setError('')}>{error}</Aviso>}
        {traza && (
          <>
            <div className="separador" />
            <div className="rejilla c3">
              <div><label>Producto</label><div className="celda-principal">{traza.producto}</div></div>
              <div><label>Estado actual</label><Estado valor={traza.estado} /></div>
              <div><label>Ingreso a bodega</label><div>{fechaHora(traza.fecha_ingreso)}</div></div>
              <div><label>Factura</label><div className="mono">{traza.factura ?? '—'}</div></div>
              <div><label>Fecha de venta</label><div>{fechaHora(traza.fecha_venta)}</div></div>
              <div><label>Cliente</label><div>{traza.cliente ?? '—'}</div></div>
              <div><label>Garantía hasta</label><div>{fecha(traza.garantia_hasta)}</div></div>
              <div><label>Estado de garantía</label><Estado valor={traza.estado_garantia} /></div>
            </div>
          </>
        )}
      </Panel>

      <Panel titulo="Productos bajo el mínimo" sub="Vista v_alertas_stock" sinRelleno>
        {stock.cargando ? <Cargando /> : (
          (stock.datos ?? []).length === 0
            ? <Vacio icono="✓">Todo el inventario está sobre el mínimo.</Vacio>
            : <Tabla
                filas={stock.datos}
                clave={(s) => s.producto_id}
                columnas={[
                  { titulo: 'SKU', clase: 'mono', celda: (s) => s.sku },
                  { titulo: 'Producto', celda: (s) => s.nombre },
                  { titulo: 'Disponibles', derecha: true,
                    celda: (s) => <Estado valor={String(s.disponibles)} tono={s.disponibles === 0 ? 'peligro' : 'alerta'} /> },
                  { titulo: 'Mínimo', derecha: true, celda: (s) => numero(s.stock_minimo) },
                  { titulo: 'Faltante', derecha: true, celda: (s) => numero(Math.max(s.stock_minimo - s.disponibles, 0)) },
                ]} />
        )}
      </Panel>
    </>
  )
}
