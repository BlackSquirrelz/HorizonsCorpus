#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import etree
import pathlib
import sys
from subprocess import call

inpath = sys.argv[1]
outpath = sys.argv[2]

def xml_lint(outfile):
    call(["xmllint", "--format", outfile, "--output", outfile[:-4]+".tmp.xml", "--encode", "utf-8"])
    call(["mv", outfile[:-4]+".tmp.xml", outfile])

if not pathlib.Path(outpath).exists() and not pathlib.Path(outpath).is_dir():
    pathlib.Path(outpath).mkdir(parents=True)
    print("\nNew directory '{}' created.".format(outpath))

for file in sorted(pathlib.Path(inpath).iterdir()):
    infile = str(file)
    if infile.endswith(".xml"):
        filename = infile.split("/")[-1]
        filename = "_".join(filename.split("_")[:4])+".xml"
        outfile = outpath + "/" + filename
        with open(infile, "r", encoding="utf8") as inf:
            with open(outfile, "w+", encoding="utf8") as outf:
                for line in inf:
                    if line.startswith("<Document document_id"):
                        print(line)
                        line = line.replace('_NNS_article_boundaries.xml"', '"')
                        line = line.replace('>', ' type="article_boundaries">')
                        print(line)
                        outf.write(line)
                    else:
                        outf.write(line)

        xml_lint(outfile)




# <Document document_id="horizonte_2014_103_de_NNS_article_boundaries.xml">

# <Document document_id="horizonte_2016_110_de" type="article_boundaries">
