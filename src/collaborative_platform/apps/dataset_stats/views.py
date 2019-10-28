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

    tags = [
    	{
    		"name": "person",
    		"count": 99,
    		"coverage": 100,
    		"attributes": [
    			{
    				"name": "gender",
    				"top_perc": 60,
    				"top_value": "1",
    				"coverage": 90,
    				"values": [
    					["1", 60],
    					["2", 39],
    				]
    			}
    		]
    	},
    	{
    		"name": "placeName",
    		"count": 190,
    		"coverage": 30,
    		"attributes": []
    	},
    	{
    		"name": "certainty",
    		"coverage": 20,
    		"count": 45,
    		"attributes": [
    			{
    				"name": "locus",
    				"top_perc": 70,
    				"top_value": "value",
    				"coverage": 100,
    				"values": [
    					["value", 40],
    					["attribute", 10],
    					["name", 20]
    				]
    			},
    			{
    				"name": "cert",
    				"top_perc": 50,
    				"top_value": "medium",
    				"coverage": 100,
    				"values": [
    					["low", 10],
    					["medium", 25],
    					["high", 5],
    					["unknown", 10]
    				]
    			},
    			{
    				"name": "type",
    				"top_perc": 90,
    				"top_value": "ignorance",
    				"coverage": 100,
    				"values": [
    					["ignorance", 90],
    					["credibility", 5],
    					["incompletness", 5]
    				]
    			},
    			{
    				"name": "tag",
    				"top_perc": 40,
    				"top_value": "person",
    				"coverage": 100,
    				"values": [
    					["person", 40],
    					["placeName", 5],
    					["date", 20],
    					["location", 20],
    					["age", 15]
    				]
    			},
    			{
    				"name": "attribute",
    				"top_perc": 100,
    				"top_value": "gender",
    				"coverage": 5,
    				"values": [
    					["gender", 2]
    				]
    			}
    		]
    	},
    ]

    content = {
    	"title":project.title, 
    	"project_id":project_id,
    	"DEVELOPMENT":True,
    	"tags": tags,
    	"document_count": 200,
    }
    return render(request, "dataset_stats/app.html", content)