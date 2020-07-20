#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from subprocess import call
from lxml import etree
import argparse
import pathlib
import re
import os
import time

###############################################################################
## ToRun: pyhton3 text_extractor.py -i <input_file_path> -o <output_file_path>
###############################################################################

bad_punct = ['◂', '▸']
# normal punctuation -- should be appended to previous word
punctuation = ['!', '"', '#', '$', '%', ')', '*', ',', '-', '.', '»',
 ':', ';', '=', '>', '?', '@', '\\', ']', '^', '_', '}', '~', '°', '…', '”', '’', '’']
# punctuation that opens new sentence -- should be appended to following word
opening = ['(', '<', '[','{','«','“','‘', '‹']
closing = ['’', '”', '›']
# punctuation that is between two words -- should be concatenated with previous and following word
both = ['`', '|', '&', '+', '\'', '/','’']

contractions = ['ll','re','s','t','ve','d','m']
# special = ['html', 'com', 'ch']
fr_contractions = ['c','l','d','j','m','n','s','qu','lorsqu','aujourd','jusqu']

abbr = {'e. g.': 'e.g.', 'i. e.': 'i.e.', 'z. b.': 'z.B.', 'd. h.': 'd.h.'}

###############################################################################

ap = argparse.ArgumentParser(description="Script for converting corrected xml files to content xml format files for SNF Horizonte corpus.\n")

ap.add_argument("-i", "--input",  required=True, type=str, help="Path to a single XML input file for processing OR path to a directory containing multiple files for bulk processing")

ap.add_argument("-o", "--outpath", required=True, type=str, help="path to directory for output files.")

args = ap.parse_args()

###############################################################################

def restore_punctuation(text):

    if isinstance(text, str): # processing a title, convert to list and treat as normal
        text = text.split()

    # TODO: In the 1930s and’ 50s --> In the 1930s and ’50s
    # 3R­-Grundsätze --> 3R­Grundsätze but should remain 3R­-Grundsätze !!

    # fixed
    # ‹ aufgezogen ›, --> ‹aufgezogen›
    # 660’ 000 --> 660’000, 13’ 807 --> 13’807
    # It’ s our future – now we’re talking’. --> ‘It’s our future – now we’re talking’.
    # ‘Crimes and Punishments ’ --> ‘Crimes and Punishments’ HACK

    found = False
    current=[]

    for index in range(0,len(text)):
        word = text[index]

        try:

            if word == None:
                continue

            # concat between word and prev./follow. punctuation (usually quotation) -> ' good ' glued together as 'good'
            elif text[index-1] in opening and text[index+1][0] in closing: #1
                # look ahead to see if pattern is followed by a contraction character that also needs to be appended. e.g. “ It ’ s ... ” -> “It’s ...”
                if text[index+2] in contractions:
                    # print("RULE 1.2:", text[index-1], word, text[index+1], text[index+2])

                    del current[-1]
                    word = text[index-1]+word[1:]+text[index+1]+text[index+2]
                    current.append(word)
                    found = True
                    continue

                else:
                    # print("RULE 1.1:", text[index-1], word[1:], text[index+1])
                    del current[-1]
                    word = text[index-1]+word[1:]+text[index+1]
                    text[index+1] = word
                    current.append(word)
                    found = True # next word was already appended
                    continue

            # concat between punctuation with prev. and follow. word -> she ' ll glued together as she'll / 600 ' 000 -> 600'000
            elif (word in both or word.encode('utf-8') == '\xe2\x80\x99') and (text[index+1] in contractions or (text[index+1].isdigit() and text[index-1].isdigit())):
                # print("RULE 2:", text[index-1], word, text[index+1])
                del current[-1]
                word = text[index-1]+word+text[index+1]
                text[index+1] = word
                current.append(word)
                found = True # next word was already appended
                continue

            # append other punctuation to previous word -> house . as house.
            elif word in punctuation:
                # print("RULE 3:", text[index-1], word)
                del current[-1]
                word = text[index-1]+word
                text[index] = word
                current.append(word)
                continue

            # append sentence opening punctuation to following word -> << She said as <<She said
            elif word in opening:
                # print("RULE 4:", word, text[index+1])
                word = word+text[index+1]
                text[index+1] = word
                current.append(word)
                found = True # next word was already appended
                continue

            # append other punctuation to previous word -> house . as house.
            elif word[0] in punctuation:
                # print("RULE 5:", text[index-1], word)
                # print(word)
                del current[-1]
                word = text[index-1]+word
                text[index] = word
                current.append(word)
                continue

        except IndexError:
            pass


        # if the current word was already apended move on
        if found:
            # print("FOUND")
            # print(word)
            # print(current)
            found = False
            continue

        # append all other words as they are
        if word:
            current.append(word)
            # print(current)
    # if we somehow left out content e.g. - - + use original
    if current == []:
        current = text

    # Hack to ensure that nothing is missed: e.g. <div>'Crime and Punishments '<\div> -> <div>'Crime and Punishments'<\div>
    try:
        if current[-1] in punctuation:
            current[-2] = current[-2] + current[-1]
            del current[-1]
    except IndexError:
        pass

    return ' '.join(current)

