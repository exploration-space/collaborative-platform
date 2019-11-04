from django.urls import path
from . import api

urlpatterns = [
    path('/', api.overview_api, name='overview_api'),
]