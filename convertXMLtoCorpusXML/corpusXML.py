#!/usr/bin/python3
# -*- coding: utf-8 -*-

# Author: Tannon Kew <tannon.kew@uzh.ch>

###############################################################################
## Converts unprocessed corpus xml file to tagged and annotated corpus xml format (3-column format, e.g. <w id="a1-s8-w5" pos="ART" lemma="eine">ein</w>
## See below for expected input/output format.
## ToRun: pyhton3 corpusXML.py -i <input_file_path> -o <output_file_path>
###############################################################################

import re
import argparse
import pathlib
import nltk # for tokenizing sentences
# import langid # language identification
from lxml import etree
import langdetect # language identification
import Cutter # https://pub.cl.uzh.ch/wiki/public/cutter/start
import treetaggerwrapper as TT # https://treetaggerwrapper.readthedocs.io/en/latest/
from subprocess import call
import time

###############################################################################

# initialise lang-specific cutters
de_cutter = Cutter.Cutter(profile='de')
en_cutter = Cutter.Cutter(profile='en')
fr_cutter = Cutter.Cutter(profile='fr')

# initialise lang-specific taggers and specify parameter files for each
de_tagger = TT.TreeTagger(TAGLANG='de', TAGOPT="-prob -threshold 0.7 -token -lemma -sgml -quiet", TAGPARFILE='/Applications/Tree-Tagger/lib/german.par')
en_tagger = TT.TreeTagger(TAGLANG='en', TAGOPT="-prob -threshold 0.7 -token -lemma -sgml -quiet", TAGPARFILE='/Applications/Tree-Tagger/lib/english.par')
fr_tagger = TT.TreeTagger(TAGLANG='fr', TAGOPT="-prob -threshold 0.7 -token -lemma -sgml -quiet", TAGPARFILE='/Applications/Tree-Tagger/lib/french.par')

###############################################################################

ap = argparse.ArgumentParser(description="Script for converting content xml files to annotated corpus format xml files for SNF Horizonte corpus.\n")

ap.add_argument("-i", "--input",  required=True, help="Path to a single XML input file for processing OR path to a directory containing multiple files for bulk processing")

ap.add_argument("-o", "--outpath", required=True, help="path to directory for output files.")

args = ap.parse_args()

###############################################################################

parser = etree.XMLParser(remove_blank_text=True, encoding="utf-8") # for parsing xml with utf-8 encoding and removing blank text

def process_file(f, lang):
    """
    :param f: file for processing
    :param lang: language id of current file (de, en or fr)
    """
    tree = etree.parse(f, parser)
    articles = tree.xpath(".//article")

    for article in articles:
        try:
            article_id = article.attrib["id"]
        except KeyError: # if not attribute "id", tag is opening/closing tag and has no contents, so skip, e.g. comic in issue 96
            continue

        paras = article.xpath("./div")

        sentence_counter = 0

        for para in paras:
            para.tag = "p"

            sents = sent_tokenize(para.text, lang)
            para.text = '' # delete text from para tag

            for sent in sents:
                sentence_counter += 1 # increment counter for id
                sentence_elem = etree.SubElement(para, "s") # create element
                sent_id = article_id + "-s" + str(sentence_counter) # set sent id
                sentence_elem.set("id", sent_id) # add sentence id attribute
                sent_lang_id = identify_language(sent, lang) # classify lang
                sentence_elem.set("lang", sent_lang_id) # add lang attribute
                sent = normalise_chars(sent) # normalise sent
                tokens = tokenize(sent, sent_lang_id) # tokenize sent
                tagged_tokens = tag_sentence(tokens, sent_lang_id) # tag sent
                # initialise token counter for token ids
                token_count = 0
                for token in tagged_tokens:
                    try:
                        token_count += 1 # increment token counter
                        token_elem = etree.SubElement(sentence_elem, "w") # create element
                        token_id = sent_id + "-w" + str(token_count) # set token id
                        token_elem.set("id", token_id) # add id attibute
                        token_elem.set("pos", token.pos) # add pos attibute
                        token_elem.set("lemma", (format_unknown_lemmas(token.lemma))) # add lemma attibute
                        token_elem.text = token.word # add text to element
                    except AttributeError:
                        print("ATTRIBUTE ERROR RAISED:", token)
                        pass
    return tree

