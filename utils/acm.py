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
    note: str = None

@dataclass
class ACM_Item:
    doi: str = None
    publication_type: str = None
    date: str = None
    title: str = None
    authors: List[str] = None
    affiliation: str = None
    publication: str = None
    publication_short: str = None
    abstract: str = None
    author_tags: List[str] = None
    index_terms: List[str] = None
    subjects: List[str] = None
    keywords: List[str] = None
    cited_by: List[str] = None
    references: List[Reference_Item] = None


logger = setup_logger('acm', r'.\\logs\\acm.log', level=logging.INFO)

def build_acm_search_url(query):
    title_query = f'Title:({query})'
    abstract_query = f'Abstract:({query})'
    keyword_query = f'Keyword:({query})'
    query = ' OR '.join([title_query, abstract_query, keyword_query])
    query = urllib.parse.quote(query)
    query = query.replace('%20', '+')
    query = f'https://dl.acm.org/action/doSearch?fillQuickSearch=false&target=advanced&AllField={query}&expand=all&startPage=0&pageSize=10'
    return query

def scrape_acm_search_results(url, search_results_list, driver=None):
    if not driver:
        driver = webdriver.Firefox()
    driver.get(url)
    # reject cookies
    decline_cookies(driver)
    # get hitslength
    try:
        hits = driver.find_element(By.CLASS_NAME, 'hitsLength').text
        if hits:
            hits = int(hits)
    except Exception as e:
        logger.error(f'Error getting hits length: {e}')
        hits = 0
    # get search results box
    search_results = driver.find_element(By.CLASS_NAME, 'search-result__xsl-body')
    # search results list
    results = search_results.find_elements(By.CLASS_NAME, 'search__item')
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
            WebDriverWait(result, 10).until(EC.element_to_be_clickable(result.find_element(By.CLASS_NAME, 'count-list').find_element(By.TAG_NAME, 'button')))
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
            WebDriverWait(result, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'abstract-text')))
            elements = result.find_element(By.CLASS_NAME, 'abstract-text').find_elements(By.TAG_NAME, 'p')
            if len(elements) == 1:
                elements = [elements]
            abstract_elements = []
            for element in elements:
                abstract_elements.append(element.text)
            acm_item.abstract = ' '.join(abstract_elements)
        except Exception as e:
            logger.error(f'Error getting abstract: {e}')
        # try loading subject
        try:
            WebDriverWait(result, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'Subject')))
            subjects = result.find_element(By.CLASS_NAME, 'Subject').find_elements(By.TAG_NAME, 'p')
            subjects_list = []
            for subject in subjects:
                text = subject.text
                if text not in subjects_list and text != '':
                    subjects_list.append(text)
            acm_item.subjects = subjects_list
        except Exception as e:
            logger.error(f'Error getting subjects: {e}')
        # try getting keywords
        try:
            WebDriverWait(result, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'keywords-text')))
            keywords = result.find_element(By.CLASS_NAME, 'keywords-text').find_elements(By.TAG_NAME, 'p')
            keywords_list = []
            for kw in keywords:
                text = kw.text
                if text not in keywords_list and text != '':
                    keywords_list.append(text)
            acm_item.keywords = keywords_list
        except Exception as e:
            logger.error(f'Error getting keywords: {e}')
        # open publication in new window and add information to acm_item
        open_publication_page(result, acm_item)
        # add acm_item to list
        search_results_list.append(acm_item)
        logger.info(f'Finished item: {acm_item.title}')
        print(f'Finished item: {acm_item.title}')
    
    logger.info(f'Finished page: {len(search_results_list)}/{hits} hits')
    print(f'Finished page: {len(search_results_list)}/{hits} hits')
    try:
        next_page_url = driver.find_element(By.CLASS_NAME, 'pagination').find_element(By.CLASS_NAME, 'pagination__btn--next').get_attribute('href')
    except Exception as e:
        next_page_url = None
        logger.error(f'Error getting next page url: {e}')
        if len(search_results_list) < hits:
            logger.error(f'Not all hits were processed: {len(search_results_list)}/{hits}')
        else:
            logger.info('All hits were processed')
    if next_page_url:
        scrape_acm_search_results(next_page_url, search_results_list, driver)

