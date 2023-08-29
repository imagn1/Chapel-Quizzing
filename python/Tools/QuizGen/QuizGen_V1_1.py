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
accepted_types = ["QT","FTV","INT","MA"]
default_type_dist = {"QT":(1,2), "FTV":(1,2), "MA":(1,2)}
default_num_questions = 20
default_num_backup = 5
default_ratio_key = 0.5

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
class Question:
    
    def __init__(self, book, _type, reference, prompt, answer):
        self.book = book
        self._type = _type
        self.reference = reference
        self.prompt = prompt
        self.answer = answer

    def to_string(self):
        buildup = "" + self.book + "," + self._type + "," + self.reference + "," + self.prompt + "," + self.answer
        return buildup

class Quiz:
      
    global debug
    
    default_num_questions = quiz_definition["Quiz"]["Questions"]["Number"]
    default_ratio_key = quiz_definition["Quiz"]["Questions"]["RatioKey"]
    default_num_backup = quiz_definition["Quiz"]["Backups"]["Number"]
    default_type_dist = quiz_definition["Quiz"]["Questions"]["Distribution"]
    
    def __init__(self):
        num_questions = default_num_questions
        ratio_key = default_ratio_key
        num_backup = default_num_backup
        ratio_types = default_type_dist
        
        question_set = []
        backup_question_set = []
        num_types = {}
        non_ints = 0
        
        # Determine the number of each question you need
        for key,value in ratio_types.items():
            print(f"{key}: {value} ratio")
            upper = value[1] + 1
            lower = value[0]
            num_types[key] = random.randrange(lower,upper)
            non_ints += num_types[key]
        
        # Fill in the rest with INTs
        assert non_ints <= num_questions
        num_types["INT"] = num_questions - non_ints
        
        # Pull questions into the quiz
        for q_type, quantity in num_types.items():
            for i in range(quantity):
                if q_type not in ["QT", "FTV"]:
                    if random.random() <= ratio_key:
                        # get key question
                        question_set.append(get_key_question(q_type))
                    else:
                        question_set.append(get_question(q_type))
                else:  # For memory verses, they'll always be key 
                    question_set.append(get_key_question(q_type))

        assert len(question_set) == num_questions
        
        # Now do the backup questions
        # There's some decision to be made here. How should backup questions
        # be distributed? Should they remove themselves from the pool?
        # I'm deciding that we generate 2 backup Q's of each non-int type,
        # and the specified number of INT backups. Also they won't pop.
        if num_backup > 0:
            for key,value in num_types.items():
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
        
    def to_string(self,title="Quiz"):
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
    Relies on the oath definition in quizgen_config.yml
    
    Returns
    
    -------
    key_verses : list of references

    """
    key_lib = []
    key_path = config["Paths"]["KeyVersesCSV"]
    assert os.path.exists(key_path), "Key verses file not found at, " + str(key_path)
    with open(key_path, mode = 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        for row in csv_reader:
            key_lib.append(row)
    key_verses = []
    for row in key_lib:
        for item in row:
            key_verses.append(item)
    return key_verses


def gen_pools(q_lib, key_refs, book):
    """
    This function takes q_lib, a plain array of questions,
    and sorts it into two pools of Question type.

    Parameters
    ----------
    q_lib : from readQuestionLibrary
    key_refs : a list of references of the key verses
    book : the book questions are from
    Returns
    -------
    pool : a list of non-key Questions
    key_pool : a list of key Questions
    """
    pool = []
    key_pool = []
    # Assume first line is headers, and is in format:
    # TYPE, REF, PROMPT, ANSWER
    q_lib = q_lib[1:]
    for line in q_lib:
        # create the question first
        current_q = Question(book, line[0],line[1],line[2],line[3])
        if current_q.reference in key_refs:
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
            return(get_question(q_type, pop))
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
    
    pass
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
                                           v1.1
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
    print("Where to place results?")
    result_path = config["Paths"]["ResultsDirectory"]
    # only Hebrews implemented so far
    global pool
    global key_pool
    
    # Debug:
    if debug:
        for question in q_lib:
            print(question)
        
    pool, key_pool = gen_pools(q_lib, key_verses, "Hebrews")
        
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
            # TODO implement titles later 
            print(quiz.to_string(f"{desired_title} #{index}"))
        else:
            title = f"{desired_title} #{index}.txt"
            with open(result_path + "/" + title, 'w') as file:
                file.write(quiz.to_string(title))
    
    print("Quiz generation complete!")
    input("Press Enter to exit")
if __name__ == "__main__":
    main()