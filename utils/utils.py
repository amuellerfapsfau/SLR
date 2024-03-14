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

# Setup a proxy generator
# pg = ProxyGenerator()
# pg.FreeProxies()
# scholarly.use_proxy(pg)

@RateLimiter(max_calls=20, period=86400)
def query_scholarly(query, patents=False, citations=True, year_low=2010, year_high=None, sort_by='relevance'):
    # Search
    search_query_results = scholarly.search_pubs(query=query,
                                                patents=patents,
                                                citations=citations,
                                                year_low=year_low,
                                                year_high=year_high,
                                                sort_by=sort_by)
    return search_query_results

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

# TODO WIP@AMl
def convert_search_string_to_regex(search_string):
    # Split each OR conjunction separated by AND
    and_terms = search_string.split(') AND (')
    # Remove leading and trailing spaces and ( ) characters
    and_terms = [x.strip(' ()') for x in and_terms]

def decompose_and_terms(and_term):
    # Split each AND conjunction
    or_terms = and_term.split(') AND (')
    # Remove leading and trailing spaces and ( ) characters
    or_terms = [x.strip(' ()') for x in or_terms]
    return or_terms

def contains_wildcards(term):
    if '*' in term or '?' in term or '-' in term:
        return True
    return False

def store_dicts_in_sqlite_with_pandas(db_name, table_name, list_of_dicts):
    # Convert the list of dicts into a DataFrame
    df = pd.DataFrame(list_of_dicts)
    
    # Create a SQLAlchemy engine
    engine = create_engine(f'sqlite:///{db_name}')
    
    # Store the DataFrame in the SQLite database
    df.to_sql(table_name, engine, if_exists='replace', index=False)