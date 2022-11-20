import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import requests
import time
import re
import os
from tqdm import tqdm
import logging
from datetime import datetime
import pickle
from collections import Counter
from functools import reduce
from nltk import word_tokenize
from nltk.corpus import stopwords
from nltk.tokenize import RegexpTokenizer
from nltk.stem import PorterStemmer
from num2words import num2words
import matplotlib.pyplot as plt
import geopandas as gpd
import pandas as pd
import numpy as np


def get_places(site, pages, filename='places.txt'):
    '''
    Save places urls
    :param site:
    :param pages:
    :param filename:
    :return:
    '''

    with open(filename, 'w') as file:
        for i in tqdm(pages):
            try:
                # Get the page
                url = f'{site}/places?page={i}&sort=likes_count'
                response = requests.get(url)

                soup = BeautifulSoup(response.text, features='html.parser')

                # Get the references
                anchors = soup.find_all('a', 'content-card content-card-place')

                if len(anchors) != 18:
                    logging.warning(f'page {i}: {len(anchors)} places founded')

                # Save page number and place reference
                file.writelines([f'{str(i)} {a.attrs["href"]}\n' for a in anchors])

            except Exception:
                logging.exception(f'page {i}: request failed')


def download_place(url, page, folder='data/html/'):
    '''
    Download html data of a place
    :param url: place url
    :param page: place page
    :param folder: path to be combined wiht page to save html file
    :return:
    '''

    slug = url.split("places/")[1]

    try:
        # Get the page
        response = requests.get(url)
        soup = BeautifulSoup(response.text, features='html.parser')

        if len(response.text) < 50:
            logging.warning(f'page {page}: short response for {url}')
            logging.debug(response.text)
            return

        # If needed create a folder
        if not os.path.exists(f'{folder}/page_{page}'):
            os.makedirs(f'{folder}/page_{page}')

        # Save html file
        with open(f'{folder}/page_{page}/{slug}.html', 'w', encoding='utf-8') as html_file:
            html_file.write(str(soup))

    except Exception:
        logging.exception(f'page {page}: request failed for {url}')


def parse_page(file_path, export_tsv=False, folder='data/tables'):
    '''
    Parse html data of a place to extract useful information
    :param file_path: path where the html file is saved
    :param export_tsv: boolean to enable tsv export
    :param folder: path for the exported tsv file
    :return:
    '''

    soup = BeautifulSoup(open(file_path, encoding='utf-8'), features='html.parser')

    try:
        place_name = soup.find('h1', {'class': 'DDPage__header-title'}).text
    except:
        place_name = None

    try:
        place_tags = [tag.text.strip() for tag in soup.find_all('a', {'class': 'itemTags__link js-item-tags-link'})]
    except:
        place_tags = None

    try:
        num_people_visited = soup.find_all('div', {'class': 'item-action-count'})[0].text
    except:
        num_people_visited = None

    try:
        num_people_want = soup.find_all('div', {'class': 'item-action-count'})[1].text
    except:
        num_people_want = None

    try:
        place_desc = ''.join([p.text for p in soup.find('div', {'id': 'place-body'}).find_all('p')])
    except:
        place_desc = None

    try:
        place_short_desc = soup.find('h3', {'class': 'DDPage__header-dek'}).text
    except:
        place_short_desc = None

    try:
        place_nearby = list(
            set([nearby.text for nearby in soup.find_all('div', {'class': 'DDPageSiderailRecirc__item-title'})]))
    except:
        place_nearby = None

    try:
        place_address = re.sub('<[^<]+?>', ' ',
                               str(soup.find('address', {'class': 'DDPageSiderail__address'}).find('div'))).strip()
    except:
        place_address = None

    try:
        place_alt, place_long = soup.find('div', {'class': 'DDPageSiderail__coordinates'}).text.strip().split(', ')
    except:
        place_alt = None
        place_long = None

    try:
        first_editors = [contributor.text for contributor in
                         soup.find_all('div', 'DDPContributorsList')[1].findChildren('a',
                                                                                     'DDPContributorsList__contributor',
                                                                                     recursive=False)]
        try:
            # Since the html structure is different for hidden editors we need to get them separately
            hidden_editors = [contributor.text for contributor in
                              soup.find('a', 'DDPContributorsList__popover-trigger').findNextSibling().find_all('span')]
        except:
            hidden_editors = []

        place_editors = first_editors + hidden_editors
    except:
        place_editors = None

    try:
        place_pub_date = soup.find_all('div', {'class': 'DDP__section-label'})[0].find_next_sibling().text.replace(',',
                                                                                                                   '')
    except:
        place_pub_date = None

    try:
        place_related_lists = [list.text.strip() for list in
                               soup.find_all('div', {'class': 'CardRecircSection__card-grid'})[2].find_all('h3', {
                                   'class': 'Card__heading'})]
    except:
        place_related_lists = None

    try:
        place_related_places = [list.text.strip() for list in
                                soup.find_all('div', {'class': 'CardRecircSection__card-grid'})[1].find_all('h3', {
                                    'class': 'Card__heading'})]
    except:
        place_related_places = None

    place_url = 'https://www.atlasobscura.com/places/' + file_path.split('/')[3][:-5]

    place = {'placeName': place_name,
             'placeTags': place_tags,
             'numPeopleVisited': num_people_visited,
             'numPeopleWant': num_people_want,
             'placeDesc': place_desc,
             'placeShortDesc': place_short_desc,
             'placeNearby': place_nearby,
             'placeAddress': place_address,
             'placeAlt': place_alt,
             'placeLong': place_long,
             'placeEditors': place_editors,
             'placePubDate': place_pub_date,
             'placeRelatedLists': place_related_lists,
             'placeRelatedPlaces': place_related_places,
             'placeURL': place_url}

    if export_tsv:

        slug = place['placeURL'].split("places/")[1]

        # Create folder if needed
        if not os.path.exists(f'{folder}'):
            os.makedirs(f'{folder}')

        # Save to tsv
        with open(f'{folder}/{slug}.tsv', 'w', encoding='utf-8') as file:
            file.write('\t'.join(list(place.keys())) + '\n')
            file.write('\t'.join(list([str(value) for value in place.values()])))
            logging.debug(f'{slug}')


