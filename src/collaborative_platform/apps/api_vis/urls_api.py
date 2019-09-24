from django.urls import path
from . import api

urlpatterns = [
    path('projects/', api.projects),
    path('projects/<int:project_id>/history/', api.project_history),
    path('projects/<int:project_id>/files/<int:file_id>/body/', api.file_body),
    path('projects/<int:project_id>/files/<int:file_id>/meta/', api.file_meta),
    path('projects/<int:project_id>/files/<int:file_id>/', api.file),
    path('projects/<int:project_id>/files/', api.project_files),
]
