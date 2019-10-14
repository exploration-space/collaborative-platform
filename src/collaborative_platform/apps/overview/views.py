from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.views_decorators import objects_exists, user_has_access
from apps.files_management.models import File, FileVersion
from apps.projects.models import Project

@login_required
@user_has_access()
def main(request, project_id=1):  # type: (HttpRequest, int, int) -> HttpResponse
    project = Project.objects.get(pk=project_id)
    content = {
    	'title':project.title, 
    	'project_id':project_id,
    	'DEVELOPMENT':True
    }
    return render(request, 'overview/app.html', content)