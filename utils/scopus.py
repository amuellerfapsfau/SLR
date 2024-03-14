from pybliometrics.scopus import ScopusSearch, AbstractRetrieval
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from utils.utils import decompose_and_terms

MAX_BACKWARD_SEARCH_ITERATIONS = 3

def convert_search_string_to_scopus(search_string):
    # Split each OR conjunction separated by AND
    and_terms = decompose_and_terms(search_string)
    # replace '-' with NOT
    and_terms = [x.replace('-', 'NOT ') for x in and_terms]
    # TODO add support for other wildcards
    # loop through each term and add TITLE-ABS-KEY( and ) to each term
    and_terms = [f'TITLE-ABS-KEY({x})' for x in and_terms]
    # join the terms with AND
    search_string = ' AND '.join(and_terms)
    
    return search_string

# Search scopus
def search_scopus(query):
    search = ScopusSearch(query)
    return search.results

# Scopus abstract retrieval
def retrieve_scopus_abstracts_from_search_results(search_results_df, db_name, backward_search_iteration=0):
    # Get the abstracts from the search results
    abstracts = []
    eid_subject_areas_tuples = []
    eid_idxterms_tuples = []
    eid_authkeywords_tuples = []
    eid_references_tuples = []

    all_idxterms = []
    all_authkeywords = []
    all_references = []
    
    for eid in search_results_df['eid']:
        ab = AbstractRetrieval(eid, id_type='eid', view='FULL')
        subject_areas = ab.subject_areas
        eid_subject_areas_tuples.append((eid, subject_areas))
        eid_idxterms_tuples.append((eid, ab.idxterms))
        all_idxterms.extend(ab.idxterms if ab.idxterms else [])
        eid_authkeywords_tuples.append((eid, ab.authkeywords))
        all_authkeywords.extend(ab.authkeywords if ab.authkeywords else [])
        eid_references_tuples.append((eid, ab.references))
        all_references.extend([pd.DataFrame(ab.references)])

    # find all unique subject areas
    all_subject_areas = []
    for tup in eid_subject_areas_tuples:
        for area in tup[1]:
            if area not in all_subject_areas:
                all_subject_areas.append(area)
    # store all subject areas in sqlite
    store_scopus_results_in_sqlite(db_name, 'subject_areas', all_subject_areas)
    # create unique eid, subject_areas code tuples
    eid_subject_area_code_tuples = []
    for tup in eid_subject_areas_tuples:
        for area in tup[1]:
            eid_subject_area_code_tuples.append((tup[0], area.code))
    # create N:M relation between eid and subject areas and store in sqlite
    df = pd.DataFrame(eid_subject_area_code_tuples, columns=['eid', 'subject_areas_code'])
    store_scopus_results_in_sqlite(db_name, 'eid_subject_areas', df)

    # find unique idxterms
    all_idxterms = list(set(all_idxterms))
    # create dataframe for idxterms and store in sqlite
    df = pd.DataFrame(all_idxterms, columns=['idxterm'])
    store_scopus_results_in_sqlite(db_name, 'idxterms', df)
    # create unique eid, idxterms tuples
    eid_idxterm_tuples = []
    for tup in eid_idxterms_tuples:
        if tup[1] is not None:
            for idxterm in tup[1]:
                eid_idxterm_tuples.append((tup[0], idxterm))
        else:
            eid_idxterm_tuples.append((tup[0], None))
    # create N:M relation between eid and idxterms and store in sqlite # TODO wie bei subject areas
    df = pd.DataFrame(eid_idxterm_tuples, columns=['eid', 'idxterm'])
    store_scopus_results_in_sqlite(db_name, 'eid_idxterms', df)

    # find unique authkeywords
    all_authkeywords = list(set(all_authkeywords))
    # create dataframe for authkeywords and store in sqlite
    df = pd.DataFrame(all_authkeywords, columns=['authkeywords'])
    store_scopus_results_in_sqlite(db_name, 'authkeywords', df)
    # create unique eid, authkeywords tuples
    eid_authkeyword_tuples = []
    for tup in eid_authkeywords_tuples:
        if tup[1] is not None:
            for authkeyword in tup[1]:
                eid_authkeyword_tuples.append((tup[0], authkeyword))
        else:
            eid_authkeyword_tuples.append((tup[0], None))
    # create N:M relation between eid and authkeywords and store in sqlite
    df = pd.DataFrame(eid_authkeyword_tuples, columns=['eid', 'authkeywords'])

    # find unique references
    all_references = pd.concat(all_references, axis=0).drop_duplicates()
    if backward_search_iteration < MAX_BACKWARD_SEARCH_ITERATIONS:
        all_references['eid'] = '2-s2.0-' + all_references['id']
        all_references['backward_search_iteration'] = backward_search_iteration + 1
        store_scopus_results_in_sqlite(db_name, 'references', all_references, mode='update')
        # create unique eid, references eid tuples
        eid_list = []
        reference_eid_list = []
        for tup in eid_references_tuples:
            if tup[1] is not None:
                eid_list.extend([tup[0]]*len(tup[1]))
                for ref in tup[1]:              
                    reference_eid_list.extend(['2-s2.0-' + ref.id])
            else:
                eid_list.append(tup[0])
                reference_eid_list.append(None)
        # create N:M relation between eid and references and store in sqlite
        df = pd.DataFrame({'eid': eid_list, 'references_eid': reference_eid_list})
        # store in sqlite
        store_scopus_results_in_sqlite(db_name, 'eid_references', df)

    return abstracts


# Store scopus results in sqlite
def store_scopus_results_in_sqlite(db_name, table_name, results, mode='replace', id_column=None):
    if not isinstance(results, pd.DataFrame):
        # Convert the results to pandas dataframe
        results = pd.DataFrame(pd.DataFrame(results))
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

