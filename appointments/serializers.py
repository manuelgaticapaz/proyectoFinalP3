from rest_framework import serializers
from .models import Appointment

class AppointmentSerializaer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'