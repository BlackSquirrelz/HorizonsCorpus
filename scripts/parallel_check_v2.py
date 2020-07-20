#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Check parallel article for html files scraped from SNF Horizonte Online
# Author: Tannon Kew

# import pathlib
import sys
import os

# path_de = "/Users/tannon/switchdrive/Horizonte/Tannon/convertHTMLtoXML/SNF_html_files/SNF_html_files_rn_de"
#
# path_fr = "/Users/tannon/switchdrive/Horizonte/Tannon/convertHTMLtoXML/SNF_html_files/SNF_html_files_rn_fr"
#
# path_en = "/Users/tannon/switchdrive/Horizonte/Tannon/convertHTMLtoXML/SNF_html_files/SNF_html_files_rn_en"

p1 = sys.argv[1]
p2 = sys.argv[2]
p3 = sys.argv[3]

def get_file_info(f):
    id = f.split('/')[-1].split('_')[0]
    date = f.split('/')[-1].split('_')[1]
    auth = f.split('/')[-1].split('_')[2]
    title = f.split('/')[-1].split('_')[3]
    return [id, date, auth, title]

def check_files(p1, p2, p3):
    # uniq = list()
    file_count = 0
    problematic = []
    for i in range(len(os.listdir(p1))):

        # f1 = pathlib.Path(p1).listdir()[i])
        # f2 = pathlib.Path(p2).listdir()[i])
        # f3 = pathlib.Path(p3).listdir()[i])
        f1 = sorted(os.listdir(p1))[i]
        f2 = sorted(os.listdir(p2))[i]
        f3 = sorted(os.listdir(p3))[i]
        # for f2 in sorted(pathlib.Path(p2).iterdir()):
        #     for f3 in sorted(pathlib.Path(p3).iterdir()):
        file_count += 1

        f1 = str(f1)
        f2 = str(f2)
        f3 = str(f3)

        f1_info = get_file_info(f1)
        f2_info = get_file_info(f2)
        f3_info = get_file_info(f3)

        # conditions aren't right...
        if f1_info[1] == f2_info[1] or f1_info[1] == f3_info[1] or f2_info[1] == f3_info[1]:
            if f1_info[2] == f2_info[2] or f1_info[2] == f3_info[2] or f2_info[2] == f3_info[2]:
                problematic.append(f1_info)
                problematic.append(f2_info)
                problematic.append(f3_info)
        else:
            print("Checked {} files".format(file_count))

    if len(problematic) == 0:
        print("Files aligned")
    for i in problematic:
        print(i)
        # element = "_".join(str(file).split('/')[-1].split('_')[0])
        # id = str(file).split('/')[-1].split('_')[0]
        # date = str(file).split('/')[-1].split('_')[1]
        # auth = str(file).split('/')[-1].split('_')[2]
        # print(element)
        # if element in uniq:
        #     print(str(file).split('/')[-1])
        # else:
        #     uniq.append(element)

    # print(file_count)
    # print(len(uniq))

# check_files(pathlib.Path(p1), pathlib.Path(p2), pathlib.Path(p3))
    # print()
check_files(p1, p2, p3)
    # print()
