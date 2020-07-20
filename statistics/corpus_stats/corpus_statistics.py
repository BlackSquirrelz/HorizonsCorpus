#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import etree
import pathlib
import sys
from collections import defaultdict
import spacy


def inspect_file(infile):
    xml_file = etree.iterparse(infile)

    article_count = 0
    token_count = 0
    vocabulary = defaultdict(int)

    for _, elem in xml_file:
        if elem.tag == "Article":
            article_count += 1

        if elem.tag == "Text" and elem.text:
            token_count += 1
            # print(elem.text)
            vocabulary[elem.text.lower()] += 1

    return (article_count, token_count, vocabulary)


def get_overview(file_dir):

    issue_count, tot_article_count, tot_token_count = 0, 0, 0
    total_vocabulary = defaultdict(int)

    for file in file_dir.iterdir():
        file = str(file)
        if file.endswith(".xml"):
            issue_count += 1
            art_article_count, art_token_count, art_vocabulary = inspect_file(file)
            tot_article_count += art_article_count
            tot_token_count += art_token_count
            for k, v in art_vocabulary.items():
                total_vocabulary[k] += v
        else:
            # print("{} not processed".format(file))
            pass

    vocab_sorted = sorted(total_vocabulary.items(), key=lambda x: x[1], reverse=True)

    rebuilt_vocabulary = {k: i for k, i in vocab_sorted}

    return issue_count, tot_article_count, tot_token_count, rebuilt_vocabulary

def process_vocabulary(vocab_dict, stop_words):
    count = 0

    for k, v in vocab_dict.items():
        if len(k) > 1 and k.lower() not in stop_words and not k.isdigit() and k.isalpha():
            print("{} : {}".format(k, v))
            count += 1

            if count > 100:
                break

def main():
    input_dir = pathlib.Path(sys.argv[1])
    

    if not input_dir.is_dir():
        print("Invalid input directory.")
        sys.exit(0)
    else:
        lang = str(input_dir)[-2:]

        nlp = spacy.load(lang)

        sw = nlp.Defaults.stop_words
        # print(sw)

        issues, articles, tokens, vocabulary = get_overview(input_dir)
        print("Number of issues in {}   :  {}".format(lang, issues))
        print("Number of articles in {} :  {}".format(lang, articles))
        print("Number of tokens in {}   :  {}".format(lang, tokens))
        print("Number of types in {}    :  {}".format(lang, len(vocabulary)))
        process_vocabulary(vocabulary, sw)


if __name__ == "__main__":
    main()
