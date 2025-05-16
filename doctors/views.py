from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from appointments.models import Appointment
from .models import Doctor

@login_required
def dashboard(request):
    try:
        doctor = Doctor.objects.get(usuario=request.user)
        citas = Appointment.objects.filter(doctor=doctor).order_by('-fecha').select_related('paciente')
        
        # Diccionario para agrupar citas por prioridad del paciente
        citas_por_prioridad = {
            'Urgente': [],
            'Alta': [],
            'Media': [],
            'Baja': [],    
        }

        for cita in citas:
            prioridad = cita.paciente.get_prioridad_display()  # Obtener la etiqueta legible
            if prioridad in citas_por_prioridad:
                citas_por_prioridad[prioridad].append(cita)
            else:
                citas_por_prioridad[prioridad] = [cita]

    except Doctor.DoesNotExist:
        return redirect('doctor_dashboard')  # Cambia esta ruta si quieres

    return render(request, 'dashboard.html', {
        'citas_por_prioridad': citas_por_prioridad,
        'user_type': 'doctor',
    })