def decline_cookies(driver):
    # decline all cookies
    try:
        driver.find_element(By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll').click()
        WebDriverWait(driver, 10).until(EC.invisibility_of_element_located((By.ID, 'CybotCookiebotDialogBodyLevelButtonLevelOptinDeclineAll')))
    except Exception as e:
        logger.error(f'Error declining cookies: {e}')


def open_publication_page(result_box, item: ACM_Item):
    # get url, open and decline cookies
    try:
        pub_link = result_box.find_element(By.CLASS_NAME, 'issue-item__title').find_element(By.TAG_NAME, 'a').get_attribute('href')
        driver = webdriver.Firefox()
        driver.get(pub_link)
        # reject cookies
        decline_cookies(driver)
    except Exception as e:
        logger.error(f'Error getting publication link: {e}')
        return
    # if item.publication_type == 'ARTICLE' or item.publication_type == 'RESEARCH-ARTICLE':
    # get abstract
    try:
        abstract = driver.find_element(By.CLASS_NAME, 'abstractSection').find_element(By.TAG_NAME, 'p').text
        if item.abstract is None or (item.abstract != abstract and len(abstract) >= len(item.abstract)):
            item.abstract = abstract
    except Exception as e:
        logger.error(f'Error getting abstract: {e}')
    # get affiliation
    try:
        item.affiliation = driver.find_element(By.CLASS_NAME, 'published-info').find_element(By.CLASS_NAME, 'rlist--inline').text
    except Exception as e:
        logger.error(f'Error getting affiliation: {e}')
    # get index terms
    try:
        elements = driver.find_element(By.CSS_SELECTOR, 'ol.rlist.organizational-chart').find_elements(By.TAG_NAME, 'a')
        index_terms = []
        for element in elements:
            index_terms.append(element.text)
        item.index_terms = index_terms
    except Exception as e:
        logger.error(f'Error getting index terms: {e}')
    # get references (RESEARCH-ARTICLE)
    try:
        references_section = driver.find_element(By.CSS_SELECTOR, 'div.article__section.article__references')
        show_all_references_button = references_section.find_element(By.CSS_SELECTOR, 'button.btn')
        if show_all_references_button:
            show_all_references_button.click()
        references = references_section.find_element(By.CSS_SELECTOR, 'ol.rlist.references__list').find_elements(By.TAG_NAME, 'li')
        references_list = []
        for ref in references:
            references_list.append(parse_reference_item(ref, item.publication_type))
        item.references = references_list
    except Exception as e:
        logger.error(f'Error getting references: {e}')
    # get citations (open in new window)
    try:
        cited_by_section = driver.find_element(By.CSS_SELECTOR, 'div.article__cited.article__section')
        citedby_url = cited_by_section.find_element(By.ID, 'downloadAllMain').get_attribute('href')
        if not citedby_url.endswith('#'):
            cited_by_list = open_cited_by_page(citedby_url, item.publication_type)
            item.cited_by = cited_by_list
    except Exception as e:
        logger.error(f'Error getting cited by: {e}')
    # get author tags (open side bar)
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CLASS_NAME, 'loa__link')))
        driver.find_element(By.CLASS_NAME, 'loa__link').click()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'tab')))
        slide_content = driver.find_element(By.CLASS_NAME, 'w-slide__content')
        # open side bar
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'pill-information__contentcon')))
        slide_content.find_element(By.ID, 'pill-information__contentcon').click()
        author_tags = slide_content.find_element(By.CLASS_NAME, 'tags-widget').find_elements(By.TAG_NAME, 'li')
        author_tags_list = []
        for author_tag in author_tags:
            author_tags_list.append(author_tag.find_element(By.CLASS_NAME, 'badge-type').get_attribute('title'))
        item.author_tags = author_tags_list
        # close side bar
        driver.find_element(By.CLASS_NAME, 'w-slide__back').click()
        # # open cited by in new window
        # try:
        #     cited_by_section = driver.find_element(By.CSS_SELECTOR, 'div.article__cited.article__section')
        #     citedby_url = cited_by_section.find_element(By.ID, 'downloadAllMain').get_attribute('href')
        #     if not item.doi in citedby_url:
        #         cited_by_list = open_cited_by_page(citedby_url, item.publication_type)
        #         item.cited_by = cited_by_list
        # except Exception as e:
        #     logger.error(f'Error getting cited by: {e}')
        # # get references (RESEARCH-ARTICLE)
        # references_section = driver.find_element(By.CSS_SELECTOR, 'div.article__section.article__references')
        # show_all_references_button = references_section.find_element(By.CSS_SELECTOR, 'button.btn')
        # if show_all_references_button:
        #     show_all_references_button.click()
        # references = references_section.find_element(By.CSS_SELECTOR, 'ol.rlist.references__list').find_elements(By.TAG_NAME, 'li')
        # references_list = []
        # for ref in references:
        #     references_list.append(parse_reference_item(ref, item.publication_type))
        # item.references = references_list
    except Exception as e:
        logger.error(f'Error getting author tags: {e}')
        pub_link = None

    # if item.publication_type == 'DOCTORAL_THESIS' or not pub_link: # TODO find better methode to distinguish publication types
    #     # get abstract
    #     try:
    #         abstract = driver.find_element(By.CLASS_NAME, 'abstractSection').find_element(By.TAG_NAME, 'p').text
    #         if item.abstract is None or (item.abstract != abstract and len(abstract) >= len(item.abstract)):
    #             item.abstract = abstract
    #     except Exception as e:
    #         logger.error(f'Error getting abstract: {e}')
    #     # get affiliation
    #     try:
    #         item.affiliation = driver.find_element(By.CLASS_NAME, 'published-info').find_element(By.CLASS_NAME, 'rlist--inline').text
    #     except Exception as e:
    #         logger.error(f'Error getting affiliation: {e}')
    #     # get index terms
    #     try:
    #         elements = driver.find_element(By.CSS_SELECTOR, 'ol.rlist.organizational-chart').find_elements(By.TAG_NAME, 'a')
    #         index_terms = []
    #         for element in elements:
    #             index_terms.append(element.text)
    #         item.index_terms = index_terms
    #     except Exception as e:
    #         logger.error(f'Error getting index terms: {e}')
    # TODO add more publication types
    if not pub_link:
        None
    driver.close()
        

