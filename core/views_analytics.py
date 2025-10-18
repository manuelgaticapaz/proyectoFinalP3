from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.db.models import Count, Q, Avg
from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment
from core.database_utils import MySQLStoredProcedures
import json


@login_required
def analytics_dashboard(request):
    """Dashboard principal de analytics y reportes"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de doctor asociado a su usuario.')
        return redirect('doctor_dashboard')
    
    # Parámetros de fecha
    end_date = request.GET.get('end_date', timezone.now().date().strftime('%Y-%m-%d'))
    start_date = request.GET.get('start_date', (timezone.now().date() - timedelta(days=30)).strftime('%Y-%m-%d'))
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        messages.error(request, 'Formato de fecha inválido.')
        start_date_obj = timezone.now().date() - timedelta(days=30)
        end_date_obj = timezone.now().date()
        start_date = start_date_obj.strftime('%Y-%m-%d')
        end_date = end_date_obj.strftime('%Y-%m-%d')
    
    try:
        # Usar stored procedures para obtener analytics
        doctor_stats = MySQLStoredProcedures.call_doctor_statistics(doctor.id)
        patient_stats = MySQLStoredProcedures.call_patient_statistics(doctor.id)
        appointment_analytics = MySQLStoredProcedures.call_appointment_analytics(start_date_obj, end_date_obj)
        
        # Filtrar citas por fecha usando SP
        filtered_appointments = MySQLStoredProcedures.call_filter_appointments_by_date(
            doctor.id, start_date_obj, end_date_obj, None
        )
        
        using_stored_procedures = True
        
    except Exception as e:
        # Fallback a consultas Django
        messages.warning(request, 'Usando consultas básicas. Para mejores analytics ejecute: python manage.py create_stored_procedures')
        
        # Estadísticas básicas del doctor
        total_appointments = Appointment.objects.filter(doctor=doctor).count()
        today_appointments = Appointment.objects.filter(
            doctor=doctor, 
            fecha__date=timezone.now().date()
        ).count()
        
        doctor_stats = {
            'total_appointments': total_appointments,
            'today_appointments': today_appointments,
            'week_appointments': 0,
            'month_appointments': 0,
            'total_patients': Patient.objects.filter(appointment__doctor=doctor).distinct().count(),
            'upcoming_appointments': Appointment.objects.filter(
                doctor=doctor, 
                fecha__gt=timezone.now()
            ).count(),
        }
        
        patient_stats = []
        appointment_analytics = []
        filtered_appointments = []
        using_stored_procedures = False
    
    # Preparar datos para gráficos
    chart_data = prepare_chart_data(doctor, start_date_obj, end_date_obj, using_stored_procedures)
    
    context = {
        'doctor': doctor,
        'doctor_stats': doctor_stats,
        'patient_stats': patient_stats[:10],  # Top 10
        'appointment_analytics': appointment_analytics,
        'filtered_appointments': filtered_appointments[:20],  # Últimas 20
        'start_date': start_date,
        'end_date': end_date,
        'chart_data': json.dumps(chart_data),
        'using_stored_procedures': using_stored_procedures,
        'date_range_days': (end_date_obj - start_date_obj).days,
    }
    
    return render(request, 'analytics/dashboard.html', context)


@login_required
def appointment_analytics_ajax(request):
    """AJAX endpoint para analytics de citas"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor no encontrado'}, status=404)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    chart_type = request.GET.get('chart_type', 'appointments_by_day')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Fechas requeridas'}, status=400)
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
    
    try:
        if chart_type == 'appointments_by_day':
            data = get_appointments_by_day_chart(doctor, start_date_obj, end_date_obj)
        elif chart_type == 'priority_distribution':
            data = get_priority_distribution_chart(doctor, start_date_obj, end_date_obj)
        elif chart_type == 'patient_age_groups':
            data = get_patient_age_groups_chart(doctor)
        elif chart_type == 'appointments_by_hour':
            data = get_appointments_by_hour_chart(doctor, start_date_obj, end_date_obj)
        else:
            return JsonResponse({'error': 'Tipo de gráfico no válido'}, status=400)
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': f'Error generando gráfico: {str(e)}'}, status=500)


