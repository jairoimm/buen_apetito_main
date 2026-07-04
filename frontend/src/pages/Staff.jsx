import React, { useState } from 'react';
import { UserPlus, Shield } from 'lucide-react';
import useFetch from '../hooks/useFetch';
import { getUsuariosNegocio, invitarUsuarioNegocio, actualizarUsuarioNegocio } from '../api/services';

const ROLES = [
  { value: 'ADMINISTRADOR', label: 'Administrador' },
  { value: 'CAJERO', label: 'Cajero' },
  { value: 'COCINERO', label: 'Cocinero' },
];

const Staff = ({ negocioId }) => {
  const { data: staff, loading, error, refetch } = useFetch(
    () => getUsuariosNegocio(negocioId), [negocioId]
  );

  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ username: '', rol: 'CAJERO' });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const handleInvitar = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError('');
    try {
      await invitarUsuarioNegocio(negocioId, form);
      setForm({ username: '', rol: 'CAJERO' });
      setShowForm(false);
      refetch();
    } catch (err) {
      const data = err.response?.data;
      const msg = data?.username?.[0] || data?.rol?.[0] || data?.detail || 'No se pudo invitar al usuario.';
      setFormError(msg);
    } finally {
      setSaving(false);
    }
  };

  const cambiarRol = async (miembro, rol) => {
    await actualizarUsuarioNegocio(negocioId, miembro.id, { rol });
    refetch();
  };

  const toggleActivo = async (miembro) => {
    await actualizarUsuarioNegocio(negocioId, miembro.id, { activo: !miembro.activo });
    refetch();
  };

  if (loading) return <div className="loading">Cargando equipo...</div>;
  if (error) return <div className="alert alert--error">{error}</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Equipo</h2>
          <span className="page-subtitle">{staff.length} personas con acceso</span>
        </div>
        <button className="btn btn--primary" onClick={() => setShowForm(!showForm)}>
          <UserPlus size={16} /> Invitar usuario
        </button>
      </div>

      {showForm && (
        <div className="card form-card">
          <h3>Invitar usuario existente</h3>
          <p className="muted" style={{ fontSize: 13, marginTop: -4 }}>
            El usuario ya debe existir en el sistema (créalo primero si es nuevo).
          </p>
          <form onSubmit={handleInvitar} className="form-grid">
            <div className="form-group">
              <label>Nombre de usuario *</label>
              <input
                type="text"
                value={form.username}
                onChange={e => setForm({ ...form, username: e.target.value })}
                placeholder="ej: james"
                required
              />
            </div>
            <div className="form-group">
              <label>Rol *</label>
              <select
                value={form.rol}
                onChange={e => setForm({ ...form, rol: e.target.value })}
              >
                {ROLES.map(r => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
            {formError && (
              <div className="alert alert--error form-group--full">{formError}</div>
            )}
            <div className="form-actions">
              <button
                type="button"
                className="btn btn--ghost"
                onClick={() => { setShowForm(false); setFormError(''); }}
              >
                Cancelar
              </button>
              <button type="submit" className="btn btn--primary" disabled={saving}>
                {saving ? 'Invitando...' : 'Invitar'}
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Usuario</th>
              <th>Rol</th>
              <th>Estado</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {staff.map(m => (
              <tr key={m.id}>
                <td>{m.username}</td>
                <td>
                  {m.rol === 'DUENO' ? (
                    <span className="badge" style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
                      <Shield size={12} /> Dueño
                    </span>
                  ) : (
                    <select value={m.rol} onChange={e => cambiarRol(m, e.target.value)}>
                      {ROLES.map(r => (
                        <option key={r.value} value={r.value}>{r.label}</option>
                      ))}
                    </select>
                  )}
                </td>
                <td>
                  <span className={`badge ${m.activo ? 'badge--success' : 'badge--danger'}`}>
                    {m.activo ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td>
                  {m.rol !== 'DUENO' && (
                    <button className="btn btn--ghost btn--sm" onClick={() => toggleActivo(m)}>
                      {m.activo ? 'Desactivar' : 'Reactivar'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Staff;