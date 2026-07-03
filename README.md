# Buen Apetito 🍵

Sistema de gestión para cafeterías y negocios gastronómicos. Backend construido con **Django + Django REST Framework**.

## Funcionalidades

- **Autenticación JWT** — login seguro con tokens de acceso y refresh
- **Gestión de negocios** — cada usuario administra sus propios locales
- **Inventario** — insumos, stock, movimientos (compras, mermas, ajustes)
- **Menú** — categorías, productos y recetas (qué insumos consume cada producto)
- **Ventas** — registro de ventas con descuento automático de stock
- **Clientes** — base de datos de clientes por negocio
- **Reportes** — resumen de ventas, ticket promedio, productos top


## Instalación

- **Backend(DJANGO) para ejecutar el proyecto en tu maquina local, sigue estos pasos:

    1. primero, navega a la carpeta del backend y asegurate de instalar las dependecias:

    2. cd backend
    3. pip install -r requirements.txt
    4. python manage.py migrate
    5. python manage.py runserver

- **Frontend(REACT) en una termina, navega a la carpeta del frontend y ejecuta :

    1. cd frontend
    2. npm install
    3. npm start

- **Asegurate de tener instalado Python y Node.js