from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Clinica, UsuarioClinica
from doctors.models import Doctor
from patients.models import Patient
from appointments.models import Appointment

def es_admin_global(user):
    """Verificar si el usuario es administrador global"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(es_admin_global)
def dashboard_clinicas(request):
    """
    Dashboard principal para administración de clínicas
    """
    clinicas = Clinica.objects.all().order_by('nombre')
    
    # Estadísticas por clínica
    estadisticas = []
    for clinica in clinicas:
        stats = {
            'clinica': clinica,
            'doctores': Doctor.objects.filter(clinica=clinica, activo=True).count(),
            'pacientes': Patient.objects.filter(clinica=clinica).count(),
            'citas_mes': Appointment.objects.filter(
                clinica=clinica,
                fecha__month=timezone.now().month,
                fecha__year=timezone.now().year
            ).count(),
            'usuarios': UsuarioClinica.objects.filter(clinica=clinica, activo=True).count()
        }
        estadisticas.append(stats)
    
    context = {
        'estadisticas': estadisticas,
        'total_clinicas': clinicas.count(),
        'clinicas_activas': clinicas.filter(activa=True).count(),
    }
    
    return render(request, 'clinicas/dashboard.html', context)

@login_required
@user_passes_test(es_admin_global)
def crear_clinica(request):
    """
    Crear nueva clínica
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                clinica = Clinica.objects.create(
                    nombre=request.POST['nombre'],
                    codigo=request.POST['codigo'],
                    direccion=request.POST['direccion'],
                    telefono=request.POST['telefono'],
                    email=request.POST['email'],
                    horario_inicio=request.POST.get('horario_inicio', '08:00'),
                    horario_fin=request.POST.get('horario_fin', '18:00'),
                    duracion_cita_default=int(request.POST.get('duracion_cita_default', 30)),
                    max_citas_por_dia=int(request.POST.get('max_citas_por_dia', 50)),
                )
                
                # Asignar administrador si se especifica
                admin_id = request.POST.get('administrador')
                if admin_id:
                    clinica.administrador_id = admin_id
                    clinica.save()
                    
                    # Crear relación usuario-clínica
                    UsuarioClinica.objects.create(
                        usuario_id=admin_id,
                        clinica=clinica,
                        rol='admin'
                    )
                
                messages.success(request, f'Clínica "{clinica.nombre}" creada exitosamente')
                return redirect('clinicas:dashboard')
                
        except Exception as e:
            messages.error(request, f'Error al crear la clínica: {str(e)}')
    
    # Obtener usuarios disponibles para ser administradores
    usuarios_disponibles = User.objects.filter(is_active=True).order_by('username')
    
    context = {
        'usuarios_disponibles': usuarios_disponibles,
    }
    
    return render(request, 'clinicas/crear.html', context)

@login_required
@user_passes_test(es_admin_global)
def editar_clinica(request, clinica_id):
    """
    Editar clínica existente
    """
    clinica = get_object_or_404(Clinica, id=clinica_id)
    
    if request.method == 'POST':
        try:
            clinica.nombre = request.POST['nombre']
            clinica.codigo = request.POST['codigo']
            clinica.direccion = request.POST['direccion']
            clinica.telefono = request.POST['telefono']
            clinica.email = request.POST['email']
            clinica.horario_inicio = request.POST.get('horario_inicio', '08:00')
            clinica.horario_fin = request.POST.get('horario_fin', '18:00')
            clinica.duracion_cita_default = int(request.POST.get('duracion_cita_default', 30))
            clinica.max_citas_por_dia = int(request.POST.get('max_citas_por_dia', 50))
            clinica.activa = 'activa' in request.POST
            
            # Actualizar administrador
            admin_id = request.POST.get('administrador')
            if admin_id:
                clinica.administrador_id = admin_id
            else:
                clinica.administrador = None
            
            clinica.save()
            
            messages.success(request, f'Clínica "{clinica.nombre}" actualizada exitosamente')
            return redirect('clinicas:dashboard')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar la clínica: {str(e)}')
    
    usuarios_disponibles = User.objects.filter(is_active=True).order_by('username')
    
    context = {
        'clinica': clinica,
        'usuarios_disponibles': usuarios_disponibles,
    }
    
    return render(request, 'clinicas/editar.html', context)