@login_required
def export_analytics_report(request):
    """Exportar reporte de analytics en formato JSON/CSV"""
    try:
        doctor = Doctor.objects.get(usuario=request.user)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor no encontrado'}, status=404)
    
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    format_type = request.GET.get('format', 'json')
    
    if not start_date or not end_date:
        return JsonResponse({'error': 'Fechas requeridas'}, status=400)
    
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Generar reporte completo
        report_data = {
            'doctor': {
                'name': f"{doctor.nombre} {doctor.apellidos}",
                'specialty': doctor.especialidad,
                'phone': doctor.telefono
            },
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date_obj - start_date_obj).days
            },
            'generated_at': timezone.now().isoformat(),
        }
        
        try:
            # Usar stored procedures si están disponibles
            doctor_stats = MySQLStoredProcedures.call_doctor_statistics(doctor.id)
            patient_stats = MySQLStoredProcedures.call_patient_statistics(doctor.id)
            appointment_analytics = MySQLStoredProcedures.call_appointment_analytics(start_date_obj, end_date_obj)
            
            report_data.update({
                'statistics': doctor_stats,
                'top_patients': patient_stats[:10],
                'analytics': appointment_analytics,
                'data_source': 'stored_procedures'
            })
            
        except Exception:
            # Fallback a consultas básicas
            appointments = Appointment.objects.filter(
                doctor=doctor,
                fecha__date__range=[start_date_obj, end_date_obj]
            )
            
            report_data.update({
                'statistics': {
                    'total_appointments_period': appointments.count(),
                    'unique_patients_period': appointments.values('paciente').distinct().count(),
                },
                'data_source': 'django_queries'
            })
        
        if format_type == 'json':
            response = JsonResponse(report_data, json_dumps_params={'indent': 2})
            response['Content-Disposition'] = f'attachment; filename="analytics_report_{start_date}_{end_date}.json"'
            return response
        
        # TODO: Implementar exportación CSV si se necesita
        return JsonResponse({'error': 'Formato no soportado'}, status=400)
        
    except Exception as e:
        return JsonResponse({'error': f'Error generando reporte: {str(e)}'}, status=500)


def prepare_chart_data(doctor, start_date, end_date, using_sp=False):
    """Preparar datos para gráficos del dashboard"""
    chart_data = {}
    
    try:
        if using_sp:
            # Usar stored procedures para datos más eficientes
            appointments_data = MySQLStoredProcedures.call_filter_appointments_by_date(
                doctor.id, start_date, end_date, None
            )
            
            # Procesar datos para gráficos
            daily_counts = {}
            priority_counts = {'U': 0, 'A': 0, 'M': 0, 'B': 0}
            hourly_counts = {str(i): 0 for i in range(8, 19)}  # 8 AM to 6 PM
            
            for apt in appointments_data:
                # Citas por día
                apt_date = apt['fecha'].strftime('%Y-%m-%d')
                daily_counts[apt_date] = daily_counts.get(apt_date, 0) + 1
                
                # Distribución por prioridad
                priority = apt['patient_priority']
                if priority in priority_counts:
                    priority_counts[priority] += 1
                
                # Citas por hora
                hour = str(apt['fecha'].hour)
                if hour in hourly_counts:
                    hourly_counts[hour] += 1
            
            chart_data = {
                'appointments_by_day': {
                    'labels': list(daily_counts.keys()),
                    'data': list(daily_counts.values())
                },
                'priority_distribution': {
                    'labels': ['Urgente', 'Alta', 'Media', 'Baja'],
                    'data': [priority_counts['U'], priority_counts['A'], priority_counts['M'], priority_counts['B']],
                    'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
                },
                'appointments_by_hour': {
                    'labels': [f"{i}:00" for i in range(8, 19)],
                    'data': [hourly_counts[str(i)] for i in range(8, 19)]
                }
            }
            
        else:
            # Fallback a consultas Django básicas
            appointments = Appointment.objects.filter(
                doctor=doctor,
                fecha__date__range=[start_date, end_date]
            ).select_related('paciente')
            
            chart_data = {
                'appointments_by_day': {'labels': [], 'data': []},
                'priority_distribution': {
                    'labels': ['Urgente', 'Alta', 'Media', 'Baja'],
                    'data': [0, 0, 0, 0],
                    'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
                },
                'appointments_by_hour': {
                    'labels': [f"{i}:00" for i in range(8, 19)],
                    'data': [0] * 11
                }
            }
    
    except Exception as e:
        # Datos vacíos en caso de error
        chart_data = {
            'appointments_by_day': {'labels': [], 'data': []},
            'priority_distribution': {'labels': [], 'data': [], 'colors': []},
            'appointments_by_hour': {'labels': [], 'data': []}
        }
    
    return chart_data


