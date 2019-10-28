from django.urls import path
from . import views

app_name = 'dataset_stats'

urlpatterns = [
    path('project/<int:project_id>/', views.main, name='main'),
]