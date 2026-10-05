import { useEffect, useState } from 'react'
import { api, fechaHora } from '../api.js'
import { useAuth } from '../auth.jsx'
import { Aviso, Campo, Cargando, Estado, Modal, Panel, Tabla, useDatos } from '../componentes/ui.jsx'

export default function Usuarios() {
  const { puede, usuario: yo } = useAuth()
  const usuarios = useDatos(() => api.usuarios(), [])
  const roles = useDatos(() => api.roles(), [])
  const permisos = useDatos(() => api.permisos(), [])
  const [ventana, setVentana] = useState(null)
  const [form, setForm] = useState({})
  const [mensaje, setMensaje] = useState(null)

  const ejecutar = async (accion, exito) => {
    setMensaje(null)
    try {
      await accion()
      setVentana(null); setForm({}); usuarios.recargar()
      setMensaje({ tipo: 'ok', texto: exito })
    } catch (e) { setMensaje({ tipo: 'error', texto: e.message }) }
  }

  return (
    <>
      <div className="encabezado-pagina">
        <h1>Usuarios y roles</h1>
        <p>Los permisos viven en la base de datos: cambiarlos aquí cambia lo que cada rol puede hacer.</p>
      </div>

      {mensaje && <Aviso tipo={mensaje.tipo} alCerrar={() => setMensaje(null)}>{mensaje.texto}</Aviso>}

      <Panel titulo="Usuarios"
             acciones={puede('usuarios.crear') &&
               <button onClick={() => { setVentana('nuevo'); setForm({ rol_id: '' }) }}>Nuevo usuario</button>}
             sinRelleno>
        {usuarios.cargando ? <Cargando /> : (
          <Tabla
            filas={usuarios.datos ?? []}
            columnas={[
              { titulo: 'Usuario', clase: 'mono', celda: (u) => u.username },
              { titulo: 'Nombre', celda: (u) => (
                  <>
                    <div className="celda-principal">{u.nombre_completo}</div>
                    <div className="celda-sub">{u.email}</div>
                  </>) },
              { titulo: 'Rol', celda: (u) => <Estado valor={u.rol?.nombre} tono="info" /> },
              { titulo: 'Último acceso', celda: (u) => fechaHora(u.ultimo_acceso) },
              { titulo: 'Estado', celda: (u) => <Estado valor={u.activo ? 'ACTIVA' : 'INACTIVO'} /> },
              { titulo: '', derecha: true, celda: (u) => puede('usuarios.editar') && (
                  <div className="acciones derecha">
                    <button className="secundario pequeno"
                            onClick={() => { setVentana('clave'); setForm({ usuario: u, password: '' }) }}>
                      Clave
                    </button>
                    <button className="secundario pequeno" disabled={u.id === yo.id}
                            onClick={() => ejecutar(() => api.actualizarUsuario(u.id, { activo: !u.activo }),
                                                    u.activo ? 'Usuario desactivado.' : 'Usuario activado.')}>
                      {u.activo ? 'Desactivar' : 'Activar'}
                    </button>
                  </div>) },
            ]} />
        )}
      </Panel>

      <Panel titulo="Roles y permisos" sub="Marca lo que cada rol puede hacer" sinRelleno>
        {roles.cargando || permisos.cargando ? <Cargando /> : (
          <div className="panel-cuerpo">
            <div className="rejilla c4">
              {(roles.datos ?? []).map((r) => (
                <div key={r.id} className="tarjeta-kpi">
                  <div className="etiqueta">{r.nombre}</div>
                  <div className="nota" style={{ marginTop: 6 }}>{r.descripcion}</div>
                  {puede('usuarios.editar') && (
                    <button className="secundario pequeno" style={{ marginTop: 12 }}
                            onClick={() => setVentana({ tipo: 'permisos', rol: r })}>
                      Editar permisos
                    </button>)}
                </div>
              ))}
            </div>
          </div>
        )}
      </Panel>

      {ventana === 'nuevo' && (
        <Modal titulo="Nuevo usuario" alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={!form.username || !form.nombre_completo || !form.email || (form.password ?? '').length < 6 || !form.rol_id}
                         onClick={() => ejecutar(() => api.crearUsuario({ ...form, rol_id: Number(form.rol_id) }),
                                                 'Usuario creado.')}>Crear</button>
               </>}>
          <div className="fila-campos">
            <Campo etiqueta="Usuario">
              <input className="mono" value={form.username ?? ''}
                     onChange={(e) => setForm({ ...form, username: e.target.value.trim() })} />
            </Campo>
            <Campo etiqueta="Rol">
              <select value={form.rol_id ?? ''} onChange={(e) => setForm({ ...form, rol_id: e.target.value })}>
                <option value="">Selecciona…</option>
                {(roles.datos ?? []).map((r) => <option key={r.id} value={r.id}>{r.nombre}</option>)}
              </select>
            </Campo>
          </div>
          <Campo etiqueta="Nombre completo">
            <input value={form.nombre_completo ?? ''}
                   onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} />
          </Campo>
          <div className="fila-campos">
            <Campo etiqueta="Correo">
              <input type="email" value={form.email ?? ''} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            </Campo>
            <Campo etiqueta="Contraseña" ayuda="Mínimo 6 caracteres.">
              <input type="password" value={form.password ?? ''}
                     onChange={(e) => setForm({ ...form, password: e.target.value })} />
            </Campo>
          </div>
        </Modal>
      )}

      {ventana === 'clave' && (
        <Modal titulo={`Nueva contraseña — ${form.usuario.username}`} alCerrar={() => setVentana(null)}
               pie={<>
                 <button className="secundario" onClick={() => setVentana(null)}>Cancelar</button>
                 <button disabled={(form.password ?? '').length < 6}
                         onClick={() => ejecutar(() => api.cambiarClave(form.usuario.id, form.password),
                                                 'Contraseña actualizada.')}>Cambiar</button>
               </>}>
          <Campo etiqueta="Contraseña" ayuda="Mínimo 6 caracteres.">
            <input type="password" autoFocus value={form.password ?? ''}
                   onChange={(e) => setForm({ ...form, password: e.target.value })} />
          </Campo>
        </Modal>
      )}

      {ventana?.tipo === 'permisos' && (
        <EditorPermisos rol={ventana.rol} permisos={permisos.datos ?? []}
                        cerrar={() => setVentana(null)}
                        guardar={(ids) => ejecutar(() => api.guardarPermisosDeRol(ventana.rol.id, ids),
                                                   `Permisos de ${ventana.rol.nombre} actualizados.`)} />
      )}
    </>
  )
}