def get_appointments_by_day_chart(doctor, start_date, end_date):
    """Generar datos para gráfico de citas por día"""
    try:
        appointments_data = MySQLStoredProcedures.call_filter_appointments_by_date(
            doctor.id, start_date, end_date, None
        )
        
        daily_counts = {}
        current_date = start_date
        
        # Inicializar todos los días con 0
        while current_date <= end_date:
            daily_counts[current_date.strftime('%Y-%m-%d')] = 0
            current_date += timedelta(days=1)
        
        # Contar citas por día
        for apt in appointments_data:
            apt_date = apt['fecha'].strftime('%Y-%m-%d')
            if apt_date in daily_counts:
                daily_counts[apt_date] += 1
        
        return {
            'labels': list(daily_counts.keys()),
            'data': list(daily_counts.values()),
            'title': 'Citas por Día'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'title': 'Citas por Día', 'error': 'No se pudieron cargar los datos'}


def get_priority_distribution_chart(doctor, start_date, end_date):
    """Generar datos para gráfico de distribución por prioridad"""
    try:
        appointments_data = MySQLStoredProcedures.call_filter_appointments_by_date(
            doctor.id, start_date, end_date, None
        )
        
        priority_counts = {'U': 0, 'A': 0, 'M': 0, 'B': 0}
        
        for apt in appointments_data:
            priority = apt['patient_priority']
            if priority in priority_counts:
                priority_counts[priority] += 1
        
        return {
            'labels': ['Urgente', 'Alta', 'Media', 'Baja'],
            'data': [priority_counts['U'], priority_counts['A'], priority_counts['M'], priority_counts['B']],
            'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745'],
            'title': 'Distribución por Prioridad'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'colors': [], 'title': 'Distribución por Prioridad', 'error': 'No se pudieron cargar los datos'}


def get_patient_age_groups_chart(doctor):
    """Generar datos para gráfico de grupos de edad de pacientes"""
    try:
        patient_stats = MySQLStoredProcedures.call_patient_statistics(doctor.id)
        
        age_groups = {
            '0-18': 0,
            '19-35': 0,
            '36-50': 0,
            '51-65': 0,
            '66+': 0
        }
        
        for patient in patient_stats:
            age = patient.get('age', 0)
            if age is None:
                continue
                
            if age <= 18:
                age_groups['0-18'] += 1
            elif age <= 35:
                age_groups['19-35'] += 1
            elif age <= 50:
                age_groups['36-50'] += 1
            elif age <= 65:
                age_groups['51-65'] += 1
            else:
                age_groups['66+'] += 1
        
        return {
            'labels': list(age_groups.keys()),
            'data': list(age_groups.values()),
            'title': 'Distribución por Edad de Pacientes'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'title': 'Distribución por Edad', 'error': 'No se pudieron cargar los datos'}


def get_appointments_by_hour_chart(doctor, start_date, end_date):
    """Generar datos para gráfico de citas por hora del día"""
    try:
        appointments_data = MySQLStoredProcedures.call_filter_appointments_by_date(
            doctor.id, start_date, end_date, None
        )
        
        hourly_counts = {i: 0 for i in range(8, 19)}  # 8 AM to 6 PM
        
        for apt in appointments_data:
            hour = apt['fecha'].hour
            if hour in hourly_counts:
                hourly_counts[hour] += 1
        
        return {
            'labels': [f"{i}:00" for i in range(8, 19)],
            'data': [hourly_counts[i] for i in range(8, 19)],
            'title': 'Distribución de Citas por Hora'
        }
        
    except Exception:
        return {'labels': [], 'data': [], 'title': 'Citas por Hora', 'error': 'No se pudieron cargar los datos'}
