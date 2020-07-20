#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Tannon Kew


import requests
from bs4 import BeautifulSoup as bs

"""
Script to download PDF files of SNF Horizonte from web archive.
"""

base_url_en = "http://www.snf.ch/en/researchinFocus/research-magazine-horizons/archive/Pages/default.aspx"

base_url_de = "http://www.snf.ch/de/fokusForschung/forschungsmagazin-horizonte/archiv/Seiten/default.aspx"

base_url_fr = "http://www.snf.ch/fr/pointrecherche/magazine-de-recherche-horizons/archives/Pages/default.aspx"

# Parse archive page.
source = requests.get(base_url_fr).text
soup = bs(source, "lxml")

# Get list of all PDF files in href tags.
pdf_tags = soup.find_all("div", class_="download-form")

# For each PDF write content to new file.
for pdf in pdf_tags:
    pdf_url = pdf.a["href"]
    pdf_name = pdf_url.split("/")[-1]
    print("saving...", pdf_name)
    pdf_bytes = requests.get(pdf_url).content
    with open(pdf_name, "wb") as outfile:
        outfile.write(pdf_bytes)
