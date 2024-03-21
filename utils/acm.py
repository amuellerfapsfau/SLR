import urllib.parse
import logging
from dataclasses import dataclass
from typing import List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from utils.utils import setup_logger


@dataclass
class Reference_Item:
    authors: List[str] = None
    year: int = None
    title: str = None
    publication: str = None
    volume: str = None
    issue: str = None
    pub_date: str = None
    doi: str = None

@dataclass
class ACM_Item:
    doi: str = None
    publication_type: str = None
    date: str = None
    title: str = None
    authors: List[str] = None
    publication: str = None
    publication_short: str = None
    abstract: str = None
    author_tags: List[str] = None
    cited_by: List[str] = None


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
    # reject cookies
    decline_cookies(driver)
    # get search results box
    search_results = driver.find_element(By.CLASS_NAME, 'search-result__xsl-body')
    # search results list
    results = search_results.find_elements(By.CLASS_NAME, 'search__item')
    search_results_list = []
    for result in results:
        acm_item = ACM_Item()
        try:
            acm_item.doi = result.find_element(By.CLASS_NAME, 'issue-Item__checkbox').get_attribute('name')
        except Exception as e:
            logger.error(f'Error getting doi: {e}')
        try:
            acm_item.publication_type = result.find_element(By.CLASS_NAME, 'issue-heading').text
        except Exception as e:
            logger.error(f'Error getting publication type: {e}')
        try:
            acm_item.date = result.find_element(By.CLASS_NAME, 'bookPubDate').get_attribute('data-title') # TODO acm_item.date.split(':')[1].strip(' ')
        except Exception as e:
            logger.error(f'Error getting date: {e}')
        try:
            acm_item.title = result.find_element(By.CLASS_NAME, 'issue-item__title').text
        except Exception as e:
            logger.error(f'Error getting title: {e}')
        
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
            if author_str not in authors_list:
                authors_list.append(author_str)
        acm_item.authors = authors_list
        # try get publication
        try:
            acm_item.publication = result.find_element(By.CLASS_NAME, 'issue-item__detail').text
            acm_item.publication_short = result.find_element(By.CLASS_NAME, 'issue-item__detail').find_element(By.TAG_NAME, 'a').get_attribute('title')
        except Exception as e:
            logger.error(f'Error getting publication: {e}')
        # try expand abstract and get abstract
        try:
            # wait = WebDriverWait(driver, 10)
            accordion = result.find_element(By.CLASS_NAME, 'highlights-holder').find_element(By.CLASS_NAME, 'accordion')
            # accordion = wait.until(EC.element_to_be_clickable(accordion))
            accordion.click()
            acm_item.abstract = result.find_element(By.CLASS_NAME, 'abstract-text').find_element(By.TAG_NAME, 'p').text
        except Exception as e:
            logger.error(f'Error getting abstract: {e}')
        # open publication in new window and add information to acm_item
        open_publication_page(result, acm_item)
        # open publication in new tab
        result.find_element(By.CLASS_NAME, 'issue-item__title').find_element(By.TAG_NAME, 'a').send_keys(Keys.CONTROL + 't')

    # input mit classname: 'issue-Item__checkbox' name enthält die DOI
    # div mit classname: 'issue-heading' enhält publication type (Article, Doctoral_thesis, ...)
    # div mit classname: 'bookPubDate simple-tooltip__block--b' --> data-title enthält das Datum in Form "Published: 04 December 2013"
    # href mit wert "/doi/{doi von oben}" (bei article) Inhalt von allen <span> tags zusammengehängt ergibt den Titel
    # bzw: das <a> tag / all <a> tags konkatentiert in node mit classname 'issue-item__title' (in einem span)
    # ul mit classname 'rlist--inline loa truncate-list trunc-done' enthält spans mit classname 'hlFld-ContribAuthor', welches ein <a> tag enthält dessen 'title' attribut den Autor enthält
    print('Finished')

