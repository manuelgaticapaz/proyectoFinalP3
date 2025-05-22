Citas Médicas - Aplicación Web

Este proyecto es una aplicación web para gestionar citas médicas, creada con el framework Django. La plataforma permite a los médicos tener un usuario individual donde pueden gestionar sus citas, pacientes y compartir información con otros médicos. Los pacientes también pueden ser compartidos entre doctores para un seguimiento más eficiente de su historial médico.

Características

- Registro y autenticación de médicos: Cada médico tiene su propio usuario y contraseña para acceder al sistema.
- Gestión de pacientes: Los administradores pueden registrar, editar y eliminar pacientes.
- Citas médicas: Los médicos pueden agendar, ver y eliminar citas con los pacientes.
- Compartir pacientes entre médicos: Los médicos pueden compartir pacientes entre sí para una atención más completa.
- Visualización de citas por paciente: Los médicos pueden consultar el historial de citas de un paciente específico.
- Interfaz amigable: Interfaz sencilla y accesible para la gestión de información médica.

Tecnologías utilizadas

- Django - Framework de Python para el desarrollo web.
- SQLite - Base de datos por defecto en Django para el almacenamiento de información.
- HTML, CSS, JavaScript - Para la creación de las interfaces de usuario.


Requisitos

Asegúrate de tener instalados los siguientes programas en tu entorno:

- Python 3.x
- pip
- Django

Instalación

1. Clona el repositorio:

2. Crea un entorno virtual:

python -m venv venv
source venv/bin/activate  # En Linux o macOS

venv\Scripts\activate     # En Windows


3. Inicia el servidor de desarrollo:

python manage.py runserver

Ahora puedes acceder a la aplicación en http://127.0.0.1:8000.

Uso

1. Después de iniciar sesión, los medicos podrán acceder a sus paneles personales.
2. Agendar citas: Cada médico podrá ver el calendario de sus citas y agendar nuevas citas con los pacientes.
3. Compartir pacientes: Un médico puede compartir un paciente con otro médico a través de su perfil de paciente.
4. Historial de citas: Los médicos podrán consultar el historial de citas de cualquier paciente asignado a su cuenta.
