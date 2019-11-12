from django.shortcuts import render
from rest_framework import views, viewsets, permissions, mixins, generics
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.decorators import detail_route
from django.http import HttpResponse, JsonResponse
from script.models.data import County, ZipCode
from script.models.statistics import Energy
from script.models.algorithms import LoadController, AggregateLoadProfile
from script.serializers import CountySerializer, ZipCodeSerializer, EnergySerializer, LoadControllerSerializer, AggregateLoadProfileSerializer


class CountyViewSet(viewsets.ModelViewSet):
    queryset = County.objects.all()
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = CountySerializer


class ZipCodeViewSet(viewsets.ModelViewSet):
    queryset = ZipCode.objects.all()
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = ZipCodeSerializer
    filter_fields = ('county',) # using django-filter


class EnergyViewSet(viewsets.ModelViewSet):
    queryset = Energy.objects.all()
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = EnergySerializer
    filter_fields = ('county', 'year', 'month') # using django-filter


<<<<<<< HEAD
class ForecastViewSet(viewsets.ModelViewSet):
    queryset = Forecast.objects.all()
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = ForecastSerializer
    filter_fields = ('county',) # using django-filter
=======
class LoadControllerViewSet(viewsets.ModelViewSet):
    queryset = LoadController.objects.all()
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = LoadControllerSerializer
    filter_fields = ('county',
                    'rate_energy_peak',
                    'rate_energy_partpeak',
                    'rate_energy_offpeak',
                    'rate_demand_peak',
                    'rate_demand_partpeak',
                    'rate_demand_overall') # using django-filter


class AggregateLoadProfileViewSet(viewsets.ModelViewSet):
    queryset = AggregateLoadProfile.objects.all()
    permission_classes = [
        permissions.AllowAny,
    ]
    serializer_class = AggregateLoadProfileSerializer
    filter_fields = ('year',
                    'day_type') # using django-filter
>>>>>>> ecaf78db8f2baf8acd6f9046dd9cd75e7d80525a
