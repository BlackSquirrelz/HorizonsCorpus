#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import etree
import sys, operator, os
from Wordplus_Parser import TetmlFile
import contents_control # necessary for validating contents list
from copy import deepcopy
import argparse
import time
import re

##############################################################################

ap = argparse.ArgumentParser(description="Script for adding article boundaries to tetml wordplus files for SNF Horizonte corpus.\nDependencies: Wordplus_Parser, tools.")

ap.add_argument("-i", "--input",  required=True, help="TETML input file")

# ap.add_argument("-f", "--filepath", required=False, default=False, help="path to directory containing input files. For bulk processing.")

ap.add_argument("-wc", "--without_control", required=False, default=False, action="store_true", help="whether article headings should be confirmed manually")

args = ap.parse_args()

##############################################################################

def add_article_boundaries(tetml_obj, content_list):
    """Creates new XML file with article boundaries.
        Args: tetml_obj from Wordplus_Parser, content_list (manually validated or automatically extracted)
        Effects: New XML file
        """

    outfile = tetml_obj.filename + "_NNS_article_boundaries.xml"

    outtree = etree.Element("Document", attrib={"document_id": outfile})

    c = 0

    for i, (num, title) in enumerate(content_list):
        if i != len(content_list)-1: # not last item in list
            # get list of page numbers for a given article
            # print(content_list)
            x = [d for d in range(content_list[i][0], content_list[i+1][0])]
        else:
            x = [content_list[-1][0]]

        # create article element in outtree
        article_elem = etree.SubElement(outtree, "Article", attrib={"article_id": "a"+str(i+1), "title": title})

        c += 1

        for l in x:
            # for each page number relevant to an article, add the page elements to the article element.
            for _, elem in etree.iterwalk(tetml_obj.tetml, tag="Page"):

                try:
                    if int(elem.attrib["number"]) == l:
                        article_elem.append(deepcopy(elem))
                        elem.clear()
                except KeyError: # page has no attrib "number"
                    pass

    outtree = etree.ElementTree(outtree)

    # for some reason, \n is missing after the Article SubElements.
    outtree.write(open(outfile, 'wb'), pretty_print=True, xml_declaration=True, encoding="utf-8")

    print("{} article boundaries created in {}.".format(c, outfile))

def write_contents(contents, filename):
    now = time.localtime(time.time())
    with open(filename+"_validated_contents.txt",
              "w+",
              encoding="utf8") as outf:
        outf.write("## Validated Contents for {}. Created: {}".format(filename, time.strftime("%y/%m/%d %H:%M.\n\n", now)))

        # outf.write("Validated Contents for {}".format(filename))
        for i in contents:
            outf.write("{}\t{}\n".format(i[0], i[1]))

def process_file(file, without_control):
    tetml = TetmlFile(file)
    # get issue number from filename
    issue_num = int(re.search("_(\d\d\d?)_[de|en|fr]", tetml.filename).group(1))
    # if issue number is 96+ process as a NEW issue.
    if issue_num > 95:
        print("Processing NEW issue...")
        contents = tetml.parse_contents_NEW()
    # if issue number is 81 - 95 process as a MID issue.
    elif issue_num < 96 and issue_num > 80:
        print("Processing MID issue...")
        contents = tetml.parse_contents_MID()
    # otherwise, process as an OLD issue.
    else:
        print("Processing OLD issue...")
        contents = tetml.parse_contents_OLD()

    if without_control == True: # process contents without validating manually
        add_article_boundaries(tetml, contents)
    else:
        validated_contents = contents_control.check_inventory(contents, tetml.filename)
        write_contents(validated_contents, tetml.filename)
        add_article_boundaries(tetml, validated_contents)

def main(args):
    if os.path.isdir(args.input):
        filepath = args.input
        for f in os.listdir(filepath):
            wordplus_tetml = os.path.join(filepath, f)
            process_file(wordplus_tetml, args.without_control)
    else:
        process_file(args.input, args.without_control)


if __name__ == "__main__":
    main(args)