@login_required
def detalle_clinica(request, clinica_id):
    """
    Ver detalles de una clínica
    """
    clinica = get_object_or_404(Clinica, id=clinica_id)
    
    # Verificar permisos
    if not (request.user.is_staff or 
            UsuarioClinica.objects.filter(usuario=request.user, clinica=clinica, activo=True).exists()):
        messages.error(request, 'No tiene permisos para ver esta clínica')
        return redirect('doctors:dashboard')
    
    # Estadísticas detalladas
    doctores = Doctor.objects.filter(clinica=clinica, activo=True)
    pacientes = Patient.objects.filter(clinica=clinica)
    
    hoy = timezone.now().date()
    citas_hoy = Appointment.objects.filter(clinica=clinica, fecha__date=hoy)
    citas_mes = Appointment.objects.filter(
        clinica=clinica,
        fecha__month=hoy.month,
        fecha__year=hoy.year
    )
    
    usuarios_clinica = UsuarioClinica.objects.filter(
        clinica=clinica, 
        activo=True
    ).select_related('usuario')
    
    context = {
        'clinica': clinica,
        'doctores': doctores,
        'pacientes': pacientes[:10],  # Mostrar solo los primeros 10
        'citas_hoy': citas_hoy,
        'citas_mes': citas_mes,
        'usuarios_clinica': usuarios_clinica,
        'estadisticas': {
            'total_doctores': doctores.count(),
            'total_pacientes': pacientes.count(),
            'citas_hoy_count': citas_hoy.count(),
            'citas_mes_count': citas_mes.count(),
            'citas_completadas_mes': citas_mes.filter(estado='completada').count(),
        }
    }
    
    return render(request, 'clinicas/detalle.html', context)

@login_required
@user_passes_test(es_admin_global)
def usuarios_clinica(request, clinica_id):
    """
    Gestionar usuarios de una clínica
    """
    clinica = get_object_or_404(Clinica, id=clinica_id)
    usuarios = UsuarioClinica.objects.filter(clinica=clinica).select_related('usuario')
    
    context = {
        'clinica': clinica,
        'usuarios': usuarios,
    }
    
    return render(request, 'clinicas/usuarios.html', context)

@login_required
@user_passes_test(es_admin_global)
def agregar_usuario_clinica(request, clinica_id):
    """
    Agregar usuario a una clínica
    """
    clinica = get_object_or_404(Clinica, id=clinica_id)
    
    if request.method == 'POST':
        try:
            usuario_id = request.POST['usuario']
            rol = request.POST['rol']
            
            # Verificar que no exista ya la relación
            if UsuarioClinica.objects.filter(usuario_id=usuario_id, clinica=clinica).exists():
                messages.warning(request, 'El usuario ya está asignado a esta clínica')
            else:
                UsuarioClinica.objects.create(
                    usuario_id=usuario_id,
                    clinica=clinica,
                    rol=rol
                )
                messages.success(request, 'Usuario agregado exitosamente a la clínica')
            
            return redirect('clinicas:usuarios', clinica_id=clinica_id)
            
        except Exception as e:
            messages.error(request, f'Error al agregar usuario: {str(e)}')
    
    # Usuarios que no están en esta clínica
    usuarios_existentes = UsuarioClinica.objects.filter(clinica=clinica).values_list('usuario_id', flat=True)
    usuarios_disponibles = User.objects.filter(is_active=True).exclude(id__in=usuarios_existentes)
    
    context = {
        'clinica': clinica,
        'usuarios_disponibles': usuarios_disponibles,
        'roles': UsuarioClinica.ROLES,
    }
    
    return render(request, 'clinicas/agregar_usuario.html', context)

