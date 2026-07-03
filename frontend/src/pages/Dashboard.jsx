import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, BarChart, Bar, Cell
} from 'recharts';
import { ShoppingBag, Users, Package, TrendingUp } from 'lucide-react';
import StatCard from '../components/StatCard';
import useFetch from '../hooks/useFetch';
import { getReporteVentas, getVentas, getInventario } from '../api/services';
 
const fmt = (n) =>
  n == null ? '$0' : '$' + Number(n).toLocaleString('es-CL', { maximumFractionDigits: 0 });
 
const COLORS = ['#c8965a', '#a07040', '#e0b882', '#7a5030', '#f0d0a0'];
 
const Dashboard = ({ negocioId }) => {
  const { data: reporte, loading: rLoading } = useFetch(
    () => getReporteVentas(negocioId), [negocioId]
  );
  const { data: ventas, loading: vLoading } = useFetch(
    () => getVentas(negocioId), [negocioId]
  );
  const { data: inventario } = useFetch(
    () => getInventario(negocioId), [negocioId]
  );
 
  // Build daily sales chart from ventas
  const ventasPorDia = React.useMemo(() => {
    if (!ventas) return [];
    const map = {};
    ventas.forEach(v => {
      const dia = new Date(v.fecha).toLocaleDateString('es-CL', { day: '2-digit', month: 'short' });
      map[dia] = (map[dia] || 0) + parseFloat(v.total);
    });
    return Object.entries(map)
      .slice(-7)
      .map(([dia, total]) => ({ dia, total }));
  }, [ventas]);
 
  const bajosStock = inventario?.filter(i => i.bajo_stock) || [];
 
  if (rLoading || vLoading) return <div className="loading">Cargando resumen...</div>;
 
  return (
    <div className="page">
      <div className="page-header">
        <h2>Resumen</h2>
        <span className="page-subtitle">Vista general de tu negocio</span>
      </div>
 
      {/* Stat cards */}
      <div className="stats-grid">
        <StatCard
          label="Ingresos totales"
          value={fmt(reporte?.resumen?.ingresos_totales)}
          icon={TrendingUp}
          color="gold"
        />
        <StatCard
          label="Total ventas"
          value={reporte?.resumen?.total_ventas ?? 0}
          icon={ShoppingBag}
          color="warm"
        />
        <StatCard
          label="Ticket promedio"
          value={fmt(reporte?.resumen?.ticket_promedio)}
          icon={TrendingUp}
          color="accent"
        />
        <StatCard
          label="Alertas de stock"
          value={bajosStock.length}
          icon={Package}
          color={bajosStock.length > 0 ? 'danger' : 'safe'}
        />
      </div>
 
      <div className="charts-row">
        {/* Area chart — ventas últimos 7 días */}
        <div className="card chart-card">
          <div className="card-header">
            <h3>Ventas últimos 7 días</h3>
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={ventasPorDia} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="gradVentas" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#c8965a" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#c8965a" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis dataKey="dia" tick={{ fill: '#8a7a6a', fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8a7a6a', fontSize: 11 }} axisLine={false} tickLine={false}
                tickFormatter={v => '$' + (v / 1000).toFixed(0) + 'k'} />
              <Tooltip
                contentStyle={{ background: '#1e1a16', border: '1px solid #3a3028', borderRadius: 8 }}
                labelStyle={{ color: '#e8d5b8' }}
                formatter={v => [fmt(v), 'Total']}
              />
              <Area type="monotone" dataKey="total" stroke="#c8965a" strokeWidth={2}
                fill="url(#gradVentas)" dot={{ fill: '#c8965a', r: 3 }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
 
        {/* Bar chart — productos top */}
        <div className="card chart-card">
          <div className="card-header">
            <h3>Productos más vendidos</h3>
          </div>
          {reporte?.productos_top?.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={reporte.productos_top} layout="vertical"
                margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#8a7a6a', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="nombre" tick={{ fill: '#c8b090', fontSize: 11 }}
                  axisLine={false} tickLine={false} width={90} />
                <Tooltip
                  contentStyle={{ background: '#1e1a16', border: '1px solid #3a3028', borderRadius: 8 }}
                  labelStyle={{ color: '#e8d5b8' }}
                  formatter={v => [v, 'veces vendido']}
                />
                <Bar dataKey="veces_vendido" radius={[0, 4, 4, 0]}>
                  {reporte.productos_top.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="empty-state">Aún no hay ventas registradas.</div>
          )}
        </div>
      </div>
 
      {/* Stock alerts */}
      {bajosStock.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h3>⚠️ Insumos con stock bajo</h3>
          </div>
          <table className="table">
            <thead>
              <tr>
                <th>Insumo</th>
                <th>Stock actual</th>
                <th>Mínimo</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {bajosStock.map(inv => (
                <tr key={inv.id}>
                  <td>{inv.insumo_nombre}</td>
                  <td>{inv.stock_actual} {inv.unidad_medida}</td>
                  <td>{inv.stock_minimo} {inv.unidad_medida}</td>
                  <td><span className="badge badge--danger">Stock bajo</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
 
export default Dashboard;