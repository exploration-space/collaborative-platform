from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.views_decorators import objects_exists, user_has_access
from apps.files_management.models import File, FileVersion
from apps.projects.models import Project

from django.db.models import Q

from . import helpers

@login_required
@user_has_access()
def main(request, project_id=1):  # type: (HttpRequest, int, int) -> HttpResponse
    project = Project.objects.get(pk=project_id)
    files_query = Q(project=project)
    files = File.objects.filter(files_query)

    get_latest_content = lambda f: f.versions \
        .latest('creation_date') \
        .get_content() \
        .split('<?xml version="1.0"?>')[1] \
        .strip()

    file_gen = ((get_latest_content(file), file.name) for file in files)
    stats_df = helpers.create_summary_for_document_collection(file_gen)
    tags = helpers.get_stats(stats_df)

    content = {
    	"title":project.title, 
    	"project_id":project_id,
    	"DEVELOPMENT":True,
    	"tags": tags,
    	"document_count": len(files),
    }
    return render(request, "dataset_stats/app.html", content)