# Buen Apetito - Guía para Agentes

Sistema de gestión para cafeterías y negocios gastronómicos (Backend Django + Frontend React).

## Comandos de Desarrollo

### Backend (`/backend`)
- **Instalar dependencias:** `pip install -r requirements.txt`
- **Migraciones:** `python manage.py migrate`
- **Servidor local:** `python manage.py runserver`
- **Ejecutar tests:** `python manage.py test`

### Frontend (`/frontend`)
- **Instalar dependencias:** `npm install`
- **Servidor local:** `npm start`
- **Build de producción:** `CI=false npm run build`
- **Ejecutar tests:** `npm test`

## Arquitectura y Estructura
- **`backend/`**: Django REST Framework + SimpleJWT.
  - `negocios/`: App principal que contiene modelos, vistas, tests y lógica de negocio (`negocios/services/`).
  - Base de datos predeterminada: SQLite (`backend/db.sqlite3`).
- **`frontend/`**: React 19 con React Router v7 y Tailwind/CSS personalizado.
  - `src/pages/`: Vistas principales (Ventas, Inventario, Menú, Reportes, Clientes, Staff, Login, Dashboard).
  - `src/api/`: Cliente HTTP y servicios de comunicación con el backend (`client.js`, `services.js`).

## Notas y Convenciones
- Lenguaje principal: **Español** (tanto en código, comentarios como en interfaz de usuario).
- Mantener la separación estricta entre la API REST en Django y la SPA en React.
