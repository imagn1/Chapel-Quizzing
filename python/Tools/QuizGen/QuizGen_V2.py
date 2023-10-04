# -*- coding: utf-8 -*-
"""
Created on Thu Oct 27 16:34:42 2022

@author: Isaiah Magnuson

Purpose:
    To be a terminal based program that allows the user to read in a .csv file
    of quizzing questions, to tweak parameters, and then generate a set of .txt
    quizzes based on those parameters.
    Goals:
        -Flexible number of quizzes
        -Ability to specify range of chapters/verses
        -Ability to name set of quizzes
        -Flexible ratio of key questions (default 50%)
        -
"""
# Imports ====================================================================
import csv
import random
import os
import sys
import yaml

# Constants ==================================================================

# Configurations +============================================================
absolute_path = os.path.dirname(__file__)

config_path = os.path.join(absolute_path, "../../../configs/")
quizgen_config_path = os.path.join(config_path, "quizgen_config.yml")
quiz_definition_path = os.path.join(config_path, "quiz_definition.yml")
question_types_path = os.path.join(config_path, "question_types.yml")

with open(quizgen_config_path, 'r') as file:
    config = yaml.safe_load(file)

with open(quiz_definition_path, 'r') as file:
    quiz_definition = yaml.safe_load(file)
    
with open(question_types_path, 'r') as file:
    question_types = yaml.safe_load(file)


# Class definitions ==========================================================
class Verse:
    def __init__(self, book, chapter, verse):
        self.book = book
        self.chapter = chapter
        self.verse = verse
        
    def to_string(self):
        buildup = "" + self.book + " " + self.chapter + ":" + self.verse
        return buildup


class Question:
    """
    A Question object that consists of a question type, a prompt, an answer
    and a reference.
    """
    
    # The tricky bit here is that we want a question to be able to have 1+
    # associated verses, or potentially span the border between chapters.
    
    def __init__(self, _type, prompt, answer, *verse):
        self.verse = verse
        self._type = _type
        self.prompt = prompt
        self.answer = answer
        
        if (len(verse) > 1):
            # Question is associated with multiple verses!
            self.is_multiple = True
        else:
            self.is_multiple = False

    def to_string(self):
        if (self.is_multiple is True):
            # Have to back-compile this to "book ch:vs-vs" form.
            # First check to see if all verses are in the same chapter
            verses = self.verse
            diff_chapters = any([chap != other for chap in [vs.chapter for vs in verses]
                                 for other in [vs.chapter for vs in verses]])
            if (diff_chapters is True):
                # Now buildup "book first_ref - second_ref"
                buildup = "" + verses[0].book + " " + verses[0].chapter + ":"\
                    + verses[0].verse + "-" + verses[-1].chapter + ":" +\
                    verses[-1].verse
            else:
                # Easy. Just buildup book chapter:vs-vs
                buildup = "" + verses[0].book + " " + verses[0].chapter + ":"\
                    + verses[0].verse + "-" + verses[-1].verse
            
        else:
            buildup = "" + self.verse[0].to_string()
        
        return (buildup + "," + self._type + "," + self.prompt + "," + self.answer)
    
    def get_verses(self):
        return [item for item in self.verse]


