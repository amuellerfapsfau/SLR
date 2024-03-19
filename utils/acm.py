import urllib.parse
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from utils.utils import setup_logger

logger = setup_logger('acm', r'.\\logs\\acm.log', level=logging.INFO)

def build_acm_search_url(query):
    title_query = f'Title:({query})'
    abstract_query = f'Abstract:({query})'
    keyword_query = f'Keyword:({query})'
    query = ' OR '.join([title_query, abstract_query, keyword_query])
    query = urllib.parse.quote(query)
    query = query.replace('%20', '+')
    query = f'https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&AllField={query}&expand=all&startPage=0&pageSize=50'
    return query

def scrape_acm_search_results(url):
    driver = webdriver.Firefox()
    driver.get(url)
    # classname searchbox 'search-result__xsl-body  items-results rlist--inline '
    search_results = driver.find_element(By.CLASS_NAME, 'search-result__xsl-body')
    # enthält die einzelnen Ergebnisse (classname 'search__item issue-item-container' )
    results = search_results.find_elements(By.CLASS_NAME, 'search__item')
    for result in results:
        doi = result.find_element(By.CLASS_NAME, 'issue-Item__checkbox').get_attribute('name')
        publication_type = result.find_element(By.CLASS_NAME, 'issue-heading').text
        date = result.find_element(By.CLASS_NAME, 'bookPubDate').get_attribute('data-title')
        title = result.find_element(By.CLASS_NAME, 'issue-item__title').text
        # try expand authors
        try:
            result.find_element(By.CLASS_NAME, 'count-list').find_element(By.TAG_NAME, 'button').click()
        except Exception as e:
            logger.error(f'Error clicking on expand-authors button: {e}')
        # get authors
        authors = result.find_element(By.CLASS_NAME, 'rlist--inline').find_elements(By.CLASS_NAME, 'hlFld-ContribAuthor')
        authors_list = []
        for author in authors:
            author_str = author.find_element(By.TAG_NAME, 'a').get_attribute('title')
            authors_list.append(author_str)
        # try get publication
        try:
            publication = result.find_element(By.CLASS_NAME, 'issue-item__detail').text
            publication_short = result.find_element(By.CLASS_NAME, 'issue-item__detail').find_element(By.TAG_NAME, 'a').get_attribute('title')
        except Exception as e:
            logger.error(f'Error getting publication: {e}')
            publication = None
            publication_short = None
        # try expand abstract and get abstract
        try:
            result.find_element(By.CLASS_NAME, 'highlights-holder').find_element(By.CLASS_NAME, 'accordion').click()
            abstract = result.find_element(By.CLASS_NAME, 'abstract-text').find_element(By.TAG_NAME, 'p').text
        except Exception as e:
            logger.error(f'Error getting abstract: {e}')
            abstract = None

    # input mit classname: 'issue-Item__checkbox' name enthält die DOI
    # div mit classname: 'issue-heading' enhält publication type (Article, Doctoral_thesis, ...)
    # div mit classname: 'bookPubDate simple-tooltip__block--b' --> data-title enthält das Datum in Form "Published: 04 December 2013"
    # href mit wert "/doi/{doi von oben}" (bei article) Inhalt von allen <span> tags zusammengehängt ergibt den Titel
    # bzw: das <a> tag / all <a> tags konkatentiert in node mit classname 'issue-item__title' (in einem span)
    # ul mit classname 'rlist--inline loa truncate-list trunc-done' enthält spans mit classname 'hlFld-ContribAuthor', welches ein <a> tag enthält dessen 'title' attribut den Autor enthält
    print('Finished')

# TODO CONTINUE HERE
# template from copilot
def open_acm_publication(doi):
    url = f'https://dl.acm.org/doi/{doi}'
    driver = webdriver.Firefox()
    driver.get(url)
    # check if we are redirected to a different page
    if 'doi' not in driver.current_url:
        # we are redirected
        # check if we are redirected to a login page
        if 'login' in driver.current_url:
            # we are redirected to a login page
            # try to login
            pass
        else:
            # we are redirected to a different page
            # check if we are redirected to a search page
            if 'search' in driver.current_url:
                # we are redirected to a search page
                # try to find the publication
                pass
            else:
                # we are redirected to a different page
                # try to find the publication
                pass
    else:
        # we are not redirected
        # we are on the publication page
        pass

