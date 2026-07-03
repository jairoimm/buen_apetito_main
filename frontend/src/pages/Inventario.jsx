import React, { useState, useMemo } from 'react';
import useFetch from '../hooks/useFetch';
import { getInventario, getInsumos, registrarMovimiento } from '../api/services';
import { AlertTriangle, Plus } from 'lucide-react';
 
// getInsumos not exported yet — add it
import client from '../api/client';
const fetchInsumos = (negocioId) =>
  client.get(`/negocios/${negocioId}/insumos/`).then(r => r.data);
 
const Inventario = ({ negocioId }) => {
  const { data: inventario, loading, error, refetch } = useFetch(
    () => getInventario(negocioId), [negocioId]
  );
  const { data: insumos } = useFetch(() => fetchInsumos(negocioId), [negocioId]);
 
  const [filtro, setFiltro] = useState('todos');
  const [busqueda, setBusqueda] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [mov, setMov] = useState({ insumo: '', tipo: 'COMPRA', cantidad: '', referencia: '' });
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState('');
 
  const filtrado = useMemo(() => {
    if (!inventario) return [];
    return inventario.filter(inv => {
      if (busqueda && !inv.insumo_nombre.toLowerCase().includes(busqueda.toLowerCase())) return false;
      if (filtro === 'bajo') return inv.bajo_stock;
      if (filtro === 'ok') return !inv.bajo_stock;
      return true;
    });
  }, [inventario, filtro, busqueda]);
 
  const handleMovimiento = async (e) => {
    e.preventDefault();
    setSaving(true);
    setFormError('');
    try {
      const cantidad = mov.tipo === 'MERMA' || mov.tipo === 'VENTA'
        ? -Math.abs(parseFloat(mov.cantidad))
        : Math.abs(parseFloat(mov.cantidad));
      await registrarMovimiento(negocioId, { ...mov, cantidad });
      setMov({ insumo: '', tipo: 'COMPRA', cantidad: '', referencia: '' });
      setShowForm(false);
      refetch();
    } catch (err) {
      setFormError(err.response?.data?.error || 'Error al registrar movimiento.');
    } finally {
      setSaving(false);
    }
  };
 
  if (loading) return <div className="loading">Cargando inventario...</div>;
  if (error) return <div className="alert alert--error">{error}</div>;
 
  const bajosStock = inventario?.filter(i => i.bajo_stock).length || 0;
 
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Inventario</h2>
          <span className="page-subtitle">{filtrado.length} insumos</span>
        </div>
        <button className="btn btn--primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} /> Registrar movimiento
        </button>
      </div>
 
      {bajosStock > 0 && (
        <div className="alert alert--warning">
          <AlertTriangle size={16} />
          {bajosStock} insumo(s) con stock bajo el mínimo. Revisa la columna Estado.
        </div>
      )}
 
      {/* Formulario movimiento */}
      {showForm && (
        <div className="card form-card">
          <h3>Nuevo movimiento de inventario</h3>
          <form onSubmit={handleMovimiento} className="form-grid">
            <div className="form-group">
              <label>Insumo</label>
              <select value={mov.insumo} onChange={e => setMov({ ...mov, insumo: e.target.value })} required>
                <option value="">Seleccionar insumo...</option>
                {insumos?.map(i => (
                  <option key={i.id} value={i.id}>{i.nombre} ({i.unidad_medida})</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label>Tipo</label>
              <select value={mov.tipo} onChange={e => setMov({ ...mov, tipo: e.target.value })}>
                <option value="COMPRA">Compra (+)</option>
                <option value="AJUSTE">Ajuste manual</option>
                <option value="MERMA">Merma (−)</option>
              </select>
            </div>
            <div className="form-group">
              <label>Cantidad</label>
              <input type="number" step="0.001" min="0.001" value={mov.cantidad}
                onChange={e => setMov({ ...mov, cantidad: e.target.value })} required />
            </div>
            <div className="form-group form-group--full">
              <label>Referencia (opcional)</label>
              <input type="text" value={mov.referencia}
                onChange={e => setMov({ ...mov, referencia: e.target.value })}
                placeholder="Ej: Proveedor Central, ajuste conteo..." />
            </div>
            {formError && <div className="alert alert--error form-group--full">{formError}</div>}
            <div className="form-actions">
              <button type="button" className="btn btn--ghost" onClick={() => setShowForm(false)}>Cancelar</button>
              <button type="submit" className="btn btn--primary" disabled={saving}>
                {saving ? 'Guardando...' : 'Guardar movimiento'}
              </button>
            </div>
          </form>
        </div>
      )}
 
      {/* Filtros */}
      <div className="tabs">
        {['todos', 'ok', 'bajo'].map(t => (
          <button key={t} className={`tab ${filtro === t ? 'tab--active' : ''}`}
            onClick={() => setFiltro(t)}>
            {t === 'todos' ? 'Todos' : t === 'ok' ? '✓ Stock normal' : '⚠ Stock bajo'}
          </button>
        ))}
        <input type="text" className="tab-search" placeholder="Buscar insumo..."
          value={busqueda} onChange={e => setBusqueda(e.target.value)} />
      </div>
 
      {/* Tabla */}
      <div className="card">
        <table className="table">
          <thead>
            <tr>
              <th>Insumo</th>
              <th>Unidad</th>
              <th>Stock actual</th>
              <th>Reservado</th>
              <th>Disponible</th>
              <th>Mínimo</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {filtrado.map(inv => (
              <tr key={inv.id}>
                <td><strong>{inv.insumo_nombre}</strong></td>
                <td className="muted">{inv.unidad_medida}</td>
                <td>{inv.stock_actual}</td>
                <td>{inv.stock_reservado}</td>
                <td><strong>{inv.stock_disponible}</strong></td>
                <td>{inv.stock_minimo}</td>
                <td>
                  <span className={`badge ${inv.bajo_stock ? 'badge--danger' : 'badge--success'}`}>
                    {inv.bajo_stock ? 'Stock bajo' : 'Normal'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
 
export default Inventario;