def pre_process_text(txt):
    '''
    Process a text applying the following steps:
    - converting number to words
    - removing stopwords
    - removing punctuation
    - stemming
    :param txt: input text
    :return: processed text
    '''

    en_stopwords = stopwords.words('english')
    tokenizer = RegexpTokenizer(r"\w+")
    porter = PorterStemmer()

    try:
        # Remove punctuation
        txt = tokenizer.tokenize(str(txt).lower())

        # Convert numbers
        txt = [num2words(word) if word.isnumeric() else word for word in txt]

        # Remove stopwords
        txt = [token for token in word_tokenize(" ".join(txt)) if token not in en_stopwords]

        # Stemming
        txt = [porter.stem(word) for word in txt]
    except:
        logging.exception(txt)

    return txt


def pre_process_tsv(path='data/merged_places.tsv'):
    '''
    Preprocess the data and save the output into a new file
    :param path: path of the data file
    :return:
    '''

    tsv = pd.read_csv(path, delimiter='\t', index_col=0)

    # Remove stopwords, remove punctuation and apply stemming
    tsv['placeDesc'] = tsv['placeDesc'].apply(lambda x: pre_process_text(x))

    # Remove stopwords, remove punctuation and apply stemming
    tsv['placeName'] = tsv['placeName'].apply(lambda x: pre_process_text(x))

    # Save to tsv
    tsv.to_csv(f'data/processed_{path.split("/")[1]}', sep='\t')


def my_mean(list):
    '''
    Get the rounded mean of a numeric list
    :param list: numeric list
    :return: 2 decimal float
    '''

    sum = 0

    for item in list:
        sum += item

    return round(sum / len(list), 2)


def name_is_before_name(first, second):
    '''
    Check if the provided string are in alphabetical order
    :param first: first string
    :param second: second string
    :return: boolean
    '''

    for char1, char2 in zip(first, second):
        if char1 < char2:
            return True
        elif char1 > char2:
            return False

    # If the loop end without a return statement it means that a name is contained into another (or they are the same)
    if len(first) <= len(second):
        return True
    return False


def get_students():
    '''
    Gets students list from ApplicantsInfo.txt
    :return: list where each student is a dict with name and avg (average of all scores)
    '''

    students = []

    with open("ApplicantsInfo.txt") as file:

        n, m = file.readline().split()

        for line in file:
            student_row = line.strip().split()

            student = " ".join(student_row[0:2]) # Get student name and surname
            grades = [int(grade) for grade in student_row[2:]] # Get student grades

            total_average = my_mean(grades) # Calculate student average

            students.append({'name': student, 'avg': total_average}) # Add student to students list

    return students
