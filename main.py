# from scholarly import scholarly
# from scholarly import ProxyGenerator
import logging
from crossref.restful import Works
from ratelimiter import RateLimiter
from utils.utils import *
from utils.scopus import *

# Set up logging
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

# Setup a proxy generator
# pg = ProxyGenerator()
# pg.FreeProxies()
# scholarly.use_proxy(pg)

# Define a search
methodology_substring = '"machine learning" OR "deep learning" OR "neural?network" OR "learn* system" OR "virtual metrology" OR "artificial intelligence" OR "data mining" OR "data science" OR "big data" OR "predictive modeling" OR "predictive analytics" OR "predictive analysis" OR "predictive algorithm" OR "predictive model" OR "predictive system" OR "predictive method" OR "predictive technique" OR "predictive tool" OR "predictive technology" OR "predictive approach" OR "predictive framework" OR "predictive process" OR "predictive application" OR "predictive software" OR "predictive hardware" OR "predictive service" OR "predictive product" OR "predictive solution" OR "predictive platform" OR "predictive environment"'
process_substring = '"physical vapor depostion" OR "physical vapour depostion" OR "pvd" OR "chemical vapor depostion" OR "chemical vapour depostion" OR "CVD" OR "sputter" OR "evaporation" OR "ebeam" AND -disease'
product_substring = '"thin?film" OR "coat*" OR "layer" OR "lamination"'
application_substring = '"semiconductor" OR "solar cell" OR "photovoltaic" OR "reflectance" OR "reflective" OR "anti?reflective" OR "ophtalmic" OR "optical" OR "optoelectronic" OR "optical filter" OR "optical coating" OR "optical film" OR "optical layer" OR "optical lamination" OR "optical device" OR "optical component" OR "optical system" OR "optical instrument" OR "optical equipment" OR "optical material" OR "optical technology" OR "optical process" OR "optical product" OR "optical application" OR "optical service" OR "optical solution" OR "optical tool" OR "optical technique" OR "optical method" OR "optical approach"'
search_string = f"({methodology_substring}) AND ({process_substring}) AND ({product_substring}) AND ({application_substring})"

# Define database
scopus_db = r"C:\\Repositories\\_Data\SLR\\scopus.db"

# Query scopus
search_string_scopus = convert_search_string_to_scopus(search_string)
scopus_results = search_scopus(search_string_scopus)
# store scopus search results in sqlite
scopus_results = store_scopus_results_in_sqlite(scopus_db, 'search_results', scopus_results)
retrieve_scopus_abstracts_from_search_results(scopus_results, scopus_db, backward_search_iteration=0)


regex = convert_search_string_to_regex(search_string)

# Define search parameters for scholar
include_patens = False
include_citations = True
year_low = 2010
year_high = None
sort_by = 'relevance' # 'relevance', 'date', 'citations'

db_crossref = r"C:\\cross_ref.db"
db_scholar = r"C:\\scholar.db"
# Create crossref object
works = Works()

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

