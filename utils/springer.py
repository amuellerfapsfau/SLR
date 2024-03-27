import urllib.parse
import requests
import logging
import re
from ratelimiter import RateLimiter
from sqlalchemy import create_engine
from sqlalchemy.engine import reflection
from utils.utils import setup_logger
from config.keys import apikey

logger = setup_logger('springer', r'.\\logs\\springer.log', level=logging.INFO)

def build_springer_query(query, start=1, page_length=9999999):
    # https://api.springernature.com/metadata/json?api_key=2d28a6e20dd40a588a79bff2a0b0c082&q=%28%22machine%20learning%22%20OR%20%22deep%20learning%22%20
    # OR%20%22neural%3Fnetwork%22%20OR%20%22learn%2A%20system%22%20OR%20%22virtual%20metrology%22%20OR%20%22artificial%20intelligence%22%20OR%20%22data%20
    # mining%22%20OR%20%22data%20science%22%20OR%20%22big%20data%22%20OR%20predictive%2A%29%20AND%20%28%22coat%2A%20machine%22%20OR%20%22physical%20vapor
    # %20deposition%22%20OR%20%22physical%20vapour%20deposition%22%20OR%20%22pvd%22%20OR%20%22chemical%20vapor%20deposition%22%20OR%20%22chemical%20vapour
    # %20deposition%22%20OR%20%22CVD%22%20OR%20%22sputter%2A%22%20OR%20%22evaporation%22%20OR%20%22ebeam%22%20AND%20-disease%29%20AND%20%28%22thin%3Ffilm
    # %22%20OR%20%22coat%2A%22%20OR%20%22lamination%22%29%20AND%20%28%22lens%2A%22%20OR%20%22reflectance%22%20OR%20%22reflective%22%20OR%20%22anti%3
    # Freflective%22%20OR%20%22ophtalmic%22%20OR%20%22optoelectronic%22%20OR%20%22optical%20filter%22%20OR%20%22optical%20coating%22%20OR%20%22optical%20
    # film%22%29&s=1&p=9999999
    # query = f"https://api.springernature.com/metadata/json?api_key={apikey['springer']}&q={query}&s={s}&p={p}"
    query = f"https://api.springernature.com/metadata/json?api_key={apikey['springer']}&q={urllib.parse.quote(query)}&s={start}&p={page_length}"
    return query

@RateLimiter(max_calls=150, period=60)
def get_results(url):
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def get_term_title_keyword_results(search_string):
    search_term_results_dict = {}
    terms = search_string.strip(' ()').split(') AND (')

    for term in terms:
        # term = term.strip(' ()') #term = term + ' AND -("test eins") OR -"test zwei"'
        # find negations --> soll: -(title:sometitle)
        indices_neg = [m.start() for m in re.finditer('-', term)]
        offset = 0
        title_term = term
        for index in indices_neg:
            if title_term[index+offset+1] == '(':
                title_term = title_term[:index+offset+2] + 'title:' + title_term[index+offset+2:]
                offset+=6
            elif title_term[index+offset+1] == '"': # -"some title" --> -(title:"some title")
                closing_bracket_index = title_term.find('"', index+offset+2)
                title_term = title_term[:index+offset+1] + '(title:' + title_term[index+offset+1:closing_bracket_index+1] + ')' + title_term[closing_bracket_index+1:]
                offset+=8
            else: # -sometitle --> -(title:sometitle)
                closing_space_index = title_term.find(' ', index+offset+1)
                if closing_space_index == -1:
                    closing_space_index = len(title_term)
                title_term = title_term[:index+offset+1] + '(title:' + title_term[index+offset+1:closing_space_index] + ')' + title_term[closing_space_index:]
                offset+=8
        title_term = f"title:{title_term.replace(' OR ', ' OR title:').replace(' AND ', ' AND title:').replace('title:-', '-')}"
        keyword_term = title_term.replace('title:', 'keyword:')
        search_term = f'({title_term}) OR ({keyword_term})'
        search_term_results = get_query_results(search_term)
        search_term_results_dict[term] = search_term_results
    return search_term_results_dict


