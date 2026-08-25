# Buen Apetito 🍵

Sistema integral de gestión y punto de venta (POS) para cafeterías y negocios gastronómicos, diseñado con una arquitectura moderna de **API REST en Django** y una **Progressive Web App (PWA) en React**.

---

## 🏗️ Arquitectura del Sistema

- **Backend (`/backend`)**: Django 5.2 + Django REST Framework (DRF), SimpleJWT para autenticación, WhiteNoise para archivos estáticos y PostgreSQL / SQLite para almacenamiento de datos.
- **Frontend (`/frontend`)**: React 19 (Create React App), React Router v7, Tailwind/CSS personalizado, Axios e integración PWA (Service Worker con caché inteligente *Network First* para menú e imágenes).
- **Despliegue Recomendado**:
  - **Backend**: Render / Railway (con PostgreSQL en producción).
  - **Frontend**: Vercel (PWA optimizada).

---

## 🚀 Funcionalidades Principales

1. **Autenticación JWT Segura** — Gestión de tokens de acceso y renovación automática.
2. **Gestión Multi-negocio** — Administración centralizada de múltiples locales y roles de staff.
3. **Control de Inventario** — Registro de insumos, stock en tiempo real, compras, mermas y ajustes.
4. **Menú y Recetas** — Categorización de productos y control de insumos consumidos por receta.
5. **Punto de Venta y Ventas** — Registro de ventas con descuento automático e instantáneo de stock.
6. **Base de Datos de Clientes** — Seguimiento y gestión de clientes por negocio.
7. **Reportes y Analíticas** — Resumen financiero, ticket promedio, ventas por periodo y productos más vendidos.
8. **Soporte Offline (PWA)** — Funcionamiento como aplicación de escritorio/móvil independiente con caché local para cargas instantáneas del menú.

---

## 🛠️ Guía de Instalación Local

### Requisitos Previos
- Python 3.10+ instalado.
- Node.js 18+ y npm instalados.

### 1. Configuración del Backend (Django)

Navega a la carpeta del backend, crea y activa tu entorno virtual, instala las dependencias y ejecuta las migraciones:

```bash
cd backend
python -m venv venv

# En Windows (PowerShell o CMD):
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Aplicar migraciones de base de datos
python manage.py migrate

# Iniciar servidor de desarrollo del backend
python manage.py runserver
```
El backend estará disponible en `http://localhost:8000/api`.

### 2. Configuración del Frontend (React PWA)

En otra terminal, navega a la carpeta del frontend, instala las dependencias e inicia el entorno de desarrollo:

```bash
cd frontend
npm install
npm start
```
El frontend estará disponible en `http://localhost:3000`.

---

## 📦 Despliegue en Producción

### Variables de Entorno del Backend (Render)
- `DEBUG` = `False`
- `SECRET_KEY` = `[clave_secreta_django]`
- `DATABASE_URL` = `[url_de_conexion_postgresql]`
- `ALLOWED_HOSTS` = `tu-backend.onrender.com`
- `CORS_ALLOWED_ORIGINS` = `https://tu-frontend.vercel.app`

### Variables de Entorno del Frontend (Vercel)
- `REACT_APP_API_URL` = `https://tu-backend.onrender.com/api`
