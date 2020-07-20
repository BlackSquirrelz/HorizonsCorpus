#!/usr/bin/env python3
# -*- coding: utf8 -*-
# UZH - Einführung in die Multilinguale Textanalyse - HS 2018
# Author: Tannon Kew

import requests
from lxml import html
import re

def save_html(filename, content):
    with open(filename, "wb") as page:
        print("writing...", filename)
        page.write(content)

def crawl(url):
    date_str = re.compile("\d\d\d\d/\d\d/\d\d")
    response = requests.get(url)
    content = response.content
    root = html.fromstring(content)

    author = root.xpath("//a[@rel='author']/text()")[0]
    title = root.xpath("//h4[@class='post-title']/text()")[0]
    date = re.search(date_str, url).group()
    date = re.sub("/", "-", date)

    id = "{}_{}_{}.html".format(date, author, title)

    save_html(id, content)

def get_articles(lang, issue_number):
    issue_url = lang + issue_number
    response = requests.get(issue_url)
    root = html.fromstring(response.content)
    article_links = root.xpath("//h4[@class='post-title']/a/@href")
    print(article_links)
    for url in article_links:
        crawl(url)



if __name__ == "__main__":
    de = "https://www.horizonte-magazin.ch/kategorie/ausgabe-"
    en = "https://www.horizons-mag.ch/category/issue-"
    fr = "https://www.revue-horizons.ch/categorie/edition-"

    # for i in range(110, 119):
        # get_articles(de, str(i))
        # get_articles(en, str(i))
        # get_articles(fr, str(i))
