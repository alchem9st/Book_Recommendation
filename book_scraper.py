#!/usr/bin/python
# -*- coding: utf-8 -*-

# A scraper that scrapes the book reviews on Amazon.com.
# Entry of the scraper: search result page which contains a list of books.
# Can limit the number of books to be scraped.
# Possible improvement: Avoid Amazon Robot Check

import sys
import time
import os
import string
import logging
from BeautifulSoup import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


reload(sys)
sys.setdefaultencoding('utf8')

user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2272.76 Safari/537.36"
headers = { 'User-Agent' : user_agent }
driver = webdriver.Chrome('./chromedriver')

base_url = 'www.amazon.com'
page_query1 = 'ref=undefined_next_' # should append a number
page_query2 = '?ie=UTF8&showViewpoints=1&sortBy=recent&pageNumber=' # should append a number

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
loghandler = logging.StreamHandler(sys.stderr)
loghandler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(loghandler)

cur_dir = os.getcwd()
book_list_file = cur_dir + '/computer_theory_books.txt'
books_dir = cur_dir + '/computer_theory_books/'
if not os.path.exists(books_dir):
    os.makedirs(books_dir)

# should append a number after page_query1 and page_query2
page_query1 = 'ref=undefined_next_'
page_query2 = '?ie=UTF8&showViewpoints=1&sortBy=recent&pageNumber='
# a substitution table to remove punctuations
table = string.maketrans("", "")
book_ids = []
book_count = 0 # number of books scraped


# Parse all the books on a page and write all the reviews to local
def parse_book_list(url):
    book_names = []

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        result_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#resultsCol")))
    except:
        log.info('Search Error: ' + url)
        return 'Error'

    soup = BeautifulSoup(result_box.get_attribute('innerHTML'))
    title_boxes = soup.findAll('a', {'class' : 'a-link-normal s-access-detail-page  a-text-normal'})
    for title_box in title_boxes:
        global book_count
        book_count += 1
        if book_count > 1000: # Limit the number of books to scrape
            log.info('Reach max number of books.')
            return None, book_names

        if title_box.has_key('title'):
            book_name = title_box['title']
            book_names.append(book_name)
        if title_box.has_key('href'):
            book_url = title_box['href']
        else:
            log.info('Get Next Book URL Error.')
            book_url = None
        parse_book(book_name, book_url) # Parse the reviews of a book

    log.info('Finish parsing a list of books: ' + url)
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        result_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a#pagnNextLink")))
    except:
        log.info('Get Book List Error: ' + url)
        next_page_url = None

    # Get the link of the next page of books
    next_page_url = driver.find_element_by_xpath('//*[@id="pagnNextLink"]').get_attribute("href")
    return next_page_url, book_names


# Get the reviews of a book
def parse_book(book_name, book_url):
    if 'dp/' in book_url and 'ref=' in book_url:
        book_id = book_url[book_url.index('dp/') + 3 : book_url.index('ref=') - 1]
    else:
        return

    book_ids.append(book_id)
    file_path = books_dir + book_id + '.dat'

    # Create a local file for a book
    try:
        os.remove(file_path)
    except OSError:
        pass

    # Write the book name at the top of the file
    with open(file_path, 'a+') as fwrite:
        fwrite.write(book_name + '\n')

    url_segment = book_url.replace('dp/', 'product-reviews/')
    i = 1
    while True:
        # time.sleep(3) # avoid robot check

        next_review_page = url_segment[:url_segment.index('ref=')] + page_query1 + str(i) + page_query2 + str(i)
        log.info('Review Page URL: ' +  next_review_page)

        text = parse_reviews(next_review_page)
        if text == 'Finish' or text == 'Error':
            log.info('Finish parsing a book.')
            break
        # Write reviews to the local file
        with open(file_path, 'a') as fwrite:
            for t in text:
                fwrite.write(t.replace('\n', ' ') + '\n')
        i += 1


# Get the reviews on each review page of a book
def parse_reviews(url):
    text = []

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        reviews_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div#cm_cr-review_list")))
    except:
        log.info('Reviews not found: ' + url)
        return 'Error'

    soup = BeautifulSoup(reviews_box.get_attribute('innerHTML'))
    reviews = soup.findAll('div', {'class' : 'a-section review'})
    if len(reviews) == 0:
        return 'Finish'
    for rev in reviews:
        r = rev.find('span', {'class' : 'a-size-base review-text'})
        text.append(r.text)
    return text


if __name__ == "__main__":

    start_time = time.time()

    # Create a local book list file to store all the names of books
    try:
        os.remove(book_list_file)
    except OSError:
        pass

    # Entry for the scraper, to be change for different tasks
    next_list_url = 'http://www.amazon.com/s/ref=sr_pg_39?fst=as%3Aoff&rh=n%3A283155%2Cn%3A5%2Cn%3A3508%2Ck%3Acomputer+theory&page=39&keywords=computer+theory&ie=UTF8&qid=1462003846'
    while True:
        log.info("Book List URL: " + next_list_url)
        # Parse the reviews of books on a page and return the next page.
        next_list_url, names = parse_book_list(next_list_url)
        with open(book_list_file, 'a+') as fwrite:
            for name in names:
                fwrite.write(name + '\n')
        if next_list_url == None:
            break

    driver.close()
    print 'time:', time.time() - start_time, 's'

