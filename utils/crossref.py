import logging
import re
import pandas as pd
from scholarly import scholarly
from scholarly import ProxyGenerator
from crossref.restful import Works
from sqlalchemy import create_engine
from ratelimiter import RateLimiter


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

def fill_missing_values_using_crossref(works: Works, df, important_columns):
    # identify rows with important missing values
    missing_values = df[df[important_columns].isnull().any(axis=1)]
    # iterate over rows and fill missing values
    for i, row in missing_values.iterrows():
        title = row['title']
        author = row['author_names']
        year = row['coverDate']
        crossref_result = call_crossref(works, title, author, year)
        if crossref_result is not None:
            for col in important_columns:
                if pd.isnull(row[col]):
                    if col in crossref_result:
                        df.at[i, col] = crossref_result[col]

@RateLimiter(max_calls=50, period=1)
def call_crossref(works: Works, title, author, year):
    if isinstance(author, list):
        author = ', '.join(author)
    bibliographic = f'{title} {author} {year}' 
    logging.info(f'Crossref search: {bibliographic}')
    results = works.query(bibliographic=bibliographic)
    for i, item in enumerate(results):
        if i == 50:
            logging.warning(f'Not within first 50 results. Breaking')
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
            logging.info(found_authors)
            return item
        
    return None