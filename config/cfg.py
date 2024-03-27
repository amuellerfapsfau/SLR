essential_columns = [
    'title', 'author', 'date', 'keywords', 'subject areas', 'abstract'
]


scopus = {
    'field_mapping' : {
        'search_results': {
            'title': 'title',
            'identifier': 'eid',
            'doi': 'doi',
            'subtype': 'subtypeDescription',
            'publication_name': 'publicationName',
            'aggregation_type': 'aggregationType',
            'author': 'author_names',
            'country': 'affiliation_country',
            'date': 'coverDate',
            'keywords': 'authkeywords',
            'open_access': 'openaccess',
            'funded_by': 'fund_sponsor',
            'abstract': 'description',
            'cited_by_count': 'citedby_count'
        },
        'references': {
            'title': 'title',
            'identifier': 'eid',
            'doi': 'doi',
            'subtype': 'subtypeDescription', # MISSING
            'publication_name': 'sourcetitle', # CHECK
            'aggregation_type': 'aggregationType', # MISSING
            'author': 'authors',
            'country': 'affiliation_country', # MISSING
            'date': 'coverDate', # EMPTY, but year in 'publicationyear'
            'keywords': 'authkeywords', # MISSING
            'subject_areas': 'TODO', # TODO
            'open_access': 'openaccess', # MISSING
            'funded_by': 'fund_sponsor', # MISSING
            'abstract': 'description', # MISSING
            'cited_by_count': 'citedby_count' # MISSING
        }
    }
}

arxiv = {
    'field_mapping' : {
        'search_results': {
            'title': 'title', # available
            # 'identifier': 'eid',
            'doi': 'doi', # often empty
            # 'subtype': 'subtypeDescription',
            'publication_name': 'journal_ref', # TODO check if mapping correct
            # 'aggregation_type': 'aggregationType',
            'author': 'authors', # list of arxiv.Result.Author
            # 'country': 'affiliation_country',
            'date': 'published', # datetime.datetime
            # 'keywords': 'authkeywords',
            'subject_areas': 'categories', #  list of strings TODO need translation of strings (e.g. cs.LG -> Computer Science, Learning)
            # see also 'primary_category'
            'open_access': 'openaccess', # always True
            # 'funded_by': 'fund_sponsor',
            'abstract': 'summary', # check if correct and always complete
            # 'cited_by_count': 'citedby_count',
            'comments': 'comment', # often empty
            'url': 'entry_id', # available
            'full_paper_pdf': 'pdf_url' # available
        },
    },
    'category_taxonomy': {
        'db_name': r"C:\\Repositories\\_Data\SLR\\arxiv_category_taxonomy.db",
        'table_name': 'category_taxonomy'
    }
}

crossref = {
    'field_mapping' : {
        'search_results': {
            'title': 'title',
            'identifier': 'eid', # TODO: CHECK
            'doi': 'DOI',
            'subtype': 'type',
            'publication_name': 'short_container_title',
            'aggregation_type': 'container-title',
            'author': 'author', # dictionary
            'country': 'affiliation_country', # TODO parse from author[0]['affiliation']['name] using list of countries and regex
            'date': 'published', # TODO parse from date-parts -> published['date-parts'][0] [0]=year, [1]=month, [2]=day
            'keywords': 'authkeywords', # MISSING
            'subject_areas': 'subject',
            'open_access': 'openaccess', # MISSING
            'funded_by': 'funder', # TODO list of dicts, parse values from 'name
            'abstract': 'description', # MISSING
            'cited_by_count': 'is-referenced-by-count',
            'language': 'language'
        }, # TODO check how to map crossref (differentiation between search_results and references probably unnecessary)
        'references': {
            'title': 'title',
            'identifier': 'eid',
            'doi': 'DOI',
            'subtype': 'type', # MISSING
            'publication_name': 'short_container_title', # CHECK
            'aggregation_type': 'container', # MISSING
            'author': 'author',
            'country': 'affiliation_country', # TODO parse from author[0]['affiliation']['name] using list of countries and regex
            'date': 'published', # TODO parse from date-parts -> published['date-parts'][0] [0]=year, [1]=month, [2]=day
            'keywords': 'authkeywords', # MISSING
            'open_access': 'openaccess', # MISSING
            'funded_by': 'funder', # TODO list of dicts, parse values from 'name
            'abstract': 'description', # MISSING
            'cited_by_count': 'is-referenced-by-count', # MISSING
            'language': 'language'
        }
    }
}


semantic_scholar = {
    'field_mapping' : {
        'search_results': {
            'title': 'title', # correct
            'identifier': 'paperId', # correct
            'doi': 'externalIds', # dictionary TODO parse from key 'DOI'
            'subtype': 'publicationTypes', # correct, list of strings TODO
            'publication_name': 'journal', # correct (also conference name), same as 'venue'
            'aggregation_type': 'container-title',
            'author': 'authors', # list of dictionary (id, name) TODO parse name
            'country': 'affiliation_country', 
            'date': 'publicationDate', # correct TODO datetime
            'keywords': 'authkeywords', 
            'subject_areas': ['fieldsOfStudy', 's2FieldsOfStudy'], # correct
            'open_access': 'isOpenAccess', # correct
            'funded_by': 'funder', 
            'abstract': 'abstract', # correct
            'cited_by_count': 'citationCount', # correct
            'language': 'language',
            'citations': 'citations' # correct --> TODO use for forward search
        }, 
        'references': {
            'title': 'title', # correct
            'identifier': 'paperId', # correct
            'doi': 'externalIds', # dictionary TODO parse from key 'DOI'
            'subtype': 'publicationTypes', # correct, list of strings TODO
            'publication_name': 'journal', # correct (also conference name), same as 'venue'
            'aggregation_type': 'container',
            'author': 'author',
            'country': 'affiliation_country', 
            'date': 'publicationDate', # correct TODO datetime
            'keywords': 'authkeywords', 
            'open_access': 'isOpenAccess', # correct
            'funded_by': 'funder', 
            'abstract': 'description',
            'cited_by_count': 'citationCount', # correct 
            'language': 'language'
        }
    }
}

springer = {
}