function EditorPermisos({ rol, permisos, cerrar, guardar }) {
  const [elegidos, setElegidos] = useState(null)
  useEffect(() => { api.permisosDeRol(rol.id).then(setElegidos).catch(() => setElegidos([])) }, [rol.id])

  if (!elegidos) return <Modal titulo={`Permisos de ${rol.nombre}`} alCerrar={cerrar}><Cargando /></Modal>

  const porModulo = permisos.reduce((acc, p) => {
    (acc[p.modulo] ??= []).push(p)
    return acc
  }, {})
  const alternar = (id) => setElegidos((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id])

  return (
    <Modal titulo={`Permisos de ${rol.nombre}`} ancho alCerrar={cerrar}
           pie={<>
             <button className="secundario" onClick={cerrar}>Cancelar</button>
             <button onClick={() => guardar(elegidos)}>Guardar {elegidos.length} permisos</button>
           </>}>
      <div className="rejilla c3">
        {Object.entries(porModulo).map(([modulo, lista]) => (
          <div key={modulo}>
            <h3 style={{ textTransform: 'capitalize', marginBottom: 8 }}>{modulo}</h3>
            {lista.map((p) => (
              <label key={p.id} style={{ display: 'flex', gap: 8, alignItems: 'flex-start', fontWeight: 400,
                                         marginBottom: 6, cursor: 'pointer' }}>
                <input type="checkbox" style={{ width: 'auto', marginTop: 3 }}
                       checked={elegidos.includes(p.id)} onChange={() => alternar(p.id)} />
                <span>
                  <span className="mono texto-pequeno">{p.codigo.split('.')[1]}</span>
                  <br /><span className="texto-tenue texto-pequeno">{p.descripcion}</span>
                </span>
              </label>
            ))}
          </div>
        ))}
      </div>
    </Modal>
  )
}
