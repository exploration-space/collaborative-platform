import re

from lxml import etree

from django.contrib.auth.models import User

from collaborative_platform.settings import ANONYMOUS_USER_ID, CUSTOM_ENTITY, DEFAULT_ENTITIES, XML_NAMESPACES

from apps.api_vis.models import Certainty, Entity, EntityProperty, EntityVersion
from apps.core.models import VirtualUser
from apps.files_management.models import File, FileVersion
from apps.projects.models import EntitySchema, UncertaintyCategory


XML_ID_KEY = f"{{{XML_NAMESPACES['xml']}}}id"


def get_first_xpath_match(root, xpath, namespaces):
    matches = root.xpath(xpath, namespaces=namespaces)

    if matches:
        match = matches[0]

        return match
    else:
        return None


class ElementsExtractor:
    def __init__(self):
        self.__old_xml_content = ''
        self.__new_xml_content = ''

        self.__tree = None

        self.__listable_entities = []
        self.__unlistable_entities = []
        self.__custom_entities = []

        self.__is_changed = False

        self.__file = None
        self.__file_version = None
        self.__message = ''

    def move_elements_to_db(self, xml_content, file_id):
        self.__old_xml_content = xml_content

        self.__load_file_objects(file_id)
        self.__load_entities_schemes()

        self.__create_tree()
        self.__move_listable_entities()
        self.__copy_unlistable_entities()
        self.__move_custom_entities()
        annotators_map = self.__move_annotators()
        self.__move_certainties(annotators_map)
        self.__create_xml_content()

        self.__check_if_changed()

        return self.__new_xml_content, self.__is_changed, self.__message

    def __load_file_objects(self, file_id):
        self.__file = File.objects.get(id=file_id)
        self.__file_version = FileVersion.objects.get(file=self.__file)

    def __load_entities_schemes(self):
        entities_schemes = self._get_entities_schemes_from_db()

        default_entities_names = DEFAULT_ENTITIES.keys()

        for entity in entities_schemes:
            if entity.name not in default_entities_names:
                self.__custom_entities.append(entity)
            else:
                if DEFAULT_ENTITIES[entity.name]['listable']:
                    self.__listable_entities.append(entity)
                else:
                    self.__unlistable_entities.append(entity)

    def _get_entities_schemes_from_db(self):
        entities_schemes = EntitySchema.objects.filter(taxonomy__project_id=self.__file.project.id)

        return entities_schemes

    def __create_tree(self):
        parser = etree.XMLParser(remove_blank_text=True)

        self.__tree = etree.fromstring(self.__old_xml_content, parser=parser)

    def __move_listable_entities(self):
        for entity in self.__listable_entities:
            list_tag = DEFAULT_ENTITIES[entity.name]['list_tag']
            xpath = f'//default:{list_tag}[@type="{entity.name}List"]//default:{entity.name}'
            elements = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

            self.__create_entities_in_db(elements, entity.name)

            xpath = f'//default:{list_tag}[@type="{entity.name}List"]'
            lists = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

            self.__remove_elements_from_tree(lists)

    def __copy_unlistable_entities(self):
        for entity in self.__unlistable_entities:
            xpath = f'//default:text//default:body//default:{entity.name}'
            elements = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

            self.__create_entities_in_db(elements, entity.name)

    def __move_custom_entities(self):
        for entity in self.__custom_entities:
            xpath = f'//default:listObject[@type="{entity.name}List"]//default:object[@type="{entity.name}"]'
            elements = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

            self.__create_entities_in_db(elements, entity.name, custom=True)

            xpath = f'//default:listObject[@type="{entity.name}List"]'
            lists = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

            self.__remove_elements_from_tree(lists)

    def __move_annotators(self):
        xpath = '//default:teiHeader//default:profileDesc//default:particDesc' \
                '//default:listPerson[@type="PROVIDEDH Annotators"]/default:person'
        annotators = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

        annotators_map = self.__get_or_create_annotators_in_db(annotators)

        xpath = '//default:teiHeader//default:profileDesc//default:particDesc' \
                '//default:listPerson[@type="PROVIDEDH Annotators"]'
        lists = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

        self.__remove_elements_from_tree(lists)

        return annotators_map

    def __move_certainties(self, annotators_map):
        xpath = '//default:teiHeader//default:profileDesc//default:textClass' \
                '//default:classCode[@scheme="http://providedh.eu/uncertainty/ns/1.0"]//default:certainty'

        certainties = self.__tree.xpath(xpath, namespaces=XML_NAMESPACES)

        categories_map = self.__create_categories_map(certainties)

        self.__create_certainties_in_db(certainties, categories_map, annotators_map)

    def __create_entities_in_db(self, elements, entity_name, custom=False):
        for element in elements:
            entity_object = self.__create_entity_object(element, entity_name)
            entity_version_object = self.__create_entity_version_object(entity_object)
            self.__create_entity_properties_objects(element, entity_name, entity_version_object, custom)

    def __create_entity_object(self, element, entity_name):
        entity_object = Entity.objects.create(
            project=self.__file.project,
            file=self.__file,
            xml_id=element.attrib[XML_ID_KEY],
            created_by=User.objects.get(id=ANONYMOUS_USER_ID),
            created_in_version=self.__file.version_number,
            type=entity_name,
        )

        return entity_object

    def __create_entity_version_object(self, entity_object):
        entity_version_object = EntityVersion.objects.create(
            fileversion=self.__file_version,
            entity=entity_object,
        )

        return entity_version_object

    def __create_entity_properties_objects(self, element, entity_name, entity_version_object, custom=False):
        property_objects = []

        if not custom:
            properties = DEFAULT_ENTITIES[entity_name]['properties']
        else:
            properties = CUSTOM_ENTITY['properties']

        for property in properties:
            xpath = f"{properties[property]['xpath']}"
            property_value = get_first_xpath_match(element, xpath, XML_NAMESPACES)
            property_type = properties[property]['type']
            clean_xpath = self.clean_xpath(xpath)

            if not property_value:
                continue

            entity_property_object = self.__create_entity_property_object(property, property_type, property_value,
                                                                          clean_xpath, entity_version_object)

            property_objects.append(entity_property_object)

        EntityProperty.objects.bulk_create(property_objects)

    def __get_or_create_annotators_in_db(self, annotators):
        annotators_map = {}

        for annotator in annotators:
            email = get_first_xpath_match(annotator, './/default:email/text()', XML_NAMESPACES)
            forename = get_first_xpath_match(annotator, './/default:forename/text()', XML_NAMESPACES)
            surname = get_first_xpath_match(annotator, './/default:surname/text()', XML_NAMESPACES)
            xml_id = get_first_xpath_match(annotator, '@xml:id', XML_NAMESPACES)

            user = self.__get_or_create_user(forename, surname, email)

            annotators_map.update({xml_id: user})

        return annotators_map

    def __create_categories_map(self, certainties):
        categories_map = {}

        unique_categories = set()

        for certainty in certainties:
            categories = get_first_xpath_match(certainty, '@ana', XML_NAMESPACES)
            categories = categories.split(' ')

            unique_categories.update(categories)

        for category in unique_categories:
            regex = r'#\w+$'
            match = re.search(regex, category)
            xml_id = match.group()
            xml_id = xml_id.replace('#', '')

            try:
                uncertainty_category = UncertaintyCategory.objects.get(
                    taxonomy__project_id=self.__file.project.id,
                    xml_id=xml_id,
                )

                categories_map.update({category: uncertainty_category})

            except UncertaintyCategory.DoesNotExist:
                continue

        return categories_map

    def __create_certainties_in_db(self, certainties, categories_map, annotators_map):
        certainties_objects = []

        for certainty in certainties:
            categories = get_first_xpath_match(certainty, '@ana', XML_NAMESPACES)
            categories = categories.split(' ')
            categories = [categories_map[category] for category in categories if category in categories_map]

            author_xml_id = get_first_xpath_match(certainty, '@resp', XML_NAMESPACES)
            author_xml_id = author_xml_id.replace('#', '')
            target_xml_id = get_first_xpath_match(certainty, '@target', XML_NAMESPACES)
            target_xml_id = target_xml_id.replace('#', '')
            target_xpath = get_first_xpath_match(certainty, '@match', XML_NAMESPACES)

            try:
                author = annotators_map[author_xml_id]
            except KeyError:
                author = User.objects.get(id=ANONYMOUS_USER_ID)

            certainty = Certainty(
                file=self.__file,
                xml_id=get_first_xpath_match(certainty, '@xml:id', XML_NAMESPACES),
                locus=get_first_xpath_match(certainty, '@locus', XML_NAMESPACES),
                cert=get_first_xpath_match(certainty, '@cert', XML_NAMESPACES),
                degree=get_first_xpath_match(certainty, '@degree', XML_NAMESPACES),
                target_xml_id=target_xml_id,
                target_match=target_xpath,
                asserted_value=get_first_xpath_match(certainty, '@assertedValue', XML_NAMESPACES),
                description=get_first_xpath_match(certainty, './default:desc/text()', XML_NAMESPACES),
                created_in_file_version=self.__file_version,
            )

            certainty.set_created_by(author)
            certainty.categories.add(*categories)

            certainties_objects.append(certainty)

        # TODO: bulk_create cause "IntegrityError: duplicate key value violates unique constraint". Figure out why
        # Certainty.objects.bulk_create(certainties_objects)

        for certainty in certainties_objects:
            certainty.save()

    @staticmethod
    def clean_xpath(xpath):
        clean_xpath = xpath.replace('./text()', '')
        clean_xpath = clean_xpath.replace('/text()', '')
        clean_xpath = clean_xpath.replace('default:', '')

        return clean_xpath

    def __create_entity_property_object(self, property, property_type, property_value, clean_xpath,
                                        entity_version_object):
        entity_property_object = EntityProperty(
            entity_version=entity_version_object,
            xpath=clean_xpath,
            name=property,
            type=property_type,
            created_by=User.objects.get(id=1),
            created_in_version=self.__file.version_number,
        )

        entity_property_object.set_value(property_value)

        return entity_property_object

    @staticmethod
    def __get_or_create_user(forename, surname, email):
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            try:
                if email:
                    user = VirtualUser.objects.get(email=email)
                else:
                    user = VirtualUser.objects.get(first_name=forename, last_name=surname)
            except VirtualUser.DoesNotExist:
                user = VirtualUser.objects.create(
                    first_name=forename,
                    last_name=surname,
                    email=email,
                )
        return user

    def __remove_elements_from_tree(self, elements):
        for element in elements:
            self.remove_element(element, clean_up_parent=True)

    def remove_element(self, element, clean_up_parent=False):
        parent = element.getparent()
        parent.remove(element)

        if len(parent) == 0 and clean_up_parent:
            self.remove_element(parent)

    def __create_xml_content(self):
        self.__new_xml_content = etree.tounicode(self.__tree, pretty_print=True)

    def __check_if_changed(self):
        if self.__old_xml_content != self.__new_xml_content:
            self.__is_changed = True

            self.__message = "Moved elements from file to database."