def format_unknown_lemmas(lemma):
    """
    Replace standard TreeTagger unknown lemma with 'unk'
    :para: lemma tag assigned by TreeTagger
    """
    if lemma == "&lt;unknown&gt;" or lemma == "<unknown>":
        lemma = "unk"
        return lemma
    else:
        return lemma

def sent_tokenize(text, lang):
    """
    Return a sentence-tokenized copy of *text*, using NLTK's recommended sentence tokenizer (currently :class:`.PunktSentenceTokenizer` for the specified language).
    :param text: text to split into sentences
    :param language: language of text string
    """
    lang_map = {"de": "german", "en": "english", "fr":"french"}
    tokenizer = nltk.data.load('tokenizers/punkt/{0}.pickle'.format(lang_map[lang]))
    return tokenizer.tokenize(text)

def tokenize(text, lang):
    """
    Tokenize a given string with language specific instance of cutter
    :param text: text to tokenize
    :param language: language of text string
    """
    if lang == 'de':
        tokenized_sent = [token[0] for token in de_cutter.cut(text)]
    elif lang == 'fr':
        tokenized_sent = [token[0] for token in fr_cutter.cut(text)]
    else:
        tokenized_sent = [token[0] for token in en_cutter.cut(text)] # default if language code != de or fr
    return tokenized_sent

def identify_language(text, lang):
    """
    Identify the language of a given string
    :param text: text to identify
    :param language: language of document. Returned by default if text string is too short to reliably use langdetect
    """

    # if string is longer than 32 characters do language identification
    if len(text) > 32 and not text.split()[0] in ["Bild:", "Picture:", "Photo:", "|"]:
        detected_lang = ''
        try:
            for i in langdetect.detect_langs(text):
                # restrict selection to either DE, EN or FR
                if i.lang in ('de', 'en', 'fr'):
                    return i.lang
                else:
                    return lang
        except langdetect.lang_detect_exception.LangDetectException:
            print("\tNo features found for language detection on following string:\n\t'{}'".format(text))
            return lang
    # else return language of article
    else:
        return lang

def tag_sentence(text, lang):
    """
    Annotate a given string with pos tags and lemmas using Tree-Tagger
    :param text: text to annotate
    :param language: language of text string
    """
    if lang == 'de':
        tagged_sent = de_tagger.tag_text(text, tagonly=True)
    elif lang == 'fr':
        tagged_sent = fr_tagger.tag_text(text, tagonly=True)
    else:
        tagged_sent = en_tagger.tag_text(text, tagonly=True) # default if language code != de, en or fr
    tagged_sent = TT.make_tags(tagged_sent, allow_extra=True)
    # print(tagged_sent)
    return tagged_sent

