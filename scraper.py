#!/usr/bin/python3
# 18 December 2017

import os
import re
import sys
import time
from random import randint

import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys


# split paragraph into sentences
def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n", " ")
    text = re.sub(prefixes, "\\1<prd>", text)
    text = re.sub(websites, "<prd>\\1", text)
    if "Ph.D" in text:
        text = text.replace("Ph.D.", "Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] ", " \\1<prd> ", text)
    text = re.sub(acronyms+" "+starters, "\\1<stop> \\2", text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps +
                  "[.]", "\\1<prd>\\2<prd>\\3<prd>", text)
    text = re.sub(caps + "[.]" + caps + "[.]", "\\1<prd>\\2<prd>", text)
    text = re.sub(" "+suffixes+"[.] "+starters, " \\1<stop> \\2", text)
    text = re.sub(" "+suffixes+"[.]", " \\1<prd>", text)
    text = re.sub(" " + caps + "[.]", " \\1<prd>", text)
    if "”" in text:
        text = text.replace(".”", "”.")
    if "\"" in text:
        text = text.replace(".\"", "\".")
    if "!" in text:
        text = text.replace("!\"", "\"!")
    if "?" in text:
        text = text.replace("?\"", "\"?")
    text = text.replace(".", ".<stop>")
    text = text.replace("?", "?<stop>")
    text = text.replace("!", "!<stop>")
    text = text.replace("<prd>", ".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences


if __name__ == '__main__':
    caps = "([A-Z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"

    # city list
    cities_file = './1000 Largest US Cities By Population2.txt'
    cities = pd.read_table(cities_file, delimiter=',')
    cities = list(cities['city'])
    cities = [word.lower() for word in cities]

    # agg of all sentences
    sent = []

    start_time = time.time()
    homepage = 'http://www.google.com.sg'
    START_URL = "https://www.<newssite_url>/templates/search/index.php?searchinput="
    count = 1

    DRIVER_PATH = os.path.join(os.getcwd(), "chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    driver = webdriver.Chrome(DRIVER_PATH, chrome_options=options)
    driver.set_page_load_timeout(7)
    driver.get(homepage)

    for city in cities:

        status = False
        city = city.replace(' ', '+')
        start_page = START_URL + city

        # frequent error when loading page (timeout error)
        timeout = 0
        breakout = False
        while(status is False):
            try:
                driver.get(start_page)
                status = True
            except:
                print('timeout error, refreshing')
                timeout = timeout + 1
                if timeout > 10:
                    print('skip %s' % city)
                    breakout = True
                    break

        if breakout is True:
            try:
                driver.close()
            except:
                pass
            driver = webdriver.Chrome(DRIVER_PATH, chrome_options=options)
            driver.set_page_load_timeout(7)
            driver.get(homepage)
            status = False
            continue

        status = False
        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")
        content = soup.findAll("p", {"class": "teaser"})

        # get link to all ten articles
        links = []
        for html in content:
            for link in html.find_all('a', href=True):
                links.append(link['href'])
            # end of for loop
        # end of for loop

        # go to each article in the page
        for url in links:

            # frequent error when loading page (timeout error)

            timeout = 0
            breakout = False
            while(status is False):
                try:
                    driver.get(url)
                    status = True
                except:
                    print('timeout error, refreshing')
                    timeout = timeout + 1
                    if timeout > 10:
                        print('error for %s' % url)
                        breakout = True
                        break

            if breakout is True:
                try:
                    driver.close()
                except:
                    pass
                driver = webdriver.Chrome(DRIVER_PATH, chrome_options=options)
                driver.set_page_load_timeout(7)
                driver.get(url)
                status = False
                continue

            status = False

            # extract out the article; split it to individual sentences; check each sentence contains the city
            try:
                html = driver.page_source
                soup = BeautifulSoup(html, "lxml")
                content = soup.find_all('p')
                for tag in content:
                    tag = tag.getText().lower()
                    sentences = split_into_sentences(tag)
                    city = city.replace('+', ' ')
                    for line in sentences:
                        if city.lower() in line:
                            sent.append(line)
                    # end of for loop
                # end of for loop
            except:
                pass

            # reset the status
            status = False

        # end of for loop

        print(count)
        count = count+1
        sent = list(set(sent))

    # End of for loop

    driver.close()

    # calculate time taken to run program
    seconds_took = time.time() - start_time
    minutes_took = seconds_took / 60
    print("Program took " + str(minutes_took) + " minutes")
    print('output to text file')
    print('number of sentences collected = %s' % len(sent))

    # ouput list to text file
    with open('./sentences.txt', 'a', encoding="utf-8") as myfile:
        for item in sent:
            myfile.write("%s\n" % item)

    print('End of program')
