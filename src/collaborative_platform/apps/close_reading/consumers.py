import json
import logging

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

from apps.projects.models import Contributor, Project
from apps.exceptions import BadRequest, NotModified
from apps.files_management.helpers import create_certainty_elements_for_file_version, certainty_elements_to_json
from apps.files_management.models import FileVersion, File

from .annotator import Annotator
from .helpers import verify_reference
from .models import AnnotatingXmlContent, RoomPresence


logger = logging.getLogger('annotator')


class AnnotatorConsumer(WebsocketConsumer):
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'close_reading_{}'.format(self.room_name)

        project_id, file_id = self.room_name.split('_')

        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            response = {
                'status': 404,
                'message': "Project with id: {} doesn't exist.".format(project_id),
                'xml_content': None,
            }

            response = json.dumps(response)
            self.send(text_data=response)
            return

        contributor = Contributor.objects.filter(project_id=project_id, user_id=self.scope['user'].pk)
        if not contributor:
            response = {
                'status': 403,
                'message': "You aren't contributor in project with id: {}.".format(project_id),
                'xml_content': None,
            }

            response = json.dumps(response)
            self.send(text_data=response)
            return

        try:
            annotating_xml_content = AnnotatingXmlContent.objects.get(file_symbol=self.room_name)

        except AnnotatingXmlContent.DoesNotExist:
            try:
                file_version = FileVersion.objects.filter(file_id=file_id).order_by('-number')[0]
            except FileVersion.DoesNotExist:
                response = {
                    'status': 404,
                    'message': 'File not found.',
                    'xml_content': None,
                }

                response = json.dumps(response)
                self.send(text_data=response)
                return

            file = File.objects.get(id=file_version.file_id, deleted=False)

            with open(file_version.upload.path) as file_version:
                xml_content = file_version.read()
                self.file_name = file.name

                annotating_xml_content = AnnotatingXmlContent(file_symbol=self.room_name, file_name=self.file_name,
                                                              xml_content=xml_content)
                annotating_xml_content.save()

                logger.info(f"Load content of file: '{self.file_name}' in version: {file.version_number} "
                            f"to room: '{self.room_name}'")

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

        logger.info(f"User: '{self.scope['user'].username}' join to room: '{self.room_name}'")

        room_presence, created = RoomPresence.objects.get_or_create(
            room_symbol=self.room_name,
            user=self.scope['user'],
            channel_name=self.channel_name,
        )

        room_presence.save()

        logger.info(f"User: '{self.scope['user'].username}' added to 'room_presence' table")

        file = File.objects.get(id=file_id, deleted=False)
        file_version = FileVersion.objects.get(
            file=file,
            number=file.version_number,
        )

        certainty_elements = create_certainty_elements_for_file_version(file_version, include_uncommitted=True,
                                                                        user=self.scope['user'], for_annotator=True)
        certainties_from_db = certainty_elements_to_json(certainty_elements)

        response = {
            'status': 200,
            'message': 'OK',
            'xml_content': annotating_xml_content.xml_content,
            'certainties_from_db': certainties_from_db,
        }

        response = json.dumps(response)

        self.send(text_data=response)

    def disconnect(self, code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

        logger.info(f"User: '{self.scope['user'].username}' left room: '{self.room_name}'")

        room_presences = RoomPresence.objects.filter(
            room_symbol=self.room_name,
            user=self.scope['user'],
        )

        for presence in room_presences:
            presence.delete()

        logger.info(f"User: '{self.scope['user'].username}' removed from 'room_presence' table")

        remain_users = RoomPresence.objects.filter(room_symbol=self.room_name)

        logger.info(f"In room: '{self.room_name}' left: {len(remain_users)} users")

        if not remain_users:
            AnnotatingXmlContent.objects.get(file_symbol=self.room_name).delete()

            logger.info(f"Remove file content from room: '{self.room_name}'")

    # Receive message from WebSocket
    def receive(self, text_data=None, bytes_data=None):
        if text_data == '"heartbeat"':
            if self.scope['user'].pk is not None:
                room_presences = RoomPresence.objects.filter(
                    room_symbol=self.room_name,
                    user=self.scope['user'],
                ).order_by('-timestamp')

                if room_presences:
                    room_presence = room_presences[0]
                    room_presence.save()

        else:
            try:
                request_json = text_data

                logger.info(f"Get request from user: '{self.scope['user'].username}' with content: '{request_json}'")

                annotating_xml_content = AnnotatingXmlContent.objects.get(file_symbol=self.room_name)
                xml_content = annotating_xml_content.xml_content

                user_id = self.scope['user'].pk
                _, file_id = self.room_name.split('_')
                request_json = json.loads(request_json)

                if 'attribute_name' in request_json and request_json['attribute_name'] == 'sameAs' and \
                        'asserted_value' in request_json and '#' in request_json['asserted_value']:
                    request_json['asserted_value'] = verify_reference(file_id, request_json['asserted_value'])

                annotator = Annotator()
                xml_content = annotator.add_annotation(xml_content, file_id, request_json, user_id)

                annotating_xml_content.xml_content = xml_content
                annotating_xml_content.save()

                # send individual messages with uncommitted certainties to every user
                room_presences = RoomPresence.objects.filter(
                    room_symbol=self.room_name
                )

                file = File.objects.get(id=file_id, deleted=False)
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

                    response = {
                        'status': 200,
                        'message': 'OK',
                        'xml_content': annotating_xml_content.xml_content,
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

            except NotModified as exception:
                self.send_response(304, exception)

            except BadRequest as error:
                self.send_response(400, error)

            except Exception:
                self.send_response(500, "Unhandled exception.")

    def send_response(self, code, message):
        response = {
            'status': code,
            'message': str(message),
            'xml_content': None,
        }

        response = json.dumps(response)

        # Send individual message to request's author
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(
            self.channel_name,
            {
                'type': 'xml_modification',
                'message': response,
            }
        )

        logger.exception(f"Send response to user: '{self.scope['user'].username}' with content: '{response}'")

    # Receive message from room group
    def xml_modification(self, event):
        message = event['message']

        # Send message to WebSocket
        self.send(text_data=message)
