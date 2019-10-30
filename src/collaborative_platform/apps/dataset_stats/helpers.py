from typing import Iterable, Dict

import pandas as pd
from lxml import etree as et
from tqdm import tqdm

NAMESPACES = {'tei': 'http://www.tei-c.org/ns/1.0', 'xml': 'http://www.w3.org/XML/1998/namespace'}

def create_summary_for_document(doc_raw: str, doc_name:str='undefined')->pd.DataFrame: 
    doc_tree = et.fromstring(doc_raw.encode())

    header_tags = doc_tree.find('.//tei:teiHeader', namespaces=NAMESPACES).iter()
    body_tags = doc_tree.find('.//tei:body', namespaces=NAMESPACES).iter()

    stats_df = pd.DataFrame(columns=['document', 'tag', 'tag_id', 'location', 'attr_name', 'attr_value'])

    tag_count = 0
    for tag in header_tags:
        for attr_name, attr_value in tag.items():
            stats_df.loc[len(stats_df)] = {
                'document': doc_name,
                'tag': tag.tag,
                'tag_id': doc_name + str(tag_count),
                'location': 'header',
                'attr_name': attr_name,
                'attr_value': attr_value
            }
        tag_count += 1
        
    for tag in body_tags:
        for attr_name, attr_value in tag.items():
            stats_df.loc[len(stats_df)] = {
                'document': doc_name,
                'tag': tag.tag,
                'tag_id': doc_name + str(tag_count),
                'location': 'body',
                'attr_name': attr_name,
                'attr_value': attr_value
            }
        tag_count += 1

    return stats_df

def create_summary_for_document_collection(doc_gen: Iterable[str])->pd.DataFrame: 
    stats_df = pd.DataFrame(columns=['document', 'tag', 'tag_id', 'location', 'attr_name', 'attr_value'])

    for doc, doc_name in tqdm(doc_gen):
        stats = create_summary_for_document(doc, doc_name)
        stats_df = stats_df.append(stats)

    return stats_df

def get_stats(stats_df:pd.DataFrame)->Dict:
    n_docs = len(stats_df['document'].unique())
    tag_g = stats_df.groupby('tag')
    tag_stats = tag_g.describe()
    
    stats = ({
        'name': row[0].split('}')[1] if '}' in row[0] else row[0],
        'count': row[1]['tag_id']['unique'],
        'coverage': 100*row[1]['document']['unique'] / n_docs,
        'n_docs': row[1]['document']['unique'],
        'location': row[1]['location']['top'],
        'attributes': tuple({
                'name': attr[0].split('}')[1] if '}' in attr[0] else attr[0],
                'top_perc': round(100*attr[1]['attr_value']['freq']/attr[1]['attr_value']['count']),
                'top_value': attr[1]['attr_value']['top'],
                'coverage': round(100*attr[1]['document']['count']/row[1]['tag_id']['unique']),
                'values': []
            }for attr in tag_g.get_group(row[0]).groupby('attr_name').describe().iterrows())
    } for row in tag_stats.iterrows())
    
    return stats