# -*- coding: utf-8 -*-
"""
Created on Tue Aug  2 12:57:05 2022
File handling, word counting, writing, dict creation and organization

Designed to identify all unique words in a given textual set, and then
insert characters to identify the unique words. It then stores that set somewhere
to be specified.

@author: Isaiah Magnuson

Changelog:
    -rev 2:
        made much more efficient
    -rev 3: WIP
        made modular, using functions
        allowed text location to be supplied via command line arguments
"""

# IMPORTS ====================================================================
import argparse
import os
import re
import sys
import yaml


# CONSTANTS ==================================================================
chapterPath = './Hebrews/Hebrews.txt'
alphaChars = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','-',"'"] # characters that make up legal words

# FUNCTIONS ==================================================================
def main(arg_material, arg_result_path, arg_title):
    
    
    
    
    def parse_yaml():
        """
            Reads the BookPaths.yml and returns a dictionary of books with their
            associated path and chapter list.
            
            Returns: material - a dict of "book"
        """
        
        absolute_path = os.path.dirname(__file__)
        paths_yaml_path = os.path.join(absolute_path, "./BookPaths.yml")
    
        with open(paths_yaml_path, 'r') as file:
            material = yaml.safe_load(file)
        
        return material
        
    
    def parse_books(specified_material):
        """
            Accepts: specified_material - a string of comma-seperated books used to
            specify the scope of texts that this script considers when finding unique words.
            (i.e. what the user enters as command line arguments)
            
            Returns: book_list - a list of individually checked books, in string form
            
            Throws an error if a book can't be found in the YAML lookup.    
        """
        final_book_list = []
        ok_books = parse_yaml().keys()
        
        # Remove spaces, split by commas
        specified_material = specified_material.translate({' ':''})
        book_list = specified_material.split(',')
        
        for book in book_list:
            if book in ok_books:
                final_book_list.append(book)
            else:
                raise IndexError(f"Book {book} not found in material library.")
        
        return final_book_list
    
    
    def bold_word(word):
        """
            Accepts: word - a string to be bolded with html tags
            Returns: tagged - same word surrounded by html bold tags
        """
        tagged = f"<b>{word}</b>"
        return tagged
    
    
    def header_word(word, level=3):
        """
            Accepts: word - a string to be made a header with html tags
                    level - an int of the header level desired, 1-6
            Returns: tagged - same string surrounded by html header tags
        """
        tagged = f"<h{level}>{word}</h{level}>"
        return tagged
    
    
    def split_and_count_words(book):
        """
            Accepts: book - "A long string of text"
            
            Returns: occurences_dict - a lowercase dictionary of every word
            that appears in the book, with values matching the number of occurences
        """
        
        word = re.compile(r"\b[a-z\-]+\b", flags=re.IGNORECASE)
        words_in_book = re.findall(word, book)
        occurences_dict = {}
        
        for occurence in words_in_book:
            if occurence.lower() not in occurences_dict.keys():
                occurences_dict[occurence.lower()] = 1
            else:
                occurences_dict[occurence.lower()] = occurences_dict[occurence.lower()] + 1
        
        return occurences_dict
    
    
    def bold_every_unique_word(book, occurences_dict):
        """
            Accepts: book - "A long string of text"
                    occurences_dict - a lowercase dictionary of every word
                    that appears in the book, with values matching the number
                    of occurences
            
            Returns: bolded_book - A copy of the original book that has every
                    unique word bolded with html bold tags
        """
        bolded_book = book
        
        for occurence in occurences_dict.keys():
            if occurences_dict[occurence] == 1:
                word = re.compile(rf"(\b{occurence}\b)", flags=re.IGNORECASE)
                temp_book = re.split(word, bolded_book)
                bolded_book = temp_book[0] + bold_word(temp_book[1]) + temp_book[2]
        
        return bolded_book
    
    
    # CODE =======================================================================
    # Section 1: Prep ----------------
    book_list = parse_books(arg_material)
    # By the end of this section, need to have the material in one giant string
    material_lookup = parse_yaml()
    material_string = ""
    
    for book in book_list:
        material_string = material_string + header_word(book, 2) + '\n'
        for chapter in material_lookup[book]['Chapters']:
            
            filename = f"{chapter}.chapter"
            absolute_path = os.path.dirname(__file__)
            book_path = os.path.join(os.path.join(absolute_path, material_lookup[book]["Path"]), filename)
            
            with open(book_path, 'r', encoding="utf8") as file:
                material_string = material_string + header_word(f"Chapter {chapter}", 3) + '\n'
                material_string = material_string + file.read()
    
    print(material_string)
# Section 2: Process -------------


# Section 3: Generate Output -----

def parse_config():
    """
        Reads BoldrConfig.yml and returns a dictionary of configurated paths
        
        Returns: arg_paths - a dict of path command line argument defaults
    """
    
    absolute_path = os.path.dirname(__file__)
    paths_yaml_path = os.path.join(absolute_path, "./BoldrConfig.yml")

    with open(paths_yaml_path, 'r') as file:
        arg_paths = yaml.safe_load(file)
    
    return arg_paths


if __name__ == "__main__":
   
    default_args = parse_config()
    # Any command line arguments not supplied will be replaced with the contents
    # of BoldrConfig.yml
    parser = argparse.ArgumentParser(prog="boldr by Isaiah Magnuson",
                                     description="Given a set of NT books, generates an .html file with all unique words bolded.",
                                     epilog="Requires --material to be specified as a string")
    
    parser.add_argument("--material",
                        help="String of NT books to use as material")
    parser.add_argument("--result_path",
                        help="Relative or absolute location to place results file")
    parser.add_argument("--title",
                        help="Title of .html file")
    options = parser.parse_args()
    
    dict_options = vars(options)
    for option in dict_options.keys():
        if dict_options[option] is None:
            print(f"Empty argument {option} identified, using default.")
            dict_options[option] = default_args[option]
            
    main(dict_options["material"], dict_options["result_path"], dict_options["title"])