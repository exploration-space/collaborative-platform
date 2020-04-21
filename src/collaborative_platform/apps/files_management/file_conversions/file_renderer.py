from lxml import etree

from apps.files_management.helpers import append_unifications
from apps.files_management.file_conversions.xml_tools import add_property_to_element, create_elements_from_xpath, \
    get_first_xpath_match
from apps.api_vis.models import Entity, EntityVersion, EntityProperty, Certainty
from apps.projects.models import EntitySchema

from collaborative_platform.settings import XML_NAMESPACES, DEFAULT_ENTITIES, NS_MAP, CUSTOM_ENTITY


class FileRenderer:
    def __init__(self):
        self.__file_version = None

        self.__tree = None

        self.__listable_entities = []
        self.__custom_entities = []

    def render_file_version(self, file_version):
        self.__file_version = file_version

        self.__load_entities_schemes()

        self.__create_tree()
        self.__append_listable_entities()
        self.__append_custom_entities()
        self.__append_certainties()




        # TODO: Append annotators

        # TODO: Fix appending unifications

        # TODO: Reorder lists in <body>

        # TODO: Move appending line with xml-model here



        # xml_content = append_unifications(xml_content, file_version)

        xml_content = self.__create_xml_content()

        return xml_content

    def __create_tree(self):
        raw_content = self.__file_version.get_raw_content()

        parser = etree.XMLParser(remove_blank_text=True)
        self.__tree = etree.fromstring(raw_content, parser=parser)

    def __load_entities_schemes(self):
        entities_schemes = self.__get_entities_schemes_from_db()

        default_entities_names = DEFAULT_ENTITIES.keys()

        for entity in entities_schemes:
            if entity.name not in default_entities_names:
                self.__custom_entities.append(entity)
            elif DEFAULT_ENTITIES[entity.name]['listable']:
                self.__listable_entities.append(entity)

    def __get_entities_schemes_from_db(self):
        entities_schemes = EntitySchema.objects.filter(taxonomy__project=self.__file_version.file.project)

        return entities_schemes

    def __append_listable_entities(self):
        for entity in self.__listable_entities:
            entities_versions = self.__get_entities_versions_from_db(entity.name)

            if entities_versions:
                elements = self.__create_entities_elements(entities_versions)

                list_tag = DEFAULT_ENTITIES[entity.name]['list_tag']

                if entity.body_list:
                    list_xpath = f'./default:text/default:body/default:div[@type="{entity.name}"]/' \
                                 f'default:{list_tag}[@type="{entity.name}List"]'
                else:
                    list_xpath = f'./default:teiHeader/default:fileDesc/default:sourceDesc/' \
                                 f'default:{list_tag}[@type="{entity.name}List"]'

                self.__append_elements_to_the_list(elements, list_xpath)

    def __append_custom_entities(self):
        for entity in self.__custom_entities:
            entities_versions = self.__get_entities_versions_from_db(entity.name)

            if entities_versions:
                elements = self.__create_entities_elements(entities_versions, custom=True)

                if entity.body_list:
                    list_xpath = f'./default:text/default:body/default:div[@type="{entity.name}"]/' \
                                 f'default:listObject[@type="{entity.name}List"]'
                else:
                    list_xpath = f'./default:teiHeader/default:fileDesc/default:sourceDesc/' \
                                 f'default:listObject[@type="{entity.name}List"]'

                self.__append_elements_to_the_list(elements, list_xpath)

    def __get_entities_versions_from_db(self, entity_type):
        entities_versions = EntityVersion.objects.filter(
            file_version=self.__file_version,
            entity__type=entity_type,
        )

        return entities_versions

    def __create_entities_elements(self, entities_versions, custom=False):
        elements = []

        for entity_version in entities_versions:
            entity_element = self.__create_entity_element(entity_version, custom)

            self.__append_entity_properties(entity_element, entity_version, custom)

            elements.append(entity_element)

        return elements

    def __create_entity_element(self, entity_version, custom=False):
        default_prefix = '{%s}' % XML_NAMESPACES['default']
        xml_prefix = '{%s}' % XML_NAMESPACES['xml']

        if not custom:
            entity_element = etree.Element(default_prefix + entity_version.entity.type, nsmap=NS_MAP)
        else:
            entity_element = etree.Element(default_prefix + 'object', nsmap=NS_MAP)
            entity_element.set('type', entity_version.entity.type)

        entity_element.set(xml_prefix + 'id', entity_version.entity.xml_id)
        entity_element.set('resp', f'#annotator-{entity_version.entity.created_by_id}')

        return entity_element

    def __append_entity_properties(self, entity_element, entity_version, custom=False):
        entities_properties = EntityProperty.objects.filter(
            entity_version=entity_version
        )

        if not custom:
            properties = DEFAULT_ENTITIES[entity_version.entity.type]['properties']
        else:
            properties = CUSTOM_ENTITY['properties']

        for entity_property in entities_properties:
            xpath = properties[entity_property.name]['xpath']
            value = entity_property.get_value(as_str=True)

            add_property_to_element(entity_element, xpath, value)

    def __append_elements_to_the_list(self, elements, list_xpath):
        list = get_first_xpath_match(self.__tree, list_xpath, XML_NAMESPACES)

        if not list:
            tree = create_elements_from_xpath(self.__tree, list_xpath)
            list = get_first_xpath_match(self.__tree, list_xpath, XML_NAMESPACES)

        for element in elements:
            list.append(element)

    def __create_xml_content(self):
        xml_content = etree.tounicode(self.__tree, pretty_print=True)

        return xml_content

    def __append_certainties(self):
        certainties = self.__get_certainties_from_db()

        if certainties:
            elements = self.__create_certainties_elements(certainties)

            list_xpath = './default:teiHeader/default:profileDesc/default:textClass/' \
                         'default:classCode[@scheme="http://providedh.eu/uncertainty/ns/1.0"]'

            self.__append_elements_to_the_list(elements, list_xpath)

    def __get_certainties_from_db(self):
        certainties = Certainty.objects.filter(
            file_version=self.__file_version
        )

        return certainties

    def __create_certainties_elements(self, certainties):
        elements = []

        for certainty in certainties:
            certainty_element = self.__create_certainty_element(certainty)

            elements.append(certainty_element)

        return elements

    def __create_certainty_element(self, certainty):
        default_prefix = '{%s}' % XML_NAMESPACES['default']
        xml_prefix = '{%s}' % XML_NAMESPACES['xml']

        certainty_element = etree.Element(default_prefix + 'certainty', nsmap=NS_MAP)

        certainty_element.set(xml_prefix + 'id', certainty.xml_id)
        certainty_element.set('resp', f'#annotator-{certainty.created_by_id}')

        certainty_element.set('ana', 'PUT CATEGORIES HERE')
        certainty_element.set('locus', certainty.locus)
        certainty_element.set('cert', certainty.cert)
        certainty_element.set('target', f'#{certainty.target_xml_id}')

        if certainty.asserted_value:
            certainty_element.set('assertedValue', certainty.asserted_value)

        if certainty.description:
            description_element = etree.Element(default_prefix + 'desc', nsmap=NS_MAP)
            description_element.text = certainty.description

            certainty_element.append(description_element)

        return certainty_element
