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
import yaml


# CONSTANTS ==================================================================
chapterPath = './Hebrews/Hebrews.txt'
alphaChars = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','-',"'"] # characters that make up legal words

# FUNCTIONS ==================================================================
parser = argparse.ArgumentParser(prog="boldr by Isaiah Magnuson",
                                 description="Given a set of NT books, generates an .html file with all unique words bolded.",
                                 epilog="Requires --material to be specified as a string")

parser.add_argument("--material", action="store_const", dest="arg_material",
                    help="String of NT books to use as material", required=True)
parser.add_argument("--result_path", action="store_const", dest="arg_result_path",
                    help="Relative or absolute location to place results file")
parser.add_argument("--title", action="store_const", dest="arg_title",
                    help="Title of .html file")


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
    specified_material = specified_material.translate(' ', '')
    book_list = specified_material.split(',')
    
    for book in book_list:
        if book in ok_books:
            final_book_list = final_book_list + book
        else:
            raise IndexError(f"Book {book} not found in material library.")
    
    return final_book_list




# CODE =======================================================================
args = parser.parse_args()
book_list = parse_books(args.arg_material)


# goal one: read in a chapter and create a dict of alphabetized words and their occurence numbers
# strategy: find a way to identify plain words, iterate through and create a copy of the file that's only the plain words
# there's some optimzation to care about here
# with open(chapterPath,'r',encoding='utf-8',errors='replace') as chapter1File:
#     chapter1 = chapter1File.read()
#     #print(chapter1)
#     wordList = []
#     tempList = chapter1
#     for item in ['0','1','2','3','4','5','6','7','8','9','\"','"','.','!',':',';','(',')','?',',','”','“']:
#         tempList = tempList.replace(item,'')
#     tempList = tempList.lower()
#     tempList = tempList.split()
#     #print(tempList)
    
#     occurenceDict = {item: tempList.count(item) for item in tempList}
#     #print(occurenceDict)
    
#     uniqueWords = []
#     #now get the unique words
#     for key, value in occurenceDict.items():
#         #print(f'{key},{value}')
#         if (value == 1):
#             uniqueWords.append(key)
#     #print(uniqueWords)
    
#     splitChapter = chapter1.split(' ')
#     #print(splitChapter)
#     acceptableTerminators = ['\"','"','.','!',':',';','(',')','?',',','”','“']
#     for idx,word in enumerate(splitChapter):
#         for query in uniqueWords:
#             match_object = re.match(query,word,re.IGNORECASE)
#             if match_object: # unique word substring match, do some checks and bold if it's not an interior match.
#                 matchingIndex = match_object.span() # is (start, end) of match
#                 try:
#                     if matchingIndex == (0,len(word)): #it's an exact match, we're good to go
                        
#                         word = "*" + word + "*"
#                     elif matchingIndex == (0,len(word)-1) and word[len(word)-1] in acceptableTerminators: #last char is a terminator, but that's ok
                        
#                         word = "*" + word[0:len(word)-1] + "*" + word[len(word)-1]
#                     elif matchingIndex == (1,len(word)) and word[0] in acceptableTerminators: #it's getting unlikely that it's not some sort of substring match
                        
#                         word = word[0] + "*" + word[1:len(word)] + "*"
#                     elif word[matchingIndex[1]] in acceptableTerminators and matchingIndex[0] == 0: #now we need to check the next char, if it's an alpha char it's no good, if it's an acceptable we're fine
                        
#                         word = "*" + word[0:matchingIndex[1]] + "*" + word[matchingIndex[1]:len(word)]
#                     elif word[matchingIndex[1]] in acceptableTerminators and word[matchingIndex[0]-1] in acceptableTerminators:
                        
#                         word = word[0:matchingIndex[0]] + "*" + word[matchingIndex[0]:matchingIndex[1]] + "*" + word[matchingIndex[1]:len(word)]
                    
#                     #debug:
#                     if word != splitChapter[idx]:
#                         print(f"{matchingIndex}, {query} in {splitChapter[idx]}")
#                     #now replace the word
#                     splitChapter[idx] = word
#                 except:
#                     print(f"probably not, is {query} == {word}?")
#     #print(splitChapter)
#     """ now join the chapter back together """
#     finalChapter = ' '.join(splitChapter)
#     print(finalChapter)
                    