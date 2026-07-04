import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard, ShoppingBag, Package,
  Users, BarChart2, LogOut, Coffee, UserCog
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Sidebar = ({ negocio, permisos }) => {
  const { logout } = useAuth();

  const links = [
    { to: '/',           icon: LayoutDashboard, label: 'Resumen',    show: true },
    { to: '/ventas',     icon: ShoppingBag,     label: 'Ventas',     show: true },
    { to: '/inventario', icon: Package,         label: 'Inventario', show: true },
    { to: '/clientes',   icon: Users,           label: 'Clientes',   show: true },
    { to: '/reportes',   icon: BarChart2,       label: 'Reportes',   show: permisos?.ver_reportes },
    { to: '/staff',      icon: UserCog,         label: 'Equipo',     show: permisos?.gestionar_usuarios },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Coffee size={20} />
        <span>Buen Apetito</span>
      </div>

      {negocio && (
        <div className="sidebar-negocio">
          <span className="sidebar-negocio-label">Negocio activo</span>
          <span className="sidebar-negocio-nombre">{negocio.nombre}</span>
        </div>
      )}

      <nav className="sidebar-nav">
        {links.filter(l => l.show).map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? 'sidebar-link--active' : ''}`
            }
            end={to === '/'}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <button className="sidebar-logout" onClick={logout}>
        <LogOut size={18} />
        <span>Cerrar sesión</span>
      </button>
    </aside>
  );
};

export default Sidebar;