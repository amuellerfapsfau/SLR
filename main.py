from scholarly import scholarly
from scholarly import ProxyGenerator
from crossref.restful import Works
from utils.utils import store_dicts_in_sqlite_with_pandas

# Setup a proxy generator
pg = ProxyGenerator()
pg.FreeProxies()
scholarly.use_proxy(pg)

# Define a search
# Define query
methodology_substring = '"machine learning" OR "deep learning" OR "neural?network" OR "learn* system" OR "virtual metrology" OR "artificial intelligence" OR "data mining" OR "data science" OR "big data" OR "predictive modeling" OR "predictive analytics" OR "predictive analysis" OR "predictive algorithm" OR "predictive model" OR "predictive system" OR "predictive method" OR "predictive technique" OR "predictive tool" OR "predictive technology" OR "predictive approach" OR "predictive framework" OR "predictive process" OR "predictive application" OR "predictive software" OR "predictive hardware" OR "predictive service" OR "predictive product" OR "predictive solution" OR "predictive platform" OR "predictive environment'
process_substring = '("physical vapor depostion" OR "physical vapour depostion" OR "pvd" OR "chemical vapor depostion" OR "chemical vapour depostion" OR "CVD" OR "sputter" OR "evaporation" OR "ebeam") AND -disease'
product_substring = '"thin?film" OR "coat*" OR "layer" OR "lamination"'
application_substring = '"semiconductor" OR "solar cell" OR "photovoltaic" OR "reflectance" OR "reflective" OR "anti?reflective" OR "ophtalmic" OR "optical" OR "optoelectronic" OR "optical filter" OR "optical coating" OR "optical film" OR "optical layer" OR "optical lamination" OR "optical device" OR "optical component" OR "optical system" OR "optical instrument" OR "optical equipment" OR "optical material" OR "optical technology" OR "optical process" OR "optical product" OR "optical application" OR "optical service" OR "optical solution" OR "optical tool" OR "optical technique" OR "optical method" OR "optical approach"'
query = f"({methodology_substring}) AND ({process_substring}) AND ({product_substring}) AND ({application_substring})"

# Define search parameters
include_patens = False
include_citations = True
year_low = 2010
year_high = None
sort_by = 'relevance' # 'relevance', 'date', 'citations'

db = r"C:\\cross_ref.db"
# Create crossref object
works = Works()

# cross_ref_results_list = []
# cross_ref_results = works.query(bibliographic=query)
# for item in cross_ref_results.filter(from_pub_date=year_low):
#     cross_ref_results_list.append(item)
# store_dicts_in_sqlite_with_pandas(db, 'crossref', cross_ref_results)

# Search
search_query_results = scholarly.search_pubs(query=query,
                                            patents=include_patens,
                                            citations=include_citations,
                                            year_low=year_low,
                                            year_high=year_high,
                                            sort_by=sort_by)

results_scholar = []
results_crossref = []
results_crossref_filtered = []

for pub in search_query_results:
    scholarly.pprint(pub)
    pub = scholarly.fill(pub)
    title = pub['bib']['title']
    year = pub['bib']['pub_year']
    bibliobgraphic = f'{title} {year}'
    author = pub['bib']['author']
    if isinstance(author, list):
        author = ', '.join(author)
    # Get DOI using crossref
    cref_res = works.query(bibliographic=bibliobgraphic, author=author)

    for item in cref_res:
        print(item)
    # if len(cref_res) > 1:
    #     print('More than one result')
    # else:
    #     cref_res = cref_res[0]
    # doi = cref_res['DOI']

    pub = scholarly.fill(pub)
    scholarly.pprint(pub)

