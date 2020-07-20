#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import etree
import pathlib

# print(len("horizonte_2007_72"))
# de = "horizonte_2007_72_de"
# fr = "horizonte_2007_72_fr"
# print(de[:17], fr[:17])


de_files = pathlib.Path("/Users/tannon/switchdrive/Horizonte/Tannon/scratch/horizonte_validated_article_boundaries_de")

fr_files = pathlib.Path("/Users/tannon/switchdrive/Horizonte/Tannon/scratch/horizonte_validated_article_boundaries_fr")

def parallel_check(file_dir1, file_dir2):
    c = 0
    for f in sorted(file_dir1.iterdir()):
        if str(f).endswith(".xml"):
            a_count = 0
            fname = str(f).split("/")[-1]
            f = etree.iterparse(str(f))
            for _, elem in f:
                if elem.tag == "Article":
                    a_count += 1
            de = (fname, a_count)
            # print(fname)
            fr = check(fname, file_dir2)
            # print("{} : {}\t{} : {}".format(de[0][:21], de[1], fr[0][:21], fr[1]))
            if de[1] != fr[1]:
                c += 1
                print("{} : {}\t{} : {}".format(de[0][:21], de[1], fr[0][:21], fr[1]))
    if c == 0:
        print("Matching number of articles in all files.")


def check(current_file, file_dir2):
    for f in sorted(file_dir2.iterdir()):
        # print(fname)
        # print(current_file)
        if str(f).split("/")[-1][:18] == current_file[:18]:
            fname = str(f).split("/")[-1]
            a_count = 0
            f = etree.iterparse(str(f))
            for _, elem in f:
                if elem.tag == "Article":
                    a_count += 1

            return (fname, a_count)

parallel_check(de_files, fr_files)
