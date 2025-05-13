from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import Http404
from appointments.models import Appointment  # Cambiar la importación aquí
from .models import Doctor

@login_required
def dashboard(request):
    try:
        # Obtener el doctor asociado con el usuario autenticado
        doctor = Doctor.objects.get(usuario=request.user)
        
        # Filtrar las citas que tienen al doctor como su doctor
        citas = Appointment.objects.filter(doctor=doctor).order_by('-fecha')  # Citas del doctor

    except Doctor.DoesNotExist:
        # Si el usuario no es un doctor, redirigir a una página de inicio o error
        return redirect('inicio')  # Puedes cambiar 'inicio' por la ruta que prefieras
    
    return render(request, 'dashboard.html', {'citas': citas, 'user_type': 'doctor'})
