#!/usr/bin/env python3
# -*- coding: utf8 -*-

# UZH - Einführung in die Multilinguale Textanalyse - HS 2018
# Author: Tannon Kew

# python3 convert_html2xml.py -i /Users/tannon/switchdrive/Horizonte/SNF_html_files/SNF_html_files_id_en -o horizonte_online_en.xml

from lxml import etree
from bs4 import BeautifulSoup as bs
import os
import sys
import argparse
import re
# import html
import html.parser as hp


##############################################################################

ap = argparse.ArgumentParser(description="Script for converting SNF html files to xml.\nRequires directory containing html files as input (-i) and the name of xml file to be outputted (-o).")

ap.add_argument("-i", "--input_dir", type=str, required=True, help="Filepath to directory containing SNF html files.")

ap.add_argument("-o", "--output_file", type=str, required=True, help="Name of output xml file.")

args = ap.parse_args()

##############################################################################

def convert_html2xml(input_file, article_counter):
    """
    """

    filename = os.path.basename(input_file)[:-5]
    id = filename.split("_")[2]

    with open(input_file) as html:
        soup = bs(html, "html.parser")
        html_body = soup.body
        # if file doesn't contain body element and cannot be processed, exit with error message.
        if not html_body:
            sys.exit("No element 'body' element found, cannot process.\nProgram aborted.\n")
        else:
            article_element = etree.Element("article")
            article_element.set("id", id)
            article_element.set("name", str(filename))

        # get title
        post_title = html_body.find("h4", class_="post-title")
        h1 = post_title.text
        if h1:
            child1 = etree.SubElement(article_element, "h1", attrib={"class": "title"})
            child1.text = h1

        # get date
        post_time = html_body.find("div", class_="post-time").contents
        date = post_time[-1].text
        if date:
            child2 = etree.SubElement(article_element, "p", attrib={"class": "date"})
            child2.text = date

        # get author
        author = post_time[0].text
        if author:
            child3 = etree.SubElement(article_element, "p", attrib={"class": "author"})
            child3.text = author

        # get abstract
        post_lead = html_body.find("div", class_="post-lead")
        abstract = post_lead.text
        if abstract:
            child4 = etree.SubElement(article_element,
                                      "p",
                                      attrib={"class": "abstract"})
            child4.text = abstract

        # get content
        post_excerpt = html_body.find("div", class_="post-excerpt")
        # text content is mainly in <p> and <h5> tags
        # this includes picture credits
        content = post_excerpt.find_all(["p", "h5"])

        for element in content:
            if element.name == "h5":
                # avoid tags with containing only nbsp
                if len(element.text) > 1:
                    par = etree.SubElement(article_element, "h3")
                    par.text = element.text
            else:
                # avoid tags with containing only nbsp
                if len(element.text) > 1:
                    par = etree.SubElement(article_element, "p")
                    # remove footers included in the text body if necessary and strip duplicate white space
                    par.text = clean_text(element.text)
                else:
                    pass

        return article_element

##############################################################################

def clean_text(string):
    footer = re.compile("CC BY-NC-ND")
    duplicate_ws = re.compile('[ \n]+')
    string = re.sub(footer, '', string)
    string = re.sub(duplicate_ws, ' ',string).strip()
    return string


def write_output(tree, output_file):
    # write the compiled tree to the output file.
    tree_element = etree.ElementTree(tree)
    tree_element.write(output_file, pretty_print=True, xml_declaration=True, encoding="utf-8")

##############################################################################

def main():
    # establish full file path and initilise variables
    in_file_path = os.path.join(os.getcwd(), args.input_dir)
    out_file_path = os.path.join(os.getcwd(), args.output_file)
    article_counter = 0
    outroot = etree.Element("corpus")

    print("Converting html files to xml.")
    # for each html file processed.
    ## TODO:
    ## ENSURE articles are read in parallel.
    for html_file in sorted(os.listdir(in_file_path)):
        if html_file.endswith(".html"):
            article_counter += 1
            print("Processing...", html_file)
            article_element = convert_html2xml(os.path.join(in_file_path, html_file), article_counter)
            outroot.append(article_element)


    write_output(outroot, out_file_path)
    print("{} articles processed.".format(article_counter))
    print("Conversion completed.")

if __name__ == "__main__":
    main()
