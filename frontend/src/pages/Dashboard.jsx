import { useEffect, useState } from 'react'
import { api, pesos } from '../api.js'

export default function Dashboard() {
  const [datos, setDatos] = useState(null)
  const [serie, setSerie] = useState([])
  const [top, setTop] = useState([])
  const [alertas, setAlertas] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([api.dashboard(), api.ventasPorDia(14), api.masVendidos(), api.alertasStock()])
      .then(([d, s, t, a]) => { setDatos(d); setSerie(s); setTop(t); setAlertas(a) })
      .catch((e) => setError(e.message))
  }, [])

  if (error) return <div className="mensaje error">{error}</div>
  if (!datos) return <p className="vacio">Cargando indicadores...</p>

  const maximo = Math.max(...serie.map((d) => Number(d.total)), 1)

  return (
    <>
      <h1>Dashboard</h1>
      <p className="descripcion">Indicadores de operacion del punto de venta</p>

      <div className="tarjetas">
        <div className="tarjeta">
          <div className="etiqueta">Ventas de hoy</div>
          <div className="valor">{pesos(datos.ventas_hoy)}</div>
          <div className="nota">{datos.numero_ventas_hoy} factura(s)</div>
        </div>
        <div className="tarjeta">
          <div className="etiqueta">Ventas del mes</div>
          <div className="valor">{pesos(datos.ventas_mes)}</div>
          <div className="nota">{datos.numero_ventas_mes} factura(s)</div>
        </div>
        <div className="tarjeta">
          <div className="etiqueta">Ticket promedio</div>
          <div className="valor">{pesos(datos.ticket_promedio_mes)}</div>
          <div className="nota">Promedio del mes en curso</div>
        </div>
        <div className="tarjeta">
          <div className="etiqueta">Equipos disponibles</div>
          <div className="valor">{datos.equipos_disponibles}</div>
          <div className="nota">Unidades con IMEI en bodega</div>
        </div>
        <div className="tarjeta">
          <div className="etiqueta">Productos bajo minimo</div>
          <div className="valor" style={{ color: datos.productos_bajo_stock ? 'var(--alerta)' : undefined }}>
            {datos.productos_bajo_stock}
          </div>
          <div className="nota">Requieren reabastecimiento</div>
        </div>
        <div className="tarjeta">
          <div className="etiqueta">Garantias</div>
          <div className="valor">{datos.garantias_vigentes}</div>
          <div className="nota">{datos.garantias_en_reclamacion} en reclamacion</div>
        </div>
      </div>

      <div className="panel">
        <h2>Ventas de los ultimos 14 dias</h2>
        <div className="barras">
          {serie.map((d) => (
            <div
              key={d.fecha}
              className="barra"
              style={{ height: `${(Number(d.total) / maximo) * 100}%` }}
              title={`${d.fecha}: ${pesos(d.total)} (${d.cantidad} ventas)`}
            >
              <span>{d.fecha.slice(8)}</span>
            </div>
          ))}
        </div>
        <div className="leyenda-barras">Pasa el cursor sobre una barra para ver el detalle del dia.</div>
      </div>

      <div className="fila">
        <div className="panel">
          <h2>Productos mas vendidos (30 dias)</h2>
          {top.length === 0 ? <div className="vacio">Aun no hay ventas registradas.</div> : (
            <table>
              <thead><tr><th>Producto</th><th className="derecha">Unid.</th><th className="derecha">Total</th></tr></thead>
              <tbody>
                {top.map((p) => (
                  <tr key={p.producto_id}>
                    <td>{p.nombre}</td>
                    <td className="derecha">{p.unidades}</td>
                    <td className="derecha">{pesos(p.total_vendido)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="panel">
          <h2>Alertas de stock</h2>
          {alertas.length === 0 ? <div className="vacio">Todo el inventario esta sobre el minimo.</div> : (
            <table>
              <thead><tr><th>SKU</th><th>Producto</th><th className="derecha">Disp.</th><th className="derecha">Min.</th></tr></thead>
              <tbody>
                {alertas.map((a) => (
                  <tr key={a.producto_id}>
                    <td>{a.sku}</td>
                    <td>{a.nombre}</td>
                    <td className="derecha"><span className="badge bad">{a.disponibles}</span></td>
                    <td className="derecha">{a.stock_minimo}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  )
}