# https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&AllField=Title%3A%28%28%22machine+learning%22+OR+%22deep+learning%22+OR+%22neural%3Fnetwork%22+OR+%22learn*+system%22+OR+%22virtual+metrology%22+OR+%22artificial+intelligence%22+OR+%22data+mining%22+OR+%22data+science%22+OR+%22big+data%22+OR+%22predictive+modeling%22+OR+%22predictive+analytics%22+OR+%22predictive+analysis%22+OR+%22predictive+algorithm%22+OR+%22predictive+model%22+OR+%22predictive+system%22+OR+%22predictive+method%22+OR+%22predictive+technique%22+OR+%22predictive+tool%22+OR+%22predictive+technology%22+OR+%22predictive+approach%22+OR+%22predictive+framework%22+OR+%22predictive+process%22+OR+%22predictive+application%22+OR+%22predictive+software%22+OR+%22predictive+hardware%22+OR+%22predictive+service%22+OR+%22predictive+product%22+OR+%22predictive+solution%22+OR+%22predictive+platform%22+OR+%22predictive+environment%22%29+AND+%28%22physical+vapor+depostion%22+OR+%22physical+vapour+depostion%22+OR+%22pvd%22+OR+%22chemical+vapor+depostion%22+OR+%22chemical+vapour+depostion%22+OR+%22CVD%22+OR+%22sputter%22+OR+%22evaporation%22+OR+%22ebeam%22+AND+-disease%29+AND+%28%22thin%3Ffilm%22+OR+%22coat*%22+OR+%22layer%22+OR+%22lamination%22%29+AND+%28%22semiconductor%22+OR+%22solar+cell%22+OR+%22photovoltaic%22+OR+%22reflectance%22+OR+%22reflective%22+OR+%22anti%3Freflective%22+OR+%22ophtalmic%22+OR+%22optical%22+OR+%22optoelectronic%22+OR+%22optical+filter%22+OR+%22optical+coating%22+OR+%22optical+film%22+OR+%22optical+layer%22+OR+%22optical+lamination%22+OR+%22optical+device%22+OR+%22optical+component%22+OR+%22optical+system%22+OR+%22optical+instrument%22+OR+%22optical+equipment%22+OR+%22optical+material%22+OR+%22optical+technology%22+OR+%22optical+process%22+OR+%22optical+product%22+OR+%22optical+application%22+OR+%22optical+service%22+OR+%22optical+solution%22+OR+%22optical+tool%22+OR+%22optical+technique%22+OR+%22optical+method%22+OR+%22optical+approach%22%29%29+OR+Abstract%3A%28%28%22machine+learning%22+OR+%22deep+learning%22+OR+%22neural%3Fnetwork%22+OR+%22learn*+system%22+OR+%22virtual+metrology%22+OR+%22artificial+intelligence%22+OR+%22data+mining%22+OR+%22data+science%22+OR+%22big+data%22+OR+%22predictive+modeling%22+OR+%22predictive+analytics%22+OR+%22predictive+analysis%22+OR+%22predictive+algorithm%22+OR+%22predictive+model%22+OR+%22predictive+system%22+OR+%22predictive+method%22+OR+%22predictive+technique%22+OR+%22predictive+tool%22+OR+%22predictive+technology%22+OR+%22predictive+approach%22+OR+%22predictive+framework%22+OR+%22predictive+process%22+OR+%22predictive+application%22+OR+%22predictive+software%22+OR+%22predictive+hardware%22+OR+%22predictive+service%22+OR+%22predictive+product%22+OR+%22predictive+solution%22+OR+%22predictive+platform%22+OR+%22predictive+environment%22%29+AND+%28%22physical+vapor+depostion%22+OR+%22physical+vapour+depostion%22+OR+%22pvd%22+OR+%22chemical+vapor+depostion%22+OR+%22chemical+vapour+depostion%22+OR+%22CVD%22+OR+%22sputter%22+OR+%22evaporation%22+OR+%22ebeam%22+AND+-disease%29+AND+%28%22thin%3Ffilm%22+OR+%22coat*%22+OR+%22layer%22+OR+%22lamination%22%29+AND+%28%22semiconductor%22+OR+%22solar+cell%22+OR+%22photovoltaic%22+OR+%22reflectance%22+OR+%22reflective%22+OR+%22anti%3Freflective%22+OR+%22ophtalmic%22+OR+%22optical%22+OR+%22optoelectronic%22+OR+%22optical+filter%22+OR+%22optical+coating%22+OR+%22optical+film%22+OR+%22optical+layer%22+OR+%22optical+lamination%22+OR+%22optical+device%22+OR+%22optical+component%22+OR+%22optical+system%22+OR+%22optical+instrument%22+OR+%22optical+equipment%22+OR+%22optical+material%22+OR+%22optical+technology%22+OR+%22optical+process%22+OR+%22optical+product%22+OR+%22optical+application%22+OR+%22optical+service%22+OR+%22optical+solution%22+OR+%22optical+tool%22+OR+%22optical+technique%22+OR+%22optical+method%22+OR+%22optical+approach%22%29%29+OR+Keyword%3A%28%28%22machine+learning%22+OR+%22deep+learning%22+OR+%22neural%3Fnetwork%22+OR+%22learn*+system%22+OR+%22virtual+metrology%22+OR+%22artificial+intelligence%22+OR+%22data+mining%22+OR+%22data+science%22+OR+%22big+data%22+OR+%22predictive+modeling%22+OR+%22predictive+analytics%22+OR+%22predictive+analysis%22+OR+%22predictive+algorithm%22+OR+%22predictive+model%22+OR+%22predictive+system%22+OR+%22predictive+method%22+OR+%22predictive+technique%22+OR+%22predictive+tool%22+OR+%22predictive+technology%22+OR+%22predictive+approach%22+OR+%22predictive+framework%22+OR+%22predictive+process%22+OR+%22predictive+application%22+OR+%22predictive+software%22+OR+%22predictive+hardware%22+OR+%22predictive+service%22+OR+%22predictive+product%22+OR+%22predictive+solution%22+OR+%22predictive+platform%22+OR+%22predictive+environment%22%29+AND+%28%22physical+vapor+depostion%22+OR+%22physical+vapour+depostion%22+OR+%22pvd%22+OR+%22chemical+vapor+depostion%22+OR+%22chemical+vapour+depostion%22+OR+%22CVD%22+OR+%22sputter%22+OR+%22evaporation%22+OR+%22ebeam%22+AND+-disease%29+AND+%28%22thin%3Ffilm%22+OR+%22coat*%22+OR+%22layer%22+OR+%22lamination%22%29+AND+%28%22semiconductor%22+OR+%22solar+cell%22+OR+%22photovoltaic%22+OR+%22reflectance%22+OR+%22reflective%22+OR+%22anti%3Freflective%22+OR+%22ophtalmic%22+OR+%22optical%22+OR+%22optoelectronic%22+OR+%22optical+filter%22+OR+%22optical+coating%22+OR+%22optical+film%22+OR+%22optical+layer%22+OR+%22optical+lamination%22+OR+%22optical+device%22+OR+%22optical+component%22+OR+%22optical+system%22+OR+%22optical+instrument%22+OR+%22optical+equipment%22+OR+%22optical+material%22+OR+%22optical+technology%22+OR+%22optical+process%22+OR+%22optical+product%22+OR+%22optical+application%22+OR+%22optical+service%22+OR+%22optical+solution%22+OR+%22optical+tool%22+OR+%22optical+technique%22+OR+%22optical+method%22+OR+%22optical+approach%22%29%29&pageSize=20%3FstartPage%3D1&pageSize=20&expand=all

