# 🏥 MediCitas Pro - Sistema de Gestión de Citas Médicas

Una aplicación web moderna y profesional para la gestión integral de citas médicas, desarrollada con Django. La plataforma permite a los médicos gestionar eficientemente sus citas, pacientes y compartir información con otros profesionales de la salud.

## ✨ Características Principales

### 🔐 Autenticación y Seguridad
- **Sistema de login moderno** con interfaz mejorada y validaciones en tiempo real
- **Autenticación segura** para médicos con sesiones controladas
- **Gestión de permisos** por tipo de usuario

### 👨‍⚕️ Gestión de Médicos
- **Dashboard personalizado** con estadísticas en tiempo real
- **Perfil individual** para cada médico
- **Visualización optimizada** de citas por prioridad

### 📅 Sistema de Citas
- **Creación intuitiva** de citas con formularios modernos
- **Filtrado avanzado** por fechas y rangos temporales
- **Organización por prioridad** (Urgente, Alta, Media, Baja)
- **Validación automática** de horarios y conflictos

### 👥 Gestión de Pacientes
- **Registro completo** de información del paciente
- **Sistema de prioridades** para atención médica
- **Compartir pacientes** entre médicos para seguimiento colaborativo
- **Historial médico** accesible

### 📊 Estadísticas y Reportes
- **Dashboard con métricas** en tiempo real
- **Contadores dinámicos** de citas totales, del día y semanales
- **Análisis de carga de trabajo** por médico
- **Reportes personalizables** por períodos

### 🎨 Interfaz Moderna
- **Diseño responsivo** con Bootstrap 5
- **Iconografía profesional** con Bootstrap Icons
- **Animaciones suaves** y efectos visuales
- **Experiencia de usuario optimizada**

## 🛠️ Tecnologías Utilizadas

### Backend
- **Django 5.2.1** - Framework web de Python
- **Django REST Framework** - API REST para integraciones
- **MySQL** - Base de datos principal (migrado desde SQLite)
- **Python 3.x** - Lenguaje de programación

### Frontend
- **Bootstrap 5.3.2** - Framework CSS moderno
- **Bootstrap Icons** - Iconografía profesional
- **JavaScript ES6+** - Interactividad y validaciones
- **CSS3 con Gradientes** - Diseño visual atractivo

### Optimización
- **Consultas optimizadas** con select_related y prefetch_related
- **Sistema de caché** para estadísticas frecuentes
- **Funciones utilitarias** para procesamiento eficiente de datos
- **Validaciones del lado cliente** para mejor UX


## 📋 Requisitos del Sistema

### Requisitos Previos
- **Python 3.8+** - Lenguaje de programación
- **pip** - Gestor de paquetes de Python
- **MySQL 8.0+** - Sistema de base de datos
- **Git** - Control de versiones (opcional)

### Dependencias Principales
- **Django 5.2.1** - Framework web
- **djangorestframework 3.16.0** - API REST
- **mysqlclient 2.2.4** - Conector MySQL
- **Bootstrap 5.3.2** - Framework CSS (CDN)

## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio
```bash
git clone [URL_DEL_REPOSITORIO]
cd proyectoFinalP3
```

### 2. Crear Entorno Virtual
```bash
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/macOS:
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
# Instalar todas las dependencias
pip install -r requirements.txt

# Si hay problemas con mysqlclient en Windows:
pip install mysqlclient==2.2.4
```

### 4. Configurar Base de Datos MySQL
```sql
-- Crear base de datos en MySQL
CREATE DATABASE proyectodb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear usuario (opcional)
CREATE USER 'medico_user'@'localhost' IDENTIFIED BY 'tu_password_segura';
GRANT ALL PRIVILEGES ON proyectodb.* TO 'medico_user'@'localhost';
FLUSH PRIVILEGES;
```

### 5. Configurar Variables de Entorno
Actualiza las credenciales en `core/settings.py`:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'proyectodb',
        'USER': 'root',  # o tu usuario MySQL
        'PASSWORD': 'admin1234',  # tu contraseña MySQL
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```

### 6. Ejecutar Migraciones
```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser
```

### 7. Iniciar Servidor de Desarrollo
```bash
python manage.py runserver
```

## 🌐 Acceso a la Aplicación

### URLs Principales
- **Aplicación Principal**: http://127.0.0.1:8000/
- **Panel de Administración**: http://127.0.0.1:8000/admin/
- **Dashboard Médico**: http://127.0.0.1:8000/doctors/dashboard/

### APIs REST Disponibles
- **Citas**: http://127.0.0.1:8000/api/v1/appointments/citas/
- **Doctores**: http://127.0.0.1:8000/api/v1/doctors/doctor/
- **Pacientes**: http://127.0.0.1:8000/api/v1/patients/paciente/

## 📖 Guía de Uso

### Para Médicos
1. **Iniciar Sesión**: Accede con tus credenciales médicas
2. **Dashboard**: Visualiza estadísticas y citas del día
3. **Crear Citas**: Utiliza el formulario intuitivo para agendar
4. **Gestionar Pacientes**: Consulta y actualiza información
5. **Filtrar Citas**: Usa los filtros por fecha y prioridad

### Funcionalidades Destacadas
- **Estadísticas en Tiempo Real**: Métricas actualizadas automáticamente
- **Validación de Horarios**: Prevención de conflictos de citas
- **Interfaz Responsiva**: Funciona en dispositivos móviles y desktop
- **Autoguardado**: Borradores automáticos en formularios
- **Notificaciones**: Alertas y confirmaciones visuales

## 🔧 Mejoras Implementadas

### ✅ Optimizaciones Realizadas
- ❌ **Eliminado**: Archivo `db.sqlite3` no utilizado
- 🧹 **Limpieza**: Carpetas `__pycache__` removidas
- 📝 **Agregado**: Archivo `.gitignore` completo
- 🔄 **Actualizado**: `requirements.txt` con `mysqlclient`
- 🎨 **Modernizado**: UI con Bootstrap 5 y diseño responsivo
- ⚡ **Optimizado**: Consultas de base de datos y funciones utilitarias
- 📊 **Agregado**: Sistema de estadísticas en tiempo real

### 🆕 Nuevas Características
- **Template Base**: Sistema de plantillas unificado
- **Dashboard Mejorado**: Estadísticas visuales y tarjetas informativas
- **Formularios Modernos**: Validación en tiempo real y autoguardado
- **Sistema de Utilidades**: Funciones optimizadas para rendimiento
- **Interfaz Profesional**: Gradientes, animaciones y efectos visuales
