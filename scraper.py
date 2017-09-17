import re
import sys
import json
import logging
from logging.handlers import RotatingFileHandler
from configparser import SafeConfigParser
import requests
from bs4 import BeautifulSoup, Tag


def scrape_info_by_title(info_title='', info_list=[]):
    if not info_title:
        logger.error('No info title (keyword) provided.')
        return False
    for tag_text in soup.find_all(text = info_title):
        for item in tag_text.parent.next_siblings:
            if isinstance(item, Tag) and div_span_pattern.match(item.name) and item.text.strip():
                txt = ' '.join(item.find_all(text = True))
                info_list.append(txt.strip(' \r\n\t'))
                break
    return True

def closeup(msg):
    logger.info(msg)
    if not out_file.closed:
        try:
            out_file.close()
        except Exception as e:
            logger.error(e)


if __name__ == '__main__':

    ####################################
    # Initialization
    ####################################
    # Load configuration file 
    config = SafeConfigParser()
    config.read('config.ini')

    # Load configurations
    URL_BASE = config.get('Remote', 'URL_BASE')
    URL_HOME = config.get('Remote', 'URL_HOME')
    ITEMS_PER_PAGE = int(config.get('Remote', 'ITEMS_PER_PAGE'))
    INFO_TO_SCRAPE = json.loads(config.get('Remote', 'INFO_TO_SCRAPE'))
    FILE_TO_SAVE = config.get('Results', 'FILE_TO_SAVE')
    LOG_FILE = config.get('Logging', 'LOG_FILE')
    LOG_LEVEL = config.get('Logging', 'LOG_LEVEL')
    LOG_SIZE_MAX = int(config.get('Logging', 'LOG_SIZE_MAX'))
    LOG_ROTATE_MAX = int(config.get('Logging', 'LOG_ROTATE_MAX'))

    # Initialize logging
    logger = logging.getLogger('Product Scraping')
    logger.setLevel(LOG_LEVEL.upper())
    log_handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_SIZE_MAX, backupCount=LOG_ROTATE_MAX)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)

    # The target text must be in such a tag
    div_span_pattern = re.compile(r'div|span')
    # List for final result
    product_list = []

    logger.info('------------------ Start Program ---------------------')    
    # Open result file
    out_file = open(FILE_TO_SAVE, 'w', encoding='utf-8')
    out_file.write(','.join([i for i, j in INFO_TO_SCRAPE])+'\n')


    ####################################
    # Download homepage
    ####################################
    logger.info('Started downloading page - {}'.format(URL_HOME))
    try:
        res = requests.get(url=URL_HOME)
    except Exception as e:
        logger.error(e)
        closeup('Exiting program --------------')
        sys.exit()
    
    logger.info('Finished downloading page - {}'.format(URL_HOME))


    ####################################
    # Find 'product list' page urls
    ####################################
    logger.info('Gathering product list page urls')
    soup = BeautifulSoup(res.text, 'html.parser')

    urls_product_list = []

    for div in soup.find_all('div', attrs = {'class': 'fixtureLink left'}):
        href = div.find('a')['href']
        if href:
            if href == '#':
                urls_product_list.append(URL_HOME)
            else:
                urls_product_list.append(URL_BASE + href)


    ####################################
    # Traverse product list pages
    ####################################
    for url in urls_product_list:

        logger.info('Started downloading page - {}'.format(url))
        try:
            page = requests.get(url=url)
        except Exception as e:
            logger.error(e)
            logger.info('Skipping this page')
            continue
        logger.info('Finished downloading page - {}'.format(url))


        # find the post url & data in Javascript AJAX 
        search_res = re.search('\$\.post\(\"(.*)\".*(\{.*\})', page.text)

        if not search_res:
            continue

        url_more = URL_BASE+search_res.group(1)
        post_data = json.loads(search_res.group(2))

        # send requests to fetch product info (page by page)
        more = True 
        index_from = 0

        while more:
            scrape_url = url_more + str(index_from)
            page = requests.post(url = scrape_url, data = post_data)
            soup = BeautifulSoup(page.text, 'html.parser')

            logger.info('Scraping page - {}'.format(scrape_url))

            # if response is valid, process it
            if soup.find('div'):
                all_found_list = []        # contains lists of found text e.g. [list_of_prod_names, list_of_prod_dates, ...]
                for header, title in INFO_TO_SCRAPE:
                    found_list = []
                    scrape_successful = scrape_info_by_title(info_title = title, info_list = found_list)
                    if not scrape_successful:
                        logger.error('Scraping failed, skipping ...')
                        continue
                    all_found_list.append(found_list)

                # put together all pieces
                new_list = list(zip(*all_found_list))

                if not new_list:           # empty list, no more products
                    more = False
                else:                      # or append the products to the result file
                    logger.info('Adding {} products to result file'.format(len(new_list)))
                    for prod in new_list:
                        try:
                            # add double-quotes around each element to escape comma in CSV
                            out_file.write('"'+'","'.join(prod)+'"'+'\n')
                        except Exception as e:
                            logger.error(e)
                            closeup('Exiting program --------------')
                            sys.exit()

                    index_from += ITEMS_PER_PAGE
            else:
                more = False


    ####################################
    # Finish program
    ####################################
    closeup('------------------ End Program ---------------------')
