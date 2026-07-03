import React, { useState, useMemo } from 'react';
import useFetch from '../hooks/useFetch';
import { getVentas } from '../api/services';
import { Search, Filter } from 'lucide-react';
 
const fmt = (n) => '$' + Number(n).toLocaleString('es-CL', { maximumFractionDigits: 0 });
const fmtFecha = (s) => new Date(s).toLocaleString('es-CL', {
  day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
});
 
const Ventas = ({ negocioId }) => {
  const { data: ventas, loading, error } = useFetch(() => getVentas(negocioId), [negocioId]);
  const [busqueda, setBusqueda] = useState('');
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [soloNoPagadas, setSoloNoPagadas] = useState(false);
 
  const filtradas = useMemo(() => {
    if (!ventas) return [];
    return ventas.filter(v => {
      const fecha = new Date(v.fecha);
      if (busqueda && !v.numero.toLowerCase().includes(busqueda.toLowerCase()) &&
          !(v.cliente_nombre || '').toLowerCase().includes(busqueda.toLowerCase())) return false;
      if (desde && fecha < new Date(desde)) return false;
      if (hasta && fecha > new Date(hasta + 'T23:59:59')) return false;
      if (soloNoPagadas && v.pagado) return false;
      return true;
    });
  }, [ventas, busqueda, desde, hasta, soloNoPagadas]);
 
  const totalFiltrado = filtradas.reduce((s, v) => s + parseFloat(v.total), 0);
 
  if (loading) return <div className="loading">Cargando ventas...</div>;
  if (error) return <div className="alert alert--error">{error}</div>;
 
  return (
    <div className="page">
      <div className="page-header">
        <h2>Ventas</h2>
        <span className="page-subtitle">{filtradas.length} registros · {fmt(totalFiltrado)} total</span>
      </div>
 
      {/* Filtros */}
      <div className="card filters-card">
        <div className="filters-row">
          <div className="search-box">
            <Search size={15} />
            <input
              type="text"
              placeholder="Buscar por N° o cliente..."
              value={busqueda}
              onChange={e => setBusqueda(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <Filter size={14} />
            <input type="date" value={desde} onChange={e => setDesde(e.target.value)} title="Desde" />
            <span className="filter-sep">—</span>
            <input type="date" value={hasta} onChange={e => setHasta(e.target.value)} title="Hasta" />
          </div>
          <label className="checkbox-label">
            <input type="checkbox" checked={soloNoPagadas}
              onChange={e => setSoloNoPagadas(e.target.checked)} />
            Solo pendientes
          </label>
          {(busqueda || desde || hasta || soloNoPagadas) && (
            <button className="btn btn--ghost btn--sm" onClick={() => {
              setBusqueda(''); setDesde(''); setHasta(''); setSoloNoPagadas(false);
            }}>Limpiar filtros</button>
          )}
        </div>
      </div>
 
      {/* Tabla */}
      <div className="card">
        {filtradas.length === 0 ? (
          <div className="empty-state">No hay ventas que coincidan con los filtros.</div>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>N°</th>
                <th>Fecha</th>
                <th>Cliente</th>
                <th>Productos</th>
                <th>Total</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {filtradas.map(v => (
                <tr key={v.id}>
                  <td><span className="mono">{v.numero}</span></td>
                  <td>{fmtFecha(v.fecha)}</td>
                  <td>{v.cliente_nombre || <span className="muted">Sin cliente</span>}</td>
                  <td>
                    {v.detalle?.map(d => (
                      <span key={d.id} className="tag">{d.producto_nombre} ×{d.cantidad}</span>
                    ))}
                  </td>
                  <td><strong>{fmt(v.total)}</strong></td>
                  <td>
                    <span className={`badge ${v.pagado ? 'badge--success' : 'badge--warning'}`}>
                      {v.pagado ? 'Pagado' : 'Pendiente'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};
 
export default Ventas;