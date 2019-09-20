from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.views_decorators import objects_exists, user_has_access
from apps.files_management.models import File, FileVersion

@login_required
@objects_exists
@user_has_access()
def ner(request, project_id, file_id):  # type: (HttpRequest, int, int) -> HttpResponse
    file = File.objects.get(id=file_id)
    version = file.version_number
    v = FileVersion.objects.get(id=version)

    content = {
        'title': file.name,
        'file': file,
        'version': version,
        'user':v.created_by.username
    }

    return render(request, 'entity_recognition/app.html', content)