def decline_cookies(driver):
    # decline all cookies
    try:
        driver.find_element(By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll').click()
    except Exception as e:
        logger.error(f'Error declining cookies: {e}')


def open_publication_page(result_box, item: ACM_Item):
    # conference paper
    try:
        pub_link = result_box.find_element(By.CLASS_NAME, 'issue-item__title').find_element(By.TAG_NAME, 'a').get_attribute('href')
        driver = webdriver.Firefox()
        driver.get(pub_link)
        # reject cookies
        decline_cookies(driver)
        driver.find_element(By.CLASS_NAME, 'loa__link').click()
        slide_content = driver.find_element(By.CLASS_NAME, 'w-slide__content')
        # open side bar
        slide_content.find_element(By.ID, 'pill-information__contentcon').click()
        author_tags = slide_content.find_element(By.CLASS_NAME, 'tags-widget').find_elements(By.TAG_NAME, 'li')
        author_tags_list = []
        for author_tag in author_tags:
            author_tags_list.append(author_tag.find_element(By.CLASS_NAME, 'badge-type').get_attribute('title'))
        item.author_tags = author_tags_list
        # close side bar
        driver.find_element(By.CLASS_NAME, 'w-slide__back').click()
        # open cited by in new window
        citedby_url = driver.find_element(By.ID, 'downloadAllMain').get_attribute('href')
        cited_by_list = open_cited_by_page(citedby_url)
        item.cited_by = cited_by_list
    except Exception as e:
        logger.error(f'Error getting publication link: {e}')
        pub_link = None
    # TODO doctoral thesis
    if not pub_link:
        try:
            pub_link = result_box.find_element(By.CLASS_NAME, 'issue-item__title').find_element(By.TAG_NAME, 'a').get_attribute('href')
        except Exception as e:
            logger.error(f'Error getting publication link: {e}')
            pub_link = None
    # TODO add more publication types
    if not pub_link:
        driver = webdriver.Firefox()
        driver.get(pub_link)
        

def open_cited_by_page(url):
    driver = webdriver.Firefox()
    driver.get(url)
    # reject cookies
    decline_cookies(driver)
    ref_items = driver.find_element(By.CLASS_NAME, 'references__item')
    ref_item_list = []
    if isinstance(ref_items, webdriver.remote.webelement.WebElement):
        ref_items = [ref_items]
    for ref_item in ref_items:
        ref_item_list.append(parse_reference_item(ref_item))   
    # close
    driver.close()
    return ref_item_list

def parse_reference_item(ref_item):
    result = Reference_Item()
    try:
        authors = ref_item.find_element(By.CLASS_NAME, 'references__authors').text
        authors_list = [author.strip() for author in authors.replace(' and ', ',').split(',')]
        result.authors = authors_list
    except Exception as e:
        logger.error(f'Error getting authors: {e}')
    try:
        year = ref_item.find_element(By.CLASS_NAME, 'pub-year').text.strip('().')
        result.year = year
    except Exception as e:
        logger.error(f'Error getting year: {e}')
    try:
        title = ref_item.find_element(By.CLASS_NAME, 'references__article-title').text
        result.title = title
    except Exception as e:
        logger.error(f'Error getting title: {e}')
    try:
        publication = ref_item.find_element(By.CLASS_NAME, 'references__source').text
        result.publication = publication
    except Exception as e:
        logger.error(f'Error getting publication: {e}')
    try:
        volume = ref_item.find_element(By.CLASS_NAME, 'volume').text
        result.volume = volume
    except Exception as e:
        logger.error(f'Error getting volume: {e}')
    try:
        issue = ref_item.find_element(By.CLASS_NAME, 'issue').text
        result.issue = issue
    except Exception as e:
        logger.error(f'Error getting issue: {e}')
    try:
        pub_date = ref_item.find_element(By.CLASS_NAME, 'pub-date').text
        pub_date = pub_date.split(':')[1].strip(' ')
        result.pub_date = pub_date
    except Exception as e:
        logger.error(f'Error getting publication date: {e}')
    try:
        doi = ref_item.find_element(By.CLASS_NAME, 'link').get_attribute('href')
        if 'doi.org' in doi:
            doi = doi.split('doi.org/')[1]
        result.doi = doi
    except Exception as e:
        logger.error(f'Error getting doi: {e}')

    return result

# TODO CONTINUE HERE
# template from copilot
def open_acm_publication(doi):
    url = f'https://dl.acm.org/doi/{doi}'
    driver = webdriver.Firefox()
    driver.get(url)
    # reject cookies
    decline_cookies(driver)
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