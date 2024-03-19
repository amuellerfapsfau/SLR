from semanticscholar import SemanticScholar
import numpy as np
import pandas as pd
import logging
from config import cfg
from utils.utils import setup_logger

logger = setup_logger('semantic_scholar', r'.\\logs\\semantic_scholar.log', level=logging.INFO)

def try_find_ss_result(row, ss_results):
    ss_result = None
    try:
        if 'doi' in row and row['doi']:
            doi = row['doi']
            for ss in ss_results:
                if 'externalIds' in ss.keys() and 'DOI' in ss['externalIds']:
                    if ss['externalIds']['DOI'] == doi:
                        logger.info(f'Found ss result for doi {doi}')
                        return ss
    except Exception as e:
        logger.error(f'Error finding ss result for doi {doi}: {e}')
    logger.info('Try using title')
    title = row['title']
    for ss in ss_results:
        if ss['title'] == title:
            ss_result = ss
            logger.info(f'Found ss result for title {title}')
            break
    title = title.lower()
    for ss in ss_results:
        if ss['title'].lower() == title:
            ss_result = ss
            logger.info(f'Found ss result for title {title}')
            break
    return ss_result

# TODO CONTINUE HERE
def get_semantic_scholar_value(field, ss_result):
    unparsed_value = ss_result[cfg.semantic_scholar['field_mapping']['search_results'][field]]
    match field:
        case 'author': # dictionary TODO
            result = []
            for author in unparsed_value:
                result.append(author['name'])
            return '; '.join(result)
        case 'country': # TODO complicated
            None
        case 'doi':
            try:
                return unparsed_value['DOI']
            except:
                return None
        case 'funded_by':
            funders = []
            for funder in unparsed_value:
                if 'name' in funder:
                    funders.append(funder['name'])
            return '; '.join(funders)
        case 'subject_areas':
            result = []
            result.extend(unparsed_value['fieldsOfStudy'])
            for area in unparsed_value['s2FieldsOfStudy']:
                if 'category' in area and area['category'] not in result:
                    result.append(area['category'])
            return result
        case _:
            if isinstance(unparsed_value, list):
                if len(unparsed_value) == 1:
                    return unparsed_value[0]
                return '; '.join(unparsed_value) # TODO
            if isinstance(unparsed_value, dict):
                return '; '.join(unparsed_value.values()) # TODO
            return unparsed_value # cited_by_count, open_access, publication_name, identifier, date, title, abstract

def fill_missing_values_using_semantic_scholar(ss: SemanticScholar, df, important_columns_dict):
    # identify rows with important missing values
    missing_values = df[df[list(important_columns_dict.values())].isnull().any(axis=1)]
    # get paper ids of missing values
    missing_values_ids = list(np.where(missing_values['doi'].notnull(), missing_values['doi'], missing_values['title']))
    results = ss.get_papers(missing_values_ids)
    # iterate over rows and fill missing values
    for i, missing_values_row in missing_values.iterrows():
        # TODO get current result from ss
        ss_item = try_find_ss_result(missing_values_row, results)
        if ss_item is not None:
            for key in important_columns_dict.keys():
                if pd.isnull(missing_values_row[important_columns_dict[key]]):
                    if cfg.semantic_scholar['field_mapping']['search_results'][key] in ss_item.keys():
                        # TODO continue here
                        result = get_semantic_scholar_value(key, ss_item)
                        df.at[i, important_columns_dict[key]] = result
                        logger.info(f'Filled {key} with {result}')
                    else:
                        logger.warning(f'No value found for {key}')
        else:
            logger.warning(f'No semantic scholar result found for {missing_values_row["title"]}')