def normalise_chars(text):
    """
    Normalise special characters (adapted from CS pipeline)
    :param text: text for processing
    """

    text = text.split()

    for i, word in enumerate(text):

        # to ensure lxml does not produce &amp;lt; when saving file
        word = re.sub(r'^(.*)&lt;(.*)$', r'\1<\2', word)
        #word = re.sub(r'^(.*)&amp;(.*)$', r'\1&\2', word) # AS trying to fix the lemma too. right place? nope

        word = re.sub(r'\xa0', ' ', word) # non-breaking whitespace '\xa0'

        # map dashes to - Hyphen-Minus U+002D
        word = re.sub(r'^(.*)–(.*)$', r'\1-\2', word) # En Dash U+2013
        word = re.sub(r'^(.*)—(.*)$', r'\1-\2', word) # Em Dash U+2014
        word = re.sub(r'^(.*)‒(.*)$', r'\1-\2', word) # Figure Dash U+2012
        word = re.sub(r'^(.*)‐(.*)$', r'\1-\2', word) # Hyphen U+2010
        word = re.sub(r'^(.*)⁃(.*)$', r'\1-\2', word) # Hyphen Bullet U+2043
        word = re.sub(r'^(.*)﹣(.*)$', r'\1-\2', word) # Small Hyphen-Minus U+FE63
        word = re.sub(r'^(.*)－(.*)$', r'\1-\2', word) # Fullwidth Hyphen-Minus U+FF0D

        # map apostrophes to ' Apostrophe U+0027
        word = re.sub(r'^(.*)’(.*)$', r"\1'\2", word) # Right Single Quotation Mark U+2019
        word = re.sub(r'^(.*)‘(.*)$', r"\1'\2", word) # Left Single Quotation Mark U+2018
        word = re.sub(r'^(.*)‚(.*)$', r"\1'\2", word) # Single Low-9 Quotation Mark U+201A
        word = re.sub(r'^(.*)‛(.*)$', r"\1'\2", word) # Single High-Reversed-9 Quotation Mark U+201B
        word = re.sub(r'^(.*)‹(.*)$', r"\1'\2", word) # Single Left-Pointing Angle Quotation Mark U+2039
        word = re.sub(r'^(.*)›(.*)$', r"\1'\2", word) # Single Right-Pointing Angle Quotation Mark U+203A
        word = re.sub(r'^(.*)<(.*)$', r"\1'\2", word) # Single less than
        word = re.sub(r'^(.*)>(.*)$', r"\1'\2", word) # Single greater than

        # map quotation marks to " Quotation Mark U+0022
        word = re.sub(r'^(.*)“(.*)$', r'\1"\2', word) # Left Double Quotation Mark U+201C
        word = re.sub(r'^(.*)‟(.*)$', r'\1"\2', word) # Double High-Reversed-9 Quotation Mark U+201F
        word = re.sub(r'^(.*)”(.*)$', r'\1"\2', word) # Right Double Quotation Mark U+201D
        word = re.sub(r'^(.*)„(.*)$', r'\1"\2', word) # Double Low-9 Quotation Mark U+201E
        word = re.sub(r'^(.*)〝(.*)$', r'\1"\2', word) # Reversed Double Prime Quotation Mark U+301D
        word = re.sub(r'^(.*)〞(.*)$', r'\1"\2', word) # Double Prime Quotation Mark U+301E
        word = re.sub(r'^(.*)〟(.*)$', r'\1"\2', word) # Low Double Prime Quotation Mark U+301F
        word = re.sub(r'^(.*)«(.*)$', r'\1"\2', word) # Left-Pointing Double Angle Quotation Mark U+00AB
        word = re.sub(r'^(.*)»(.*)$', r'\1"\2', word) # Right-Pointing Double Angle Quotation Mark U+00BB
        if word:
            text[i] = word
        else:
            del text[i]

    return ' '.join(text).strip()

def write_output(tree, outfile):
    """
    Write the new tree to the output file.
    :param tree: collection of article elements in valid xml (_ElementTree)
    :output_file: output file for writing (file_object)
    """
    # tree_element = etree.ElementTree(tree)
    tree.write(outfile, pretty_print=True, xml_declaration=True, encoding="utf-8")

    call(["xmllint", "--format", outfile, "--output", outfile[:-4]+".tmp.xml", "--encode", "utf-8"])
    call(["mv", outfile[:-4]+".tmp.xml", outfile])

def main():

    if not pathlib.Path(args.outpath).exists() and not pathlib.Path(args.outpath).is_dir():
        pathlib.Path(args.outpath).mkdir(parents=True)
        print("\nNew directory '{}' created.".format(args.outpath))


    if pathlib.Path(args.input).is_dir():
        for f in sorted(pathlib.Path(args.input).iterdir()):
            if str(f).endswith(".xml"):
                start_time = time.time() # start timer
                infile = str(f)
                file_name = infile.split("/")[-1]
                file_lang = re.search(r'_(de|en|fr).xml', file_name).group(1)
                print("\ncurrently processing {}...".format(file_name))
                processed_tree = process_file(infile, file_lang)
                outfile = str(pathlib.Path(args.outpath) / file_name)
                write_output(processed_tree, outfile)
                elapsed_time = time.time() - start_time
                print("\t{0} processed in {1:.2f} seconds".format(file_name, elapsed_time))
    else:
        infile = str(pathlib.Path(args.input))
        start_time = time.time() # start timer
        file_name = infile.split("/")[-1]
        file_lang = re.search(r'_(de|en|fr).xml', file_name).group(1)
        print("\nProcessing {}...".format(file_name))
        processed_tree = process_file(infile, file_lang)
        outfile = str(pathlib.Path(args.outpath) / file_name)
        write_output(processed_tree, outfile)
        elapsed_time = time.time() - start_time
        print("\t{0} processed in {1:.2f} seconds".format(file_name, elapsed_time))

