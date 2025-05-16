from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import AppointmentForm
from .models import Appointment
from doctors.models import Doctor  # Importa el modelo Doctor para obtener el doctor logueado

@login_required
def crear_cita(request):
    doctor = Doctor.objects.get(usuario=request.user)  # Obtén el doctor actual según el usuario

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            cita = form.save(commit=False)  # No guardes aún para asignar doctor
            cita.doctor = doctor  # Asigna el doctor logueado
            cita.save()
            return redirect('doctor_dashboard')
    else:
        form = AppointmentForm()
    
    return render(request, 'crear_cita.html', {'form': form})
