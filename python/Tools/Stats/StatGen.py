# -*- coding: utf-8 -*-
"""
Created on Fri Jan 12 12:09:54 2024

@author: imagn

Designed to read in the results.xml file generated by the NextGen quizzing
software.
Once processed, we should display:
    1. Teams sorted by points
    2. Tiebreaks if necessary
    3. Individuals and their stats
    
The option to just run stats for individuals and teams would be handy.

Configuration for this script is in the head/configs/ directory.
Data to be processed should be placed in the head/data/ directory
"""
# Imports ====================================================================

import os
import xml.etree.ElementTree as ET
import yaml

# Constants ==================================================================
match_points_map = {
    "1": 3,
    "2": 2,
    "3": 1
}

# Functions ===================================================================
def is_player_in_players(id_ref, list_of_players):
    """
    Returns True and an index is player is in the list already.
    """
    found = False
    return_index = 0
    for index, player in enumerate(list_of_players):
        if player.id_ref == id_ref:
            found = True
            return_index = index
    
    return found, return_index


def is_team_in_teams(id_ref, list_of_teams):
    """
    Returns True and an index is team is in the list already.
    """
    found = False
    return_index = 0
    for index, team in enumerate(list_of_teams):
        if team.id_ref == id_ref:
            found = True
            return_index = index
    
    return found, return_index


# Classes ====================================================================
class Player:
    def __init__(self, id_ref, name):
        self.id_ref = id_ref
        self.name = name
        self.score = 0
        self.errors = 0
        self.matches_played = 0
        
    def add_score(self, added_score):
        self.score = self.score + added_score
        
    def add_errors(self, added_error):
        self.errors = self.errors + added_error
        
    def increment_match(self):
        self.matches_played += 1
        
    def to_string(self):
        return f"\n{self.id_ref}.{self.name}. Pts:{self.score}. Errs:{self.errors}. Pts/Match:{round(self.score/self.matches_played, 2)}."


class Team:
    def __init__(self, id_ref, name):
        self.id_ref = id_ref
        self.name = name
        self.score = 0
        self.errors = 0
        self.match_points = 0
        self.matches_played = 0
    
    def add_match_points(self, add_points):
        self.match_points = self.match_points + add_points
    
    def add_score(self, added_score):
        self.score = self.score + added_score
        
    def add_errors(self, added_error):
        self.errors = self.errors + added_error
        
    def increment_match(self):
        self.matches_played += 1
        
    def to_string(self):
        return f"\n{self.id_ref}.{self.name}. Match Points:{self.match_points}. Total Pts:{self.score}. Total Errs:{self.errors}. Pts/Match:{round(self.score/self.matches_played, 2)}."


# Setup ======================================================================
absolute_path = os.path.dirname(__file__)

config_path = os.path.join(absolute_path, "../../../configs/")
results_path = os.path.join(absolute_path, "../../../results/")
statgen_map_path = os.path.join(config_path, "statgen_map.yml")

with open(statgen_map_path, 'r') as file:
    id_map = yaml.safe_load(file)

data_path = os.path.join(absolute_path, "../../../data/")
xml_path = os.path.join(data_path, id_map["Filename"])

# Careful that data is a safe XML, that's not handled here.
tree = ET.parse(xml_path)
root = tree.getroot()

team_map = id_map["Teams"]
player_map = id_map["Players"]

# Data Processing ============================================================
results = root[0]

players = []
teams = []

for match in results:
    # Is the info new?
    for node in match:
        line = node.attrib
        print(line)
        if node.tag == "team":
            new_check = is_team_in_teams(int(line["id"]), teams)
            team_id = int(line["id"])
            if new_check[0] == False:
                teams.append(Team(team_id, team_map[team_id]))
                list_index = -1
            else:
                list_index = new_check[1]
            
            teams[list_index].add_score(int(line["score"]))
            teams[list_index].add_errors((int(line["errors"])))
            teams[list_index].add_match_points(match_points_map[line["place"]])
            teams[list_index].increment_match()
                
        elif node.tag == "quizzer":
            new_check = is_player_in_players(int(line["id"]), players)
            player_id = int(line["id"])
            if new_check[0] == False:
                players.append(Player(player_id, player_map[player_id]))
                list_index = -1
            else:
                list_index = new_check[1]
            
            players[list_index].add_score(int(line["score"]))
            players[list_index].add_errors((int(line["errors"])))
            players[list_index].increment_match()
            
        else:
            print(f"node {node} not recognized.")

# Report Out =================================================================
report = ""
for team in teams:
    report += team.to_string()
report += "\n -------------- \n"
for player in players:
    report += player.to_string()

title = id_map["Title"]
with open(f"{results_path}/{title}.txt", 'x') as file:
    file.write(report)
    