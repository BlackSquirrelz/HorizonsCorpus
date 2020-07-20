#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from Wordplus_Parser import TetmlFile
import datetime

def check_inventory(contents, filename):
    """
    Allows user to validate list of contents extracted from Wordplus_Parser
        Args: automatically extracted contents list of tuples.
        Returns: validated contents list of tuples
    """
    validated_contents = []
    for i, (num, title) in enumerate(contents):
        print("Currently processing {}\n".format(filename))
        valid_pair = input("Valid page number and title? ((y)es/(n)o)\n\t{}\t{}\n".format(num, title))
        if valid_pair != "n":
            validated_contents.append((num, title))
        else:
            valid_page = input("Valid page number?\n\t{}\t\n((y)es/(n)o)\n".format(num))
            if valid_page == "n":
                true_page = input("Enter the true page number, or hit (d) to delete it from the contents list.\n")
                if true_page != "d":
                    try:
                        true_page = int(true_page)
                    except TypeError:
                        true_page = input("Page number must be of type integer. Try again.\n")
                        try:
                            true_page = int(true_page)
                        except TypeError:
                            print("Invalid page number.\n")
                            sys.exit("Process aborted.")
                else:
                    # del contents[i]
                    continue
            else:
                true_page = num

            valid_title = input("Valid title?\n\t{}\n((y)es/(n)o)\n".format(title))
            if valid_title == "n":
                true_title = input("Enter the correct title.\n")
            else:
                true_title = title


            validated_contents.append((true_page, true_title))

    # catch all
    print("{} articles found".format(len(validated_contents)))
    final_control = input("Anything missing?\n\t((y)es/(n)o)\n")
    if final_control == "y":
        additions_pg_numbers = input("Enter page numbers of all missing items separated by '|'.\n")
        additions_titles = input("Enter titles of missing all items separated by '|'.\n")
        for num, title in zip(additions_pg_numbers.split("|"), additions_titles.split("|")):
            try:
                validated_contents.append((int(num), str(title)))
                # validated_contents.append((int(additions[i]), additions[i+1]))
            except TypeError:
                print("Invalid page number entered. Process aborted.")
    else:
        pass
    # resort validated contents and return
    validated_contents.sort(key=lambda tup: tup[0])
    # print(validated_contents)
    return validated_contents


def main():
    pass
    # wordplus_tetml = "/Volumes/Hard Drive/UNI/SwitchDrive/Horizonte/Tannon/scripts/SNF_tetml_wordplus_en/horizonte_2014_100_en.tetml"
    # tetml = TetmlFile(wordplus_tetml)
    # contents = tetml.parse_contents()
    # for i in contents:
    #     print(i)
    # # to validate contents
    # true_contents = check_inventory(contents)
    # for i in true_contents:
    #     print(i)

if __name__ == "__main__":
    main()
