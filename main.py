# from scholarly import scholarly
# from scholarly import ProxyGenerator
import logging
import numpy as np
from crossref.restful import Works
from semanticscholar import SemanticScholar
from ratelimiter import RateLimiter
from utils.utils import *
from utils.scopus import *
from utils.crossref import *
from utils.semantic_scholar import *
from utils.acm import *
from utils.arxiv import *
from config import cfg

logger = setup_logger('main', r'.\\logs\\main.log', level=logging.INFO)
logger.info('Run main.py')

# Setup a proxy generator
# pg = ProxyGenerator()
# pg.FreeProxies()
# scholarly.use_proxy(pg)


# Create crossref object
works = Works()

# Create Semantic Scholar object
ss = SemanticScholar()

# Define a search
methodology_substring = '"machine learning" OR "deep learning" OR "neural?network" OR "learn* system" OR "virtual metrology" OR "artificial intelligence" OR "data mining" OR "data science" OR "big data" OR predictive*' # modeling" OR "predictive analytics" OR "predictive analysis" OR "predictive algorithm" OR "predictive model" OR "predictive system" OR "predictive method" OR "predictive technique" OR "predictive tool" OR "predictive technology" OR "predictive approach" OR "predictive framework" OR "predictive process" OR "predictive application" OR "predictive software" OR "predictive hardware" OR "predictive service" OR "predictive product" OR "predictive solution" OR "predictive platform" OR "predictive environment"'
process_substring = '"coat* machine" OR "physical vapor deposition" OR "physical vapour deposition" OR "pvd" OR "chemical vapor deposition" OR "chemical vapour deposition" OR "CVD" OR "sputter*" OR "evaporation" OR "ebeam" AND -disease'
process_substring_arxiv = '"coat* machine" OR "physical vapor deposition" OR "physical vapour deposition" OR "pvd" OR "chemical vapor deposition" OR "chemical vapour deposition" OR "CVD" OR "sputter*" OR "evaporation" OR "ebeam"'
not_disease_substring = '-disease'
product_substring = '"thin?film" OR "coat*" OR "lamination"'
application_substring = '"semiconductor" OR "solar cell" OR "photovoltaic" OR "lens" OR "reflectance" OR "reflective" OR "anti?reflective" OR "ophtalmic" OR "optical" OR "optoelectronic" OR "optical filter" OR "optical coating" OR "optical film" OR "optical layer" OR "optical lamination" OR "optical device" OR "optical component" OR "optical system" OR "optical instrument" OR "optical equipment" OR "optical material" OR "optical technology" OR "optical process" OR "optical product" OR "optical application" OR "optical service" OR "optical solution" OR "optical tool" OR "optical technique" OR "optical method" OR "optical approach"'
application_substring = '"lens*" OR "reflectance" OR "reflective" OR "anti?reflective" OR "ophtalmic" OR "optoelectronic" OR "optical filter" OR "optical coating" OR "optical film"' # OR "optical device" OR "optical component" OR "optical system" OR "optical instrument" OR "optical equipment" OR "optical material" OR "optical technology" OR "optical process" OR "optical product" OR "optical application" OR "optical service" OR "optical solution" OR "optical tool" OR "optical technique" OR "optical method" OR "optical approach"'
search_string = f"({methodology_substring}) AND ({process_substring}) AND ({product_substring}) AND ({application_substring})"
# search_string = f"({methodology_substring}) AND ({product_substring} OR {process_substring}) AND ({application_substring})" # testweise
arxiv_search_string = f"({methodology_substring}) AND ({process_substring_arxiv}) {not_disease_substring} AND ({product_substring}) AND ({application_substring})"

# wip arxiv
category_taxonomy_df = load_arxiv_category_taxonomy_db()

# Construct the default API client.
client = arxiv.Client()
arxiv_query = build_arxiv_query(search_string)
# Create arxiv search
search = arxiv.Search(
  query = arxiv_query,
#   max_results = 10,
  sort_by = arxiv.SortCriterion.SubmittedDate
)
# exhaust results into a list
results_arxiv = list(client.results(search))
# store arxiv search results in sqlite
arxiv_db = r"C:\\Repositories\\_Data\SLR\\arxiv.db"
store_arxiv_results_in_sqlite(arxiv_db, "search_results", results_arxiv, category_taxonomy_df)#, mode='replace', id_column=None)

# works
acm_results = []
acm_url = build_acm_search_url(search_string)
scrape_acm_search_results(acm_url, acm_results)

# Define database
scopus_db = r"C:\\Repositories\\_Data\SLR\\scopus.db"

# Query scopus
search_string_scopus = convert_search_string_to_scopus(search_string)
scopus_results = search_scopus(search_string_scopus)
# store scopus search results in sqlite
scopus_results_df = store_scopus_results_in_sqlite(scopus_db, 'search_results', scopus_results)
abstract_retrieval_df = retrieve_scopus_abstracts_from_search_results(scopus_results_df, scopus_db, backward_search_iteration=0)

scopus_results_df = scopus_results_df.merge(abstract_retrieval_df, on='eid', how='left')
scopus_results_df = remove_irrelevant_scopus_search_results(scopus_results_df)

# get dict_items where the value of cfg.essential_columns is are in cfg.scopus['field_mapping']['search_results'].keys()
important_columns = {}
for element in cfg.scopus['field_mapping']['search_results'].items():
    if element[0] in cfg.essential_columns:
        important_columns[element[0]] = element[1]

fill_missing_values_using_crossref(works, scopus_results_df, important_columns)
fill_missing_values_using_semantic_scholar(ss, scopus_results_df, important_columns)
regex = convert_search_string_to_regex(search_string)

# Define search parameters for scholar
include_patens = False
include_citations = True
year_low = 2010
year_high = None
sort_by = 'relevance' # 'relevance', 'date', 'citations'

db_crossref = r"C:\\cross_ref.db"
db_scholar = r"C:\\scholar.db"


# cross_ref_results_list = []
# cross_ref_results = works.query(bibliographic=query)
# for item in cross_ref_results.filter(from_pub_date=year_low):
#     cross_ref_results_list.append(item)
# store_dicts_in_sqlite_with_pandas(db, 'crossref', cross_ref_results)

# Search
search_query_results = query_scholarly(query=search_string,
                                       patents=include_patens,
                                       citations=include_citations,
                                       year_low=year_low,
                                       year_high=year_high,
                                       sort_by=sort_by)

results_scholar = []
results_crossref = []
results_crossref_filtered = []
results = []
scholar_only = []

for pub in search_query_results:
    # scholarly.pprint(pub)
    # pub = scholarly.fill(pub)
    title = pub['bib']['title']
    year = pub['bib']['pub_year']
    author = pub['bib']['author']
    logging.info(f'Processing {title} {author} {year}')

    # Get DOI using crossref
    cref_res = call_crossref(works, title, author, year)
    if cref_res:
        results_crossref.append(cref_res)
    else:
        logging.warning(f'No crossref results found for {title} {author} {year}')
        pub = scholarly.fill(pub)
        logging.info('Using Google Scholar only')
        scholar_only.append(pub)

store_dicts_in_sqlite_with_pandas(db_crossref, 'crossref', results_crossref)
store_dicts_in_sqlite_with_pandas(db_scholar, 'scholar', scholar_only)
    # for item in cref_res:
    #     print(item)
    # if len(cref_res) > 1:
    #     print('More than one result')
    # else:
    #     cref_res = cref_res[0]
    # doi = cref_res['DOI']

    # pub = scholarly.fill(pub)
    # scholarly.pprint(pub)

