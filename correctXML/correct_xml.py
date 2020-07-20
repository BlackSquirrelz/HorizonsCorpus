#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Tannon Kew - Dec 2018
# Horizonte SNF PDF Corpus

###############################################################################
## To run: python3 correct_xml.py [input xml] [directory path for output]
## For efficient processing of multiple files, use a bash loop
## for f in /Users/tannon/switchdrive/Horizonte/SNF_xml_files/horizonte_validated_article_boundaries/en/*.xml; do python3 merge_broken_xml_paras_v5.py $f merged_para_xmls_en/; done
###############################################################################

from subprocess import call
from lxml import etree
from copy import deepcopy
from collections import Counter
import sys
import re
import os
import math
from pre_noun_words_de import pre_noun_words

final_punctuation = ['.', '?', '!', '…']

def denoise(article_tag):
    """
    Removes noisey text from paragraphs and if necessary entire paragraph elements.

    Args:
        article_tag (_Element): article element for processing
    """

    c = 0
    denoised = []

    paras = article_tag.xpath(".//Para")

    for i, para in enumerate(paras):
        tokens = para.xpath(".//Text")

        for token in tokens:
            if token != None:
                # print(token.text)
                glyph_info = token.getnext().xpath('./Glyph')[0]
                # print(glyph_info.tag)
                if float(glyph_info.attrib["size"]) < 8.00 or ("alpha" in glyph_info.attrib and "beta" in glyph_info.attrib):
                    word_elem = token.getparent()
                    denoised.append(token.text)
                    word_elem.getparent().remove(word_elem)
                    c += 1

    for i, para in enumerate(paras):
        if len(para.getchildren()) == 0:
            para.getparent().remove(para)

    # if c > 100:
    #     pass
        # print("Denoising has removed the following tokens:", denoised)
        # article_tag = mark_potential_errors(article_tag)

    return article_tag

def inspect_next_para(p):
    """
    Performs a lookahead opertaion on given p argument

    Args:
        p (_Element): paragraph node

    Returns:
        para_initial (string): first word of paragraph
        font (int): font number of first letter of paragraph
        size (float): font size of first letter of paragraph
    """
    try:
        para_initial = p.xpath(".//Text")[0]
        font = int(para_initial.getnext().xpath("Glyph/@font")[0][1:])
        size = float(para_initial.getnext().xpath("Glyph/@size")[0])
        return para_initial, font, size
    except IndexError:
        return None, None, None

def merge_para_elems(elem1, elem2):
    """
    Merges two nodes by appending all children nodes of elem2 to elem1

    Args:
        elem1 (_Element): paragraph element 1
        elem2 (_Element): paragraph element 2

    Returns:
        elem1 (_Element): paragraph element 1 with appended nodes
    """
    for e in elem2:
        elem1.append(e)
    return elem1

def merge_dropcaps(article_tag, verbose=True):
    """
    Finds loose dropcaps and appends them to the following word.

    Args:
        article_tag (_Element): article element for processing
    """

    paras = article_tag.xpath(".//Para")

    for i, para in enumerate(paras):
        para_glyphs = para.xpath(".//Glyph")

        if i < len(paras)-1 and len(para_glyphs) == 1:
            try:
                if para_glyphs[0].attrib["dropcap"] == "true":

                    dropcap_char = para_glyphs[0]
                    # get following paragraph elem for manipulation
                    follow_para = paras[i+1]
                    # get the first word of para
                    para_initial = follow_para.xpath("./Word/Text")[0]
                    # list of glyph elements in first word of following para

                    para_initial_glyphs = para_initial.getnext().xpath("./Glyph")
                    # insert the dropcap glyph element into list
                    para_initial.getnext().insert(0, dropcap_char) # gets 'Box' element of first word and inserts the dropcap character element into the first position.

                    # replace the text of the first word in para
                    para_initial.text = dropcap_char.text + para_initial.text

                    # remove the paragraph containing only the dropcap character
                    para.getparent().remove(para)

                    if verbose:

                        new_para_text = [t.text for t in paras[i+1].xpath(".//Text")]

                        print("Dropcap merged in {}, '{}', p. {}: {}".format(article_tag.attrib["article_id"], article_tag.attrib["title"][:20]+"...", article_tag.xpath("./Page")[0].attrib["number"], ' '.join(new_para_text[:5])))

            except KeyError:
                pass

    return article_tag


def mark_potential_errors(article_tag):
    """
    Sets potential error flag to true

    Args:
        article_tag (_Element): article element for processing
    """
    article_tag.attrib["potential_errors"] = "true"
    return article_tag

