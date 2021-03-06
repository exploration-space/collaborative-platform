from django.urls import path
from . import api


urlpatterns = [
    path('projects/', api.projects),
    path('projects/<int:project_id>/history/', api.project_history),
    path('projects/<int:project_id>/files/<int:file_id>/body/', api.file_body),
    path('projects/<int:project_id>/files/<int:file_id>/meta/', api.file_meta),
    path('projects/<int:project_id>/files/<int:file_id>/names/', api.file_names),
    path('projects/<int:project_id>/files/<int:file_id>/annotations/', api.file_annotations),
    path('projects/<int:project_id>/files/<int:file_id>/people/', api.file_people),
    path('projects/<int:project_id>/files/<int:file_id>/', api.file),
    path('projects/<int:project_id>/files/<int:file_id>/cliques/', api.file_cliques),
    path('projects/<int:project_id>/files/<int:file_id>/entities/unbound_entities/', api.file_unbound_entities),
    path('projects/<int:project_id>/files/<int:file_id>/entities/', api.file_entities),
    path('projects/<int:project_id>/files/', api.project_files),
    path('projects/<int:project_id>/context/<str:text>/', api.context_search),
    path('projects/<int:project_id>/cliques/<int:clique_id>/entities/', api.clique_entities),
    path('projects/<int:project_id>/cliques/', api.project_cliques),
    path('projects/<int:project_id>/commits/uncommitted_changes/', api.uncommitted_changes),
    path('projects/<int:project_id>/commits/', api.commits),
    path('projects/<int:project_id>/entities/unbound_entities/', api.project_unbound_entities),
    path('projects/<int:project_id>/entities/', api.project_entities),
]