def get_title_keyword_results(search_string):
    final_title_keyword_search_string = []
    terms = search_string.split(') AND (')
    for term in terms:
        term = term.strip(' ()') #term = term + ' AND -("test eins") OR -"test zwei"'
        # find negations --> soll: -(title:sometitle)
        indices_neg = [m.start() for m in re.finditer('-', term)]
        offset = 0
        for index in indices_neg:
            if term[index+offset+1] == '(':
                term = term[:index+offset+2] + 'title:' + term[index+offset+2:]
                offset+=6
            elif term[index+offset+1] == '"': # -"some title" --> -(title:"some title")
                closing_bracket_index = term.find('"', index+offset+2)
                term = term[:index+offset+1] + '(title:' + term[index+offset+1:closing_bracket_index+1] + ')' + term[closing_bracket_index+1:]
                offset+=8
            else: # -sometitle --> -(title:sometitle)
                closing_space_index = term.find(' ', index+offset+1)
                if closing_space_index == -1:
                    closing_space_index = len(term)
                term = term[:index+offset+1] + '(title:' + term[index+offset+1:closing_space_index] + ')' + term[closing_space_index:]
                offset+=8
        title_term = f"title:{term.replace(' OR ', ' OR title:').replace(' AND ', ' AND title:').replace('title:-', '-')}"
        keyword_term = title_term.replace('title:', 'keyword:')
        search_term = f'({title_term}) OR ({keyword_term})'
        final_title_keyword_search_string.append(search_term)
    final_title_keyword_search_string = ') AND ('.join(final_title_keyword_search_string)
    final_title_keyword_search_string = f'({final_title_keyword_search_string})'
    search_term_results = get_query_results(final_title_keyword_search_string)
    return search_term_results


def get_query_results(search_term):
    results = []
    # get first page and determine max pagelength, number of required requests
    json_results = get_results(build_springer_query(search_term))
    results.extend(json_results['records'])
    hits = int(json_results['result'][0]['total'])
    page_length = json_results['result'][0]['pageLength']
    start = int(json_results['result'][0]['start'])
    while len(results) < hits:
        start += 1
        json_results = get_results(build_springer_query(search_term, start, page_length))
        if json_results:
            results.extend(json_results['records'])
        else:
            logger.error(f'No results for {search_term} at start {start}')
        # testweise
        if start == 2:
            break
    return results

def get_all_results(search_term):
    results = []
    # get first page and determine max pagelength, number of required requests
    json_results = get_results(build_springer_query(search_term))
    results.extend(json_results['records'])
    hits = int(json_results['result'][0]['total'])
    page_length = json_results['result'][0]['pageLength']
    start = int(json_results['result'][0]['start'])
    while len(results) < hits:
        start += 1
        json_results = get_results(build_springer_query(search_term, start, page_length))
        if json_results:
            results.extend(json_results['records'])
        else:
            logger.error(f'No results for {search_term} at start {start}')
        # testweise
        if start == 2:
            break
    return results

def get_negative_lookahead_terms(term):
    if ' AND ' in term:
        logger.error('AND not supported in negation')
        return []
    if ' OR ' in term:
        terms = term.split(' OR ')
    else:
        terms = [term]
    
    return terms

def convert_search_string_to_regex(search_string):
    # terms = search_string.strip(' ()').split(') AND (')
    dict_keys = search_string.strip(' ()').split(') AND (')
    # search negations
    regex_expressions_dict = {}
    terms = search_string.strip(' ()').replace('"', '').replace('?', '.') .split(') AND (')
    for i, term in enumerate(terms):
        # term = term.strip(' ()') #term = term + ' AND -("test eins") OR -"test zwei"'
        # find negations --> soll: -(title:sometitle)
        indices_neg = [m.start() for m in re.finditer('-', term)]
        neg_term_slices = []
        neg_terms = []
        for index in indices_neg:
            if term[index+1] == '(':
                closing_bracket_index = term.find(')', index+2)
                neg_term = term[index+2:closing_bracket_index]
                neg_terms.extend(get_negative_lookahead_terms(neg_term))
                neg_term_slices.append((index, closing_bracket_index))
            else: # -sometitle --> -(title:sometitle)
                next_and = term.find(' AND ', index+1)
                next_or = term.find(' OR ', index+1)
                last_char = len(term)
                if next_and == -1 and next_or == -1:
                    end = last_char
                elif next_and == -1:
                    end = next_or
                else: # next_or == -1:
                    end = next_and
                neg_terms.extend(get_negative_lookahead_terms(term[index+1:end]))
                neg_term_slices.append((index, end))
        if neg_terms:
            neg_lookahead = f'^(?!.*({"|".join(neg_terms)}))'
            neg_term_slices = sorted(neg_term_slices, key=lambda x: x[0], reverse=True)
            for start, end in neg_term_slices:
                term = term[:start].rstrip(' ').removesuffix('AND').removesuffix('OR') + term[end:]
            term = term.strip(' ')
        else:
            neg_lookahead = ''
        # create capture group for each term
        term = term.replace(' OR ', '|').replace(' AND ', '|')
        term = f'{neg_lookahead}.*({term}).*'
        regex_expressions_dict[dict_keys[i]] = term
                
    return regex_expressions_dict


