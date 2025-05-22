from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone # Para obtener la fecha actual con zona horaria
from datetime import timedelta, date
from appointments.models import Appointment
from .models import Doctor # Asegúrate que este es el modelo correcto para Doctor

@login_required
def dashboard(request):
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        # Redirige a una página donde el usuario pueda crear un perfil de doctor
        # o a una página de error genérica. 'doctor_dashboard' podría ser un bucle
        # si el perfil aún no existe.
        return redirect('crear_perfil_doctor') # O alguna otra ruta apropiada

    today = timezone.now().date()
    start_date_filter = today  # Por defecto, desde hoy
    filter_description = "Citas de hoy en adelante"

    # Comprobar si se solicita el rango extendido (incluyendo el mes anterior)
    if request.GET.get('rango') == 'mes_anterior':
        # Calcular el primer día del mes actual
        first_day_current_month = today.replace(day=1)
        # Restar un día para obtener el último día del mes anterior
        last_day_previous_month = first_day_current_month - timedelta(days=1)
        # Obtener el primer día del mes anterior
        start_date_filter = last_day_previous_month.replace(day=1)
        filter_description = f"Citas desde el {start_date_filter.strftime('%d/%m/%Y')} en adelante"

    # Filtrar citas
    citas_query = Appointment.objects.filter(
        doctor=doctor,
        fecha__gte=start_date_filter # Mayor o igual a la fecha de inicio del filtro
    ).order_by('fecha').select_related('paciente') # Ordenar por fecha ascendente para ver las más próximas primero

    # Diccionario para agrupar citas por prioridad del paciente
    # Es buena idea predefinir las prioridades para que siempre aparezcan en el template
    citas_por_prioridad = {
        'Urgente': [],
        'Alta': [],
        'Media': [],
        'Baja': [],
        # Podrías añadir una categoría para prioridades no definidas o por si get_prioridad_display() devuelve algo inesperado
        # 'Otra': []
    }

    for cita in citas_query:
        prioridad = cita.paciente.get_prioridad_display()
        if prioridad in citas_por_prioridad:
            citas_por_prioridad[prioridad].append(cita)
        else:
            # Si la prioridad no está en las claves predefinidas, la añadimos dinámicamente
            # o la agrupamos en una categoría 'Otra' si prefieres
            citas_por_prioridad.setdefault(prioridad, []).append(cita)
            # O si quieres agrupar en 'Otra':
            # citas_por_prioridad.setdefault('Otra', []).append(cita)


    context = {
        'citas_por_prioridad': citas_por_prioridad,
        'user_type': 'doctor',
        'current_filter_description': filter_description,
        'is_showing_previous_month': request.GET.get('rango') == 'mes_anterior',
        'today_date_for_template': today , # Útil para el template si necesitas comparar fechas
        'hay_citas': citas_query.exists(), # ¡IMPORTANTE PARA EL TEMPLATE!
    }

    return render(request, 'dashboard.html', context)