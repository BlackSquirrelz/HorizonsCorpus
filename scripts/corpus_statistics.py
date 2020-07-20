# !/usr/bin/env python3
# -*- coding: utf8 -*-


from lxml import etree
import argparse
import pathlib
from collections import defaultdict, Counter, namedtuple
import re
import time

de_tags = {"NN": "noun", "ADJA": "adjective", "ADJD": "adjective", "CARD": "number", "FM": "foreign word", "V": "verb"}

en_tags = {"NN": "noun", "NN": "noun", "JJ": "adjective", "CD": "number", "FW": "foreign word", "V": "verb"}
# JJ Adjective
# JJR Adjective, comparative
# JJS Adjective, superlative
# NN Noun, singular or mass
# NNS Noun, plural

fr_tags = {"NOM": "noun", "ADJ": "adjective", "NUM": "number", "VER": "verb"}

###############################################################################

ap = argparse.ArgumentParser(description="Script for extracting corpus statistics from input corpus.\n")

ap.add_argument("-i", "--input",  required=True, help="Path to a single XML input file for processing OR path to a directory containing multiple files for bulk processing")

# ap.add_argument("-o", "--outpath", required=True, help="path to directory for output files.")

args = ap.parse_args()

###############################################################################

class CorpusXML:
    parser = etree.XMLParser(remove_blank_text=True, encoding="utf-8") # for parsing xml with utf-8 encoding and removing blank text

    def __init__(self, xml):
        self.corpus = etree.parse(xml, self.parser)
        self.filename = xml.split('/')[-1]
        self.file_lang = re.search('_(de|en|fr)', self.filename).group(1)

    def show_deatails(self):
        print(self.filename)

    def count_articles(self):
        return len(self.corpus.xpath('.//article'))

    def count_paragraphs(self):
        return len(self.corpus.xpath('.//p'))

    def count_sentences(self):
        return len(self.corpus.xpath('.//s'))

    def count_tokens(self):
        return len(self.corpus.xpath('.//w'))

    def count_types(self):
        return len(set(self.get_types()))

    def get_types(self):
        types = Counter(tok.text for tok in self.corpus.xpath('.//w'))
        return types

    def count_lemmas(self):
        return len(set(self.get_lemmas()))

    def get_lemmas(self):
        lemmas = Counter(tok.attrib["lemma"] for tok in self.corpus.xpath('.//w'))
        return lemmas

    def get_pos(self):
        noun = Counter()
        adj = Counter()
        num = 0
        foreign = 0
        verb = Counter()

        if self.file_lang == 'de':

            for tok in self.corpus.xpath('.//w'):
                if tok.attrib['pos'] == 'NN': # noun
                    noun[tok.attrib['lemma']] += 1
                elif 'ADJ' in tok.attrib['pos']: # ADJA or ADJD
                    adj[tok.attrib['lemma']] += 1
                elif tok.attrib['pos'] == 'CARD': # number
                    num += 1
                elif tok.attrib['pos'] == 'FM': # foreign word
                    foreign += 1
                elif 'V' in tok.attrib['pos'][0]:
                    verb[tok.attrib['lemma']] += 1

        elif self.file_lang == 'fr':

            for tok in self.corpus.xpath('.//w'):
                if tok.attrib['pos'] == 'NOM': # noun
                    noun[tok.attrib['lemma']] += 1
                elif tok.attrib['pos'] == 'ADJ': # adjective
                    adj[tok.attrib['lemma']] += 1
                elif tok.attrib['pos'] == 'NUM': # number
                    num += 1
                # elif tok.attrib['pos'] == 'FM': # foreign word
                    # foreign[tok.attrib['lemma']] += 1
                elif 'VER' in tok.attrib['pos']:
                    verb[tok.attrib['lemma']] += 1

        elif self.file_lang == 'en':
            for tok in self.corpus.xpath('.//w'):
                if tok.attrib['pos'] in ['NN', 'NNS']: # noun
                    noun[tok.attrib['lemma']] += 1
                elif tok.attrib['pos'] in ['JJ', 'JJR', 'JJS']: # ADJA or ADJD
                    adj[tok.attrib['lemma']] += 1
                elif tok.attrib['pos'] == 'CD': # number
                    num += 1
                elif tok.attrib['pos'] == 'FW': # foreign word
                    foreign += 1
                elif 'V' in tok.attrib['pos'][0]: # verb
                    verb[tok.attrib['lemma']] += 1

        # create named tuple
        POS = namedtuple('POS', 'nouns adjectives numbers foreigners verbs')

        pos = POS(nouns=noun, adjectives=adj, numbers=num, foreigners=foreign, verbs=verb)

        return pos

    def count_unknown(self):
        unk = 0
        for token in self.corpus.xpath('.//w'):
            if token.attrib['lemma'] == 'unk':
                unk += 1
        return unk

    def code_switching(self):
        foreign_sents = 0
        for s in self.corpus.xpath('.//s'):
            if s.attrib['lang'] != self.file_lang:
                foreign_sents += 1
        return foreign_sents

    def get_potential_errors(self):
        c = 0
        articles = self.corpus.xpath('.//article')
        for article in articles:
            try:
                if article.attrib['potential_errors'] != 'false':
                    c += 1
            except KeyError: # attribute not supplied
                # print(article.attrib, self.filename)
                pass
        return c