def restore_french_punctuation(text):

    if isinstance(text, str): # processing a title, convert to list and treat as normal
        text = text.split()

    found = False
    current=[]
    for index in range(0,len(text)):
        word = text[index]
        try:
            # concat between word and prev./follow. punctuation (usually quotation) -> ' good ' glued together as 'good'
            if text[index-1] in opening and text[index+1][0] in closing :
                    del current[-1]
                    word = text[index-1]+word[1:]+text[index+1]
                    text[index+1] = word
                    current.append(word)
                    found = True # next word was already appended
                    continue
            # concat between punctuation with prev. and follow. word -> l ' amour glued together as l'amour
            elif word and (word in both or word.encode('utf-8') == '\xe2\x80\x99') and text[index-1].lower() in fr_contractions:
                del current[-1]
                word = text[index-1]+word+text[index+1]
                text[index+1] = word
                current.append(word)
                found = True # next word was already appended
                continue
            # append other punctuation to previous word -> house . as house.
            elif word in punctuation:
                del current[-1]
                word = text[index-1]+word
                text[index] = word
                current.append(word)
                continue
            # append sentence opening punctuation to following word -> << She said as <<She said
            elif word in opening:
                word = word+text[index+1]
                text[index+1] = word
                current.append(word)
                found = True # next word was already appended
                continue
            # append other punctuation to previous word -> house . as house.
            elif word and word[0] in punctuation:
                del current[-1]
                word = text[index-1]+word
                text[index] = word
                current.append(word)
                continue
        except IndexError:
            pass

        # if the current word was already apended move on
        if found:
            found = False
            continue

        # append all other words as they are
        if word:
            current.append(word)

    # if we somehow left out content e.g. - - + use original
    if current == []:
        current = text


    return ' '.join(current)

def fix_urls_emails(newstring):

    if "@" in newstring:
        m = re.search(r"\w+@ \w+\. [a-z]{2,3}",newstring)
        if m:
            temp=newstring[m.start():m.end()]
            temp=re.sub(" ","",temp)
            newstring = re.sub(newstring[m.start():m.end()],temp,newstring)
    if "www" in newstring:
        if ("(www") in newstring:
            newstring = re.sub("[()]","",newstring)
        # m = re.search(r"www\. (.+?) ?\. ?([a-z]{2,3}) ?/ ?([^\.]+)", newstring)
        # added this to fix web endings not being attached to address, e.g. '. php', '. html'
        m = re.search(r"www\. (.+?) ?\. ?([a-z]{2,3}) ?/ ?([^\.]+)\.? ?(html?|php|com|ch|uk|co|au)?", newstring)
        if m:
            # print(m.groups())
            temp=newstring[m.start():m.end()]
            temp=re.sub(" ","",temp)
            newstring = re.sub(newstring[m.start():m.end()],temp,newstring)
        try:
            newstring = re.sub(r'www\. (.+?) ?\. ?([a-z]{2,3})', r'www.\1.\2.\3', newstring)
        except re.error:
            newstring = re.sub(r'www\. (.+?) ?\. ?([a-z]{2,3})', r'www.\1.\2.', newstring)

    return newstring

def restore_abbreviations(newstring):
    # restores i. e. --> i.e.
    for i in abbr:
        if i in newstring.lower():
            newstring = newstring.replace(i, abbr[i])
            print("abbreviation replaced:", i, "-->", abbr[i])
    return newstring

def denoise(newstring):
    newstring = newstring.replace('◂ ', '')
    newstring = newstring.replace('▸ ', '')
    # newstring = newstring.strip()
    return newstring.strip()

def remove_page_nums(article_content, document_content):
    #remove page numbers occuring right before or right after the article boundary
    try:
        if re.search("^[0-9]{1,2}$",article_content[1]):
            del(article_content[1])
        if re.search("^[0-9]{1,2}$",article_content[-1]):
            del(article_content[-1])
    except IndexError:
        pass
    #remove page numbers occuring within an article which is not ToC
    #and merge paragraphs broken by page numbers
    for idx,line in enumerate(article_content):
        if len(line)==1 and line[0].isupper():
            if line[0]=="A":
                article_content[idx]+=" "+ article_content[idx+1]
            else:
                article_content[idx]+=article_content[idx+1]
            del(article_content[idx+1])
        if line=="«":
            article_content[idx] = line + article_content[0] + " "+ article_content[idx+1]
            del(article_content[idx+1])
            del(article_content[0])
        if re.search("^[0-9]{1,2}$",line) and len(document_content)>2:
            if idx<len(article_content)-1 and article_content[idx+1] and article_content[idx+1][0].islower() and not re.search("[\.\?\!]$",article_content[idx-1]):
                article_content[idx-1]=article_content[idx-1]+" "+article_content[idx+1]
                del(article_content[idx+1])
            elif idx<len(article_content)-2 and article_content[idx+2] and article_content[idx+2][0].islower() and not re.search("[\.\?\!]$",article_content[idx-1]):
                article_content[idx-1]=article_content[idx-1]+" "+article_content[idx+2]
                if not article_content[idx+1]:
                    del(article_content[idx+1:idx+3])
                else:
                    del(article_content[idx+2:idx+3])
            del(article_content[idx])

    return article_content