def combine_results_to_TITLE_ABS_KEY(all_fields_results, title_keyword_results, terms_title_keyword_results_dict, terms_regex_dict):
    # title_keywords_result are part of total results
    title_abs_key_results = title_keyword_results
    terms_abstract_results_dict = {term: [] for term in terms_regex_dict.keys()}
    for term, regex in terms_regex_dict.items():
        for all_fields_res in all_fields_results:
            if not 'abstract' in all_fields_res:
                continue
            if re.match(regex, all_fields_res['abstract'], re.IGNORECASE):
                terms_abstract_results_dict[term].append(all_fields_res)
                # TODO überprüfen --> lens* ist das problem
                # .*(lens.*|reflectance|reflective|anti.reflective|ophtalmic|optoelectronic|optical filter|optical coating|optical film).*
                # Real-time monitoring lenses of students’ classroom engagement level is of paramount importance in modern education. Facial expression recognition has been extensively explored in various studies to achieve this goal. However, conventional models often grapple with a high number of parameters and substantial computational costs, limiting their practicality in real-time applications and real-world scenarios. To address this limitation, this paper proposes “Light_Fer,” a lightweight model designed to attain high accuracy while reducing parameters. Light_Fer’s novelty lies in the integration of depthwise separable convolution, group convolution, and inverted bottleneck structure. These techniques optimize the models’ architecture, resulting in superior accuracy with fewer parameters. Experimental results demonstrate that Light_Fer, with just 0.23M parameters, achieves remarkable accuracies of 87.81% and 88.20% on FERPLUS and RAF-DB datasets, respectively. Furthermore, by establishing a correlation between facial expressions and students’ engagement levels, we extend the application of Light_Fer to real-time detection and monitoring of students’ engagement during classroom activities. In conclusion, the proposed Light_Fer model, with its lightweight design and enhanced accuracy, offers a promising solution for real-time student engagement monitoring through facial expression recognition.
    # combine abstract results with title_keyword_results
    for res in all_fields_results:
        if res in title_keyword_results:
            logger.info(f'Found {res} in title_keyword_results')
            continue
        found = True
        for term in terms_abstract_results_dict.keys():
            if not (res in terms_title_keyword_results_dict[term] or res in terms_abstract_results_dict[term]):
                logger.info(f'{res} not found in "{term}"')
                found = False
                break
        if found:
            logger.info(f'Found {res} using abstract')
            title_abs_key_results.append(res)
    # for result in results:
    #     result['title'] = result['title'] + ' ' + result['abstract'] + ' ' + result['keyword']
    # return results

# (title:"coat* machine" OR title:"physical vapor deposition" OR title:"physical vapour deposition" OR title:"pvd" OR title:"chemical vapor deposition" OR title:"chemical vapour deposition" OR title:"CVD" OR title:"sputter*" OR title:"evaporation" OR title:"ebeam" AND title:-disease) AND ("thin?film" OR title:"coat*" OR title:"lamination") AND ("lens*" OR title:"reflectance" OR title:"reflective" OR title:"anti?reflective" OR title:"ophtalmic" OR title:"optoelectronic" OR title:"optical filter" OR title:"optical coating" OR title:"optical film") AND (title:"machine learning" OR title:"deep learning" OR title:"neural?network" OR title:"learn* system" OR title:"virtual metrology" OR title:"artificial intelligence" OR title:"data mining" OR title:"data science" OR title:"big data" OR title:predictive*)
# (keyword:"coat* machine" OR keyword:"physical vapor deposition" OR keyword:"physical vapour deposition" OR keyword:"pvd" OR keyword:"chemical vapor deposition" OR keyword:"chemical vapour deposition" OR keyword:"CVD" OR keyword:"sputter*" OR keyword:"evaporation" OR keyword:"ebeam" AND -"cardiovascular disease") AND ("thin?film" OR keyword:"coat*" OR keyword:"lamination") AND ("lens*" OR keyword:"reflectance" OR keyword:"reflective" OR keyword:"anti?reflective" OR keyword:"ophtalmic" OR keyword:"optoelectronic" OR keyword:"optical filter" OR keyword:"optical coating" OR keyword:"optical film") AND (keyword:"machine learning" OR keyword:"deep learning" OR keyword:"neural?network" OR keyword:"learn* system" OR keyword:"virtual metrology" OR keyword:"artificial intelligence" OR keyword:"data mining" OR keyword:"data science" OR keyword:"big data" OR keyword:predictive*)