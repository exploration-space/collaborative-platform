from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render

from apps.views_decorators import objects_exists, user_has_access
from apps.files_management.models import File

from .ner.posttagging_spacy import annotate as spacy_annotate

@login_required
@objects_exists
@user_has_access()
def overview_api(request):  # type: (HttpRequest, int) -> JsonResponse

    return JsonResponse({'name':'Alex'})