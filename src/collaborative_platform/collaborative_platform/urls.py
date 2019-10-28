"""collaborative_platform URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/files/', include('apps.files_management.urls_api')),
    path('files/', include('apps.files_management.urls')),
    path('api/projects/', include('apps.projects.urls_api')),
    path('projects/', include('apps.projects.urls', namespace='projects')),
    path('api/close_reading/', include('apps.close_reading.urls_api')),
    path('close_reading/', include('apps.close_reading.urls')),
    path('api/search/', include('apps.index_and_search.urls_api')),
    path('social_auth/', include('social_django.urls', namespace='social')),
    path('api/vis/', include('apps.api_vis.urls_api')),
    path('entity_recognition/', include('apps.entity_recognition.urls')),
    path('api/entity_recognition/', include('apps.entity_recognition.urls_api')),
    path('overview/', include('apps.overview.urls')),
    path('stats/', include('apps.dataset_stats.urls')),
    path('', include('apps.core.urls')),
]
