import client from './client';
import axios from 'axios';
 
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';
 
// ── Auth ──────────────────────────────────────────────────────────────────
export const login = async (username, password) => {
  const { data } = await axios.post(`${BASE_URL}/auth/login/`, { username, password });
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
  return data;
};
 
export const logout = () => localStorage.clear();
 
// ── Negocios ──────────────────────────────────────────────────────────────
export const getNegocios = () => client.get('/negocios/').then(r => r.data);
 
// ── Ventas ────────────────────────────────────────────────────────────────
export const getVentas = (negocioId) =>
  client.get(`/negocios/${negocioId}/ventas/`).then(r => r.data);
 
export const crearVenta = (negocioId, data) =>
  client.post(`/negocios/${negocioId}/ventas/`, data).then(r => r.data);
 
// ── Reportes ──────────────────────────────────────────────────────────────
export const getReporteVentas = (negocioId, params = {}) =>
  client.get(`/negocios/${negocioId}/reportes/ventas/`, { params }).then(r => r.data);
 
// ── Inventario ────────────────────────────────────────────────────────────
export const getInventario = (negocioId, params = {}) =>
  client.get(`/negocios/${negocioId}/inventario/`, { params }).then(r => r.data);
 
export const getMovimientos = (negocioId) =>
  client.get(`/negocios/${negocioId}/movimientos/`).then(r => r.data);
 
export const registrarMovimiento = (negocioId, data) =>
  client.post(`/negocios/${negocioId}/movimientos/`, data).then(r => r.data);
 
// ── Productos ─────────────────────────────────────────────────────────────
export const getProductos = (negocioId) =>
  client.get(`/negocios/${negocioId}/productos/`).then(r => r.data);
 
// ── Clientes ──────────────────────────────────────────────────────────────
export const getClientes = (negocioId) =>
  client.get(`/negocios/${negocioId}/clientes/`).then(r => r.data);
 
export const crearCliente = (negocioId, data) =>
  client.post(`/negocios/${negocioId}/clientes/`, data).then(r => r.data);