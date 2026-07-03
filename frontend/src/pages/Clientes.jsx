import React, { useState, useMemo } from 'react';
import { Users, Plus, Search, Phone, Mail } from 'lucide-react';
import useFetch from '../hooks/useFetch';
import { getClientes, crearCliente } from '../api/services';

const Clientes = ({ negocioId }) => {
  const { data: clientes, loading, error, refetch } = useFetch(
    () => getClientes(negocioId), [negocioId]
  );

  const [busqueda, setBusqueda] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ nombre: '', telefono: '', email: '' });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');

  const filtrados = useMemo(() => {
    if (!clientes) return [];
    return clientes.filter(c =>
      c.nombre.toLowerCase().includes(busqueda.toLowerCase()) ||
      (c.email || '').toLowerCase().includes(busqueda.toLowerCase()) ||
      (c.telefono || '').includes(busqueda)
    );
  }, [clientes, busqueda]);

  const handleCrear = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError('');
    try {
      await crearCliente(negocioId, form);
      setForm({ nombre: '', telefono: '', email: '' });
      setShowForm(false);
      refetch();
    } catch (err) {
      setFormError(err.response?.data?.error || 'Error al crear el cliente.');
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="loading">Cargando clientes...</div>;
  if (error) return <div className="alert alert--error">{error}</div>;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Clientes</h2>
          <span className="page-subtitle">{filtrados.length} registros</span>
        </div>
        <button className="btn btn--primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} /> Nuevo cliente
        </button>
      </div>

      {/* Formulario */}
      {showForm && (
        <div className="card form-card">
          <h3>Agregar cliente</h3>
          <form onSubmit={handleCrear} className="form-grid">
            <div className="form-group">
              <label>Nombre *</label>
              <input
                type="text"
                value={form.nombre}
                onChange={e => setForm({ ...form, nombre: e.target.value })}
                placeholder="Nombre completo"
                required
              />
            </div>
            <div className="form-group">
              <label>Teléfono</label>
              <input
                type="tel"
                value={form.telefono}
                onChange={e => setForm({ ...form, telefono: e.target.value })}
                placeholder="+56 9 1234 5678"
              />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input
                type="email"
                value={form.email}
                onChange={e => setForm({ ...form, email: e.target.value })}
                placeholder="correo@ejemplo.com"
              />
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
                {saving ? 'Guardando...' : 'Guardar cliente'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Buscador */}
      <div className="card filters-card">
        <div className="filters-row">
          <div className="search-box">
            <Search size={15} />
            <input
              type="text"
              placeholder="Buscar por nombre, email o teléfono..."
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
            />
          </div>
          {busqueda && (
            <button className="btn btn--ghost btn--sm" onClick={() => setBusqueda('')}>
              Limpiar
            </button>
          )}
        </div>
      </div>

      {/* Lista */}
      {filtrados.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <Users size={32} style={{ marginBottom: 8, opacity: 0.3 }} />
            <p>{busqueda ? 'No hay clientes que coincidan con la búsqueda.' : 'Aún no hay clientes registrados.'}</p>
          </div>
        </div>
      ) : (
        <div className="clientes-grid">
          {filtrados.map(c => (
            <div key={c.id} className="cliente-card">
              <div className="cliente-avatar">
                {c.nombre.split(' ').map(p => p[0]).join('').slice(0, 2).toUpperCase()}
              </div>
              <div className="cliente-info">
                <div className="cliente-nombre">{c.nombre}</div>
                <div className="cliente-meta">
                  {c.telefono && (
                    <span className="cliente-dato">
                      <Phone size={12} /> {c.telefono}
                    </span>
                  )}
                  {c.email && (
                    <span className="cliente-dato">
                      <Mail size={12} /> {c.email}
                    </span>
                  )}
                  {!c.telefono && !c.email && (
                    <span className="muted" style={{ fontSize: 12 }}>Sin datos de contacto</span>
                  )}
                </div>
              </div>
              <span className={`badge ${c.activo ? 'badge--success' : 'badge--danger'}`}>
                {c.activo ? 'Activo' : 'Inactivo'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Clientes;
