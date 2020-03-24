import os
import pytest

from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client

from apps.api_vis.models import Entity, EntityProperty
from apps.files_management.models import Directory, File
from apps.projects.models import Project


SCRIPT_DIR = os.path.dirname(__file__)


@pytest.mark.usefixtures('file_upload_with_hd_and_db__db_setup', 'reset_db_files_directory_after_each_test')
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestFileUploadWithHdAndDb:
    def test_file_upload_create_file_on_hd_and_entries_in_db(self):
        user_id = 2
        project_id = 1

        client = Client()
        user = User.objects.get(id=user_id)
        client.force_login(user)

        files_in_db = File.objects.all()
        assert len(files_in_db) == 0

        files_on_hd = os.listdir(os.path.join(settings.MEDIA_ROOT, 'uploaded_files'))
        assert len(files_on_hd) == 0

        project = Project.objects.get(id=project_id)
        directory = Directory.objects.get(project=project, name=project.title, parent_dir=None)
        source_file_path = os.path.join(SCRIPT_DIR, 'test_files', 'source_files', 'group_0_long_original_0.xml')

        upload_file(client, source_file_path, directory.id)

        files_in_db = File.objects.all()
        assert len(files_in_db) == 1

        files_on_hd = os.listdir(os.path.join(settings.MEDIA_ROOT, 'uploaded_files'))
        assert len(files_on_hd) == 2

    def test_file_upload_extract_elements_from_file_to_db(self):
        user_id = 2
        project_id = 1

        client = Client()
        user = User.objects.get(id=user_id)
        client.force_login(user)

        entities_in_db = Entity.objects.all()
        assert len(entities_in_db) == 0

        entities_properties_in_db = EntityProperty.objects.all()
        assert len(entities_properties_in_db) == 0

        project = Project.objects.get(id=project_id)
        directory = Directory.objects.get(project=project, name=project.title, parent_dir=None)
        source_file_path = os.path.join(SCRIPT_DIR, 'test_files', 'source_files',
                                        'move_elements_to_db__move_all__source.xml')

        upload_file(client, source_file_path, directory.id)

        entities_in_db = Entity.objects.all()
        assert len(entities_in_db) == 16

        entities_properties_in_db = EntityProperty.objects.all()
        assert len(entities_properties_in_db) == 20

        expected_file_path = os.path.join(SCRIPT_DIR, 'test_files', 'expected_files',
                                          'move_elements_to_db__move_all__expected.xml')
        expected_xml = read_file(expected_file_path)

        file = File.objects.last()
        file_version = file.versions.last()
        result_xml = file_version.get_content()

        assert result_xml == expected_xml


def read_file(path):
    with open(path, 'r') as file:
        text = file.read()

    return text


def upload_file(client, path, directory_id):
    file_name = os.path.basename(path)

    with open(path, 'r') as uploaded_file:
        url = f'/api/files/upload/{directory_id}/'
        payload = {
            'name': file_name,
            'file': uploaded_file,
        }

        client.post(url, payload)
