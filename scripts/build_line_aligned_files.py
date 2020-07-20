# !/usr/bin/env python3
# -*- coding: utf8 -*-

# Tannon Kew; UZH Einführung in die MLTA 2018

import sys
import os
from lxml import etree as ET
import re
import argparse as ap

## To run:
## $ python3 build_line_aligned_files.py <directiory containing l1 corpus, l2 ## corpus and alignment file> <lang1_code> <lang2_code>
## e.g. python3 build_line_aligned_files.py fr-en/2002/ fr en
## to process an entire language pair with dir structure
## <lang1-lang2/year/[corpus_l1|corpus_l2|alignment_file]>
## use a bash for loop
## e.g. $ for i in {2002..2017}; do python3 build_line_aligned_files.py fr-en/$i/ fr en; done


dir = sys.argv[1]
pwd = os.getcwd()

filename_structure = re.compile("cs_news_(20\d\d)_(\w.*).xml")

corpus_l1 = ''
corpus_l2 = ''
alignment_file = ''

parser = ap.ArgumentParser()
parser.add_argument("input_dir", help="directory containing l1 corpus for a particular year, l2 corpus for the same year, the year's alignment file")
parser.add_argument("language1", help="language code of source language")
parser.add_argument("language2", help="language code of target language")
args = parser.parse_args()


for filename in os.listdir(dir):
    if filename.endswith(".xml"):
        match = filename_structure.search(filename)
        if match:
            year = match.group(1)
            ftype = match.group(2)
            if ftype == args.language1:
                corpus_l1 = os.path.join(dir, filename)
            elif ftype == args.language2:
                corpus_l2 = os.path.join(dir, filename)
            elif ftype == "s-align":
                alignment_file = os.path.join(dir, filename)
            else:
                # print("Not using {}".format(filename))
                sys.exit("Not all files found.")

print("currently processing {} and {} accoridng to sentence alignments in {}...\n".format(corpus_l1, corpus_l2, alignment_file))

# de-en/2001/cs_news_2001_de.xml --> cs_news_2001_de_lines.txt
outfile1 = os.path.join(pwd, corpus_l1[11:-4] + "_lines.txt")
outfile2 = os.path.join(pwd, corpus_l2[11:-4] + "_lines.txt")

## for testing
# outfile1 = corpus_l1[:-4] + "_lines.txt"
# outfile2 = corpus_l2[:-4] + "_lines.txt"


def sentence_dictionary(inf):
    """
    reads in sentences from input corpus files and save to dictionary
    """
    xml = ET.parse(inf)
    corpus_sents = dict()
    sents = xml.xpath(".//s")
    for sent in sents:
        corpus_sents[sent.attrib["id"]] = " ".join([word.text for word in sent.getchildren()])
    return corpus_sents

d1 = sentence_dictionary(corpus_l1)
d2 = sentence_dictionary(corpus_l2)

## for testing
# print(d1)
# print(d2)

##############################################################################

with open(outfile1, "w", encoding="utf8") as outf1, open(outfile2, "w", encoding="utf8") as outf2:
    alignments = ET.parse(alignment_file)
    grps = alignments.xpath("./linkGrp")
    for grp in grps:
        l1_a_id = grp.attrib["xtargets"].split(";")[0]
        l2_a_id = grp.attrib["xtargets"].split(";")[1]
        links = grp.getchildren()
        for link in links:

            s_ids = link.attrib["xtargets"]

            if link.attrib["type"] == "1-1":
                left = s_ids.split(";")[0]
                right = s_ids.split(";")[1]
                try:
                    l1_line = "{}\n".format(d1[l1_a_id + "-" + left])
                    l2_line = "{}\n".format(d2[l2_a_id + "-" + right])

                except KeyError:
                    print("Failed to find alignment for for {};{}, {};{}".format(l1_a_id, l2_a_id, left, right))
                    l1_line = ''
                    l2_line = ''

                if l1_line and l2_line:
                    outf1.write(l1_line)
                    outf2.write(l2_line)

            elif link.attrib["type"] == "1-2":
                left = s_ids.split(";")[0].split()
                right = s_ids.split(";")[1]
                try:
                    l1_line = "{}\t{}\n".format(d1[l1_a_id + "-" + left[0]], d1[l1_a_id + "-" + left[1]])
                    l2_line = "{}\n".format(d2[l2_a_id + "-" + right])

                except KeyError:
                    print("Failed to find alignment for {};{}, {};{}".format(l1_a_id, l2_a_id, " ".join(left), right))
                    l1_line = ''
                    l2_line = ''

                if l1_line and l2_line:
                    outf1.write(l1_line)
                    outf2.write(l2_line)

            elif link.attrib["type"] == "2-1":
                left = s_ids.split(";")[0]
                right = s_ids.split(";")[1].split()
                try:
                    l1_line = "{}\n".format(d1[l1_a_id + "-" + left])
                    l2_line = "{}\t{}\n".format(d2[l2_a_id + "-" + right[0]], d2[l2_a_id + "-" + right[1]])

                except KeyError:
                    print("Failed to find alignment for {};{}, {};{}".format(l1_a_id, l2_a_id, left, " ".join(right)))
                    l1_line = ''
                    l2_line = ''

                if l1_line and l2_line:
                    outf1.write(l1_line)
                    outf2.write(l2_line)

##############################################################################
