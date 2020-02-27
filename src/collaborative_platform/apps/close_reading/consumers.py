import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

from apps.projects.models import Contributor, Project
from apps.exceptions import BadRequest, Forbidden, NotModified
from apps.files_management.helpers import create_certainty_elements_for_file_version, certainty_elements_to_json
from apps.files_management.models import FileVersion, File

from .annotator import Annotator
from .helpers import verify_reference
from .models import AnnotatingXmlContent, RoomPresence


logger = logging.getLogger('annotator')


class AnnotatorConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.__room_name = ''
        self.__room_group_name = ''

        self.__project_id = ''
        self.__file_id = ''

        self.__annotating_xml_content = None

    def connect(self):
        try:
            self.__room_name = self.scope['url_route']['kwargs']['room_name']
            self.__room_group_name = f'close_reading_{self.__room_name}'
            self.__project_id, self.__file_id = self.__room_name.split('_')

            self.__check_if_project_exist()
            self.__check_if_user_is_contributor()

            self.__load_xml_content()
            self.__add_user_to_room_group()
            self.__add_user_to_presence_table()

            self.accept()

            certainties_from_db = self.__get_certainties_from_db()
            xml_content = self.__annotating_xml_content.xml_content

            response = {
                'status': 200,
                'message': 'OK',
                'xml_content': xml_content,
                'certainties_from_db': certainties_from_db,
            }

            response = json.dumps(response)

            self.send(text_data=response)

        except BadRequest as error:
            self.accept()
            self.__send_error(400, error)
            self.close()

        except Forbidden as error:
            self.accept()
            self.__send_error(403, error)
            self.close()

    def __check_if_project_exist(self):
        try:
            _ = Project.objects.get(id=self.__project_id)
        except Project.DoesNotExist:
            raise BadRequest(f"Project with id: {self.__project_id} doesn't exist.")

    def __check_if_user_is_contributor(self):
        contributor = Contributor.objects.filter(project_id=self.__project_id, user_id=self.scope['user'].pk)

        if not contributor:
            raise Forbidden(f"You aren't contributor in project with id: {self.__project_id}.")

    def __load_xml_content(self):
        try:
            self.__annotating_xml_content = AnnotatingXmlContent.objects.get(file_symbol=self.__room_name)

        except AnnotatingXmlContent.DoesNotExist:
            try:
                file_version = FileVersion.objects.filter(file_id=self.__file_id).order_by('-number')[0]
            except IndexError:
                raise BadRequest(f"File with id: {self.__file_id} doesn't exist.")

            file = File.objects.get(id=file_version.file_id, deleted=False)

            with open(file_version.upload.path) as file_version:
                xml_content = file_version.read()

                self.__annotating_xml_content = AnnotatingXmlContent(file_symbol=self.__room_name, file_name=file.name,
                                                                     xml_content=xml_content)
                self.__annotating_xml_content.save()

                logger.info(f"Load content of file: '{file.name}' in version: {file.version_number} "
                            f"to room: '{self.__room_name}'")

    def __add_user_to_room_group(self):
        async_to_sync(self.channel_layer.group_add)(
            self.__room_group_name,
            self.channel_name
        )

        logger.info(f"User: '{self.scope['user'].username}' join to room group: '{self.__room_group_name}'")

    def __add_user_to_presence_table(self):
        room_presence, created = RoomPresence.objects.get_or_create(
            room_symbol=self.__room_name,
            user=self.scope['user'],
            channel_name=self.channel_name,
        )

        room_presence.save()

        logger.info(f"User: '{self.scope['user'].username}' added to 'room_presence' table")

    def __get_certainties_from_db(self):
        file = File.objects.get(id=self.__file_id, deleted=False)
        file_version = FileVersion.objects.get(
            file=file,
            number=file.version_number,
        )

        certainty_elements = create_certainty_elements_for_file_version(file_version, include_uncommitted=True,
                                                                        user=self.scope['user'], for_annotator=True)
        certainties_from_db = certainty_elements_to_json(certainty_elements)

        return certainties_from_db

    def disconnect(self, code):
        self.__remove_user_from_room_group()
        self.__remove_user_from_presence_table()

        self.close()

        remain_users = self.__count_remain_users()

        if not remain_users:
            self.__remove_xml_content()

    def __remove_user_from_room_group(self):
        if self.groups and self.channel_name in self.groups[self.__room_group_name]:
            async_to_sync(self.channel_layer.group_discard)(
                self.__room_group_name,
                self.channel_name
            )

            logger.info(f"User: '{self.scope['user'].username}' left room group: '{self.__room_group_name}'")

    def __remove_user_from_presence_table(self):
        if self.scope['user'].pk is not None:
            room_presences = RoomPresence.objects.filter(
                room_symbol=self.__room_name,
                user=self.scope['user'],
            )

            for presence in room_presences:
                presence.delete()

            logger.info(f"User: '{self.scope['user'].username}' removed from 'room_presence' table")

    def __count_remain_users(self):
        remain_users = RoomPresence.objects.filter(room_symbol=self.__room_name)

        logger.info(f"In room: '{self.__room_name}' left: {len(remain_users)} users")

        return len(remain_users)

    def __remove_xml_content(self):
        try:
            AnnotatingXmlContent.objects.get(file_symbol=self.__room_name).delete()

            logger.info(f"Remove file content from room: '{self.__room_name}'")
        except AnnotatingXmlContent.DoesNotExist:
            pass

    def receive(self, text_data=None, bytes_data=None):
        if text_data == '"heartbeat"':
            self.__update_users_presence()

        elif text_data == 'ping':
            self.send('pong')

        else:
            try:
                request = self.__parse_text_data(text_data)
                self.__update_file(request)
                self.__send_personalized_changes_to_users()

            except NotModified as exception:
                self.__send_error(304, exception)

            except BadRequest as error:
                self.__send_error(400, error)

            except Exception:
                self.__send_error(500, "Unhandled exception.")

    def __update_users_presence(self):
        if self.scope['user'].pk is not None:
            room_presences = RoomPresence.objects.filter(
                room_symbol=self.__room_name,
                user=self.scope['user'],
            ).order_by('-timestamp')

            if room_presences:
                room_presence = room_presences[0]
                room_presence.save()

    def __parse_text_data(self, text_data):
        request = json.loads(text_data)
        logger.info(f"Get request from user: '{self.scope['user'].username}' with content: '{request}'")

        return request

    def __update_file(self, request):
        xml_content = self.__annotating_xml_content.xml_content
        user_id = self.scope['user'].pk
        _, file_id = self.__room_name.split('_')

        if 'attribute_name' in request and request['attribute_name'] == 'sameAs' and \
                'asserted_value' in request and '#' in request['asserted_value']:
            request['asserted_value'] = verify_reference(file_id, request['asserted_value'])

        annotator = Annotator()
        xml_content = annotator.add_annotation(xml_content, file_id, request, user_id)

        self.__annotating_xml_content.xml_content = xml_content
        self.__annotating_xml_content.save()

    def __send_personalized_changes_to_users(self):
        room_presences = RoomPresence.objects.filter(
            room_symbol=self.__room_name
        )

        file = File.objects.get(id=self.__file_id, deleted=False)
        file_version = FileVersion.objects.get(
            file=file,
            number=file.version_number,
        )

        for presence in room_presences:
            certainty_elements = create_certainty_elements_for_file_version(file_version,
                                                                            include_uncommitted=True,
                                                                            user=presence.user,
                                                                            for_annotator=True)
            certainties_from_db = certainty_elements_to_json(certainty_elements)
            xml_content = self.__annotating_xml_content.xml_content

            response = {
                'status': 200,
                'message': 'OK',
                'xml_content': xml_content,
                'certainties_from_db': certainties_from_db,
            }

            response = json.dumps(response)

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(
                presence.channel_name,
                {
                    'type': 'xml_modification',
                    'message': response,
                }
            )

        user_names = ', '.join([f"'{presence.user.username}'" for presence in room_presences])

        logger.info(f"Content of file: '{file.name}' updated with request from user: "
                    f"'{self.scope['user'].username}' was sent to users: {user_names}")

    def __send_error(self, code, message):
        response = {
            'status': code,
            'message': str(message),
            'xml_content': None,
        }

        response = json.dumps(response)
        self.send(text_data=response)

        logger.exception(f"Send response to user: '{self.scope['user'].username}' with content: '{response}'")

    def xml_modification(self, event):
        message = event['message']
        self.send(text_data=message)
