from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render

from apps.views_decorators import objects_exists, user_has_access
from apps.files_management.models import File

from .ner.posttagging_spacy import annotate as spacy_annotate

@login_required
@objects_exists
@user_has_access()
def posttagging_spacy(request, file_id):  # type: (HttpRequest, int) -> JsonResponse
    file = File.objects.get(id=file_id)
    version = file.version_number

    f_download = file.download()
    f_content = f_download.getvalue().decode('UTF-8')

    result = {
        'title': file.name,
        'tags': 9,
        'original': f_content,
        'annotated': spacy_annotate(f_content)
    }

    return JsonResponse(result)