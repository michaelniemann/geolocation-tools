"""
This code will take in a number of txt files and extract LOCATIONS, ORGANIZATION AND PERSON and print this in column 0 of csv,
entity type will be printed in column 1 and filename will be printed in column 2. Stanford NER can be downloaded from https://nlp.stanford.edu/software/CRF-NER.html
"""

import os
from pickle import NONE
import nltk
import csv
import time
import urllib
import requests
import json
import math

import matplotlib.pyplot as plt
import pandas as pd
import geopandas as gpd
from geopandas import GeoDataFrame

from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize

from shapely.geometry import Point

# there are options for additional clssifiers
# As before make sure these link to your local versions of the libaries

st = StanfordNERTagger(
    os.path.normpath('./stanford-ner-2020-11-17/classifiers/english.all.3class.distsim.crf.ser.gz'),
    os.path.normpath('./stanford-ner-2020-11-17/stanford-ner.jar'))

# text_directory = os.path.normpath("texts/") 
text_directory = os.path.normpath("short_texts/") 
csv_directory = os.path.normpath("ner_output/")

if not os.path.exists(text_directory):
    os.makedirs(text_directory)
if not os.path.exists(csv_directory):
    os.makedirs(csv_directory)

# ------- TLC api call stuff -------
def build_url(placename: str, search_type: str, search_public_data: bool = True) -> str:
    """
    Build a url to query the tlcmap/ghap API.

    placename: the place we're trying to locate
    search_type: what search type to use (accepts one of ['contains','fuzzy','exact'])
    """
    safe_placename = urllib.parse.quote(placename.strip().lower())
    url = f"https://tlcmap.org/ghap/search?"
    if search_type == 'fuzzy':
        url += f"fuzzyname={safe_placename}"
    elif search_type == 'exact':
        url = f"name={safe_placename}"
    elif search_type == 'contains':
        url = f"containsname={safe_placename}"
    else:
        return None
    # Search Australian National Placenames Survey provided data
    url += "&searchausgaz=on"
    # Search public provided data, this data could be unreliable
    if search_public_data == True:
        url += "&searchpublicdatasets=on"
    # Retreive data as JSON
    url += "&format=json"
    return url

def query_name(placename: str, search_type: str):
    """
    Use tlcmap/ghap API to check a placename, implemented fuzzy search but will not handle non returns.
    """
    url = build_url(placename, search_type='fuzzy', search_public_data = False)
    if url:
        r = requests.get(url)
        if r.url == 'https://tlcmap.org/ghap/maxpaging':
            return None
        if r.content.decode() == 'No search results to display.':
            # This should have obviously just be an empty list of features, but TLCMap is badly behaved
            return json.loads('{"type": "FeatureCollection","metadata": {},"features": []}')
        if r.ok:
            #data = json.loads(r.content)
            return r.json()
    return None

# ------- mapping stuff -------
def map(filename, locations):
    #df = pd.read_csv("Long_Lats.csv", delimiter=',', skiprows=0, low_memory=False)

    df = pd.DataFrame(locations, columns = ['placename', 'long', 'lat'])
    geometry = [Point(xy) for xy in zip(df['long'], df['lat'])]
    gdf = GeoDataFrame(df, geometry=geometry)   

    # TODO: fit content to frame
    world = gpd.read_file(gpd.datasets.get_path('naturalearth_lowres'))

    minx, miny, maxx, maxy = gdf.total_bounds

    if not all(math.isinf(coord) for coord in [minx, miny, maxx, maxy]) \
    and not all(math.isnan(coord) for coord in [minx, miny, maxx, maxy]):
        MAP_PADDING = 5
        ax = world.plot(figsize=(10,6))
        ax.set_xlim(minx - MAP_PADDING, maxx + MAP_PADDING)
        ax.set_ylim(miny - MAP_PADDING, maxy + MAP_PADDING)

        gdf.plot(ax=ax, marker='o', color='red', markersize=15)

        plt.savefig(f"maps/{filename}.png", bbox_inches='tight')
    
# ------- end of mapping stuff -----

def tlc_query(placename):
    response = query_name(placename, "fuzzy")
    # TODO: don't just choose the first result
    if response and len(response['features']):
        return response['features'][0]['geometry']['coordinates']
    else:
        return []


def textcheck(filename):
    start = time.time()
    print("Working on | ", filename)
    # set the specific path for the 'filename' which is basically working through a list of everything that is in the folder
    textlocation = os.path.normpath(os.path.join(
            text_directory,
            filename))
    text = open(textlocation, encoding='utf-8').read()

    text_filename = os.path.basename(textlocation)

    tokenized_text = word_tokenize(text)
    classified_text = st.tag(tokenized_text)

    locations = []
    entities = []  # this means entities, not locations
    p_item = ('gibberish', '-1')  # ('New South Wales': 'LOCATION') (of, )

    for i in classified_text:
        if p_item[1] != '-1' and i[1] != p_item[1] and p_item[1] != 'O':
            # Returning only named entities!
            if p_item[1] == "LOCATION":
                results = tlc_query(p_item[0])
                location = [p_item[0]] + results
                if len(location) == 3:
                    locations.append(location)
            entities.append(p_item)
        if p_item[1] != 'O' and p_item[1] != '-1' and p_item[1] == i[1]:
            p_item = (p_item[0] + ' ' + i[0], i[1])
            continue
        p_item = i
    if p_item[1] != 'O':
        entities.append(p_item)

    map(text_filename, locations)
   
    plusfile = [xs + (text_filename,) for xs in entities]  # this adds the FILEName into the CSV file

    # print(locations)

    with open(os.path.normpath(os.path.join(csv_directory, filename + ".csv")),
              'w') as f:  # Writing these to a CSV file that has the same name as the text file
        writer = csv.writer(f, delimiter=',', lineterminator='\n')
        writer.writerows(plusfile)
    end = time.time()
    print("Time elapsed | ", round(end - start, 2), "seconds")
    print("CSV written")


def startup():  # gets all the file names of the TEXT file and works through each of them iteratively
    for file in os.listdir(text_directory):
        filename = os.fsdecode(file)
        if filename.endswith(".txt"):
            # print(filename)
            textcheck(filename)
            continue
        else:
            pass


startup()