@login_required
@user_passes_test(es_admin_global)
def editar_usuario_clinica(request, usuario_clinica_id):
    """
    Editar rol de usuario en clínica
    """
    usuario_clinica = get_object_or_404(UsuarioClinica, id=usuario_clinica_id)
    
    if request.method == 'POST':
        try:
            usuario_clinica.rol = request.POST['rol']
            usuario_clinica.activo = 'activo' in request.POST
            usuario_clinica.save()
            
            messages.success(request, 'Usuario actualizado exitosamente')
            return redirect('clinicas:usuarios', clinica_id=usuario_clinica.clinica.id)
            
        except Exception as e:
            messages.error(request, f'Error al actualizar usuario: {str(e)}')
    
    context = {
        'usuario_clinica': usuario_clinica,
        'roles': UsuarioClinica.ROLES,
    }
    
    return render(request, 'clinicas/editar_usuario.html', context)

@login_required
@user_passes_test(es_admin_global)
def transferir_paciente(request):
    """
    Transferir paciente entre clínicas
    """
    if request.method == 'POST':
        try:
            paciente_id = request.POST['paciente_id']
            clinica_destino_id = request.POST['clinica_destino']
            
            paciente = get_object_or_404(Patient, id=paciente_id)
            clinica_destino = get_object_or_404(Clinica, id=clinica_destino_id)
            
            # Verificar citas pendientes
            citas_pendientes = Appointment.objects.filter(
                paciente=paciente,
                fecha__gt=timezone.now(),
                estado__in=['programada', 'confirmada']
            ).count()
            
            if citas_pendientes > 0:
                return JsonResponse({
                    'success': False,
                    'error': f'El paciente tiene {citas_pendientes} citas pendientes'
                })
            
            with transaction.atomic():
                clinica_origen = paciente.clinica
                
                # Transferir paciente
                paciente.clinica = clinica_destino
                paciente.save()
                
                # Actualizar citas históricas
                Appointment.objects.filter(paciente=paciente).update(clinica=clinica_destino)
                
                return JsonResponse({
                    'success': True,
                    'message': f'Paciente transferido de {clinica_origen} a {clinica_destino}'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # GET request - mostrar formulario
    clinicas = Clinica.objects.filter(activa=True)
    pacientes = Patient.objects.select_related('clinica').order_by('apellidos', 'nombre')
    
    context = {
        'clinicas': clinicas,
        'pacientes': pacientes,
    }
    
    return render(request, 'clinicas/transferir_paciente.html', context)

@login_required
@user_passes_test(es_admin_global)
def reportes_consolidados(request):
    """
    Reportes consolidados de todas las clínicas
    """
    clinicas = Clinica.objects.filter(activa=True)
    
    # Estadísticas consolidadas
    estadisticas_consolidadas = []
    
    for clinica in clinicas:
        hoy = timezone.now().date()
        inicio_mes = hoy.replace(day=1)
        
        stats = {
            'clinica': clinica,
            'doctores_activos': Doctor.objects.filter(clinica=clinica, activo=True).count(),
            'pacientes_total': Patient.objects.filter(clinica=clinica).count(),
            'citas_hoy': Appointment.objects.filter(clinica=clinica, fecha__date=hoy).count(),
            'citas_mes': Appointment.objects.filter(
                clinica=clinica,
                fecha__date__gte=inicio_mes
            ).count(),
            'citas_completadas_mes': Appointment.objects.filter(
                clinica=clinica,
                fecha__date__gte=inicio_mes,
                estado='completada'
            ).count(),
        }
        
        # Calcular porcentaje de éxito
        if stats['citas_mes'] > 0:
            stats['porcentaje_exito'] = round(
                (stats['citas_completadas_mes'] / stats['citas_mes']) * 100, 1
            )
        else:
            stats['porcentaje_exito'] = 0
        
        estadisticas_consolidadas.append(stats)
    
    # Totales generales
    totales = {
        'clinicas_activas': len(estadisticas_consolidadas),
        'doctores_total': sum(s['doctores_activos'] for s in estadisticas_consolidadas),
        'pacientes_total': sum(s['pacientes_total'] for s in estadisticas_consolidadas),
        'citas_hoy_total': sum(s['citas_hoy'] for s in estadisticas_consolidadas),
        'citas_mes_total': sum(s['citas_mes'] for s in estadisticas_consolidadas),
    }
    
    context = {
        'estadisticas_consolidadas': estadisticas_consolidadas,
        'totales': totales,
    }
    
    return render(request, 'clinicas/reportes_consolidados.html', context)
