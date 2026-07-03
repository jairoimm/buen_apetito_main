import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Sidebar from './components/Sidebar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Ventas from './pages/Ventas';
import Inventario from './pages/Inventario';
import Clientes from './pages/Clientes';
import Reportes from './pages/Reportes';
import { getNegocios } from './api/services';
import './App.css';

const NegocioSelector = ({ onSelect }) => {
  const [negocios, setNegocios] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getNegocios()
      .then(data => {
        if (data.length === 1) {
          onSelect(data[0]);
        } else {
          setNegocios(data);
          setLoading(false);
        }
      })
      .catch(() => setLoading(false));
  }, [onSelect]);

  if (loading) return <div className="loading fullscreen">Cargando tu negocio...</div>;

  return (
    <div className="negocio-selector">
      <h2>Selecciona tu negocio</h2>
      <div className="negocio-grid">
        {negocios.map(n => (
          <button key={n.id} className="negocio-card" onClick={() => onSelect(n)}>
            <span className="negocio-card-nombre">{n.nombre}</span>
            <span className="negocio-card-tipo">{n.tipo_negocio}</span>
            <span className="negocio-card-dir">{n.comuna}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

const AppLayout = () => {
  const [negocio, setNegocio] = useState(null);

  if (!negocio) return <NegocioSelector onSelect={setNegocio} />;

  return (
    <div className="app-layout">
      <Sidebar negocio={negocio} />
      <main className="main-content">
        <Routes>
          <Route path="/"           element={<Dashboard   negocioId={negocio.id} />} />
          <Route path="/ventas"     element={<Ventas      negocioId={negocio.id} />} />
          <Route path="/inventario" element={<Inventario  negocioId={negocio.id} />} />
          <Route path="/clientes"   element={<Clientes    negocioId={negocio.id} />} />
          <Route path="/reportes"   element={<Reportes    negocioId={negocio.id} />} />
          <Route path="*"           element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
};

const AuthGuard = () => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <AppLayout /> : <Login />;
};

const App = () => (
  <BrowserRouter>
    <AuthProvider>
      <AuthGuard />
    </AuthProvider>
  </BrowserRouter>
);

export default App;