################################################################################

if __name__ == "__main__":
    main()

###############################################################################

# Expected input example:
"""
<corpus>
  <article id="a1" name="2016-08-28_Daniel-Saraga_a1_Die-Barrieren-niederreissen">
    <div class="title">Die Barrieren niederreissen</div>
    <div class="date">28. August 2016</div>
    <div class="author">Daniel Saraga</div>
    <div class="abstract">Die Open-Science-Bewegung möchte mehr Forschende dazu bewegen, ihre Daten zu teilen. Das Ziel: Die Wissenschaft effizienter, nützlicher und zuverlässiger zu machen.
"""

# Target output example:
"""
<corpus>
  <article id="a1" cross_lang_id="cs-2001-06-18-Euro-Cash--No-golden-days-for-forgers">
    <h1 category="Europe">
      <s id="a1-s1" lang="de">
        <w id="a1-s1-w1" pos="NN" lemma="Euro-Bargeld">Euro-Bargeld</w>
        <w id="a1-s1-w2" pos="$." lemma=":">:</w>
      </s>
      <s id="a1-s2" lang="de">
        <w id="a1-s2-w1" pos="PIAT" lemma="kein">Keine</w>
        <w id="a1-s2-w2" pos="NN" lemma="Blütezeit">Blütezeit</w>
        <w id="a1-s2-w3" pos="APPR" lemma="für">für</w>
        <w id="a1-s2-w4" pos="NN" lemma="Blüte">Blüten</w>
      </s>
    </h1>
    <p class="date">
      <s id="a1-s3" lang="de">
        <w id="a1-s3-w1" pos="CARD" lemma="@card@">18.06.2001</w>
      </s>
    </p>
    <p class="abstract">
      <s id="a1-s4" lang="de">
        <w id="a1-s4-w1" pos="APPRART" lemma="an">Am</w>
        <w id="a1-s4-w2" pos="ADJA" lemma="@ord@">1.</w>
        <w id="a1-s4-w3" pos="NN" lemma="Januar">Januar</w>
        <w id="a1-s4-w4" pos="CARD" lemma="@card@">2002</w>
        <w id="a1-s4-w5" pos="VAFIN" lemma="sein">ist</w>
        <w id="a1-s4-w6" pos="PPER" lemma="es">es</w>
        <w id="a1-s4-w7" pos="ADV" lemma="soweit">soweit</w>
        <w id="a1-s4-w8" pos="$." lemma=":">:</w>
      </s>
      <s id="a1-s5" lang="de">
        <w id="a1-s5-w1" pos="ART" lemma="d">Das</w>
        <w id="a1-s5-w2" pos="NN" lemma="Eurobargeld">Eurobargeld</w>
        <w id="a1-s5-w3" pos="VAFIN" lemma="werden">wird</w>
        <w id="a1-s5-w4" pos="APPR" lemma="in">in</w>
        <w id="a1-s5-w5" pos="ART" lemma="d">den</w>
        <w id="a1-s5-w6" pos="CARD" lemma="zwölf">zwölf</w>
        <w id="a1-s5-w7" pos="NN" lemma="Land">Ländern</w>
        <w id="a1-s5-w8" pos="ART" lemma="d">der</w>
        <w id="a1-s5-w9" pos="ADJA" lemma="europäisch">europäischen</w>
        <w id="a1-s5-w10" pos="NN" lemma="Währungsunion">Währungsunion</w>
        <w id="a1-s5-w11" pos="VVPP" lemma="einführen">eingeführt</w>
        <w id="a1-s5-w12" pos="$." lemma=".">.</w>
      </s>
"""
