from apps.files_management.models import File, FileVersion, Directory
from apps.projects.models import Project

from django.db.models import Q

from lxml import etree as et
import re

#import nltk
import spacy
import en_core_web_md
sp_nlp_en = en_core_web_md.load()

def wrap_text_in_tag(text,substring,tag_name):
    text_node = text.getparent()
    partitions = text.partition(substring)
    text_node.tail = partitions[0]
    
    newElement = et.Element(tag_name)
    newElement.text = partitions[1]
    newElement.tail = partitions[2]
    
    index = text_node.getparent().index(text_node) + 1
    text_node.getparent().insert(index,newElement)

def annotate(file):
	namespaces = {'tei': 'http://www.tei-c.org/ns/1.0', 'xml': 'http://www.w3.org/XML/1998/namespace'}

	f_et = et.XML(file)
	body = f_et.xpath('.//tei:body', namespaces=namespaces)[0]

	withtextnodes = lambda x: len(x.xpath('text()')) > 0
	notemptyline = lambda text: len(text.strip()) > 0
	withnotemptylines = lambda node: any(map(notemptyline, node.xpath('text()')))

	nodes_filtered = filter(withnotemptylines, filter(withtextnodes, body.iter()))
	text_nodes = list(map(lambda x: list(filter(notemptyline, x.xpath('text()'))), nodes_filtered))

	body_text_filtered = ' '.join(map(lambda x: ' '.join(x), text_nodes))

	body_sp = sp_nlp_en(str(body_text_filtered))

	entities = list([e for e in body_sp.ents]) 

	for text_node in text_nodes:
	    for fragment in text_node:
	        for entity in entities:
	            if entity.text in fragment:
	                wrap_text_in_tag(fragment, entity.text, entity.label_)
	                entities.pop(0)

	return et.tostring(f_et).decode('UTF-8')