def check_for_odd_dropcaps(article_tag):
    """
    If a dropcap doesn't occur in the first 5 paragraphs of an article, but does occur elsewhere, the article is marked for potential errors.

    Args:
        article_tag (_Element): article element for processing
    """

    pages = article_tag.xpath(".//Page")

    for page in pages:
        paras = article_tag.xpath(".//Para")

        odd_dropcap_found = False

        for i, para in enumerate(paras):
            para_initial_glyph = para.xpath('./Word/Box/Glyph')[0]

            try:
                if para_initial_glyph.attrib["dropcap"] == "true" and i <= 5:
                    # A dropcap appears in the first 5 paragraphs, so it's ok
                    return article_tag

                elif para_initial_glyph.attrib["dropcap"] == "true" and i > 5:
                    # there's no dropcap in the first five paras, mark as potential error
                    article_tag = mark_potential_errors(article_tag)

            except KeyError:
                pass

    return article_tag

def consecutive_merger(article_tag, lang, page_nums, main_font, main_size, verbose=False):
    """
    Performs consecutive paragraph merging.

    Args:
        article_tag (_Element): article element for processing
        lang (string): language code of relevant article, e.g. de, en or fr
        page_nums (set): set of relevant page numbers for the article which will be ignored when merging
        main_font (int): most common font number for relevant article
        main_size (float): most common font size for relevant article
        verbose (bool): if set to True, merges found are printed to stdout

    Returns:
        article_tag (_Element): article element containining merged paragraphs
    """
    paras = article_tag.xpath(".//Para")

    for i, para in enumerate(paras):

        eligible = False

        if i != len(paras)-1:

            try:
                para_final = para.xpath(".//Text")[-1] # get final word of para
                para_final_token = para_final.text
                current_font = int(para_final.getnext().xpath("Glyph/@font")[0][1:]) # get font style of final word (as integer)
                current_size = float(para_final.getnext().xpath("Glyph/@size")[0]) # get size of final word
            except IndexError:
                continue

            # ignore None values
            if not para_final.text:
                # print(para_final.text)
                continue

            # ignore paras with fontsize smaller than 8.00
            elif current_size < 8.00:
                continue

            # 'Vor Ort : Die Stärke...', p. 33: Asmara Addis (Hidden text)
            elif "alpha" in para_final.getnext().xpath('./Glyph')[0].attrib and "beta" in para_final.getnext().xpath('./Glyph')[0].attrib:
                continue

            # ignore page numbers
            # ignore page numbers
            elif para_final.text.isdigit():
                try:
                    if int(para_final.text) in page_nums or article_tag.attrib["title"] == "Inhalt/Sommaire/Contents":
                        eligible = False
                        continue
                    else:
                        eligible = True

                except ValueError: # e.g. ValueError: invalid literal for int() with base 10: '❷'
                    continue

            # if the final paragraph char is punctuation, check to see if it's sentence final. If not, paragraph is eligible for merge.
            elif not para_final.text.isalpha():
                for char in para_final.text.strip():
                    if char in final_punctuation:
                        eligible = False
                        break
                    else:
                        eligible = True

            else:
                eligible = True

            if eligible == True:

                eligible = False

                # check the initial word of following paragraph for font size and style.
                para_initial, fol_font, fol_size = inspect_next_para(paras[i+1])

                # if the following paragraph is no good, don't merge
                if para_initial is None:
                    continue

                # if the following paragraph starts with a potential page number, don't merge
                elif para_initial.text.isdigit():
                    try:
                        if int(para_initial.text) in page_nums or article_tag.attrib["title"] == "Inhalt/Sommaire/Contents":
                            eligible = False
                            continue
                        else:
                            eligible = True
                    except ValueError: # e.g. ValueError: invalid literal for int() with base 10: '❷'
                        continue

                # avoid consecutive merges is initial word is capitalised in EN and FR '• A rapist The general' --> No merge. But "L ' Aucun" --> merge.
                elif lang != 'de' and (para_final.text.isalpha() or para_final.text.isdigit()) and para_initial.text[0].isupper():
                    # print("******************", para_final.text, para_initial.text, article_tag.attrib["article_id"])
                    continue

                # otherwise, perform merge and call the function again
                else:
                    eligible = True

                if eligible == True:
                    if current_font == fol_font and current_size == fol_size:

                        # merge matching paragraphs
                        if verbose:
                            print("Consecutive merge found in {}, '{}', p. {}:".format(article_tag.attrib["article_id"], article_tag.attrib["title"][:20]+"...", article_tag.xpath("./Page")[0].attrib["number"]), para_final.text, para_initial.text)

                        p1 = para_final.getparent().getparent()
                        p2 = para_initial.getparent().getparent()
                        merged = merge_para_elems(p1, p2)
                        p1.getparent().replace(p1, merged)
                        p2.getparent().remove(p2)

                        if verbose:
                            consecutive_merger(article_tag, lang, page_nums, main_font, main_size, verbose=True)
                        else:
                            consecutive_merger(article_tag, lang, page_nums, main_font, main_size, verbose=False)
                    else:
                        continue
            # else:
            #     continue

        # if no more merges are to be performed, return the updated article elem
        else:
            return article_tag