# https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&AllField=
# Title%3A%28   %28%22machine+learning%22+OR+%22deep+learning%22+OR+%22neural%3Fnetwork%22+OR+%22learn*+system%22+OR+%22virtual+metrology%22+OR+%22artificial+intelligence%22+
# OR+%22data+mining%22+OR+%22data+science%22+OR+%22big+data%22+OR+%22predictive+modeling%22+OR+%22predictive+analytics%22+OR+%22predictive+analysis%22+OR+%22predictive+algorithm%22
# +OR+%22predictive+model%22+OR+%22predictive+system%22+OR+%22predictive+method%22+OR+%22predictive+technique%22+OR+%22predictive+tool%22+OR+%22predictive+technology%22+OR+%22
# predictive+approach%22+OR+%22predictive+framework%22+OR+%22predictive+process%22+OR+%22predictive+application%22+OR+%22predictive+software%22+OR+%22predictive+hardware%22+OR+
# %22predictive+service%22+OR+%22predictive+product%22+OR+%22predictive+solution%22+OR+%22predictive+platform%22+OR+%22predictive+environment%22%29+AND+%28%22
# physical+vapor+depostion%22+OR+%22physical+vapour+depostion%22+OR+%22pvd%22+OR+%22chemical+vapor+depostion%22+OR+%22chemical+vapour+depostion%22+OR+%22CVD%22+OR+%22
# sputter%22+OR+%22evaporation%22+OR+%22ebeam%22+AND+-disease%29+AND+%28%22thin%3Ffilm%22+OR+%22coat*%22+OR+%22layer%22+OR+%22lamination%22%29+AND+%28%22semiconductor%22+OR+%22
# solar+cell%22+OR+%22photovoltaic%22+OR+%22reflectance%22+OR+%22reflective%22+OR+%22anti%3Freflective%22+OR+%22ophtalmic%22+OR+%22optical%22+OR+%22optoelectronic%22+OR+%22
# optical+filter%22+OR+%22optical+coating%22+OR+%22optical+film%22+OR+%22optical+layer%22+OR+%22optical+lamination%22+OR+%22optical+device%22+OR+%22optical+component%22+OR+%22
# optical+system%22+OR+%22optical+instrument%22+OR+%22optical+equipment%22+OR+%22optical+material%22+OR+%22optical+technology%22+OR+%22optical+process%22+OR+%22optical+product%22
# +OR+%22optical+application%22+OR+%22optical+service%22+OR+%22optical+solution%22+OR+%22optical+tool%22+OR+%22optical+technique%22+OR+%22optical+method%22+OR+%22optical+
# approach%22%29   %29+OR+Abstract%3A%28%28%22machine+learning%22+OR+%22deep+learning%22+OR+%22neural%3Fnetwork%22+OR+%22learn*+system%22+OR+%22virtual+metrology%22+OR+%22
# artificial+intelligence%22+OR+%22data+mining%22+OR+%22data+science%22+OR+%22big+data%22+OR+%22predictive+modeling%22+OR+%22predictive+analytics%22+OR+%22predictive+analysis%22
# +OR+%22predictive+algorithm%22+OR+%22predictive+model%22+OR+%22predictive+system%22+OR+%22predictive+method%22+OR+%22predictive+technique%22+OR+%22predictive+tool%22+OR+%22
# predictive+technology%22+OR+%22predictive+approach%22+OR+%22predictive+framework%22+OR+%22predictive+process%22+OR+%22predictive+application%22+OR+%22predictive+software%22+OR+
# %22predictive+hardware%22+OR+%22predictive+service%22+OR+%22predictive+product%22+OR+%22predictive+solution%22+OR+%22predictive+platform%22+OR+%22predictive+environment%22%29+
# AND+%28%22physical+vapor+depostion%22+OR+%22physical+vapour+depostion%22+OR+%22pvd%22+OR+%22chemical+vapor+depostion%22+OR+%22chemical+vapour+depostion%22+OR+%22CVD%22+OR+
# %22sputter%22+OR+%22evaporation%22+OR+%22ebeam%22+AND+-disease%29+AND+%28%22thin%3Ffilm%22+OR+%22coat*%22+OR+%22layer%22+OR+%22lamination%22%29+AND+%28%22semiconductor%22+OR+%22
# solar+cell%22+OR+%22photovoltaic%22+OR+%22reflectance%22+OR+%22reflective%22+OR+%22anti%3Freflective%22+OR+%22ophtalmic%22+OR+%22optical%22+OR+%22optoelectronic%22+OR+%22optical
# +filter%22+OR+%22optical+coating%22+OR+%22optical+film%22+OR+%22optical+layer%22+OR+%22optical+lamination%22+OR+%22optical+device%22+OR+%22optical+component%22+OR+%22optical
# +system%22+OR+%22optical+instrument%22+OR+%22optical+equipment%22+OR+%22optical+material%22+OR+%22optical+technology%22+OR+%22optical+process%22+OR+%22optical+product%22+OR+%22
# optical+application%22+OR+%22optical+service%22+OR+%22optical+solution%22+OR+%22optical+tool%22+OR+%22optical+technique%22+OR+%22optical+method%22+OR+%22optical+approach%22%29%29
# +OR+Keyword%3A%28%28%22machine+learning%22+OR+%22deep+learning%22+OR+%22neural%3Fnetwork%22+OR+%22learn*+system%22+OR+%22virtual+metrology%22+OR+%22artificial+intelligence%22+
# OR+%22data+mining%22+OR+%22data+science%22+OR+%22big+data%22+OR+%22predictive+modeling%22+OR+%22predictive+analytics%22+OR+%22predictive+analysis%22+OR+%22predictive+algorithm%22
# +OR+%22predictive+model%22+OR+%22predictive+system%22+OR+%22predictive+method%22+OR+%22predictive+technique%22+OR+%22predictive+tool%22+OR+%22predictive+technology%22+OR+%22
# predictive+approach%22+OR+%22predictive+framework%22+OR+%22predictive+process%22+OR+%22predictive+application%22+OR+%22predictive+software%22+OR+%22predictive+hardware%22+OR+%22
# predictive+service%22+OR+%22predictive+product%22+OR+%22predictive+solution%22+OR+%22predictive+platform%22+OR+%22predictive+environment%22%29+AND+%28%22physical+vapor+depostion
# %22+OR+%22physical+vapour+depostion%22+OR+%22pvd%22+OR+%22chemical+vapor+depostion%22+OR+%22chemical+vapour+depostion%22+OR+%22CVD%22+OR+%22sputter%22+OR+%22evaporation%22+OR+
# %22ebeam%22+AND+-disease%29+AND+%28%22thin%3Ffilm%22+OR+%22coat*%22+OR+%22layer%22+OR+%22lamination%22%29+AND+%28%22semiconductor%22+OR+%22solar+cell%22+OR+%22photovoltaic%22+
# OR+%22reflectance%22+OR+%22reflective%22+OR+%22anti%3Freflective%22+OR+%22ophtalmic%22+OR+%22optical%22+OR+%22optoelectronic%22+OR+%22optical+filter%22+OR+%22optical+coating%22
# +OR+%22optical+film%22+OR+%22optical+layer%22+OR+%22optical+lamination%22+OR+%22optical+device%22+OR+%22optical+component%22+OR+%22optical+system%22+OR+%22optical+instrument%22
# +OR+%22optical+equipment%22+OR+%22optical+material%22+OR+%22optical+technology%22+OR+%22optical+process%22+OR+%22optical+product%22+OR+%22optical+application%22+OR+%22optical
# +service%22+OR+%22optical+solution%22+OR+%22optical+tool%22+OR+%22optical+technique%22+OR+%22optical+method%22+OR+%22optical+approach%22%29%29
# &pageSize=20%3FstartPage%3D1&pageSize=20&expand=all