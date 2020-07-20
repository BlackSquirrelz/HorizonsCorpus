#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Check parallel article for html files scraped from SNF Horizonte Online
# Author: Tannon Kew

import pathlib
import sys

path_de = "/Users/tannon/switchdrive/Horizonte/Tannon/convertHTMLtoXML/SNF_html_files/SNF_html_files_rn_de"

path_fr = "/Users/tannon/switchdrive/Horizonte/Tannon/convertHTMLtoXML/SNF_html_files/SNF_html_files_rn_fr"

path_en = "/Users/tannon/switchdrive/Horizonte/Tannon/convertHTMLtoXML/SNF_html_files/SNF_html_files_rn_en"

def check_files(pfad):

    uniq = list()
    file_count = 0

    for file in sorted(pathlib.Path(pfad).iterdir()):
        file_count += 1
        element = "_".join(str(file).split('/')[-1].split('_')[:3])
        if element in uniq:
            print(str(file).split('/')[-1])
        else:
            uniq.append(element)

    print(file_count)
    print(len(uniq))


check_files(path_de)
print()
check_files(path_en)
print()
check_files(path_fr)