def get_stats_for_single_corpus(file):
    start_time = time.time() # start timer
    c = CorpusXML(file)
    print("collecting stats for {}".format(c.filename), c.file_lang)
    article_count = c.count_articles()
    para_count = c.count_paragraphs()
    sent_count = c.count_sentences()
    tok_count = c.count_tokens()
    type_count = c.count_types()
    types = c.get_types()
    lemmas = c.get_lemmas()
    unknowns = c.count_unknown()
    foreign_sents = c.code_switching()
    pos = c.get_pos()
    nouns = pos.nouns
    adjectives = pos.adjectives
    verbs = pos.verbs
    numbers = pos.numbers
    foreigners = pos.foreigners
    potential_errors = c.get_potential_errors()

    elapsed_time = time.time() - start_time
    print("\nstatistics for '{0}' completed in {1:.2f} seconds\n".format(c.filename, elapsed_time))

    print_stats(article_count, para_count, sent_count, tok_count, types, lemmas, unknowns, foreign_sents, nouns, adjectives, verbs, numbers, foreigners, potential_errors)

def get_stats_for_multiple_files(filepath):
    start_time = time.time() # start timer

    articles = 0
    paragraphs = 0
    sents = 0
    tokens = 0
    types = Counter()
    lemmas = Counter()
    unknowns = 0
    foreign_sents = 0
    nouns = Counter()
    adjectives = Counter()
    verbs = Counter()
    numbers = 0
    foreigners = 0
    potential_errors = 0

    for f in sorted(filepath.iterdir()):
        c = CorpusXML(str(f))
        # print("\ncurrently processing {}...".format(c.filename))
        articles += c.count_articles()
        paragraphs += c.count_paragraphs()
        sents += c.count_sentences()
        tokens += c.count_tokens()
        types += c.get_types()
        lemmas += c.get_lemmas()
        unknowns += c.count_unknown()
        foreign_sents += c.code_switching()
        pos = c.get_pos()
        nouns += pos.nouns
        adjectives += pos.adjectives
        verbs += pos.verbs
        numbers += pos.numbers
        foreigners += pos.foreigners
        potential_errors += c.get_potential_errors()


    elapsed_time = time.time() - start_time
    print("\nstatistics for files in {0} completed in {1:.2f} seconds\n".format(str(filepath), elapsed_time))

    print_stats(articles, paragraphs, sents, tokens, types, lemmas, unknowns, foreign_sents, nouns, adjectives, verbs, numbers, foreigners, potential_errors)

def print_stats(articles, paragraphs, sents, tokens, types, lemmas, unknowns, foreign_sents, nouns, adjectives, verbs, numbers, foreigners, potential_errors):
    print("articles:\t{}".format(articles))
    print("paragraphs:\t{}".format(paragraphs))
    print("sentences:\t{}".format(sents))
    print("foreign sentences:\t{}".format(foreign_sents))
    print("tokens:\t{}".format(tokens))
    print("token types:\t{}".format(len(types))) #, list(types)[-10:])
    print("lemma types:\t{}".format(len(lemmas))) #, list(lemmas)[-10:])
    print("unknown lemmas:\t{}".format(unknowns))

    print("noun types:\t{}".format(len(nouns)))
    # print("most common nouns:", nouns.most_common(20))
    print("adj types:\t{}".format(len(adjectives)))
    # print("most common adjectives:", adjectives.most_common(20))
    print("verb types:\t{}".format(len(verbs)))
    # print("most common verbs:", verbs.most_common(20))
    print("numbers:\t{}".format(numbers))
    print("foreign words:\t{}".format(foreigners))
    print("potential errors:\t{}".format(potential_errors))
    print("error percentage:\t{0:.2f}%".format((potential_errors/articles)*100))

def main():

    if pathlib.Path(args.input).is_dir():
        get_stats_for_multiple_files(pathlib.Path(args.input))
    else:
        get_stats_for_single_corpus(str(pathlib.Path(args.input)))

if __name__ == '__main__':
    main()
