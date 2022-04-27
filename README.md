# geolocation-tools

## Setup

1. Download Stanford NER from https://nlp.stanford.edu/software/CRF-NER.html#Download
1. Extract to the project's base directory

Geopandas was difficult to install on my M1 macOS, this guide worked:
- https://stackoverflow.com/questions/71137617/error-installing-geopandas-in-python-on-mac-m1

## Folders

### Short texts

Contains arbitrarily truncated versions of the full texts, to be used for testing the NER script more quickly

## Scripts

### Stanford_NER_toCSV.py

This script performs NER on the texts in either `full_texts` or `short_texts`. It creates one CSV file per text, containing all identified Entities. Additionally, it searches each placename using the GHAP API and creates a map of the results.

### TLC_Disambig.py

This script searches names from `test_csv.csv` using the GHAP API and attempts to disambiguate to a single location. It creates a single CSV file of all outputs.

### atap_geolocations.ipynb

This is a Python notebook that explains how to use the geolocation tools. It is found in the `notebooks/` folder.
