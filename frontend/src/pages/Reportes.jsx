import React, { useState, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { BarChart2, Search } from 'lucide-react';
import { getReporteVentas } from '../api/services';
import useFetch from '../hooks/useFetch';

const fmt = (n) =>
  n == null ? '$0' : '$' + Number(n).toLocaleString('es-CL', { maximumFractionDigits: 0 });

const COLORS = ['#c8965a', '#a07040', '#e0b882', '#7a5030', '#f0d0a0'];

const Reportes = ({ negocioId }) => {
  const [desde, setDesde] = useState('');
  const [hasta, setHasta] = useState('');
  const [params, setParams] = useState({});

  const fetchReporte = useCallback(
    () => getReporteVentas(negocioId, params),
    [negocioId, params]
  );
  const { data: reporte, loading, error } = useFetch(fetchReporte, [params]);

  const aplicarFiltros = () => {
    const p = {};
    if (desde) p.fecha_inicio = desde;
    if (hasta) p.fecha_fin = hasta;
    setParams(p);
  };

  const limpiarFiltros = () => {
    setDesde('');
    setHasta('');
    setParams({});
  };

  const hayFiltros = desde || hasta;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Reportes</h2>
          <span className="page-subtitle">Análisis de ventas</span>
        </div>
      </div>

      {/* Filtros de fecha */}
      <div className="card filters-card">
        <div className="filters-row">
          <div className="filter-group">
            <BarChart2 size={14} />
            <label style={{ fontSize: 13, color: 'var(--color-text-secondary, #8a7a6a)', marginRight: 4 }}>
              Desde
            </label>
            <input
              type="date"
              value={desde}
              onChange={e => setDesde(e.target.value)}
            />
          </div>
          <div className="filter-group">
            <label style={{ fontSize: 13, color: 'var(--color-text-secondary, #8a7a6a)', marginRight: 4 }}>
              Hasta
            </label>
            <input
              type="date"
              value={hasta}
              onChange={e => setHasta(e.target.value)}
            />
          </div>
          <button className="btn btn--primary btn--sm" onClick={aplicarFiltros}>
            <Search size={14} /> Aplicar
          </button>
          {hayFiltros && (
            <button className="btn btn--ghost btn--sm" onClick={limpiarFiltros}>
              Limpiar
            </button>
          )}
        </div>
        {hayFiltros && (
          <div style={{ marginTop: 8, fontSize: 12, color: 'var(--color-text-tertiary, #a09080)' }}>
            Mostrando datos {desde && `desde ${desde}`} {hasta && `hasta ${hasta}`}
          </div>
        )}
      </div>

      {loading && <div className="loading">Cargando reporte...</div>}
      {error && <div className="alert alert--error">{error}</div>}

      {reporte && !loading && (
        <>
          {/* Tarjetas resumen */}
          <div className="stats-grid" style={{ marginBottom: '1rem' }}>
            <div className="stat-card stat-card--gold">
              <div className="stat-card-top">
                <span className="stat-card-label">Ingresos totales</span>
              </div>
              <div className="stat-card-value">{fmt(reporte.resumen?.ingresos_totales)}</div>
            </div>
            <div className="stat-card stat-card--warm">
              <div className="stat-card-top">
                <span className="stat-card-label">Total de ventas</span>
              </div>
              <div className="stat-card-value">{reporte.resumen?.total_ventas ?? 0}</div>
            </div>
            <div className="stat-card stat-card--accent">
              <div className="stat-card-top">
                <span className="stat-card-label">Ticket promedio</span>
              </div>
              <div className="stat-card-value">{fmt(reporte.resumen?.ticket_promedio)}</div>
            </div>
          </div>

          {/* Gráfico productos top */}
          <div className="card chart-card">
            <div className="card-header">
              <h3>Top 5 productos más vendidos</h3>
              {hayFiltros && (
                <span className="pill">Filtrado por fecha</span>
              )}
            </div>
            {reporte.productos_top?.length > 0 ? (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart
                  data={reporte.productos_top}
                  margin={{ top: 10, right: 20, left: 0, bottom: 40 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                  <XAxis
                    dataKey="nombre"
                    tick={{ fill: '#c8b090', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                    angle={-20}
                    textAnchor="end"
                    interval={0}
                  />
                  <YAxis
                    tick={{ fill: '#8a7a6a', fontSize: 11 }}
                    axisLine={false}
                    tickLine={false}
                  />
                  <Tooltip
                    contentStyle={{
                      background: '#1e1a16',
                      border: '1px solid #3a3028',
                      borderRadius: 8,
                    }}
                    labelStyle={{ color: '#e8d5b8' }}
                    formatter={(v, name) => [
                      v,
                      name === 'veces_vendido' ? 'veces vendido' : 'ingresos'
                    ]}
                  />
                  <Bar dataKey="veces_vendido" radius={[4, 4, 0, 0]}>
                    {reporte.productos_top.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state">No hay ventas en el período seleccionado.</div>
            )}
          </div>

          {/* Tabla detalle */}
          {reporte.productos_top?.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3>Detalle por producto</h3>
              </div>
              <table className="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Producto</th>
                    <th>Veces vendido</th>
                    <th>Ingresos generados</th>
                  </tr>
                </thead>
                <tbody>
                  {reporte.productos_top.map((p, i) => (
                    <tr key={p.id}>
                      <td>
                        <span
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: 24,
                            height: 24,
                            borderRadius: '50%',
                            background: COLORS[i % COLORS.length],
                            color: '#1e1a16',
                            fontSize: 11,
                            fontWeight: 600,
                          }}
                        >
                          {i + 1}
                        </span>
                      </td>
                      <td><strong>{p.nombre}</strong></td>
                      <td>{p.veces_vendido} veces</td>
                      <td style={{ color: '#c8965a', fontWeight: 500 }}>
                        {fmt(p.ingresos)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {/* Estado vacío inicial */}
      {!reporte && !loading && !error && (
        <div className="card">
          <div className="empty-state">
            <BarChart2 size={32} style={{ marginBottom: 8, opacity: 0.3 }} />
            <p>Selecciona un rango de fechas y haz clic en Aplicar para ver el reporte.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reportes;
