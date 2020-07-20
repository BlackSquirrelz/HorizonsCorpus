#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from lxml import etree
import operator
import os

class TetmlFile(object):
    "Class storing SNF_tetml_pages_files"
    # parse xml with utf-8 encoding and removing blank text
    # parser = etree.XMLParser(remove_blank_text=True, encoding="utf-8")
    # TET namespace
    # ns = {"tet": "http://www.pdflib.com/XML/TET3/TET-3.0"}

    ###################################################

    def __init__(self, tetml_file):
        "initialises Object of Class tetml_file"
        # read file with lxml, get root and find all pages
        # self.tetml = etree.parse(tetml_file, TetmlFile.parser)
        self.filename = tetml_file.split("/")[-1][:-6]
        self.tetml = self._parse_NNS(tetml_file)
        self.root = self.tetml.getroottree()
        self.pages = self.root.xpath("//Page")
        self.num_of_pages = len(self.pages)

    def _parse_NNS(self, tetml_file):
        """
        Parses tetml file removing namespace and declaration.
        """
        with open(tetml_file) as f:
            # read lines from xml skipping <TET> and <Creation> tags.
            xml_lines = f.readlines()[8:-1]

        # xml_lines = [line.strip() for line in xml_lines]
        xml_string = " ".join(xml_lines)

        # output xml file with no namespace declaration.
        # root = etree.ElementTree(etree.fromstring(xml_string))
        # root.write(open(self.filename+"_NNS.xml", 'wb'), pretty_print=True, xml_declaration=True, encoding="utf-8")

        # initialise parser that removes whitespace and
        parser = etree.XMLParser(remove_blank_text=True)

        parsed_dom = etree.XML(xml_string, parser=parser)
        return parsed_dom

    def _front_matter_NEW(self):
        """
        Finds and returns a contents pages of issues > 96.
        :param doc_pages: Tetmlfile as ElementTree object
        :return: navigable page object
        """
        editorial_page = self.pages[1]
        contents_pages = self.pages[3:5]
        return editorial_page, contents_pages

    def _front_matter_MID(self):
        """
        Finds and returns a contents pages of issues > 96.
        :param doc_pages: Tetmlfile as ElementTree object
        :return: navigable page object
        """
        editorial_page = None
        contents_page = None
        for page in self.pages:
            # if editorial_page == None and contents_page == None:
            if editorial_page == None:
                if page.xpath(".//Para/Word/Text")[0].text in ["editorial", "éditorial", "rubrik"]: # for some unknown reason, issue 90_fr contains 'rubrik editorial'.
                    editorial_page = page
            if contents_page == None:
                if page.xpath(".//Para/Word/Text")[0].text in ["inhalt", "sommaire"]:
                    contents_page = page
            else:
                break

        # if editorial_page and contents_page:
        return editorial_page, contents_page

    def _front_matter_OLD(self):
        """
        Finds and returns a contents pages of issues > 96.
        :param doc_pages: Tetmlfile as ElementTree object
        :return: navigable page object
        """
        editorial_page = None
        contents_page = None

        for page in self.pages:
            # if editorial_page == None and contents_page == None:
            if editorial_page == None:
                if page.xpath(".//Text")[0].text in ["editorial", "éditorial", "éditorial"]: # normally the first word on the page
                    editorial_page = page
                elif page.xpath(".//Para")[1].xpath("./Word/Text")[0].text in ["editorial", "éditorial", "éditorial"]: # can sometimes be in the second paragraph depending on formatting
                    editorial_page = page
                    # print("ed found")
                else: # if not found in first or second word, look further
                    for word in page.xpath(".//Text")[:15]:
                        if word.text in ["editorial", "éditorial", "éditorial"]:
                            editorial_page = page
                            # print("ed found")

            if contents_page == None:
                if page.xpath(".//Text")[0].text in ["inhalt", "sommaire"]:
                    contents_page = page # normally the first word on the page
                elif page.xpath(".//Para")[0].xpath("./Word/Text")[0].text in ["inhalt", "sommaire"]:# can sometimes be in the second paragraph depending on formatting
                    contents_page = page
            else:
                break

        # if editorial_page and contents_page:
        return editorial_page, contents_page

    ##########################################################################

    def parse_contents_NEW(self, min_font_size=float(8.00)):

        editorial, contents_pages = self._front_matter_NEW()

        content_dict = {}

        for page in contents_pages:

            page_number_elems = []

            text_elems = page.xpath(".//Text")

            for elem in text_elems:
                if elem.text != None:
                    if elem.text.isdigit() and float(elem.getnext().xpath("./Glyph/@size")[0]) >= min_font_size:

                        if int(elem.text) != 5: # assumed second contents page
                            if int(elem.text) < len(self.pages):
                                page_number_elems.append(elem)
                                content_dict[int(elem.text)] = ''


            for elem in page_number_elems:

                if len(elem.getparent().getparent().getchildren()) > 1:

                    # if title text is in same para
                    text_elems = [token.text for token in elem.getparent().getparent().xpath(".//Text") if float(token.getnext().xpath("./Glyph/@size")[0]) >= min_font_size and token.text != None]
                    content_dict[int(elem.text)] = " ".join(text_elems[1:])

                else:
                    # title is assumed to be in the following para tag
                    text_elems = [token.text for token in elem.getparent().getparent().getnext().xpath(".//Text") if float(token.getnext().xpath("./Glyph/@size")[0]) >= min_font_size and token.text != None]
                    content_dict[int(elem.text)] = " ".join(text_elems)

        content_dict[int(editorial.attrib["number"])] = "Editorial/Editorial/Éditorial"
        content_dict[int(contents_pages[0].attrib["number"])] = "Inhalt/Sommaire/Contents"

        return sorted(content_dict.items(), key=operator.itemgetter(0))

    ##########################################################################

    def parse_contents_MID(self, min_font_size=float(8.00)):

        offset = input("Is a page offset required? ((y)es / (n)o)\n")

        editorial, contents_page = self._front_matter_MID()

        content_dict = {}

        page_number_elems = []

        text_elems = contents_page.xpath(".//Text")

        for elem in text_elems:
            if elem.text != None:
                if elem.text.isdigit() and float(elem.getnext().xpath("./Glyph/@size")[0]) >= min_font_size:

                    if offset == "y":
                        if int(elem.text) < len(self.pages) + 2:
                            page_number_elems.append(elem)
                            content_dict[int(elem.text)] = ''
                    else:
                        if int(elem.text) < len(self.pages) + 40: # buffer
                            page_number_elems.append(elem)
                            content_dict[int(elem.text)] = ''


        for elem in page_number_elems:

            if len(elem.getparent().getparent().xpath(".//Word")) > 1:

                text_elems = []
                for i, token in enumerate(elem.getparent().getparent().xpath(".//Text")):
                    if float(token.getnext().xpath("./Glyph/@size")[0]) >= min_font_size and token.text != None:
                        text_elems.append(token.text)
                    if i == len(elem.getparent().getparent().xpath(".//Text"))-1:
                        try:
                            # look for subtitle in the following para
                            if elem.getparent().getparent().getnext().xpath(".//Text")[0].text.isalpha() or elem.getparent().getparent().getnext().xpath(".//Text")[0].text == "«" and len(elem.getparent().getparent().getnext().xpath(".//Text")) > 1:
                                text_elems.append("-")
                                for token in elem.getparent().getparent().getnext().xpath(".//Text"):
                                    text_elems.append(token.text)
                        except AttributeError:
                            pass

                content_dict[int(elem.text)] = " ".join(text_elems[1:])

            else:
                # title is assumed to be in the following para tag
                try:
                    text_elems = [token.text for token in elem.getparent().getparent().getnext().xpath(".//Text") if float(token.getnext().xpath("./Glyph/@size")[0]) >= min_font_size and token.text != None]
                    content_dict[int(elem.text)] = " ".join(text_elems)
                except AttributeError:
                    pass


        content_dict[int(editorial.attrib["number"])] = "Editorial/Editorial/Éditorial"
        content_dict[int(contents_page.attrib["number"])] = "Inhalt/Sommaire/Contents"

        if offset == "y": # assumes an offset of -1
            offset_dict = {}
            for k, v in content_dict.items():
                if not k in offset_dict:
                    if k == 1 or k == 2:
                        offset_dict[k] = v
                    else:
                        offset_dict[k-1] = v
            return sorted(offset_dict.items(), key=operator.itemgetter(0))

        return sorted(content_dict.items(), key=operator.itemgetter(0))

    ##########################################################################

    def parse_contents_OLD(self, min_font_size=float(8.00)):

        offset = input("Is a page offset required? ((y)es / (n)o)\n")

        editorial, contents_page = self._front_matter_OLD()

        if not editorial:
            print("Problem finding editorial page.")

        content_dict = {}

        page_number_elems = []

        text_elems = contents_page.xpath(".//Text")

        for elem in text_elems:
            if elem.text != None:
                if elem.text.isdigit() and float(elem.getnext().xpath("./Glyph/@size")[0]) >= min_font_size and int(elem.text) < len(self.pages) and int(elem.text) > 1:
                    y_pos = float(elem.getnext().attrib["lly"])
                    page_number_elems.append((elem, y_pos))
                    # add page number to content dictionary
                    content_dict[int(elem.text)] = ''

        # print([i for i in page_number_elems])

        for elem, y_pos in page_number_elems:
            text_elems = []
            current_size = 0

            ## handles Rubriken box
            if len(elem.getparent().getparent().xpath(".//Word")) == 1 and elem.getparent().getparent().getparent().tag == "Cell":
                cell = elem.getparent().getparent().getparent()
                for token in cell.getnext().xpath(".//Text"):
                    text_elems.append(token.text)
                    content_dict[int(elem.text)] = " ".join(text_elems)


            elif len(elem.getparent().getparent().getchildren()) > 1:
                for i, token in enumerate(elem.getparent().getparent().xpath(".//Text")):
                    if float(token.getnext().attrib["lly"]) == y_pos and token.text != None:
                        current_size = float(elem.getnext().xpath(".//Glyph/@size")[0])
                        text_elems.append(token.text)

                    ## check for continuation of title in following para
                    if i == len(elem.getparent().getparent().xpath(".//Text"))-1:
                        para_tag = elem.getparent().getparent()
                        try:
                            ## look for subtitle in the following para
                            if para_tag.getnext().xpath(
                                ".//Text")[0].text.isalpha()\
                            and len(para_tag.getnext().xpath(
                                ".//Text")[0].text) > 1\
                            and float(
                                para_tag.getnext().xpath(
                                    ".//Word/Box/Glyph/@size"
                                    )[0]
                                ) <= current_size\
                            and\
                            float(para_tag.getnext().xpath(".//Word/Box/Glyph/@size")[0]) > min_font_size:
                                for token in para_tag.getnext().xpath(".//Text"):
                                    text_elems.append(token.text)
                        except (AttributeError, IndexError):
                            print("Error raised")

                ## if page has multiple titles, split with " / "
                if content_dict[int(elem.text)] and not content_dict[int(elem.text)].isdigit():
                    content_dict[int(elem.text)] = content_dict[int(elem.text)] + " / " + " ".join(text_elems[1:])
                else:
                    content_dict[int(elem.text)] = " ".join(text_elems[1:])


        content_dict[int(editorial.attrib["number"])] = "Editorial/Editorial/Éditorial"
        content_dict[int(contents_page.attrib["number"])] = "Inhalt/Sommaire/Contents"

        # assumptions:
        if "de" in self.filename:
            rubriken_pages = [(35, "Bücher / Agenda"), (34, "Nussnacker / Exkursion / Impressum") ]
        elif "fr" in self.filename:
            rubriken_pages = [(35, "A lire / Agenda"), (34, "Enigmes / Excursion / Impressum") ]

        for i, page in enumerate(rubriken_pages):
            content_dict[int(rubriken_pages[i][0])] =  rubriken_pages[i][1]

        # for k, v in content_dict.items():
        #     if str(k) + " )" in v:
        #         content_dict.pop()

        if offset == "y": # assumes an offset of +1
            offset_dict = {}
            for k, v in content_dict.items():
                if not k in offset_dict:
                    if k == 1 or k == 2:
                        offset_dict[k] = v
                    else:
                        offset_dict[k+1] = v
            return sorted(offset_dict.items(), key=operator.itemgetter(0))


        print(content_dict)

        return sorted(content_dict.items(), key=operator.itemgetter(0))

    ##########################################################################

def main():
    pass
    ## test MID
    # wordplus_tetml = "/Volumes/Hard Drive/UNI/SwitchDrive/Horizonte/Tannon/wordplus_parsing_MID/SNF_tetml_wordplus_de_MID/horizonte_2012_92_de.tetml"
    # tetml = TetmlFile(wordplus_tetml)
    # contents_list = tetml.parse_contents_MID()
    # print(contents_list)

    ## test OLD
    # wordplus_tetml = "/Volumes/Hard Drive/UNI/SwitchDrive/Horizonte/SNF_tetml_wordplus_files/SNF_tetml_wordplus_de/horizonte_2006_69_de.tetml"
    # tetml = TetmlFile(wordplus_tetml)
    # contents_list = tetml.parse_contents_OLD()
    # print(contents_list)

if __name__ == "__main__":
    main()
