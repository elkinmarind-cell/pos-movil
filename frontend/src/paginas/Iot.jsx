import { useState } from 'react'
import { api, fechaHora, legible } from '../api.js'
import { Aviso, Cargando, Estado, Kpi, Panel, Tabla, useDatos } from '../componentes/ui.jsx'

export default function Iot() {
  const dispositivos = useDatos(() => api.dispositivos(), [])
  const eventos = useDatos(() => api.eventos(), [])
  const alertas = useDatos(() => api.alertas(), [])
  const [mensaje, setMensaje] = useState(null)

  const atender = async (a) => {
    try {
      await api.atenderAlerta(a.id)
      alertas.recargar()
      setMensaje({ tipo: 'ok', texto: 'Alerta marcada como atendida.' })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  const sinAtender = (alertas.datos ?? []).filter((a) => !a.fecha_atencion)
  const activos = (dispositivos.datos ?? []).filter((d) => d.activo)

  return (
    <>
      <div className="encabezado-pagina">
        <h1>IoT y alertas</h1>
        <p>Lectores de código de barras, arco RFID en la puerta y sensores de la tienda.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <div className="rejilla c4" style={{ marginBottom: 18 }}>
        <Kpi etiqueta="Dispositivos" valor={activos.length} nota={`${dispositivos.datos?.length ?? 0} registrados`} />
        <Kpi etiqueta="Alertas sin atender" valor={sinAtender.length}
             tono={sinAtender.length ? 'peligro' : 'exito'} nota="requieren revisión" />
        <Kpi etiqueta="Eventos recientes" valor={eventos.datos?.length ?? 0} nota="últimas lecturas" />
      </div>

      <Panel titulo="Alertas" sinRelleno>
        {alertas.cargando ? <Cargando /> : (
          <Tabla
            filas={alertas.datos ?? []}
            vacio="No hay alertas."
            columnas={[
              { titulo: 'Severidad', celda: (a) => <Estado valor={a.severidad} /> },
              { titulo: 'Tipo', celda: (a) => legible(a.tipo) },
              { titulo: 'Mensaje', celda: (a) => a.mensaje },
              { titulo: 'Fecha', celda: (a) => fechaHora(a.fecha) },
              { titulo: 'Atendida', celda: (a) => a.fecha_atencion
                  ? <Estado valor="ATENDIDA" tono="ok" /> : <Estado valor="PENDIENTE" tono="peligro" /> },
              { titulo: '', derecha: true, celda: (a) => !a.fecha_atencion && (
                  <button className="secundario pequeno" onClick={() => atender(a)}>Marcar atendida</button>) },
            ]} />
        )}
      </Panel>

      <div className="rejilla c2" style={{ marginTop: 18 }}>
        <Panel titulo="Dispositivos" sinRelleno>
          {dispositivos.cargando ? <Cargando /> : (
            <Tabla
              filas={dispositivos.datos ?? []}
              columnas={[
                { titulo: 'Nombre', celda: (d) => (
                    <>
                      <div className="celda-principal">{d.nombre}</div>
                      <div className="celda-sub">{legible(d.tipo)} · {d.ubicacion}</div>
                    </>) },
                { titulo: 'Red', clase: 'mono', celda: (d) => (
                    <>
                      <div>{d.direccion_ip ?? '—'}</div>
                      <div className="celda-sub mono">{d.direccion_mac}</div>
                    </>) },
                { titulo: 'Protocolo', celda: (d) => <Estado valor={d.protocolo} tono="info" /> },
                { titulo: 'Estado', celda: (d) => <Estado valor={d.activo ? 'ACTIVA' : 'INACTIVO'} /> },
              ]} />
          )}
        </Panel>

        <Panel titulo="Últimos eventos" sinRelleno>
          {eventos.cargando ? <Cargando /> : (
            <Tabla
              filas={(eventos.datos ?? []).slice(0, 12)}
              columnas={[
                { titulo: 'Evento', celda: (e) => (
                    <>
                      <div className="celda-principal">{legible(e.tipo_evento)}</div>
                      <div className="celda-sub mono texto-pequeno">{JSON.stringify(e.payload)}</div>
                    </>) },
                { titulo: 'Fecha', celda: (e) => fechaHora(e.fecha) },
              ]} />
          )}
        </Panel>
      </div>
    </>
  )
}
