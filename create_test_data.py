#!/usr/bin/env python
"""
Script to create test data for MediCitas Pro
"""
import os
import sys
import django
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment

def create_test_data():
    print("🏥 Creando datos de prueba para MediCitas Pro...")
    
    # Create superuser
    if not User.objects.filter(username='admin').exists():
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@medicitas.com',
            password='admin123',
            first_name='Administrador',
            last_name='Sistema'
        )
        print("✅ Superusuario creado: admin / admin123")
    else:
        admin_user = User.objects.get(username='admin')
        print("ℹ️ Superusuario ya existe: admin")
    
    # Create test doctors
    doctors_data = [
        {
            'username': 'dr.martinez',
            'email': 'martinez@medicitas.com',
            'password': 'doctor123',
            'first_name': 'Carlos',
            'last_name': 'Martínez',
            'especialidad': 'Cardiología',
            'telefono': '+1234567890',
            'direccion': 'Av. Principal 123, Ciudad'
        },
        {
            'username': 'dra.rodriguez',
            'email': 'rodriguez@medicitas.com',
            'password': 'doctor123',
            'first_name': 'Ana',
            'last_name': 'Rodríguez',
            'especialidad': 'Pediatría',
            'telefono': '+1234567891',
            'direccion': 'Calle Secundaria 456, Ciudad'
        },
        {
            'username': 'dr.lopez',
            'email': 'lopez@medicitas.com',
            'password': 'doctor123',
            'first_name': 'Miguel',
            'last_name': 'López',
            'especialidad': 'Medicina General',
            'telefono': '+1234567892',
            'direccion': 'Plaza Central 789, Ciudad'
        }
    ]
    
    created_doctors = []
    for doctor_data in doctors_data:
        if not User.objects.filter(username=doctor_data['username']).exists():
            user = User.objects.create_user(
                username=doctor_data['username'],
                email=doctor_data['email'],
                password=doctor_data['password'],
                first_name=doctor_data['first_name'],
                last_name=doctor_data['last_name']
            )
            
            doctor = Doctor.objects.create(
                usuario=user,
                especialidad=doctor_data['especialidad'],
                telefono=doctor_data['telefono'],
                direccion=doctor_data['direccion']
            )
            created_doctors.append(doctor)
            print(f"✅ Doctor creado: {doctor_data['username']} / doctor123")
        else:
            user = User.objects.get(username=doctor_data['username'])
            doctor = Doctor.objects.get(usuario=user)
            created_doctors.append(doctor)
            print(f"ℹ️ Doctor ya existe: {doctor_data['username']}")
    
    # Create test patients
    patients_data = [
        {
            'nombre': 'Juan',
            'apellidos': 'Pérez García',
            'dni': '12345678A',
            'fecha_nacimiento': '1985-03-15',
            'prioridad': 'M',
            'historial_medico_basico': 'Hipertensión controlada, alergia a penicilina',
            'informacion_contacto': 'Tel: +1111111111, Email: juan.perez@email.com, Dir: Calle 1, #123'
        },
        {
            'nombre': 'María',
            'apellidos': 'González López',
            'dni': '87654321B',
            'fecha_nacimiento': '1990-07-22',
            'prioridad': 'A',
            'historial_medico_basico': 'Diabetes tipo 2, seguimiento nutricional',
            'informacion_contacto': 'Tel: +2222222222, Email: maria.gonzalez@email.com, Dir: Avenida 2, #456'
        },
        {
            'nombre': 'Pedro',
            'apellidos': 'Martín Ruiz',
            'dni': '11223344C',
            'fecha_nacimiento': '1978-12-03',
            'prioridad': 'B',
            'historial_medico_basico': 'Paciente sano, chequeos rutinarios',
            'informacion_contacto': 'Tel: +3333333333, Email: pedro.martin@email.com, Dir: Plaza 3, #789'
        },
        {
            'nombre': 'Ana',
            'apellidos': 'Fernández Silva',
            'dni': '55667788D',
            'fecha_nacimiento': '1995-05-18',
            'prioridad': 'U',
            'historial_medico_basico': 'Asma bronquial, uso de inhaladores',
            'informacion_contacto': 'Tel: +4444444444, Email: ana.fernandez@email.com, Dir: Barrio 4, #012'
        },
        {
            'nombre': 'Luis',
            'apellidos': 'Sánchez Moreno',
            'dni': '99887766E',
            'fecha_nacimiento': '1982-09-10',
            'prioridad': 'M',
            'historial_medico_basico': 'Colesterol alto, tratamiento con estatinas',
            'informacion_contacto': 'Tel: +5555555555, Email: luis.sanchez@email.com, Dir: Sector 5, #345'
        }
    ]
    
    created_patients = []
    for patient_data in patients_data:
        if not Patient.objects.filter(dni=patient_data['dni']).exists():
            patient = Patient.objects.create(
                nombre=patient_data['nombre'],
                apellidos=patient_data['apellidos'],
                dni=patient_data['dni'],
                fecha_nacimiento=datetime.strptime(patient_data['fecha_nacimiento'], '%Y-%m-%d').date(),
                prioridad=patient_data['prioridad'],
                historial_medico_basico=patient_data['historial_medico_basico'],
                informacion_contacto=patient_data['informacion_contacto']
            )
            created_patients.append(patient)
            print(f"✅ Paciente creado: {patient_data['nombre']} {patient_data['apellidos']}")
        else:
            patient = Patient.objects.get(dni=patient_data['dni'])
            created_patients.append(patient)
            print(f"ℹ️ Paciente ya existe: {patient_data['nombre']} {patient_data['apellidos']}")
    
    # Create test appointments
    print("\n📅 Creando citas de prueba...")
    
    # Generate appointments for the next 30 days
    today = timezone.now().date()
    
    appointment_templates = [
        {
            'motivo': 'Consulta de control cardiovascular',
            'observaciones': 'Revisar presión arterial y medicación actual'
        },
        {
            'motivo': 'Chequeo pediátrico rutinario',
            'observaciones': 'Vacunas al día, desarrollo normal'
        },
        {
            'motivo': 'Consulta por dolor de cabeza recurrente',
            'observaciones': 'Evaluar posibles causas, solicitar estudios si es necesario'
        },
        {
            'motivo': 'Seguimiento de diabetes',
            'observaciones': 'Revisar niveles de glucosa y ajustar tratamiento'
        },
        {
            'motivo': 'Consulta por síntomas respiratorios',
            'observaciones': 'Evaluar función pulmonar, ajustar medicación para asma'
        },
        {
            'motivo': 'Examen médico general',
            'observaciones': 'Chequeo anual preventivo, solicitar análisis de rutina'
        }
    ]
    
    appointments_created = 0
    for i in range(20):  # Create 20 appointments
        # Random date in the next 30 days
        random_days = random.randint(0, 30)
        appointment_date = today + timedelta(days=random_days)
        
        # Random time during business hours (8 AM to 6 PM)
        random_hour = random.randint(8, 17)
        random_minute = random.choice([0, 30])  # Only :00 or :30 minutes
        
        appointment_datetime = timezone.make_aware(
            datetime.combine(appointment_date, datetime.min.time().replace(hour=random_hour, minute=random_minute))
        )
        
        # Random doctor and patient
        doctor = random.choice(created_doctors)
        patient = random.choice(created_patients)
        template = random.choice(appointment_templates)
        
        # Check if appointment already exists at this time for this doctor
        if not Appointment.objects.filter(doctor=doctor, fecha=appointment_datetime).exists():
            appointment = Appointment.objects.create(
                doctor=doctor,
                paciente=patient,
                fecha=appointment_datetime,
                motivo=template['motivo'],
                observaciones=template['observaciones']
            )
            appointments_created += 1
    
    print(f"✅ {appointments_created} citas creadas exitosamente")
    
    print("\n🎉 ¡Datos de prueba creados exitosamente!")
    print("\n📋 Credenciales de acceso:")
    print("👨‍💼 Administrador: admin / admin123")
    print("👨‍⚕️ Doctores:")
    for doctor_data in doctors_data:
        print(f"   • {doctor_data['username']} / doctor123 ({doctor_data['first_name']} {doctor_data['last_name']} - {doctor_data['especialidad']})")
    
    print(f"\n📊 Resumen:")
    print(f"   • {len(created_doctors)} doctores")
    print(f"   • {len(created_patients)} pacientes")
    print(f"   • {appointments_created} citas")
    
    print("\n🚀 ¡Puedes iniciar el servidor con: python manage.py runserver")

if __name__ == '__main__':
    create_test_data()