def open_cited_by_page(url, pub_type):
    driver = webdriver.Firefox()
    driver.get(url)
    # reject cookies
    decline_cookies(driver)
    ref_items = driver.find_elements(By.CLASS_NAME, 'references__item')
    ref_item_list = []
    if isinstance(ref_items, webdriver.remote.webelement.WebElement):
        ref_items = [ref_items]
    for ref_item in ref_items:
        ref_item_list.append(parse_reference_item(ref_item, pub_type))   
    # close
    driver.close()
    return ref_item_list

def parse_authors_from_text(ref_item):
    try:
        authors = ref_item.find_element(By.CLASS_NAME, 'references__authors').text
        authors_list = [author.strip() for author in authors.replace(' and ', ',').split(',')]
        return authors_list
    except Exception as e:
        logger.error(f'Error getting authors from references__authors.text: {e}')
        return []

def parse_reference_item(ref_item, pub_type):
    result = Reference_Item()
    # get authors (working)
    try:
        try:
            authors = ref_item.find_element(By.CLASS_NAME, 'references__authors').find_elements(By.CLASS_NAME, 'references__name')
            if len(authors) > 0:
                authors_list = [author.text.strip() for author in authors]
                result.authors = authors_list
        except Exception as e:
            logger.error(f'Error getting authors using references__name: {e}')
        
        if not result.authors:
            result.authors = parse_authors_from_text(ref_item)
    except Exception as e:
        logger.error(f'Error getting authors: {e}')
    # get year (working)
    try:
        try:
            year = ref_item.find_element(By.CLASS_NAME, 'references__year').text.strip('().')
            if year:
                result.year = year
        except Exception as e:
            logger.error(f'Error getting year using references__year: {e}')
        if not result.year:
            result.year = ref_item.find_element(By.CLASS_NAME, 'pub-year').text.strip('().')
    except Exception as e:
        logger.error(f'Error getting year using pub-year: {e}')
    # get title (working)
    try:
        title = ref_item.find_element(By.CLASS_NAME, 'references__article-title').text
        result.title = title
    except Exception as e:
        logger.error(f'Error getting title: {e}')
    # get publication (working)
    try:
        publication = ref_item.find_element(By.CLASS_NAME, 'references__source').text
        result.publication = publication
    except Exception as e:
        logger.error(f'Error getting publication: {e}')
    # get volume (working)
    try:
        try:
            volume = ref_item.find_element(By.CLASS_NAME, 'references__volume').text
            if volume:
                result.volume = volume
        except Exception as e:
            logger.error(f'Error getting volume using references__volume: {e}')
        
        if not result.volume:
            result.volume = ref_item.find_element(By.CLASS_NAME, 'volume').text
    except Exception as e:
        logger.error(f'Error getting volume using volume classname: {e}')
    # get issue (working)
    try:
        try:
            issue = ref_item.find_element(By.CLASS_NAME, 'references__issue').text
            if issue:
                result.issue = issue
        except Exception as e:
            logger.error(f'Error getting issue using references__issue: {e}')
        if not result.issue:
            result.issue = ref_item.find_element(By.CLASS_NAME, 'issue').text
    except Exception as e:
        logger.error(f'Error getting issue using issue classname: {e}')
    # get publication date
    try:
        pub_date = ref_item.find_element(By.CLASS_NAME, 'pub-date').text
        pub_date = pub_date.split(':')[1].strip(' ')
        result.pub_date = pub_date
    except Exception as e:
        logger.error(f'Error getting publication date using pub-date classname: {e}')
    # get doi (working)
    try:
        try:
            doi = ref_item.find_element(By.CSS_SELECTOR, 'span.doi').text
        except Exception as e:
            doi = None
            logger.error(f'Error getting doi using span.doi: {e}')
        if not doi:
            doi = ref_item.find_element(By.CLASS_NAME, 'link').get_attribute('href')
        if 'doi.org' in doi:
            doi = doi.split('doi.org/')[1]
        result.doi = doi
    except Exception as e:
        logger.error(f'Error getting doi using link classname and href attribute: {e}')
    # try get note
    try:
        note = ref_item.find_element(By.CLASS_NAME, 'references__note').text
        if note:
            result.note = note
    except Exception as e:
        logger.error(f'Error getting note: {e}')

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