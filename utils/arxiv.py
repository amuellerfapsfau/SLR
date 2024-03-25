import arxiv
import urllib.parse
import logging
import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from utils.utils import setup_logger
from config.cfg import arxiv as cfg
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

logger = setup_logger('arxiv', r'.\\logs\\arxiv.log', level=logging.INFO)


def build_arxiv_query(query):
    # `au:del_maestro AND ti:checkerboard`, not
    # `au:del_maestro+AND+ti:checkerboard`.
    query = query.replace('-', 'NOT ')
    query = query.replace('AND NOT', 'ANDNOT')
    if 'OR NOT' in query:
        logger.error('OR NOT not supported by arxiv API. Please use ANDNOT instead.')
    query = query.replace('(', 'all:(')
    # query = urllib.parse.quote(query)
    # query = query.replace('%20', '+')
    # query = query.replace('%28', 'all:%28')	
    return query

def search_arxiv(client, arxiv_query):
    # Create arxiv search
    search = arxiv.Search(
        query = arxiv_query,
        sort_by = arxiv.SortCriterion.SubmittedDate
    )
    # exhaust results into a list
    results_arxiv = list(client.results(search))
    return results_arxiv

# Store scopus results in sqlite
def store_arxiv_results_in_sqlite(db_name, table_name, arxiv_results, category_taxonomy, mode='replace', id_column=None):
    columns = list(cfg['field_mapping']['search_results'].keys())
    tuple_list = []
    for result in arxiv_results:
        tuple_list.append(tuple([get_result_column(result, column, category_taxonomy) for column in cfg['field_mapping']['search_results'].values()]))
    
    # Convert the results to pandas dataframe
    results = pd.DataFrame(tuple_list, columns=columns)
    # Create a SQLAlchemy engine
    engine = create_engine(f'sqlite:///{db_name}')
    # Store the DataFrame in the SQLite database
    if mode == 'replace':
        results.to_sql(table_name, engine, if_exists='replace', index=False)
    elif mode == 'update':
        insp = reflection.Inspector.from_engine(engine)
        if table_name in insp.get_table_names():
            existing_df = pd.read_sql(f'select * from "{table_name}"', engine)
            results = pd.concat([existing_df, results], axis=0).drop_duplicates(subset=id_column, keep=False)
        results.to_sql(table_name, engine, if_exists='append', index=False)
    else:
        raise NotImplementedError(f'Mode {mode} not implemented')
    return results

def get_result_column(result, column, taxonomy=None):
    if column == 'openaccess':
        return True
    value = getattr(result, column)
    if column == 'categories':
        categories = []
        for category in value:
            if category in taxonomy['category_id'].values:
                cat_row = taxonomy[taxonomy['category_id'] == category].iloc[0]
                cat_str = f"{cat_row['group_name']} - {cat_row['category_name']}"
                categories.append(cat_str)
        return ', '.join(categories)
    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], arxiv.Result.Author):
        return ', '.join([author.name for author in value])
    return value

def load_arxiv_category_taxonomy_db():
    db_name = cfg['category_taxonomy']['db_name']
    # check if db exists
    if not os.path.exists(db_name):
        return build_arxiv_category_taxonomy_db()
    # Create a SQLAlchemy engine
    engine = create_engine(f'sqlite:///{db_name}')
    # Create a table with the category taxonomy
    df = pd.read_sql('select * from category_taxonomy', engine)
    return df

def build_arxiv_category_taxonomy_db():
    db_name = cfg['category_taxonomy']['db_name']
    table_name = cfg['category_taxonomy']['table_name']
    # group tuple list
    group_list = []
    # Scrape taxonomy from web
    url = 'https://arxiv.org/category_taxonomy'
    driver = webdriver.Firefox()
    driver.get(url)
    # get category taxonomly list
    category_taxonomy_root = driver.find_element(By.ID, 'category_taxonomy_list')
    # get groups
    groups = category_taxonomy_root.find_elements(By.CLASS_NAME, 'accordion-head')
    category_bodies = category_taxonomy_root.find_elements(By.CLASS_NAME, 'accordion-body')
    for i, group in enumerate(groups):
        group_name = group.text
        # click on group to make text visible
        WebDriverWait(group, 10).until(EC.element_to_be_clickable(group))
        group.click()
        # get categories
        # category_root = category_bodies[i].find_element(By.CSS_SELECTOR, 'div.accordion-body.open')
        categories = category_bodies[i].find_elements(By.CSS_SELECTOR, 'div.columns.divided')
        for category in categories:
            columns = category.find_elements(By.CSS_SELECTOR, 'div.column')
            category_text = columns[0].text
            category_id = category_text.split('(')[0].strip()
            category_name = category_text.split('(')[1].replace(')', '')
            category_description = columns[1].text
            group_list.append((category_id, group_name, category_name, category_description))
    driver.quit()     
    # Create a SQLAlchemy engine
    engine = create_engine(f'sqlite:///{db_name}')
    # Create a table with the category taxonomy
    df = pd.DataFrame(group_list, columns=['category_id', 'group_name', 'category_name', 'category_description'])
    df.to_sql(table_name, engine, if_exists='replace', index=False)
    return df