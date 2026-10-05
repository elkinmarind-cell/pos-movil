import { Link } from 'react-router-dom'
import { api, pesos, numero, fechaHora } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Cargando, Estado, Kpi, Panel, Tabla, Vacio, useDatos } from '../componentes/ui.jsx'

export default function Dashboard() {
  const { puede, usuario } = useAuth()
  const conReportes = puede('reportes.ver')

  const d = useDatos(() => (conReportes
    ? Promise.all([api.dashboard(), api.ventasPorDia(14), api.masVendidos(), api.alertasStock()])
    : Promise.all([null, null, null, null])), [conReportes])
  const turno = useDatos(() => api.miTurno(), [])

  if (d.cargando || turno.cargando) return <Cargando />
  if (d.error) return <Aviso tipo="error">{d.error}</Aviso>

  if (!conReportes) {
    return (
      <>
        <div className="encabezado-pagina">
          <h1>Hola, {usuario.nombre_completo.split(' ')[0]}</h1>
          <p>Tu rol no incluye los reportes de dirección. Estos son tus accesos.</p>
        </div>
        <div className="rejilla c3">
          <Panel titulo="Caja">
            {turno.datos
              ? <p>Tienes la caja abierta desde {fechaHora(turno.datos.apertura)}.</p>
              : <p className="texto-tenue">No tienes caja abierta.</p>}
            <div className="separador" />
            <Link to="/caja"><button className="secundario">Ir a caja</button></Link>
          </Panel>
          <Panel titulo="Vender">
            <p className="texto-tenue">Registra una venta con lectura de IMEI y pago mixto.</p>
            <div className="separador" />
            <Link to="/venta"><button>Abrir punto de venta</button></Link>
          </Panel>
          <Panel titulo="Clientes">
            <p className="texto-tenue">Consulta el historial y las garantías de un cliente.</p>
            <div className="separador" />
            <Link to="/clientes"><button className="secundario">Ver clientes</button></Link>
          </Panel>
        </div>
      </>
    )
  }

  const [kpi, serie, top, stock] = d.datos
  const maximo = Math.max(...serie.map((x) => Number(x.total)), 1)

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Hola, {usuario.nombre_completo.split(' ')[0]}</h1>
        <p>
          {kpi.turno_abierto
            ? 'Tienes la caja abierta. Así va el negocio hoy.'
            : 'No tienes caja abierta: ábrela para poder vender.'}
        </p>
      </div>

      <div className="rejilla c4" style={{ marginBottom: 18 }}>
        <Kpi etiqueta="Ventas de hoy" valor={pesos(kpi.ventas_hoy)} tono="acento"
             nota={`${kpi.numero_ventas_hoy} factura${kpi.numero_ventas_hoy === 1 ? '' : 's'}`} />
        <Kpi etiqueta="Ventas del mes" valor={pesos(kpi.ventas_mes)} tono="exito"
             nota={`ticket promedio ${pesos(kpi.ticket_promedio_mes)}`} />
        <Kpi etiqueta="Equipos disponibles" valor={numero(kpi.equipos_disponibles)}
             nota="unidades con IMEI en bodega" />
        <Kpi etiqueta="Bajo mínimo" valor={numero(kpi.productos_bajo_stock)}
             tono={kpi.productos_bajo_stock ? 'alerta' : ''} nota="productos por reabastecer" />
        <Kpi etiqueta="Garantías vigentes" valor={numero(kpi.garantias_vigentes)}
             nota={`${kpi.ordenes_servicio_abiertas} en servicio técnico`} />
        <Kpi etiqueta="Apartados" valor={numero(kpi.apartados_vigentes)} nota="equipos reservados" />
        <Kpi etiqueta="Alertas sin atender" valor={numero(kpi.alertas_sin_atender)}
             tono={kpi.alertas_sin_atender ? 'peligro' : ''} nota="IoT y operación" />
      </div>

      <Panel titulo="Ventas de los últimos 14 días"
             sub="Pasa el cursor sobre una barra para ver el detalle del día">
        <div className="barras">
          {serie.map((x) => (
            <div className="barra-col" key={x.fecha}
                 title={`${x.fecha}: ${pesos(x.total)} · ${x.cantidad} venta(s)`}>
              <div className="barra" style={{ height: `${(Number(x.total) / maximo) * 100}%` }} />
              <div className="dia">{x.fecha.slice(8)}</div>
            </div>
          ))}
        </div>
      </Panel>

      <div className="rejilla c2" style={{ marginTop: 18 }}>
        <Panel titulo="Productos más vendidos" sinRelleno>
          <Tabla
            vacio="Aún no hay ventas registradas."
            filas={top.slice(0, 8)}
            clave={(f) => f.producto_id}
            columnas={[
              { titulo: 'Producto', celda: (f) => <span className="celda-principal">{f.nombre}</span> },
              { titulo: 'Unid.', derecha: true, celda: (f) => numero(f.unidades) },
              { titulo: 'Ingreso', derecha: true, celda: (f) => pesos(f.total_vendido) },
            ]} />
        </Panel>

        <Panel titulo="Alertas de inventario" sinRelleno>
          {stock.length === 0
            ? <Vacio icono="✓">Todo el inventario está sobre el mínimo.</Vacio>
            : <Tabla
                filas={stock}
                clave={(f) => f.producto_id}
                columnas={[
                  { titulo: 'SKU', clase: 'mono', celda: (f) => f.sku },
                  { titulo: 'Producto', celda: (f) => f.nombre },
                  { titulo: 'Disp.', derecha: true,
                    celda: (f) => <Estado valor={String(f.disponibles)} tono={f.disponibles === 0 ? 'peligro' : 'alerta'} /> },
                  { titulo: 'Mínimo', derecha: true, celda: (f) => numero(f.stock_minimo) },
                ]} />}
        </Panel>
      </div>
    </>
  )
}