def extract_text(xml_file, lang):

    document_content = []

    for _, elem in etree.iterparse(xml_file, tag="Article"):
        paras = elem.xpath(".//Para")
        article_content = []

        for para in paras:
            para_content = []
            tokens = para.xpath(".//Text")
            for token in tokens:
                if float(token.getnext().getchildren()[0].attrib["size"]) >= 8:
                    para_content.append(token.text)

            if lang == 'fr':
                newstring = restore_french_punctuation(para_content) # newstring is paragraph text as string
            else:
                newstring = restore_punctuation(para_content)

            newstring = fix_urls_emails(newstring)
            newstring = restore_abbreviations(newstring)
            newstring = denoise(newstring)

            article_content.append(newstring)
            para_content = []

        article_content = remove_page_nums(article_content, document_content)

        article_content = list(filter(None, article_content))
        document_content.append(article_content)

    return document_content

def restore_xml_tree(xml_file, document_content, lang):
    #start "refactoring" the xml tree

    newtree = etree.parse(xml_file)

    for idx, article in enumerate(document_content):
        if not article:
            newtree.getroot()[idx].tag="article"
            newtree.getroot()[idx].clear()
            continue
        copy=newtree.getroot()[idx].items()
        newtree.getroot()[idx].clear()
        for k,v in copy:
            newtree.getroot()[idx].set(k,v)

        newtree.getroot()[idx].tag="article"
        newtree.getroot()[idx].attrib["id"] = newtree.getroot()[idx].attrib.pop("article_id")

        #split long titles
        if lang == 'fr':
            current_title=restore_french_punctuation(newtree.getroot()[idx].attrib["title"])
        else:
            current_title=restore_punctuation(newtree.getroot()[idx].attrib["title"])
        mt=re.search("[\.\?\!]",current_title)
        if mt and mt.start()<len(current_title)-1 or len(current_title.split())>8:
            splittitle = re.split("[\.\?\!]",current_title)
            if len(article[0])>10 and article[0] in current_title:
                newtree.getroot()[idx].set("title",article[0])
            elif len(article[1])>10 and article[1] in current_title:
                newtree.getroot()[idx].set("title",article[1])
            else:
                if mt:
                    newtree.getroot()[idx].set("title",splittitle[0]+current_title[mt.start()])

        consec_blank_lines=0
        max_consec_blank=-1
        for pidx,paras in enumerate(article):
            if paras:
                new = etree.SubElement(newtree.getroot()[idx],"div")
                new.text=paras
            if not paras:
                consec_blank_lines+=1
            else:
                if consec_blank_lines>0:
                    prev_max =max_consec_blank
                    if consec_blank_lines>prev_max:
                        max_consec_blank=consec_blank_lines
                consec_blank_lines=0

        if max_consec_blank>5:
            newtree.getroot()[idx].attrib["potential_errors"] = "true"
            print("potential_errors set to true")

    output_tree = etree.ElementTree(newtree.getroot())
    return output_tree

def write_output(tree, outfile):
    """
    Write the new tree to the output file.
    :param tree: collection of article elements in valid xml (_ElementTree)
    :output_file: output file for writing (file_object)
    """
    tree.write(outfile, pretty_print=True, xml_declaration=True, encoding="utf-8")

    call(["xmllint", "--format", outfile, "--output", outfile[:-4]+".tmp.xml", "--encode", "utf-8"])
    call(["mv", outfile[:-4]+".tmp.xml", outfile])

##############################################################################

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
                document_content = extract_text(infile, file_lang)
                outfile = str(pathlib.Path(args.outpath) / file_name)
                newtree = restore_xml_tree(infile, document_content, file_lang)
                write_output(newtree, outfile)
                elapsed_time = time.time() - start_time
                print("\t{0} processed in {1:.2f} seconds".format(file_name, elapsed_time))

    else:
        infile = str(pathlib.Path(args.input))
        start_time = time.time() # start timer
        file_name = infile.split("/")[-1]
        file_lang = re.search(r'_(de|en|fr).xml', file_name).group(1)
        print("\nProcessing {}...".format(file_name))
        document_content = extract_text(infile, file_lang)
        outfile = str(pathlib.Path(args.outpath) / file_name)
        newtree = restore_xml_tree(infile, document_content, file_lang)
        write_output(newtree, outfile)
        elapsed_time = time.time() - start_time
        print("\t{0} processed in {1:.2f} seconds".format(file_name, elapsed_time))

if __name__ == "__main__":
    main()