class Quiz:
      
    global debug
    
    def __init__(self):
        self.default_num_questions = quiz_definition["Quiz"]["Questions"]["Number"]
        self.default_ratio_key = quiz_definition["Quiz"]["Questions"]["RatioKey"]
        self.default_num_backup = quiz_definition["Quiz"]["Backups"]["Number"]
        self.default_type_dist = quiz_definition["Quiz"]["Questions"]["Distribution"]
        self.default_qtype = quiz_definition["Quiz"]["Questions"]["Default"]
        
        # These probably shouldn't be done this way, but I'm lazily taking
        # advantage of the old way I did it.
        num_questions = self.default_num_questions
        ratio_key = self.default_ratio_key
        num_backup = self.default_num_backup
        ratio_types = self.default_type_dist
        default_qtype_use = self.default_qtype
        
        question_set = []
        backup_question_set = []
        num_types = {}
        
        # Determine the number of each question types to use for this quiz
        for qtype in ratio_types.keys():
            poss_range = ratio_types[qtype].split(',')
            # Assume poss_range =["min", "max"]
            min_num = int(poss_range[0])
            max_num = int(poss_range[1])
            num_types[qtype] = random.randrange(min_num, max_num + 1)
        
        non_default_questions_count = sum(num_types.values())

        # Fill in the rest with deafult questions
        assert non_default_questions_count <= num_questions
        num_types[default_qtype_use] = num_questions - non_default_questions_count
        
        # Now assume any leftover qtypes are zero
        for qtype in question_types["Question Types"].keys():
            if qtype not in num_types.keys():
                num_types[qtype] = 0
        
        # Make a list of key question types
        key_types = [smtg for smtg in ratio_types.keys() if question_types["Question Types"][smtg]["is_key_only"] is True]
        
        # Now actually pull questions into the quiz
        for qtype, qty in num_types.items():
            for i in range(qty):
                if qtype not in key_types:
                    # Generate as normal
                    if random.random() <= ratio_key:
                        # get key question
                        question_set.append(get_key_question(qtype))
                    else:
                        question_set.append(get_question(qtype))
                else:  # Memory verses are always key
                    question_set.append(get_key_question(qtype))

        assert len(question_set) == num_questions
        
        # Now do the backup questions
        # There's some decision to be made here. How should backup questions
        # be distributed? Should they remove themselves from the pool?
        # I'm deciding that we generate 2 backup Q's of each non-int type,
        # and the specified number of INT backups. Also they won't pop.
        if num_backup > 0:
            for key, value in num_types.items():
                # Debug
                if debug:
                    print(f"Backup {key}")
                if key != "INT":
                    if key not in ["QT", "FTV"]:
                        for i in range(2):
                            backup_question_set.append(get_question(key, False))
                    else:
                        for i in range(2):
                            backup_question_set.append(get_key_question(key, False))
                else:
                    for i in range(num_backup):
                        backup_question_set.append(get_question(key, False))
        
        # Shuffle the quiz
        random.shuffle(question_set)
        self.question_set = question_set
        self.backup_question_set = backup_question_set
        
    def to_string(self, title="Quiz"):
        buildup = "-----------\n"
        buildup += title + "\n"
        buildup += "-----------\n"
        for index, question in enumerate(self.question_set):
            buildup += str(index + 1) + ". " + question.book + " " + question.reference
            buildup += "\n " + question._type
            buildup += "\n " + question.prompt
            buildup += "\n " + question.answer + "\n"
        buildup += "\nBackup Questions\n"
        for index, question in enumerate(self.backup_question_set):
            buildup += str(index + 1) + ". " + question.book + " " + question.reference
            buildup += "\n " + question._type
            buildup += "\n " + question.prompt
            buildup += "\n " + question.answer + "\n"
        return buildup