def skip_merger(article_tag, lang, page_nums, main_font, main_size, n_skip, verbose=False):
    """
    Performs skip paragraph merging.

    Args:
        article_tag (_Element): article element for processing
        lang (string): language code of relevant article, e.g. de, en or fr
        main_font (int): most common font number for relevant article
        main_size (float): most common font size for relevant article
        n_skip (int): number of paragraphs to skip
        page_nums (set): set of relevant page numbers for the article which will be ignored when merging
        verbose (bool): if set to True, merges found are printed to stdout

    Returns:
        article_tag (_Element): article element containining merged paragraphs
    """

    paras = article_tag.xpath(".//Para")

    for i, para in enumerate(paras):

        eligible = False

        # ensure there are enough paragraph elements in article
        if i != len(paras)-(n_skip+1) and len(paras) > n_skip:
            try:
                para_final = para.xpath(".//Text")[-1] # get final word of para
                current_font = int(para_final.getnext().xpath("Glyph/@font")[0][1:]) # get font style of final word (as integer)
                current_size = float(para_final.getnext().xpath("Glyph/@size")[0]) # get size of final word

            except IndexError:
                continue

            if not para_final.text:
                continue

            # ignore paras with fontsize smaller than 8.00
            elif current_size < 8.00:
                continue

            # ignore paras with font not equal to main size or main font
            elif current_font != main_font or current_size != main_size:
            #     "********* Caught with font and size conditions ********"
                continue

            # ignore page numbers
            elif para_final.text.isdigit():
                try:
                    if int(para_final.text) in page_nums or article_tag.attrib["title"] == "Inhalt/Sommaire/Contents":
                        eligible = False
                        continue
                    else:
                        eligible = True

                except ValueError:
                    continue

            # if the final paragraph char is punctuation, check to see if it's sentence final. If not, paragraph is eligible for merge.
            elif not para_final.text.isalpha():
                for char in para_final.text.strip():
                    if char in final_punctuation:
                        eligible = False
                        break
                    else:
                        eligible = True

            else:
                eligible = True

            if eligible == True:

                # check the initial word of following paragraph for fontsize. If matches, merge
                para_initial, fol_font, fol_size = inspect_next_para(paras[i+(n_skip+1)])

                if para_initial is None: # if the following paragraph is not good, no merge
                    continue

                # if the following paragraph starts with a potential page number, don't merge
                elif para_initial.text.isdigit():
                    try:
                        if int(para_initial.text) in page_nums or article_tag.attrib["title"] == "Inhalt/Sommaire/Contents":
                            eligible = False
                            continue
                        else:
                            eligible = True
                    except ValueError: # e.g. ValueError: invalid literal for int() with base 10: '❷'
                        continue

                # Special handling for contents page: don't merge paras if following paragraph starts with an assumed page number
                elif article_tag.attrib['title'] == "Inhalt/Sommaire/Contents" and para_initial.text.isdigit():
                    continue

                # avoid catching titles where words are capitalised in English and French.
                elif lang != "de" and para_final.text[0].isupper() and para_initial.text[0].isupper():
                    continue

                # avoid consecutive merges is initial word is capitalised in EN and FR '• A rapist The general' --> No merge. But "L ' Aucun" --> merge.
                elif lang != 'de' and (para_final.text.isalpha() or para_final.text.isdigit()) and para_initial.text[0].isupper():
                    # print("******************", para_final.text, para_initial.text, article_tag.attrib["article_id"])
                    continue

                # Special handling for DE: if the final word of a paragraph is in list of pre_noun_words (common articles and prepositions) a marge is permitted.
                elif lang == "de" and para_initial.text[0].isupper() and  para_final.text.lower() not in pre_noun_words:
                    continue

                else:
                    eligible = True

                if eligible == True:
                    if current_font == fol_font and current_size == fol_size:

                        # merge matching paragraphs
                        if verbose:
                            print("{}-skip merge found in {}, '{}', p. {}:".format(n_skip, article_tag.attrib["article_id"], article_tag.attrib["title"][:20]+"...", article_tag.xpath("./Page")[0].attrib["number"]), para_final.text, para_initial.text)

                        p1 = para_final.getparent().getparent()
                        p2 = para_initial.getparent().getparent()
                        merged = merge_para_elems(p1, p2)
                        p1.getparent().replace(p1, merged)
                        p2.getparent().remove(p2)

                        if verbose:
                            skip_merger(article_tag, lang, page_nums, main_font, main_size, n_skip, verbose=True)
                        else:
                            skip_merger(article_tag, lang, page_nums, main_font, main_size, n_skip, verbose=False)

                    else:
                        continue

        else:
            return article_tag

