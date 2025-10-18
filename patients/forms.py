from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['nombre', 'apellidos', 'dni', 'fecha_nacimiento', 'prioridad', 
                 'historial_medico_basico', 'informacion_contacto']
        widgets = {
            'nombre': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Nombre del paciente...',
                    'required': True
                }
            ),
            'apellidos': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Apellidos del paciente...',
                    'required': True
                }
            ),
            'dni': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'DNI/Cédula del paciente...',
                    'required': True
                }
            ),
            'fecha_nacimiento': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'form-control'
                }
            ),
            'prioridad': forms.Select(
                attrs={
                    'class': 'form-select'
                }
            ),
            'historial_medico_basico': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Alergias, condiciones preexistentes, medicación actual...'
                }
            ),
            'informacion_contacto': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 3,
                    'placeholder': 'Teléfono, email, dirección, contacto de emergencia...'
                }
            ),
        }
        labels = {
            'nombre': 'Nombre',
            'apellidos': 'Apellidos',
            'dni': 'DNI/Cédula',
            'fecha_nacimiento': 'Fecha de Nacimiento',
            'prioridad': 'Prioridad Médica',
            'historial_medico_basico': 'Historial Médico Básico',
            'informacion_contacto': 'Información de Contacto'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set maximum date to today for birth date
        today = timezone.now().date()
        self.fields['fecha_nacimiento'].widget.attrs['max'] = today.strftime('%Y-%m-%d')
        
        # Set minimum date to 120 years ago (reasonable maximum age)
        min_date = today - timedelta(days=120*365)
        self.fields['fecha_nacimiento'].widget.attrs['min'] = min_date.strftime('%Y-%m-%d')

    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        
        if dni:
            # Remove spaces and convert to uppercase
            dni = dni.replace(' ', '').upper()
            
            # Basic length validation
            if len(dni) < 5:
                raise forms.ValidationError(
                    "El DNI debe tener al menos 5 caracteres."
                )
            
            if len(dni) > 20:
                raise forms.ValidationError(
                    "El DNI no puede exceder los 20 caracteres."
                )
            
            # Check for uniqueness (excluding current instance if editing)
            existing_patient = Patient.objects.filter(dni=dni)
            if self.instance and self.instance.pk:
                existing_patient = existing_patient.exclude(pk=self.instance.pk)
            
            if existing_patient.exists():
                raise forms.ValidationError(
                    f"Ya existe un paciente con el DNI {dni}."
                )
        
        return dni

    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        
        if fecha_nacimiento:
            today = timezone.now().date()
            
            # Check if birth date is in the future
            if fecha_nacimiento > today:
                raise forms.ValidationError(
                    "La fecha de nacimiento no puede ser en el futuro."
                )
            
            # Check if age is reasonable (not more than 120 years)
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or \
               (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            
            if age > 120:
                raise forms.ValidationError(
                    "La edad calculada no puede ser mayor a 120 años."
                )
            
            if age < 0:
                raise forms.ValidationError(
                    "La fecha de nacimiento no es válida."
                )
        
        return fecha_nacimiento

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        
        if nombre:
            # Remove extra spaces and title case
            nombre = ' '.join(nombre.split()).title()
            
            # Minimum length validation
            if len(nombre.strip()) < 2:
                raise forms.ValidationError(
                    "El nombre debe tener al menos 2 caracteres."
                )
            
            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            import re
            if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$", nombre):
                raise forms.ValidationError(
                    "El nombre solo puede contener letras, espacios, guiones y apostrofes."
                )
        
        return nombre

    def clean_apellidos(self):
        apellidos = self.cleaned_data.get('apellidos')
        
        if apellidos:
            # Remove extra spaces and title case
            apellidos = ' '.join(apellidos.split()).title()
            
            # Minimum length validation
            if len(apellidos.strip()) < 2:
                raise forms.ValidationError(
                    "Los apellidos deben tener al menos 2 caracteres."
                )
            
            # Check for valid characters
            import re
            if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s\-']+$", apellidos):
                raise forms.ValidationError(
                    "Los apellidos solo pueden contener letras, espacios, guiones y apostrofes."
                )
        
        return apellidos

    def clean_historial_medico_basico(self):
        historial = self.cleaned_data.get('historial_medico_basico')
        
        if historial:
            # Maximum length validation
            if len(historial) > 2000:
                raise forms.ValidationError(
                    "El historial médico no puede exceder los 2000 caracteres."
                )
            
            return historial.strip()
        
        return historial

    def clean_informacion_contacto(self):
        info_contacto = self.cleaned_data.get('informacion_contacto')
        
        if info_contacto:
            # Maximum length validation
            if len(info_contacto) > 1000:
                raise forms.ValidationError(
                    "La información de contacto no puede exceder los 1000 caracteres."
                )
            
            return info_contacto.strip()
        
        return info_contacto
