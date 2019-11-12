from typing import Iterable, Dict

import pandas as pd
from lxml import etree as et
from tqdm import tqdm
import json

NAMESPACES = {'tei': 'http://www.tei-c.org/ns/1.0', 'xml': 'http://www.w3.org/XML/1998/namespace'}

def create_fast_stats_for_document_collection(doc_gen: Iterable[str])->pd.DataFrame: 
    stats_df = pd.DataFrame(columns=['body', 'header', 'count', 'attr_count'])

    for doc, doc_name in tqdm(doc_gen):
        doc_tree = et.fromstring(doc.encode())

        header_tags = doc_tree.find('.//tei:teiHeader', namespaces=NAMESPACES).iter()
        body_tags = doc_tree.find('.//tei:body', namespaces=NAMESPACES).iter()
        

        for tag in header_tags:
            try:
                tag_name = tag.tag.split('}')[1] if '}' in tag.tag else tag.tag
                if not tag_name in stats_df.index:
                    stats_df.loc[tag_name] = {
                        'body': 0,
                        'header': 1,
                        'count': 1,
                        'attr_count': len(tag.keys()),
                    }
                else:
                    stats_df.loc[tag_name] = {
                        'body': stats_df.loc[tag_name, 'body'],
                        'header': stats_df.loc[tag_name, 'header'] + 1,
                        'count': stats_df.loc[tag_name, 'count'] + 1,
                        'attr_count': stats_df.loc[tag_name, 'attr_count'] + len(tag.keys()),
                    }
            except Exception:
                pass

        for tag in body_tags:
            try:
                tag_name = tag.tag.split('}')[1] if '}' in tag.tag else tag.tag
                if not tag_name in stats_df.index:
                    stats_df.loc[tag_name] = {
                        'body': 1,
                        'header': 0,
                        'count': 1,
                        'attr_count': len(tag.keys()),
                    }
                else:
                    stats_df.loc[tag_name] = {
                        'body': stats_df.loc[tag_name, 'body'] + 1,
                        'header': stats_df.loc[tag_name, 'header'],
                        'count': stats_df.loc[tag_name, 'count'] + 1,
                        'attr_count': stats_df.loc[tag_name, 'attr_count'] + len(tag.keys()),
                    }
            except Exception:
                pass
    
    most_common = stats_df.sort_values('count', ascending=False).iloc[:4] 
    most_common['tag'] = most_common.index
    most_common['attr_count'] = most_common['attr_count'] / most_common['count']

    return most_common.to_dict(orient='records')

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

def get_stats(stats_df):
    n_docs = len(stats_df['document'].unique())
    tag_g = stats_df.groupby('tag')
    tag_stats = tag_g.describe()
    attr_value_counts = stats_df \
            .loc[:,['tag','attr_name', 'attr_value']] \
            .groupby(['tag','attr_name']) \
            .attr_value \
            .value_counts()
    
    stats = ({
        'name': row[0],
        'short_name': row[0].split('}')[1] if '}' in row[0] else row[0],
        'count': row[1]['tag_id']['unique'],
        'coverage': round(100*row[1]['document']['unique'] / n_docs, 2),
        'n_docs': row[1]['document']['unique'],
        'location': row[1]['location']['top'],
        'attributes': tuple({
                'name': attr[0].split('}')[1] if '}' in attr[0] else attr[0],
                'top_perc': round(round(100*attr[1]['attr_value']['freq']/attr[1]['attr_value']['count']),2),
                'top_value': attr[1]['attr_value']['top'],
                'distinct_values': attr_value_counts[row[0]][attr[0]].count(),
                'coverage': round(100*attr[1]['document']['count']/row[1]['tag_id']['unique'], 2),
                'values_json': json.dumps(list(attr_value_counts[row[0]][attr[0]].head().items()))
            }for attr in tag_g.get_group(row[0]).groupby('attr_name').describe().iterrows())
    } for row in tag_stats.iterrows())
        
    return stats