def count_font_styles(elem):
    """
    Collects font information for an article element.

    Args:
        elem (_Element): article element

    Returns:
        main_font (int): most common font number for article element
        main_size (float): most common font size for article element
    """

    fonts_counter = Counter(elem.xpath(".//Glyph/@font"))
    sizes_counter = Counter(elem.xpath(".//Glyph/@size"))

    main_font = int(fonts_counter.most_common(1)[0][0][1:])
    main_size = float(sizes_counter.most_common(1)[0][0])
    # print("article {}: font: {}, size: {}".format(elem.attrib["article_id"], main_font, main_size))
    return main_font, main_size

def collect_page_numbers(elem):
    """
    Collects potential page numbers relevant for the article which will be ignored when merging paragraphs. A buffer is used to allow for pdfs with page offsets.
    Args:
        elem (_Element): article element

    Returns:
        buffered_nums (set): set of likely page numbers belonging to the article
    """
    p_nums = elem.xpath("./Page/@number")
    buffered_nums = set()

    for num in p_nums:
        buffered_nums.add(int(num))
        buffered_nums.add(int(num)+1)
        buffered_nums.add(int(num)-1)
    # print(buffered_nums)
    return buffered_nums

def write_and_format_outfile(xml_file, out_tree, outpath):
    """Write and format output xml file

    Args:
        xml_file (fileObject): input xml file
        out_tree (_ElementTree): xml tree structure for writing to file
        output (string): local file path for output file

    Effects:
        output file written to output file path
    """
    output_xml = os.path.join(outpath, "_".join(xml_file.split("/")[-1][:-4].split("_")[:4]) + "_corrected.xml")

    out_tree.write(output_xml, pretty_print=True, encoding="utf-8")

    call(["xmllint", "--format",output_xml,"--output", output_xml[:-3]+"format.xml","--encode","utf-8"])
    call(["mv",output_xml[:-3]+"format.xml",output_xml])

###############################################################################

def correct_xml(xml_file, outpath, verbose=True):
    """
    Reads in input xml file and processes for corrections, i.e. merging broken paragraphs

    Args:
        xml_file (fileObject): input xml file for processing
        output (string): local file path for output file
        verbose (bool): if set to True, processing steps are printed to stdout

    """
    in_tree = etree.parse(xml_file)
    root = in_tree.getroot()

    lang = re.search(r'(de|fr|en)', xml_file).group(1)
    # print(lang)

    # doc_id is expected to be 'horizonte_2005_66_de_NNS_article_boundaries.xml'
    doc_id = root.attrib["document_id"].split('_')[:4]

    new_root = etree.Element(root.tag.lower())
    new_root.attrib["document_id"] = doc_id

    articles = root.xpath(".//Article")

    for article in articles:

        article.attrib["potential_errors"] = "false"

        main_font, main_size = count_font_styles(article)

        page_nums = collect_page_numbers(article)

        article = merge_dropcaps(article)

        article = denoise(article)

        # article = shift_dropcap_para(article) # attempt to fix first paragraph incorrectly extracted by tet

        merged_article = consecutive_merger(article, lang, page_nums, main_font, main_size, verbose)

        for i in range(1,8):
            merged_article = skip_merger(article, lang, page_nums, main_font, main_size, i, verbose)

        merged_article = check_for_odd_dropcaps(merged_article)

        new_root.append(merged_article)

    out_tree = etree.ElementTree(new_root)

    write_and_format_outfile(xml_file, out_tree, outpath)

###############################################################################
###############################################################################

def main():
    xml_file = sys.argv[1]
    outpath = sys.argv[2]

    print("Processing {}".format(xml_file))
    correct_xml(xml_file, outpath, verbose=True)
    print()

if __name__ == "__main__":
    main()

###############################################################################
# END CODE
