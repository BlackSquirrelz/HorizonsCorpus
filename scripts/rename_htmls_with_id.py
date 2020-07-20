#!/usr/bin/env python3
# -*- coding: utf8 -*-

# Author: Tannon Kew
# SNF Horizonte corpus

import pathlib
import sys

# specify paths for input and output files
in_path = sys.argv[1]
out_path = sys.argv[2]

def rewrite(inpath, outpath):
    """
    Rewrites filenames from "date_author_title" to "date_author_uniqueID_title"
    id is in the form of a1 to aN
    """
    counter = 0

    outfilepath = pathlib.Path(outpath)
    outfilepath.mkdir(parents=True, exist_ok=True)

    for file in sorted(pathlib.Path(inpath).iterdir()):
        counter += 1
        fn = str(file).split("/")[-1]
        fn_mod = fn.split("_")
        fn_new = fn_mod[0] + "_" + fn_mod[1] + "_a" + str(counter) + "_" + fn_mod[2]

        outfile = outfilepath / fn_new
        with open(file, "r", encoding="utf8") as inf:
            with open(outfile, "w+") as outf:
                outf.write(inf.read())

rewrite(in_path, out_path)
