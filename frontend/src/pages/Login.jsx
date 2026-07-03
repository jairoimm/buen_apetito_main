import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Coffee } from 'lucide-react';

const Login = () => {
  const { login } = useAuth();
  const [form, setForm] = useState({ username: '', password: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      await login(form.username, form.password);
    } catch {
      setError('Usuario o contraseña incorrectos.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo">
          <Coffee size={32} />
          <h1>Buen Apetito</h1>
          <p>Panel de administración</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-group">
            <label>Usuario</label>
            <input
              type="text"
              value={form.username}
              onChange={e => setForm({ ...form, username: e.target.value })}
              placeholder="tu_usuario"
              required
            />
          </div>
          <div className="form-group">
            <label>Contraseña</label>
            <input
              type="password"
              value={form.password}
              onChange={e => setForm({ ...form, password: e.target.value })}
              placeholder="••••••••"
              required
            />
          </div>
          {error && <div className="alert alert--error">{error}</div>}
          <button type="submit" className="btn btn--primary btn--full" disabled={loading}>
            {loading ? 'Entrando...' : 'Iniciar sesión'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default Login;