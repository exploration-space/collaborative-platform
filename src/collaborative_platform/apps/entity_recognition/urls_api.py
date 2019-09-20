from django.urls import path
from . import api

urlpatterns = [
    path('posttagging_spacy/file/<int:file_id>/', api.posttagging_spacy, name='ner'),
]