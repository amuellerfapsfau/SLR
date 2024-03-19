import logging
import re
import pandas as pd
from scholarly import scholarly
from scholarly import ProxyGenerator
from crossref.restful import Works
from sqlalchemy import create_engine
from ratelimiter import RateLimiter
from config import cfg
from utils.utils import setup_logger

logger = setup_logger('crossref', r'.\\logs\\crossref.log', level=logging.INFO)


def fill_missing_values_using_crossref(works: Works, df, important_columns_dict):
    # identify rows with important missing values
    missing_values = df[df[list(important_columns_dict.values())].isnull().any(axis=1)]
    logger.info(f'Filling missing values using Crossref for {len(missing_values)} rows')
    # iterate over rows and fill missing values
    for i, missing_values_row in missing_values.iterrows():
        title = missing_values_row['title']
        author = missing_values_row['author_names']
        year = missing_values_row['coverDate']
        crossref_result = call_crossref(works, title, author, year)
        if crossref_result is not None:
            logger.info(f'Crossref result found for {title} {author} {year}')
            for key in important_columns_dict.keys():
                if pd.isnull(missing_values_row[important_columns_dict[key]]):
                    if cfg.crossref['field_mapping']['search_results'][key] in crossref_result:
                        result = get_crossref_value(key, crossref_result)
                        df.at[i, important_columns_dict[key]] = result
                        logger.info(f'Filled {key} with {result}')
                    else:
                        logger.warning(f'No value found for {key}')
        else:
            logger.warning(f'No crossref result found for {title} {author} {year}')


def get_crossref_value(field, crossref_result):
    unparsed_value = crossref_result[cfg.crossref['field_mapping']['search_results'][field]]
    match field:
        case 'author': # dictionary TODO
            None
        case 'country': # TODO complicated
            None
        case 'date': # TODO parse from date-parts -> published['date-parts'][0] [0]=year, [1]=month, [2]=day
            None
        case 'funded_by':
            funders = []
            for funder in unparsed_value:
                if 'name' in funder:
                    funders.append(funder['name'])
            return '; '.join(funders)
        case _:
            return unparsed_value[0]

@RateLimiter(max_calls=50, period=1)
def call_crossref(works: Works, title, author, year):
    if isinstance(author, list):
        author = ', '.join(author)
    bibliographic = f'{title} {author} {year}' 
    logger.info(f'Crossref search: {bibliographic}')
    results = works.query(bibliographic=bibliographic)
    for i, item in enumerate(results):
        if i == 50:
            logger.warning(f'Not within first 50 results. Breaking')
            break 
        # check if title and author exists
        if 'title' not in item:
            continue
        if 'author' not in item:
            continue
        if item['title'][0].lower() == title.lower():
            # check authors
            found_authors = []
            for cref_author in item['author']:
                if cref_author['family'].lower() in author.lower():
                    found_authors.append(cref_author['family'])
            logger.info(found_authors)
            return item
        
    return None