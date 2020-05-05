import inspect
import json
import os
import pytest

from channels.testing import WebsocketCommunicator

from django.contrib.auth.models import User
from django.test import Client

from apps.api_vis.models import Entity, EntityProperty

from collaborative_platform.routing import application


SCRIPT_DIR = os.path.dirname(__file__)


# TODO: Extract creating communicators and disconnecting them to pytest fixture
# TODO: Figure out how to reset database after each test inside class and reduce number of test classes


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb:
    async def test_authorized_user_can_connect(self):
        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        connected, _ = await communicator.connect()
        assert connected is True

        response = await communicator.receive_json_from()
        assert response['status'] == 200
        assert response['message'] == 'OK'

        await communicator.send_to(text_data='ping')
        response = await communicator.receive_from()
        assert response == 'pong'

        await communicator.disconnect()

    test_parameters_names = "project_id, file_id, user_id, response_status, response_message"
    test_parameters_list = [
        (999, 1, 2, 400, "Project with id: 999 doesn't exist."),
        (1, 1, None, 403, "You aren't contributor in project with id: 1."),
        (1, 999, 2, 400, "File with id: 999 doesn't exist."),
    ]

    @pytest.mark.parametrize(test_parameters_names, test_parameters_list)
    async def test_connecting_exceptions(self, project_id, file_id, user_id, response_status, response_message):
        communicator = get_communicator(project_id, file_id, user_id)

        connected, _ = await communicator.connect()
        assert connected is True

        response = await communicator.receive_json_from()
        assert response['status'] == response_status
        assert response['message'] == response_message

        await communicator.send_to(text_data='ping')
        with pytest.raises(AssertionError):
            _ = await communicator.receive_from()

    async def test_user_get_correct_response_after_connection(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        request_nr = 0

        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()

    async def test_add_tags_to_text(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'POST',
                'element_type': 'tag',
                'parameters': {
                    'start_pos': 265,
                    'end_pos': 271,
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        request = [
            {
                'method': 'POST',
                'element_type': 'tag',
                'parameters': {
                    'start_pos': 400,
                    'end_pos': 404
                }
            }
        ]
        request_nr = 1

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()

    async def test_move_tag_to_new_position(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'PUT',
                'element_type': 'tag',
                'edited_element_id': 'name-3',
                'parameters': {
                    'start_pos': 313,
                    'end_pos': 328,
                    'new_start_pos': 272,
                    'new_end_pos': 342,
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()

    async def test_delete_tag_from_text(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'DELETE',
                'element_type': 'tag',
                'edited_element_id': 'name-3'
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb2:
    async def test_add_reference_to_entity_to_text__entity_doesnt_exist__entity_listable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'POST',
                'element_type': 'tag',
                'parameters': {
                    'start_pos': 265,
                    'end_pos': 271,
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        request = [
            {
                'method': 'POST',
                'element_type': 'reference',
                'edited_element_id': 'ab-1',
                'parameters': {
                    'entity_type': 'person',
                    'entity_properties': {
                        'forename': 'Bugs',
                        'surname': 'Bunny',
                        'sex': 'M'
                    }
                }
            }
        ]
        request_nr = 1

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb3:
    async def test_add_reference_to_entity_to_text__entity_doesnt_exist__entity_unlistable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'POST',
                'element_type': 'tag',
                'parameters': {
                    'start_pos': 265,
                    'end_pos': 271,
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        date_entities_in_db = Entity.objects.filter(type='date')
        assert len(date_entities_in_db) == 3

        request = [
            {
                'method': 'POST',
                'element_type': 'reference',
                'edited_element_id': 'ab-1',
                'parameters': {
                    'entity_type': 'date',
                    'entity_properties': {
                        'when': '2000-01-01'
                    }
                }
            }
        ]
        request_nr = 1

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        date_entities_in_db = Entity.objects.filter(type='date')
        assert len(date_entities_in_db) == 4

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb4:
    async def test_add_reference_to_entity_to_text__entity_exist__entity_listable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'POST',
                'element_type': 'tag',
                'parameters': {
                    'start_pos': 265,
                    'end_pos': 271,
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        request = [
            {
                'method': 'POST',
                'element_type': 'reference',
                'edited_element_id': 'ab-1',
                'new_element_id': 'person-2'
            }
        ]
        request_nr = 1

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb5:
    async def test_add_reference_to_entity_to_text__entity_exist__entity_unlistable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'POST',
                'element_type': 'tag',
                'parameters': {
                    'start_pos': 265,
                    'end_pos': 271,
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        request = [
            {
                'method': 'POST',
                'element_type': 'reference',
                'edited_element_id': 'ab-1',
                'new_element_id': 'date-0'
            }
        ]
        request_nr = 1

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb6:
    async def test_remove_reference_to_entity_from_text__entity_listable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'DELETE',
                'element_type': 'reference',
                'edited_element_id': 'name-4',
                'old_element_id': 'ingredient-2',
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb7:
    async def test_remove_reference_to_entity_from_text__entity_unlistable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        date_entity_in_db = Entity.objects.get(
            file_id=file_id,
            xml_id='date-2'
        )

        assert date_entity_in_db.deleted_by is None

        date_entity_properties_in_db = EntityProperty.objects.filter(
            entity_version=date_entity_in_db.entityversion_set.all().order_by('-id')[0]
        )

        for entity_property in date_entity_properties_in_db:
            assert entity_property.deleted_by is None

        request = [
            {
                'method': 'DELETE',
                'element_type': 'reference',
                'edited_element_id': 'date-2',
                'old_element_id': 'date-2',
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        date_entity_in_db.refresh_from_db()
        assert date_entity_in_db.deleted_by.id == user_id

        for entity_property in date_entity_properties_in_db:
            entity_property.refresh_from_db()
            assert entity_property.deleted_by.id == user_id

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb8:
    async def test_modify_reference_to_entity__entity_doesnt_exist__entity_listable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        date_entity_in_db = Entity.objects.get(
            file_id=file_id,
            xml_id='date-2'
        )

        assert date_entity_in_db.deleted_by is None

        date_entity_properties_in_db = EntityProperty.objects.filter(
            entity_version=date_entity_in_db.entityversion_set.all().order_by('-id')[0]
        )

        for entity_property in date_entity_properties_in_db:
            assert entity_property.deleted_by is None

        request = [
            {
                'method': 'PUT',
                'element_type': 'reference',
                'edited_element_id': 'date-2',
                'old_element_id': 'date-2',
                'parameters': {
                    'entity_type': 'person',
                    'entity_properties': {
                        'forename': 'Bugs',
                        'surname': 'Bunny',
                        'sex': 'M'
                    }
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        date_entity_in_db.refresh_from_db()
        assert date_entity_in_db.deleted_by.id == user_id

        for entity_property in date_entity_properties_in_db:
            entity_property.refresh_from_db()
            assert entity_property.deleted_by.id == user_id

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb9:
    async def test_modify_reference_to_entity__entity_doesnt_exist__entity_unlistable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        date_entities_in_db = Entity.objects.filter(type='date')
        assert len(date_entities_in_db) == 3

        request = [
            {
                'method': 'PUT',
                'element_type': 'reference',
                'edited_element_id': 'name-4',
                'old_element_id': 'ingredient-2',
                'parameters': {
                    'entity_type': 'date',
                    'entity_properties': {
                        'when': '1410-07-15'
                    }
                }
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        date_entities_in_db = Entity.objects.filter(type='date')
        assert len(date_entities_in_db) == 4

        await communicator.disconnect()


@pytest.mark.usefixtures('annotator_with_ws_and_db_setup', 'reset_db_files_directory_before_each_test')
@pytest.mark.asyncio
@pytest.mark.django_db()
@pytest.mark.integration_tests
class TestAnnotatorWithWsAndDb10:
    async def test_modify_reference_to_entity__entity_exist__entity_listable(self):
        test_name = inspect.currentframe().f_code.co_name

        project_id = 1
        file_id = 1
        user_id = 2

        communicator = get_communicator(project_id, file_id, user_id)

        await communicator.connect()
        await communicator.receive_json_from()

        request = [
            {
                'method': 'PUT',
                'element_type': 'reference',
                'edited_element_id': 'name-4',
                'old_element_id': 'ingredient-2',
                'new_element_id': 'ingredient-0'
            }
        ]
        request_nr = 0

        await communicator.send_json_to(request)
        response = await communicator.receive_json_from()
        verify_response(test_name, response, request_nr)

        await communicator.disconnect()


def get_communicator(project_id, file_id, user_id=None):
    communicator = WebsocketCommunicator(
        application=application,
        path=f'/ws/close_reading/{project_id}_{file_id}/',
    )

    if user_id:
        client = Client()
        user = User.objects.get(id=user_id)
        client.force_login(user)

        communicator.scope['user'] = user

    return communicator


def verify_response(test_name, response, request_nr):
    test_results_file_path = os.path.join(SCRIPT_DIR, 'tests_results.json')
    test_results = read_file(test_results_file_path)
    test_results = json.loads(test_results)
    expected = test_results[test_name][request_nr]

    for field in expected.keys():
        assert response[field] == expected[field]


def read_file(path):
    with open(path, 'r') as file:
        text = file.read()

    return text
