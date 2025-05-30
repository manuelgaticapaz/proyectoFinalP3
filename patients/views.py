from django.shortcuts import render
from rest_framework import viewsets
from .models import Patient
from .serializers import PatientsSerializer

# Create your views here.


class PatientsViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all().order_by('-id') # Define el conjunto de datos base
    serializer_class = PatientsSerializer