# Function definitions =======================================================
def readQuestionLibrary():
    """
    This function reads in the CSV of questions, and turns it into an array.
    Relies on the path definition in quizgen_config.yml

    Returns
    -------
    q_lib, an array of the data of the CSV
    """
    q_lib = []
    lib_path = config["Paths"]["QuestionsCSV"]
    assert os.path.exists(lib_path), "File not found at, " + str(lib_path)
    with open(lib_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            q_lib.append(row)
    return q_lib


def readKeyList():
    """
    This function reads in a CSV file of key verses, and makes a list of them
    Relies on the path definition in quizgen_config.yml
    
    Assumed format of csv is book | verses | verses | verses
                             book | verses | verses ...
                             
    Returns
    -------
    key_verses : list of Verse type key verses

    """

    key_lib = []
    key_path = config["Paths"]["KeyVersesCSV"]
    assert os.path.exists(key_path), "Key verses file not found at, " + str(key_path)
    with open(key_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            key_lib.append(row)
    
    key_verses = []
    for row in key_lib:
        for index, reference in enumerate(row):
            if index != 0:
                # Returns a bunch of None's, but the following is kinda pretty.
                [key_verses.append(item) for item in create_verse(row[0], reference)]
    
    return key_verses


def create_verse(book, chapter, verse):
    """
    Passed book, chapter, verse.
    i.e. Hebrews, 1, 1
    constructs a Verse object out of it and returns it.
    """
    return Verse(book, chapter, verse)


def create_verse(book, reference):
    """
    A different way to create verse objects.
    Takes something like:
        Hebrews 1:1
        or
        Hebrews 1:1-2
    And returns the appropriate number of verse objects.
    """
    verses = []
    
    assert ':' in reference, f"Invalid reference {book} {reference}"
    reference = reference.split(':')
    if '-' in reference[-1]:
        reference = reference[-1].split('-')
        # Multiple references identified. Need to create multiple verses
        for item in reference[1:]:
            verses = verses.append(Verse(book, reference[0], item))
    else:
        verses = [Verse(book, reference[0], reference[1])]
    return verses


def gen_pools(q_lib, key_refs):
    """
    This function takes q_lib, a plain array of questions,
    and sorts it into two pools of Question type.

    Parameters
    ----------
    q_lib : from readQuestionLibrary
    key_refs : a list of references of the key verses
    Returns
    -------
    pool : a list of non-key Questions
    key_pool : a list of key Questions
    """
    pool = []
    key_pool = []
    # Assume first line is headers, and is in format:
    # BOOK, REF, TYPE, PROMPT, ANSWER
    q_lib = q_lib[1:]
    for line in q_lib:
        # create the question first
        # Need to determine reference!
        temp_verse = create_verse(line[0], line[1])
        current_q = Question(line[2], line[3], line[4], *[temp_verse])
        if any([vs in key_refs for vs in current_q.get_verses()]):
            key_pool.append(current_q)
        else:
            pool.append(current_q)
    return pool, key_pool


def get_key_question(q_type, pop=True):
    """
    Parameters
    ----------
    q_type : type of question to pull

    Returns
    -------
    A question, from the memory verses,
    of the given type, and removes it from the pool of questions
    """
    global key_pool
    random.shuffle(key_pool)
    for question in key_pool:
        if question._type == q_type:
            if pop:
                key_pool.remove(question)
            return question
    else:
        print("Ran out of key questions. Substitute regular questions?")
        response = input("y/n:")
        if response.lower() == 'y':
            return (get_question(q_type, pop))
        else:
            raise ValueError("Ran out of key questions...")


def get_question(q_type, pop=True):
    """
    Parameters
    ----------
    q_type : type of question to pull

    Returns
    -------
    A question of the given type, and removes it from the pool of questions
    """
    global pool
    random.shuffle(pool)
    for question in pool:
        if question._type == q_type:
            if pop:
                pool.remove(question)
            return question
    else:
        print([q.to_string() for q in pool])
        raise ValueError(f"{q_type} not found, are any remaining?")
    

def string_to_html(text, title="Quiz"):
    """
    Takes any old string and formats it for writing as an .html file.
    Optionally specify a title to be written as a header at the top of the page.
    
    Returns
    -------
    html : A string with proper html tags, like the initial header and line br.
    """
    html = text.translate({'\n': "<br>"})
    html = f"<html><h1>{title}</h1>" + html + "</html>"
    return html


# Main =======================================================================
def main():
    # General flow:
    # Welcome screen
    # Configure settings, paths, ratios
    # Choose output type (print, txt, location)
    # Crunch numbers
    global debug
    debug = False
    print("""
          ====================================================================
          
                                          QuizGen
                                           v2.0
                                    by Isaiah Magnuson
                                    
          ====================================================================
          """)
    # type 'debug' to enter debug mode
    resp = input("Press Enter to continue")
    if resp == 'debug':
        debug = True
    else:
        debug = False

    q_lib = readQuestionLibrary()
    print("File read succesfully")
    key_verses = readKeyList()
    print("File read succesfully")
    result_path = config["Paths"]["ResultsDirectory"]
    
    global pool
    global key_pool
    
    # Debug:
    if debug:
        for question in q_lib:
            print(question)
        
    pool, key_pool = gen_pools(q_lib, key_verses)
        
    # set params
    num_quizzes = config["NumberToGenerate"]
    if not num_quizzes:
        num_quizzes = 1
    
    desired_title = config["Titles"]
    
    # crunch numbers
    quizzes = []
    for i in range(num_quizzes):
        quizzes.append(Quiz())
    
    # spit out results
    for index, quiz in enumerate(quizzes):
        index = index + 1
        if not result_path:
            # TODO implement titles later, console output only
            print(quiz.to_string(f"{desired_title} #{index}"))
        else:
            desired_title = f"{desired_title} #{index}"
            html = string_to_html(quiz.to_string(desired_title))
            title = f"{desired_title}.html"
            with open(result_path + "/" + title, 'x') as file:
                file.write(html)
        
    
if __name__ == "__main__":
    main()
