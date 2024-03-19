import logging
import re
import pandas as pd
from scholarly import scholarly
from scholarly import ProxyGenerator
from crossref.restful import Works
from sqlalchemy import create_engine
from ratelimiter import RateLimiter

def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    
    handler = logging.FileHandler(log_file)        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

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